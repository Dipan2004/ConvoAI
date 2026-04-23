from typing import Any, Dict, Protocol, Tuple

from modules.intent.intent_node import IntentNode
from utils.logger import AppLogger

logger = AppLogger(__name__)


class Node(Protocol):
    def execute(self, state: Dict[str, Any], user_input: str) -> Tuple[Dict[str, Any], str]:
        ...


class Router:
    def __init__(
        self,
        intent_node: IntentNode,
        rag_node: Node,
        lead_node: Node,
        clarification_node: Node,
        fallback_node: Node,
        smalltalk_node: Node,
    ):
        self._intent_node = intent_node
        self._rag_node = rag_node
        self._lead_node = lead_node
        self._clarification_node = clarification_node
        self._fallback_node = fallback_node
        self._smalltalk_node = smalltalk_node

    def route(
        self, state: Dict[str, Any], user_input: str
    ) -> Tuple[Node, Dict[str, Any]]:
        state, _ = self._intent_node.execute(state, user_input)

        confidence = state.get("confidence", 0.0)
        intent = state.get("intent", "out_of_scope")

        logger.info({
            "event": "router_decision",
            "session_id": state.get("session_id"),
            "intent": intent,
            "confidence": confidence,
        })

        if confidence < 0.6:
            return self._clarification_node, state

        if intent == "small_talk":
            return self._smalltalk_node, state

        if intent == "out_of_scope":
            return self._fallback_node, state

        if intent == "lead_capture":
            return self._lead_node, state

        if intent in ("product_inquiry", "support_request"):
            lead_captured = state.get("flags", {}).get("lead_captured", False)
            if not lead_captured:
                return self._lead_node, state
            return self._rag_node, state

        return self._fallback_node, state