from __future__ import annotations

import json
import re
from typing import Any, Iterable
from urllib.parse import urlparse

from crewai import Crew
from dotenv import load_dotenv
from tavily import TavilyClient

from .agents import build_llm, researcher_agent, writer_agent
from .config import Settings
from .rag_store import ChromaSourceCache
from .schemas import ResearchBrief, VehicleQuery, WriterOutput, Source
from .tasks import build_research_task, build_writer_task
from .normalize import normalize_vehicle_query


def _vehicle_key(v: VehicleQuery) -> str:
    nq = normalize_vehicle_query(v.query or "")
    if nq.normalized:
        return nq.normalized
    # fallback if query is empty/garbage
    if nq.make and nq.model:
        return f"{nq.make}|{nq.model}"
    return (v.query or "").strip().lower()


def _extract_json_object(text: str) -> dict:
    """
    Crew/LLM outputs may wrap JSON with extra text. Extract the outermost JSON object.
    """
    if not text:
        raise ValueError("Empty response")
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in response")
    candidate = text[start : end + 1]
    return json.loads(candidate)


_PREFERRED_DOMAINS = [
    # OEM / official
    "marutisuzuki.com",
    "mahindra.com",
    "tatamotors.com",
    "toyota.com",
    "honda.com",
    "hyundai.com",
    "kia.com",
    "nissanusa.com",
    "ford.com",
    "chevrolet.com",
    "bmw.com",
    "mercedes-benz.com",
    "audi.com",
    "tesla.com",
    "volkswagen.com",
    "edmunds.com",
    "kbb.com",
    "caranddriver.com",
    "motortrend.com",
    "autocarindia.com",
    "carwale.com",
    "cardekho.com",
    "zigwheels.com",
    "autotrader.com",
]


def _domain(url: str) -> str:
    try:
        host = (urlparse(url).hostname or "").lower()
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return ""


def _source_score(url: str) -> int:
    d = _domain(url)
    if not d:
        return 0
    for i, pd in enumerate(_PREFERRED_DOMAINS):
        if d == pd or d.endswith("." + pd):
            return 1000 - i  # earlier in list = higher
    return 10


def _dedupe_and_rank_sources(sources: Iterable[Source], limit: int = 10) -> list[Source]:
    seen: set[str] = set()
    unique: list[Source] = []
    for s in sources:
        u = (s.url or "").strip()
        if not u:
            continue
        key = u.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(s)

    unique.sort(key=lambda s: (_source_score(s.url), len((s.snippet or ""))), reverse=True)
    return unique[:limit]


_CONFLICT_HINTS_RE = re.compile(
    r"\b(conflict|conflicting|varies|depending|approx|approximately|around|tbd|unknown)\b",
    flags=re.IGNORECASE,
)


def _count_conflict_signals(brief: ResearchBrief) -> int:
    signals = 0
    # Notes already carry conflict/uncertainty information from the agent.
    joined_notes = " ".join(brief.notes or [])
    if _CONFLICT_HINTS_RE.search(joined_notes):
        signals += 1

    # Heuristics on key fields: values like "X or Y", "varies by market", etc.
    fields = [
        brief.engine,
        brief.power,
        brief.torque,
        brief.transmission,
        brief.drivetrain,
        brief.fuel_economy,
        brief.dimensions,
        brief.weight,
        brief.pricing,
        brief.safety,
    ]
    
    for f in fields:
        if not f:
            continue

        if isinstance(f, dict):
            f_str = json.dumps(f)
        else:
            f_str = str(f)

        if _CONFLICT_HINTS_RE.search(f_str):
            signals += 1
            continue

        if " or " in f_str.lower():
            signals += 1
            continue

        if "/" in f_str and "http" not in f_str:
            signals += 1
            continue

    return signals


def _compute_confidence(num_sources: int) -> str:
    # Simple rule requested by user
    if num_sources >= 3:
        return "high"
    if num_sources == 2:
        return "medium"
    return "low"


def _postprocess_brief(brief: ResearchBrief) -> ResearchBrief:
    ranked_sources = _dedupe_and_rank_sources(brief.sources, limit=10)
    conflict_signals = _count_conflict_signals(brief)
    notes = list(brief.notes or [])
    if conflict_signals > 0 and not any("conflict" in (n or "").lower() for n in notes):
        notes.append("Conflicting or market-dependent data detected; verify specs for the exact trim/market.")

    if not ranked_sources:
        return brief.model_copy(
            update={
                "overview": brief.overview or "Data not available",
                "notes": (notes + ["Could not retrieve reliable sources"]) if notes else ["Could not retrieve reliable sources"],
                "confidence": "low",
                "sources": [],
            }
        )

    computed_conf = _compute_confidence(len(ranked_sources))

    return brief.model_copy(
        update={
            "sources": ranked_sources,
            "notes": notes,
            "confidence": computed_conf,
        }
    )


def run_automotive_crew(vehicle: VehicleQuery) -> WriterOutput:
    load_dotenv()
    settings = Settings.load()
    if not settings.groq_api_key:
        raise RuntimeError("Missing GROQ_API_KEY. Add it to your .env.")
    if not settings.tavily_api_key:
        raise RuntimeError("Missing TAVILY_API_KEY. Add it to your .env.")

    llm = build_llm(settings)
    cache = ChromaSourceCache(persist_dir=settings.chroma_persist_dir)
    tavily = TavilyClient(api_key=settings.tavily_api_key)

    vehicle_key = _vehicle_key(vehicle)
    normalized_vehicle_query = normalize_vehicle_query(vehicle.query or "").normalized or vehicle.pretty()
    # Programmatic multi-query retrieval to avoid excessive agent/tool LLM loops (TPM limits)
    queries = [
        f"{normalized_vehicle_query} specifications",
        f"{normalized_vehicle_query} engine power torque",
        f"{normalized_vehicle_query} price safety features",
    ]

    sources_payload: list[dict] = []
    seen_urls: set[str] = set()
    source_origin = "unknown"

    # Try cache hits first
    for q in queries:
        cached = cache.search(vehicle_key, query=q, k=4)
        for c in cached:
            md = c.get("metadata") or {}
            url = str(md.get("url", "")).strip()
            title = str(md.get("title", "")).strip()
            snippet = str(c.get("document") or "").strip()[:380]
            if not url:
                continue
            uk = url.lower()
            if uk in seen_urls:
                continue
            seen_urls.add(uk)
            sources_payload.append({"title": title or "Cached source", "url": url, "snippet": snippet, "source_type": "cache"})

    if sources_payload:
        source_origin = "cache"
    else:
        # Fetch from web (compact)
        for q in queries:
            res = tavily.search(query=q, max_results=4, include_raw_content=False, include_answer=False)
            results = res.get("results", []) if isinstance(res, dict) else []
            for r in results:
                url = str(r.get("url", "")).strip()
                if not url:
                    continue
                uk = url.lower()
                if uk in seen_urls:
                    continue
                seen_urls.add(uk)
                title = str(r.get("title", "")).strip()
                snippet = str(r.get("content", "") or r.get("snippet", "")).strip()[:380]
                sources_payload.append({"title": title, "url": url, "snippet": snippet, "source_type": "web"})

        cache.upsert_sources(vehicle_key, sources_payload)
        source_origin = "web" if sources_payload else "unknown"

    researcher = researcher_agent(llm=llm, tools=[])
    writer = writer_agent(llm=llm)

    research_task = build_research_task(researcher)
    writer_task = build_writer_task(writer)

    research_crew = Crew(agents=[researcher], tasks=[research_task], verbose=True)
    research_json_text = str(
        research_crew.kickoff(
            inputs={
                "vehicle_query": normalized_vehicle_query,
                "sources_json": json.dumps(sources_payload, ensure_ascii=False),
            }
        )
    ).strip()

    try:
        data = _extract_json_object(research_json_text)
        # Ensure the brief always contains the original query.
        vehicle_obj = data.get("vehicle") or {}
        if isinstance(vehicle_obj, dict) and not vehicle_obj.get("query"):
            vehicle_obj["query"] = vehicle.query
            data["vehicle"] = vehicle_obj
        brief = ResearchBrief.model_validate(data)
    except Exception as e:
        raise RuntimeError(
            "Researcher did not return valid JSON. "
            "Try again or adjust the query."
        ) from e
    brief = _postprocess_brief(brief)

    writer_crew = Crew(agents=[writer], tasks=[writer_task], verbose=True)
    markdown_report = str(
        writer_crew.kickoff(
            inputs={
                "research_brief_json": json.dumps(brief.model_dump(), ensure_ascii=False),
            }
        )
    ).strip()

    title = f"{vehicle.pretty()} — Research Report"
    return WriterOutput(
        title=title,
        markdown_report=markdown_report,
        brief=brief,
        citations=brief.sources,
        meta={
            "model": settings.groq_model,
            "chroma_persist_dir": settings.chroma_persist_dir,
            "source_origin": source_origin,
        },
    )

