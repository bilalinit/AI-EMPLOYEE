# Gmail MCP Server Documentation

**Part of:** Personal AI Employee - Silver/Gold Tier
**File:** `ai_employee_scripts/mcp_servers/gmail_mcp.py`
**MCP Name:** `ai-gmail`

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
- [File Reference](#file-reference)

---

## Overview

The Gmail MCP Server enables the AI Employee to interact with Gmail through the Model Context Protocol (MCP). It provides tools for reading, searching, sending, and drafting emails.

### Features

| Feature | Description |
|---------|-------------|
| **Read Emails** | Fetch full email content by message ID |
| **Search Emails** | Gmail-style search queries |
| **List Emails** | Browse emails by label (INBOX, SENT, DRAFT, SPAM) |
| **Send Emails** | Compose and send emails via Gmail API |
| **Create Drafts** | Save email drafts without sending |
| **OAuth Authentication** | Secure token-based auth with auto-refresh |

### Key Files

| File | Purpose | Location |
|------|---------|----------|
| `gmail_mcp.py` | MCP server implementation | `ai_employee_scripts/mcp_servers/` |
| `credentials.json` | OAuth client secrets | `ai_employee_scripts/` |
| `token_gmail.json` | OAuth refresh token (auto-generated) | `ai_employee_scripts/` |
| `gmail_watcher.py` | Background email monitor | `ai_employee_scripts/watchers/` |

---

## Architecture & Workflow

### System Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     GMAIL MCP WORKFLOW                          │
└─────────────────────────────────────────────────────────────────┘

     ┌──────────────┐
     │  Claude Code │ ◄───── Calls MCP tools
     └──────┬───────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   MCP Server (gmail_mcp.py)                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  1. authenticate() → Validates/refreshes OAuth token     │  │
│  │  2. build_gmail_service() → Creates Gmail API client     │  │
│  │  3. Tool functions → Execute Gmail operations           │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  Gmail API    │
                    │ (googleapis)  │
                    └───────────────┘


┌─────────────────────────────────────────────────────────────────┐
│                   GMAIL WATCHER WORKFLOW                        │
└─────────────────────────────────────────────────────────────────┘

     ┌──────────────┐
     │ Orchestrator │ ◄───── Starts watcher
     └──────┬───────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│              GmailWatcher (gmail_watcher.py)                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  1. Polls Gmail every 2 minutes                          │  │
│  │  2. Checks for new emails (newer_than:1d -in:sent)      │  │
│  │  3. Creates task in Needs_Action/                       │  │
│  │  4. Saves full email to Inbox/                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Authentication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    GMAIL OAUTH FLOW                             │
└─────────────────────────────────────────────────────────────────┘

FIRST RUN:
┌────────────────┐      ┌────────────────┐      ┌────────────────┐
│ credentials.json│ ──► │   Browser      │ ──► │   Google       │
│ (Client Secret) │      │  Authorization │      │   OAuth Screen│
└────────────────┘      └────────────────┘      └───────┬────────┘
                                                        │
                                                        ▼
                                               ┌────────────────┐
                                               │Auth Code      │
                                               │redirect to    │
                                               │localhost:8080 │
                                               └───────┬────────┘
                                                       │
                                                       ▼
                                         ┌─────────────────────────┐
                                         │ token_gmail.json        │
                                         │ (Refresh Token Saved)   │
                                         └─────────────────────────┘

SUBSEQUENT RUNS:
┌────────────────┐      ┌────────────────┐      ┌────────────────┐
│ token_gmail    │ ──► │ Token Expired? │ ──► │ Auto-refresh     │
│ .json          │      │                │      │ (No user action)│
└────────────────┘      └────────────────┘      └────────────────┘
```

---

## Setup Instructions

### Prerequisites

- Python 3.13+ with UV package manager
- Google Cloud account
- Gmail account to monitor

### Step 1: Enable Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing one
3. Navigate to **APIs & Services** → **Library**
4. Search for "Gmail API" and click **Enable**

### Step 2: Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Choose **External** user type
3. Fill in:
   - App name: `AI Employee Gmail`
   - User support email: `your-email@gmail.com`
   - Developer contact: `your-email@gmail.com`
4. Add scopes (click **Add or remove scopes**):
   - `.../auth/gmail.readonly`
   - `.../auth/gmail.send`
   - `.../auth/gmail.modify`
5. Save and continue (skip other sections for testing)

### Step 3: Create OAuth Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **+ Create Credentials** → **OAuth client ID**
3. Application type: **Desktop app**
4. Name: `AI Employee Gmail`
5. Click **Create**
6. **Download** the JSON file and rename to `credentials.json`

### Step 4: Install Credentials

Place `credentials.json` in the scripts directory:

```bash
# From your project root
mv ~/Downloads/credentials.json ai_employee_scripts/
```

Your project structure should look like:

```
your-project/
├── ai_employee_scripts/
│   ├── credentials.json          # ← OAuth client secrets
│   ├── token_gmail.json          # ← Auto-generated after first auth
│   ├── mcp_servers/
│   │   └── gmail_mcp.py          # ← MCP server
│   └── watchers/
│       └── gmail_watcher.py      # ← Background monitor
└── AI_Employee_Vault/
    └── Logs/
        └── gmail_processed_ids.txt
```

### Step 5: First-Time Authentication

Run the MCP server to authenticate:

```bash
cd ai_employee_scripts
uv run python mcp_servers/gmail_mcp.py
```

**What happens:**

1. The server checks for `credentials.json`
   - ❌ **If missing:** Prints setup instructions to Google Cloud Console and exits
   - ✅ **If found:** Continues to token check

2. The server checks for `token_gmail.json`
   - ✅ **If exists and valid:** Skips authentication, starts MCP server
   - ❌ **If missing or invalid:** Starts OAuth flow

3. **OAuth flow begins** - The server will:
   - Generate an authorization URL (unique to your credentials)
   - Display it in your terminal with a banner
   - Start a local server on `http://localhost:8080`
   - Wait for you to authorize

4. **You authorize:**
   - Copy the URL displayed in your terminal
   - Open it in your browser
   - Sign in to Google and grant permissions
   - Google redirects back to `localhost:8080`

5. **Token saved automatically:**
   - The server receives the authorization code
   - Exchanges it for a refresh token
   - Saves to `ai_employee_scripts/token_gmail.json`
   - Starts the MCP server

**Expected Output:**

```
📧 ╔════════════════════════════════════════════════════════╗
🤖 ║         Gmail MCP Server for AI Employee              ║
📧 ╚════════════════════════════════════════════════════════╝

📧 Gmail MCP Server - Authentication

✅ Found credentials.json
ℹ️ No existing token found

🔐 Starting OAuth flow...
🌐 Opening browser for authorization...

────────────────────────────────────────────────────────────
🌐 OPEN THIS URL IN YOUR BROWSER:
────────────────────────────────────────────────────────────
🔗 https://accounts.google.com/o/oauth2/v2/auth?client_id=XXXX...
────────────────────────────────────────────────────────────

✅ Authentication successful!
💾 Token saved to: ai_employee_scripts/token_gmail.json

🚀 Starting MCP server...
🛠️ Tools available: send_email, read_email, search_emails, list_emails, draft_email

⏳ Server is running. Press Ctrl+C to stop.
```

**Important Notes:**
- The authorization URL is **unique each time** - don't bookmark it
- The local server on port 8080 must not be blocked by your firewall
- On WSL, copy the URL and open it in your **Windows browser**
- `token_gmail.json` contains your refresh token - keep it secret!

### Step 6: Enable MCP in Claude Code

The Gmail MCP server is configured in `AI_Employee_Vault/.mcp.json`. This file contains all MCP server configurations for the AI Employee project.

**Project MCP Configuration (`AI_Employee_Vault/.mcp.json`):**

```json
{
  "mcpServers": {
    "ai-gmail": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts",
        "run",
        "mcp_servers/gmail_mcp.py"
      ],
      "env": {
        "PYTHONPATH": "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts"
      }
    }
  }
}
```

**Alternative: Claude Code Settings**

You can also configure in `.claude/settings.local.json`:

```json
{
  "mcpServers": {
    "ai-gmail": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "./ai_employee_scripts",
        "run",
        "mcp_servers/gmail_mcp.py"
      ],
      "env": {
        "PYTHONPATH": "./ai_employee_scripts"
      }
    }
  }
}
```

**Important:** Update the paths to match your project directory if different from the example above.

Restart Claude Code to load the MCP server.

---

## Configuration

### Scopes

The Gmail MCP uses these OAuth scopes:

```python
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',  # Read emails
    'https://www.googleapis.com/auth/gmail.send',      # Send emails
    'https://www.googleapis.com/auth/gmail.modify',    # Drafts, labels
]
```

### File Locations

| File | Default Location | Purpose |
|------|------------------|---------|
| `credentials.json` | `ai_employee_scripts/` | OAuth client secrets |
| `token_gmail.json` | `ai_employee_scripts/` | Refresh token (auto-generated) |
| `gmail_processed_ids.txt` | `AI_Employee_Vault/Logs/` | Tracks processed emails |

**Important:** Both `gmail_mcp.py` (MCP server) and `gmail_watcher.py` (background monitor) share the same `credentials.json` and `token_gmail.json` files. You only need to authenticate once - the token will work for both.

---

## Available Tools

### 1. send_email

Send an email via Gmail API.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `to` | string | Yes | Recipient email address |
| `subject` | string | Yes | Email subject line |
| `body` | string | Yes | Email body content (plain text) |
| `cc` | string | No | CC recipients (comma-separated) |

**Returns:** Message ID of sent email

**Example:**
```python
await mcp__ai_gmail__send_email(
    to="client@example.com",
    subject="Invoice #1234",
    body="Hi, please find attached invoice..."
)
```

---

### 2. read_email

Read a specific email by message ID.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `message_id` | string | Yes | Gmail message ID |

**Returns:** Email content in readable format

**Return format:**
```
From: Sender Name <sender@example.com>
To: recipient@example.com
Subject: Email subject here
Date: Mon, 01 Jan 2026 12:00:00 +0000

Email body content here...
```

**Example:**
```python
content = await mcp__ai_gmail__read_email(
    message_id="1234567890abcdef"
)
```

---

### 3. search_emails

Search for emails using Gmail search syntax.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Gmail search query |
| `max_results` | int | No | Maximum results (default: 10) |

**Returns:** List of matching emails with snippets

**Return format:**
```
---
ID: 1234567890abcdef
From: Sender Name <sender@example.com>
Subject: Email subject
Date: Mon, 01 Jan 2026 12:00:00 +0000
Preview: First 100 characters of email...
---
ID: 0987654321fedcba
From: Another Sender <another@example.com>
Subject: Another subject
Date: Mon, 01 Jan 2026 11:00:00 +0000
Preview: Another email preview...
```

**Search Query Examples:**
- `from:client@example.com` - Emails from specific sender
- `subject:invoice` - Emails with "invoice" in subject
- `is:unread` - Unread emails only
- `newer_than:7d` - Emails from last 7 days
- `has:attachment` - Emails with attachments

**Example:**
```python
results = await mcp__ai_gmail__search_emails(
    query="from:client@example.com invoice",
    max_results=20
)
```

---

### 4. list_emails

List recent emails from a specific label.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `label` | string | No | Gmail label (default: INBOX) |
| `max_results` | int | No | Maximum results (default: 10) |

**Returns:** List of emails with summaries (same format as `search_emails`)

**Valid Labels:** `INBOX`, `SENT`, `DRAFT`, `SPAM`, `TRASH`, `IMPORTANT`

**Example:**
```python
emails = await mcp__ai_gmail__list_emails(
    label="INBOX",
    max_results=15
)
```

---

### 5. draft_email

Create a draft email (does not send).

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `to` | string | Yes | Recipient email address |
| `subject` | string | Yes | Email subject line |
| `body` | string | Yes | Email body content (plain text) |
| `cc` | string | No | CC recipients (comma-separated) |

**Returns:** Draft ID

**Example:**
```python
draft_id = await mcp__ai_gmail__draft_email(
    to="client@example.com",
    subject="Proposal Draft",
    body="Here's the proposal we discussed..."
)
```

---

## Usage Examples

### Example 1: Processing New Emails

```python
# List recent unread emails
emails = await mcp__ai_gmail__search_emails(
    query="is:unread -in:sent newer_than:1d",
    max_results=20
)

# Read each email and categorize
for email in emails:
    full_content = await mcp__ai_gmail__read_email(email['id'])
    # AI analyzes content and determines action
```

### Example 2: Sending a Reply

```python
# Draft and send reply
await mcp__ai_gmail__send_email(
    to="sender@example.com",
    subject="Re: Project Update",
    body="Thanks for the update! I'll review and get back to you."
)
```

### Example 3: Creating Invoice Follow-up

```python
# Search for unpaid invoice emails
invoices = await mcp__ai_gmail__search_emails(
    query="subject:invoice unpaid"
)

# Send follow-up
for invoice in invoices:
    await mcp__ai_gmail__send_email(
        to=invoice['from'],
        subject=f"Follow-up: {invoice['subject']}",
        body="Just following up on the unpaid invoice..."
    )
```

---

## Integration with AI Employee

### GmailWatcher (Background Monitoring)

The `GmailWatcher` runs as a background process that:

1. **Polls every 2 minutes** for new emails
2. **Search query:** `newer_than:1d -in:sent`
3. **Creates tasks** in `Needs_Action/TASK_EMAIL_*.md`
4. **Saves full emails** in `Inbox/EMAIL_*.md`
5. **Tracks processed IDs** in `Logs/gmail_processed_ids.txt`

### Workflow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ GmailWatcher │ ──► │   Inbox/     │ ──► │ Needs_Action/│
│  (polling)   │     │ EMAIL_*.md   │     │ TASK_*.md    │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                                                  ▼
                                          ┌──────────────┐
                                          │ Claude Code  │
                                          │ /process-tasks│
                                          └──────┬───────┘
                                                  │
                                                  ▼
                                          ┌──────────────┐
                                          │    Reply?    │
                                          └──────┬───────┘
                                                  │
                                    ┌─────────────┴─────────────┐
                                    ▼                           ▼
                            ┌──────────────┐           ┌──────────────┐
                            │ Gmail MCP    │           │    Done/     │
                            │ Send Reply   │           │              │
                            └──────────────┘           └──────────────┘
```

### Starting the GmailWatcher

```bash
cd ai_employee_scripts

# Direct run (for testing)
uv run python watchers/gmail_watcher.py

# Via orchestrator (recommended - runs all watchers)
uv run python orchestrator.py ../AI_Employee_Vault

# Via watchdog (production - auto-restarts if crashed)
uv run python watchdog.py
```

**What the watcher does:**
- Polls Gmail every **2 minutes** (default, configurable)
- Query: `newer_than:1d -in:sent` (emails from last day, excluding sent)
- Creates task file in `Needs_Action/TASK_EMAIL_*.md`
- Saves full email in `Inbox/EMAIL_*.md`
- Tracks processed message IDs in `Logs/gmail_processed_ids.txt`

---

## Troubleshooting

### Problem: "credentials.json not found"

**Error:**
```
📧 Gmail MCP Server - Authentication

❌ credentials.json not found!
🔍 Looking at: /path/to/ai_employee_scripts/credentials.json

📝 To set up Gmail API:
1️⃣ Go to https://console.cloud.google.com
2️⃣ Create a project and enable Gmail API
3️⃣ Configure OAuth consent screen
4️⃣ Create OAuth 2.0 credentials (Desktop app)
5️⃣ Download credentials.json to ai_employee_scripts/

📖 For detailed instructions, see:
🔗 https://developers.google.com/gmail/api/quickstart/python

FileNotFoundError: credentials.json not found
```

**Solution:**
1. Verify `credentials.json` exists in `ai_employee_scripts/`
2. Check file permissions: `ls -la ai_employee_scripts/credentials.json`
3. Re-download from Google Cloud Console if needed (see Step 3 above)

---

### Problem: "Redirect URI mismatch"

**Error:**
```
Error: redirect_uri_mismatch
The redirect URI in the request, http://localhost:8080, does not match...
```

**Solution:**
1. Go to Google Cloud Console → Credentials
2. Edit your OAuth client ID
3. Add `http://localhost:8080` to Authorized redirect URIs
4. Save and retry

---

### Problem: "Token expired - refresh failed"

**Error:**
```
⚠️ Token expired, refreshing...
⚠️ Refresh failed: Token has been expired or revoked.
```

**Solution:**
```bash
# Delete old token
rm ai_employee_scripts/token_gmail.json

# Re-authenticate
cd ai_employee_scripts
uv run python mcp_servers/gmail_mcp.py
```

---

### Problem: "Permission denied"

**Error:**
```
HttpError 403: Insufficient Permission
```

**Solution:**
1. Check OAuth consent screen has required scopes
2. Delete `token_gmail.json` and re-authenticate
3. Verify scopes in code match those in Google Console

---

### Problem: "No emails found"

**Symptom:** `list_emails` returns no results

**Solution:**
1. Verify you have emails in the requested label
2. Try a broader search: `query=""` or `label="INBOX"`
3. Check Gmail API is enabled in Google Console
4. Verify authentication with `search_emails` using a simple query

---

### Problem: "Watcher not creating tasks"

**Symptom:** GmailWatcher runs but no tasks appear in `Needs_Action/`

**Solution:**
1. Check watcher logs: `tail -f AI_Employee_Vault/Logs/orchestrator_*.log`
2. Verify processed IDs file: `AI_Employee_Vault/Logs/gmail_processed_ids.txt`
3. Test search query manually in Gmail web interface
4. Check for circuit breaker status: `AI_Employee_Vault/Logs/circuit_breakers.json`

---

### Problem: "Port 8080 already in use"

**Error:**
```
OSError: [Errno 48] Address already in use
```

**Solution:**
```bash
# Find process using port 8080
lsof -i :8080

# Kill the process or wait for it to finish
# Or modify port in gmail_mcp.py:
creds = flow.run_local_server(port=8081, open_browser=False)
```

---

### Debug Mode

Enable verbose logging by modifying `gmail_mcp.py`:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or check watcher logs:

```bash
tail -f AI_Employee_Vault/Logs/orchestrator_*.log
```

---

## File Reference

### gmail_mcp.py Structure

```
gmail_mcp.py
├── CONFIGURATION
│   ├── SCOPES (OAuth permissions)
│   ├── CREDENTIALS_FILE (credentials.json path)
│   └── TOKEN_FILE (token_gmail.json path)
│
├── AUTHENTICATION
│   ├── authenticate() → Main auth flow
│   ├── build_gmail_service() → Create API client
│   └── ensure_service() → Lazy init service
│
├── MCP TOOLS
│   ├── send_email() → Send via Gmail API
│   ├── read_email() → Fetch full message
│   ├── search_emails() → Gmail search
│   ├── list_emails() → Browse by label
│   └── draft_email() → Create draft
│
└── MAIN ENTRY POINT
    └── main() → Start MCP server
```

### gmail_watcher.py Structure

```
gmail_watcher.py
├── CONFIGURATION
│   ├── SCOPES (readonly for watcher)
│   ├── check_interval (default: 120s)
│   └── credentials_path
│
├── AUTHENTICATION
│   └── _authenticate() → OAuth flow
│
├── STATE MANAGEMENT
│   ├── _load_processed_ids() → Load state
│   └── _save_processed_ids() → Persist state
│
├── WATCHER METHODS
│   ├── check_for_updates() → Poll Gmail API
│   ├── get_item_id() → Return message ID
│   ├── create_action_file() → Create task + inbox file
│   └── run() → Main polling loop
│
└── HELPER METHODS
    ├── _get_email_body() → Extract email content
    ├── _determine_priority() → Classify importance
    └── _sanitize_filename() → Safe filenames
```

---

## Quick Reference

### Common Gmail Search Queries

| Query | Description |
|-------|-------------|
| `is:unread` | Unread emails |
| `from:sender@example.com` | From specific sender |
| `subject:keyword` | Subject contains keyword |
| `has:attachment` | Has attachments |
| `newer_than:7d` | Last 7 days |
| `-in:sent` | Exclude sent items |
| `label:important` | In Important label |

### MCP Tools Quick Reference

| Tool | Purpose |
|------|---------|
| `send_email()` | Send an email |
| `read_email()` | Read full email by ID |
| `search_emails()` | Search with Gmail query |
| `list_emails()` | Browse by label |
| `draft_email()` | Save as draft |

---

**Last Updated:** February 28, 2026
**Part of:** Personal AI Employee Hackathon 0 - Silver/Gold Tier
