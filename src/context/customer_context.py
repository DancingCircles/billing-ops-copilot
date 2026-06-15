"""Per-customer runtime context cache for a case."""

from __future__ import annotations

from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore


def resolve_case_id(state: dict[str, Any], config: RunnableConfig) -> str:
    """Resolve a stable case ID from graph state or runnable config."""

    if state.get("case_id"):
        return str(state["case_id"])

    configurable = (config or {}).get("configurable", {})
    if configurable.get("thread_id"):
        return str(configurable["thread_id"])

    return "default_case"


def save_customer_context(
    *,
    store: BaseStore | None,
    case_id: str,
    customer_id: str,
    case_summary: str = "",
    evidence_refs: list[str] | None = None,
) -> None:
    """Persist the current compacted context for one customer inside one case."""

    if not store or not case_id or not customer_id:
        return

    context = {
        "case_id": case_id,
        "customer_id": customer_id,
        "case_summary": case_summary or "",
        "evidence_refs": list(evidence_refs or []),
    }
    store.put(_customer_context_namespace(case_id), customer_id, context)


def load_customer_context(
    *,
    store: BaseStore | None,
    case_id: str,
    customer_id: str,
) -> dict[str, Any]:
    """Load saved context for one customer inside one case."""

    if not store or not case_id or not customer_id:
        return {}

    stored = store.get(_customer_context_namespace(case_id), customer_id)
    if not stored or not stored.value:
        return {}

    return dict(stored.value)


def _customer_context_namespace(case_id: str) -> tuple[str, str]:
    return ("customer_context", case_id)
