# Personal AI Employee

**A fully autonomous AI employee that monitors your digital life and handles business operations automatically.**

Built for the **Personal AI Employee Hackathon 0** - Gold Tier Complete (12/12 requirements - 100%)

---

## Hackathon Progress

### Tier Completion Status

```
███████████████████████████████████████████  BRONZE  ███████████████████████████████████████████
███████████████████████████████████████████  SILVER  ███████████████████████████████████████████
███████████████████████████████████████████   GOLD   ███████████████████████████████████████████
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ PLATINUM ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
```

| Tier | Status | Requirements | Completion Date |
|------|--------|--------------|-----------------|
| **Bronze** | ✅ Complete | 4/4 | February 15, 2026 |
| **Silver** | ✅ Complete | 4/4 | February 21, 2026 |
| **Gold** | ✅ Complete | 12/12 | February 26, 2026 |
| **Platinum** | ❌ Not Started | TBD | - |

### Overall Progress: **upto Gold tier Complete** (3 of 4 Tiers)

#### Bronze Tier ✅
- FileSystemWatcher with drop folder monitoring
- Task processing pipeline (Inbox → Needs_Action → Plans → Done)
- 4 core agent skills
- Obsidian vault with Company Handbook
- Human approval workflow

#### Silver Tier ✅
- GmailWatcher for email monitoring
- MCP servers for Gmail and LinkedIn
- LinkedIn posting automation
- Email categorization and processing
- Integration with Claude Code

#### Gold Tier ✅
- Full cross-domain integration (Personal + Business)
- **6 MCP Servers** (Gmail, LinkedIn API, LinkedIn Playwright, Meta, Twitter, Odoo)
- Odoo Accounting (self-hosted Docker, local MCP)
- Facebook/Instagram posting via Meta Graph API
- Twitter/X posting
- Weekly CEO Briefing with automatic email delivery
- 3-layer error recovery (watchdog, retry, circuit breaker, DLQ)
- Comprehensive audit logging
- Ralph Wiggum stop hook
- **12 Agent Skills** for complete automation

#### Platinum Tier (Future)
- 24/7 cloud hosting with fallback to local
- Agent-to-Agent (A2A) communication
- Work-zone specialization
- Multi-cloud deployment

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Components](#components)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Overview

The Personal AI Employee is a 24/7 autonomous system that perceives, reasons about, and acts on your personal and business tasks. It combines:

- **Perception:** Watchers monitor Gmail, LinkedIn, Facebook/Instagram, Twitter/X, and local files
- **Reasoning:** Claude Code (Claude 4.6) processes tasks and creates execution plans
- **Action:** MCP servers execute actions (post content, send emails, create invoices, etc.)
- **Memory:** Obsidian vault stores all data, tasks, plans, and logs
- **Safety:** Human-in-the-loop approval for sensitive actions

### What It Does

| Category | Capability |
|----------|------------|
| **Email** | Monitors Gmail, categorizes messages, drafts replies |
| **Social Media** | Generates and posts content to LinkedIn, Facebook, Instagram, Twitter/X |
| **Accounting** | Creates invoices in Odoo, tracks revenue and expenses |
| **Files** | Monitors drop folder for new files and tasks |
| **Reporting** | Generates weekly CEO briefings with financial and activity summaries |

---

### Error Recovery (3-Layer Architecture)

1. **External Watchdog** - Monitors and restarts orchestrator if it crashes
2. **Internal Watchdog** - Orchestrator restarts crashed watchers
3. **Operation-Level** - Retry with exponential backoff, circuit breaker, dead letter queue

---

## Architecture

### System Workflow

```
                    ╔═════════════════════════════════════════════╗
                    ║            ENTRY POINTS                    ║
                    ╠═════════════════════════════════════════════╣
                    ║  1. Cron Jobs (Scheduled Automation)       ║
                    ║  2. Claude Code Skills (Interactive)       ║
                    ║  3. Watchdog.py (Production Monitoring)    ║
                    ╚═════════════════════════════════════════════╝
                                     │
                    ┌────────────────┴────────────────┐
                    ▼                                 ▼
        ╔═══════════════════════╗         ╔═══════════════════════╗
        ║    Cron Triggers      ║         ║     Watchdog.py       ║
        ║  (linkedin/meta/      ║         ║  Monitors & Restarts  ║
        ║   twitter/weekly)     ║         ║   Orchestrator.py     ║
        ╚════════════╤═══════════╝         ╚════════════╤═════════╝
                     │                                 │
                     │    ┌────────────────────────────┘
                     │    │
                     ▼    ▼
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator.py                           │
│              (Master Controller - 24/7 Process)              │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Needs_Action │◄─┤  Watchers    │  │   Approved   │      │
│  │   Folder     │  │  (Perception)│  │   Folder     │      │
│  └───────┬──────┘  └──────────────┘  └───────┬──────┘      │
│          │                                  │              │
└──────────┼──────────────────────────────────┼──────────────┘
           │                                  │
           │     ┌────────────┐               │
           └────►│ Claude Code│◄──────────────┘
                 │ (Reasoning)│
                 └─────┬──────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│ Pending_     │ │  Plans   │ │   Rejected   │
│  Approval    │ │          │ │              │
└──────┬───────┘ └──────────┘ └──────────────┘
       │
   ┌───┴───┐
   ▼       ▼
┌──────┐ ┌──────┐
│Human │ │Auto- │
│Review│ │skip │
└───┬──┘ └──┬───┘
    │       │
    ▼       │
┌─────────┐ │
│ Approved│◄┘
└────┬────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│                    MCP Servers (Action)                     │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │  Gmail  │ │LinkedIn │ │  Meta   │ │ Twitter │           │
│  │   MCP   │ │   MCP   │ │   MCP   │ │   MCP   │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
│  ┌─────────┐                                               │
│  │  Odoo   │                                               │
│  │   MCP   │                                               │
│  └────┬────┘                                               │
└───────┼────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────┐
│     Done     │
│   Folder     │
└──────────────┘

═══════════════════════════════════════════════════════════════
                    SCHEDULED AUTOMATION (CRON)
═══════════════════════════════════════════════════════════════
  2 AM → LinkedIn Post    3 AM → Meta (FB/IG)    4 AM → Twitter
                          │
                          ▼
                 Sunday 5 AM → CEO Briefing → Email to You
```

### Data Flow

```
1. PERCEPTION (Watchers)
   ├─ FileSystemWatcher → Monitors drop_folder/ for new files
   ├─ GmailWatcher      → Polls Gmail every 2 min for new emails
   └─ LinkedInWatcher   → Polls LinkedIn every 5 min for messages
          │
          ▼
2. TRIGGER (Orchestrator detects new files in Needs_Action/)
          │
          ▼
3. REASONING (Claude Code via /process-tasks skill)
   ├─ Reads task file
   ├─ Analyzes content
   ├─ Creates execution plan (if needed)
   └─ Generates approval request
          │
          ▼
4. APPROVAL (Human-in-the-loop)
   ├─ Pending_Approval/ → Human reviews
   ├─ Approved/ → Ready to execute
   └─ Rejected/ → Cancelled
          │
          ▼
5. ACTION (MCP Servers via /execute-approved skill)
   ├─ Post to social media
   ├─ Send emails
   ├─ Create invoices
   └─ Log results
          │
          ▼
6. COMPLETION (Done/)
   └─ Summary with results and logs
```

### Error Recovery Layers

```
┌─────────────────────────────────────────────────────────────┐
│ LAYER 1: External Watchdog (watchdog.py)                    │
│ ─────────────────────────────────────────────────────────── │
│ Monitors orchestrator.py process                            │
│ If orchestrator dies → Restart automatically                │
│ Check interval: 60 seconds                                  │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ LAYER 2: Internal Watchdog (orchestrator.py)                │
│ ─────────────────────────────────────────────────────────── │
│ Orchestrator monitors all watcher processes                 │
│ If watcher dies → Restart with full configuration           │
│ Log: watcher_restarts.jsonl                                 │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ LAYER 3: Operation-Level Recovery (error_recovery.py)       │
│ ─────────────────────────────────────────────────────────── │
│ • Retry Decorator      → 3 attempts, exponential backoff    │
│ • Circuit Breaker      → Opens after 5 failures (60s cooldown)│
│ • Dead Letter Queue    → Failed items to Failed/ folder     │
│ • Health Monitor       → Track component status             │
└─────────────────────────────────────────────────────────────┘
```

---

## Features

### Bronze Tier (Complete)
- ✅ FileSystemWatcher for drop folder monitoring
- ✅ Task processing pipeline (Needs_Action → Plans → Done)
- ✅ 4 core agent skills (start/stop watcher, process tasks, create plan, complete task)
- ✅ Obsidian vault for memory and dashboard
- ✅ Company handbook with approval rules

### Silver Tier (Complete)
- ✅ GmailWatcher for email monitoring
- ✅ MCP servers for Gmail and LinkedIn
- ✅ LinkedIn posting skill
- ✅ Email processing and categorization
- ✅ Human approval workflow

### Gold Tier (Complete)
- ✅ Full cross-domain integration (Personal + Business)
- ✅ Odoo Accounting (self-hosted, local, MCP)
- ✅ Facebook/Instagram posting via Meta Graph API
- ✅ Twitter/X posting
- ✅ 6 MCP servers (Gmail, LinkedIn API, LinkedIn Playwright, Meta, Twitter, Odoo)
- ✅ Weekly CEO Briefing with automatic email delivery
- ✅ 3-layer error recovery (watchdog, retry, circuit breaker, DLQ)
- ✅ Comprehensive audit logging
- ✅ Ralph Wiggum stop hook (blocks exit until tasks complete)
- ✅ All AI as Agent Skills (12 skills total)

---

## Quick Start

### Prerequisites

- **Python 3.13+** (managed via UV)
- **Docker & Docker Compose** (for Odoo)
- **Claude Code CLI** (with Opus 4.6)
- **LinkedIn Developer Account** (for OAuth)
- **Meta Developer Account** (for Facebook/Instagram)
- **Twitter/X Developer Account** (for posting)
- **Gmail Account** (with OAuth)

### 1. Clone and Install

```bash
cd "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts"

# Install dependencies via UV
uv sync

# Install Playwright browsers
uv run playwright install chromium
```

### 2. Configure Environment

```bash
# Copy the example env file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Required credentials:
```bash
# LinkedIn (OAuth)
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
LINKEDIN_ACCESS_TOKEN=your_access_token

# Twitter/X API
X_API_KEY=your_api_key
X_API_SECRET=your_api_secret
X_ACCESS_TOKEN=your_access_token
X_ACCESS_TOKEN_SECRET=your_access_token_secret

# Meta (Facebook/Instagram)
META_ACCESS_TOKEN=your_access_token
META_PAGE_ID=your_page_id

# Odoo Accounting
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USER=your_email
ODOO_PASSWORD=your_password

# Gmail (OAuth) - credentials.json and token_gmail.json
```

### 3. Start Odoo (Accounting)

```bash
cd "/mnt/d/coding Q4/hackathon-0/save-1"
docker-compose up -d

# Access Odoo at http://localhost:8069
# Initial setup: Create database, install Invoicing app
```

### 4. Start the AI Employee

```bash
cd "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts"

# Option 1: Start orchestrator directly
uv run python orchestrator.py ../AI_Employee_Vault

# Option 2: Start with watchdog (recommended for 24/7)
uv run python watchdog.py
```

### 5. Setup Cron Jobs (Automated Posting)

```bash
crontab -e
```

Add these entries:
```bash
# LinkedIn post daily at 2 AM
0 2 * * * cd "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts" && uv run python scripts/linkedin_cron_trigger.py >> ../AI_Employee_Vault/Logs/cron.log 2>&1

# Facebook/Instagram post daily at 3 AM
0 3 * * * cd "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts" && uv run python scripts/meta_cron_trigger.py >> ../AI_Employee_Vault/Logs/meta_cron.log 2>&1

# Twitter post daily at 4 AM
0 4 * * * cd "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts" && uv run python scripts/twitter_cron_trigger.py >> ../AI_Employee_Vault/Logs/twitter_cron.log 2>&1

# Weekly CEO Briefing on Sunday at 5 AM
0 5 * * 0 cd "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts" && uv run python scripts/weekly_cron_trigger.py >> ../AI_Employee_Vault/Logs/weekly_cron.log 2>&1
```

---

## Installation

### Step-by-Step Setup

#### 1. LinkedIn OAuth Setup

```bash
# Run the OAuth callback server
python get_token.py

# 1. Open the displayed URL in your browser
# 2. Authorize the application
# 3. Copy the displayed access token
# 4. Add to .env as LINKEDIN_ACCESS_TOKEN
```

#### 2. Gmail OAuth Setup

Gmail OAuth credentials are stored in:
- `credentials.json` - OAuth client credentials
- `token_gmail.json` - Refresh token (auto-generated on first run)

Get credentials from: https://console.cloud.google.com/

#### 3. Meta (Facebook/Instagram) Setup

1. Create a Meta Developer Account
2. Create a Facebook Page
3. Link Instagram Business Account to Page
4. Generate Page Access Token with `pages_read_engagement`, `pages_manage_posts`
5. Add `META_ACCESS_TOKEN` and `META_PAGE_ID` to .env

#### 4. Twitter/X Setup

1. Create Twitter/X Developer Account
2. Create a Project and App
3. Generate API Key, API Secret, Access Token, Access Token Secret
4. Add to .env

**Note:** Twitter/X posting requires API credits for live posting (402 Payment Required if at limits).

#### 5. Odoo Setup

```bash
# Start containers
docker-compose up -d

# Access at http://localhost:8069
# Create database: "odoo"
# Install "Invoicing" app
# Create user matching .env credentials
```

---

## Configuration

### MCP Server Configuration

Located in `.claude/settings.local.json`:

```json
{
  "enableAllProjectMcpServers": true,
  "enabledMcpjsonServers": [
    "ai-gmail",
    "linkedin-mcp",
    "linkedin-api",
    "odoo",
    "twitter-api",
    "meta"
  ]
}
```

### Vault Structure

```
AI_Employee_Vault/
├── Inbox/              # Dropped files stored here
├── Needs_Action/       # Tasks awaiting processing
├── Plans/              # Execution plans
├── Pending_Approval/   # Awaiting human review
├── Approved/           # Human-approved actions
├── Rejected/           # Human-rejected actions
├── Done/               # Completed tasks/summaries
├── Failed/             # Failed items (dead letter queue)
├── Logs/               # System logs
├── Accounting/         # Financial records
├── Briefings/          # CEO briefings
├── Content_To_Post/    # Queued social media content
│   ├── queued/
│   ├── posted/
│   └── rejected/
├── Company_Handbook.md # Rules and approval thresholds
├── Dashboard.md        # System status overview
└── Business_Goals.md   # Business objectives
```

---

## Usage

### Agent Skills

Use these slash commands in Claude Code:

| Command | Description |
|---------|-------------|
| `/start-watcher` | Start FileSystemWatcher monitoring drop_folder |
| `/stop-watcher` | Stop the File System Watcher |
| `/process-tasks` | Process all pending tasks in Needs_Action |
| `/create-plan` | Create structured execution plan for a task |
| `/complete-task` | Mark task as completed and move to Done |
| `/execute-approved` | Execute approved LinkedIn/Meta/Twitter posts, Odoo invoices, emails |
| `/linkedin-posting` | Generate lead-generating LinkedIn post ideas |
| `/meta-posting` | Generate Facebook/Instagram posts for business |
| `/twitter-posting` | Generate engaging tweets for business growth |
| `/create-invoice` | Create draft invoice in Odoo accounting |
| `/check-accounting` | Query Odoo for invoices, payments, revenue, expenses |
| `/weekly-audit` | Generate CEO Briefing with Odoo financial data |

### Workflow Example

1. **Drop a file** in `drop_folder/` → FileSystemWatcher detects it
2. **Task created** in `Needs_Action/TASK_*.md`
3. **Run `/process-tasks`** → Claude Code analyzes and creates plan
4. **Review plan** in `Plans/PLAN_*.md`
5. **Approval request** created in `Pending_Approval/`
6. **Human approves** → Move to `Approved/`
7. **Run `/execute-approved`** → Actions executed via MCP servers
8. **Summary** created in `Done/`

### Cron Automation

Daily at 2 AM, 3 AM, 4 AM:
- Cron trigger generates social media post
- Creates approval file in `Pending_Approval/`
- Human reviews and approves
- `/execute-approved` posts to platform

Weekly Sunday at 5 AM:
- Generates CEO Briefing
- Emails briefing automatically
- Includes revenue, expenses, social media stats, email activity

---

## Components

### Watchers (3 Total)

| Watcher | Purpose | File |
|---------|---------|------|
| **FileSystemWatcher** | Monitors `drop_folder/` for new files | `watchers/filesystem_watcher.py` |
| **GmailWatcher** | Monitors Gmail for new emails (2min poll) | `watchers/gmail_watcher.py` |
| **LinkedInWatcher** | Monitors LinkedIn for unread messages (5min poll) | `watchers/linkedin_watcher.py` |

### MCP Servers (6 Total)

| MCP Server | Tools Provided | Purpose |
|------------|----------------|---------|
| **gmail_mcp.py** | send_email, read_email, search_emails, list_emails, draft_email | Gmail operations via OAuth |
| **linkedin_api_mcp.py** | post_to_linkedin, get_linkedin_profile | LinkedIn posting via REST API |
| **linkedin_mcp.py** | post_content, reply_message, get_messages, verify_connection | LinkedIn via Playwright |
| **meta_mcp.py** | post_to_facebook, post_to_instagram, post_to_both, get_meta_profile | Facebook/Instagram posting |
| **twitter_mcp.py** | post_tweet, post_business_update, get_twitter_profile | Twitter/X posting |
| **odoo_mcp.py** | get_invoices, get_payments, get_revenue, get_expenses, create_draft_invoice, post_invoice | Odoo Accounting |

### Error Recovery

| Component | Purpose | File |
|-----------|---------|------|
| **Watchdog** | External process monitor for orchestrator | `watchdog.py` |
| **Error Recovery** | Retry, circuit breaker, dead letter queue | `error_recovery.py` |
| **Base Watcher** | Abstract base with error recovery built-in | `watchers/base_watcher.py` |
| **Orchestrator** | Internal watchdog for watcher processes | `orchestrator.py` |

### Log Files

| File | Purpose |
|------|---------|
| `Logs/cron.log` | LinkedIn cron output |
| `Logs/meta_cron.log` | Facebook/Instagram cron output |
| `Logs/twitter_cron.log` | Twitter cron output |
| `Logs/weekly_cron.log` | CEO briefing cron output |
| `Logs/watchdog.log` | Watchdog events |
| `Logs/health_status.json` | Component health status |
| `Logs/circuit_breakers.json` | Circuit breaker states (dynamic) |
| `Logs/dead_letter_queue.jsonl` | Failed items (dynamic) |
| `Logs/watcher_restarts.jsonl` | Watcher restart events (dynamic) |
| `Logs/process_events.jsonl` | Process lifecycle events |

---

## Development

### Project Structure

```
/mnt/d/coding Q4/hackathon-0/save-1/
├── AI_Employee_Vault/         # Obsidian vault (data/memory)
├── ai_employee_scripts/       # Python code (never syncs - has secrets)
│   ├── watchers/              # Watcher scripts
│   ├── mcp_servers/           # MCP server implementations
│   ├── scripts/               # Cron trigger scripts
│   ├── orchestrator.py        # Master controller
│   ├── watchdog.py            # External watchdog
│   ├── error_recovery.py      # Error handling utilities
│   ├── main.py                # CLI entry point
│   ├── pyproject.toml         # UV dependencies
│   └── .env                   # API credentials
├── drop_folder/               # External input staging
├── .claude/                   # Claude Code configuration
│   ├── skills/                # Agent skill definitions
│   ├── hooks/                 # Hook scripts
│   └── settings.local.json    # MCP server config
├── docker-compose.yml         # Odoo + PostgreSQL
├── get_token.py               # LinkedIn OAuth helper
└── README.md                  # This file
```

### Adding a New Watcher

1. Inherit from `BaseWatcher` in `watchers/base_watcher.py`
2. Implement abstract methods:
   - `check_for_updates()` - Return list of new items
   - `create_action_file(item)` - Create .md in Needs_Action
   - `get_item_id(item)` - Return unique identifier
3. Use polling instead of inotify for WSL compatibility
4. Add to `orchestrator.py` watcher configs

### Python Dependencies

```toml
[dependencies]
mcp = ">=1.2.0"
httpx = ">=0.27.0"
google-api-python-client = ">=2.189.0"
google-auth = ">=2.48.0"
google-auth-oauthlib = ">=1.2.4"
playwright = ">=1.58.0"
watchdog = ">=6.0.0"
odoorpc = ">=0.10.1"
tweepy = ">=4.14.0"
```

---

## Troubleshooting

### Watchdog says "Orchestrator already running" but it's not

Kill stale processes:
```bash
ps aux | grep orchestrator
kill <pid>
# Or remove PID file manually
rm /tmp/ai_employee_orchestrator.pid
```

### Gmail authentication fails

Delete old token and re-authenticate:
```bash
rm ai_employee_scripts/token_gmail.json
# Re-run orchestrator - it will prompt for OAuth
```

### Odoo connection refused

Make sure Docker containers are running:
```bash
docker-compose ps
docker-compose up -d
```

### LinkedIn posting fails (401 Unauthorized)

Access token expired. Run OAuth again:
```bash
python get_token.py
# Copy new token to .env
```

### Twitter posting returns 402 Payment Required

Twitter API has rate limits or requires credits. Check your X API dashboard.

### Ralph Wiggum hook blocking exit

Either complete pending tasks or use emergency override:
```bash
touch AI_Employee_Vault/stop_ralph
```

### Circuit breaker is open

Wait 60 seconds for cooldown, or manually reset:
```bash
rm AI_Employee_Vault/Logs/circuit_breakers.json
```

---

## Statistics

| Metric | Count |
|--------|-------|
| **Tiers Completed** | 3 (Bronze, Silver, Gold) |
| **Watchers** | 3 |
| **MCP Servers** | 6 |
| **Agent Skills** | 12 |
| **Cron Jobs** | 4 (3 daily + 1 weekly) |
| **Error Recovery Components** | 4 |

---

## License

This project is part of the Personal AI Employee Hackathon 0.

---

**Built with:** Claude Code, Python, UV, Docker, Odoo, Obsidian

**Last Updated:** February 28, 2026

**Project Status:** Gold Tier Complete (12/12 requirements - 100%)
