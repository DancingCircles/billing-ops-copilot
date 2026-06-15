"""Tests for subscription context and billing evidence tools."""

import json

from src.tools.invoice import (
    get_billing_timeline,
    get_invoice_line_items,
    get_invoices_by_customer_sorted_by_date,
    get_payments_by_customer,
    get_refunds_by_customer,
    get_support_tickets_by_customer,
)
from src.tools.subscription_context import (
    get_current_subscription,
    get_customer_profile,
    get_plan_details,
    get_subscription_events,
    list_subscription_plans,
)


class TestSubscriptionContextTools:
    def test_list_subscription_plans(self):
        result = list_subscription_plans.invoke({})
        data = json.loads(result)
        assert len(data) == 4
        assert data[0]["PlanCode"] == "BASIC"
        assert data[-1]["PlanCode"] == "ENTERPRISE"

    def test_get_plan_details(self):
        result = get_plan_details.invoke({"plan_code_or_name": "Business"})
        data = json.loads(result)
        assert len(data) >= 1
        assert data[0]["PlanCode"] == "BUSINESS"
        assert any(row["FeatureName"] == "SSO" for row in data)

    def test_get_customer_profile(self):
        result = get_customer_profile.invoke({"customer_id": "5"})
        data = json.loads(result)
        assert data[0]["Company"] == "HelioWorks GmbH"
        assert data[0]["AssignedTeam"] == "Enterprise Success"

    def test_get_current_subscription(self):
        result = get_current_subscription.invoke({"customer_id": "5"})
        data = json.loads(result)
        assert data[0]["PlanName"] == "Business"
        assert data[0]["Seats"] == 18
        assert data[0]["DiscountCode"] == "ANNUAL10"

    def test_get_subscription_events_upgrade_and_refund_request(self):
        result = get_subscription_events.invoke({"customer_id": "5"})
        data = json.loads(result)
        event_types = {row["EventType"] for row in data}
        assert {"plan_upgrade", "refund_requested"}.issubset(event_types)
        assert any("duplicate charge" in row["Reason"].lower() for row in data)


class TestBillingEvidenceTools:
    def test_get_invoices_by_customer_sorted_by_date(self):
        result = get_invoices_by_customer_sorted_by_date.invoke({"customer_id": "5"})
        data = json.loads(result)
        assert len(data) == 4
        assert data[0]["InvoiceId"] == 5404
        assert data[1]["InvoiceId"] == 5403
        assert data[1]["Status"] == "refunded"

    def test_get_invoice_line_items_for_duplicate_invoice(self):
        result = get_invoice_line_items.invoke({"invoice_id": "5403", "customer_id": "5"})
        data = json.loads(result)
        assert len(data) == 2
        assert any("Duplicate" in row["Description"] for row in data)
        assert sum(row["Amount"] for row in data) == 249.0

    def test_get_payments_by_customer_includes_duplicate_payment(self):
        result = get_payments_by_customer.invoke({"customer_id": "5"})
        data = json.loads(result)
        refs = {row["ProcessorRef"] for row in data}
        assert "pay_elena_may_dup" in refs
        assert all(row["Status"] == "succeeded" for row in data)

    def test_get_refunds_by_customer_duplicate_charge(self):
        result = get_refunds_by_customer.invoke({"customer_id": "5"})
        data = json.loads(result)
        assert len(data) == 1
        assert data[0]["Amount"] == 266.68
        assert "Duplicate May Business invoice" in data[0]["Reason"]

    def test_get_support_tickets_by_customer_duplicate_charge(self):
        result = get_support_tickets_by_customer.invoke({"customer_id": "5"})
        data = json.loads(result)
        assert any(row["Category"] == "duplicate_charge" for row in data)
        assert any("refunded in full" in row["Summary"] for row in data)

    def test_get_billing_timeline_links_refund_invoice_and_support_ticket(self):
        result = get_billing_timeline.invoke({"customer_id": "5"})
        data = json.loads(result)
        sources = {row["Source"] for row in data}
        assert {"subscription_event", "invoice", "payment", "refund", "support_ticket"}.issubset(sources)
        assert any(row["EventType"] == "refund_succeeded" for row in data)
        assert any("Duplicate Business charge" in row["Detail"] for row in data)

    def test_failed_payment_customer(self):
        payments = json.loads(get_payments_by_customer.invoke({"customer_id": "4"}))
        assert payments[0]["Status"] == "failed"
        assert payments[0]["FailureReason"] == "card_declined"

        timeline = json.loads(get_billing_timeline.invoke({"customer_id": "4"}))
        assert any(row["EventType"] == "payment_failed" for row in timeline)
        assert any(row["EventType"] == "payment_failed" or row["Status"] == "failed" for row in timeline)

    def test_temporary_seat_bill_increase_customer(self):
        invoices = json.loads(get_invoices_by_customer_sorted_by_date.invoke({"customer_id": "1"}))
        may_invoice = next(row for row in invoices if row["InvoiceId"] == 5002)
        assert may_invoice["Total"] == 69.12

        line_items = json.loads(get_invoice_line_items.invoke({"invoice_id": "5002", "customer_id": "1"}))
        assert any(row["ItemType"] == "seat_overage" for row in line_items)
        assert any(row["Description"] == "Temporary contractor seat" for row in line_items)
