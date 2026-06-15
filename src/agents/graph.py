"""Graph builder module. Assembles the complete multi-agent LangGraph workflow."""

import logging

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, create_react_agent
from langgraph.store.memory import InMemoryStore

from src.agents.nodes import (
    create_memory_node,
    create_subscription_assistant_node,
    create_verify_info_node,
    human_input,
    load_memory,
    should_continue,
    should_interrupt,
)
from src.agents.prompts import INVOICE_SUBAGENT_PROMPT, SUPERVISOR_PROMPT
from src.config import settings
from src.context import create_context_compaction_node
from src.state import State
from src.tools import invoice_tools, subscription_tools

logger = logging.getLogger(__name__)


def build_graph(
    model_name: str = "gpt-4o-mini",
    temperature: float = 0,
    openai_api_key: str = None,
    openai_api_base: str = None,
):
    llm_kwargs = {
        "model": model_name,
        "temperature": temperature,
    }
    if openai_api_key:
        llm_kwargs["api_key"] = openai_api_key
    if openai_api_base:
        llm_kwargs["base_url"] = openai_api_base
    if openai_api_base and "deepseek" in openai_api_base.lower():
        llm_kwargs["extra_body"] = {"thinking": {"type": "disabled"}}

    llm = ChatOpenAI(**llm_kwargs)
    logger.info(f"LLM initialized: {model_name}, temperature={temperature}")

    # Both stores are in-memory only; all data is lost on restart.
    in_memory_store = InMemoryStore()
    checkpointer = MemorySaver()

    subscription_assistant_fn = create_subscription_assistant_node(llm, subscription_tools)
    subscription_tool_node = ToolNode(subscription_tools)

    subscription_workflow = StateGraph(State)
    subscription_workflow.add_node("subscription_assistant", subscription_assistant_fn)
    subscription_workflow.add_node("subscription_tool_node", subscription_tool_node)
    subscription_workflow.add_edge(START, "subscription_assistant")
    subscription_workflow.add_conditional_edges(
        "subscription_assistant",
        should_continue,
        {"continue": "subscription_tool_node", "end": END},
    )
    subscription_workflow.add_edge("subscription_tool_node", "subscription_assistant")

    subscription_context_subagent = subscription_workflow.compile(
        name="subscription_context_subagent",
        checkpointer=checkpointer,
        store=in_memory_store,
    )
    logger.info("Subscription context sub-agent compiled.")

    invoice_information_subagent = create_react_agent(
        llm,
        tools=invoice_tools,
        name="invoice_information_subagent",
        prompt=INVOICE_SUBAGENT_PROMPT,
        state_schema=State,
        checkpointer=checkpointer,
        store=in_memory_store,
    )
    logger.info("Invoice information sub-agent compiled.")

    from langgraph_supervisor import create_supervisor

    supervisor_workflow = create_supervisor(
        agents=[invoice_information_subagent, subscription_context_subagent],
        output_mode="last_message",
        model=llm,
        prompt=SUPERVISOR_PROMPT,
        state_schema=State,
    )
    supervisor_prebuilt = supervisor_workflow.compile(
        name="supervisor",
        checkpointer=checkpointer,
        store=in_memory_store,
    )
    logger.info("Supervisor compiled.")

    verify_info_fn = create_verify_info_node(llm)
    create_memory_fn = create_memory_node(llm)
    compact_context_fn = create_context_compaction_node(settings.recent_message_limit)

    multi_agent = StateGraph(State)
    multi_agent.add_node("verify_info", verify_info_fn)
    multi_agent.add_node("human_input", human_input)
    multi_agent.add_node("load_memory", load_memory)
    multi_agent.add_node("supervisor", supervisor_prebuilt)
    multi_agent.add_node("create_memory", create_memory_fn)
    multi_agent.add_node("compact_context", compact_context_fn)

    multi_agent.add_edge(START, "verify_info")
    multi_agent.add_conditional_edges(
        "verify_info",
        should_interrupt,
        {"continue": "load_memory", "interrupt": "human_input"},
    )
    multi_agent.add_edge("human_input", "verify_info")
    multi_agent.add_edge("load_memory", "supervisor")
    multi_agent.add_edge("supervisor", "create_memory")
    multi_agent.add_edge("create_memory", "compact_context")
    multi_agent.add_edge("compact_context", END)

    compiled_graph = multi_agent.compile(
        name="multi_agent_final",
        checkpointer=checkpointer,
        store=in_memory_store,
    )
    logger.info("Final multi-agent graph compiled successfully.")

    return compiled_graph, checkpointer, in_memory_store
