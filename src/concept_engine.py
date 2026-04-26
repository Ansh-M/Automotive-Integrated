from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

from groq import Groq
from dotenv import load_dotenv

from .config import Settings


_SYSTEM_PROMPT = """You are a world-class automotive designer with 30 years of experience 
in conceptual vehicle design. You specialize in both Indian and global markets.
Your descriptions are vivid, technical, and inspiring — covering exterior styling, 
interior design, materials, performance, technology, and target audience."""


@dataclass
class ConceptResult:
    user_prompt: str
    narrative: str
    image_prompt: str
    processing_time: float


class ConceptEngine:
    """Gen AI: prompt → narrative → image prompt using Groq (free)."""

    def __init__(self, settings: Settings):
        if not settings.groq_api_key:
            raise RuntimeError("Missing GROQ_API_KEY")
        self._client = Groq(api_key=settings.groq_api_key)
        self._model = settings.groq_model

    def _call(self, system: str, user: str, max_tokens: int = 1000) -> str:
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.8,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()

    def generate_narrative(self, user_prompt: str) -> str:
        return self._call(
            system=_SYSTEM_PROMPT,
            user=(
                f"Create a detailed, professional design narrative for this automotive concept:\n"
                f"{user_prompt}\n\n"
                "Cover: exterior styling, interior, materials, performance philosophy, "
                "target market, and what makes this concept unique. "
                "Write 3-4 rich paragraphs."
            ),
            max_tokens=900,
        )

    def generate_image_prompt(self, narrative: str, user_prompt: str) -> str:
        return self._call(
            system="You are an expert at writing prompts for AI image generation, specializing in automotive design.",
            user=(
                "Convert this automotive design narrative into an optimized AI image generation prompt.\n"
                "Make it visually descriptive: include design style, colors, materials, lighting, "
                "camera angle, and artistic style. Keep it under 200 words.\n\n"
                f"Original concept: {user_prompt}\n\n"
                f"Narrative:\n{narrative}"
            ),
            max_tokens=300,
        )

    def generate_concept(self, user_prompt: str) -> ConceptResult:
        start = time.time()
        narrative = self.generate_narrative(user_prompt)
        image_prompt = self.generate_image_prompt(narrative, user_prompt)
        return ConceptResult(
            user_prompt=user_prompt,
            narrative=narrative,
            image_prompt=image_prompt,
            processing_time=round(time.time() - start, 2),
        )


def get_concept_engine() -> ConceptEngine:
    load_dotenv()
    return ConceptEngine(Settings.load())
