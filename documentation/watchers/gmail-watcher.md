# GmailWatcher Documentation

## Overview

The GmailWatcher monitors a Gmail account for new emails and automatically creates action items in the AI Employee vault. It uses the Gmail API with OAuth 2.0 authentication.

## Architecture

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   Gmail API     │      │   Watcher       │      │    Vault        │
│   (new emails)  │─────▶│   polls every   │─────▶│   stores        │
│                 │      │   2 minutes     │      │   email + task  │
└─────────────────┘      └─────────────────┘      └─────────────────┘
        │
        ▼
   OAuth 2.0
  Authentication
```

### Workflow

```
1. Authenticate with Gmail (OAuth 2.0)
   │
2. Poll every 2 minutes for new emails
   │
3. Filter new emails (not in processed_ids)
   │
4. For each new email:
   ├── Save full email to Inbox
   └── Create task in Needs_Action
   │
5. Claude processes task → Reads email, drafts response
```

## Key Features

### OAuth 2.0 Authentication

```
First Run:
├── 1. Open authorization URL in browser
├── 2. User grants Gmail permissions
├── 3. Receive access token
├── 4. Save token_gmail.json
└── 5. Use saved token for subsequent runs

Subsequent Runs:
├── 1. Load token_gmail.json
├── 2. Check if token is valid
├── 3. If expired, refresh automatically
└── 4. Authenticate without user interaction
```

### Dual File Creation

For each new email, TWO files are created:

| File | Location | Purpose |
|------|----------|---------|
| **Inbox Copy** | `Inbox/EMAIL_SUBJECT_TIMESTAMP.md` | Full email content |
| **Task File** | `Needs_Action/TASK_EMAIL_SUBJECT_TIMESTAMP.md` | Action items |

### Email Priority Detection

Priority is determined automatically:

| Priority | Trigger |
|----------|---------|
| **high** | Subject contains: urgent, asap, emergency, important, deadline |
| **medium** | Subject contains: invoice, payment, meeting, proposal |
| **low** | Everything else |

### State Persistence

Processed email IDs are tracked to avoid duplicates:

```
AI_Employee_Vault/Logs/gmail_processed_ids.txt
```

## Constructor

```python
GmailWatcher(
    vault_path: str,                  # Path to AI_Employee_Vault
    credentials_path: str = None,      # Path to credentials.json
    check_interval: int = 120          # Seconds between checks (default: 2 min)
)
```

### Credentials Path

If not specified, searches these locations in order:
1. `ai_employee_scripts/credentials.json`
2. `../credentials.json` (parent of ai_employee_scripts)
3. `../ai_employee_scripts/credentials.json` (parent/ai_employee_scripts)

## Gmail API Setup

### 1. Create Google Cloud Project

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project
3. Enable Gmail API:
   - Navigate to "APIs & Services" → "Library"
   - Search for "Gmail API"
   - Click "Enable"

### 2. Create OAuth Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Application type: **Desktop app**
4. Name: `Gmail Watcher`
5. Click "Create"

### 3. Download Credentials

1. Download the JSON file
2. Rename to `credentials.json`
3. Place in `ai_employee_scripts/`

### Scopes Required

```
https://www.googleapis.com/auth/gmail.readonly
```

## Authentication Flow

### First Run

```
2026-02-28 10:30:00 | GmailWatcher | INFO | Starting Gmail Watcher (polling mode)
2026-02-28 10:30:00 | GmailWatcher | INFO | No valid credentials found, starting OAuth flow...
2026-02-28 10:30:00 | GmailWatcher | INFO | Waiting for authorization on http://localhost:8080
2026-02-28 10:30:00 | GmailWatcher | INFO | Open this URL in your browser (WSL users: use Windows browser):
2026-02-28 10:30:00 | GmailWatcher | INFO | ============================================================
2026-02-28 10:30:00 | GmailWatcher | INFO | Open this URL in your Windows browser:
2026-02-28 10:30:00 | GmailWatcher | INFO | ============================================================
2026-02-28 10:30:00 | GmailWatcher | INFO | https://accounts.google.com/o/oauth2/...
2026-02-28 10:30:00 | GmailWatcher | INFO | ============================================================
```

1. Copy the authorization URL
2. Open in your browser (WSL users: use Windows browser)
3. Grant Gmail permissions
4. Token automatically saved to `token_gmail.json`

### Subsequent Runs

```
2026-02-28 10:35:00 | GmailWatcher | INFO | Starting Gmail Watcher (polling mode)
2026-02-28 10:35:00 | GmailWatcher | INFO | Using existing valid credentials
2026-02-28 10:35:00 | GmailWatcher | INFO | Gmail authentication complete
```

## Email Query

The watcher uses this Gmail search query:

```
newer_than:1d -in:sent
```

| Term | Meaning |
|------|---------|
| `newer_than:1d` | Emails from the last day |
| `-in:sent` | Exclude sent emails |
| `maxResults=20` | Limit to 20 emails per check |

## Inbox File Format

```yaml
---
type: email
source: GmailWatcher
created: 2026-02-28T10:30:45
message_id: 123abc456def
---

# Subject: Project Proposal

## From
John Doe <john.doe@example.com>

## To
me@example.com

## Cc
manager@example.com

## Date
Fri, 28 Feb 2026 10:30:00 -0800

## Body
Hi,

I wanted to discuss the project proposal...

---
*Email ID: 123abc456def*
```

## Task File Format

```yaml
---
type: email
source: GmailWatcher
created: 2026-02-28T10:30:45
status: pending
priority: medium
message_id: 123abc456def
original_file: EMAIL_Project_Proposal_20260228_103045.md
---

# Email: Project Proposal

## From
John Doe <john.doe@example.com>

## Date
Fri, 28 Feb 2026 10:30:00 -0800

## Subject
Project Proposal

## Preview
Hi, I wanted to discuss the project proposal...

## Actions
- [ ] Read full email in [EMAIL_...|Inbox/EMAIL_...]
- [ ] Determine if action needed
- [ ] Draft reply or take action
- [ ] Move to Done when handled

---
*Email ID: 123abc456def*
```

## Running the Watcher

### Direct Execution

```bash
cd ai_employee_scripts
python watchers/gmail_watcher.py
```

### With Custom Vault Path

```bash
python watchers/gmail_watcher.py /path/to/AI_Employee_Vault
```

### Using UV

```bash
cd ai_employee_scripts
uv run python watchers/gmail_watcher.py
```

## Startup Output

```
2026-02-28 10:30:00 | GmailWatcher | INFO | Starting Gmail Watcher (polling mode)
2026-02-28 10:30:00 | GmailWatcher | INFO | Credentials: /path/to/credentials.json
2026-02-28 10:30:00 | GmailWatcher | INFO | Check interval: 120s
2026-02-28 10:30:00 | GmailWatcher | INFO | Press Ctrl+C to stop
2026-02-28 10:30:01 | GmailWatcher | INFO | Using existing valid credentials
2026-02-28 10:30:01 | GmailWatcher | INFO | Gmail authentication complete
```

## Email Processing Example

When a new email arrives:

```
2026-02-28 10:32:00 | GmailWatcher | INFO | Starting check for updates...
2026-02-28 10:32:01 | GmailWatcher | INFO | Saved email to Inbox: EMAIL_Urgent_Request_20260228_103201.md
2026-02-28 10:32:01 | GmailWatcher | INFO | Created email task: TASK_EMAIL_Urgent_Request_20260228_103201.md
```

## Error Handling

### Retry Logic

Email fetching uses exponential backoff retry:

```python
@with_retry(max_attempts=3, base_delay=2, backoff_factor=2)
def check_for_updates(self) -> list:
    # Gmail API call
```

| Attempt | Delay |
|---------|-------|
| 1 | Immediate |
| 2 | 2 seconds |
| 3 | 4 seconds |

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `credentials.json not found` | Missing credentials file | Download from Google Cloud Console |
| `Invalid credentials` | Bad credentials.json | Verify Desktop app type |
| `Token refresh failed` | Token expired, can't refresh | Delete token_gmail.json and re-auth |
| `HttpError 403` | Insufficient permissions | Check Gmail API is enabled |
| `HttpError 429` | Rate limit exceeded | Watcher will retry automatically |

## Troubleshooting

### Credentials Not Found

```bash
# Check file exists
ls -la ai_employee_scripts/credentials.json

# Verify location
pwd  # Should be in ai_employee_scripts parent directory
```

### OAuth Flow Fails

1. **Port 8080 in use:**
   ```bash
   # Check if port is available
   netstat -an | grep 8080
   ```

2. **Browser not opening:**
   - WSL users: Manually copy URL to Windows browser
   - Check firewall settings

3. **Permissions denied:**
   - Verify OAuth consent screen is configured
   - Check API is enabled in Google Cloud Console

### Token Expired

```bash
# Delete old token
rm ai_employee_scripts/token_gmail.json

# Re-run watcher to authenticate
python watchers/gmail_watcher.py
```

## Configuration

### Environment Variables

Not required. Credentials are stored in `credentials.json` and `token_gmail.json`.

### Dependencies

```toml
[tool.poetry.dependencies]
python = "^3.13"
google-api-python-client = "^2.0"
google-auth-oauthlib = "^1.0"
google-auth-httplib2 = "^0.2"
```

Install:
```bash
cd ai_employee_scripts
uv sync
```

## Files Created

| File | Location | Purpose |
|------|----------|---------|
| `credentials.json` | `ai_employee_scripts/` | OAuth client secrets (user provides) |
| `token_gmail.json` | `ai_employee_scripts/` | OAuth access token (auto-generated) |
| `gmail_processed_ids.txt` | `AI_Employee_Vault/Logs/` | Processed email IDs |

## Comparison with Other Watchers

| Feature | GmailWatcher | FileSystemWatcher | LinkedInWatcher |
|---------|--------------|-------------------|-----------------|
| **Setup Difficulty** | Medium (OAuth) | Easy (no API) | Hard (browser) |
| **Data Source** | Gmail API | Local files | LinkedIn Web |
| **Authentication** | OAuth 2.0 | None | Browser session |
| **Polling Interval** | 120 seconds | 2 seconds | 300 seconds |
| **State Persistence** | processed_ids.txt | In-memory (seen_files) | JSON state file |

## Related Files

- `watchers/base_watcher.py` - Abstract base class
- `watchers/filesystem_watcher.py` - File monitoring
- `watchers/linkedin_watcher.py` - LinkedIn monitoring
- `mcp_servers/gmail_mcp.py` - Gmail MCP server for sending emails
