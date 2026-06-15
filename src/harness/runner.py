"""Scripted harness runner for context isolation and evidence checks."""

from __future__ import annotations

import json
from typing import Any

from src.agents.nodes import extract_identifier, get_customer_id_from_identifier
from src.harness.models import (
    HarnessRunResult,
    HarnessScenario,
    HarnessStep,
    HarnessTurnResult,
    ToolCallRecord,
    ToolEvidence,
)
from src.tools.invoice import (
    get_billing_timeline,
    get_invoices_by_customer_sorted_by_date,
    get_payments_by_customer,
    get_refunds_by_customer,
    get_support_tickets_by_customer,
)
from src.tools.subscription_context import (
    get_current_subscription,
    get_customer_profile,
    get_subscription_events,
)


CUSTOMER_SCOPED_TOOLS = {
    "get_customer_profile": get_customer_profile,
    "get_current_subscription": get_current_subscription,
    "get_subscription_events": get_subscription_events,
    "get_invoices_by_customer_sorted_by_date": get_invoices_by_customer_sorted_by_date,
    "get_payments_by_customer": get_payments_by_customer,
    "get_refunds_by_customer": get_refunds_by_customer,
    "get_support_tickets_by_customer": get_support_tickets_by_customer,
    "get_billing_timeline": get_billing_timeline,
}

RECORD_ID_FIELDS = (
    "InvoiceId",
    "InvoiceItemId",
    "PaymentId",
    "RefundId",
    "TicketId",
    "SubscriptionId",
    "EventId",
)


class ScriptedAgentHarness:
    """Runs deterministic scenarios without requiring an LLM provider.

    This harness exercises the context contract that the runtime agent should
    honor: identify the active customer, re-verify on customer changes, and
    keep all customer-scoped tool calls aligned with the verified customer.
    """

    def run(self, scenario: HarnessScenario) -> HarnessRunResult:
        verified_customer_id: str | None = None
        turns: list[HarnessTurnResult] = []

        for step in scenario.steps:
            turn = self._run_step(step, verified_customer_id)
            turns.append(turn)
            verified_customer_id = turn.verified_customer_id_after

        return HarnessRunResult(scenario=scenario, turns=tuple(turns))

    def _run_step(self, step: HarnessStep, current_customer_id: str | None) -> HarnessTurnResult:
        detected_identifier = extract_identifier(step.user_message)
        detected_customer_id = self._resolve_customer_id(detected_identifier)
        next_customer_id = current_customer_id
        reverified = False

        if detected_customer_id and detected_customer_id != current_customer_id:
            next_customer_id = detected_customer_id
            reverified = True

        if step.expected_tools and not next_customer_id:
            return HarnessTurnResult(
                step=step,
                customer_id_before=current_customer_id,
                detected_identifier=detected_identifier,
                detected_customer_id=detected_customer_id,
                verified_customer_id_after=next_customer_id,
                reverified=reverified,
                blocked_reason="customer_not_verified",
            )

        tool_calls = tuple(self._invoke_customer_tool(tool_name, next_customer_id) for tool_name in step.expected_tools)

        return HarnessTurnResult(
            step=step,
            customer_id_before=current_customer_id,
            detected_identifier=detected_identifier,
            detected_customer_id=detected_customer_id,
            verified_customer_id_after=next_customer_id,
            reverified=reverified,
            tool_calls=tool_calls,
        )

    def _resolve_customer_id(self, identifier: str) -> str | None:
        if not identifier:
            return None

        customer_id = get_customer_id_from_identifier(identifier)
        if customer_id is None:
            return None
        return str(customer_id)

    def _invoke_customer_tool(self, tool_name: str, customer_id: str | None) -> ToolCallRecord:
        if tool_name not in CUSTOMER_SCOPED_TOOLS:
            raise ValueError(f"Unsupported harness tool: {tool_name}")
        if not customer_id:
            raise ValueError(f"Cannot invoke {tool_name} without a verified customer")

        arguments = {"customer_id": customer_id}
        result_text = CUSTOMER_SCOPED_TOOLS[tool_name].invoke(arguments)
        evidence = self._summarize_evidence(tool_name, result_text)

        return ToolCallRecord(
            tool_name=tool_name,
            arguments=arguments,
            evidence=evidence,
            result_preview=result_text[:500],
        )

    def _summarize_evidence(self, tool_name: str, result_text: str) -> ToolEvidence:
        rows = self._parse_rows(result_text)
        customer_ids = sorted({str(row["CustomerId"]) for row in rows if row.get("CustomerId") is not None})
        record_ids: dict[str, tuple[Any, ...]] = {}

        for field_name in RECORD_ID_FIELDS:
            values = tuple(row[field_name] for row in rows if row.get(field_name) is not None)
            if values:
                record_ids[field_name] = values

        return ToolEvidence(
            tool_name=tool_name,
            customer_ids=tuple(customer_ids),
            row_count=len(rows),
            record_ids=record_ids,
        )

    def _parse_rows(self, result_text: str) -> list[dict[str, Any]]:
        try:
            parsed = json.loads(result_text)
        except json.JSONDecodeError:
            return []

        if not isinstance(parsed, list):
            return []

        return [row for row in parsed if isinstance(row, dict)]
