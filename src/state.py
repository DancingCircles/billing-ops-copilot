from typing import Annotated, Optional
from typing_extensions import NotRequired, TypedDict
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.managed.is_last_step import RemainingSteps


class State(TypedDict):
    case_id: NotRequired[Optional[str]]
    customer_id: Optional[str]
    verified_customer_id: NotRequired[Optional[str]]
    verification_status: NotRequired[str]
    context_changed: NotRequired[bool]
    evidence_refs: NotRequired[list[str]]
    case_summary: NotRequired[str]
    messages: Annotated[list[AnyMessage], add_messages]
    loaded_memory: str
    remaining_steps: RemainingSteps
