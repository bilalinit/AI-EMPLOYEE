# LinkedIn MCP Server (Playwright) Documentation

**Part of:** Personal AI Employee - Gold Tier
**File:** `ai_employee_scripts/mcp_servers/linkedin_mcp.py`
**MCP Name:** `linkedin-mcp`

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
- [Session Management](#session-management)

---

## Overview

The LinkedIn MCP Server (Playwright) enables the AI Employee to interact with LinkedIn through browser automation. Unlike the API-based `linkedin-api` MCP, this server uses Playwright to automate the actual LinkedIn website, enabling additional features like **message reading and replying**.

### Features

| Feature | Description |
|---------|-------------|
| **Post to Feed** | Publish content to LinkedIn profile |
| **Reply to Messages** | Reply to LinkedIn conversations |
| **Get Messages** | Fetch LinkedIn message list |
| **Session Persistence** | Saves login session for subsequent runs |
| **Human-like Typing** | Types content with random delays to appear human |

### Key Files

| File | Location | Purpose |
|------|----------|---------|
| `linkedin_mcp.py` | `ai_employee_scripts/mcp_servers/` | MCP server implementation |
| `sessions/linkedin_mcp/` | `ai_employee_scripts/sessions/` | Saved browser session |

### Playwright vs API-based MCP

| Feature | `linkedin-mcp` (Playwright) | `linkedin-api` (API) |
|---------|---------------------------|---------------------|
| **Post to feed** | ✅ Yes | ✅ Yes |
| **Reply to messages** | ✅ Yes | ❌ No |
| **Get messages** | ✅ Yes | ❌ No |
| **Authentication** | Browser login (session) | OAuth tokens |
| **Reliability** | Medium (DOM changes can break) | High (stable API) |
| **Setup complexity** | Low (just log in) | Medium (developer app) |

---

## Architecture & Workflow

### System Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                  LINKEDIN MCP (PLAYWRIGHT)                      │
└─────────────────────────────────────────────────────────────────┘

     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
     │   LinkedIn   │     │linkedin_mcp  │     │  Playwright  │
     │   Website    │     │    .py       │     │   Browser    │
     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
            │                    │                    │
            ▼                    ▼                    ▼
     Login/Post          FastMCP Server      Chromium with
     /Messages          (linkedin-mcp)     Persistent Context
            │                    │                    │
            └────────────────────┴────────────────────┘
                                    │
                                    ▼
                         ┌─────────────────────────────────────┐
                         │    AI Employee System              │
                         │                                     │
                         │  1. Cron triggers /linkedin-messaging│
                         │  2. Get messages from inbox         │
                         │  3. Create replies for approval     │
                         │  4. Human approves → reply_message  │
                         └─────────────────────────────────────┘
```

### Session Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    SESSION MANAGEMENT FLOW                      │
└─────────────────────────────────────────────────────────────────┘

FIRST RUN:
┌────────────────┐      ┌────────────────┐      ┌────────────────┐
│ MCP Server     │ ──► │ Browser Opens  │ ──► │ User Logs In   │
│ Starts         │      │ (Headed Mode)  │      │ Manually       │
└────────────────┘      └────────────────┘      └────────┬───────┘
                                                        │
                                                        ▼
                                         ┌─────────────────────────┐
                                         │ Session Saved           │
                                         │ sessions/linkedin_mcp/  │
                                         │ (Cookies, Storage)      │
                                         └────────┬────────────────┘
                                                  │
                                                  ▼
                                         ┌─────────────────────────┐
                                         │ Browser Closes          │
                                         │ MCP Server Runs         │
                                         └─────────────────────────┘

SUBSEQUENT RUNS:
┌────────────────┐      ┌────────────────┐      ┌────────────────┐
│ MCP Server     │ ──► │ Session Loaded  │ ──► │ Browser Starts  │
│ Starts         │      │ From Disk      │      │ (Headless Mode) │
└────────────────┘      └────────────────┘      └────────┬───────┘
                                                        │
                                                        ▼
                                         ┌─────────────────────────┐
                                         │ Tools Ready to Use     │
                                         │ - post_content          │
                                         │ - reply_message         │
                                         │ - get_messages          │
                                         └─────────────────────────┘
```

---

## Setup Instructions

### Prerequisites

- Python 3.13+ with UV package manager
- LinkedIn account
- Chromium browser (installed by Playwright)

### Step 1: Install Playwright Browsers

Playwright needs to download Chromium:

```bash
cd ai_employee_scripts
uv run playwright install chromium
```

### Step 2: First-Time Setup

When you first run the MCP server, it will detect no existing session and open a browser for you to log in:

```bash
cd ai_employee_scripts
uv run python mcp_servers/linkedin_mcp.py
```

**What happens:**

1. **First Run Detected:**
   ```
   ╔════════════════════════════════════════════════════════╗
   ║         LinkedIn MCP Server for AI Employee           ║
   ╚════════════════════════════════════════════════════════╝

   📁 Session Path: /path/to/sessions/linkedin_mcp
   🔐 First Run: True

   ⚠️ FIRST RUN DETECTED!
   🌐 Browser will open for LinkedIn login...

   📝 Instructions:
     1️⃣ Browser will open
     2️⃣ Log in to LinkedIn
     3️⃣ Session will be saved automatically
     4️⃣ Wait for 'Login detected' message
   ```

2. **Browser Opens** - Chromium opens with LinkedIn login page

3. **You Log In** - Enter your credentials (optionally with 2FA)

4. **Session Saved** - Once login is detected, session is saved to `sessions/linkedin_mcp/`

5. **MCP Server Starts** - Server runs and waits for tool calls

### Step 3: Verify MCP Configuration

The LinkedIn MCP is configured in `AI_Employee_Vault/.mcp.json`:

```json
{
  "mcpServers": {
    "linkedin-mcp": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts",
        "run",
        "mcp_servers/linkedin_mcp.py"
      ],
      "env": {
        "PYTHONPATH": "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts",
        "LINKEDIN_MCP_SESSION": "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts/sessions/linkedin_mcp"
      }
    }
  }
}
```

**Important:** Update the paths to match your project directory if different from the example above.

### Step 4: Restart Claude Code

Restart Claude Code to load the MCP server. On subsequent runs, the server will:
- Load the saved session
- Verify it's still valid
- Start in headless mode (no visible browser)
- Be ready to handle tool calls

---

## Configuration

### Session Path

The session path can be configured via environment variable:

| Variable | Purpose | Default |
|----------|---------|---------|
| `LINKEDIN_MCP_SESSION` | Path to save browser session | `ai_employee_scripts/sessions/linkedin_mcp/` |

### File Locations

| File/Directory | Location | Purpose |
|----------------|----------|---------|
| `linkedin_mcp.py` | `ai_employee_scripts/mcp_servers/` | MCP server implementation |
| `sessions/linkedin_mcp/` | `ai_employee_scripts/sessions/` | Saved browser session (cookies, storage) |
| `logs/linkedin_*.png` | `AI_Employee_Vault/Logs/` | Debug screenshots |

### Browser Settings

| Setting | Value | Purpose |
|---------|-------|---------|
| **Browser** | Chromium | Playwright-controlled browser |
| **Viewport** | 1280x720 | Desktop viewport size |
| **Headless** | False (first run), True (subsequent) | Show browser for login, hide after |
| **Sandbox** | Disabled | Required for WSL compatibility |

---

## Available Tools

### 1. post_content

Post content to LinkedIn feed.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content` | string | Yes | Post content (supports line breaks, hashtags, mentions) |
| `visibility` | string | No | Post visibility: `PUBLIC` or `CONNECTIONS` (default: `PUBLIC`) |

**Returns:** Confirmation message with post details

**Example:**
```python
await mcp__linkedin_mcp__post_content(
    content="Just launched a new AI automation service! 🚀\n\n#AI #Automation",
    visibility="PUBLIC"
)
```

**What happens internally:**
1. Browser navigates to LinkedIn feed
2. Finds and clicks "Start a post" button
3. Types content with human-like delays (10-30ms per character)
4. Finds and clicks "Post" button
5. Returns confirmation

---

### 2. reply_message

Reply to a LinkedIn message conversation.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `conversation_url` | string | Yes | Full conversation URL (e.g., `https://www.linkedin.com/messaging/thread/ABC123/`) **OR** sender name to search |
| `message` | string | Yes | Reply message content |
| `wait_before_send` | int | No | Seconds to wait before sending (default: 2) |

**Returns:** Confirmation message with conversation details

**Example - Using URL:**
```python
await mcp__linkedin_mcp__reply_message(
    conversation_url="https://www.linkedin.com/messaging/thread/ABC123-DEF456/",
    message="Thanks for reaching out! I'll get back to you shortly.",
    wait_before_send=2
)
```

**Example - Using Sender Name:**
```python
await mcp__linkedin_mcp__reply_message(
    conversation_url="John Doe",
    message="Hi John, regarding our discussion..."
)
```

---

### 3. get_messages

Get LinkedIn messages/conversations.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `filter` | string | No | Filter messages: `all`, `unread`, or `pinned` (default: `all`) |
| `limit` | int | No | Maximum messages to return (default: 10) |
| `include_content` | bool | No | Fetch full message content (slower, default: `False`) |

**Returns:** JSON string with messages array

**Return format:**
```json
{
  "filter": "all",
  "requested_limit": 10,
  "total_found": 15,
  "total_processed": 10,
  "messages": [
    {
      "sender": "John Doe",
      "preview": "Hi, I saw your profile and...",
      "conversation_url": "https://www.linkedin.com/messaging/thread/ABC123/",
      "full_content": null,
      "is_unread": false,
      "timestamp": "2026-02-28 12:34:56"
    }
  ],
  "fetched_at": "2026-02-28T12:34:56.789012"
}
```

**Example:**
```python
# Get recent unread messages
messages = await mcp__linkedin_mcp__get_messages(
    filter="unread",
    limit=20,
    include_content=False
)
```

**Note:** When `include_content=True`, the server will click each conversation and fetch the full message text. This is slower but provides complete message history.

---

### 4. verify_connection

Verify LinkedIn connection status.

**Parameters:** None

**Returns:** JSON string with connection status

**Return format:**
```json
{
  "status": "connected",
  "session_path": "/path/to/sessions/linkedin_mcp",
  "first_run": false,
  "verified_at": "2026-02-28T12:34:56.789012"
}
```

**Example:**
```python
status = await mcp__linkedin_mcp__verify_connection()
```

---

## Usage Examples

### Example 1: Post to LinkedIn Feed

```python
await mcp__linkedin_mcp__post_content(
    content="""Excited to share that I've just launched my AI Employee automation system!

It's already helping me manage:
✉️ Email processing
📱 Social media posting
💰 Invoicing and accounting

#AI #Automation #Productivity"""
)
```

### Example 2: Check and Reply to Messages

```python
# Get unread messages
messages = await mcp__linkedin_mcp__get_messages(
    filter="unread",
    limit=10
)

# Parse and process each message
for msg in messages['messages']:
    sender = msg['sender']
    preview = msg['preview']
    url = msg['conversation_url']

    print(f"From: {sender}")
    print(f"Preview: {preview}")

    # Generate appropriate reply (would go to approval)
    # ... then reply:
    await mcp__linkedin_mcp__reply_message(
        conversation_url=url,
        message=f"Hi {sender.split()[0]}, thanks for your message! I'll review and get back to you shortly."
    )
```

### Example 3: Get Full Conversation Content

```python
# Get messages with full content
messages = await mcp__linkedin_mcp__get_messages(
    filter="all",
    limit=5,
    include_content=True
)

for msg in messages['messages']:
    if msg['full_content']:
        print(f"=== Conversation with {msg['sender']} ===")
        print(msg['full_content'])
        print()
```

### Example 4: Verify Session Before Posting

```python
# First verify connection
status = await mcp__linkedin_mcp__verify_connection()

import json
status_data = json.loads(status)

if status_data['status'] == 'connected':
    # Safe to post
    await mcp__linkedin_mcp__post_content(
        content="Today's update: Project milestones achieved! 🎉"
    )
else:
    print("Session expired - need to re-login")
```

---

## Integration with AI Employee

### Cron Automation

Daily at specific times, the LinkedIn messaging cron trigger runs:

```bash
0 9,17 * * * cd "/path/to/ai_employee_scripts" && uv run python scripts/linkedin_messaging_cron.py
```

**Workflow:**
1. Cron trigger executes `/linkedin-messaging` skill
2. Skill fetches unread messages via `get_messages()`
3. Creates reply drafts in `Pending_Approval/`
4. Human reviews and moves to `Approved/`
5. `/execute-approved` skill sends replies via `reply_message()`

### Skills That Use This MCP

| Skill | Purpose |
|-------|---------|
| `/linkedin-messaging` | Fetch and draft replies to LinkedIn messages |
| `/linkedin-posting` | Generate and post LinkedIn content |
| `/execute-approved` | Post approved content and send replies |

---

## Troubleshooting

### Problem: "First run detected every time"

**Symptom:** Browser opens for login every time, despite logging in previously.

**Solution:**
1. Check if session directory exists:
   ```bash
   ls -la ai_employee_scripts/sessions/linkedin_mcp/Default/Cookies
   ```
2. If missing or small (< 100 bytes), session wasn't saved properly
3. Ensure browser closed normally during first run (don't force quit)
4. Try manually removing the session directory and retry:
   ```bash
   rm -rf ai_employee_scripts/sessions/linkedin_mcp
   uv run python mcp_servers/linkedin_mcp.py
   ```

---

### Problem: "Could not find 'Start a post' button"

**Error:**
```
Error: Could not find 'Start a post' button. You might not be logged in.
```

**Solution:**
1. Check debug screenshot in `AI_Employee_Vault/Logs/linkedin_feed_*.png`
2. If login page shown, session has expired - re-login:
   ```bash
   rm -rf ai_employee_scripts/sessions/linkedin_mcp
   # Restart MCP server - will open browser for login
   ```
3. If LinkedIn changed UI, the selectors may need updating

---

### Problem: "Could not find message input box"

**Error (when replying):**
```
Error: Could not find message input box. The conversation URL might be invalid.
```

**Solution:**
1. Verify the conversation URL is correct
2. Try using sender name instead of URL:
   ```python
   await mcp__linkedin_mcp__reply_message(
       conversation_url="John Doe",  # Use name instead
       message="..."
   )
   ```
3. Check if conversation still exists in LinkedIn

---

### Problem: "No text input elements found"

**Error (when posting):**
```
Error: No text input elements found. LinkedIn may have changed their UI.
```

**Solution:**
1. Check debug screenshot in `AI_Employee_Vault/Logs/linkedin_modal_*.png`
2. LinkedIn may have updated their UI - selectors may need updating
3. Check `linkedin_mcp.py` for the selector list and update if needed

---

### Problem: "Timeout: Could not load LinkedIn page"

**Error:**
```
Timeout: Could not load LinkedIn page. This might be a network issue or LinkedIn is blocking automated access.
```

**Solution:**
1. Check internet connection
2. Try accessing LinkedIn manually in a browser
3. LinkedIn may be blocking automated access - wait and retry
4. Consider using a delay between operations

---

### Problem: Playwright browser not installed

**Error:**
```
Executable doesn't exist at /path/to/playwright/chromium
```

**Solution:**
```bash
cd ai_employee_scripts
uv run playwright install chromium
```

---

## Session Management

### How Sessions Work

1. **First Run:**
   - Browser opens in visible mode (`headless=False`)
   - You log in manually
   - Session is saved to `sessions/linkedin_mcp/`
   - Browser closes
   - MCP server starts

2. **Subsequent Runs:**
   - Session is loaded from disk
   - Browser starts in headless mode
   - Tools can immediately execute

3. **Session Expiration:**
   - LinkedIn sessions typically last 30-90 days
   - When expired, you'll need to re-login
   - Delete session directory to trigger fresh login

### Manually Clearing Session

To force a fresh login:

```bash
# Delete the session directory
rm -rf ai_employee_scripts/sessions/linkedin_mcp

# Restart MCP server - will prompt for login
```

### Session Location

The session is stored at:

```
ai_employee_scripts/sessions/linkedin_mcp/
├── Default/
│   ├── Cookies          # Saved cookies (login session)
│   ├── Local Storage/
│   └── Session Storage/
```

### Debug Screenshots

The server saves debug screenshots to `AI_Employee_Vault/Logs/`:

- `linkedin_feed_HHMMSS.png` - Screenshot after navigating to feed
- `linkedin_modal_HHMMSS.png` - Screenshot after clicking post button

These are useful for troubleshooting UI issues.

---

## Security Best Practices

1. **Session directory** - Contains login cookies, keep it private
2. **Don't share sessions** - Each installation should have its own session
3. **HTTPS only** - LinkedIn only works over HTTPS
4. **Human-like typing** - The server types with delays to appear human
5. **Approval workflow** - Always review messages/replies before sending

---

## Quick Reference

### MCP Tools

| Tool | Purpose |
|------|---------|
| `post_content()` | Post to LinkedIn feed |
| `reply_message()` | Reply to LinkedIn message |
| `get_messages()` | Get message list |
| `verify_connection()` | Check login status |

### Message Filters

| Filter | Description |
|--------|-------------|
| `all` | All messages |
| `unread` | Unread messages only |
| `pinned` | Pinned conversations only |

### Conversation URL Format

```
https://www.linkedin.com/messaging/thread/ABC123-DEF456/
```

You can also use sender name instead of URL.

---

## Comparison with API-based MCP

| Feature | `linkedin-mcp` (Playwright) | `linkedin-api` (API) |
|---------|---------------------------|---------------------|
| **Post to feed** | ✅ DOM automation | ✅ API call |
| **Reply to messages** | ✅ DOM automation | ❌ Not available |
| **Get messages** | ✅ DOM scraping | ❌ Not available |
| **Get profile** | ❌ Not implemented | ✅ API call |
| **Reliability** | Medium (DOM dependent) | High (stable API) |
| **Setup** | Login once | OAuth setup |
| **Rate limits** | None (human-like) | LinkedIn API limits |
| **Maintenance** | Selectors may break | API changes rarely |

**Recommendation:** Use `linkedin-mcp` (Playwright) for messaging features and `linkedin-api` (API) for posting to feed if you want maximum reliability.

---

**Last Updated:** February 28, 2026
**Part of:** Personal AI Employee Hackathon 0 - Gold Tier
