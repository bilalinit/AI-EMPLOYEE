"""
Cloud MCP Servers

MCP servers for cloud agents (OpenAI Agents SDK integration).
These servers provide read-only and draft-only access to business systems.
"""

from .odoo_server import create_odoo_server, get_available_tools

__all__ = [
    "create_odoo_server",
    "get_available_tools"
]
