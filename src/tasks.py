from __future__ import annotations
from crewai import Task


def build_research_task(researcher) -> Task:
    return Task(
        description=(
            "Research the vehicle: {vehicle_query}.\n\n"
            "Use the Automotive_Web_Research tool to search for specs. "
            "Make 2-3 targeted searches, for example:\n"
            "  - '{vehicle_query} engine power torque transmission specs'\n"
            "  - '{vehicle_query} dimensions weight fuel economy'\n"
            "  - '{vehicle_query} price safety features India'\n\n"
            "After searching, output a single JSON object — nothing else.\n"
            "Use exact values from sources. Use 'N/A' only if truly not found.\n\n"
            "{{\n"
            "  \"vehicle\": {{\"make\": \"\", \"model\": \"\", \"year\": \"\", \"trim\": \"\", \"market\": \"\"}},\n"
            "  \"overview\": \"2-3 sentence summary\",\n"
            "  \"engine\": \"e.g. 1.5L Turbo 4-cyl\",\n"
            "  \"power\": \"e.g. 160 hp\",\n"
            "  \"torque\": \"e.g. 250 Nm\",\n"
            "  \"transmission\": \"e.g. 6-speed AT\",\n"
            "  \"drivetrain\": \"e.g. FWD\",\n"
            "  \"fuel_economy\": \"e.g. 17 kmpl\",\n"
            "  \"dimensions\": \"e.g. 4300 x 1790 x 1635 mm\",\n"
            "  \"weight\": \"e.g. 1385 kg\",\n"
            "  \"pricing\": \"e.g. Rs 10-18 lakh\",\n"
            "  \"safety\": \"e.g. 5-star Global NCAP, 6 airbags\",\n"
            "  \"key_features\": [\"feature 1\", \"feature 2\", \"feature 3\"],\n"
            "  \"sources\": [{{\"title\": \"\", \"url\": \"\", \"snippet\": \"\"}}],\n"
            "  \"confidence\": \"high\",\n"
            "  \"notes\": []\n"
            "}}"
        ),
        expected_output="A single valid JSON object with no surrounding text.",
        agent=researcher,
    )


def build_writer_task(writer, research_task) -> Task:
    return Task(
        description=(
            "Convert the JSON brief from the previous task into a clean Markdown report.\n"
            "Use ONLY values from the JSON. Do NOT invent or add anything.\n\n"
            "## Overview\n"
            "Write the overview as a plain paragraph.\n\n"
            "## Specifications\n"
            "Markdown table — columns: Engine | Power | Torque | Transmission | Drivetrain | Fuel Economy | Weight\n"
            "One data row. Write N/A if the value is N/A.\n\n"
            "## Dimensions\n"
            "Write the dimensions value.\n\n"
            "## Pricing\n"
            "Write the pricing value as a plain sentence.\n\n"
            "## Safety\n"
            "Write the safety value as a plain sentence.\n\n"
            "## Key Features\n"
            "Bullet point list.\n\n"
            "## Sources\n"
            "Numbered list: title + URL.\n\n"
            "RULES: No label prefixes. No code blocks. Clean markdown only."
        ),
        expected_output="A single clean Markdown report with no code blocks.",
        agent=writer,
        context=[research_task],
    )
