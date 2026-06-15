"""Evidence capture helpers for customer-scoped tool results."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any

from langgraph.store.base import BaseStore


RECORD_ID_FIELDS = (
    "InvoiceId",
    "InvoiceItemId",
    "PaymentId",
    "RefundId",
    "TicketId",
    "SubscriptionId",
    "EventId",
)


@dataclass(frozen=True)
class EvidenceRecord:
    """A compact index entry for a raw tool result."""

    evidence_id: str
    case_id: str
    customer_id: str
    source_type: str
    tool_name: str
    row_count: int
    customer_ids: tuple[str, ...] = ()
    record_ids: dict[str, tuple[Any, ...]] = field(default_factory=dict)
    short_summary: str = ""
    raw_result: str = ""


def summarize_tool_result(tool_name: str, result_text: str) -> tuple[int, tuple[str, ...], dict[str, tuple[Any, ...]], str]:
    """Return a compact summary of a JSON tool result."""

    rows = _parse_rows(result_text)
    customer_ids = tuple(sorted({str(row["CustomerId"]) for row in rows if row.get("CustomerId") is not None}))
    record_ids: dict[str, tuple[Any, ...]] = {}

    for field_name in RECORD_ID_FIELDS:
        values = tuple(row[field_name] for row in rows if row.get(field_name) is not None)
        if values:
            record_ids[field_name] = values

    parts = [f"{tool_name}: {len(rows)} row(s)"]
    if customer_ids:
        parts.append(f"customer_ids={','.join(customer_ids)}")
    if record_ids:
        compact_ids = []
        for field_name, values in record_ids.items():
            preview = ",".join(str(value) for value in values[:5])
            if len(values) > 5:
                preview += ",..."
            compact_ids.append(f"{field_name}={preview}")
        parts.append("; ".join(compact_ids))

    return len(rows), customer_ids, record_ids, " | ".join(parts)


def capture_tool_evidence(
    *,
    store: BaseStore,
    case_id: str,
    customer_id: str,
    messages: list[Any],
    existing_refs: list[str] | None = None,
) -> list[str]:
    """Persist tool results as evidence records and return evidence IDs."""

    evidence_refs = list(existing_refs or [])
    seen_refs = set(evidence_refs)

    for message in messages:
        if getattr(message, "type", "") != "tool":
            continue

        tool_name = getattr(message, "name", "") or "unknown_tool"
        result_text = str(getattr(message, "content", "") or "")
        if not result_text:
            continue

        evidence_id = _build_evidence_id(case_id, customer_id, tool_name, getattr(message, "tool_call_id", ""), result_text)
        if evidence_id in seen_refs:
            continue

        row_count, customer_ids, record_ids, short_summary = summarize_tool_result(tool_name, result_text)
        if customer_ids and set(customer_ids) != {customer_id}:
            continue

        record = EvidenceRecord(
            evidence_id=evidence_id,
            case_id=case_id,
            customer_id=customer_id,
            source_type=_source_type_from_tool(tool_name),
            tool_name=tool_name,
            row_count=row_count,
            customer_ids=customer_ids,
            record_ids=record_ids,
            short_summary=short_summary,
            raw_result=result_text,
        )
        store.put(_evidence_namespace(case_id, customer_id), evidence_id, asdict(record))
        evidence_refs.append(evidence_id)
        seen_refs.add(evidence_id)

    return evidence_refs


def _parse_rows(result_text: str) -> list[dict[str, Any]]:
    try:
        parsed = json.loads(result_text)
    except json.JSONDecodeError:
        return []

    if not isinstance(parsed, list):
        return []
    return [row for row in parsed if isinstance(row, dict)]


def _build_evidence_id(case_id: str, customer_id: str, tool_name: str, tool_call_id: str, result_text: str) -> str:
    digest_source = f"{case_id}:{customer_id}:{tool_name}:{tool_call_id}:{result_text}"
    digest = hashlib.sha1(digest_source.encode("utf-8")).hexdigest()[:12]
    return f"ev_{customer_id}_{tool_name}_{digest}"


def _evidence_namespace(case_id: str, customer_id: str) -> tuple[str, str, str]:
    return ("case_evidence", case_id, customer_id)


def _source_type_from_tool(tool_name: str) -> str:
    for source_type in ("invoice", "payment", "refund", "ticket", "timeline", "subscription", "customer", "plan"):
        if source_type in tool_name:
            return source_type
    return "tool"
