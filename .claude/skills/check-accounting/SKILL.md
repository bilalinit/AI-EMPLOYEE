# Check Accounting

## Description
Query Odoo accounting system for invoices, payments, revenue, and expenses. Provides a financial overview for business decisions.

## Instructions

### 1. Determine What to Check
Ask the user what information they need:
- **Recent invoices** - Get list of recent invoices
- **Recent payments** - Get list of recent payments
- **Revenue** - Get total revenue for a period
- **Expenses** - Get total expenses for a period
- **Company status** - Get Odoo connection status

### 2. Query Odoo

#### For Recent Invoices
Use: `mcp__odoo__get_invoices`
Parameters:
- `limit`: Number of invoices (default: 10)
- `state`: Filter by state - 'draft', 'posted', 'paid', 'cancel' (optional)

#### For Recent Payments
Use: `mcp__odoo__get_payments`
Parameters:
- `limit`: Number of payments (default: 10)

#### For Revenue
Use: `mcp__odoo__get_revenue`
Parameters:
- `period`: 'today', 'this_week', 'this_month', 'this_year', 'all'

#### For Expenses
Use: `mcp__odoo__get_expenses`
Parameters:
- `period`: 'today', 'this_week', 'this_month', 'this_year', 'all'

#### For System Status
Use: `mcp__odoo__get_odoo_status`
No parameters required.

### 3. Format the Output
Present the information in a clear, readable format:

```
## [Title]

[Summary]

### Details
[Formatted list or table]

### Summary Stats
- Total: [amount]
- Count: [number]
```

### 4. Log to Vault
If requested, save a summary to `AI_Employee_Vault/Accounting/`:
- File: `YYYY-MM-DD_Accounting_Summary.md`

## MCP Tools Available
- **mcp__odoo__get_invoices** - Fetch recent invoices
- **mcp__odoo__get_payments** - Fetch recent payments
- **mcp__odoo__get_revenue** - Get total revenue for period
- **mcp__odoo__get_expenses** - Get total expenses for period
- **mcp__odoo__get_odoo_status** - Get Odoo system status

## Notes
- This is a read-only operation - no approvals needed
- Use this skill for financial snapshots and reporting
- Data comes from the Odoo accounting system
