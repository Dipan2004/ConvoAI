from modules.lead.validator import LeadValidator
from modules.lead.lead_manager import LeadManager
from modules.lead.lead_node import LeadNode


def _fresh_state() -> dict:
    return {
        "session_id": "test-lead",
        "lead_data": {},
        "flags": {},
        "messages": [],
        "intent": "lead_capture",
        "confidence": 0.91,
        "rag_context": [],
    }


def _make_manager() -> LeadManager:
    return LeadManager(validator=LeadValidator())


def test_validator_valid_name():
    v = LeadValidator()
    ok, err = v.validate_name("Jane Doe")
    assert ok is True
    assert err is None


def test_validator_invalid_name_too_short():
    v = LeadValidator()
    ok, _ = v.validate_name("J")
    assert ok is False


def test_validator_invalid_name_with_digits():
    v = LeadValidator()
    ok, _ = v.validate_name("Jane123")
    assert ok is False


def test_validator_valid_email():
    v = LeadValidator()
    ok, err = v.validate_email("jane@example.com")
    assert ok is True
    assert err is None


def test_validator_invalid_email_no_at():
    v = LeadValidator()
    ok, _ = v.validate_email("janeexample.com")
    assert ok is False


def test_validator_invalid_email_empty():
    v = LeadValidator()
    ok, _ = v.validate_email("")
    assert ok is False


def test_validator_valid_platform():
    v = LeadValidator()
    ok, err = v.validate_platform("Slack")
    assert ok is True
    assert err is None


def test_validator_invalid_platform_empty():
    v = LeadValidator()
    ok, _ = v.validate_platform("")
    assert ok is False


def test_validator_field_dispatch_unknown():
    v = LeadValidator()
    ok, err = v.validate_field("unknown_field", "value")
    assert ok is False


def test_first_turn_asks_for_name():
    manager = _make_manager()
    state = _fresh_state()
    state, response = manager.collect(state, "I want a demo")
    assert "name" in response.lower()


def test_collect_name_stores_and_asks_email():
    manager = _make_manager()
    state = _fresh_state()
    state, _ = manager.collect(state, "start")
    state, response = manager.collect(state, "Jane Doe")
    assert state["lead_data"].get("name") == "Jane Doe"
    assert "email" in response.lower()


def test_invalid_email_re_asks():
    manager = _make_manager()
    state = _fresh_state()
    state["lead_data"] = {"name": "Jane Doe"}
    state["_pending_lead_field"] = "email"
    state, response = manager.collect(state, "notanemail")
    assert state["lead_data"].get("email") is None
    assert "email" in response.lower()


def test_valid_email_stored():
    manager = _make_manager()
    state = _fresh_state()
    state["lead_data"] = {"name": "Jane Doe"}
    state["_pending_lead_field"] = "email"
    state, _ = manager.collect(state, "jane@example.com")
    assert state["lead_data"].get("email") == "jane@example.com"


def test_is_complete_false_when_missing_fields():
    manager = _make_manager()
    state = _fresh_state()
    state["lead_data"] = {"name": "Jane Doe"}
    assert manager.is_complete(state) is False


def test_is_complete_true_when_all_fields_present():
    manager = _make_manager()
    state = _fresh_state()
    state["lead_data"] = {"name": "Jane Doe", "email": "jane@example.com", "platform": "Slack"}
    assert manager.is_complete(state) is True


def test_lead_ready_flag_set_on_completion():
    manager = _make_manager()
    state = _fresh_state()
    state["lead_data"] = {"name": "Jane Doe", "email": "jane@example.com"}
    state["_pending_lead_field"] = "platform"
    state, response = manager.collect(state, "Slack")
    assert state["flags"].get("lead_ready") is True
    assert "team" in response.lower() or "touch" in response.lower()


def test_existing_valid_data_not_overwritten():
    manager = _make_manager()
    state = _fresh_state()
    state["lead_data"] = {"name": "Jane Doe", "email": "jane@example.com"}
    state["_pending_lead_field"] = "platform"
    state, _ = manager.collect(state, "Slack")
    assert state["lead_data"]["name"] == "Jane Doe"
    assert state["lead_data"]["email"] == "jane@example.com"


def test_lead_node_execute_increments_flow():
    node = LeadNode(lead_manager=_make_manager())
    state = _fresh_state()
    updated, response = node.execute(state, "I want a demo")
    assert "_pending_lead_field" in updated
    assert len(response) > 0


def run():
    tests = [
        test_validator_valid_name,
        test_validator_invalid_name_too_short,
        test_validator_invalid_name_with_digits,
        test_validator_valid_email,
        test_validator_invalid_email_no_at,
        test_validator_invalid_email_empty,
        test_validator_valid_platform,
        test_validator_invalid_platform_empty,
        test_validator_field_dispatch_unknown,
        test_first_turn_asks_for_name,
        test_collect_name_stores_and_asks_email,
        test_invalid_email_re_asks,
        test_valid_email_stored,
        test_is_complete_false_when_missing_fields,
        test_is_complete_true_when_all_fields_present,
        test_lead_ready_flag_set_on_completion,
        test_existing_valid_data_not_overwritten,
        test_lead_node_execute_increments_flow,
    ]
    passed, failed = 0, []
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as exc:
            failed.append((t.__name__, str(exc)))
    return passed, failed