from typing import Tuple

from modules.intent.intent_classifier import IntentClassifier
from utils.logger import AppLogger

logger = AppLogger(__name__)


class IntentNode:
    def __init__(self, classifier: IntentClassifier):
        self._classifier = classifier

    def execute(self, state: dict, user_input: str) -> Tuple[dict, str]:
        intent, confidence = self._classifier.classify(user_input)
        state["intent"] = intent
        state["confidence"] = confidence
        logger.info({
            "event": "intent_node_executed",
            "session_id": state.get("session_id"),
            "intent": intent,
            "confidence": confidence,
        })
        return state, ""