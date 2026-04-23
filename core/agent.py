import time
from typing import Any, Dict, Optional

from core.state_manager import StateManager
from utils.logger import AppLogger

logger = AppLogger(__name__)

_SAFE_FALLBACK = "Something went wrong. Please try again."
_DEFAULT_RATE_LIMIT = 50


class Agent:
    def __init__(
        self,
        state_manager: StateManager,
        graph: Any,
        rate_limit: int = _DEFAULT_RATE_LIMIT,
    ):
        self._state_manager = state_manager
        self._graph = graph
        self._rate_limit = rate_limit

    def handle_request(self, session_id: str, user_input: str) -> Dict[str, Any]:
        t_start = time.monotonic()
        log = logger.with_session(session_id)

        log.step("request_received", input_preview=user_input[:80])

        try:
            state = self._state_manager.load(session_id)
        except Exception as exc:
            log.step("state_load_error", error=str(exc))
            return self._error_response(session_id)

        if self._is_rate_limited(state):
            log.step("rate_limit_exceeded", request_count=state.get("_request_count", 0))
            return {
                "session_id": session_id,
                "response": "Too many requests. Please wait before sending another message.",
                "meta": {
                    "intent": None,
                    "confidence": 0.0,
                    "tokens": {"input": 0, "output": 0, "total": 0},
                    "cost_usd": 0.0,
                    "latency_ms": 0.0,
                    "error": "rate_limited",
                },
            }

        state = self._increment_request_count(state)
        state = self._inject_input(state, user_input)
        state = self._append_user_message(state, user_input)

        try:
            result = self._graph.invoke(state)
        except Exception as exc:
            log.step("graph_invoke_error", error=str(exc))
            try:
                self._state_manager.save(session_id, state)
            except Exception:
                pass
            return self._error_response(session_id)

        response = result.get("_last_response") or _SAFE_FALLBACK
        result = self._append_assistant_message(result, response)
        result = self._sync_lead_flag(result, log)
        result.pop("_current_input", None)

        tokens = result.pop("_last_tokens", {"input": 0, "output": 0, "total": 0})
        cost = result.pop("_last_cost", 0.0)
        latency_ms = round((time.monotonic() - t_start) * 1000, 2)

        try:
            self._state_manager.save(session_id, result)
        except Exception as exc:
            log.step("state_save_error", error=str(exc))

        log.step(
            "request_completed",
            intent=result.get("intent"),
            confidence=result.get("confidence"),
            lead_captured=result.get("flags", {}).get("lead_captured", False),
            latency_ms=latency_ms,
            tokens=tokens,
            cost=cost,
        )

        return {
            "session_id": session_id,
            "response": response,
            "meta": {
                "intent": result.get("intent"),
                "confidence": result.get("confidence"),
                "tokens": tokens,
                "cost_usd": cost,
                "latency_ms": latency_ms,
                "lead_captured": result.get("flags", {}).get("lead_captured", False),
            },
        }

    def _inject_input(self, state: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        state["_current_input"] = user_input
        return state

    def _append_user_message(self, state: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        if not isinstance(state.get("messages"), list):
            state["messages"] = []
        state["messages"].append({"role": "user", "content": user_input})
        return state

    def _append_assistant_message(self, state: Dict[str, Any], response: str) -> Dict[str, Any]:
        if not isinstance(state.get("messages"), list):
            state["messages"] = []
        if response:
            state["messages"].append({"role": "assistant", "content": response})
        if len(state["messages"]) > 20:
            state["messages"] = state["messages"][-20:]
        return state

    def _sync_lead_flag(self, state: Dict[str, Any], log: AppLogger) -> Dict[str, Any]:
        flags = state.get("flags", {})
        if flags.get("lead_ready") and not flags.get("lead_captured"):
            flags["lead_captured"] = True
            state["flags"] = flags
            log.step("lead_marked_captured")
        return state

    def _is_rate_limited(self, state: Dict[str, Any]) -> bool:
        return state.get("_request_count", 0) >= self._rate_limit

    def _increment_request_count(self, state: Dict[str, Any]) -> Dict[str, Any]:
        state["_request_count"] = state.get("_request_count", 0) + 1
        return state

    def _error_response(self, session_id: str) -> Dict[str, Any]:
        return {
            "session_id": session_id,
            "response": _SAFE_FALLBACK,
            "meta": {
                "intent": None,
                "confidence": 0.0,
                "tokens": {"input": 0, "output": 0, "total": 0},
                "cost_usd": 0.0,
                "latency_ms": 0.0,
                "error": "internal_error",
            },
        }