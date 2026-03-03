#!/usr/bin/env python3
"""
Gmail MCP Server for AI Employee

First Run:
  uv run python mcp_servers/gmail_mcp.py

  ✅ Checks for credentials.json → Found it!
  ✅ Checks for token_gmail.json → Not found
  ✅ Opens browser for OAuth → You authorize the app
  ✅ Saves token_gmail.json → Token stored for next runs

Second Run (token exists):
  ✅ Loads token from token_gmail.json
  ✅ Checks if expired → Refreshes if needed
  ✅ Builds Gmail service
  ✅ Starts MCP server, waits for Claude calls
"""

import sys
import os
import base64
import email
from pathlib import Path
from typing import Any

# MCP imports
from mcp.server.fastmcp import FastMCP

# Google imports
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow

# =============================================================================
# CONFIGURATION
# =============================================================================

# Gmail API Scopes - Updated to include SEND permission!
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',  # Read emails
    'https://www.googleapis.com/auth/gmail.send',      # Send emails
    'https://www.googleapis.com/auth/gmail.modify',    # Drafts, labels
]

# File locations
SCRIPT_DIR = Path(__file__).parent.parent
CREDENTIALS_FILE = SCRIPT_DIR / 'credentials.json'
TOKEN_FILE = SCRIPT_DIR / 'token_gmail.json'

# =============================================================================
# AUTHENTICATION
# =============================================================================

def print_status(message: str, emoji: str = "✅"):
    """Print status message to stderr (safe for MCP stdio transport)."""
    print(f"{emoji} {message}", file=sys.stderr, flush=True)


def authenticate() -> Credentials:
    """
    Authenticate with Gmail API using OAuth.

    Handles:
    - First-time OAuth flow
    - Token refresh
    - Loading existing tokens

    Returns:
        Valid Credentials object
    """
    print_status("Gmail MCP Server - Authentication", "📧")
    print_status("", "")

    creds = None

    # Step 1: Check for credentials.json
    if not CREDENTIALS_FILE.exists():
        print_status("credentials.json not found!", "❌")
        print_status(f"Looking at: {CREDENTIALS_FILE}", "🔍")
        print_status("", "")
        print_status("To set up Gmail API:", "📝")
        print_status("1. Go to https://console.cloud.google.com", "1️⃣")
        print_status("2. Create a project and enable Gmail API", "2️⃣")
        print_status("3. Configure OAuth consent screen", "3️⃣")
        print_status("4. Create OAuth 2.0 credentials (Desktop app)", "4️⃣")
        print_status("5. Download credentials.json to ai_employee_scripts/", "5️⃣")
        print_status("", "")
        print_status("For detailed instructions, see:", "📖")
        print_status("https://developers.google.com/gmail/api/quickstart/python", "🔗")
        raise FileNotFoundError("credentials.json not found")

    print_status(f"Found credentials.json", "✅")

    # Step 2: Check for existing token
    if TOKEN_FILE.exists():
        print_status(f"Found token_gmail.json", "✅")
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

            if creds and creds.valid:
                print_status("Token is valid, ready to go!", "✅")
                return creds
            elif creds and creds.expired and creds.refresh_token:
                print_status("Token expired, refreshing...", "🔄")
                try:
                    creds.refresh(Request())
                    # Save refreshed token
                    with open(TOKEN_FILE, 'w') as token:
                        token.write(creds.to_json())
                    print_status("Token refreshed successfully!", "✅")
                    return creds
                except Exception as e:
                    print_status(f"Refresh failed: {e}", "⚠️")
                    print_status("Need to re-authenticate...", "🔄")
                    creds = None
            else:
                print_status("Token invalid, need to re-authenticate...", "⚠️")
                creds = None
        except Exception as e:
            print_status(f"Error loading token: {e}", "⚠️")
            creds = None
    else:
        print_status("No existing token found", "ℹ️")

    # Step 3: Run OAuth flow for new token
    print_status("", "")
    print_status("Starting OAuth flow...", "🔐")
    print_status("Opening browser for authorization...", "🌐")

    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_FILE), SCOPES
        )

        # Generate authorization URL
        auth_url, _ = flow.authorization_url(prompt='consent')

        print_status("", "")
        print_status("=" * 60, "─")
        print_status("OPEN THIS URL IN YOUR BROWSER:", "🌐")
        print_status("=" * 60, "─")
        print_status(auth_url, "🔗")
        print_status("=" * 60, "─")
        print_status("", "")

        # Run local server flow (port 8080 for WSL compatibility)
        creds = flow.run_local_server(
            port=8080,
            open_browser=False
        )

        # Save credentials for next run
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

        print_status("", "")
        print_status("Authentication successful!", "✅")
        print_status(f"Token saved to: {TOKEN_FILE}", "💾")
        print_status("", "")

        return creds

    except Exception as e:
        print_status(f"OAuth flow failed: {e}", "❌")
        raise


def build_gmail_service(creds: Credentials):
    """Build Gmail API service with credentials."""
    try:
        service = build('gmail', 'v1', credentials=creds)
        return service
    except Exception as e:
        print_status(f"Failed to build Gmail service: {e}", "❌")
        raise


# =============================================================================
# MCP SERVER
# =============================================================================

# Initialize FastMCP server
mcp = FastMCP(
    "ai-gmail",
    instructions="Gmail operations: send emails, read emails, search emails, create drafts"
)

# Global service instance (initialized after auth)
gmail_service = None


def ensure_service():
    """Ensure Gmail service is initialized."""
    global gmail_service
    if gmail_service is None:
        creds = authenticate()
        gmail_service = build_gmail_service(creds)
    return gmail_service


# =============================================================================
# MCP TOOLS
# =============================================================================

@mcp.tool()
async def send_email(to: str, subject: str, body: str, cc: str = "") -> str:
    """Send an email via Gmail.

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Email body content (plain text)
        cc: Optional CC recipients (comma-separated)

    Returns:
        Message ID of sent email
    """
    service = ensure_service()
    print_status(f"Sending email to {to}...", "📤")

    try:
        # Build email message
        message = email.message.EmailMessage()
        message.set_content(body)
        message['To'] = to
        message['Subject'] = subject
        if cc:
            message['Cc'] = cc

        # Encode to base64url
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Send via Gmail API
        result = service.users().messages().send(
            userId='me',
            body={'raw': raw}
        ).execute()

        message_id = result['id']
        print_status(f"Email sent! ID: {message_id}", "✅")

        return f"Email sent successfully! Message ID: {message_id}"

    except HttpError as e:
        error_msg = f"Gmail API error: {e}"
        print_status(error_msg, "❌")
        return error_msg
    except Exception as e:
        error_msg = f"Failed to send email: {e}"
        print_status(error_msg, "❌")
        return error_msg


@mcp.tool()
async def read_email(message_id: str) -> str:
    """Read a specific email by message ID.

    Args:
        message_id: Gmail message ID

    Returns:
        Email content in readable format
    """
    service = ensure_service()
    print_status(f"Reading email {message_id}...", "📧")

    try:
        message = service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()

        # Extract headers
        headers = {}
        for h in message['payload'].get('headers', []):
            name = h['name']
            if name in ['From', 'To', 'Subject', 'Date', 'Cc']:
                headers[name] = h['value']

        # Get body
        body = ""
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8')
                        break
        elif 'body' in message['payload']:
            data = message['payload']['body'].get('data', '')
            if data:
                body = base64.urlsafe_b64decode(data).decode('utf-8')

        result = f"""From: {headers.get('From', 'Unknown')}
To: {headers.get('To', '')}
Subject: {headers.get('Subject', '')}
Date: {headers.get('Date', '')}

{body}
"""
        return result

    except HttpError as e:
        return f"Gmail API error: {e}"
    except Exception as e:
        return f"Failed to read email: {e}"


@mcp.tool()
async def search_emails(query: str, max_results: int = 10) -> str:
    """Search for emails matching a query.

    Args:
        query: Gmail search query (same syntax as Gmail search box)
        max_results: Maximum number of results (default: 10)

    Returns:
        List of matching emails with snippets
    """
    service = ensure_service()
    print_status(f"Searching for: {query}", "🔍")

    try:
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()

        messages = results.get('messages', [])

        if not messages:
            return "No emails found matching your query."

        # Get details for each message
        output = []
        for msg in messages[:max_results]:
            try:
                detail = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'Date']
                ).execute()

                headers = {}
                for h in detail['payload'].get('headers', []):
                    headers[h['name']] = h['value']

                snippet = detail.get('snippet', '')
                output.append(f"""
---
ID: {msg['id']}
From: {headers.get('From', 'Unknown')}
Subject: {headers.get('Subject', '')}
Date: {headers.get('Date', '')}
Preview: {snippet[:100]}...
""")
            except Exception as e:
                output.append(f"ID: {msg['id']} - Error: {e}")

        return "\n".join(output)

    except HttpError as e:
        return f"Gmail API error: {e}"
    except Exception as e:
        return f"Failed to search emails: {e}"


@mcp.tool()
async def list_emails(label: str = "INBOX", max_results: int = 10) -> str:
    """List recent emails from a label.

    Args:
        label: Gmail label (e.g., INBOX, SENT, DRAFT, SPAM)
        max_results: Maximum number of emails (default: 10)

    Returns:
        List of emails with summaries
    """
    service = ensure_service()
    print_status(f"Listing emails from {label}...", "📬")

    try:
        results = service.users().messages().list(
            userId='me',
            labelIds=[label],
            maxResults=max_results
        ).execute()

        messages = results.get('messages', [])

        if not messages:
            return f"No emails in {label}."

        # Get details for each message
        output = []
        for msg in messages[:max_results]:
            try:
                detail = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'Date']
                ).execute()

                headers = {}
                for h in detail['payload'].get('headers', []):
                    headers[h['name']] = h['value']

                snippet = detail.get('snippet', '')
                output.append(f"""
---
ID: {msg['id']}
From: {headers.get('From', 'Unknown')}
Subject: {headers.get('Subject', '')}
Date: {headers.get('Date', '')}
Preview: {snippet[:100]}...
""")
            except Exception as e:
                output.append(f"ID: {msg['id']} - Error: {e}")

        return "\n".join(output)

    except HttpError as e:
        return f"Gmail API error: {e}"
    except Exception as e:
        return f"Failed to list emails: {e}"


@mcp.tool()
async def draft_email(to: str, subject: str, body: str, cc: str = "") -> str:
    """Create a draft email (does not send).

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Email body content (plain text)
        cc: Optional CC recipients (comma-separated)

    Returns:
        Draft ID
    """
    service = ensure_service()
    print_status(f"Creating draft for {to}...", "📝")

    try:
        # Build email message
        message = email.message.EmailMessage()
        message.set_content(body)
        message['To'] = to
        message['Subject'] = subject
        if cc:
            message['Cc'] = cc

        # Encode to base64url
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Create draft via Gmail API
        result = service.users().drafts().create(
            userId='me',
            body={'message': {'raw': raw}}
        ).execute()

        draft_id = result['id']
        print_status(f"Draft created! ID: {draft_id}", "✅")

        return f"Draft created successfully! Draft ID: {draft_id}"

    except HttpError as e:
        error_msg = f"Gmail API error: {e}"
        print_status(error_msg, "❌")
        return error_msg
    except Exception as e:
        error_msg = f"Failed to create draft: {e}"
        print_status(error_msg, "❌")
        return error_msg


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Run the Gmail MCP server."""
    print_status("", "")
    print_status("╔════════════════════════════════════════════════════════╗", "📧")
    print_status("║         Gmail MCP Server for AI Employee              ║", "🤖")
    print_status("╚════════════════════════════════════════════════════════╝", "📧")
    print_status("", "")

    # Authenticate before starting MCP server
    try:
        creds = authenticate()
        gmail_service = build_gmail_service(creds)

        print_status("", "")
        print_status("Starting MCP server...", "🚀")
        print_status("Tools available: send_email, read_email, search_emails, list_emails, draft_email", "🛠️")
        print_status("", "")
        print_status("Server is running. Press Ctrl+C to stop.", "⏳")
        print_status("", "")

        # Start MCP server
        mcp.run(transport="stdio")

    except KeyboardInterrupt:
        print_status("", "")
        print_status("Gmail MCP Server stopped by user", "👋")
    except Exception as e:
        print_status("", "")
        print_status(f"Fatal error: {e}", "❌")
        raise


if __name__ == "__main__":
    main()
