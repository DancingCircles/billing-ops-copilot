"""Tests for the deterministic agent harness."""

import pytest

from src.harness import DEFAULT_SCENARIOS, ScriptedAgentHarness, assert_scenario_passed
from src.harness.assertions import _validate_turn
from src.harness.models import HarnessScenario, HarnessStep


@pytest.mark.parametrize("scenario", DEFAULT_SCENARIOS, ids=lambda scenario: scenario.name)
def test_default_harness_scenarios_pass(scenario):
    result = ScriptedAgentHarness().run(scenario)

    assert_scenario_passed(result)


def test_customer_switch_reverifies_and_rescopes_tools():
    scenario = next(item for item in DEFAULT_SCENARIOS if item.name == "customer_switch_requires_reverification")
    result = ScriptedAgentHarness().run(scenario)
    switch_turn = result.turns[1]

    assert switch_turn.customer_id_before == "5"
    assert switch_turn.verified_customer_id_after == "4"
    assert switch_turn.reverified is True
    assert {tool_call.arguments["customer_id"] for tool_call in switch_turn.tool_calls} == {"4"}


def test_harness_detects_forbidden_customer_tool_use():
    scenario = HarnessScenario(
        name="forbidden_customer_guard",
        description="A deliberately strict scenario that forbids the active customer.",
        steps=(
            HarnessStep(
                name="verify_and_call",
                user_message="Customer ID is 5",
                expected_verified_customer_id="5",
                expected_tools=("get_customer_profile",),
                forbidden_customer_ids=("5",),
            ),
        ),
    )
    result = ScriptedAgentHarness().run(scenario)

    with pytest.raises(AssertionError, match="forbidden customer"):
        assert_scenario_passed(result)


def test_validate_turn_reports_missing_expected_tool():
    scenario = HarnessScenario(
        name="missing_tool_guard",
        description="A scenario whose expected tool list is intentionally edited after the run.",
        steps=(
            HarnessStep(
                name="verify_only",
                user_message="Customer ID is 5",
                expected_verified_customer_id="5",
            ),
        ),
    )
    result = ScriptedAgentHarness().run(scenario)
    edited_step = HarnessStep(
        name="verify_only",
        user_message="Customer ID is 5",
        expected_verified_customer_id="5",
        expected_tools=("get_customer_profile",),
    )
    edited_turn = result.turns[0].__class__(
        step=edited_step,
        customer_id_before=result.turns[0].customer_id_before,
        detected_identifier=result.turns[0].detected_identifier,
        detected_customer_id=result.turns[0].detected_customer_id,
        verified_customer_id_after=result.turns[0].verified_customer_id_after,
        reverified=result.turns[0].reverified,
        tool_calls=result.turns[0].tool_calls,
        blocked_reason=result.turns[0].blocked_reason,
    )

    assert any("missing expected tools" in error for error in _validate_turn(1, edited_turn))
