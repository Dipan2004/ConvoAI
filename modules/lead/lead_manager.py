from typing import Optional, Tuple

from modules.lead.validator import LeadValidator
from utils.logger import AppLogger

logger = AppLogger(__name__)

_FIELD_ORDER = ["name", "email", "platform"]

_QUESTIONS = {
    "name": "Sure - I can help with pricing. Before that, could you share your name?",
    "email": "Could you share your email?",
    "platform": "Got it - which platform are you mainly using? (YouTube, Instagram, etc.)",
}


def mock_lead_capture(name: str, email: str, platform: str):
    print(f"Lead captured successfully: {name}, {email}, {platform}")


def _question_for(field: str, data: dict) -> str:
    if field == "email" and data.get("name"):
        return f"Nice to meet you {data['name']}! Could you share your email?"
    return _QUESTIONS[field]


def _next_step(field: str) -> str:
    if field == "name":
        return "email"
    if field == "email":
        return "platform"
    return "complete"


class LeadManager:
    def __init__(self, validator: LeadValidator):
        self._validator = validator

    def collect(self, state: dict, user_input: str) -> Tuple[dict, str]:
        if "lead_data" not in state or not isinstance(state["lead_data"], dict):
            state["lead_data"] = {}
        if "flags" not in state or not isinstance(state["flags"], dict):
            state["flags"] = {}
        if "lead_complete" not in state:
            state["lead_complete"] = False
        current_step = state.get("lead_step")
        if current_step not in (*_FIELD_ORDER, "complete"):
            current_step = state.get("_pending_lead_field") or self._next_missing(state["lead_data"]) or "complete"
            state["lead_step"] = current_step

        if current_step == "complete" and not self.is_complete(state):
            current_step = self._next_missing(state["lead_data"]) or "complete"
            state["lead_step"] = current_step
            state["lead_complete"] = False

        if state.get("_pending_lead_field") in _FIELD_ORDER:
            state["flags"]["lead_in_progress"] = True

        if current_step in _FIELD_ORDER and not state.get("flags", {}).get("lead_in_progress", False):
            state["flags"]["lead_in_progress"] = True
            state["_pending_lead_field"] = current_step
            return state, _question_for(current_step, state["lead_data"])

        if current_step in _FIELD_ORDER and user_input.strip():
            ok, error = self._validator.validate_field(current_step, user_input.strip())
            if ok:
                state["lead_data"][current_step] = user_input.strip()
                state["lead_step"] = _next_step(current_step)
                state["_pending_lead_field"] = state["lead_step"]
            else:
                return state, f"{error} {_question_for(current_step, state['lead_data'])}"

        if state.get("lead_step") == "complete":
            was_ready = state["flags"].get("lead_ready", False)
            state["flags"]["lead_ready"] = True
            state["flags"]["lead_in_progress"] = False
            state["lead_complete"] = self.is_complete(state)
            print("lead_complete:", state["lead_complete"])
            state.pop("_pending_lead_field", None)
            if not was_ready:
                mock_lead_capture(
                    state["lead_data"].get("name"),
                    state["lead_data"].get("email"),
                    state["lead_data"].get("platform"),
                )
            logger.info({"event": "lead_complete", "session_id": state.get("session_id")})
            name = state["lead_data"].get("name", "there")
            return state, (
                f"Thanks {name}! I've got your details. "
                "Let me walk you through pricing and features, and our team can help if needed."
            )

        next_field = state.get("lead_step") or self._next_missing(state["lead_data"]) or "name"
        state["flags"]["lead_in_progress"] = True
        state["lead_complete"] = False
        print("lead_complete:", state["lead_complete"])
        state["_pending_lead_field"] = next_field
        return state, _question_for(next_field, state["lead_data"])

    def is_complete(self, state: dict) -> bool:
        data = state.get("lead_data", {})
        return all(data.get(f) for f in _FIELD_ORDER)

    def next_question(self, state: dict) -> str:
        field = self._next_missing(state.get("lead_data", {}))
        return _question_for(field, state.get("lead_data", {})) if field else ""

    def _next_missing(self, data: dict) -> Optional[str]:
        for field in _FIELD_ORDER:
            if not data.get(field):
                return field
        return None
