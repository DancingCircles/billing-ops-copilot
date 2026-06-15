"""Runtime context management primitives."""

from src.context.compaction import create_context_compaction_node
from src.context.customer_context import load_customer_context, resolve_case_id, save_customer_context
from src.context.evidence import EvidenceRecord, capture_tool_evidence, summarize_tool_result

__all__ = [
    "EvidenceRecord",
    "capture_tool_evidence",
    "create_context_compaction_node",
    "load_customer_context",
    "resolve_case_id",
    "save_customer_context",
    "summarize_tool_result",
]
