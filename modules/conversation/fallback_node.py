from typing import Tuple

from utils.logger import AppLogger

logger = AppLogger(__name__)

_RESPONSE = (
    "I'm not sure I can help with that. "
    "I'm best at answering product questions, helping with support, "
    "or connecting you with our team. What can I help you with?"
)


class FallbackNode:
    def execute(self, state: dict, user_input: str) -> Tuple[dict, str]:
        logger.warning({
            "event": "fallback_triggered",
            "session_id": state.get("session_id"),
            "intent": state.get("intent"),
            "confidence": state.get("confidence"),
        })
        return state, _RESPONSE