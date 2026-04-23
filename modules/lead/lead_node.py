from typing import Tuple

from modules.lead.lead_manager import LeadManager
from utils.logger import AppLogger

logger = AppLogger(__name__)


class LeadNode:
    def __init__(self, lead_manager: LeadManager):
        self._manager = lead_manager

    def execute(self, state: dict, user_input: str) -> Tuple[dict, str]:
        state, response = self._manager.collect(state, user_input)
        complete = state.get("flags", {}).get("lead_ready", False)
        logger.info({
            "event": "lead_node_executed",
            "session_id": state.get("session_id"),
            "lead_complete": complete,
        })
        return state, response