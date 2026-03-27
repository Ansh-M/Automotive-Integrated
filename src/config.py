from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    groq_api_key: str
    tavily_api_key: str
    groq_model: str
    chroma_persist_dir: str

    @staticmethod
    def load() -> "Settings":
        groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
        tavily_api_key = os.getenv("TAVILY_API_KEY", "").strip()
        groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip() or "llama-3.1-8b-instant"
        chroma_persist_dir = os.getenv("CHROMA_PERSIST_DIR", ".chroma").strip() or ".chroma"
        return Settings(
            groq_api_key=groq_api_key,
            tavily_api_key=tavily_api_key,
            groq_model=groq_model,
            chroma_persist_dir=chroma_persist_dir,
        )

