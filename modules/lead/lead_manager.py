from typing import Optional, Tuple

from modules.lead.validator import LeadValidator
from utils.logger import AppLogger

logger = AppLogger(__name__)

_FIELD_ORDER = ["name", "email", "platform"]

_QUESTIONS = {
    "name": "Could I get your name?",
    "email": "What email address should we reach you at?",
    "platform": "Which platform or product are you interested in?",
}


class LeadManager:
    def __init__(self, validator: LeadValidator):
        self._validator = validator

    def collect(self, state: dict, user_input: str) -> Tuple[dict, str]:
        if "lead_data" not in state or not isinstance(state["lead_data"], dict):
            state["lead_data"] = {}
        if "flags" not in state or not isinstance(state["flags"], dict):
            state["flags"] = {}

        pending = state.get("_pending_lead_field")

        if pending and user_input.strip():
            ok, error = self._validator.validate_field(pending, user_input.strip())
            if ok:
                state["lead_data"][pending] = user_input.strip()
                state.pop("_pending_lead_field", None)
            else:
                return state, f"{error} {_QUESTIONS[pending]}"

        next_field = self._next_missing(state["lead_data"])
        if next_field is None:
            state["flags"]["lead_ready"] = True
            logger.info({"event": "lead_complete", "session_id": state.get("session_id")})
            return state, "Thanks! Someone from our team will be in touch shortly."

        state["_pending_lead_field"] = next_field
        return state, _QUESTIONS[next_field]

    def is_complete(self, state: dict) -> bool:
        data = state.get("lead_data", {})
        return all(data.get(f) for f in _FIELD_ORDER)

    def next_question(self, state: dict) -> str:
        field = self._next_missing(state.get("lead_data", {}))
        return _QUESTIONS[field] if field else ""

    def _next_missing(self, data: dict) -> Optional[str]:
        for field in _FIELD_ORDER:
            if not data.get(field):
                return field
        return None