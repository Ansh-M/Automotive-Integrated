from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlparse
import time

from crewai import Crew
from dotenv import load_dotenv
from tavily import TavilyClient

from .agents import build_llm, researcher_agent, writer_agent
from .config import Settings
from .rag_store import ChromaSourceCache
from .schemas import ResearchBrief, Source, VehicleQuery, WriterOutput
from .tasks import build_research_task, build_writer_task
from .normalize import normalize_vehicle_query


def _vehicle_key(v: VehicleQuery) -> str:
    nq = normalize_vehicle_query(v.query or "")
    return nq.normalized or (v.query or "").strip().lower()


def _extract_json_object(text: str) -> dict:
    if not text:
        raise ValueError("Empty response")
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in response")
    return json.loads(text[start: end + 1])


def _domain(url: str) -> str:
    try:
        host = (urlparse(url).hostname or "").lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""


_PREFERRED = [
    "autocarindia.com", "carwale.com", "cardekho.com", "zigwheels.com",
    "edmunds.com", "caranddriver.com", "motortrend.com", "kbb.com",
    "autotrader.com", "marutisuzuki.com", "mahindra.com", "tatamotors.com",
    "hyundai.com", "kia.com", "bmw.com", "mercedes-benz.com",
]


def _source_score(url: str) -> int:
    d = _domain(url)
    for i, pd in enumerate(_PREFERRED):
        if d == pd or d.endswith("." + pd):
            return 1000 - i
    return 10


def _dedupe_sources(sources: list[Source], limit: int = 8) -> list[Source]:
    seen: set[str] = set()
    unique = []
    for s in sources:
        key = (s.url or "").lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(s)
    unique.sort(key=lambda s: _source_score(s.url or ""), reverse=True)
    return unique[:limit]


def _fill_missing(brief: ResearchBrief) -> ResearchBrief:
    """Replace None values with 'N/A' so the writer never sees nulls."""
    updates: dict[str, Any] = {}
    for field in ["overview", "engine", "power", "torque", "transmission",
                  "drivetrain", "fuel_economy", "dimensions", "weight",
                  "pricing", "safety"]:
        if not getattr(brief, field):
            updates[field] = "N/A"
    if not brief.key_features:
        updates["key_features"] = ["Information not available"]
    return brief.model_copy(update=updates) if updates else brief


def _build_report_from_brief(brief: ResearchBrief) -> str:
    features = "\n".join(f"- {f}" for f in (brief.key_features or ["N/A"]))
    sources = "\n".join(
        f"{i+1}. [{s.title or s.url}]({s.url})"
        for i, s in enumerate(brief.sources or [])
    )
    return f"""## Overview
{brief.overview or "N/A"}

## Specifications
| Engine | Power | Torque | Transmission | Drivetrain | Fuel Economy | Weight |
|--------|-------|--------|--------------|------------|--------------|--------|
| {brief.engine or "N/A"} | {brief.power or "N/A"} | {brief.torque or "N/A"} | {brief.transmission or "N/A"} | {brief.drivetrain or "N/A"} | {brief.fuel_economy or "N/A"} | {brief.weight or "N/A"} |

## Dimensions & Weight
{brief.dimensions or "N/A"}

## Pricing
{brief.pricing or "N/A"}

## Safety
{brief.safety or "N/A"}

## Key Features
{features}

## Sources
{sources}
"""


def _fetch_sources(
    query: str,
    vehicle_key: str,
    cache: ChromaSourceCache,
    tavily: TavilyClient,
    max_results: int = 7,
) -> list[dict]:
    """Try cache first, fall back to Tavily with targeted spec queries."""

    # Targeted queries that surface spec pages rather than generic overviews
    queries = [
        f"{query} engine power torque transmission specifications",
        f"{query} dimensions weight fuel economy mileage",
        f"{query} price variants safety rating features India",
    ]

    sources: list[dict] = []
    seen_urls: set[str] = set()

    for q in queries:
        for c in cache.search(vehicle_key, query=q, k=3):
            md = c.get("metadata") or {}
            url = str(md.get("url", "")).strip()
            if not url or url.lower() in seen_urls:
                continue
            seen_urls.add(url.lower())
            sources.append({
                "title": md.get("title", "Cached source"),
                "url": url,
                "snippet": str(c.get("document") or "")[:600],
                "source_type": "cache",
            })

    if sources:
        return sources

    for q in queries:
        try:
            res = tavily.search(
                query=q, max_results=max_results, include_raw_content=False
            )
            for r in (res.get("results", []) if isinstance(res, dict) else []):
                url = str(r.get("url", "")).strip()
                if not url or url.lower() in seen_urls:
                    continue
                seen_urls.add(url.lower())
                sources.append({
                    "title": str(r.get("title", "")),
                    "url": url,
                    "snippet": str(r.get("content", "") or r.get("snippet", ""))[:600],
                    "source_type": "web",
                })
        except Exception:
            pass

    if sources:
        cache.upsert_sources(vehicle_key, sources)

    return sources


def run_automotive_crew(vehicle: VehicleQuery) -> WriterOutput:
    load_dotenv()
    settings = Settings.load()
    if not settings.groq_api_key:
        raise RuntimeError("Missing GROQ_API_KEY in .env")
    if not settings.tavily_api_key:
        raise RuntimeError("Missing TAVILY_API_KEY in .env")

    llm = build_llm(settings)
    cache = ChromaSourceCache(persist_dir=settings.chroma_persist_dir)
    tavily = TavilyClient(api_key=settings.tavily_api_key)

    vehicle_key = _vehicle_key(vehicle)
    normalized_query = normalize_vehicle_query(vehicle.query or "").normalized or vehicle.pretty()

    sources = _fetch_sources(normalized_query, vehicle_key, cache, tavily)
    source_origin = "cache" if any(s.get("source_type") == "cache" for s in sources) else "web"

    researcher = researcher_agent(llm=llm, tools=[])
    writer = writer_agent(llm=llm)
    research_task = build_research_task(researcher)
    writer_task = build_writer_task(writer, research_task)

    crew = Crew(
        agents=[researcher, writer],
        tasks=[research_task, writer_task],
        verbose=False,
        max_rpm=10,
    )

    # Pass 6 sources with 500-char snippets for better spec coverage
    trimmed_sources = [
        {
            "title": s.get("title", "")[:80],
            "url": s.get("url", ""),
            "snippet": s.get("snippet", "")[:500],
        }
        for s in sources[:6]
    ]

    result = None

    for attempt in range(3):
        try:
            result = crew.kickoff(inputs={
                "vehicle_query": normalized_query,
                "sources_json": json.dumps(trimmed_sources, ensure_ascii=False),
            })
            break
        except Exception as e:
            if "rate_limit" in str(e).lower() and attempt < 2:
                time.sleep(12)
                continue
            raise

    tasks_output = crew.tasks
    research_raw = str(tasks_output[0].output or "").strip()
    markdown_report = str(writer_task.output or result).strip()

    if "```" in markdown_report:
        lines = markdown_report.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        markdown_report = "\n".join(lines).strip()

    try:
        data = _extract_json_object(research_raw)
        vehicle_obj = data.get("vehicle") or {}
        if isinstance(vehicle_obj, dict) and not vehicle_obj.get("query"):
            vehicle_obj["query"] = vehicle.query
            data["vehicle"] = vehicle_obj
        brief = ResearchBrief.model_validate(data)
    except Exception:
        brief = ResearchBrief(
            vehicle=vehicle,
            overview=f"Research data for {vehicle.pretty()}.",
            notes=["Could not parse structured data. Report generated from raw sources."],
            confidence="low",
            sources=[Source(title=s["title"], url=s["url"], snippet=s.get("snippet"))
                     for s in sources[:5] if s.get("url")],
        )

    brief = _fill_missing(brief)
    brief = brief.model_copy(update={
        "sources": _dedupe_sources(brief.sources),
        "confidence": _compute_confidence(len(brief.sources)),
    })

    return WriterOutput(
        title=f"{vehicle.pretty()} — Research Report",
        markdown_report=markdown_report,
        brief=brief,
        citations=brief.sources,
        meta={
            "model": settings.groq_model,
            "source_origin": source_origin,
        },
    )


def _compute_confidence(n: int) -> str:
    if n >= 3: return "high"
    if n == 2: return "medium"
    return "low"


def run_comparison(query_a: str, query_b: str) -> tuple[WriterOutput, WriterOutput]:
    va = VehicleQuery(query=query_a)
    vb = VehicleQuery(query=query_b)
    result_a = run_automotive_crew(va)
    time.sleep(10)  # give TPM limit time to recover
    result_b = run_automotive_crew(vb)
    return result_a, result_b
