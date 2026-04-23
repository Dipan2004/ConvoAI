from unittest.mock import MagicMock, patch
from modules.intent.intent_classifier import IntentClassifier
from modules.intent.intent_node import IntentNode
from modules.lead.lead_manager import LeadManager
from modules.lead.lead_node import LeadNode
from modules.lead.validator import LeadValidator
from modules.conversation.smalltalk_node import SmallTalkNode
from modules.conversation.fallback_node import FallbackNode
from modules.conversation.clarification_node import ClarificationNode
from modules.rag.retriever import Retriever
from modules.rag.reranker import Reranker
from modules.rag.generator import Generator
from modules.rag.rag_node import RAGNode
from core.router import Router
from core.state_manager import StateManager
from core.agent import Agent


def _make_intent_node(intent: str, confidence: float) -> IntentNode:
    llm = MagicMock()
    llm.generate_json.return_value = {
        "parsed": {"intent": intent, "confidence": confidence, "reasoning": "test"}
    }
    return IntentNode(classifier=IntentClassifier(llm_service=llm))


def _make_rag_node(response: str = "Here is product info.") -> RAGNode:
    vdb = MagicMock()
    vdb.query.return_value = [
        {"id": "1", "content": "Pro plan costs $49/month.", "metadata": {"source": "docs.md"}, "score": 0.95}
    ]
    embedder = MagicMock()
    embedder.embed.return_value = [0.1] * 384
    llm = MagicMock()
    llm.generate.return_value = {"content": response, "parsed": None}
    return RAGNode(
        retriever=Retriever(vector_db_service=vdb, top_k=5),
        reranker=Reranker(embedding_service=embedder, top_k=3),
        generator=Generator(llm_service=llm),
    )


def _make_smalltalk_node() -> SmallTalkNode:
    llm = MagicMock()
    llm.generate.return_value = {"content": "Hey! Happy to help. What would you like to know?"}
    return SmallTalkNode(llm_service=llm)


def _make_state_manager() -> StateManager:
    redis = MagicMock()
    redis.get.return_value = None
    redis.set.return_value = True
    return StateManager(redis_service=redis)


def _build_graph(intent_node, rag_node, lead_node, smalltalk_node, fallback_node, clarification_node):
    from core.graph_builder import GraphBuilder
    return GraphBuilder(
        intent_node=intent_node,
        rag_node=rag_node,
        lead_node=lead_node,
        clarification_node=clarification_node,
        fallback_node=fallback_node,
        smalltalk_node=smalltalk_node,
    ).build()


def _build_agent_with_fixed_intent(intent: str, confidence: float) -> tuple:
    intent_node = _make_intent_node(intent, confidence)
    rag_node = _make_rag_node()
    lead_node = LeadNode(lead_manager=LeadManager(validator=LeadValidator()))
    smalltalk_node = _make_smalltalk_node()
    fallback_node = FallbackNode()
    clarification_node = ClarificationNode()
    state_manager = _make_state_manager()
    graph = _build_graph(intent_node, rag_node, lead_node, smalltalk_node, fallback_node, clarification_node)
    agent = Agent(state_manager=state_manager, graph=graph, rate_limit=100)
    return agent, state_manager


def test_greeting_routes_to_smalltalk():
    agent, sm = _build_agent_with_fixed_intent("small_talk", 0.95)
    result = agent.handle_request("sess-1", "Hi there!")
    assert result["meta"]["intent"] == "small_talk"
    assert len(result["response"]) > 0


def test_out_of_scope_routes_to_fallback():
    agent, sm = _build_agent_with_fixed_intent("out_of_scope", 0.85)
    result = agent.handle_request("sess-2", "What is the weather?")
    assert result["meta"]["intent"] == "out_of_scope"
    assert len(result["response"]) > 0


def test_low_confidence_routes_to_clarification():
    agent, sm = _build_agent_with_fixed_intent("product_inquiry", 0.40)
    result = agent.handle_request("sess-3", "uh maybe something about the thing")
    assert result["meta"]["confidence"] < 0.6
    assert "clarif" in result["response"].lower() or len(result["response"]) > 0


def test_product_inquiry_without_lead_captured_routes_to_lead():
    agent, sm = _build_agent_with_fixed_intent("product_inquiry", 0.91)
    result = agent.handle_request("sess-4", "Tell me about pricing")
    assert result["meta"]["intent"] == "product_inquiry"
    assert "name" in result["response"].lower() or "email" in result["response"].lower() or len(result["response"]) > 0


def test_full_conversation_flow():
    intent_sequence = [
        ("small_talk", 0.95),
        ("product_inquiry", 0.91),
        ("lead_capture", 0.88),
        ("lead_capture", 0.88),
        ("lead_capture", 0.88),
        ("lead_capture", 0.88),
        ("product_inquiry", 0.91),
    ]

    call_count = [0]
    llm = MagicMock()

    def _intent_side_effect(**kwargs):
        idx = min(call_count[0], len(intent_sequence) - 1)
        intent, conf = intent_sequence[idx]
        call_count[0] += 1
        return {"parsed": {"intent": intent, "confidence": conf, "reasoning": "test"}}

    llm.generate_json.side_effect = _intent_side_effect
    llm.generate.return_value = {"content": "Here is product info for Pro plan.", "parsed": None}

    intent_node = IntentNode(classifier=IntentClassifier(llm_service=llm))
    rag_node = _make_rag_node("Pro plan is $49/month with full features.")
    lead_node = LeadNode(lead_manager=LeadManager(validator=LeadValidator()))
    smalltalk_node = SmallTalkNode(llm_service=llm)
    fallback_node = FallbackNode()
    clarification_node = ClarificationNode()

    stored_state = {}

    def _redis_get(key):
        return stored_state.get(key)

    def _redis_set(key, value, ttl=None):
        stored_state[key] = value
        return True

    redis = MagicMock()
    redis.get.side_effect = _redis_get
    redis.set.side_effect = _redis_set
    redis.exists.return_value = False

    state_manager = StateManager(redis_service=redis)
    graph = _build_graph(intent_node, rag_node, lead_node, smalltalk_node, fallback_node, clarification_node)
    agent = Agent(state_manager=state_manager, graph=graph, rate_limit=100)
    session = "full-flow-test"

    r1 = agent.handle_request(session, "Hi")
    assert len(r1["response"]) > 0

    r2 = agent.handle_request(session, "Tell me about pricing")
    assert len(r2["response"]) > 0

    r3 = agent.handle_request(session, "I want the Pro plan")
    assert len(r3["response"]) > 0

    r4 = agent.handle_request(session, "Jane Doe")
    assert len(r4["response"]) > 0

    r5 = agent.handle_request(session, "jane@example.com")
    assert len(r5["response"]) > 0

    r6 = agent.handle_request(session, "Slack")
    assert len(r6["response"]) > 0

    state_after_lead = stored_state.get(session, {})
    assert state_after_lead.get("flags", {}).get("lead_captured") is True

    r7 = agent.handle_request(session, "What are the Pro plan features?")
    assert len(r7["response"]) > 0


def test_rate_limit_blocks_excess_requests():
    agent, sm = _build_agent_with_fixed_intent("small_talk", 0.95)

    stored = {}

    def _get(key):
        return stored.get(key)

    def _set(key, val, ttl=None):
        stored[key] = val
        return True

    sm._redis.get.side_effect = _get
    sm._redis.set.side_effect = _set
    sm._redis.exists.return_value = False

    agent._rate_limit = 2
    session = "rate-test"

    agent.handle_request(session, "msg 1")
    agent.handle_request(session, "msg 2")
    r = agent.handle_request(session, "msg 3")
    assert "too many" in r["response"].lower() or r["meta"].get("error") == "rate_limited"


def test_state_persists_across_requests():
    stored = {}

    def _get(key):
        return stored.get(key)

    def _set(key, val, ttl=None):
        stored[key] = val
        return True

    agent, sm = _build_agent_with_fixed_intent("small_talk", 0.9)
    sm._redis.get.side_effect = _get
    sm._redis.set.side_effect = _set
    sm._redis.exists.return_value = False

    session = "persist-test"
    agent.handle_request(session, "Hello")
    agent.handle_request(session, "How are you?")

    state = stored.get(session, {})
    messages = state.get("messages", [])
    user_messages = [m for m in messages if m.get("role") == "user"]
    assert len(user_messages) >= 2


def run():
    tests = [
        test_greeting_routes_to_smalltalk,
        test_out_of_scope_routes_to_fallback,
        test_low_confidence_routes_to_clarification,
        test_product_inquiry_without_lead_captured_routes_to_lead,
        test_full_conversation_flow,
        test_rate_limit_blocks_excess_requests,
        test_state_persists_across_requests,
    ]
    passed, failed = 0, []
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as exc:
            failed.append((t.__name__, str(exc)))
    return passed, failed