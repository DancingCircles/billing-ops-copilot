"""In-memory case and message store for the React API."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.api.models import CaseDetail, CaseSummary, ChatMessage


@dataclass
class CaseRecord:
    id: str
    title: str
    created_at: str
    updated_at: str
    messages: list[ChatMessage] = field(default_factory=list)
    verified_customer_id: str | None = None
    case_summary: str = ""
    evidence_refs: list[str] = field(default_factory=list)


class InMemoryCaseStore:
    """A simple process-local case store.

    This intentionally starts as an in-memory store while the API and frontend
    workflow settle. It can be swapped for SQLite/Postgres later without
    changing the React contract.
    """

    def __init__(self):
        self._cases: dict[str, CaseRecord] = {}
        self._order: list[str] = []

    def list_cases(self) -> list[CaseSummary]:
        return [self._to_summary(self._cases[case_id]) for case_id in self._order if case_id in self._cases]

    def create_case(self, title: str | None = None) -> CaseDetail:
        now = _now_iso()
        case_id = str(uuid.uuid4())
        record = CaseRecord(
            id=case_id,
            title=(title or "New billing case").strip() or "New billing case",
            created_at=now,
            updated_at=now,
        )
        self._cases[case_id] = record
        self._order.insert(0, case_id)
        return self._to_detail(record)

    def get_case(self, case_id: str) -> CaseDetail | None:
        record = self._cases.get(case_id)
        if not record:
            return None
        return self._to_detail(record)

    def update_title(self, case_id: str, title: str) -> CaseDetail | None:
        record = self._cases.get(case_id)
        if not record:
            return None
        record.title = title.strip() or "Untitled case"
        record.updated_at = _now_iso()
        return self._to_detail(record)

    def delete_case(self, case_id: str) -> bool:
        if case_id not in self._cases:
            return False
        del self._cases[case_id]
        self._order = [item for item in self._order if item != case_id]
        return True

    def add_message(self, case_id: str, role: str, body: str) -> ChatMessage | None:
        record = self._cases.get(case_id)
        if not record:
            return None
        message = ChatMessage(
            id=str(uuid.uuid4()),
            role=role,
            body=body,
            created_at=_now_iso(),
        )
        record.messages.append(message)
        record.updated_at = message.created_at
        if role == "user" and record.title == "New billing case":
            record.title = _title_from_message(body)
        return message

    def update_runtime_context(
        self,
        case_id: str,
        *,
        verified_customer_id: str | None = None,
        case_summary: str = "",
        evidence_refs: list[str] | None = None,
    ) -> CaseDetail | None:
        record = self._cases.get(case_id)
        if not record:
            return None
        record.verified_customer_id = verified_customer_id
        record.case_summary = case_summary or ""
        record.evidence_refs = list(evidence_refs or [])
        record.updated_at = _now_iso()
        return self._to_detail(record)

    def _to_summary(self, record: CaseRecord) -> CaseSummary:
        return CaseSummary(
            id=record.id,
            title=record.title,
            group=_group_for_timestamp(record.updated_at),
            created_at=record.created_at,
            updated_at=record.updated_at,
            verified_customer_id=record.verified_customer_id,
            message_count=len(record.messages),
        )

    def _to_detail(self, record: CaseRecord) -> CaseDetail:
        return CaseDetail(
            **self._to_summary(record).model_dump(),
            messages=list(record.messages),
            case_summary=record.case_summary,
            evidence_refs=list(record.evidence_refs),
        )


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _title_from_message(message: str) -> str:
    title = " ".join(message.strip().split())
    if not title:
        return "Untitled case"
    return title[:42] + ("..." if len(title) > 42 else "")


def _group_for_timestamp(timestamp: str) -> str:
    try:
        updated = datetime.fromisoformat(timestamp)
    except ValueError:
        return "Earlier"

    now = datetime.now(UTC)
    delta = now.date() - updated.date()
    if delta.days <= 0:
        return "Today"
    if delta.days == 1:
        return "Yesterday"
    if delta.days <= 7:
        return "Last 7 days"
    return "Last 30 days"
