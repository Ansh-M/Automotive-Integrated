from __future__ import annotations
from crewai import Task


def build_research_task(researcher) -> Task:
    return Task(
        description=(
            "Research the vehicle: {vehicle_query}.\n\n"
            "Use the Automotive_Web_Research tool. Make 2-3 targeted searches:\n"
            "  - '{vehicle_query} engine specs power torque transmission'\n"
            "  - '{vehicle_query} price dimensions safety features India'\n\n"
            "After ALL searches, output a single JSON object — nothing else.\n"
            "Use EXACT values from sources. Use 'N/A' only if truly not found after searching.\n\n"
            "{{\n"
            "  \"vehicle\": {{\"make\": \"\", \"model\": \"\", \"year\": \"\", \"trim\": \"\", \"market\": \"\"}},\n"
            "  \"overview\": \"2-3 sentence summary with key highlights\",\n"
            "  \"engine\": \"e.g. 1.5L Turbo 4-cyl\",\n"
            "  \"power\": \"e.g. 160 hp / 118 kW\",\n"
            "  \"torque\": \"e.g. 250 Nm\",\n"
            "  \"transmission\": \"e.g. 6-speed MT / 7-speed DCT\",\n"
            "  \"drivetrain\": \"e.g. FWD / AWD\",\n"
            "  \"fuel_economy\": \"e.g. 17.4 kmpl (ARAI)\",\n"
            "  \"dimensions\": \"e.g. L x W x H mm, wheelbase mm\",\n"
            "  \"weight\": \"e.g. 1385 kg kerb weight\",\n"
            "  \"pricing\": \"e.g. Rs 10.5 - 18.5 lakh (ex-showroom)\",\n"
            "  \"safety\": \"e.g. 5-star Global NCAP, 6 airbags standard\",\n"
            "  \"key_features\": [\"feature 1\", \"feature 2\", \"feature 3\", \"feature 4\", \"feature 5\"],\n"
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
            "Write the overview as a plain paragraph (2-3 sentences).\n\n"
            "## Specifications\n"
            "Markdown table — columns: Engine | Power | Torque | Transmission | Drivetrain | Fuel Economy | Weight\n"
            "One data row. Write N/A if the value is N/A.\n\n"
            "## Dimensions\n"
            "Write the dimensions value as a plain sentence.\n\n"
            "## Pricing\n"
            "Write the pricing value as a plain sentence.\n\n"
            "## Safety\n"
            "Write the safety value as a plain sentence.\n\n"
            "## Key Features\n"
            "Bullet point list of ALL key features from the JSON.\n\n"
            "## Sources\n"
            "Numbered list: [title](url) for each source.\n\n"
            "RULES: No label prefixes. No code blocks. Clean markdown only. Include ALL sections even if N/A."
        ),
        expected_output="A single clean Markdown report with no code blocks.",
        agent=writer,
        context=[research_task],
    )
