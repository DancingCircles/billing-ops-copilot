DROP TABLE IF EXISTS SupportTicket;
DROP TABLE IF EXISTS Refund;
DROP TABLE IF EXISTS Payment;
DROP TABLE IF EXISTS InvoiceItem;
DROP TABLE IF EXISTS Invoice;
DROP TABLE IF EXISTS SubscriptionEvent;
DROP TABLE IF EXISTS Subscription;
DROP TABLE IF EXISTS PlanFeature;
DROP TABLE IF EXISTS Plan;
DROP TABLE IF EXISTS SupportAgent;
DROP TABLE IF EXISTS Customer;

CREATE TABLE Customer (
    CustomerId INTEGER PRIMARY KEY,
    FirstName TEXT NOT NULL,
    LastName TEXT NOT NULL,
    Email TEXT NOT NULL UNIQUE,
    Phone TEXT,
    Company TEXT,
    Segment TEXT NOT NULL,
    Country TEXT NOT NULL,
    Status TEXT NOT NULL,
    CreatedAt TEXT NOT NULL,
    SupportAgentId INTEGER
);

CREATE TABLE SupportAgent (
    AgentId INTEGER PRIMARY KEY,
    FirstName TEXT NOT NULL,
    LastName TEXT NOT NULL,
    Team TEXT NOT NULL,
    Email TEXT NOT NULL
);

CREATE TABLE Plan (
    PlanId INTEGER PRIMARY KEY,
    PlanCode TEXT NOT NULL UNIQUE,
    PlanName TEXT NOT NULL,
    MonthlyPrice REAL NOT NULL,
    BillingCycle TEXT NOT NULL,
    IncludedSeats INTEGER NOT NULL,
    Description TEXT NOT NULL
);

CREATE TABLE PlanFeature (
    FeatureId INTEGER PRIMARY KEY,
    PlanId INTEGER NOT NULL,
    FeatureName TEXT NOT NULL,
    LimitDescription TEXT NOT NULL,
    FOREIGN KEY (PlanId) REFERENCES Plan(PlanId)
);

CREATE TABLE Subscription (
    SubscriptionId INTEGER PRIMARY KEY,
    CustomerId INTEGER NOT NULL,
    PlanId INTEGER NOT NULL,
    Status TEXT NOT NULL,
    StartDate TEXT NOT NULL,
    RenewalDate TEXT,
    Seats INTEGER NOT NULL,
    AutoRenew INTEGER NOT NULL,
    TrialEndsAt TEXT,
    DiscountCode TEXT,
    DiscountPercent REAL DEFAULT 0,
    FOREIGN KEY (CustomerId) REFERENCES Customer(CustomerId),
    FOREIGN KEY (PlanId) REFERENCES Plan(PlanId)
);

CREATE TABLE SubscriptionEvent (
    EventId INTEGER PRIMARY KEY,
    SubscriptionId INTEGER NOT NULL,
    CustomerId INTEGER NOT NULL,
    EventDate TEXT NOT NULL,
    EventType TEXT NOT NULL,
    OldPlanId INTEGER,
    NewPlanId INTEGER,
    OldSeats INTEGER,
    NewSeats INTEGER,
    Reason TEXT NOT NULL,
    Actor TEXT NOT NULL,
    FOREIGN KEY (SubscriptionId) REFERENCES Subscription(SubscriptionId),
    FOREIGN KEY (CustomerId) REFERENCES Customer(CustomerId)
);

CREATE TABLE Invoice (
    InvoiceId INTEGER PRIMARY KEY,
    CustomerId INTEGER NOT NULL,
    SubscriptionId INTEGER NOT NULL,
    InvoiceDate TEXT NOT NULL,
    DueDate TEXT NOT NULL,
    PeriodStart TEXT NOT NULL,
    PeriodEnd TEXT NOT NULL,
    Status TEXT NOT NULL,
    Subtotal REAL NOT NULL,
    DiscountAmount REAL NOT NULL,
    TaxAmount REAL NOT NULL,
    Total REAL NOT NULL,
    Currency TEXT NOT NULL,
    Notes TEXT,
    FOREIGN KEY (CustomerId) REFERENCES Customer(CustomerId),
    FOREIGN KEY (SubscriptionId) REFERENCES Subscription(SubscriptionId)
);

CREATE TABLE InvoiceItem (
    InvoiceItemId INTEGER PRIMARY KEY,
    InvoiceId INTEGER NOT NULL,
    ItemType TEXT NOT NULL,
    Description TEXT NOT NULL,
    Quantity REAL NOT NULL,
    UnitPrice REAL NOT NULL,
    Amount REAL NOT NULL,
    ServiceStart TEXT,
    ServiceEnd TEXT,
    FOREIGN KEY (InvoiceId) REFERENCES Invoice(InvoiceId)
);

CREATE TABLE Payment (
    PaymentId INTEGER PRIMARY KEY,
    InvoiceId INTEGER NOT NULL,
    CustomerId INTEGER NOT NULL,
    PaymentDate TEXT NOT NULL,
    Amount REAL NOT NULL,
    Method TEXT NOT NULL,
    Status TEXT NOT NULL,
    ProcessorRef TEXT NOT NULL,
    FailureReason TEXT,
    FOREIGN KEY (InvoiceId) REFERENCES Invoice(InvoiceId),
    FOREIGN KEY (CustomerId) REFERENCES Customer(CustomerId)
);

CREATE TABLE Refund (
    RefundId INTEGER PRIMARY KEY,
    PaymentId INTEGER NOT NULL,
    InvoiceId INTEGER NOT NULL,
    CustomerId INTEGER NOT NULL,
    RefundDate TEXT NOT NULL,
    Amount REAL NOT NULL,
    Status TEXT NOT NULL,
    Reason TEXT NOT NULL,
    ProcessorRef TEXT NOT NULL,
    FOREIGN KEY (PaymentId) REFERENCES Payment(PaymentId),
    FOREIGN KEY (InvoiceId) REFERENCES Invoice(InvoiceId),
    FOREIGN KEY (CustomerId) REFERENCES Customer(CustomerId)
);

CREATE TABLE SupportTicket (
    TicketId INTEGER PRIMARY KEY,
    CustomerId INTEGER NOT NULL,
    CreatedAt TEXT NOT NULL,
    Category TEXT NOT NULL,
    Status TEXT NOT NULL,
    Priority TEXT NOT NULL,
    Subject TEXT NOT NULL,
    Summary TEXT NOT NULL,
    AssignedAgentId INTEGER,
    FOREIGN KEY (CustomerId) REFERENCES Customer(CustomerId),
    FOREIGN KEY (AssignedAgentId) REFERENCES SupportAgent(AgentId)
);

INSERT INTO SupportAgent VALUES
    (1, 'Maya', 'Chen', 'Billing Operations', 'maya.chen@example.com'),
    (2, 'Noah', 'Patel', 'Retention', 'noah.patel@example.com'),
    (3, 'Iris', 'Wong', 'Enterprise Success', 'iris.wong@example.com');

INSERT INTO Customer VALUES
    (1, 'Ava', 'Lin', 'ava.lin@example.com', '+1 (415) 555-0101', 'BrightPath Studio', 'SMB', 'US', 'active', '2024-01-15', 1),
    (2, 'Ben', 'Carter', 'ben.carter@example.com', '+1 (212) 555-0198', 'Northstar Analytics', 'Startup', 'US', 'active', '2024-03-02', 2),
    (3, 'Clara', 'Ng', 'clara.ng@example.com', '+44 20 7946 0958', 'Clara Ng Consulting', 'Solo', 'UK', 'active', '2024-05-20', 1),
    (4, 'Diego', 'Ramos', 'diego.ramos@example.com', '+55 (11) 94444-1100', 'Ramos Retail', 'SMB', 'BR', 'past_due', '2024-06-18', 2),
    (5, 'Elena', 'Petrova', 'elena.petrova@example.com', '+49 30 5555 0190', 'HelioWorks GmbH', 'Mid Market', 'DE', 'active', '2024-02-11', 3),
    (6, 'Farah', 'Khan', 'farah.khan@example.com', '+65 8123 4567', 'Orchid Learning', 'Education', 'SG', 'cancelled', '2023-11-05', 1);

INSERT INTO Plan VALUES
    (1, 'BASIC', 'Basic', 19.00, 'monthly', 1, 'Entry plan for solo users with core reporting.'),
    (2, 'PRO', 'Pro', 49.00, 'monthly', 3, 'Team plan with automation, exports, and priority support.'),
    (3, 'BUSINESS', 'Business', 129.00, 'monthly', 10, 'Advanced plan with audit logs, SSO, and team analytics.'),
    (4, 'ENTERPRISE', 'Enterprise', 399.00, 'monthly', 50, 'Custom contract plan with dedicated success support.');

INSERT INTO PlanFeature VALUES
    (1, 1, 'Projects', 'Up to 3 active projects'),
    (2, 1, 'Exports', 'CSV exports only'),
    (3, 2, 'Projects', 'Unlimited projects'),
    (4, 2, 'Automation', '1,000 automation runs per month'),
    (5, 3, 'Audit Logs', '365 days of audit history'),
    (6, 3, 'SSO', 'SAML SSO included'),
    (7, 4, 'Dedicated Success', 'Named customer success manager'),
    (8, 4, 'Custom Billing', 'Custom invoicing and procurement terms');

INSERT INTO Subscription VALUES
    (101, 1, 2, 'active', '2024-01-15', '2025-07-15', 3, 1, NULL, NULL, 0),
    (102, 2, 3, 'active', '2024-03-02', '2025-07-02', 12, 1, NULL, 'STARTUP20', 20),
    (103, 3, 1, 'active', '2024-05-20', '2025-07-20', 1, 1, NULL, NULL, 0),
    (104, 4, 2, 'past_due', '2024-06-18', '2025-07-18', 5, 1, NULL, NULL, 0),
    (105, 5, 3, 'active', '2024-02-11', '2025-07-11', 18, 1, NULL, 'ANNUAL10', 10),
    (106, 6, 1, 'cancelled', '2023-11-05', NULL, 1, 0, NULL, NULL, 0);

INSERT INTO SubscriptionEvent VALUES
    (1001, 1, 1, '2025-04-15', 'plan_upgrade', 1, 2, 1, 3, 'Customer upgraded from Basic to Pro for team collaboration.', 'support_agent:maya'),
    (1002, 1, 1, '2025-05-01', 'seat_change', 2, 2, 3, 4, 'Added one temporary contractor seat for May.', 'customer_portal'),
    (1003, 2, 2, '2025-05-10', 'seat_change', 3, 3, 8, 12, 'Customer expanded data team from 8 to 12 seats.', 'account_manager:noah'),
    (1004, 3, 3, '2025-06-01', 'trial_end', 1, 1, 1, 1, 'Introductory 50 percent launch discount ended.', 'system'),
    (1005, 4, 4, '2025-06-18', 'payment_failed', 2, 2, 5, 5, 'Card declined on renewal; subscription marked past due.', 'billing_system'),
    (1006, 5, 5, '2025-05-06', 'plan_upgrade', 2, 3, 8, 18, 'Upgraded from Pro to Business and added 10 seats after security review.', 'support_agent:iris'),
    (1007, 5, 5, '2025-06-02', 'refund_requested', 3, 3, 18, 18, 'Customer reported duplicate charge on May invoice.', 'customer_email'),
    (1008, 6, 6, '2025-03-05', 'cancellation', 1, 1, 1, 1, 'Customer cancelled after project ended.', 'customer_portal');

INSERT INTO Invoice VALUES
    (5001, 1, 101, '2025-04-15', '2025-04-22', '2025-04-15', '2025-05-14', 'paid', 49.00, 0.00, 3.92, 52.92, 'USD', 'First Pro invoice after upgrade.'),
    (5002, 1, 101, '2025-05-15', '2025-05-22', '2025-05-15', '2025-06-14', 'paid', 64.00, 0.00, 5.12, 69.12, 'USD', 'Included one temporary additional seat.'),
    (5003, 1, 101, '2025-06-15', '2025-06-22', '2025-06-15', '2025-07-14', 'paid', 49.00, 0.00, 3.92, 52.92, 'USD', 'Returned to standard Pro seat count.'),
    (5101, 2, 102, '2025-05-02', '2025-05-09', '2025-05-02', '2025-06-01', 'paid', 169.00, 33.80, 10.82, 146.02, 'USD', 'Business plan with startup discount.'),
    (5102, 2, 102, '2025-06-02', '2025-06-09', '2025-06-02', '2025-07-01', 'paid', 189.00, 37.80, 12.10, 163.30, 'USD', 'Higher amount due to 4 added seats.'),
    (5201, 3, 103, '2025-05-20', '2025-05-27', '2025-05-20', '2025-06-19', 'paid', 9.50, 9.50, 1.90, 11.40, 'GBP', 'Introductory discount applied.'),
    (5202, 3, 103, '2025-06-20', '2025-06-27', '2025-06-20', '2025-07-19', 'paid', 19.00, 0.00, 3.80, 22.80, 'GBP', 'Discount ended.'),
    (5301, 4, 104, '2025-06-18', '2025-06-25', '2025-06-18', '2025-07-17', 'open', 89.00, 0.00, 7.12, 96.12, 'BRL', 'Renewal pending after card failure.'),
    (5401, 5, 105, '2025-04-11', '2025-04-18', '2025-04-11', '2025-05-10', 'paid', 89.00, 8.90, 15.22, 95.32, 'EUR', 'Pro plan before upgrade.'),
    (5402, 5, 105, '2025-05-11', '2025-05-18', '2025-05-11', '2025-06-10', 'paid', 249.00, 24.90, 42.58, 266.68, 'EUR', 'Business upgrade plus 10 additional seats.'),
    (5403, 5, 105, '2025-05-12', '2025-05-19', '2025-05-11', '2025-06-10', 'refunded', 249.00, 24.90, 42.58, 266.68, 'EUR', 'Duplicate charge automatically refunded.'),
    (5404, 5, 105, '2025-06-11', '2025-06-18', '2025-06-11', '2025-07-10', 'paid', 249.00, 24.90, 42.58, 266.68, 'EUR', 'Normal Business renewal.'),
    (5501, 6, 106, '2025-02-05', '2025-02-12', '2025-02-05', '2025-03-04', 'paid', 19.00, 0.00, 1.52, 20.52, 'SGD', 'Final paid month before cancellation.'),
    (5502, 6, 106, '2025-03-05', '2025-03-12', '2025-03-05', '2025-04-04', 'void', 19.00, 0.00, 1.52, 20.52, 'SGD', 'Voided after cancellation request.');

INSERT INTO InvoiceItem VALUES
    (1, 5001, 'subscription', 'Pro plan monthly subscription', 1, 49.00, 49.00, '2025-04-15', '2025-05-14'),
    (2, 5002, 'subscription', 'Pro plan monthly subscription', 1, 49.00, 49.00, '2025-05-15', '2025-06-14'),
    (3, 5002, 'seat_overage', 'Temporary contractor seat', 1, 15.00, 15.00, '2025-05-15', '2025-06-14'),
    (4, 5003, 'subscription', 'Pro plan monthly subscription', 1, 49.00, 49.00, '2025-06-15', '2025-07-14'),
    (5, 5101, 'subscription', 'Business base plan', 1, 129.00, 129.00, '2025-05-02', '2025-06-01'),
    (6, 5101, 'seat_overage', '2 additional seats', 2, 20.00, 40.00, '2025-05-02', '2025-06-01'),
    (7, 5102, 'subscription', 'Business base plan', 1, 129.00, 129.00, '2025-06-02', '2025-07-01'),
    (8, 5102, 'seat_overage', '3 additional seats', 3, 20.00, 60.00, '2025-06-02', '2025-07-01'),
    (9, 5201, 'subscription', 'Basic plan with launch discount', 1, 19.00, 19.00, '2025-05-20', '2025-06-19'),
    (10, 5201, 'discount', 'Launch discount 50 percent', 1, -9.50, -9.50, '2025-05-20', '2025-06-19'),
    (11, 5202, 'subscription', 'Basic plan monthly subscription', 1, 19.00, 19.00, '2025-06-20', '2025-07-19'),
    (12, 5301, 'subscription', 'Pro plan monthly subscription', 1, 49.00, 49.00, '2025-06-18', '2025-07-17'),
    (13, 5301, 'seat_overage', '2 additional support seats', 2, 20.00, 40.00, '2025-06-18', '2025-07-17'),
    (14, 5401, 'subscription', 'Pro plan monthly subscription', 1, 49.00, 49.00, '2025-04-11', '2025-05-10'),
    (15, 5401, 'seat_overage', '2 additional analyst seats', 2, 20.00, 40.00, '2025-04-11', '2025-05-10'),
    (16, 5402, 'subscription', 'Business base plan after upgrade', 1, 129.00, 129.00, '2025-05-11', '2025-06-10'),
    (17, 5402, 'seat_overage', '8 additional Business seats', 8, 15.00, 120.00, '2025-05-11', '2025-06-10'),
    (18, 5403, 'subscription', 'Duplicate Business base plan charge', 1, 129.00, 129.00, '2025-05-11', '2025-06-10'),
    (19, 5403, 'seat_overage', 'Duplicate additional seat charge', 8, 15.00, 120.00, '2025-05-11', '2025-06-10'),
    (20, 5404, 'subscription', 'Business base plan renewal', 1, 129.00, 129.00, '2025-06-11', '2025-07-10'),
    (21, 5404, 'seat_overage', '8 additional Business seats', 8, 15.00, 120.00, '2025-06-11', '2025-07-10'),
    (22, 5501, 'subscription', 'Basic monthly subscription', 1, 19.00, 19.00, '2025-02-05', '2025-03-04'),
    (23, 5502, 'subscription', 'Voided Basic renewal after cancellation', 1, 19.00, 19.00, '2025-03-05', '2025-04-04');

INSERT INTO Payment VALUES
    (9001, 5001, 1, '2025-04-15', 52.92, 'visa_4242', 'succeeded', 'pay_ava_apr', NULL),
    (9002, 5002, 1, '2025-05-15', 69.12, 'visa_4242', 'succeeded', 'pay_ava_may', NULL),
    (9003, 5003, 1, '2025-06-15', 52.92, 'visa_4242', 'succeeded', 'pay_ava_jun', NULL),
    (9101, 5101, 2, '2025-05-02', 146.02, 'amex_0005', 'succeeded', 'pay_ben_may', NULL),
    (9102, 5102, 2, '2025-06-02', 163.30, 'amex_0005', 'succeeded', 'pay_ben_jun', NULL),
    (9201, 5201, 3, '2025-05-20', 11.40, 'mastercard_4444', 'succeeded', 'pay_clara_may', NULL),
    (9202, 5202, 3, '2025-06-20', 22.80, 'mastercard_4444', 'succeeded', 'pay_clara_jun', NULL),
    (9301, 5301, 4, '2025-06-18', 96.12, 'visa_1111', 'failed', 'pay_diego_jun_fail', 'card_declined'),
    (9401, 5401, 5, '2025-04-11', 95.32, 'sepa_debit', 'succeeded', 'pay_elena_apr', NULL),
    (9402, 5402, 5, '2025-05-11', 266.68, 'sepa_debit', 'succeeded', 'pay_elena_may_a', NULL),
    (9403, 5403, 5, '2025-05-12', 266.68, 'sepa_debit', 'succeeded', 'pay_elena_may_dup', NULL),
    (9404, 5404, 5, '2025-06-11', 266.68, 'sepa_debit', 'succeeded', 'pay_elena_jun', NULL),
    (9501, 5501, 6, '2025-02-05', 20.52, 'visa_7878', 'succeeded', 'pay_farah_feb', NULL);

INSERT INTO Refund VALUES
    (7001, 9403, 5403, 5, '2025-05-13', 266.68, 'succeeded', 'Duplicate May Business invoice was charged twice.', 'rf_elena_dup_may'),
    (7002, 5501, 5501, 6, '2025-03-06', 10.26, 'succeeded', 'Courtesy partial refund after cancellation.', 'rf_farah_partial');

INSERT INTO SupportTicket VALUES
    (3001, 1, '2025-05-16', 'billing_explanation', 'closed', 'normal', 'May invoice higher than April', 'Explained temporary contractor seat caused $15 subtotal increase plus tax.', 1),
    (3002, 2, '2025-06-03', 'plan_change', 'closed', 'normal', 'June bill increased', 'Explained additional seats after team expansion.', 2),
    (3003, 3, '2025-06-21', 'billing_explanation', 'closed', 'low', 'Basic price doubled', 'Explained 50 percent launch discount ended.', 1),
    (3004, 4, '2025-06-19', 'payment_failure', 'open', 'high', 'Card declined on renewal', 'Customer needs to update payment method before subscription leaves grace period.', 2),
    (3005, 5, '2025-05-12', 'duplicate_charge', 'closed', 'urgent', 'Duplicate Business charge', 'Duplicate invoice 5403 refunded in full on May 13.', 3),
    (3006, 5, '2025-06-12', 'billing_explanation', 'closed', 'normal', 'Business renewal amount', 'Explained Business base plan plus 8 additional seats and ANNUAL10 discount.', 3),
    (3007, 6, '2025-03-05', 'cancellation', 'closed', 'normal', 'Cancel Basic plan', 'Voided March renewal and issued partial courtesy refund.', 1);
