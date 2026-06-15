"""Assertions for agent harness run results."""

from __future__ import annotations

from src.harness.models import HarnessRunResult, HarnessTurnResult


def assert_scenario_passed(result: HarnessRunResult) -> None:
    """Raise AssertionError when a scenario violates the context contract."""

    errors: list[str] = []
    for turn_index, turn in enumerate(result.turns, start=1):
        errors.extend(_validate_turn(turn_index, turn))

    if errors:
        scenario_name = result.scenario.name
        details = "\n".join(f"- {error}" for error in errors)
        raise AssertionError(f"Harness scenario failed: {scenario_name}\n{details}")


def _validate_turn(turn_index: int, turn: HarnessTurnResult) -> list[str]:
    errors: list[str] = []
    step = turn.step

    if step.expected_verified_customer_id and turn.verified_customer_id_after != step.expected_verified_customer_id:
        errors.append(
            f"turn {turn_index} expected verified customer {step.expected_verified_customer_id}, "
            f"got {turn.verified_customer_id_after}"
        )

    if step.expected_reverified is not None and turn.reverified != step.expected_reverified:
        errors.append(f"turn {turn_index} expected reverified={step.expected_reverified}, got {turn.reverified}")

    observed_tools = {tool_call.tool_name for tool_call in turn.tool_calls}
    missing_tools = set(step.expected_tools) - observed_tools
    if missing_tools:
        errors.append(f"turn {turn_index} missing expected tools: {', '.join(sorted(missing_tools))}")

    if step.expected_tools and turn.blocked_reason:
        errors.append(f"turn {turn_index} blocked before expected tool calls: {turn.blocked_reason}")

    expected_customer = step.expected_verified_customer_id or turn.verified_customer_id_after
    forbidden_customer_ids = set(step.forbidden_customer_ids)

    for tool_call in turn.tool_calls:
        argument_customer_id = str(tool_call.arguments.get("customer_id", ""))
        if expected_customer and argument_customer_id != expected_customer:
            errors.append(
                f"turn {turn_index} tool {tool_call.tool_name} used customer {argument_customer_id}, "
                f"expected {expected_customer}"
            )

        if argument_customer_id in forbidden_customer_ids:
            errors.append(f"turn {turn_index} tool {tool_call.tool_name} used forbidden customer {argument_customer_id}")

        leaked_customer_ids = set(tool_call.evidence.customer_ids) & forbidden_customer_ids
        if leaked_customer_ids:
            leaked = ", ".join(sorted(leaked_customer_ids))
            errors.append(f"turn {turn_index} tool {tool_call.tool_name} returned forbidden customer evidence: {leaked}")

    return errors
