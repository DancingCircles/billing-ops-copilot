"""Node functions for the multi-agent graph."""

import logging
import re
from typing import Optional

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore
from langgraph.types import interrupt

from src.state import State
from src.models import UserProfile
from src.agents.prompts import generate_subscription_assistant_prompt, VERIFICATION_PROMPT, CREATE_MEMORY_PROMPT
from src.context.customer_context import load_customer_context, resolve_case_id, save_customer_context
from src.db.database import get_engine, normalize_phone
from src.config import settings

logger = logging.getLogger(__name__)


def extract_explicit_identifier(message: str) -> str:
    """Extract only explicit customer identifiers from a message."""
    if not message:
        return ""

    customer_id_match = re.search(r"\b(?:customer\s*id|customer|id)\s*(?:is|:|#)?\s*(\d+)\b", message, re.I)
    if customer_id_match:
        return customer_id_match.group(1)

    email_match = re.search(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", message)
    if email_match:
        return email_match.group(0)

    phone_match = re.search(r"\+?\d[\d\s().-]{5,}\d", message)
    if phone_match:
        return phone_match.group(0)

    return ""


def extract_identifier(message: str) -> str:
    """Extract a customer identifier without relying on provider-specific JSON mode."""
    if not message:
        return ""

    explicit_identifier = extract_explicit_identifier(message)
    if explicit_identifier:
        return explicit_identifier

    numeric_match = re.search(r"\b\d+\b", message)
    if numeric_match:
        return numeric_match.group(0)

    return ""


def get_verified_customer_id(state: State) -> Optional[str]:
    """Return the canonical verified customer ID from runtime state."""
    verified_customer_id = state.get("verified_customer_id") or state.get("customer_id")
    if verified_customer_id is None:
        return None
    return str(verified_customer_id)


def build_verified_customer_message(
    customer_id: str,
    context_changed: bool = False,
    case_summary: str = "",
    evidence_refs: list[str] | None = None,
) -> SystemMessage:
    """Build the latest system guardrail for customer-scoped tool calls."""
    prefix = "Customer context switched and re-verified." if context_changed else "Customer verified successfully."
    content_parts = [
        (
            f"{prefix} "
            f"The current verified customer ID is: {customer_id}. "
            f"Use ONLY customer_id {customer_id} for all subscription, invoice, payment, refund, and support-ticket "
            f"lookups. Ignore any earlier verified customer_id messages if they mention a different customer."
        )
    ]

    if case_summary:
        content_parts.append(f"Current compacted case summary:\n{case_summary}")

    if evidence_refs:
        content_parts.append(f"Available evidence refs for this customer: {', '.join(evidence_refs[-10:])}")

    content_parts.append(
        "Default to Simplified Chinese for assistant-facing responses in this local demo unless the user asks "
        "for another language. Do not use emoji or decorative symbols."
    )
    return SystemMessage(content="\n\n".join(content_parts))


def get_customer_id_from_identifier(identifier: str) -> Optional[int]:
    if not identifier or not identifier.strip():
        return None

    identifier = identifier.strip()
    engine = get_engine()

    try:
        from sqlalchemy import text

        if "@" in identifier:
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT CustomerId FROM Customer WHERE LOWER(Email) = LOWER(:email)"),
                    {"email": identifier},
                )
                row = result.fetchone()
                if row:
                    return int(row[0])

        if identifier.isdigit():
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT CustomerId FROM Customer WHERE CustomerId = :cid"),
                    {"cid": int(identifier)},
                )
                row = result.fetchone()
                if row:
                    return int(row[0])

        normalized_input = normalize_phone(identifier)
        if normalized_input and len(normalized_input) >= 5:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT CustomerId, Phone FROM Customer WHERE Phone IS NOT NULL"))
                for row in result:
                    db_phone_normalized = normalize_phone(str(row[1]))
                    if db_phone_normalized == normalized_input:
                        return int(row[0])

    except Exception as e:
        logger.error(f"Error looking up customer by identifier '{identifier}': {e}")

    return None


def format_user_memory(user_data: dict) -> str:
    try:
        profile = user_data.get("memory")
        if profile and hasattr(profile, "support_preferences") and profile.support_preferences:
            return f"Support Context: {', '.join(profile.support_preferences)}"
    except Exception as e:
        logger.error(f"Error formatting user memory: {e}")
    return ""


def create_subscription_assistant_node(llm, subscription_tools):
    llm_with_tools = llm.bind_tools(subscription_tools)

    def subscription_assistant(state: State, config: RunnableConfig):
        memory = state.get("loaded_memory", "None") or "None"
        prompt = generate_subscription_assistant_prompt(memory)

        messages = [SystemMessage(content=prompt)]
        verified_customer_id = get_verified_customer_id(state)
        if verified_customer_id:
            messages.append(
                SystemMessage(content=f"The current verified customer ID is: {verified_customer_id}")
            )
        messages.extend(state["messages"])

        logger.info(f"Subscription context assistant invoked with {len(state['messages'])} conversation messages")
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    return subscription_assistant


def should_continue(state: State, config: RunnableConfig) -> str:
    messages = state["messages"]
    last_message = messages[-1]
    if not last_message.tool_calls:
        return "end"
    return "continue"


def should_interrupt(state: State, config: RunnableConfig) -> str:
    if get_verified_customer_id(state) is not None:
        return "continue"
    return "interrupt"


def create_verify_info_node(llm):
    def verify_info(state: State, config: RunnableConfig, store: BaseStore | None = None):
        user_input = state["messages"][-1]
        user_content = getattr(user_input, "content", "")
        logger.info(f"Verification attempt with message: {user_content[:100]}")

        case_id = resolve_case_id(state, config)
        current_customer_id = get_verified_customer_id(state)
        identifier = (
            extract_explicit_identifier(str(user_content))
            if current_customer_id is not None
            else extract_identifier(str(user_content))
        )
        logger.info(f"Extracted identifier: '{identifier}'")

        customer_id = None
        if identifier:
            customer_id = get_customer_id_from_identifier(identifier)
            logger.info(f"DB lookup result: customer_id={customer_id}")

        if customer_id is not None:
            verified_customer_id = str(customer_id)
            context_changed = current_customer_id is not None and current_customer_id != verified_customer_id
            should_reset_context = current_customer_id is None or context_changed
            if context_changed and current_customer_id:
                save_customer_context(
                    store=store,
                    case_id=case_id,
                    customer_id=current_customer_id,
                    case_summary=state.get("case_summary", ""),
                    evidence_refs=list(state.get("evidence_refs") or []),
                )

            if current_customer_id == verified_customer_id:
                restored_summary = str(state.get("case_summary", ""))
                restored_evidence_refs = list(state.get("evidence_refs") or [])
            else:
                restored_context = load_customer_context(
                    store=store,
                    case_id=case_id,
                    customer_id=verified_customer_id,
                )
                restored_summary = str(restored_context.get("case_summary", ""))
                restored_evidence_refs = list(restored_context.get("evidence_refs") or [])
            logger.info(
                "Customer verified: current=%s, next=%s, context_changed=%s, restored_refs=%s",
                current_customer_id,
                verified_customer_id,
                context_changed,
                len(restored_evidence_refs),
            )
            result = {
                "case_id": case_id,
                "customer_id": verified_customer_id,
                "verified_customer_id": verified_customer_id,
                "verification_status": "verified",
                "context_changed": context_changed,
                "case_summary": restored_summary,
                "evidence_refs": restored_evidence_refs,
                "messages": [
                    build_verified_customer_message(
                        verified_customer_id,
                        context_changed,
                        restored_summary,
                        restored_evidence_refs,
                    )
                ],
            }
            if should_reset_context:
                result["loaded_memory"] = ""
            return result

        if current_customer_id is not None and not identifier:
            logger.info(f"Continuing with verified customer: {current_customer_id}")
            return {
                "customer_id": current_customer_id,
                "verified_customer_id": current_customer_id,
                "verification_status": "verified",
                "context_changed": False,
                "messages": [
                    build_verified_customer_message(
                        current_customer_id,
                        case_summary=state.get("case_summary", ""),
                        evidence_refs=list(state.get("evidence_refs") or []),
                    )
                ],
            }

        if current_customer_id is not None and identifier:
            logger.info("Explicit customer identifier did not match a known account; clearing active context.")
            response = llm.invoke([SystemMessage(content=VERIFICATION_PROMPT)] + state["messages"])
            return {
                "case_id": case_id,
                "customer_id": None,
                "verified_customer_id": None,
                "verification_status": "verification_failed",
                "context_changed": True,
                "loaded_memory": "",
                "evidence_refs": [],
                "case_summary": "",
                "messages": [response],
            }
        else:
            response = llm.invoke(
                [SystemMessage(content=VERIFICATION_PROMPT)] + state["messages"]
            )
            return {"verification_status": "unverified", "context_changed": False, "messages": [response]}

    return verify_info


def human_input(state: State, config: RunnableConfig):
    user_input = interrupt("Please provide input.")
    return {"messages": [HumanMessage(content=user_input)]}


def load_memory(state: State, config: RunnableConfig, store: BaseStore):
    user_id = str(get_verified_customer_id(state) or "")
    if not user_id:
        return {"loaded_memory": ""}

    namespace = ("memory_profile", user_id)
    try:
        existing_memory = store.get(namespace, "user_memory")
        if existing_memory and existing_memory.value:
            formatted = format_user_memory(existing_memory.value)
            logger.info(f"Loaded memory for customer {user_id}: {formatted}")
            return {"loaded_memory": formatted}
    except Exception as e:
        logger.error(f"Error loading memory for user {user_id}: {e}")

    return {"loaded_memory": ""}


def create_memory_node(llm):
    def create_memory(state: State, config: RunnableConfig, store: BaseStore):
        if "deepseek" in settings.openai_api_base.lower():
            logger.info("Skipping structured memory update for DeepSeek provider.")
            return {}

        user_id = str(get_verified_customer_id(state) or "")
        if not user_id:
            return {}

        namespace = ("memory_profile", user_id)

        try:
            existing_preferences = []
            existing_memory = store.get(namespace, "user_memory")
            formatted_memory = ""
            if existing_memory and existing_memory.value:
                mem_dict = existing_memory.value
                profile = mem_dict.get("memory")
                if profile and hasattr(profile, "support_preferences"):
                    existing_preferences = list(profile.support_preferences or [])
                    formatted_memory = f"Support Context: {', '.join(existing_preferences)}"

            recent_messages = state["messages"][-10:]
            conversation_summary = "\n".join(
                f"{getattr(msg, 'type', 'unknown')}: {getattr(msg, 'content', '')}"
                for msg in recent_messages
                if getattr(msg, "content", "")
            )

            formatted_prompt = CREATE_MEMORY_PROMPT.format(
                conversation=conversation_summary,
                memory_profile=formatted_memory or "Empty, no existing profile",
            )

            updated_memory = llm.with_structured_output(UserProfile).invoke(
                [SystemMessage(content=formatted_prompt)]
            )

            new_prefs = updated_memory.support_preferences or []
            if not new_prefs and existing_preferences:
                logger.info(f"Memory unchanged for customer {user_id} (preserving existing preferences)")
                return {}

            merged_prefs = list(set(existing_preferences + new_prefs))
            updated_memory.support_preferences = merged_prefs
            updated_memory.customer_id = user_id

            store.put(namespace, "user_memory", {"memory": updated_memory})
            logger.info(f"Memory updated for customer {user_id}: {merged_prefs}")

        except Exception as e:
            logger.error(f"Error creating/updating memory for user {user_id}: {e}")

    return create_memory
