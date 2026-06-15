"""Default harness scenarios for subscription billing support."""

from src.harness.models import HarnessScenario, HarnessStep


DEFAULT_SCENARIOS = (
    HarnessScenario(
        name="customer_5_duplicate_charge",
        description="Customer 5 asks for duplicate charge and refund evidence.",
        steps=(
            HarnessStep(
                name="verify_customer_5",
                user_message="Customer ID is 5",
                expected_verified_customer_id="5",
                expected_reverified=True,
            ),
            HarnessStep(
                name="duplicate_charge_evidence",
                user_message="Was there a duplicate May charge or refund? Show the evidence.",
                expected_verified_customer_id="5",
                expected_tools=(
                    "get_payments_by_customer",
                    "get_refunds_by_customer",
                    "get_support_tickets_by_customer",
                ),
                forbidden_customer_ids=("1", "2", "3", "4", "6"),
                expected_reverified=False,
            ),
        ),
    ),
    HarnessScenario(
        name="customer_switch_requires_reverification",
        description="A case switches from customer 5 to customer 4 and must re-scope tools.",
        steps=(
            HarnessStep(
                name="verify_customer_5",
                user_message="Customer ID is 5",
                expected_verified_customer_id="5",
                expected_reverified=True,
            ),
            HarnessStep(
                name="switch_to_customer_4",
                user_message="Now check Customer ID 4. Why is the account past_due?",
                expected_verified_customer_id="4",
                expected_tools=(
                    "get_payments_by_customer",
                    "get_billing_timeline",
                ),
                forbidden_customer_ids=("5",),
                expected_reverified=True,
            ),
        ),
    ),
)
