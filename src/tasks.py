from __future__ import annotations

from crewai import Task


def build_research_task(researcher) -> Task:
    return Task(
        description=(
            "Research the vehicle: {vehicle_query}.\n\n"
            "You are given pre-fetched sources from multiple web searches (already deduplicated as much as possible):\n"
            "{sources_json}\n\n"
            "Your job is to synthesize these sources into a single, strict JSON brief.\n"
            "Prioritize consistency across sources; if data conflicts or varies by market/trim, set the field to null and add a note.\n\n"
            "Return ONLY a valid JSON object with this exact shape:\n"
            "{\n"
            '  "vehicle": {"make": "...", "model": "...", "year": mostly current, otherwise last, "trim": "...", "market": "..."},\n'
            '  "overview": "...",\n'
            '  "engine": "...", "power": "...", "torque": "...", "transmission": "...", "drivetrain": "...",\n'
            '  "fuel_economy": "...", "dimensions": "...", "weight": "...",\n'
            '  "pricing": "...", "safety": "...",\n'
            '  "key_features": ["...", "..."],\n'
            '  "sources": [{"title":"...","url":"...","snippet":"..."}],\n'
            '  "confidence": "low|medium|high",\n'
            '  "notes": ["..."]\n'
            "}\n\n"
            "Rules:\n"
            "- No markdown, no commentary outside JSON.\n"
            "- If you cannot verify a field, set it to null and add a note.\n"
            "- Include at least 3 sources with URLs (prefer 5+ if possible).\n"
        ),
        expected_output="A single JSON object matching the schema exactly.",
        agent=researcher,
    )


def build_writer_task(writer) -> Task:
    return Task(
        description=(
            "Use ONLY this JSON research brief (do not add external facts):\n\n"
            "{research_brief_json}\n\n"
            "Write a user-friendly report in Markdown with:\n"
            "- A short overview paragraph\n"
            "- A specs table (engine, power, torque, transmission, drivetrain)\n"
            "- Secondary specs (dimensions, weight, fuel economy)\n"
            "- Pricing notes + market caveats\n"
            "- Safety highlights\n"
            "- Key features bullets\n"
            "- Sources section with numbered citations\n\n"
            "Important:\n"
            "- Do not invent facts beyond the JSON.\n"
            "- Keep units as provided; if mixed, call it out briefly.\n"
            "- Output ONLY markdown.\n"
        ),
        expected_output="A single Markdown report.",
        agent=writer,
    )

