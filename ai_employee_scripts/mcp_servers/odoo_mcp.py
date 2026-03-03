#!/usr/bin/env python3
"""
Odoo MCP Server for Personal AI Employee - Gold Tier Accounting Integration

This MCP server provides tools for interacting with Odoo Community 19+ accounting system.
It uses odoorpc library with JSON-RPC protocol for cleaner, more Pythonic code.

Supported operations:
- Read invoices, payments, revenue, expenses
- Create draft invoices
- Post approved invoices

Required Environment Variables:
- ODOO_URL: http://localhost:8069
- ODOO_DB: odoo
- ODOO_USER: admin@example.com
- ODOO_PASSWORD: your_admin_password
"""

import os
import odoorpc
from datetime import datetime, timedelta, date
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional
import sys
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from error_recovery import with_retry, is_transient_error

from mcp.server.fastmcp import FastMCP

# Environment variables
ENV_FILE = Path(__file__).parent.parent / ".env"

def _load_env_file():
    """Load environment variables from .env file if not already set."""
    if ENV_FILE.exists():
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key.strip() not in os.environ:
                        os.environ[key.strip()] = value.strip()

# Load .env file at module import
_load_env_file()

# Odoo configuration
ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB", "odoo")
ODOO_USER = os.getenv("ODOO_USER", "admin@example.com")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "")

# Create MCP server
mcp = FastMCP("odoo")

# Global Odoo connection (odoorpc with JSON-RPC)
_odoo = None


def get_odoo_connection():
    """Get or create Odoo connection via odoorpc using JSON-RPC with retry."""
    global _odoo
    if _odoo is None:
        _connect_with_retry()
    return _odoo


def _connect_with_retry():
    """Connect to Odoo with retry logic."""
    global _odoo

    max_attempts = 3
    base_delay = 2

    for attempt in range(max_attempts):
        try:
            # Parse URL to get hostname (odoorpc needs hostname, not full URL)
            hostname = ODOO_URL.replace("http://", "").replace("https://", "")
            hostname = hostname.split(":")[0] if ":" in hostname else hostname

            # Extract port from URL or use default
            port = 8069
            if ":" in hostname:
                parts = hostname.split(":")
                hostname = parts[0]
                port = int(parts[1])

            # Connect using odoorpc with JSON-RPC protocol
            _odoo = odoorpc.ODOO(hostname, port=port, protocol='jsonrpc')
            _odoo.login(ODOO_DB, ODOO_USER, ODOO_PASSWORD)
            print_status(f"Connected to Odoo at {ODOO_URL} via JSON-RPC")
            return

        except Exception as e:
            is_last = attempt == max_attempts - 1
            delay = min(base_delay * (2 ** attempt), 30)

            if is_last:
                print_status(f"Failed to connect to Odoo after {max_attempts} attempts: {e}", "error")
                raise

            print_status(f"Odoo connection attempt {attempt + 1} failed: {e}. Retrying in {delay}s...", "warning")
            time.sleep(delay)

def print_status(message: str, level: str = "info"):
    """Print status message to stderr."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefix = {
        "info": "[INFO]",
        "error": "[ERROR]",
        "success": "[SUCCESS]"
    }.get(level, "[INFO]")
    print(f"{timestamp} {prefix} odoo_mcp: {message}", file=sys.stderr)


def _execute_with_retry(func, *args, **kwargs):
    """Execute Odoo operation with retry on connection errors."""
    max_attempts = 3
    base_delay = 1

    for attempt in range(max_attempts):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_str = str(e).lower()

            # Check if it's a connection error (transient)
            is_transient = any(
                pattern in error_str
                for pattern in ['connection', 'timeout', 'network', 'unavailable']
            )

            if not is_transient or attempt == max_attempts - 1:
                raise

            delay = min(base_delay * (2 ** attempt), 10)
            print_status(f"Operation failed (attempt {attempt + 1}): {e}. Retrying in {delay}s...", "warning")
            time.sleep(delay)

            # Try to reconnect
            global _odoo
            _odoo = None
            get_odoo_connection()


def _execute(model_name, method, domain=None, fields=None, limit=None, offset=0, order=None, context=None, create_data=None, record_ids=None):
    """Helper to execute Odoo model methods via odoorpc with retry."""
    def _do_execute():
        odoo = get_odoo_connection()
        model = odoo.env[model_name]

        # Handle different argument patterns
        if record_ids is not None:
            # Methods called on recordsets (e.g., action_post)
            if method == 'action_post':
                return model.action_post(record_ids)
            return getattr(model, method)(record_ids)
        elif create_data is not None:
            # Create method
            return model.create(create_data)
        elif domain is not None and domain != []:
            # Search method
            return model.search(domain, limit=limit, offset=offset, order=order)
        else:
            # No domain or empty domain - empty list for "all records"
            return model.search([], limit=limit, offset=offset, order=order)

    # Use retry for read operations, but not for writes (require manual retry)
    if create_data is None and record_ids is None and method == 'search':
        return _execute_with_retry(_do_execute)
    else:
        return _do_execute()


def _read(model_name, ids, fields=None):
    """Helper to read records via odoorpc."""
    odoo = get_odoo_connection()
    model = odoo.env[model_name]
    if isinstance(ids, list):
        return model.read(ids, fields if fields else [])
    return model.read([ids], fields if fields else [])


def _search_read(model_name, domain, fields=None, limit=None, order=None):
    """Helper to search and read in one call via odoorpc."""
    odoo = get_odoo_connection()
    model = odoo.env[model_name]
    kwargs = {}
    if fields is not None:
        kwargs['fields'] = fields
    if limit is not None:
        kwargs['limit'] = limit
    if order is not None:
        kwargs['order'] = order
    return model.search_read(domain, **kwargs)


def _to_dict(value):
    """Convert frozendict or other types to regular dict."""
    if isinstance(value, dict):
        return dict(value)
    elif isinstance(value, list):
        return [_to_dict(v) for v in value]
    elif isinstance(value, (datetime, date)):
        return value.isoformat()
    elif isinstance(value, Decimal):
        return float(value)
    else:
        return value


@mcp.tool()
def get_invoices(limit: int = 10, state: Optional[str] = None) -> dict:
    """
    Fetch recent invoices from Odoo.

    Args:
        limit: Maximum number of invoices to return (default: 10)
        state: Filter by state - 'draft', 'posted', 'paid', 'cancel' (optional)

    Returns:
        Dictionary with invoice list and metadata
    """
    try:
        domain = [('move_type', '=', 'out_invoice')]
        if state:
            domain.append(('state', '=', state))

        fields = ['id', 'name', 'partner_id', 'amount_total', 'currency_id',
                  'state', 'invoice_date', 'payment_state']

        invoices = _search_read('account.move', domain, fields=fields, limit=limit, order='invoice_date desc')

        result = []
        for inv in invoices:
            result.append({
                'id': inv['id'],
                'number': inv.get('name') or 'Draft',
                'partner': inv.get('partner_id', [False, 'No Partner'])[1] if inv.get('partner_id') else 'No Partner',
                'amount_total': float(inv.get('amount_total', 0)),
                'currency': inv.get('currency_id', [False, 'USD'])[1] if inv.get('currency_id') else 'USD',
                'state': inv.get('state', 'draft'),
                'invoice_date': inv.get('invoice_date'),
                'payment_status': inv.get('payment_state', 'not_paid'),
            })

        print_status(f"Retrieved {len(result)} invoices")
        return {
            'success': True,
            'count': len(result),
            'invoices': result
        }
    except Exception as e:
        print_status(f"Error fetching invoices: {e}", "error")
        return {
            'success': False,
            'error': str(e)
        }


@mcp.tool()
def get_payments(limit: int = 10) -> dict:
    """
    Fetch recent payments from Odoo.

    Args:
        limit: Maximum number of payments to return (default: 10)

    Returns:
        Dictionary with payment list and metadata
    """
    try:
        # First get payment IDs, then read them (empty domain = all payments)
        payment_ids = _execute('account.payment', 'search', [], limit=limit)

        if not payment_ids:
            return {
                'success': True,
                'count': 0,
                'payments': []
            }

        fields = ['id', 'name', 'amount', 'currency_id', 'payment_type', 'state',
                  'date', 'partner_id', 'journal_id']

        payments = _read('account.payment', payment_ids, fields=fields)

        result = []
        for pay in payments:
            result.append({
                'id': pay['id'],
                'name': pay.get('name', ''),
                'amount': float(pay.get('amount', 0)),
                'currency': pay.get('currency_id', [False, 'USD'])[1] if pay.get('currency_id') else 'USD',
                'payment_type': pay.get('payment_type', 'inbound'),
                'state': pay.get('state', 'draft'),
                'payment_date': pay.get('date'),
                'partner': pay.get('partner_id', [False, ''])[1] if pay.get('partner_id') else None,
                'journal': pay.get('journal_id', [False, ''])[1] if pay.get('journal_id') else '',
            })

        print_status(f"Retrieved {len(result)} payments")
        return {
            'success': True,
            'count': len(result),
            'payments': result
        }
    except Exception as e:
        print_status(f"Error fetching payments: {e}", "error")
        return {
            'success': False,
            'error': str(e)
        }


@mcp.tool()
def get_revenue(period: str = "this_month") -> dict:
    """
    Get total revenue for a period.

    Args:
        period: Time period - 'today', 'this_week', 'this_month', 'this_year', or 'all'

    Returns:
        Dictionary with revenue total and breakdown by invoice
    """
    try:
        today = datetime.now().date()
        if period == "today":
            date_from = today
        elif period == "this_week":
            date_from = today - timedelta(days=today.weekday())
        elif period == "this_month":
            date_from = today.replace(day=1)
        elif period == "this_year":
            date_from = today.replace(month=1, day=1)
        else:  # all
            date_from = None

        domain = [
            ('move_type', '=', 'out_invoice'),
            ('state', 'in', ['posted', 'paid'])
        ]
        if date_from:
            domain.append(('invoice_date', '>=', date_from.isoformat()))

        fields = ['id', 'name', 'partner_id', 'amount_total', 'invoice_date', 'state']
        invoices = _search_read('account.move', domain, fields=fields, order='invoice_date desc')

        total_revenue = 0.0
        result = []
        for inv in invoices[:20]:
            amount = float(inv.get('amount_total', 0))
            total_revenue += amount
            result.append({
                'id': inv['id'],
                'number': inv.get('name') or 'Draft',
                'partner': inv.get('partner_id', [False, 'No Partner'])[1] if inv.get('partner_id') else 'No Partner',
                'amount': amount,
                'date': inv.get('invoice_date'),
                'state': inv.get('state', 'draft'),
            })

        print_status(f"Retrieved revenue for {period}: {total_revenue:.2f}")
        return {
            'success': True,
            'period': period,
            'total_revenue': total_revenue,
            'invoice_count': len(invoices),
            'invoices': result
        }
    except Exception as e:
        print_status(f"Error fetching revenue: {e}", "error")
        return {
            'success': False,
            'error': str(e)
        }


@mcp.tool()
def get_expenses(period: str = "this_month") -> dict:
    """
    Get total expenses for a period.

    Args:
        period: Time period - 'today', 'this_week', 'this_month', 'this_year', or 'all'

    Returns:
        Dictionary with expense total and breakdown
    """
    try:
        today = datetime.now().date()
        if period == "today":
            date_from = today
        elif period == "this_week":
            date_from = today - timedelta(days=today.weekday())
        elif period == "this_month":
            date_from = today.replace(day=1)
        elif period == "this_year":
            date_from = today.replace(month=1, day=1)
        else:  # all
            date_from = None

        domain = [
            ('move_type', '=', 'in_invoice'),
            ('state', 'in', ['posted', 'paid'])
        ]
        if date_from:
            domain.append(('invoice_date', '>=', date_from.isoformat()))

        fields = ['id', 'name', 'partner_id', 'amount_total', 'invoice_date', 'state']
        invoices = _search_read('account.move', domain, fields=fields, order='invoice_date desc')

        total_expenses = 0.0
        result = []
        for inv in invoices[:20]:
            amount = float(inv.get('amount_total', 0))
            total_expenses += amount
            result.append({
                'id': inv['id'],
                'number': inv.get('name') or 'Draft',
                'partner': inv.get('partner_id', [False, 'No Partner'])[1] if inv.get('partner_id') else 'No Partner',
                'amount': amount,
                'date': inv.get('invoice_date'),
                'state': inv.get('state', 'draft'),
            })

        print_status(f"Retrieved expenses for {period}: {total_expenses:.2f}")
        return {
            'success': True,
            'period': period,
            'total_expenses': total_expenses,
            'bill_count': len(invoices),
            'expenses': result
        }
    except Exception as e:
        print_status(f"Error fetching expenses: {e}", "error")
        return {
            'success': False,
            'error': str(e)
        }


@mcp.tool()
def create_draft_invoice(
    partner_name: str,
    amount: float,
    description: str = "Services",
    currency: str = "USD"
) -> dict:
    """
    Create a draft invoice in Odoo (no approval required).

    Args:
        partner_name: Name of the customer
        amount: Invoice amount
        description: Invoice line description
        currency: Currency code (default: USD)

    Returns:
        Dictionary with created invoice ID and details
    """
    try:
        # Find or create partner
        partner_ids = _execute('res.partner', 'search', [('name', 'ilike', partner_name)], limit=1)
        if not partner_ids:
            partner_id = _execute('res.partner', 'create', None, create_data={
                'name': partner_name,
                'customer_rank': 1,
            })
            print_status(f"Created new partner: {partner_name}")
        else:
            partner_id = partner_ids[0]

        # Get currency
        currency_ids = _execute('res.currency', 'search', [('name', '=', currency)], limit=1)
        if not currency_ids:
            return {
                'success': False,
                'error': f'Currency {currency} not found'
            }
        currency_id = currency_ids[0]

        # Create draft invoice
        invoice_id = _execute('account.move', 'create', None, create_data={
            'move_type': 'out_invoice',
            'partner_id': partner_id,
            'currency_id': currency_id,
            'invoice_line_ids': [(0, 0, {
                'name': description,
                'quantity': 1,
                'price_unit': amount,
            })]
        })

        print_status(f"Created draft invoice {invoice_id} for {partner_name}: {amount} {currency}")
        return {
            'success': True,
            'invoice_id': invoice_id,
            'state': 'draft',
            'partner': partner_name,
            'amount': amount,
            'currency': currency
        }
    except Exception as e:
        print_status(f"Error creating draft invoice: {e}", "error")
        return {
            'success': False,
            'error': str(e)
        }


@mcp.tool()
def post_invoice(invoice_id: int) -> dict:
    """
    Post a draft invoice to final state (REQUIRES APPROVAL).

    WARNING: This action confirms the invoice and sends it to the customer.
    Use human-in-the-loop approval before calling this.

    Args:
        invoice_id: ID of the draft invoice to post

    Returns:
        Dictionary with posted invoice details
    """
    try:
        # Check if invoice exists and is in draft state
        invoices = _read('account.move', [invoice_id], ['id', 'state', 'name', 'amount_total'])
        if not invoices:
            return {
                'success': False,
                'error': f'Invoice {invoice_id} not found'
            }

        inv = invoices[0]
        if inv['state'] != 'draft':
            return {
                'success': False,
                'error': f'Invoice {invoice_id} is not in draft state (current: {inv["state"]})'
            }

        # Post the invoice
        _execute('account.move', 'action_post', record_ids=[invoice_id])

        # Read updated invoice
        updated = _read('account.move', [invoice_id], ['name', 'state', 'amount_total'])[0]

        print_status(f"Posted invoice {invoice_id} - APPROVED", "success")
        return {
            'success': True,
            'invoice_id': invoice_id,
            'state': updated['state'],
            'number': updated.get('name'),
            'amount': float(updated.get('amount_total', 0))
        }
    except Exception as e:
        print_status(f"Error posting invoice: {e}", "error")
        return {
            'success': False,
            'error': str(e)
        }


@mcp.tool()
def get_odoo_status() -> dict:
    """
    Get Odoo server status and connection info.

    Returns:
        Dictionary with connection status and system info
    """
    try:
        odoo = get_odoo_connection()

        # Get current user info via odoorpc
        User = odoo.env['res.users']
        user = User.read(odoo.env.uid, ['name', 'company_id'])[0]

        # Get company info
        Company = odoo.env['res.company']
        Currency = odoo.env['res.currency']

        # company_id is returned as [id, name] list in Odoo
        company_id_field = user.get('company_id')
        company_id = company_id_field[0] if company_id_field and isinstance(company_id_field, list) else False
        companies = []

        if company_id:
            company = Company.read(company_id, ['name', 'currency_id'])[0]
            company_name = company.get('name')
            currency_id_field = company.get('currency_id', False)
            currency_id = currency_id_field[0] if currency_id_field and isinstance(currency_id_field, list) else False
            if currency_id:
                currency_data = Currency.read(currency_id, ['name'])[0]
                currency = currency_data.get('name', 'USD') if isinstance(currency_data, dict) else 'USD'
            else:
                currency = 'USD'
        else:
            company_name = 'Unknown'
            currency = 'USD'

        # Get all companies
        company_ids = Company.search([])
        for co_id in company_ids:
            co = Company.read(co_id, ['name', 'currency_id'])[0]
            curr_id_field = co.get('currency_id', False)
            curr_id = curr_id_field[0] if curr_id_field and isinstance(curr_id_field, list) else False
            curr_name = 'USD'
            if curr_id:
                curr_data = Currency.read(curr_id, ['name'])[0]
                curr_name = curr_data.get('name', 'USD') if isinstance(curr_data, dict) else 'USD'
            companies.append({
                'id': co_id,
                'name': co.get('name'),
                'currency': curr_name
            })

        return {
            'success': True,
            'connected': True,
            'protocol': 'jsonrpc',
            'url': ODOO_URL,
            'database': ODOO_DB,
            'user': user.get('name'),
            'companies': companies
        }
    except Exception as e:
        print_status(f"Error getting Odoo status: {e}", "error")
        return {
            'success': False,
            'connected': False,
            'error': str(e)
        }


# Main entry point
if __name__ == "__main__":
    print_status("Starting Odoo MCP server (using odoorpc with JSON-RPC)...")
    print_status(f"Odoo URL: {ODOO_URL}")
    print_status(f"Database: {ODOO_DB}")
    print_status(f"User: {ODOO_USER}")
    mcp.run()
