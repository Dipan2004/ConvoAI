import uuid
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from config.settings import settings
from services.embedding_service import EmbeddingService
from utils.logger import AppLogger

logger = AppLogger(__name__)


class VectorDBService:
    def __init__(
        self,
        embedding_service: EmbeddingService,
        persist_dir: Optional[str] = None,
        collection_name: Optional[str] = None,
    ):
        self._embedder = embedding_service
        self._persist_dir = persist_dir or settings.chroma_persist_dir
        self._collection_name = collection_name or settings.chroma_collection_name
        self._client = chromadb.PersistentClient(
            path=self._persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            {
                "event": "vector_db_initialized",
                "collection": self._collection_name,
                "persist_dir": self._persist_dir,
                "doc_count": self._collection.count(),
            }
        )

    def add_documents(
        self,
        docs: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        if not docs:
            return []

        resolved_ids = ids or [str(uuid.uuid4()) for _ in docs]
        resolved_metas = metadatas or [{} for _ in docs]
        embeddings = self._embedder.embed_batch(docs)

        self._collection.upsert(
            ids=resolved_ids,
            embeddings=embeddings,
            documents=docs,
            metadatas=resolved_metas,
        )

        logger.info(
            {
                "event": "documents_added",
                "count": len(docs),
                "collection": self._collection_name,
            }
        )
        return resolved_ids

    def query(
        self,
        query: str,
        top_k: Optional[int] = None,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        k = top_k or settings.rag_top_k_dense
        embedding = self._embedder.embed(query)

        kwargs: Dict[str, Any] = {
            "query_embeddings": [embedding],
            "n_results": min(k, self._collection.count() or 1),
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where

        raw = self._collection.query(**kwargs)
        return self._parse_results(raw)

    def delete(self, ids: List[str]) -> None:
        if not ids:
            return
        self._collection.delete(ids=ids)
        logger.info({"event": "documents_deleted", "count": len(ids)})

    def count(self) -> int:
        return self._collection.count()

    def _parse_results(self, raw: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        if not raw or not raw.get("ids") or not raw["ids"][0]:
            return results
        ids = raw["ids"][0]
        docs = raw["documents"][0]
        metas = raw["metadatas"][0]
        distances = raw["distances"][0]
        for chunk_id, doc, meta, dist in zip(ids, docs, metas, distances):
            results.append(
                {
                    "id": chunk_id,
                    "content": doc,
                    "metadata": meta,
                    "score": round(1.0 - dist, 6),
                }
            )
        return results