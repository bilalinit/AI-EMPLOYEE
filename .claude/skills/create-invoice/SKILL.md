# Create Draft Invoice

## Description
Create a draft invoice in Odoo accounting system. The invoice will be created in draft state and can be reviewed before posting.

**Note:** This skill can be invoked directly by the user, OR automatically by other skills like `/process-tasks` when an invoice request is detected in emails or LinkedIn messages.

## Instructions

### 1. Read Business Context
- Read `AI_Employee_Vault/business_goals.md` for service rates and business info
- Read `AI_Employee_Vault/Accounting/Rates.md` for pricing information

### 2. Gather Invoice Details
You need the following information:
- **Customer Name**: Who is the invoice for?
- **Amount**: Invoice total amount
- **Description**: What services/products were provided?
- **Currency**: Default to USD unless specified

### 3. Create Draft Invoice
Use the Odoo MCP tool: `mcp__odoo__create_draft_invoice`

Parameters:
- `partner_name`: Customer name
- `amount`: Invoice amount
- `description`: Invoice line description
- `currency`: Currency code (default: USD)

### 4. Create Approval Request
After creating the draft invoice, create an approval request file in `AI_Employee_Vault/Pending_Approval/`:

File name format: `INVOICE_{customer_name}_{YYYY-MM-DD}.md`

```yaml
---
type: approval_request
action: post_invoice
invoice_id: [from create_draft_invoice response]
customer: [customer name]
amount: [amount]
currency: [currency]
created: [ISO timestamp]
status: pending
---

# Invoice Posting Request

## Invoice Details
- **Customer**: [customer name]
- **Amount**: [amount] [currency]
- **Description**: [description]

## Draft Invoice ID
[Invoice ID from Odoo]

## To Approve
Move this file to `/Approved/` folder. The invoice will then be posted.

## To Reject
Move this file to `/Rejected/` folder. The draft invoice will remain in Odoo but won't be posted.
```

### 5. Update Dashboard
Add entry to `AI_Employee_Vault/Dashboard.md`:
```markdown
- [Timestamp] Created draft invoice for [customer]: [amount] ([state])
```

## MCP Tools Available
- **mcp__odoo__create_draft_invoice** - Create draft invoice in Odoo

## Notes
- Draft invoices are NOT sent to customers until approved and posted
- Always use human-in-the-loop approval for posting invoices
- Check if customer already exists in Odoo before creating (tool handles this automatically)
