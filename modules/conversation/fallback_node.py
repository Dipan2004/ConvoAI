from typing import Tuple

from utils.logger import AppLogger

logger = AppLogger(__name__)

_RESPONSE = (
    "I'm best at helping with product details, pricing, or support. "
    "What would you like to explore?"
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
