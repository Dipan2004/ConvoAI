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

_HIGH_THRESHOLD = 0.7
_LOW_THRESHOLD = 0.4
_LIMITED_DATA_DISCLAIMER = "This answer is based on limited available data."

_NO_DOCUMENTS_FALLBACK = (
    "I don’t have enough information on that right now. "
    "Let me connect you with our team."
)

_SYSTEM_TEMPLATE = """You are a knowledgeable product assistant.
Answer the user question using ONLY the context below.
Do not fabricate information not present in the context.
If the context is insufficient, say so clearly and offer to escalate.
Do not use markdown tables, ASCII tables, or pipe characters.
Format answers as clean bullet points or short paragraphs.
Keep the tone professional and easy to scan.

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
            return _NO_DOCUMENTS_FALLBACK
        top_score = docs[0].get("rerank_score") or docs[0].get("score", 0.0)
        score_level = self._score_level(top_score)
        logger.info({
            "event": "rag_decision",
            "score": top_score,
            "level": score_level,
            "threshold_used": self._min_score,
        })
        if score_level == "low":
            logger.warning({
                "event": "rag_low_relevance",
                "top_score": top_score,
                "threshold_used": self._min_score,
                "score_level": score_level,
            })
            return _FALLBACK
        context = self._format_context(docs)
        system = self._build_system(context)
        result = self._llm.generate(prompt=query, system=system, history=history)
        content = result.get("content") or _FALLBACK
        if score_level == "medium":
            content = f"{content}\n\n{_LIMITED_DATA_DISCLAIMER}"
        logger.info({
            "event": "rag_generated",
            "top_score": top_score,
            "docs_used": len(docs),
            "threshold_used": self._min_score,
            "score_level": score_level,
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

    def _score_level(self, top_score: float) -> str:
        if top_score >= _HIGH_THRESHOLD:
            return "high"
        if top_score >= _LOW_THRESHOLD:
            return "medium"
        return "low"
