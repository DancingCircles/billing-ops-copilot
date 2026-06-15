"""Tests for the FastAPI case management surface."""

from fastapi.testclient import TestClient

from src.api.app import create_api_app
from src.api.case_store import InMemoryCaseStore


class FakeAgentService:
    def run_turn(self, case_id: str, user_message: str):
        return {
            "content": f"Reply for: {user_message}",
            "tools_used": ["billing_evidence"],
            "verified_customer_id": "5",
            "case_summary": "Customer 5 billing summary",
            "evidence_refs": ["ev_5_test"],
        }

    def get_evidence_records(self, case_id: str, customer_id: str | None = None):
        return [
            {
                "evidence_id": "ev_5_test",
                "case_id": case_id,
                "customer_id": customer_id or "5",
                "source_type": "payment",
                "tool_name": "get_payments_by_customer",
                "row_count": 1,
                "customer_ids": ["5"],
                "record_ids": {"PaymentId": [9001]},
                "short_summary": "payment evidence",
            }
        ]


def make_client():
    return TestClient(create_api_app(case_store=InMemoryCaseStore(), agent_service=FakeAgentService()))


def test_case_lifecycle_and_chat_response():
    client = make_client()

    created = client.post("/api/cases", json={"title": "Test case"}).json()
    assert created["title"] == "Test case"
    case_id = created["id"]

    response = client.post(
        f"/api/cases/{case_id}/messages",
        json={"content": "Customer ID is 5"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["assistant_message"]["body"] == "Reply for: Customer ID is 5"
    assert payload["case"]["verified_customer_id"] == "5"
    assert payload["case"]["evidence_refs"] == ["ev_5_test"]
    assert len(payload["case"]["messages"]) == 2

    listed = client.get("/api/cases").json()
    assert listed[0]["id"] == case_id
    assert listed[0]["message_count"] == 2

    evidence = client.get(f"/api/cases/{case_id}/evidence").json()
    assert evidence[0]["evidence_id"] == "ev_5_test"


def test_update_title_and_delete_case():
    client = make_client()
    case_id = client.post("/api/cases", json={"title": "Old title"}).json()["id"]

    renamed = client.patch(f"/api/cases/{case_id}", json={"title": "Renamed case"}).json()
    assert renamed["title"] == "Renamed case"

    deleted = client.delete(f"/api/cases/{case_id}")
    assert deleted.status_code == 204
    assert client.get(f"/api/cases/{case_id}").status_code == 404


def test_rejects_empty_chat_message():
    client = make_client()
    case_id = client.post("/api/cases", json={}).json()["id"]

    response = client.post(f"/api/cases/{case_id}/messages", json={"content": "   "})

    assert response.status_code == 400
