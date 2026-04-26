from __future__ import annotations
from crewai import Task


def build_research_task(researcher) -> Task:
    return Task(
        description=(
            "Research the vehicle: {vehicle_query}.\n\n"
            "You have pre-fetched web sources below. Read them carefully.\n"
            "{sources_json}\n\n"
            "Synthesize ONLY from these sources. Do NOT search the web again.\n"
            "Return ONLY a valid JSON object — no markdown, no explanation, no preamble.\n\n"
            "JSON shape (fill every field; use 'N/A' if genuinely not found, never null):\n"
            "{{\n"
            "  \"vehicle\": {{\"make\": \"...\", \"model\": \"...\", \"year\": \"...\", \"trim\": \"...\", \"market\": \"...\"}},\n"
            "  \"overview\": \"2-3 sentence summary of this vehicle\",\n"
            "  \"engine\": \"e.g. 2.0L Turbocharged 4-cylinder\",\n"
            "  \"power\": \"e.g. 204 hp\",\n"
            "  \"torque\": \"e.g. 300 Nm\",\n"
            "  \"transmission\": \"e.g. 7-speed DCT\",\n"
            "  \"drivetrain\": \"e.g. FWD\",\n"
            "  \"fuel_economy\": \"e.g. 15 kmpl or 32 mpg\",\n"
            "  \"dimensions\": \"e.g. 4450 x 1800 x 1450 mm\",\n"
            "  \"weight\": \"e.g. 1420 kg\",\n"
            "  \"pricing\": \"e.g. Rs 15-18 lakh or $28,000 USD\",\n"
            "  \"safety\": \"e.g. 5-star NCAP, 6 airbags\",\n"
            "  \"key_features\": [\"feature 1\", \"feature 2\", \"feature 3\"],\n"
            "  \"sources\": [{{\"title\": \"...\", \"url\": \"...\", \"snippet\": \"...\"}}],\n"
            "  \"confidence\": \"high\",\n"
            "  \"notes\": []\n"
            "}}\n\n"
            "CRITICAL: Output the JSON object and nothing else."
        ),
        expected_output="A single valid JSON object with no surrounding text.",
        agent=researcher,
    )


def build_writer_task(writer, research_task) -> Task: 
    return Task(
        description=(
            "You will receive a JSON research brief from the previous task.\n"
            "Write a clean Markdown report. Use ONLY the values from the JSON, no labels or prefixes.\n\n"
            "## Overview\n"
            "Write the overview value as a plain paragraph.\n\n"
            "## Specifications\n"
            "Create a markdown table with these exact columns: Engine | Power | Torque | Transmission | Drivetrain | Fuel Economy | Weight\n"
            "Put the values directly in the table cells. If a value is N/A, write N/A.\n\n"
            "## Dimensions & Weight\n"
            "Write the dimensions value as-is. Write the weight value as-is.\n\n"
            "## Pricing\n"
            "Write the pricing value as a plain sentence.\n\n"
            "## Safety\n"
            "Write the safety value as a plain sentence.\n\n"
            "## Key Features\n"
            "Write each feature as a bullet point. List at least 3 if available.\n\n"
            "## Sources\n"
            "Number each source with its title and URL.\n\n"
            "CRITICAL: Do NOT add labels like 'Pricing info:', 'Safety rating:', 'Market caveats:'. "
            "Do NOT wrap output in code blocks. Output ONLY clean markdown."
        ),
        expected_output="A single clean Markdown report with no code blocks.",
        agent=writer,
        context=[research_task],
    )