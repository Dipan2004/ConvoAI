from typing import Tuple

from utils.logger import AppLogger

logger = AppLogger(__name__)

_RESPONSE = (
    "I want to make sure I help you correctly. "
    "Could you clarify what you're looking for? "
    "For example: product info, technical support, or a demo?"
)


class ClarificationNode:
    def execute(self, state: dict, user_input: str) -> Tuple[dict, str]:
        state["_pending_clarification"] = user_input
        logger.info({
            "event": "clarification_requested",
            "session_id": state.get("session_id"),
            "confidence": state.get("confidence"),
        })
        return state, _RESPONSE