from __future__ import annotations

import json
from typing import Optional

from crewai.tools import BaseTool
from tavily import TavilyClient

from .rag_store import ChromaSourceCache
from .normalize import normalize_vehicle_query


class AutomotiveWebResearchTool(BaseTool):
    name: str = "Automotive_Web_Research"
    description: str = (
        "Search the web for authoritative car specs and return a compact JSON payload "
        "with sources. Use for: engine/power/torque, dimensions, trims, pricing, safety."
    )

    def __init__(
        self,
        tavily_api_key: str,
        cache: ChromaSourceCache,
        vehicle_key: str,
        include_answer: bool = False,
        max_results: int = 6,
    ) -> None:
        super().__init__()
        self._client = TavilyClient(api_key=tavily_api_key)
        self._cache = cache
        self._vehicle_key = vehicle_key
        self._include_answer = include_answer
        self._max_results = max_results

    def _run(self, query: str) -> str:
        nq = normalize_vehicle_query(query)
        norm_query = nq.normalized or query
      
        cached = self._cache.search(self._vehicle_key, query=norm_query, k=min(5, self._max_results))
        cached_sources = []
        for c in cached:
            md = c.get("metadata") or {}
            doc = (c.get("document") or "").strip()
            if md.get("url") and (md.get("title") or doc):
                cached_sources.append(
                    {
                        "title": md.get("title") or "Cached source",
                        "url": md.get("url"),
                        "snippet": doc[:280],
                        "source_type": "cache",
                    }
                )

        if cached_sources:
            return json.dumps(
                {
                    "query": norm_query,
                    "sources": cached_sources[: self._max_results],
                    "note": "Returned from Chroma cache.",
                },
                ensure_ascii=False,
            )

        res = self._client.search(
            query=norm_query,
            max_results=min(self._max_results, 4),
            include_answer=self._include_answer,
            include_raw_content=False,
        )

        results = res.get("results", []) if isinstance(res, dict) else []
        sources = []
        seen_urls: set[str] = set()
        for r in results:
            url = str(r.get("url", "")).strip()
            title = str(r.get("title", "")).strip()
            snippet = str(r.get("content", "") or r.get("snippet", "")).strip()
            if not url:
                continue
            url_key = url.lower()
            if url_key in seen_urls:
                continue
            seen_urls.add(url_key)
            sources.append(
                {
                    "title": title,
                    "url": url,
                    "snippet": snippet[:380] if snippet else None,
                    "source_type": "web",
                }
            )

        self._cache.upsert_sources(self._vehicle_key, sources)

        return json.dumps(
            {
                "query": norm_query,
                "sources": sources,
                "note": "Fetched from Tavily and cached into Chroma.",
            },
            ensure_ascii=False,
        )

