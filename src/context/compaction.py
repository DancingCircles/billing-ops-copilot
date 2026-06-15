"""Conversation compaction for long-running billing support cases."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import RemoveMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from src.context.customer_context import resolve_case_id, save_customer_context
from src.context.evidence import capture_tool_evidence
from src.state import State


DEFAULT_RECENT_MESSAGE_LIMIT = 12
MAX_SUMMARY_CHARS = 2500
MAX_MESSAGE_SUMMARY_CHARS = 220


def create_context_compaction_node(recent_message_limit: int = DEFAULT_RECENT_MESSAGE_LIMIT):
    """Create a graph node that captures evidence and trims old messages."""

    def compact_context(state: State, config: RunnableConfig, store: BaseStore):
        messages = list(state.get("messages", []))
        customer_id = str(state.get("verified_customer_id") or state.get("customer_id") or "")
        case_id = resolve_case_id(state, config)
        context_changed = bool(state.get("context_changed"))
        keep_start = _latest_human_message_index(messages) if context_changed else 0
        evidence_messages = messages[keep_start:] if context_changed else messages

        updates: dict[str, Any] = {"case_id": case_id}

        evidence_refs = list(state.get("evidence_refs") or [])
        if customer_id:
            captured_refs = capture_tool_evidence(
                store=store,
                case_id=case_id,
                customer_id=customer_id,
                messages=evidence_messages,
                existing_refs=evidence_refs,
            )
            if captured_refs != evidence_refs:
                updates["evidence_refs"] = captured_refs

        if len(messages) <= recent_message_limit and not context_changed:
            if customer_id:
                save_customer_context(
                    store=store,
                    case_id=case_id,
                    customer_id=customer_id,
                    case_summary=state.get("case_summary", ""),
                    evidence_refs=updates.get("evidence_refs", evidence_refs),
                )
            return updates

        if context_changed:
            removable_messages = messages[:keep_start]
            compacted_summary = ""
        else:
            removable_messages = messages[: len(messages) - recent_message_limit]
            compacted_summary = _summarize_messages(removable_messages)

        removals = [RemoveMessage(id=message.id) for message in removable_messages if getattr(message, "id", None)]
        if removals:
            updates["messages"] = removals

        if compacted_summary:
            updates["case_summary"] = _merge_summary(state.get("case_summary", ""), compacted_summary)

        if customer_id:
            save_customer_context(
                store=store,
                case_id=case_id,
                customer_id=customer_id,
                case_summary=updates.get("case_summary", state.get("case_summary", "")),
                evidence_refs=updates.get("evidence_refs", evidence_refs),
            )

        return updates

    return compact_context


def _summarize_messages(messages: list[Any]) -> str:
    lines = []
    for message in messages:
        message_type = getattr(message, "type", "message")
        if message_type == "system":
            continue
        if message_type == "tool":
            tool_name = getattr(message, "name", "") or "tool"
            lines.append(f"tool:{tool_name} result captured as evidence when applicable")
            continue

        content = str(getattr(message, "content", "") or "").strip()
        if not content:
            continue
        content = " ".join(content.split())
        if len(content) > MAX_MESSAGE_SUMMARY_CHARS:
            content = content[: MAX_MESSAGE_SUMMARY_CHARS - 3] + "..."
        lines.append(f"{message_type}: {content}")

    if not lines:
        return ""
    return "\n".join(lines[-20:])


def _latest_human_message_index(messages: list[Any]) -> int:
    for index in range(len(messages) - 1, -1, -1):
        if getattr(messages[index], "type", "") == "human":
            return index
    return max(len(messages) - DEFAULT_RECENT_MESSAGE_LIMIT, 0)


def _merge_summary(existing_summary: str, compacted_summary: str) -> str:
    if existing_summary:
        merged = f"{existing_summary.rstrip()}\n{compacted_summary}"
    else:
        merged = compacted_summary

    if len(merged) <= MAX_SUMMARY_CHARS:
        return merged

    return merged[-MAX_SUMMARY_CHARS:]
