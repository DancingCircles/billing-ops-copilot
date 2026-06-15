"""Billing, invoice, payment, refund, and support-ticket tools."""

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
def get_invoices_by_customer_sorted_by_date(customer_id: str) -> str:
    """Look up all invoices for a verified customer, newest first."""
    logger.info(f"TOOL_CALL: get_invoices_by_customer_sorted_by_date | customer_id={customer_id}")
    result = run_query_safe(
        """
        SELECT Invoice.InvoiceId, Invoice.CustomerId, Invoice.SubscriptionId,
               Invoice.InvoiceDate, Invoice.DueDate, Invoice.PeriodStart, Invoice.PeriodEnd,
               Invoice.Status, Invoice.Subtotal, Invoice.DiscountAmount,
               Invoice.TaxAmount, Invoice.Total, Invoice.Currency, Invoice.Notes
        FROM Invoice
        WHERE Invoice.CustomerId = :customer_id
        ORDER BY Invoice.InvoiceDate DESC, Invoice.InvoiceId DESC;
        """,
        {"customer_id": _safe_int(customer_id, "customer ID")},
    )
    logger.info(f"TOOL_RESULT: get_invoices_by_customer_sorted_by_date | result_length={len(result)}")
    if result == "[]":
        return f"No invoices found for customer {customer_id}."
    return result


@tool
def get_invoice_line_items(invoice_id: str, customer_id: str) -> str:
    """Get invoice line items for a specific invoice owned by the verified customer."""
    logger.info(f"TOOL_CALL: get_invoice_line_items | invoice_id={invoice_id}, customer_id={customer_id}")
    result = run_query_safe(
        """
        SELECT InvoiceItem.InvoiceItemId, InvoiceItem.InvoiceId, InvoiceItem.ItemType,
               InvoiceItem.Description, InvoiceItem.Quantity, InvoiceItem.UnitPrice,
               InvoiceItem.Amount, InvoiceItem.ServiceStart, InvoiceItem.ServiceEnd
        FROM InvoiceItem
        JOIN Invoice ON InvoiceItem.InvoiceId = Invoice.InvoiceId
        WHERE InvoiceItem.InvoiceId = :invoice_id
          AND Invoice.CustomerId = :customer_id
        ORDER BY InvoiceItem.InvoiceItemId;
        """,
        {"invoice_id": _safe_int(invoice_id, "invoice ID"), "customer_id": _safe_int(customer_id, "customer ID")},
    )
    logger.info(f"TOOL_RESULT: get_invoice_line_items | result_length={len(result)}")
    if result == "[]":
        return f"No line items found for invoice {invoice_id} (customer {customer_id})."
    return result


@tool
def get_payments_by_customer(customer_id: str) -> str:
    """Get all payment attempts for a verified customer."""
    logger.info(f"TOOL_CALL: get_payments_by_customer | customer_id={customer_id}")
    result = run_query_safe(
        """
        SELECT Payment.PaymentId, Payment.InvoiceId, Payment.PaymentDate, Payment.Amount,
               Payment.Method, Payment.Status, Payment.ProcessorRef, Payment.FailureReason
        FROM Payment
        WHERE Payment.CustomerId = :customer_id
        ORDER BY Payment.PaymentDate DESC, Payment.PaymentId DESC;
        """,
        {"customer_id": _safe_int(customer_id, "customer ID")},
    )
    logger.info(f"TOOL_RESULT: get_payments_by_customer | result_length={len(result)}")
    if result == "[]":
        return f"No payment records found for customer {customer_id}."
    return result


@tool
def get_refunds_by_customer(customer_id: str) -> str:
    """Get all refunds for a verified customer."""
    logger.info(f"TOOL_CALL: get_refunds_by_customer | customer_id={customer_id}")
    result = run_query_safe(
        """
        SELECT Refund.RefundId, Refund.PaymentId, Refund.InvoiceId, Refund.RefundDate,
               Refund.Amount, Refund.Status, Refund.Reason, Refund.ProcessorRef
        FROM Refund
        WHERE Refund.CustomerId = :customer_id
        ORDER BY Refund.RefundDate DESC, Refund.RefundId DESC;
        """,
        {"customer_id": _safe_int(customer_id, "customer ID")},
    )
    logger.info(f"TOOL_RESULT: get_refunds_by_customer | result_length={len(result)}")
    if result == "[]":
        return f"No refunds found for customer {customer_id}."
    return result


@tool
def get_support_tickets_by_customer(customer_id: str) -> str:
    """Get support tickets that explain billing questions, refunds, failures, or subscription changes."""
    logger.info(f"TOOL_CALL: get_support_tickets_by_customer | customer_id={customer_id}")
    result = run_query_safe(
        """
        SELECT SupportTicket.TicketId, SupportTicket.CreatedAt, SupportTicket.Category,
               SupportTicket.Status, SupportTicket.Priority, SupportTicket.Subject,
               SupportTicket.Summary,
               SupportAgent.FirstName || ' ' || SupportAgent.LastName AS AssignedAgent
        FROM SupportTicket
        LEFT JOIN SupportAgent ON SupportTicket.AssignedAgentId = SupportAgent.AgentId
        WHERE SupportTicket.CustomerId = :customer_id
        ORDER BY SupportTicket.CreatedAt DESC, SupportTicket.TicketId DESC;
        """,
        {"customer_id": _safe_int(customer_id, "customer ID")},
    )
    logger.info(f"TOOL_RESULT: get_support_tickets_by_customer | result_length={len(result)}")
    if result == "[]":
        return f"No support tickets found for customer {customer_id}."
    return result


@tool
def get_billing_timeline(customer_id: str) -> str:
    """Get a combined timeline of subscription events, invoices, payments, refunds, and support tickets."""
    logger.info(f"TOOL_CALL: get_billing_timeline | customer_id={customer_id}")
    result = run_query_safe(
        """
        SELECT 'subscription_event' AS Source, EventDate AS EventDate,
               EventType AS EventType, Reason AS Detail, NULL AS Amount, NULL AS Status
        FROM SubscriptionEvent
        WHERE CustomerId = :customer_id
        UNION ALL
        SELECT 'invoice' AS Source, InvoiceDate AS EventDate,
               'invoice_' || Status AS EventType, Notes AS Detail, Total AS Amount, Status
        FROM Invoice
        WHERE CustomerId = :customer_id
        UNION ALL
        SELECT 'payment' AS Source, PaymentDate AS EventDate,
               'payment_' || Status AS EventType, COALESCE(FailureReason, ProcessorRef) AS Detail, Amount, Status
        FROM Payment
        WHERE CustomerId = :customer_id
        UNION ALL
        SELECT 'refund' AS Source, RefundDate AS EventDate,
               'refund_' || Status AS EventType, Reason AS Detail, Amount, Status
        FROM Refund
        WHERE CustomerId = :customer_id
        UNION ALL
        SELECT 'support_ticket' AS Source, CreatedAt AS EventDate,
               Category AS EventType, Subject || ': ' || Summary AS Detail, NULL AS Amount, Status
        FROM SupportTicket
        WHERE CustomerId = :customer_id
        ORDER BY EventDate DESC;
        """,
        {"customer_id": _safe_int(customer_id, "customer ID")},
    )
    logger.info(f"TOOL_RESULT: get_billing_timeline | result_length={len(result)}")
    if result == "[]":
        return f"No billing timeline found for customer {customer_id}."
    return result


invoice_tools = [
    get_invoices_by_customer_sorted_by_date,
    get_invoice_line_items,
    get_payments_by_customer,
    get_refunds_by_customer,
    get_support_tickets_by_customer,
    get_billing_timeline,
]
