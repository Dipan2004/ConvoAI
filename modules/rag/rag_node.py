from typing import Tuple

from modules.rag.generator import Generator
from modules.rag.reranker import Reranker
from modules.rag.retriever import Retriever
from utils.logger import AppLogger

logger = AppLogger(__name__)


class RAGNode:
    def __init__(self, retriever: Retriever, reranker: Reranker, generator: Generator):
        self._retriever = retriever
        self._reranker = reranker
        self._generator = generator

    def execute(self, state: dict, user_input: str) -> Tuple[dict, str]:
        history = self._extract_history(state)
        docs = self._retriever.retrieve(user_input)
        reranked = self._reranker.rerank(user_input, docs)
        state["rag_context"] = reranked
        response = self._generator.generate(user_input, reranked, history)
        logger.info({
            "event": "rag_node_executed",
            "session_id": state.get("session_id"),
            "docs_retrieved": len(docs),
            "docs_reranked": len(reranked),
        })
        return state, response

    def _extract_history(self, state: dict) -> list:
        messages = state.get("messages", [])
        history = []
        for msg in messages[-6:]:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                history.append({"role": msg["role"], "content": msg["content"]})
        return history