from typing import Any, Dict, Optional

from services.redis_service import RedisService
from utils.logger import AppLogger

logger = AppLogger(__name__)

_DEFAULT_STATE: Dict[str, Any] = {
    "intent": None,
    "confidence": 0.0,
    "lead_complete": False,
    "lead_step": "complete",
    "original_query": None,
    "lead_data": {},
    "flags": {
        "lead_captured": False,
        "lead_ready": False,
        "lead_in_progress": False,
    },
    "rag_context": [],
    "messages": [],
}


class StateManager:
    def __init__(self, redis_service: RedisService):
        self._redis = redis_service

    def load(self, session_id: str) -> Dict[str, Any]:
        state = self._redis.get(session_id)
        if state is None:
            state = self._init_state(session_id)
            self._redis.set(session_id, state)
            logger.info({"event": "state_created", "session_id": session_id})
        else:
            logger.info({"event": "state_loaded", "session_id": session_id})
        return state

    def save(self, session_id: str, state: Dict[str, Any]) -> None:
        success = self._redis.set(session_id, state)
        if not success:
            logger.error({"event": "state_save_failed", "session_id": session_id})
        else:
            logger.info({"event": "state_saved", "session_id": session_id})

    def delete(self, session_id: str) -> None:
        self._redis.delete(session_id)
        logger.info({"event": "state_deleted", "session_id": session_id})

    def exists(self, session_id: str) -> bool:
        return self._redis.exists(session_id)

    def _init_state(self, session_id: str) -> Dict[str, Any]:
        import copy
        state = copy.deepcopy(_DEFAULT_STATE)
        state["session_id"] = session_id
        state["lead_complete"] = False
        return state
