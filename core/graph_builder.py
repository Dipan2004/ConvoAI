from typing import Any, Dict, Tuple

from langgraph.graph import StateGraph, END

from modules.intent.intent_node import IntentNode
from utils.logger import AppLogger

logger = AppLogger(__name__)


def _route_after_intent(state: Dict[str, Any]) -> str:
    confidence = state.get("confidence", 0.0)
    intent = state.get("intent", "out_of_scope")

    if confidence < 0.6:
        return "clarification_node"
    if intent == "small_talk":
        return "smalltalk_node"
    if intent == "out_of_scope":
        return "fallback_node"
    if intent == "lead_capture":
        return "lead_node"
    if intent in ("product_inquiry", "support_request"):
        if not state.get("flags", {}).get("lead_captured", False):
            return "lead_node"
        return "rag_node"
    return "fallback_node"


def _wrap_node(node_instance: Any):
    def _fn(state: Dict[str, Any]) -> Dict[str, Any]:
        user_input = state.get("_current_input", "")
        updated_state, response = node_instance.execute(state, user_input)
        updated_state["_last_response"] = response
        return updated_state
    return _fn


def _wrap_intent_node(node_instance: IntentNode):
    def _fn(state: Dict[str, Any]) -> Dict[str, Any]:
        user_input = state.get("_current_input", "")
        updated_state, _ = node_instance.execute(state, user_input)
        return updated_state
    return _fn


class GraphBuilder:
    def __init__(
        self,
        intent_node: IntentNode,
        rag_node: Any,
        lead_node: Any,
        clarification_node: Any,
        fallback_node: Any,
        smalltalk_node: Any,
    ):
        self._intent_node = intent_node
        self._rag_node = rag_node
        self._lead_node = lead_node
        self._clarification_node = clarification_node
        self._fallback_node = fallback_node
        self._smalltalk_node = smalltalk_node

    def build(self):
        graph = StateGraph(dict)

        graph.add_node("intent_node", _wrap_intent_node(self._intent_node))
        graph.add_node("rag_node", _wrap_node(self._rag_node))
        graph.add_node("lead_node", _wrap_node(self._lead_node))
        graph.add_node("clarification_node", _wrap_node(self._clarification_node))
        graph.add_node("fallback_node", _wrap_node(self._fallback_node))
        graph.add_node("smalltalk_node", _wrap_node(self._smalltalk_node))

        graph.set_entry_point("intent_node")

        graph.add_conditional_edges(
            "intent_node",
            _route_after_intent,
            {
                "rag_node": "rag_node",
                "lead_node": "lead_node",
                "clarification_node": "clarification_node",
                "fallback_node": "fallback_node",
                "smalltalk_node": "smalltalk_node",
            },
        )

        for node_name in (
            "rag_node",
            "lead_node",
            "clarification_node",
            "fallback_node",
            "smalltalk_node",
        ):
            graph.add_edge(node_name, END)

        compiled = graph.compile()
        logger.info({"event": "graph_compiled"})
        return compiled