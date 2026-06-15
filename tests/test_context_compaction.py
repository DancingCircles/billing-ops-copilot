"""Tests for evidence capture and context compaction."""

import json

from langchain_core.messages import HumanMessage, RemoveMessage, ToolMessage
from langgraph.store.memory import InMemoryStore

from src.context.compaction import create_context_compaction_node
from src.context.evidence import capture_tool_evidence, summarize_tool_result


def test_summarize_tool_result_extracts_customer_and_record_ids():
    result_text = json.dumps(
        [
            {"CustomerId": 5, "InvoiceId": 5403, "Total": 266.68},
            {"CustomerId": 5, "InvoiceId": 5404, "Total": 0},
        ]
    )

    row_count, customer_ids, record_ids, summary = summarize_tool_result(
        "get_invoices_by_customer_sorted_by_date",
        result_text,
    )

    assert row_count == 2
    assert customer_ids == ("5",)
    assert record_ids["InvoiceId"] == (5403, 5404)
    assert "2 row(s)" in summary
    assert "InvoiceId=5403,5404" in summary


def test_capture_tool_evidence_persists_record_and_returns_ref():
    store = InMemoryStore()
    tool_message = ToolMessage(
        content=json.dumps([{"CustomerId": 5, "PaymentId": 9001, "Status": "succeeded"}]),
        name="get_payments_by_customer",
        tool_call_id="call_1",
        id="tool_1",
    )

    refs = capture_tool_evidence(
        store=store,
        case_id="case_1",
        customer_id="5",
        messages=[tool_message],
    )

    assert len(refs) == 1
    stored = store.get(("case_evidence", "case_1", "5"), refs[0])
    assert stored is not None
    assert stored.value["customer_id"] == "5"
    assert stored.value["tool_name"] == "get_payments_by_customer"
    assert stored.value["record_ids"]["PaymentId"] == (9001,)


def test_capture_tool_evidence_skips_mismatched_customer_rows():
    store = InMemoryStore()
    tool_message = ToolMessage(
        content=json.dumps([{"CustomerId": 5, "PaymentId": 9001, "Status": "succeeded"}]),
        name="get_payments_by_customer",
        tool_call_id="call_1",
        id="tool_1",
    )

    refs = capture_tool_evidence(
        store=store,
        case_id="case_1",
        customer_id="4",
        messages=[tool_message],
    )

    assert refs == []


def test_compaction_node_captures_evidence_and_removes_old_messages():
    store = InMemoryStore()
    messages = [
        HumanMessage(content=f"message {index}", id=f"msg_{index}")
        for index in range(5)
    ]
    messages.append(
        ToolMessage(
            content=json.dumps([{"CustomerId": 5, "RefundId": 7001, "Amount": 266.68}]),
            name="get_refunds_by_customer",
            tool_call_id="call_refund",
            id="tool_refund",
        )
    )
    messages.extend(HumanMessage(content=f"recent {index}", id=f"recent_{index}") for index in range(5))
    compact_context = create_context_compaction_node(recent_message_limit=6)

    updates = compact_context(
        {
            "case_id": "case_1",
            "customer_id": "5",
            "verified_customer_id": "5",
            "messages": messages,
            "loaded_memory": "",
        },
        {"configurable": {"thread_id": "case_1"}},
        store,
    )

    assert updates["case_id"] == "case_1"
    assert len(updates["evidence_refs"]) == 1
    assert "case_summary" in updates
    assert "message 0" in updates["case_summary"]
    assert all(isinstance(message, RemoveMessage) for message in updates["messages"])
    assert len(updates["messages"]) == len(messages) - 6
    saved_context = store.get(("customer_context", "case_1"), "5")
    assert saved_context.value["evidence_refs"] == updates["evidence_refs"]
    assert "message 0" in saved_context.value["case_summary"]


def test_compaction_node_saves_customer_context_without_message_trimming():
    store = InMemoryStore()
    messages = [
        HumanMessage(content="Customer ID is 5", id="human_1"),
        ToolMessage(
            content=json.dumps([{"CustomerId": 5, "InvoiceId": 5403}]),
            name="get_invoices_by_customer_sorted_by_date",
            tool_call_id="invoice_call",
            id="invoice_tool",
        ),
    ]
    compact_context = create_context_compaction_node(recent_message_limit=12)

    updates = compact_context(
        {
            "case_id": "case_1",
            "customer_id": "5",
            "verified_customer_id": "5",
            "case_summary": "existing customer 5 summary",
            "messages": messages,
            "loaded_memory": "",
        },
        {"configurable": {"thread_id": "case_1"}},
        store,
    )

    assert "messages" not in updates
    saved_context = store.get(("customer_context", "case_1"), "5")
    assert saved_context.value["case_summary"] == "existing customer 5 summary"
    assert saved_context.value["evidence_refs"] == updates["evidence_refs"]


def test_compaction_node_does_not_summarize_old_customer_messages_after_switch():
    store = InMemoryStore()
    messages = [
        HumanMessage(content="Customer ID is 5", id="old_human"),
        ToolMessage(
            content=json.dumps([{"CustomerId": 5, "PaymentId": 9001}]),
            name="get_payments_by_customer",
            tool_call_id="old_tool",
            id="old_tool_msg",
        ),
        HumanMessage(content="Now check Customer ID 4", id="new_human"),
        ToolMessage(
            content=json.dumps([{"CustomerId": 4, "PaymentId": 8001}]),
            name="get_payments_by_customer",
            tool_call_id="new_tool",
            id="new_tool_msg",
        ),
    ]
    compact_context = create_context_compaction_node(recent_message_limit=12)

    updates = compact_context(
        {
            "case_id": "case_1",
            "customer_id": "4",
            "verified_customer_id": "4",
            "context_changed": True,
            "messages": messages,
            "loaded_memory": "",
        },
        {"configurable": {"thread_id": "case_1"}},
        store,
    )

    assert "case_summary" not in updates
    assert len(updates["messages"]) == 2
    assert all(isinstance(message, RemoveMessage) for message in updates["messages"])
    assert len(updates["evidence_refs"]) == 1
    stored = store.get(("case_evidence", "case_1", "4"), updates["evidence_refs"][0])
    assert stored.value["record_ids"]["PaymentId"] == (8001,)


def test_compaction_node_ignores_old_unscoped_tool_results_after_switch():
    store = InMemoryStore()
    messages = [
        HumanMessage(content="Customer ID is 5", id="old_human"),
        ToolMessage(
            content=json.dumps([{"PlanId": 1, "PlanName": "Basic"}]),
            name="list_subscription_plans",
            tool_call_id="old_unscoped_tool",
            id="old_unscoped_tool_msg",
        ),
        HumanMessage(content="Now check Customer ID 4", id="new_human"),
        ToolMessage(
            content=json.dumps([{"CustomerId": 4, "PaymentId": 8001}]),
            name="get_payments_by_customer",
            tool_call_id="new_tool",
            id="new_tool_msg",
        ),
    ]
    compact_context = create_context_compaction_node(recent_message_limit=12)

    updates = compact_context(
        {
            "case_id": "case_1",
            "customer_id": "4",
            "verified_customer_id": "4",
            "context_changed": True,
            "messages": messages,
            "loaded_memory": "",
        },
        {"configurable": {"thread_id": "case_1"}},
        store,
    )

    assert len(updates["evidence_refs"]) == 1
    stored = store.get(("case_evidence", "case_1", "4"), updates["evidence_refs"][0])
    assert stored.value["tool_name"] == "get_payments_by_customer"
