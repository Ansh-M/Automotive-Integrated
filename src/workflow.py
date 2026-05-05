from __future__ import annotations

import json
import time
from typing import Any
from urllib.parse import urlparse

from crewai import Crew
from dotenv import load_dotenv

from .agents import build_llm, researcher_agent, writer_agent
from .config import Settings
from .rag_store import ChromaSourceCache
from .schemas import ResearchBrief, Source, VehicleQuery, WriterOutput
from .tasks import build_research_task, build_writer_task
from .tools import AutomotiveWebResearchTool
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

## Dimensions
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


def _compute_confidence(n: int) -> str:
    if n >= 3:
        return "high"
    if n == 2:
        return "medium"
    return "low"


def run_automotive_crew(vehicle: VehicleQuery) -> WriterOutput:
    load_dotenv()
    settings = Settings.load()
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY is not set. Contact the app admin to configure server API keys.")
    if not settings.tavily_api_key:
        raise RuntimeError("TAVILY_API_KEY is not set. Contact the app admin to configure server API keys.")

    # Researcher needs more tokens for JSON output; writer just formats existing data.
    llm = build_llm(settings, max_tokens=2048)
    llm_writer = build_llm(settings, max_tokens=1024)
    cache = ChromaSourceCache(persist_dir=settings.chroma_persist_dir)

    vehicle_key = _vehicle_key(vehicle)
    normalized_query = normalize_vehicle_query(vehicle.query or "").normalized or vehicle.pretty()

    # Wire tool into researcher — agent fetches its own sources, keeping each LLM call small
    research_tool = AutomotiveWebResearchTool(
        tavily_api_key=settings.tavily_api_key,
        cache=cache,
        vehicle_key=vehicle_key,
    )

    researcher = researcher_agent(llm=llm, tools=[research_tool])
    writer = writer_agent(llm=llm_writer)
    research_task = build_research_task(researcher)
    writer_task = build_writer_task(writer, research_task)

    crew = Crew(
        agents=[researcher, writer],
        tasks=[research_task, writer_task],
        verbose=False,
        max_rpm=10,
    )

    result = None
    for attempt in range(3):
        try:
            result = crew.kickoff(inputs={"vehicle_query": normalized_query})
            break
        except Exception as e:
            if "rate_limit" in str(e).lower() and attempt < 2:
                time.sleep(15)
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
            sources=[],
        )

    brief = _fill_missing(brief)
    brief = brief.model_copy(update={
        "sources": _dedupe_sources(brief.sources),
        "confidence": _compute_confidence(len(brief.sources)),
    })

    if not markdown_report or len(markdown_report) < 100:
        markdown_report = _build_report_from_brief(brief)

    return WriterOutput(
        title=f"{vehicle.pretty()} — Research Report",
        markdown_report=markdown_report,
        brief=brief,
        citations=brief.sources,
        meta={
            "model": settings.groq_model,
            "source_origin": "tool",
        },
    )


def run_comparison(query_a: str, query_b: str) -> tuple[WriterOutput, WriterOutput]:
    va = VehicleQuery(query=query_a)
    vb = VehicleQuery(query=query_b)
    result_a = run_automotive_crew(va)
    # Small pause — just enough to avoid hitting TPM in the same second.
    # Token usage is kept low via max_tokens=1024 on the writer agent.
    time.sleep(5)
    result_b = run_automotive_crew(vb)
    return result_a, result_b
