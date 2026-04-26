from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable, Optional

import chromadb
from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2


def _stable_id(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update((p or "").encode("utf-8", errors="ignore"))
        h.update(b"\n")
    return h.hexdigest()


@dataclass
class ChromaSourceCache:
    persist_dir: str
    collection_name: str = "automotive_sources"

    def __post_init__(self) -> None:
        self._client = chromadb.PersistentClient(path=self.persist_dir)
        self._embed_fn = ONNXMiniLM_L6_V2()
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self._embed_fn,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert_sources(self, vehicle_key: str, sources: Iterable[dict]) -> int:
        docs: list[str] = []
        ids: list[str] = []
        metadatas: list[dict] = []
        seen_urls: set[str] = set()
        for s in sources:
            url = str(s.get("url", "")).strip()
            title = str(s.get("title", "")).strip()
            content = str(s.get("snippet", "")).strip()
            if not (url and (content or title)):
                continue
            url_key = url.lower()
            if url_key in seen_urls:
                continue
            seen_urls.add(url_key)
            doc = content if content else title
            doc_id = _stable_id(vehicle_key, url, title, doc[:5000])
            ids.append(doc_id)
            docs.append(doc[:2000])
            metadatas.append(
                {
                    "vehicle_key": vehicle_key,
                    "url": url,
                    "title": title,
                }
            )

        if not ids:
            return 0

        self._collection.upsert(ids=ids, documents=docs, metadatas=metadatas)
        return len(ids)

    def search(self, vehicle_key: str, query: str, k: int = 5) -> list[dict]:
        where = {"vehicle_key": vehicle_key} if vehicle_key else None
        res = self._collection.query(query_texts=[query], n_results=k, where=where)
        out: list[dict] = []
        for i in range(len(res.get("ids", [[]])[0])):
            out.append(
                {
                    "id": res["ids"][0][i],
                    "document": (res.get("documents", [[]])[0][i] if res.get("documents") else None),
                    "metadata": (res.get("metadatas", [[]])[0][i] if res.get("metadatas") else None),
                    "distance": (res.get("distances", [[]])[0][i] if res.get("distances") else None),
                }
            )
        return out

    def dump_vehicle_sources(self, vehicle_key: str, limit: int = 50) -> list[dict]:
        res = self._collection.get(where={"vehicle_key": vehicle_key}, limit=limit, include=["documents", "metadatas"])
        docs = res.get("documents", []) or []
        metas = res.get("metadatas", []) or []
        out: list[dict] = []
        for d, m in zip(docs, metas):
            out.append(
                {
                    "title": (m or {}).get("title", ""),
                    "url": (m or {}).get("url", ""),
                    "content": d or "",
                }
            )
        return out

