"""Run deterministic agent harness scenarios."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.harness import DEFAULT_SCENARIOS, ScriptedAgentHarness, assert_scenario_passed  # noqa: E402


def main() -> None:
    harness = ScriptedAgentHarness()

    for scenario in DEFAULT_SCENARIOS:
        result = harness.run(scenario)
        assert_scenario_passed(result)
        print(f"PASS {scenario.name}: {len(result.turns)} turns")


if __name__ == "__main__":
    main()
