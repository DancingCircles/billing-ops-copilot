"""API models for cases, chat messages, and evidence."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    id: str
    role: str
    body: str
    created_at: str


class CaseSummary(BaseModel):
    id: str
    title: str
    group: str
    created_at: str
    updated_at: str
    verified_customer_id: str | None = None
    message_count: int = 0


class CaseDetail(CaseSummary):
    messages: list[ChatMessage] = Field(default_factory=list)
    case_summary: str = ""
    evidence_refs: list[str] = Field(default_factory=list)


class CreateCaseRequest(BaseModel):
    title: str | None = None


class UpdateCaseRequest(BaseModel):
    title: str


class SendMessageRequest(BaseModel):
    content: str


class SendMessageResponse(BaseModel):
    case: CaseDetail
    assistant_message: ChatMessage
    tools_used: list[str] = Field(default_factory=list)
    verified_customer_id: str | None = None


class EvidenceRecordResponse(BaseModel):
    evidence_id: str
    case_id: str
    customer_id: str
    source_type: str
    tool_name: str
    row_count: int
    customer_ids: list[str] = Field(default_factory=list)
    record_ids: dict[str, list] = Field(default_factory=dict)
    short_summary: str = ""
