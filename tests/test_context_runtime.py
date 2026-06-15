"""Tests for runtime customer context behavior."""

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.store.memory import InMemoryStore

from src.agents.nodes import create_verify_info_node, extract_explicit_identifier
from src.context.customer_context import save_customer_context


class FakeLLM:
    def invoke(self, messages):
        return AIMessage(content="Please provide a valid customer identifier.")


def test_extract_explicit_identifier_does_not_treat_invoice_number_as_customer():
    assert extract_explicit_identifier("Why did invoice 5403 get refunded?") == ""
    assert extract_explicit_identifier("Now check Customer ID 4") == "4"


def test_verify_info_switches_to_explicit_new_customer_and_clears_derived_context():
    verify_info = create_verify_info_node(FakeLLM())
    state = {
        "customer_id": "5",
        "verified_customer_id": "5",
        "verification_status": "verified",
        "loaded_memory": "Support Context: old customer",
        "evidence_refs": ["old-evidence"],
        "case_summary": "old summary",
        "messages": [HumanMessage(content="Now check Customer ID 4. Why is the account past_due?")],
    }

    result = verify_info(state, {})

    assert result["customer_id"] == "4"
    assert result["verified_customer_id"] == "4"
    assert result["verification_status"] == "verified"
    assert result["context_changed"] is True
    assert result["loaded_memory"] == ""
    assert result["evidence_refs"] == []
    assert result["case_summary"] == ""
    assert isinstance(result["messages"][0], SystemMessage)
    assert "The current verified customer ID is: 4" in result["messages"][0].content
    assert "Ignore any earlier verified customer_id messages" in result["messages"][0].content


def test_verify_info_keeps_current_customer_when_message_has_non_customer_number():
    verify_info = create_verify_info_node(FakeLLM())
    state = {
        "customer_id": "5",
        "verified_customer_id": "5",
        "verification_status": "verified",
        "messages": [HumanMessage(content="Why did invoice 5403 get refunded?")],
    }

    result = verify_info(state, {})

    assert result["customer_id"] == "5"
    assert result["verified_customer_id"] == "5"
    assert result["verification_status"] == "verified"
    assert result["context_changed"] is False
    assert "The current verified customer ID is: 5" in result["messages"][0].content


def test_verify_info_does_not_clear_context_when_same_customer_is_repeated():
    verify_info = create_verify_info_node(FakeLLM())
    state = {
        "customer_id": "5",
        "verified_customer_id": "5",
        "verification_status": "verified",
        "loaded_memory": "Support Context: keep me",
        "evidence_refs": ["keep-evidence"],
        "case_summary": "keep summary",
        "messages": [HumanMessage(content="Customer ID is 5")],
    }

    result = verify_info(state, {})

    assert result["customer_id"] == "5"
    assert result["verified_customer_id"] == "5"
    assert result["context_changed"] is False
    assert "loaded_memory" not in result
    assert result["evidence_refs"] == ["keep-evidence"]
    assert result["case_summary"] == "keep summary"


def test_verify_info_restores_saved_context_when_switching_back_to_customer():
    store = InMemoryStore()
    save_customer_context(
        store=store,
        case_id="case_1",
        customer_id="5",
        case_summary="customer 5 duplicate charge was refunded",
        evidence_refs=["ev_5_refund"],
    )
    verify_info = create_verify_info_node(FakeLLM())
    state = {
        "case_id": "case_1",
        "customer_id": "4",
        "verified_customer_id": "4",
        "verification_status": "verified",
        "case_summary": "customer 4 past_due context",
        "evidence_refs": ["ev_4_payment"],
        "messages": [HumanMessage(content="Now check Customer ID 5 again")],
    }

    result = verify_info(state, {"configurable": {"thread_id": "case_1"}}, store)

    assert result["customer_id"] == "5"
    assert result["verified_customer_id"] == "5"
    assert result["context_changed"] is True
    assert result["case_summary"] == "customer 5 duplicate charge was refunded"
    assert result["evidence_refs"] == ["ev_5_refund"]
    assert "customer 5 duplicate charge was refunded" in result["messages"][0].content
    saved_customer_4 = store.get(("customer_context", "case_1"), "4")
    assert saved_customer_4.value["case_summary"] == "customer 4 past_due context"


def test_verify_info_clears_context_when_explicit_new_identifier_is_unknown():
    verify_info = create_verify_info_node(FakeLLM())
    state = {
        "customer_id": "5",
        "verified_customer_id": "5",
        "verification_status": "verified",
        "loaded_memory": "Support Context: old customer",
        "evidence_refs": ["old-evidence"],
        "case_summary": "old summary",
        "messages": [HumanMessage(content="Now check Customer ID 999.")],
    }

    result = verify_info(state, {})

    assert result["customer_id"] is None
    assert result["verified_customer_id"] is None
    assert result["verification_status"] == "verification_failed"
    assert result["context_changed"] is True
    assert result["loaded_memory"] == ""
    assert result["evidence_refs"] == []
    assert result["case_summary"] == ""
    assert result["messages"][0].content == "Please provide a valid customer identifier."
