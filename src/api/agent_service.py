"""Adapter between FastAPI case endpoints and the LangGraph agent."""

from __future__ import annotations

import logging
import time

from langchain_core.messages import AIMessage, HumanMessage

from src.agents.graph import build_graph
from src.config import settings
from src.db.database import verify_database

logger = logging.getLogger(__name__)


class AgentService:
    """Lazy LangGraph wrapper for API chat requests."""

    def __init__(self):
        self._graph = None
        self._store = None

    @property
    def store(self):
        self._ensure_initialized()
        return self._store

    def run_turn(self, case_id: str, user_message: str) -> dict:
        self._ensure_initialized()
        config = {"configurable": {"thread_id": case_id}}
        input_state = {"case_id": case_id, "messages": [HumanMessage(content=user_message)]}

        final_response = None
        tools_used: list[str] = []
        start_time = time.time()

        for event in self._graph.stream(input_state, config=config, stream_mode="updates"):
            for node_name, node_output in event.items():
                logger.info("API graph event: node=%s", node_name)
                if node_name == "subscription_tool_node":
                    tools_used.append("subscription_context")
                elif node_name == "invoice_information_subagent":
                    tools_used.append("billing_evidence")

                if isinstance(node_output, dict) and "messages" in node_output:
                    for message in node_output["messages"]:
                        if isinstance(message, AIMessage) and message.content:
                            final_response = str(message.content)

        snapshot = self._graph.get_state(config)
        values = getattr(snapshot, "values", {}) if snapshot else {}
        if not final_response:
            for message in reversed(values.get("messages", [])):
                if isinstance(message, AIMessage) and message.content:
                    final_response = str(message.content)
                    break

        return {
            "content": final_response or "I wasn't able to generate a response. Please try rephrasing your question.",
            "elapsed": time.time() - start_time,
            "tools_used": sorted(set(tools_used)),
            "verified_customer_id": _string_or_none(values.get("verified_customer_id") or values.get("customer_id")),
            "case_summary": str(values.get("case_summary", "") or ""),
            "evidence_refs": list(values.get("evidence_refs") or []),
        }

    def get_evidence_records(self, case_id: str, customer_id: str | None = None) -> list[dict]:
        self._ensure_initialized()
        records: list[dict] = []
        namespace_prefix = ("case_evidence", case_id)

        if customer_id:
            items = self._store.search((*namespace_prefix, customer_id))
        else:
            items = []
            # InMemoryStore does not expose namespace enumeration cleanly, so evidence
            # retrieval is scoped to the verified customer for now.

        for item in items:
            if item.value:
                records.append(dict(item.value))
        return records

    def _ensure_initialized(self):
        if self._graph is not None:
            return

        db_health = verify_database()
        if db_health.get("status") != "healthy":
            raise RuntimeError(f"Database unhealthy: {db_health}")

        self._graph, _checkpointer, self._store = build_graph(
            model_name=settings.model_name,
            temperature=settings.temperature,
            openai_api_key=settings.openai_api_key or None,
            openai_api_base=settings.openai_api_base or None,
        )


def _string_or_none(value) -> str | None:
    if value is None or value == "":
        return None
    return str(value)
