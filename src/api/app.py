"""FastAPI app for the React billing operations UI."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.api.agent_service import AgentService
from src.api.case_store import InMemoryCaseStore
from src.api.models import (
    CaseDetail,
    CaseSummary,
    CreateCaseRequest,
    EvidenceRecordResponse,
    SendMessageRequest,
    SendMessageResponse,
    UpdateCaseRequest,
)
from src.config import settings


def create_api_app(
    *,
    case_store: InMemoryCaseStore | None = None,
    agent_service: AgentService | None = None,
) -> FastAPI:
    app = FastAPI(title="Billing Ops Copilot API")
    app.state.case_store = case_store or InMemoryCaseStore()
    app.state.agent_service = agent_service or AgentService()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin, "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/cases", response_model=list[CaseSummary])
    def list_cases():
        return app.state.case_store.list_cases()

    @app.post("/api/cases", response_model=CaseDetail)
    def create_case(payload: CreateCaseRequest | None = None):
        return app.state.case_store.create_case((payload.title if payload else None))

    @app.get("/api/cases/{case_id}", response_model=CaseDetail)
    def get_case(case_id: str):
        case = app.state.case_store.get_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        return case

    @app.patch("/api/cases/{case_id}", response_model=CaseDetail)
    def update_case(case_id: str, payload: UpdateCaseRequest):
        case = app.state.case_store.update_title(case_id, payload.title)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        return case

    @app.delete("/api/cases/{case_id}", status_code=204)
    def delete_case(case_id: str):
        deleted = app.state.case_store.delete_case(case_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Case not found")
        return None

    @app.post("/api/cases/{case_id}/messages", response_model=SendMessageResponse)
    def send_message(case_id: str, payload: SendMessageRequest):
        case = app.state.case_store.get_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        content = payload.content.strip()
        if not content:
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        app.state.case_store.add_message(case_id, "user", content)
        result = app.state.agent_service.run_turn(case_id, content)
        assistant_message = app.state.case_store.add_message(case_id, "assistant", result["content"])
        updated_case = app.state.case_store.update_runtime_context(
            case_id,
            verified_customer_id=result.get("verified_customer_id"),
            case_summary=result.get("case_summary", ""),
            evidence_refs=result.get("evidence_refs", []),
        )
        return SendMessageResponse(
            case=updated_case,
            assistant_message=assistant_message,
            tools_used=result.get("tools_used", []),
            verified_customer_id=result.get("verified_customer_id"),
        )

    @app.get("/api/cases/{case_id}/evidence", response_model=list[EvidenceRecordResponse])
    def list_evidence(case_id: str):
        case = app.state.case_store.get_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        if not case.verified_customer_id:
            return []
        return app.state.agent_service.get_evidence_records(case_id, case.verified_customer_id)

    return app
