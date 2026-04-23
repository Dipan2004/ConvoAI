from typing import Any, Dict, List, Optional

from config.settings import settings
from services.llm_service import LLMService
from utils.logger import AppLogger
from utils.prompt_loader import PromptLoader

logger = AppLogger(__name__)

_FALLBACK = (
    "I don't have reliable information to answer that. "
    "Would you like me to connect you with our team?"
)

_SYSTEM_TEMPLATE = """You are a knowledgeable product assistant.
Answer the user question using ONLY the context below.
Do not fabricate information not present in the context.
If the context is insufficient, say so clearly and offer to escalate.

Context:
{context}"""


class Generator:
    def __init__(self, llm_service: LLMService, prompt_loader: Optional[PromptLoader] = None):
        self._llm = llm_service
        self._prompt_loader = prompt_loader
        self._min_score = settings.rag_min_relevance_score

    def generate(
        self,
        query: str,
        docs: List[Dict[str, Any]],
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        if not docs:
            return _FALLBACK
        top_score = docs[0].get("rerank_score") or docs[0].get("score", 0.0)
        if top_score < self._min_score:
            logger.warning({
                "event": "rag_low_relevance",
                "top_score": top_score,
                "threshold": self._min_score,
            })
            return _FALLBACK
        context = self._format_context(docs)
        system = self._build_system(context)
        result = self._llm.generate(prompt=query, system=system, history=history)
        content = result.get("content") or _FALLBACK
        logger.info({
            "event": "rag_generated",
            "top_score": top_score,
            "docs_used": len(docs),
            "grounded": self._check_grounding(content, docs),
        })
        return content

    def _format_context(self, docs: List[Dict[str, Any]]) -> str:
        parts = []
        for i, doc in enumerate(docs, 1):
            source = doc.get("metadata", {}).get("source", "unknown")
            parts.append(f"[{i}] Source: {source}\n{doc['content']}")
        return "\n\n".join(parts)

    def _build_system(self, context: str) -> str:
        if self._prompt_loader:
            try:
                template = self._prompt_loader.load("rag_v1")
                return template.format(context=context)
            except (FileNotFoundError, KeyError):
                pass
        return _SYSTEM_TEMPLATE.format(context=context)

    def _check_grounding(self, response: str, docs: List[Dict[str, Any]]) -> bool:
        combined = " ".join(d["content"] for d in docs).lower()
        words = {w for w in response.lower().split() if len(w) > 4}
        return len(words & set(combined.split())) >= 3