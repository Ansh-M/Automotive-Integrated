from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


_STOPWORDS = {
    "best",
    "price",
    "prices",
    "pricing",
    "onroad",
    "on-road",
    "road",
    "review",
    "reviews",
    "spec",
    "specs",
    "specifications",
    "mileage",
    "top",
    "vs",
    "comparison",
    "compare",
    "features",
    "feature",
    "variant",
    "variants",
    "trim",
    "details",
    "info",
    "in",
    "for",
    "the",
    "a",
    "an",
    "new",
    "latest",
    "car",
    "cars",
    "vehicle",
}


@dataclass(frozen=True)
class NormalizedVehicleQuery:
    normalized: str
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None


def normalize_vehicle_query(query: str) -> NormalizedVehicleQuery:
    """
    Best-effort query normalization:
    - lowercases and trims
    - removes common intent words like 'best', 'price', 'review'
    - extracts a 4-digit year if present
    - attempts to infer make + model from first tokens
    """
    q = (query or "").strip().lower()
    q = re.sub(r"[^\w\s\-]", " ", q)  # keep words, spaces, hyphens
    q = re.sub(r"\s+", " ", q).strip()

    year: Optional[int] = None
    m = re.search(r"\b(19\d{2}|20\d{2})\b", q)
    if m:
        try:
            year = int(m.group(1))
        except Exception:
            year = None

    tokens = [t for t in q.split(" ") if t]
    cleaned_tokens: list[str] = []
    for t in tokens:
        if t in _STOPWORDS:
            continue
        if re.fullmatch(r"(19\d{2}|20\d{2})", t):
            cleaned_tokens.append(t)
            continue
        cleaned_tokens.append(t)

    make: Optional[str] = None
    model: Optional[str] = None
    mm_tokens = [t for t in cleaned_tokens if not re.fullmatch(r"(19\d{2}|20\d{2})", t)]
    if len(mm_tokens) >= 1:
        make = mm_tokens[0]
    if len(mm_tokens) >= 2:
        model = mm_tokens[1]

    normalized = " ".join(cleaned_tokens).strip()
    normalized = re.sub(r"\s+", " ", normalized)
    return NormalizedVehicleQuery(normalized=normalized, make=make, model=model, year=year)

