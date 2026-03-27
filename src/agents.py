from __future__ import annotations

from crewai import Agent, LLM

from .config import Settings


def build_llm(settings: Settings) -> LLM:
    model = settings.groq_model.strip()
    if "/" not in model:
        model = f"groq/{model}"
    return LLM(
        model=model,
        api_key=settings.groq_api_key,
        temperature=0.2,
    )


def researcher_agent(llm: LLM, tools: list) -> Agent:
    return Agent(
        role="Automotive Researcher",
        goal=(
            "Collect accurate, sourced automotive specifications and facts, "
            "and output a strict JSON brief for downstream writing."
        ),
        backstory=(
            "You are a meticulous automotive analyst. You never guess specs. "
            "When data is uncertain or market-dependent, you explicitly say so and cite sources."
        ),
        tools=tools,
        llm=llm,
        verbose=True,
    )


def writer_agent(llm: LLM) -> Agent:
    return Agent(
        role="Automotive Writer",
        goal="Turn a structured research brief into a clean, well-formatted report for users.",
        backstory=(
            "You are a technical writer specialized in car spec sheets. "
            "You preserve accuracy, keep formatting consistent, and include citations."
        ),
        tools=[],
        llm=llm,
        verbose=True,
    )

