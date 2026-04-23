from typing import Optional, Tuple

from services.llm_service import LLMService
from utils.json_parser import JSONParser
from utils.logger import AppLogger
from utils.prompt_loader import PromptLoader

logger = AppLogger(__name__)

_VALID_INTENTS = {
    "product_inquiry",
    "support_request",
    "lead_capture",
    "small_talk",
    "out_of_scope",
}

_SYSTEM = """You are an intent classification system.
Classify the user message into exactly one of:
- product_inquiry
- support_request
- lead_capture
- small_talk
- out_of_scope
Return ONLY valid JSON. No explanation. No markdown.
Format: {"intent": "<label>", "confidence": <float 0.0-1.0>, "reasoning": "<one sentence>"}"""


class IntentClassifier:
    def __init__(self, llm_service: LLMService, prompt_loader: Optional[PromptLoader] = None):
        self._llm = llm_service
        self._parser = JSONParser()
        self._prompt_loader = prompt_loader

    def classify(self, text: str) -> Tuple[str, float]:
        system = self._get_system_prompt()
        parsed = self._attempt(text, system)
        if not parsed:
            parsed = self._attempt(text, system)
        if not parsed or "intent" not in parsed:
            logger.warning({"event": "intent_classify_failed", "preview": text[:80]})
            return "out_of_scope", 0.0
        intent = parsed.get("intent", "out_of_scope")
        if intent not in _VALID_INTENTS:
            intent = "out_of_scope"
        confidence = max(0.0, min(1.0, float(parsed.get("confidence", 0.0))))
        logger.info({"event": "intent_classified", "intent": intent, "confidence": confidence})
        return intent, confidence

    def _attempt(self, text: str, system: str) -> dict:
        result = self._llm.generate_json(prompt=text, system=system)
        return result.get("parsed") or {}

    def _get_system_prompt(self) -> str:
        if self._prompt_loader:
            try:
                return self._prompt_loader.load("intent_v1")
            except FileNotFoundError:
                pass
        return _SYSTEM