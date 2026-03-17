"""
Finance Agent

Handles financial tasks: invoices, payments, expenses, reporting.
Part A: Core Basics - Agent with Tools
"""

from agents import Agent
from cloud.bots.models import FinanceAction, FinanceActionType, RiskLevel
from cloud.bots.base_agent import create_base_agent, get_common_tools


# ============================================================================
# FINANCE AGENT INSTRUCTIONS
# ============================================================================

FINANCE_INSTRUCTIONS = """
You are the Finance Agent. Your job is to handle financial tasks safely.

ODOO MCP TOOLS AVAILABLE:
- get_customer(partner_name): Get customer details (email, phone, balance, payment terms) from Odoo
- search_partners(search_term, limit): Search customers/vendors by name/email/phone in Odoo
- get_invoice_history(partner_name, limit): Get past invoices and payment status from Odoo
- get_pricing(service_type): Get pricing for services (consulting, development, design, etc.)
- create_draft_invoice(partner_name, amount, description, hours, rate): Create draft invoice in Odoo

WHEN TO USE ODOO TOOLS:
1. Before creating invoice: Use get_customer(partner_name) to verify customer exists in Odoo
2. For new customers: Check their payment history with get_invoice_history(partner_name)
3. For pricing: Use get_pricing(service_type) to verify rates
4. To create invoice: Use create_draft_invoice(...) to create DRAFT invoice in Odoo (needs local approval to post)

CAPABILITIES:
- Create draft invoices in Odoo (via MCP tools)
- Categorize expenses
- Generate financial summaries
- Detect unusual transactions
- Assess financial risk

SAFETY RULES (CRITICAL):
- NEVER execute payments - only draft for approval
- NEVER include real banking credentials in outputs
- ALWAYS set needs_approval=True for financial actions
- Flag ANYTHING unusual for human review

INVOICE CREATION PROCESS:
1. Extract customer name, amount, description from task
2. Use get_customer(partner_name) to verify customer exists in Odoo
3. Use get_invoice_history(partner_name) to check customer's payment status
4. Use get_pricing(service_type) to verify pricing
5. Use create_draft_invoice(...) to create the draft invoice in Odoo
6. OUTPUT confirmation with invoice_id, amount, and customer details

EXPENSE CATEGORIZATION:
- Categorize by type (software, service, hardware, etc.)
- Flag unusual amounts (>$1000 = HIGH risk)
- Note recurring vs one-time

REPORTING:
- Summarize revenue, expenses, profit
- Highlight trends or concerns
- Keep factual and accurate

RISK ASSESSMENT:
- LOW: Routine invoices < $500, known vendors
- MEDIUM: Invoices $500-1000, new customers
- HIGH: Invoices > $1000, first-time transactions
- CRITICAL: Unusual patterns, large amounts, new payees

YOUR PROCESS:
1. Use get_task_content() to read the task
2. Use Odoo MCP tools to verify customer and pricing
3. Use read_context_file("Accounting", "Rates.md") for additional pricing reference
4. Use read_context_file("Handbook", "") for approval thresholds
5. Process according to action type
6. OUTPUT your draft content as plain text - the orchestrator will save it

IMPORTANT: You have Odoo MCP tools AND vault file tools available.
Use Odoo tools for customer/pricing data and invoice creation.
Use vault tools (read_context_file) for company policies and approval thresholds.
DO NOT try to call save_draft, complete_task, or any other orchestrator-only tools.

FINANCE ACTIONS:
- create_invoice: Draft a new invoice in Odoo
- payment_received: Log an incoming payment
- expense_categorize: Categorize an expense
- report_generate: Create financial summary
- anomaly_detected: Flag unusual transaction
"""

# ============================================================================
# CREATE FINANCE AGENT
# ============================================================================

def create_finance_agent(model=None) -> Agent:
    """
    Create the finance agent for financial tasks.

    This implements Part A: Core Basics from the OpenAI Agents SDK.

    Note: GLM API doesn't support structured output well, so we parse manually.

    Args:
        model: The model to use (default: None, will be set by orchestrator)

    Returns:
        Agent: Configured finance agent (no structured output for GLM compatibility)
    """
    return create_base_agent(
        name="FinanceAgent",
        instructions=FINANCE_INSTRUCTIONS,
        tools=get_common_tools(),
        model=model,
        output_type=None  # No structured output for GLM
    )


# ============================================================================
# FINANCE TEMPLATE GENERATORS
# ============================================================================

def create_invoice_draft(
    customer_name: str,
    amount: float,
    description: str,
    currency: str = "USD"
) -> str:
    """
    Create an invoice draft format.

    Args:
        customer_name: Name of customer
        amount: Invoice amount
        description: Service/product description
        currency: Currency code

    Returns:
        str: Formatted invoice draft
    """
    draft = f"""---
type: invoice_draft
customer: {customer_name}
amount: {amount} {currency}
action: create_invoice
needs_approval: true
risk_level: HIGH if amount > 1000 else MEDIUM
---

# Invoice Draft

**Customer:** {customer_name}
**Amount:** {currency} {amount:.2f}
**Description:** {description}

---
*Drafted by AI Employee Cloud Agent*
*Review and approve before posting to accounting system*
"""

    return draft


def create_payment_summary(
    amount: float,
    source: str,
    description: str = ""
) -> str:
    """
    Create a payment received summary.

    Args:
        amount: Payment amount
        source: Payment source/customer
        description: Additional details

    Returns:
        str: Formatted payment summary
    """
    return f"""---
type: payment_received
amount: {amount}
source: {source}
---

# Payment Received

**Source:** {source}
**Amount:** ${amount:.2f}
{f"**Note:** {description}" if description else ""}

Payment logged successfully.
"""


def assess_risk_level(amount: float, is_new_customer: bool = False) -> RiskLevel:
    """
    Assess risk level for a transaction.

    Args:
        amount: Transaction amount
        is_new_customer: Whether this is a new customer

    Returns:
        RiskLevel: Assessed risk level
    """
    if amount > 5000 or (is_new_customer and amount > 2000):
        return RiskLevel.CRITICAL
    elif amount > 1000 or is_new_customer:
        return RiskLevel.HIGH
    elif amount > 500:
        return RiskLevel.MEDIUM
    else:
        return RiskLevel.LOW
