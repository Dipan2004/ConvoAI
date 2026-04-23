from typing import Tuple

from modules.intent.intent_classifier import IntentClassifier
from utils.logger import AppLogger

logger = AppLogger(__name__)


class IntentNode:
    def __init__(self, classifier: IntentClassifier):
        self._classifier = classifier

    def execute(self, state: dict, user_input: str) -> Tuple[dict, str]:
        if state.get("lead_step") and state.get("lead_step") != "complete":
            state["intent"] = "lead_capture"
            state["confidence"] = 1.0
            logger.info({
                "event": "intent_node_bypassed",
                "session_id": state.get("session_id"),
                "reason": "lead_step_in_progress",
            })
            return state, ""

        intent, confidence = self._classifier.classify(user_input)
        state["intent"] = intent
        state["confidence"] = confidence
        if intent in ("product_inquiry", "support_request") and not state.get("flags", {}).get("lead_captured", False):
            state["original_query"] = state.get("original_query") or user_input
        logger.info({
            "event": "intent_node_executed",
            "session_id": state.get("session_id"),
            "intent": intent,
            "confidence": confidence,
        })
        return state, ""
