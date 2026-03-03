# LinkedInWatcher Documentation

## Overview

The LinkedInWatcher monitors LinkedIn for new unread messages using Playwright browser automation. (Connection request monitoring is planned for future release). It doesn't require the LinkedIn API - instead, it automates the LinkedIn website directly.

## Architecture

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  LinkedIn Web   │      │   Playwright    │      │    Vault        │
│  (messages)     │─────▶│   browser       │─────▶│   stores        │
│                 │      │   automation    │      │   message+task  │
└─────────────────┘      └─────────────────┘      └─────────────────┘
        │
        ▼
   Persistent Session
  (first run: login)
  (subsequent: auto-login)
```

### Workflow

```
First Run:
├── 1. Open browser (visible, not headless)
├── 2. Navigate to LinkedIn messaging
├── 3. User logs in manually
├── 4. Session saved to sessions/linkedin/
└── 5. Browser closes, monitoring begins

Subsequent Runs:
├── 1. Open browser (headless, with saved session)
├── 2. Navigate to LinkedIn messaging (auto-logged in)
├── 3. Check for unread messages
├── 4. Save messages to Inbox
├── 5. Create tasks in Needs_Action
└── 6. Browser closes

Every Check (5 min):
├── 1. Launch browser with saved session
├── 2. Navigate to messaging?filter=unread
├── 3. Scrape unread messages
├── 4. Filter already-seen messages
└── 5. Create tasks for new messages
```

## Key Features

### Playwright Browser Automation

Uses Playwright's persistent browser context:

```python
browser = p.chromium.launch_persistent_context(
    user_data_dir=str(self.session_path),
    headless=headless,
    args=['--no-sandbox', '--disable-setuid-sandbox']
)
```

| Feature | Description |
|---------|-------------|
| **Persistent Context** | Session (cookies, localStorage) saved to disk |
| **Headless Mode** | Subsequent runs run invisibly |
| **WSL Compatible** | Uses sandbox flags for WSL compatibility |

### Session Persistence

```
sessions/linkedin/
├── [Session data managed by Chromium]
└── Includes: cookies, localStorage, sessionStorage
```

| Run Mode | Headless | Browser Visible |
|----------|----------|-----------------|
| **First Run** | No | ✅ Yes (for login) |
| **Subsequent** | Yes | ❌ No |

### State Persistence

Seen messages are tracked (connection request tracking prepared for future):

```json
{
  "messages": ["hash1", "hash2", ...],
  "requests": []
}
```

Stored at: `AI_Employee_Vault/Logs/linkedin_state.json`

### Debug Artifacts

For troubleshooting, the watcher saves:

| Artifact | Location | Purpose |
|----------|----------|---------|
| **Screenshot** | `Logs/linkedin_debug.png` | Visual debugging |
| **HTML Dump** | `Logs/linkedin_debug.html` | DOM inspection |

## Constructor

```python
LinkedInWatcher(
    vault_path: str,                  # Path to AI_Employee_Vault
    session_path: str = None,         # Path to store session (default: sessions/linkedin)
    check_interval: int = 300         # Seconds between checks (default: 5 min)
)
```

## Playwright Setup

### 1. Install Playwright

```bash
cd ai_employee_scripts
uv sync
```

### 2. Install Browser

```bash
# Install Chromium browser
uv run playwright install chromium

# Or install all browsers
uv run playwright install
```

### 3. Verify Installation

```bash
uv run python -c "from playwright.sync_api import sync_playwright; print('OK')"
```

## First Run Setup

### Step 1: Start the Watcher

```bash
cd ai_employee_scripts
python watchers/linkedin_watcher.py
```

### Step 2: Browser Opens for Login

```
2026-02-28 10:30:00 | LinkedInWatcher | INFO | Starting LinkedInWatcher (polling mode)
2026-02-28 10:30:00 | LinkedInWatcher | INFO | Session: /path/to/sessions/linkedin
2026-02-28 10:30:00 | LinkedInWatcher | INFO | Check interval: 300s
2026-02-28 10:30:00 | LinkedInWatcher | INFO |
2026-02-28 10:30:00 | LinkedInWatcher | INFO | ==================================================
2026-02-28 10:30:00 | LinkedInWatcher | INFO | FIRST RUN DETECTED!
2026-02-28 10:30:00 | LinkedInWatcher | INFO | Browser will open for LinkedIn authentication.
2026-02-28 10:30:00 | LinkedInWatcher | INFO | Please log in - session will be saved for future runs.
2026-02-28 10:30:00 | LinkedInWatcher | INFO | ==================================================
```

### Step 3: Log In to LinkedIn

1. Browser window opens automatically
2. Log in with your LinkedIn credentials
3. Complete any 2FA if enabled
4. Wait for redirect to messaging page
5. Watcher detects successful login

### Step 4: Session Saved

```
2026-02-28 10:31:30 | LinkedInWatcher | INFO | ✅ Detected logged in state!
```

Session is now saved for future headless runs.

## Message Detection

### LinkedIn URL

```
https://www.linkedin.com/messaging/?filter=unread
```

### Unread Detection

Messages are detected by CSS selectors:

```python
# Primary indicator
unread_indicator = convo.query_selector('.msg-conversation-card__convo-item-container--unread')

# Fallback indicator
if not unread_indicator:
    unread_indicator = convo.query_selector('.msg-conversation-card__message-snippet--unread')
```

### Message ID Generation

Since LinkedIn doesn't expose stable message IDs, we use a hash:

```python
msg_id = str(hash(f"{sender_name}:{preview}"))
```

## Inbox File Format

```yaml
---
type: linkedin_message
source: LinkedInWatcher
created: 2026-02-28T10:30:45
message_id: 1234567890
---

# LinkedIn Message from John Doe

## Sender
John Doe

## Message Preview
Hi, I saw your profile and wanted to connect...

## Detected
2026-02-28 10:30:45

## Full Message Content
 **Note:** This is a preview. View the full message on LinkedIn.

 Sender: John Doe
 Preview: Hi, I saw your profile and wanted to connect...

---
*Message ID: 1234567890*
```

## Task File Format

```yaml
---
type: linkedin_message
source: LinkedInWatcher
created: 2026-02-28T10:30:45
status: pending
priority: medium
---

# LinkedIn Message: John Doe

## Sender
John Doe

## Preview
Hi, I saw your profile and wanted to connect...

## Full Message
Read full message in [LINKEDIN_MSG_...|Inbox/LINKEDIN_MSG_...]

## Actions
- [ ] Read full message in [LINKEDIN_MSG_...|Inbox/LINKEDIN_MSG_...]
- [ ] Determine response needed
- [ ] Respond or archive

---
*Item ID: 1234567890*
```

## Running the Watcher

### Direct Execution

```bash
cd ai_employee_scripts
python watchers/linkedin_watcher.py
```

### With Custom Vault Path

```bash
python watchers/linkedin_watcher.py /path/to/AI_Employee_Vault
```

### Using UV

```bash
cd ai_employee_scripts
uv run python watchers/linkedin_watcher.py
```

## Startup Output

### First Run

```
2026-02-28 10:30:00 | LinkedInWatcher | INFO | Starting LinkedInWatcher (polling mode)
2026-02-28 10:30:00 | LinkedInWatcher | INFO | Session: /path/to/sessions/linkedin
2026-02-28 10:30:00 | LinkedInWatcher | INFO | Check interval: 300s
2026-02-28 10:30:00 | LinkedInWatcher | INFO |
2026-02-28 10:30:00 | LinkedInWatcher | INFO | ==================================================
2026-02-28 10:30:00 | LinkedInWatcher | INFO | Monitoring LinkedIn for:
2026-02-28 10:30:00 | LinkedInWatcher | INFO |   - New unread messages
2026-02-28 10:30:00 | LinkedInWatcher | INFO | ==================================================
2026-02-28 10:30:00 | LinkedInWatcher | INFO |
2026-02-28 10:30:00 | LinkedInWatcher | INFO | ==================================================
2026-02-28 10:30:00 | LinkedInWatcher | INFO | FIRST RUN DETECTED!
2026-02-28 10:30:00 | LinkedInWatcher | INFO | Browser will open for LinkedIn authentication.
2026-02-28 10:30:00 | LinkedInWatcher | INFO | Please log in - session will be saved for future runs.
2026-02-28 10:30:00 | LinkedInWatcher | INFO | ==================================================
```

### Subsequent Runs

```
2026-02-28 10:35:00 | LinkedInWatcher | INFO | Starting LinkedInWatcher (polling mode)
2026-02-28 10:35:00 | LinkedInWatcher | INFO | Session: /path/to/sessions/linkedin
2026-02-28 10:35:00 | LinkedInWatcher | INFO | Check interval: 300s
2026-02-28 10:35:00 | LinkedInWatcher | INFO |
2026-02-28 10:35:00 | LinkedInWatcher | INFO | ==================================================
2026-02-28 10:35:00 | LinkedInWatcher | INFO | Monitoring LinkedIn for:
2026-02-28 10:35:00 | LinkedInWatcher | INFO |   - New unread messages
2026-02-28 10:35:00 | LinkedInWatcher | INFO | ==================================================
```

## Message Processing Example

```
2026-02-28 10:35:05 | LinkedInWatcher | INFO | Starting LinkedIn check...
2026-02-28 10:35:05 | LinkedInWatcher | INFO | Creating browser context (headless=True)...
2026-02-28 10:35:06 | LinkedInWatcher | INFO | Browser context created successfully
2026-02-28 10:35:06 | LinkedInWatcher | INFO | Creating new page...
2026-02-28 10:35:06 | LinkedInWatcher | INFO | Navigating to LinkedIn messaging...
2026-02-28 10:35:09 | LinkedInWatcher | INFO | Page loaded successfully
2026-02-28 10:35:11 | LinkedInWatcher | INFO | Conversation list loaded
2026-02-28 10:35:11 | LinkedInWatcher | INFO | Checking for unread messages...
2026-02-28 10:35:12 | LinkedInWatcher | INFO |   New unread from Jane Smith: Hi, I'd like to discuss...
2026-02-28 10:35:12 | LinkedInWatcher | INFO | Found 1 unread messages
2026-02-28 10:35:13 | LinkedInWatcher | INFO | Saved full message to Inbox: LINKEDIN_MSG_Jane_Smith_...
2026-02-28 10:35:13 | LinkedInWatcher | INFO | Created LinkedIn task: LINKEDIN_MSG_...
2026-02-28 10:35:15 | LinkedInWatcher | INFO | Closing browser...
```

## Error Handling

### Login Timeout

If first run doesn't complete login within 2 minutes:

```
2026-02-28 10:32:00 | LinkedInWatcher | WARNING | Login timeout - will try again on next run
```

Solution:
1. Close watcher
2. Delete `sessions/linkedin/` folder
3. Restart watcher

### Session Expired

If LinkedIn session expires:

```
2026-02-28 10:35:10 | LinkedInWatcher | INFO | Current URL: https://www.linkedin.com/login
```

Solution:
1. Delete `sessions/linkedin/` folder
2. Restart watcher (will open browser for login)

### Playwright Timeout

```
2026-02-28 10:35:00 | LinkedInWatcher | ERROR | Playwright timeout occurred
```

Causes:
- Slow network
- LinkedIn rate limiting
- LinkedIn login page changed

Solution:
- Check internet connection
- Wait and retry (circuit breaker will pause)

## Troubleshooting

### Browser Not Installing

```bash
# Manually install Chromium
uv run playwright install chromium

# Verify installation
uv run playwright install --dry-run chromium
```

### Session Not Persisting

```bash
# Check session folder exists
ls -la sessions/linkedin/

# If corrupt, delete and re-authenticate
rm -rf sessions/linkedin/
python watchers/linkedin_watcher.py
```

### CSS Selectors Not Working

LinkedIn may update their CSS classes. Check debug artifacts:

```bash
# View screenshot
open AI_Employee_Vault/Logs/linkedin_debug.png

# View HTML
cat AI_Employee_Vault/Logs/linkedin_debug.html | grep "msg-conversation"
```

## Configuration

### Environment Variables

Not required. Session is stored in `sessions/linkedin/`.

### Dependencies

```toml
[tool.poetry.dependencies]
python = "^3.13"
playwright = "^1.40"
```

Install:
```bash
cd ai_employee_scripts
uv sync
uv run playwright install chromium
```

## Files Created

| File/Dir | Location | Purpose |
|----------|----------|---------|
| `sessions/linkedin/` | `ai_employee_scripts/` | Persistent browser session |
| `linkedin_state.json` | `AI_Employee_Vault/Logs/` | Seen messages/requests |
| `linkedin_debug.png` | `AI_Employee_Vault/Logs/` | Screenshot for debugging |
| `linkedin_debug.html` | `AI_Employee_Vault/Logs/` | HTML dump for debugging |

## Comparison with Other Watchers

| Feature | LinkedInWatcher | GmailWatcher | FileSystemWatcher |
|---------|-----------------|--------------|-------------------|
| **Setup Difficulty** | Hard (browser) | Medium (OAuth) | Easy (no API) |
| **Data Source** | LinkedIn Web | Gmail API | Local files |
| **Authentication** | Browser session | OAuth 2.0 | None |
| **Polling Interval** | 300 seconds | 120 seconds | 2 seconds |
| **First Run** | Manual login | OAuth flow | No setup |
| **State Persistence** | JSON state file | processed_ids.txt | In-memory |

## CSS Selectors Used

| Element | Selector |
|---------|----------|
| **Conversation List** | `.msg-conversation-listitem` |
| **Unread Indicator** | `.msg-conversation-card__convo-item-container--unread` |
| **Unread Snippet** | `.msg-conversation-card__message-snippet--unread` |
| **Sender Name** | `.msg-conversation-listitem__participant-names` |
| **Message Preview** | `.msg-conversation-card__message-snippet` |
| **Close Button** | `.msg-thread__close-icon` or `.artdeco-button[data-test-conversation-close-icon="true"]` |

**Note:** LinkedIn may update CSS class names. If detection stops working, inspect the LinkedIn messaging page and update selectors.

## Related Files

- `watchers/base_watcher.py` - Abstract base class
- `watchers/gmail_watcher.py` - Gmail monitoring
- `watchers/filesystem_watcher.py` - File monitoring
- `mcp_servers/linkedin_mcp.py` - LinkedIn MCP server for posting/replying
