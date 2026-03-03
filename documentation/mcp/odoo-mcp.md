# Odoo MCP Server Documentation

**Part of:** Personal AI Employee - Gold Tier
**File:** `ai_employee_scripts/mcp_servers/odoo_mcp.py`
**MCP Name:** `odoo`

---

## Table of Contents

- [Overview](#overview)
- [Architecture & Workflow](#architecture--workflow)
- [Setup Instructions](#setup-instructions)
- [Configuration](#configuration)
- [Available Tools](#available-tools)
- [Usage Examples](#usage-examples)
- [Integration with AI Employee](#integration-with-ai-employee)
- [Troubleshooting](#troubleshooting)
- [Odoo Data Models](#odoo-data-models)

---

## Overview

The Odoo MCP Server enables the AI Employee to interact with Odoo Community 19+ accounting system. It uses the `odoorpc` library with JSON-RPC protocol for clean, Pythonic access to Odoo's accounting features.

### Features

| Feature | Description |
|---------|-------------|
| **Read Invoices** | Fetch customer invoices with state filtering |
| **Read Payments** | Browse recent payment records |
| **Revenue Tracking** | Get revenue totals by period (today, week, month, year, all) |
| **Expense Tracking** | Get vendor bill totals by period |
| **Create Draft Invoices** | Create draft invoices (auto-creates partners if needed) |
| **Post Invoices** | Post draft invoices to final state (requires approval) |
| **Connection Status** | Check Odoo server connection and info |

### Key Files

| File | Location | Purpose |
|------|----------|---------|
| `odoo_mcp.py` | `ai_employee_scripts/mcp_servers/` | MCP server implementation |
| `.env` | `ai_employee_scripts/` | Stores Odoo connection credentials |
| `error_recovery.py` | `ai_employee_scripts/` | Retry logic for transient errors |

---

## Architecture & Workflow

### System Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                       ODOO MCP WORKFLOW                        │
└─────────────────────────────────────────────────────────────────┘

     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
     │  Odoo Server │     │  odoo_mcp.py │     │   odoorpc    │
     │  (localhost) │     │              │     │   Library    │
     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
            │                    │                    │
            ▼                    ▼                    ▼
     Database            FastMCP Server        JSON-RPC
     (odoo)              (odoo MCP)            Protocol
            │                    │                    │
            └────────────────────┴────────────────────┘
                                    │
                                    ▼
                         ┌─────────────────────────────────────┐
                         │    AI Employee System              │
                         │                                     │
                         │  1. Cron triggers /accounting       │
                         │  2. Read revenue/expenses           │
                         │  3. Create draft invoices           │
                         │  4. Human approves → post_invoice   │
                         └─────────────────────────────────────┘
```

### Connection Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    ODOO CONNECTION FLOW                         │
└─────────────────────────────────────────────────────────────────┘

STEP 1: LOAD CREDENTIALS
┌──────────────────────────────────────────────────────────────┐
│ .env file:                                                   │
│  ODOO_URL=http://localhost:8069                              │
│  ODOO_DB=odoo                                                 │
│  ODOO_USER=admin@example.com                                  │
│  ODOO_PASSWORD=your_password                                  │
└──────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
STEP 2: CONNECT WITH RETRY
┌──────────────────────────────────────────────────────────────┐
│ 1. Parse URL → extract hostname and port                      │
│ 2. Create odoorpc.ODOO(hostname, port, protocol='jsonrpc')   │
│ 3. Login with database, user, password                        │
│ 4. 3 attempts with exponential backoff                        │
└──────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
STEP 3: EXECUTE OPERATIONS
┌──────────────────────────────────────────────────────────────┐
│ All operations use:                                           │
│  - _execute(model, method, domain, fields, limit)            │
│  - _read(model, ids, fields)                                 │
│  - _search_read(model, domain, fields, limit)                │
│                                                              │
│ Retry on connection errors for read operations               │
└──────────────────────────────────────────────────────────────┘
```

---

## Setup Instructions

### Prerequisites

- Python 3.13+ with UV package manager
- Odoo Community 19+ installed and running
- Odoo admin credentials

### Step 1: Install Odoo

If you don't have Odoo installed:

**Option A: Docker (Recommended)**
```bash
docker run -d \
  -e POSTGRES_USER=odoo \
  -e POSTGRES_PASSWORD=odoo \
  -e POSTGRES_DB=postgres \
  --name db \
  postgres:15

docker run -d \
  -p 8069:8069 \
  --name odoo \
  --link db:db \
  -e HOST=db \
  -e USER=admin \
  -e PASSWORD=admin \
  odoo:latest
```

**Option B: Local Installation**
```bash
# Visit https://www.odoo.com/documentation/19.0/administration/on_premise.html
# Follow the installation guide for your OS
```

### Step 2: Configure Odoo for Accounting

1. **Access Odoo:**
   - Open http://localhost:8069 in your browser
   - Create database (e.g., `odoo`)
   - Set admin email and password

2. **Enable Accounting Module:**
   - Go to **Apps**
   - Search for **"Accounting"**
   - Click **Install**

3. **Configure Basic Settings:**
   - Go to **Accounting** → **Configuration** → **Settings**
   - Set your default currency (e.g., USD)
   - Configure your chart of accounts

### Step 3: Configure .env File

Add your Odoo credentials to `ai_employee_scripts/.env`:

```bash
# Odoo Connection
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USER=admin@example.com
ODOO_PASSWORD=your_admin_password
```

**Important:**
- `ODOO_URL` - Your Odoo server URL (include port if not 80)
- `ODOO_DB` - The database name you created
- `ODOO_USER` - Admin email or username
- `ODOO_PASSWORD` - Admin password

### Step 4: Verify MCP Configuration

The Odoo MCP is configured in `AI_Employee_Vault/.mcp.json`:

```json
{
  "mcpServers": {
    "odoo": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts",
        "run",
        "mcp_servers/odoo_mcp.py"
      ],
      "env": {
        "PYTHONPATH": "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts"
      }
    }
  }
}
```

**Important:** Update the paths to match your project directory if different from the example above.

Restart Claude Code to load the MCP server.

### Step 5: Test the Connection

When the MCP server starts, you should see:

```
[INFO] odoo_mcp: Starting Odoo MCP server (using odoorpc with JSON-RPC)...
[INFO] odoo_mcp: Odoo URL: http://localhost:8069
[INFO] odoo_mcp: Database: odoo
[INFO] odoo_mcp: User: admin@example.com
[INFO] odoo_mcp: Connected to Odoo at http://localhost:8069 via JSON-RPC
```

---

## Configuration

### Required Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `ODOO_URL` | Odoo server URL | `http://localhost:8069` |
| `ODOO_DB` | Database name | `odoo` |
| `ODOO_USER` | Admin username/email | `admin@example.com` |
| `ODOO_PASSWORD` | Admin password | `your_secure_password` |

### File Locations

| File | Location | Purpose |
|------|----------|---------|
| `odoo_mcp.py` | `ai_employee_scripts/mcp_servers/` | MCP server implementation |
| `.env` | `ai_employee_scripts/.env` | Credentials storage |
| `error_recovery.py` | `ai_employee_scripts/` | Retry logic utilities |

### Odoo Models Used

| Model | Purpose |
|-------|---------|
| `account.move` | Invoices (customer) and bills (vendor) |
| `account.payment` | Payment records |
| `res.partner` | Customers and vendors |
| `res.currency` | Currency definitions |
| `res.company` | Company information |
| `res.users` | User information |

---

## Available Tools

### 1. get_invoices

Fetch recent invoices from Odoo.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `limit` | int | No | Maximum invoices to return (default: 10) |
| `state` | string | No | Filter by state: `draft`, `posted`, `paid`, `cancel` |

**Returns:** Dictionary with invoice list and metadata

**Return format:**
```json
{
  "success": true,
  "count": 5,
  "invoices": [
    {
      "id": 123,
      "number": "INV/2026/0001",
      "partner": "Client Name",
      "amount_total": 1500.00,
      "currency": "USD",
      "state": "posted",
      "invoice_date": "2026-02-28",
      "payment_status": "not_paid"
    }
  ]
}
```

**Example:**
```python
await mcp__odoo__get_invoices(limit=20, state="posted")
```

---

### 2. get_payments

Fetch recent payments from Odoo.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `limit` | int | No | Maximum payments to return (default: 10) |

**Returns:** Dictionary with payment list and metadata

**Return format:**
```json
{
  "success": true,
  "count": 3,
  "payments": [
    {
      "id": 456,
      "name": "PAY/2026/0001",
      "amount": 1500.00,
      "currency": "USD",
      "payment_type": "inbound",
      "state": "posted",
      "payment_date": "2026-02-28",
      "partner": "Client Name",
      "journal": "Bank"
    }
  ]
}
```

**Example:**
```python
await mcp__odoo__get_payments(limit=15)
```

---

### 3. get_revenue

Get total revenue for a specific period. Revenue is calculated from customer invoices (`move_type='out_invoice'`) that are in `posted` or `paid` state.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `period` | string | No | Time period: `today`, `this_week`, `this_month`, `this_year`, `all` (default: `this_month`) |

**Returns:** Dictionary with revenue total and invoice breakdown

**Note:** The invoice breakdown is limited to 20 most recent invoices.

**Return format:**
```json
{
  "success": true,
  "period": "this_month",
  "total_revenue": 8500.00,
  "invoice_count": 5,
  "invoices": [
    {
      "id": 123,
      "number": "INV/2026/0001",
      "partner": "Client A",
      "amount": 2500.00,
      "date": "2026-02-15",
      "state": "posted"
    }
  ]
}
```

**Example:**
```python
await mcp__odoo__get_revenue(period="this_month")
```

---

### 4. get_expenses

Get total expenses for a specific period. Expenses are calculated from vendor bills (`move_type='in_invoice'`) that are in `posted` or `paid` state.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `period` | string | No | Time period: `today`, `this_week`, `this_month`, `this_year`, `all` (default: `this_month`) |

**Returns:** Dictionary with expense total and bill breakdown

**Note:** The expense breakdown is limited to 20 most recent vendor bills.

**Return format:**
```json
{
  "success": true,
  "period": "this_month",
  "total_expenses": 1200.00,
  "bill_count": 3,
  "expenses": [
    {
      "id": 789,
      "number": "BILL/2026/0001",
      "partner": "Vendor B",
      "amount": 400.00,
      "date": "2026-02-10",
      "state": "posted"
    }
  ]
}
```

**Example:**
```python
await mcp__odoo__get_expenses(period="this_month")
```

---

### 5. create_draft_invoice

Create a draft invoice in Odoo (no approval required). Auto-creates partner if not exists.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `partner_name` | string | Yes | Name of the customer |
| `amount` | float | Yes | Invoice amount |
| `description` | string | No | Invoice line description (default: "Services") |
| `currency` | string | No | Currency code (default: "USD") |

**Returns:** Dictionary with created invoice ID and details

**Return format:**
```json
{
  "success": true,
  "invoice_id": 456,
  "state": "draft",
  "partner": "Client Name",
  "amount": 2500.00,
  "currency": "USD"
}
```

**Example:**
```python
await mcp__odoo__create_draft_invoice(
    partner_name="Acme Corp",
    amount=2500.00,
    description="Web Development Services",
    currency="USD"
)
```

**Note:** This creates a draft invoice that can be reviewed before posting.

---

### 6. post_invoice

Post a draft invoice to final state (REQUIRES HUMAN APPROVAL).

⚠️ **WARNING:** This action confirms the invoice and sends it to the customer. Use human-in-the-loop approval before calling this.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `invoice_id` | int | Yes | ID of the draft invoice to post |

**Returns:** Dictionary with posted invoice details

**Return format:**
```json
{
  "success": true,
  "invoice_id": 456,
  "state": "posted",
  "number": "INV/2026/0005",
  "amount": 2500.00
}
```

**Example:**
```python
await mcp__odoo__post_invoice(invoice_id=456)
```

---

### 7. get_odoo_status

Get Odoo server status and connection info.

**Parameters:** None

**Returns:** Dictionary with connection status and system info

**Return format:**
```json
{
  "success": true,
  "connected": true,
  "protocol": "jsonrpc",
  "url": "http://localhost:8069",
  "database": "odoo",
  "user": "Administrator",
  "companies": [
    {
      "id": 1,
      "name": "My Company",
      "currency": "USD"
    }
  ]
}
```

**Example:**
```python
status = await mcp__odoo__get_odoo_status()
```

---

## Usage Examples

### Example 1: Check Connection and Get Revenue

```python
# First verify Odoo is accessible
status = await mcp__odoo__get_odoo_status()

if status['connected']:
    # Get this month's revenue
    revenue = await mcp__odoo__get_revenue(period="this_month")
    print(f"Revenue: ${revenue['total_revenue']:.2f}")
```

### Example 2: Create and Post Invoice Workflow

```python
# Step 1: Create draft invoice (no approval needed)
draft = await mcp__odoo__create_draft_invoice(
    partner_name="Acme Corporation",
    amount=3500.00,
    description="AI Automation Project - Phase 1",
    currency="USD"
)

# Draft invoice created - invoice_id: 456
# This would go to Pending_Approval/ for human review

# Step 2: After human approval, post the invoice
# (This requires approval in your workflow)
await mcp__odoo__post_invoice(invoice_id=draft['invoice_id'])
```

### Example 3: Monthly Financial Summary

```python
# Get both revenue and expenses for this month
revenue = await mcp__odoo__get_revenue(period="this_month")
expenses = await mcp__odoo__get_expenses(period="this_month")

profit = revenue['total_revenue'] - expenses['total_expenses']

summary = f"""
Monthly Financial Summary:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Revenue:    ${revenue['total_revenue']:,.2f}
Expenses:   ${expenses['total_expenses']:,.2f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Profit:     ${profit:,.2f}
"""
print(summary)
```

### Example 4: List Unpaid Invoices

```python
# Get posted but unpaid invoices
invoices = await mcp__odoo__get_invoices(
    limit=50,
    state="posted"
)

unpaid = [inv for inv in invoices['invoices'] if inv['payment_status'] != 'paid']

print(f"Unpaid invoices: {len(unpaid)}")
for inv in unpaid:
    print(f"  {inv['number']} - {inv['partner']}: ${inv['amount_total']:.2f}")
```

### Example 5: Recent Payments Report

```python
# Get last 20 payments
payments = await mcp__odoo__get_payments(limit=20)

total_collected = sum(p['amount'] for p in payments['payments'])

print(f"""
Recent Payments Report:
Total payments: {payments['count']}
Amount collected: ${total_collected:,.2f}
""")
```

---

## Integration with AI Employee

### Accounting Workflow

The Odoo MCP integrates with the AI Employee's accounting system:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Cron Job    │ ──► │ /accounting  │ ──► │ Odoo MCP     │
│  (Daily)     │     │  Skill       │     │              │
└──────────────┘     └──────┬───────┘     └──────┬───────┘
                            │                    │
                            ▼                    ▼
                    ┌──────────────┐     ┌──────────────┐
                    │   Vault      │     │   Odoo       │
                    │ Accounting/  │     │   Server     │
                    └──────────────┘     └──────────────┘
```

### Skills That Use This MCP

| Skill | Purpose |
|-------|---------|
| `/accounting` | Generate financial summaries and reports |
| `/create-invoice` | Create draft invoices for approval |
| `/execute-approved` | Post approved invoices to Odoo |

### Vault Integration

Financial data can be stored in the vault:
- `AI_Employee_Vault/Accounting/` - Financial records
- `AI_Employee_Vault/Accounting/Rates.md` - Service rates
- `AI_Employee_Vault/Logs/` - Transaction logs

---

## Troubleshooting

### Problem: "Connection failed"

**Error:**
```
[ERROR] odoo_mcp: Failed to connect to Odoo after 3 attempts: ...
```

**Solution:**
1. Verify Odoo is running:
   ```bash
   curl http://localhost:8069
   ```
2. Check credentials in `.env` match your Odoo setup
3. Verify database name is correct
4. Check firewall isn't blocking port 8069

---

### Problem: "Database not found"

**Error:**
```
Odoo server error: Database not found
```

**Solution:**
1. Login to Odoo web interface at http://localhost:8069
2. Verify the database name exists
3. Update `ODOO_DB` in `.env` to match

---

### Problem: "Access denied"

**Error:**
```
Odoo server error: AccessError
```

**Solution:**
1. Verify `ODOO_USER` has admin privileges
2. Check user has Accounting module access
3. Reset password if needed in Odoo interface

---

### Problem: "Currency not found"

**Error (when creating invoice):**
```json
{"success": false, "error": "Currency EUR not found"}
```

**Solution:**
1. Go to Odoo → Accounting → Configuration → Currencies
2. Activate the currency you need
3. Or use the default currency (USD) instead

---

### Problem: "Invoice not in draft state"

**Error (when posting invoice):**
```json
{"success": false, "error": "Invoice 456 is not in draft state (current: posted)"}
```

**Solution:**
- The invoice has already been posted
- Check invoice state before trying to post
- Use `get_invoices()` to verify invoice status

---

## Odoo Data Models

### Invoice States

| State | Description | Can Post? |
|-------|-------------|-----------|
| `draft` | Initial state, not yet posted | ✅ Yes |
| `posted` | Posted, awaiting payment | ❌ Already posted |
| `paid` | Fully paid | ❌ Already posted |
| `cancel` | Cancelled | ❌ Cancelled |

### Payment Types

| Type | Description |
|------|-------------|
| `inbound` | Customer payment (money in) |
|outbound | Vendor payment (money out) |

### Payment States

| State | Description |
|-------|-------------|
| `draft` | Initial state |
| `posted` | Posted to accounting |
| `sent` | Payment sent |
| `reconciled` | Payment reconciled |
| `cancelled` | Payment cancelled |

### Invoice Move Types

| Type | Description |
|------|-------------|
| `out_invoice` | Customer invoice |
| `in_invoice` | Vendor bill |
| `out_refund` | Customer refund |
| `in_refund` | Vendor refund |

---

## Security Best Practices

1. **Never commit `.env` file** - Contains admin credentials
2. **Use strong passwords** - Odoo admin password should be secure
3. **Limit database access** - Odoo should not be exposed to the internet
4. **Review draft invoices** - Always review before posting
5. **Regular backups** - Backup Odoo database regularly

---

## Quick Reference

### MCP Tools

| Tool | Purpose |
|------|---------|
| `get_invoices()` | Fetch customer invoices |
| `get_payments()` | Browse payment records |
| `get_revenue()` | Get revenue totals |
| `get_expenses()` | Get expense totals |
| `create_draft_invoice()` | Create draft invoice |
| `post_invoice()` | Post draft invoice (requires approval) |
| `get_odoo_status()` | Check connection status |

### Period Options

| Period | Description |
|--------|-------------|
| `today` | Current day only |
| `this_week` | Monday through today |
| `this_month` | From 1st of month to today |
| `this_year` | From January 1st to today |
| `all` | All time |

### Invoice States

| State | Can Post? |
|-------|-----------|
| `draft` | ✅ Yes |
| `posted` | ❌ No (already posted) |
| `paid` | ❌ No (already paid) |
| `cancel` | ❌ No (cancelled) |

---

**Last Updated:** February 28, 2026
**Part of:** Personal AI Employee Hackathon 0 - Gold Tier
