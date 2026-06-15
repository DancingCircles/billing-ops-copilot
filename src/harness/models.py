"""Data models for agent harness scenarios and run results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class HarnessStep:
    """One user turn in a repeatable agent evaluation scenario."""

    name: str
    user_message: str
    expected_verified_customer_id: str | None = None
    expected_tools: tuple[str, ...] = ()
    forbidden_customer_ids: tuple[str, ...] = ()
    expected_reverified: bool | None = None


@dataclass(frozen=True)
class HarnessScenario:
    """A multi-turn scenario that exercises context and evidence behavior."""

    name: str
    description: str
    steps: tuple[HarnessStep, ...]


@dataclass(frozen=True)
class ToolEvidence:
    """Structured summary of rows returned by a tool call."""

    tool_name: str
    customer_ids: tuple[str, ...] = ()
    row_count: int = 0
    record_ids: dict[str, tuple[Any, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolCallRecord:
    """A single tool invocation captured by the harness."""

    tool_name: str
    arguments: dict[str, Any]
    evidence: ToolEvidence
    result_preview: str


@dataclass(frozen=True)
class HarnessTurnResult:
    """Observed state for one harness step."""

    step: HarnessStep
    customer_id_before: str | None
    detected_identifier: str
    detected_customer_id: str | None
    verified_customer_id_after: str | None
    reverified: bool
    tool_calls: tuple[ToolCallRecord, ...] = ()
    blocked_reason: str | None = None


@dataclass(frozen=True)
class HarnessRunResult:
    """Complete result for one scenario run."""

    scenario: HarnessScenario
    turns: tuple[HarnessTurnResult, ...]
