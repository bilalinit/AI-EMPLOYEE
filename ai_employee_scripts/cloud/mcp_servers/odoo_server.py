"""
Odoo MCP Server for Cloud Agents

READ-ONLY + DRAFT-ONLY access to Odoo for cloud agents.
Per hackathon requirements: Cloud can read data and create drafts,
but CANNOT post/finalize invoices (local-only operation).

Security: This server only exposes safe operations for cloud deployment.
"""

import os
import json
from typing import Optional, Any, Dict
from pathlib import Path

# FastMCP for MCP server
try:
    from mcp.server.fastmcp import FastMCP
    FASTMCP_AVAILABLE = True
except ImportError:
    FastMCP = None
    FASTMCP_AVAILABLE = False

# Odoo RPC imports
try:
    import odoorpc
    ODOORPC_AVAILABLE = True
except ImportError:
    odoorpc = None
    ODOORPC_AVAILABLE = False

# Configuration
try:
    from ..config.settings import get_settings
except ImportError:
    # For standalone testing, use default config
    def get_settings():
        class Settings:
            vault_path = Path(".")
        return Settings()

# Load environment from .env file (for subprocess execution)
try:
    from dotenv import load_dotenv
    ENV_FILE = Path(__file__).parent.parent.parent / '.env'
    if ENV_FILE.exists():
        load_dotenv(ENV_FILE)
except ImportError:
    pass


# ============================================================================
# ODOO CONNECTION (Read-Only)
# ============================================================================

def get_odoo_connection():
    """
    Establish read-only connection to Odoo via JSON-RPC.

    Returns:
        odoorpc.ODOO connection object
    """
    if not ODOORPC_AVAILABLE:
        raise ImportError("odoorpc not installed. Install with: uv add odoorpc")

    settings = get_settings()

    # Odoo configuration from environment
    url = os.getenv("ODOO_URL", "http://localhost:8069")
    db = os.getenv("ODOO_DB", "odoo")
    user = os.getenv("ODOO_USER", "admin")
    password = os.getenv("ODOO_PASSWORD", "admin")

    try:
        # Parse URL to get hostname
        hostname = url.replace("http://", "").replace("https://", "")
        hostname = hostname.split(":")[0] if ":" in hostname else hostname

        odoo = odoorpc.ODOO(hostname, port=8069, protocol='jsonrpc')
        odoo.login(db, user, password)

        return odoo
    except Exception as e:
        raise ConnectionError(f"Failed to connect to Odoo: {e}")


# ============================================================================
# MCP SERVER FACTORY
# ============================================================================

def create_odoo_server() -> Optional[FastMCP]:
    """
    Create and configure the Odoo MCP server for cloud agents.

    Returns:
        FastMCP server instance with read-only and draft-only tools
    """
    if not FASTMCP_AVAILABLE:
        print("Warning: FastMCP not installed. Odoo server not created.")
        print("Install with: uv add mcp")
        return None

    if not ODOORPC_AVAILABLE:
        print("Warning: odoorpc not installed. Odoo server not created.")
        print("Install with: uv add odoorpc")
        return None

    # Create FastMCP server
    mcp = FastMCP(
        "odoo_cloud",
        instructions="""Odoo Read-Only + Draft-Only Access for Cloud Agents.

You have READ access to:
- Customer information (names, emails, balances, payment terms)
- Pricing data (service rates, hourly rates)
- Invoice history (past invoices, payment status)

You can CREATE:
- Draft invoices (state: draft, not posted)

You CANNOT:
- Post or finalize invoices
- Modify existing invoices
- Make payments
- Modify accounting data

This is a security restriction - posting/finalizing requires human approval
and is done by the local agent with full credentials.
"""
    )

    # ========================================================================
    # REGISTER TOOLS
    # ========================================================================

    @mcp.tool()
    def get_customer(partner_name: str) -> str:
        """
        Get customer information from Odoo (READ-ONLY).

        Args:
            partner_name: Customer name to search for

        Returns:
            Customer details including contact info, balance, payment terms
        """
        try:
            odoo = get_odoo_connection()
            Partner = odoo.env['res.partner']

            # Search for partner
            partner_ids = Partner.search([('name', 'ilike', partner_name)], limit=1)

            if not partner_ids:
                odoo.logout()
                return json.dumps({
                    "success": False,
                    "error": f"Customer not found: {partner_name}"
                })

            # Read partner details
            partners = Partner.read(partner_ids, [
                'name', 'email', 'phone', 'street', 'city',
                'country_id', 'website', 'lang', 'supplier_rank',
                'total_invoiced', 'debit', 'credit'
            ])

            odoo.logout()

            partner = partners[0]
            return json.dumps({
                "success": True,
                "data": {
                    "id": partner.get('id'),
                    "name": partner.get('name'),
                    "email": partner.get('email'),
                    "phone": partner.get('phone'),
                    "address": f"{partner.get('street', '')}, {partner.get('city', '')}",
                    "country": partner.get('country_id', [False, ''])[1] if isinstance(partner.get('country_id'), list) else None,
                    "website": partner.get('website'),
                    "language": partner.get('lang'),
                    "total_invoiced": partner.get('total_invoiced', 0),
                    "debit": partner.get('debit', 0),  # Amount customer owes
                    "credit": partner.get('credit', 0)  # Amount overpaid (credit balance)
                }
            })

        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"{type(e).__name__}: {str(e)}"
            })

    @mcp.tool()
    def search_partners(search_term: str, limit: int = 10) -> str:
        """
        Search for customers/vendors in Odoo (READ-ONLY).

        Args:
            search_term: Search term (searches name, email, phone)
            limit: Maximum results (default: 10)

        Returns:
            List of matching partners
        """
        try:
            odoo = get_odoo_connection()
            Partner = odoo.env['res.partner']

            # Search by name, email, or phone
            partner_ids = Partner.search([
                '|', '|',
                ('name', 'ilike', search_term),
                ('email', 'ilike', search_term),
                ('phone', 'ilike', search_term)
            ], limit=limit)

            partners = Partner.read(partner_ids, ['name', 'email', 'phone', 'supplier_rank'])

            odoo.logout()

            return json.dumps({
                "success": True,
                "count": len(partners),
                "data": [
                    {
                        "id": p.get('id'),
                        "name": p.get('name'),
                        "email": p.get('email'),
                        "phone": p.get('phone'),
                        "is_vendor": bool(p.get('supplier_rank'))
                    }
                    for p in partners
                ]
            })

        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"{type(e).__name__}: {str(e)}"
            })

    @mcp.tool()
    def get_invoice_history(partner_name: str, limit: int = 10) -> str:
        """
        Get customer's invoice history (READ-ONLY).

        Args:
            partner_name: Customer name
            limit: Maximum invoices to return (default: 10)

        Returns:
            List of past invoices with amounts and payment status
        """
        try:
            odoo = get_odoo_connection()
            Partner = odoo.env['res.partner']
            Invoice = odoo.env['account.move']

            # Find partner
            partner_ids = Partner.search([('name', 'ilike', partner_name)], limit=1)

            if not partner_ids:
                odoo.logout()
                return json.dumps({
                    "success": False,
                    "error": f"Customer not found: {partner_name}"
                })

            partner_id = partner_ids[0]

            # Get customer invoices
            invoice_ids = Invoice.search([
                ('move_type', '=', 'out_invoice'),
                ('partner_id', '=', partner_id)
            ], order='invoice_date desc', limit=limit)

            invoices = Invoice.read(invoice_ids, [
                'name', 'invoice_date', 'amount_total',
                'state', 'payment_state', 'amount_residual'
            ])

            odoo.logout()

            return json.dumps({
                "success": True,
                "customer": partner_name,
                "count": len(invoices),
                "data": [
                    {
                        "invoice": inv.get('name'),
                        "date": inv.get('invoice_date'),
                        "amount": inv.get('amount_total', 0),
                        "state": inv.get('state'),  # draft, posted, cancelled
                        "payment_status": inv.get('payment_state'),  # not_paid, partial, paid
                        "amount_due": inv.get('amount_residual', 0)  # Amount still owed
                    }
                    for inv in invoices
                ]
            })

        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"{type(e).__name__}: {str(e)}"
            })

    @mcp.tool()
    def get_pricing(service_type: str = "") -> str:
        """
        Get pricing information (READ-ONLY).

        This reads from a pricing lookup. In a real implementation,
        this would query a product/service price list from Odoo.

        Args:
            service_type: Type of service (e.g., "consulting", "development", "design")

        Returns:
            Pricing information for the service type
        """
        # Default pricing structure (can be extended to read from Odoo products)
        pricing_data = {
            "consulting": {
                "hourly_rate": 150,
                "daily_rate": 1200,
                "weekly_rate": 5000
            },
            "development": {
                "hourly_rate": 125,
                "daily_rate": 1000,
                "weekly_rate": 4200
            },
            "design": {
                "hourly_rate": 100,
                "daily_rate": 800,
                "weekly_rate": 3500
            },
            "video_editing": {
                "hourly_rate": 80,
                "project_based": True
            }
        }

        if service_type and service_type.lower() in pricing_data:
            return json.dumps({
                "success": True,
                "service_type": service_type,
                "pricing": pricing_data[service_type.lower()]
            })

        # Return all pricing if no specific type requested
        return json.dumps({
            "success": True,
            "available_services": list(pricing_data.keys()),
            "all_pricing": pricing_data
        })

    @mcp.tool()
    def create_draft_invoice(partner_name: str, amount: float, description: str, hours: Optional[float] = None, rate: Optional[float] = None) -> str:
        """
        Create a DRAFT invoice in Odoo (DRAFT-ONLY, not posted).

        This creates a draft invoice that requires human approval and posting
        by the local agent. The draft is saved in Odoo but not finalized.

        Args:
            partner_name: Customer name
            amount: Invoice amount (if hours/rate not provided)
            description: Line item description
            hours: Optional hours worked (overrides amount if provided with rate)
            rate: Optional hourly rate (overrides amount if provided with hours)

        Returns:
            Draft invoice details (invoice_id, state, url for human review)
        """
        try:
            odoo = get_odoo_connection()
            Partner = odoo.env['res.partner']
            Invoice = odoo.env['account.move']
            Journal = odoo.env['account.journal']

            # Find or create partner
            partner_ids = Partner.search([('name', 'ilike', partner_name)], limit=1)

            if not partner_ids:
                # Create new partner
                partner_id = Partner.create({'name': partner_name})
            else:
                partner_id = partner_ids[0]

            # Calculate amount from hours/rate if provided
            if hours is not None and rate is not None:
                calculated_amount = hours * rate
            else:
                calculated_amount = amount

            # Find default Sales Journal (required for invoice creation)
            journal_ids = Journal.search([
                ('type', '=', 'sale'),
                ('company_id', '=', odoo.env.user.company_id.id)
            ], limit=1)

            if not journal_ids:
                odoo.logout()
                return json.dumps({
                    "success": False,
                    "error": "No Sales Journal found in Odoo. Please configure a Sales Journal in Accounting > Configuration > Journals"
                })

            journal_id = journal_ids[0]

            # Get income account from the journal (use default_account_id for Sales journals)
            journal_data = Journal.read(journal_id, ['default_account_id'])[0]
            income_account_id = journal_data.get('default_account_id')

            # Handle many2one field format: [id, name] - extract the id
            if isinstance(income_account_id, list):
                income_account_id = income_account_id[0] if income_account_id else False

            if not income_account_id:
                odoo.logout()
                return json.dumps({
                    "success": False,
                    "error": "Sales Journal has no default account configured. Please configure the journal's default account."
                })

            # Create DRAFT invoice (not posted)
            invoice_id = Invoice.create({
                'move_type': 'out_invoice',
                'partner_id': partner_id,
                'journal_id': journal_id,
                'invoice_date': False,  # Let Odoo set default
                'invoice_line_ids': [(0, 0, {
                    'name': description,
                    'quantity': 1 if hours is None else hours,
                    'price_unit': calculated_amount if hours is None else rate,
                    'account_id': income_account_id,
                })]
            })

            # Read the created draft invoice
            invoice = Invoice.read(invoice_id, ['name', 'state', 'amount_total'])[0]

            odoo.logout()

            return json.dumps({
                "success": True,
                "invoice_id": invoice_id,
                "invoice_number": invoice.get('name'),  # Will be False/None for drafts
                "amount": invoice.get('amount_total'),
                "customer": partner_name,
                "state": invoice.get('state'),  # Should be "draft"
                "description": description,
                "note": "This is a DRAFT invoice. It requires human approval and posting by the local agent.",
                "url": f"http://localhost:8069/web#id={invoice_id}&model=account.move"
            })

        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"{type(e).__name__}: {str(e)}"
            })

    @mcp.tool()
    def get_available_tools() -> str:
        """
        List all available tools in this Odoo MCP server.

        Returns:
            List of available tools and their purposes
        """
        return json.dumps({
            "success": True,
            "server": "odoo_cloud",
            "tools": [
                {
                    "name": "get_customer",
                    "purpose": "Get detailed customer information (read-only)",
                    "access": "read"
                },
                {
                    "name": "search_partners",
                    "purpose": "Search for customers/vendors by name/email/phone",
                    "access": "read"
                },
                {
                    "name": "get_invoice_history",
                    "purpose": "Get customer's past invoices and payment status",
                    "access": "read"
                },
                {
                    "name": "get_pricing",
                    "purpose": "Get pricing information for services",
                    "access": "read"
                },
                {
                    "name": "create_draft_invoice",
                    "purpose": "Create a draft invoice (not posted, requires approval)",
                    "access": "draft"
                }
            ],
            "security_note": "This server does NOT have post_invoice or payment capabilities. Posting/finalizing invoices is done by the local agent with full credentials."
        })

    return mcp


def get_available_tools() -> list:
    """
    Get list of available tool names for documentation.

    Returns:
        List of tool names available in this server
    """
    return [
        "get_customer",
        "search_partners",
        "get_invoice_history",
        "get_pricing",
        "create_draft_invoice",
        "get_available_tools"
    ]


# ============================================================================
# MAIN (for standalone testing)
# ============================================================================

if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("Odoo Cloud MCP Server")
    print("Read-Only + Draft-Only Odoo Access for Cloud Agents")
    print("=" * 60)
    print()

    if not FASTMCP_AVAILABLE:
        print("ERROR: FastMCP not installed")
        print("Install with: uv add mcp")
        sys.exit(1)

    if not ODOORPC_AVAILABLE:
        print("ERROR: odoorpc not installed")
        print("Install with: uv add odoorpc")
        sys.exit(1)

    # Show configuration
    url = os.getenv("ODOO_URL", "http://localhost:8069")
    db = os.getenv("ODOO_DB", "odoo")
    user = os.getenv("ODOO_USER", "admin")

    print(f"Configuration:")
    print(f"  URL: {url}")
    print(f"  Database: {db}")
    print(f"  User: {user}")
    print()

    print("Available Tools:")
    for tool in get_available_tools():
        print(f"  - {tool}")
    print()

    print("Security: READ-ONLY + DRAFT-ONLY (no posting/finalizing)")
    print()

    print("Starting MCP server (stdio)...")
    print("Press Ctrl+C to stop")
    print()

    try:
        mcp = create_odoo_server()
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        print("\nServer stopped")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
