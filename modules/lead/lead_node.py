from typing import Tuple

from modules.lead.lead_manager import LeadManager
from modules.rag.rag_node import RAGNode
from utils.logger import AppLogger

logger = AppLogger(__name__)


class LeadNode:
    def __init__(self, lead_manager: LeadManager, rag_node: RAGNode | None = None):
        self._manager = lead_manager
        self._rag_node = rag_node

    def execute(self, state: dict, user_input: str) -> Tuple[dict, str]:
        state, response = self._manager.collect(state, user_input)
        complete = state.get("flags", {}).get("lead_ready", False)
        if complete and self._rag_node and state.get("original_query"):
            original_query = state["original_query"]
            state, rag_response = self._rag_node.execute(state, original_query)
            response = f"{response}\n\n{rag_response}"
            state["original_query"] = None
        logger.info({
            "event": "lead_node_executed",
            "session_id": state.get("session_id"),
            "lead_complete": complete,
        })
        return state, response
