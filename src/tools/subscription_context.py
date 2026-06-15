"""Subscription plan and account-context tools for the multi-agent system."""

import logging
from langchain_core.tools import tool
from src.db.database import run_query_safe

logger = logging.getLogger(__name__)


def _safe_int(value: str, label: str = "value") -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid {label}: '{value}'. Please provide a numeric value.")


@tool
def list_subscription_plans() -> str:
    """List all subscription plans, prices, included seats, and descriptions."""
    logger.info("TOOL_CALL: list_subscription_plans")
    result = run_query_safe(
        """
        SELECT PlanId, PlanCode, PlanName, MonthlyPrice, BillingCycle,
               IncludedSeats, Description
        FROM Plan
        ORDER BY MonthlyPrice;
        """
    )
    logger.info(f"TOOL_RESULT: list_subscription_plans | result_length={len(result)}")
    return result


@tool
def get_plan_details(plan_code_or_name: str) -> str:
    """Get plan price and feature details by plan code or name."""
    logger.info(f"TOOL_CALL: get_plan_details | plan_code_or_name={plan_code_or_name}")
    result = run_query_safe(
        """
        SELECT Plan.PlanId, Plan.PlanCode, Plan.PlanName, Plan.MonthlyPrice,
               Plan.BillingCycle, Plan.IncludedSeats, Plan.Description,
               PlanFeature.FeatureName, PlanFeature.LimitDescription
        FROM Plan
        LEFT JOIN PlanFeature ON Plan.PlanId = PlanFeature.PlanId
        WHERE LOWER(Plan.PlanCode) LIKE LOWER(:pattern)
           OR LOWER(Plan.PlanName) LIKE LOWER(:pattern)
        ORDER BY Plan.PlanId, PlanFeature.FeatureId;
        """,
        {"pattern": f"%{plan_code_or_name}%"},
    )
    logger.info(f"TOOL_RESULT: get_plan_details | result_length={len(result)}")
    if result == "[]":
        return f"No plan found matching: {plan_code_or_name}"
    return result


@tool
def get_customer_profile(customer_id: str) -> str:
    """Get verified customer account profile and assigned support agent."""
    logger.info(f"TOOL_CALL: get_customer_profile | customer_id={customer_id}")
    result = run_query_safe(
        """
        SELECT Customer.CustomerId, Customer.FirstName, Customer.LastName,
               Customer.Email, Customer.Phone, Customer.Company, Customer.Segment,
               Customer.Country, Customer.Status, Customer.CreatedAt,
               SupportAgent.FirstName || ' ' || SupportAgent.LastName AS AssignedAgent,
               SupportAgent.Team AS AssignedTeam,
               SupportAgent.Email AS AssignedAgentEmail
        FROM Customer
        LEFT JOIN SupportAgent ON Customer.SupportAgentId = SupportAgent.AgentId
        WHERE Customer.CustomerId = :customer_id;
        """,
        {"customer_id": _safe_int(customer_id, "customer ID")},
    )
    logger.info(f"TOOL_RESULT: get_customer_profile | result_length={len(result)}")
    if result == "[]":
        return f"No customer found for ID {customer_id}."
    return result


@tool
def get_current_subscription(customer_id: str) -> str:
    """Get a customer's current subscription, plan, seats, renewal date, and discount."""
    logger.info(f"TOOL_CALL: get_current_subscription | customer_id={customer_id}")
    result = run_query_safe(
        """
        SELECT Subscription.SubscriptionId, Subscription.CustomerId,
               Subscription.Status, Subscription.StartDate, Subscription.RenewalDate,
               Subscription.Seats, Subscription.AutoRenew, Subscription.DiscountCode,
               Subscription.DiscountPercent,
               Plan.PlanCode, Plan.PlanName, Plan.MonthlyPrice, Plan.IncludedSeats,
               Plan.Description
        FROM Subscription
        JOIN Plan ON Subscription.PlanId = Plan.PlanId
        WHERE Subscription.CustomerId = :customer_id
        ORDER BY Subscription.SubscriptionId DESC
        LIMIT 1;
        """,
        {"customer_id": _safe_int(customer_id, "customer ID")},
    )
    logger.info(f"TOOL_RESULT: get_current_subscription | result_length={len(result)}")
    if result == "[]":
        return f"No subscription found for customer {customer_id}."
    return result


@tool
def get_subscription_events(customer_id: str) -> str:
    """Get subscription lifecycle events such as upgrades, seat changes, cancellations, and failures."""
    logger.info(f"TOOL_CALL: get_subscription_events | customer_id={customer_id}")
    result = run_query_safe(
        """
        SELECT Event.EventId, Event.EventDate, Event.EventType,
               OldPlan.PlanName AS OldPlanName, NewPlan.PlanName AS NewPlanName,
               Event.OldSeats, Event.NewSeats, Event.Reason, Event.Actor
        FROM SubscriptionEvent AS Event
        LEFT JOIN Plan AS OldPlan ON Event.OldPlanId = OldPlan.PlanId
        LEFT JOIN Plan AS NewPlan ON Event.NewPlanId = NewPlan.PlanId
        WHERE Event.CustomerId = :customer_id
        ORDER BY Event.EventDate DESC, Event.EventId DESC;
        """,
        {"customer_id": _safe_int(customer_id, "customer ID")},
    )
    logger.info(f"TOOL_RESULT: get_subscription_events | result_length={len(result)}")
    if result == "[]":
        return f"No subscription events found for customer {customer_id}."
    return result


subscription_tools = [
    list_subscription_plans,
    get_plan_details,
    get_customer_profile,
    get_current_subscription,
    get_subscription_events,
]
