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
        temperature=0.1,
        max_tokens=1024,
    )


def researcher_agent(llm: LLM, tools: list) -> Agent:
    return Agent(
        role="Automotive Researcher",
        goal="Search for accurate vehicle specifications using tools and output strict JSON.",
        backstory=(
            "You are a precise automotive data analyst. You use search tools to find facts. "
            "You never guess. You always output clean JSON with no extra text."
        ),
        tools=tools,
        llm=llm,
        verbose=False,
        max_iter=5,
        max_retry_limit=1,
    )


def writer_agent(llm: LLM) -> Agent:
    return Agent(
        role="Automotive Writer",
        goal="Convert a JSON research brief into a clean, well-structured Markdown report.",
        backstory=(
            "You are a technical writer for automotive publications. "
            "You write clearly, accurately, and never add facts not in the brief."
        ),
        tools=[],
        llm=llm,
        verbose=False,
        max_iter=2,
        max_retry_limit=1,
    )
