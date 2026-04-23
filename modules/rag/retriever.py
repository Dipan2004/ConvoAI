from typing import Any, Dict, List, Optional

from services.vector_db_service import VectorDBService
from utils.logger import AppLogger

logger = AppLogger(__name__)


class Retriever:
    def __init__(self, vector_db_service: VectorDBService, top_k: int = 5):
        self._vdb = vector_db_service
        self._top_k = top_k

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        k = top_k or self._top_k
        results = self._vdb.query(query=query, top_k=k)
        logger.info({
            "event": "retrieval_done",
            "query_preview": query[:80],
            "results": len(results),
            "top_score": results[0]["score"] if results else 0.0,
        })
        return results

    def retrieve_with_filter(
        self,
        query: str,
        where: Dict[str, Any],
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        k = top_k or self._top_k
        return self._vdb.query(query=query, top_k=k, where=where)