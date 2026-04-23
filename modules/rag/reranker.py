import math
from typing import Any, Dict, List

from services.embedding_service import EmbeddingService
from utils.logger import AppLogger

logger = AppLogger(__name__)


class Reranker:
    def __init__(self, embedding_service: EmbeddingService, top_k: int = 3):
        self._embedder = embedding_service
        self._top_k = top_k

    def rerank(self, query: str, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not docs:
            return []
        if len(docs) <= self._top_k:
            return docs
        query_vec = self._embedder.embed(query)
        scored = []
        for doc in docs:
            doc_vec = self._embedder.embed(doc["content"])
            score = self._cosine(query_vec, doc_vec)
            scored.append({**doc, "rerank_score": score})
        scored.sort(key=lambda d: d["rerank_score"], reverse=True)
        result = scored[: self._top_k]
        logger.info({
            "event": "rerank_done",
            "input": len(docs),
            "output": len(result),
            "top_score": round(result[0]["rerank_score"], 4) if result else 0.0,
        })
        return result

    def _cosine(self, a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        mag_a = math.sqrt(sum(x * x for x in a))
        mag_b = math.sqrt(sum(x * x for x in b))
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)