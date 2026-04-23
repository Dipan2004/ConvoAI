from typing import Tuple

from services.llm_service import LLMService
from utils.logger import AppLogger

logger = AppLogger(__name__)

_SYSTEM = (
    "You are a friendly assistant for a SaaS product. "
    "Respond warmly to casual messages but gently guide toward product questions. "
    "Keep replies under 3 sentences."
)


class SmallTalkNode:
    def __init__(self, llm_service: LLMService):
        self._llm = llm_service

    def execute(self, state: dict, user_input: str) -> Tuple[dict, str]:
        result = self._llm.generate(prompt=user_input, system=_SYSTEM, temperature=0.7)
        response = result.get("content") or "Happy to chat! What can I help you with today?"
        logger.info({
            "event": "smalltalk_node_executed",
            "session_id": state.get("session_id"),
        })
        return state, response