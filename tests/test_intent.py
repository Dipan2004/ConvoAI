from unittest.mock import MagicMock
from modules.intent.intent_classifier import IntentClassifier
from modules.intent.intent_node import IntentNode


def _make_classifier(intent: str, confidence: float) -> IntentClassifier:
    llm = MagicMock()
    llm.generate_json.return_value = {
        "parsed": {"intent": intent, "confidence": confidence, "reasoning": "test"}
    }
    return IntentClassifier(llm_service=llm)


def test_product_inquiry_intent():
    clf = _make_classifier("product_inquiry", 0.92)
    intent, confidence = clf.classify("What features do you offer?")
    assert intent == "product_inquiry"
    assert confidence > 0.85


def test_support_request_intent():
    clf = _make_classifier("support_request", 0.88)
    intent, confidence = clf.classify("I have a bug with the login flow")
    assert intent == "support_request"
    assert confidence > 0.6


def test_lead_capture_intent():
    clf = _make_classifier("lead_capture", 0.91)
    intent, confidence = clf.classify("I want to book a demo")
    assert intent == "lead_capture"
    assert confidence > 0.6


def test_small_talk_intent():
    clf = _make_classifier("small_talk", 0.95)
    intent, confidence = clf.classify("Hey, how are you?")
    assert intent == "small_talk"
    assert confidence > 0.6


def test_out_of_scope_intent():
    clf = _make_classifier("out_of_scope", 0.80)
    intent, confidence = clf.classify("What is the weather in Paris?")
    assert intent == "out_of_scope"


def test_invalid_json_falls_back_to_out_of_scope():
    llm = MagicMock()
    llm.generate_json.return_value = {"parsed": None, "content": "not json"}
    clf = IntentClassifier(llm_service=llm)
    intent, confidence = clf.classify("gibberish input")
    assert intent == "out_of_scope"
    assert confidence == 0.0


def test_unknown_intent_label_falls_back():
    llm = MagicMock()
    llm.generate_json.return_value = {
        "parsed": {"intent": "something_unknown", "confidence": 0.9, "reasoning": "x"}
    }
    clf = IntentClassifier(llm_service=llm)
    intent, _ = clf.classify("some message")
    assert intent == "out_of_scope"


def test_confidence_clamped_above_one():
    llm = MagicMock()
    llm.generate_json.return_value = {
        "parsed": {"intent": "small_talk", "confidence": 1.5, "reasoning": "x"}
    }
    clf = IntentClassifier(llm_service=llm)
    _, confidence = clf.classify("hi")
    assert confidence == 1.0


def test_confidence_clamped_below_zero():
    llm = MagicMock()
    llm.generate_json.return_value = {
        "parsed": {"intent": "small_talk", "confidence": -0.3, "reasoning": "x"}
    }
    clf = IntentClassifier(llm_service=llm)
    _, confidence = clf.classify("hi")
    assert confidence == 0.0


def test_intent_node_updates_state():
    clf = _make_classifier("product_inquiry", 0.90)
    node = IntentNode(classifier=clf)
    state = {"session_id": "s1", "intent": None, "confidence": 0.0}
    updated, _ = node.execute(state, "Tell me about pricing")
    assert updated["intent"] == "product_inquiry"
    assert updated["confidence"] == 0.90


def run():
    tests = [
        test_product_inquiry_intent,
        test_support_request_intent,
        test_lead_capture_intent,
        test_small_talk_intent,
        test_out_of_scope_intent,
        test_invalid_json_falls_back_to_out_of_scope,
        test_unknown_intent_label_falls_back,
        test_confidence_clamped_above_one,
        test_confidence_clamped_below_zero,
        test_intent_node_updates_state,
    ]
    passed, failed = 0, []
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as exc:
            failed.append((t.__name__, str(exc)))
    return passed, failed