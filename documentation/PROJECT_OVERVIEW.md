# Personal AI Employee - Complete Project Documentation

**Hackathon:** Personal AI Employee Hackathon 0
**Tier Progress:** Bronze ✅ | Silver ✅ | Gold ✅ | Platinum ⏸️
**Last Updated:** 2026-03-03

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Component Deep Dive](#component-deep-dive)
4. [Data Flow](#data-flow)
5. [File Structure Reference](#file-structure-reference)
6. [Setup & Installation](#setup--installation)
7. [Running the System](#running-the-system)
8. [Troubleshooting](#troubleshooting)

---

## Project Overview

### What is the Personal AI Employee?

The **Personal AI Employee** is a local-first automation system that uses Claude Code as its reasoning engine to manage digital tasks. It monitors external sources (email, files, social media), creates actionable tasks, and executes actions with human oversight.

### Core Philosophy: Perception → Reasoning → Action

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  PERCEPTION     │      │   REASONING     │      │    ACTION       │
│                 │      │                 │      │                 │
│  Watchers       │ ───▶ │  Claude Code    │ ───▶ │  MCP Servers    │
│  Monitor        │      │  Plans          │      │  Execute        │
│  Detect         │      │  Drafts         │      │  Posts/Sends    │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

### Key Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Local-First** | All data stored in Obsidian vault, no cloud dependencies |
| **Human-in-the-Loop** | All significant actions require approval |
| **Modular** | Watchers, MCPs, and Skills are independent components |
| **Resilient** | Error recovery, circuit breakers, watchdog monitoring |
| **Transparent** | Everything logged to vault for audit trail |

---

## System Architecture

### High-Level Component Map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PERSONAL AI EMPLOYEE SYSTEM                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         WATCHERS (Perception)                       │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │   FileSystem │  │     Gmail    │  │   LinkedIn   │              │   │
│  │  │   Watcher    │  │   Watcher    │  │   Watcher    │              │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │   │
│  └─────────┼──────────────────┼──────────────────┼──────────────────────┘   │
│            │                  │                  │                          │
│            ▼                  ▼                  ▼                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      AI_Employee_Vault (Memory)                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │  Inbox/      │  │Needs_Action/ │  │  Plans/      │              │   │
│  │  │  Store data  │  │  Task queue  │  │  Strategies  │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                     │
│                                      ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     CLAUDE CODE (Reasoning)                        │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │  Agent Skills│  │   /process   │  │  /execute    │              │   │
│  │  │  - Create    │  │   -tasks     │  │  -approved   │              │   │
│  │  │  - Complete  │  │   -plan      │  │              │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                     │
│                                      ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      MCP SERVERS (Action)                           │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐  │   │
│  │  │  Gmail   │ │LinkedIn  │ │ Twitter  │ │  Odoo    │ │  Meta   │  │   │
│  │  │   MCP    │ │   MCP    │ │   MCP    │ │   MCP    │ │   MCP   │  │   │
│  │  │  Send    │ │  Post    │ │  Tweet   │ │Invoice   │ │FB/IG    │  │   │
│  │  │  Email   │ │  Reply   │ │          │ │Revenue   │ │  Post   │  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └─────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATION & MONITORING LAYER                       │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐              │
│  │  Watchdog.py │ ──▶ │Orchestrator  │ ──▶ │   Watchers   │              │
│  │  24/7 Monitor │     │  Manager     │     │  (Managed)   │              │
│  └──────────────┘     └──────────────┘     └──────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Deep Dive

### 1. WATCHERS (Perception Layer)

**Location:** `ai_employee_scripts/watchers/`

Watchers monitor external data sources and create tasks when new items are detected. All watchers inherit from `BaseWatcher` which provides:

- **Retry Logic:** Exponential backoff (3 attempts, 2s → 4s → 8s)
- **Circuit Breaker:** Pauses after 5 consecutive failures (60s timeout)
- **Dead Letter Queue:** Failed items stored in `Failed/{watcher_name}/`
- **Health Monitoring:** Tracks health status (healthy/degraded/down)

| Watcher | File | Monitors | Polling | Creates |
|---------|------|----------|---------|---------|
| **FileSystemWatcher** | `filesystem_watcher.py` | `drop_folder/` | 2 sec | File processing tasks |
| **GmailWatcher** | `gmail_watcher.py` | Gmail API | 2 min | Email response tasks |
| **LinkedInWatcher** | `linkedin_watcher.py` | LinkedIn Web | 5 min | Message reply tasks |

**Watcher Output Format:**
```yaml
---
type: task
source: GmailWatcher
created: 2026-03-03T10:30:45
status: pending
priority: medium
original_file: EMAIL_subject_20260303_103045.md
---
# Task: Process New Email
...instructions for Claude...
```

---

### 2. ORCHESTRATOR (Management Layer)

**Location:** `ai_employee_scripts/orchestrator.py`

The orchestrator is the **24/7 master controller** that:

| Function | Description |
|----------|-------------|
| **Start Watchers** | Launches all enabled watchers as subprocesses |
| **Monitor Needs_Action** | Detects new tasks every 30 seconds |
| **Trigger Claude** | Calls `/process-tasks` skill when tasks arrive |
| **Monitor Approved** | Calls `/execute-approved` when items approved |
| **Watchdog Watchers** | Restarts crashed watchers automatically |
| **Graceful Shutdown** | Handles SIGINT/SIGTERM for clean exit |

**Orchestrator Architecture:**
```
┌─────────────────────────────────────────────────────────────────┐
│                    orchestrator.py                              │
├─────────────────────────────────────────────────────────────────┤
│  Main Thread                                                    │
│  ├── start_watchers()      → Launch watcher subprocesses        │
│  ├── monitor_needs_action() → Thread: Detect new tasks         │
│  ├── monitor_approved()    → Thread: Execute approvals         │
│  └── _watchdog_watchers()  → Thread: Restart crashed watchers │
│                                                                 │
│  When tasks detected:                                          │
│  └── call_claude_skill('process-tasks')                        │
│      ├── Uses: 'claude code -p --dangerously-skip-permissions' │
│      ├── Input: '/process-tasks\n'                             │
│      ├── Timeout: 300 seconds                                  │
│      └── Working Dir: AI_Employee_Vault                        │
└─────────────────────────────────────────────────────────────────┘
```

---

### 3. WATCHDOG (Reliability Layer)

**Location:** `ai_employee_scripts/watchdog.py`

The watchdog ensures **24/7 uptime** by:

1. **Monitoring:** Checks orchestrator PID every 60 seconds
2. **Restarting:** Auto-restarts crashed orchestrator
3. **Rate Limiting:** Gives up after 10 restarts in 5 minutes
4. **Process Health:** Uses `/proc/{pid}/status` to detect zombie processes

**Hierarchy:**
```
watchdog.py
    └── monitors → orchestrator.py
            └── manages → [all watchers]
```

---

### 4. AGENT SKILLS (Reasoning Layer)

**Location:** `.claude/skills/{skill-name}/SKILL.md`

Skills are Claude Code agents that process tasks. Each skill has a `SKILL.md` file defining its behavior.

| Skill | Purpose | Input | Output |
|-------|---------|-------|--------|
| `/start-watcher` | Start FileSystemWatcher | None | Watcher running |
| `/stop-watcher` | Stop active watcher | None | Watcher stopped |
| `/process-tasks` | Process all pending tasks | Files in `Needs_Action/` | Plans or Approvals |
| `/create-plan` | Create execution plan | Task description | `PLAN_*.md` |
| `/execute-approved` | Execute approved actions | Files in `Approved/` | MCP calls + Done |
| `/complete-task` | Mark task complete | Task file | Moved to `Done/` |
| `/linkedin-posting` | Generate LinkedIn posts | Business context | Post in `Pending_Approval/` |
| `/twitter-posting` | Generate tweets | Business context | Tweet in `Pending_Approval/` |
| `/meta-posting` | Generate FB/IG posts | Business context | Post in `Pending_Approval/` |
| `/check-accounting` | Review financials | Odoo data | Summary report |
| `/create-invoice` | Create draft invoice | Customer details | Odoo draft |
| `/weekly-audit` | Business review | Week's activity | Audit report |

**Skill Invocation:**
```bash
# Via Claude Code
/process-tasks

# Via Orchestrator (non-interactive)
echo "/process-tasks\n" | claude code -p --dangerously-skip-permissions
```

---

### 5. MCP SERVERS (Action Layer)

**Location:** `ai_employee_scripts/mcp_servers/`
**Config:** `AI_Employee_Vault/.mcp.json`

MCP (Model Context Protocol) servers enable Claude Code to execute actions in external systems.

| MCP | Purpose | Authentication | Key Tools |
|-----|---------|----------------|-----------|
| **ai-gmail** | Send/read emails | OAuth 2.0 | `send_email`, `read_email`, `search_emails` |
| **linkedin-api** | Post to LinkedIn | OAuth token | `post_to_linkedin`, `get_linkedin_profile` |
| **linkedin-mcp** | LinkedIn messaging | Browser session | `post_content`, `reply_message`, `get_messages` |
| **twitter-api** | Post tweets | OAuth 1.0a (4 keys) | `post_tweet`, `post_business_update` |
| **odoo** | Accounting | JSON-RPC | `get_revenue`, `create_draft_invoice`, `post_invoice` |
| **meta** | Facebook/Instagram | Long-lived token | `post_to_facebook`, `post_to_instagram`, `post_to_both` |

**MCP Tool Call Pattern:**
```python
# Claude Code invokes MCP tools
await mcp__ai_gmail__send_email(
    to="client@example.com",
    subject="Invoice #1234",
    body="Hi, please find attached invoice..."
)

await mcp__odoo__create_draft_invoice(
    partner_name="Acme Corp",
    amount=2500.00,
    description="Web Development Services"
)
```

---

### 6. AI EMPLOYEE VAULT (Memory Layer)

**Location:** `AI_Employee_Vault/`

The vault is an **Obsidian workspace** that serves as the system's memory and state management.

```
AI_Employee_Vault/
├── Inbox/                    # Raw data from watchers
├── Needs_Action/             # Task queue (watchers create here)
├── Plans/                    # Execution strategies (Claude creates)
├── Pending_Approval/         # Awaiting human review
├── Approved/                 # Human-approved, ready to execute
├── Rejected/                 # Human-rejected actions
├── Done/                     # Completed tasks + summaries
├── Failed/                   # Failed items (dead letter queue)
├── Logs/                     # System logs + debug info
├── Accounting/               # Financial records + Rates.md
├── Content_To_Post/          # Social media queue
│   ├── queued/               # Generated, not yet reviewed
│   └── posted/               # Successfully posted
├── Briefings/                # Daily context for Claude
├── .claude/                  # Claude Code configuration
│   └── skills/               # Agent skills
├── Company_Handbook.md       # Rules + approval thresholds
├── Dashboard.md              # System status + recent activity
├── AGENTS.md                 # Agent instructions
├── Business_Goals.md         # Business objectives
└── .mcp.json                 # MCP server configurations
```

**File Movement Workflow (Approval Pipeline):**
```
1. Watcher detects item → Creates in Needs_Action/ + Inbox/
2. /process-tasks skill → Reads task, creates plan in Plans/
3. If multi-step → Moves to Pending_Approval/
4. Human approves → Moves to Approved/
5. /execute-approved skill → Executes via MCP, moves to Done/

OR (for simple tasks):
1. Watcher → Needs_Action/
2. /process-tasks → Handles directly, moves to Done/
```

---

## Data Flow

### Complete Lifecycle: Email → Reply

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    EMAIL PROCESSING LIFECYCLE                              │
└─────────────────────────────────────────────────────────────────────────────┘

STEP 1: PERCEPTION (GmailWatcher)
┌─────────────────────────────────────────────────────────────────────────────┐
│ GmailWatcher polls Gmail API every 2 minutes                               │
│ Query: "newer_than:1d -in:sent"                                            │
│                                                                             │
│ New email detected from: client@company.com                                 │
│ Subject: "Project Update Request"                                          │
│                                                                             │
│ → Creates: Inbox/EMAIL_Project_Update_20260303_103045.md                  │
│ → Creates: Needs_Action/TASK_EMAIL_Project_Update_20260303_103045.md       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
STEP 2: DETECTION (Orchestrator)
┌─────────────────────────────────────────────────────────────────────────────┐
│ Orchestrator monitor_needs_action() detects new file                       │
│                                                                             │
│ → Calls: call_claude_skill('process-tasks')                                │
│ → Command: claude code -p --dangerously-skip-permissions                   │
│ → Input: "/process-tasks\n"                                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
STEP 3: REASONING (Claude Code + /process-tasks)
┌─────────────────────────────────────────────────────────────────────────────┐
│ /process-tasks skill executes:                                              │
│                                                                             │
│ 1. Reads task file from Needs_Action/                                      │
│ 2. Reads full email from Inbox/                                            │
│ 3. Analyzes content against Company_Handbook.md                             │
│ 4. Determines: This is a new client requesting project update              │
│ 5. Checks Company_Handbook.md: New contacts require approval                │
│                                                                             │
│ → Creates: Plans/PLAN_Email_Response_20260303_103100.md                    │
│ → Creates: Pending_Approval/EMAIL_RESPONSE_Client_20260303.md              │
│   (Contains drafted reply for human review)                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
STEP 4: APPROVAL (Human)
┌─────────────────────────────────────────────────────────────────────────────┐
│ Human reviews draft in Pending_Approval/                                   │
│                                                                             │
│ Draft:                                                                      │
│ "Hi [Client], Thanks for reaching out! I'd be happy to provide..."        │
│                                                                             │
│ Human edits and moves to: Approved/                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
STEP 5: ACTION (Orchestrator + /execute-approved)
┌─────────────────────────────────────────────────────────────────────────────┐
│ Orchestrator monitor_approved() detects file in Approved/                  │
│                                                                             │
│ → Calls: call_claude_skill('execute-approved')                             │
│                                                                             │
│ /execute-approved skill:                                                    │
│ 1. Reads approval file                                                     │
│ 2. Extracts: to=client@company.com, subject="Re: Project Update"           │
│ 3. Calls: await mcp__ai_gmail__send_email(...)                             │
│ 4. Email sent successfully!                                                │
│                                                                             │
│ → Creates: Done/EMAIL_RESPONSE_Client_20260303.md                          │
│   (Contains execution summary)                                              │
│ → Deletes: Original from Approved/                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Complete Lifecycle: File Drop → Processing

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FILE PROCESSING LIFECYCLE                               │
└─────────────────────────────────────────────────────────────────────────────┘

STEP 1: USER DROPS FILE
┌─────────────────────────────────────────────────────────────────────────────┐
│ User drops: contract.pdf                                                   │
│ Into: drop_folder/                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
STEP 2: FILESYSTEMWATCHER DETECTS
┌─────────────────────────────────────────────────────────────────────────────┐
│ Polling check (every 2 seconds)                                            │
│                                                                             │
│ → Copies to: Inbox/20260303_104500_contract.pdf                            │
│ → Creates: Needs_Action/TASK_20260303_104500_contract.pdf.md               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
STEP 3: CLAUDE PROCESSES
┌─────────────────────────────────────────────────────────────────────────────┐
│ /process-tasks reads the PDF, determines action needed:                     │
│ - This is a client contract                                                │
│ - Needs: Review, counter-sign if needed, file in accounting               │
│                                                                             │
│ Multi-step action required → Creates plan                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## File Structure Reference

### Root Directory Files

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Instructions for Claude Code when working in this repo |
| `README.md` | Project overview and quick start |
| `PROJECT_PROGRESS.md` | Detailed feature completion status |
| `get_token.py` | OAuth helper for LinkedIn API authentication |
| `docker-compose.yml` | Odoo + PostgreSQL containers (for accounting) |
| `.env` | Contains all API credentials and secrets |

### ai_employee_scripts/ Directory

| File/Directory | Purpose |
|----------------|---------|
| `main.py` | CLI entry point for running individual watchers |
| `orchestrator.py` | 24/7 master controller (starts watchers, triggers Claude) |
| `watchdog.py` | Orchestrator monitor (auto-restarts if crashed) |
| `error_recovery.py` | Retry logic, circuit breaker, dead letter queue |
| `watchers/` | Watcher implementations (filesystem, Gmail, LinkedIn) |
| `mcp_servers/` | MCP server implementations (Gmail, LinkedIn, Twitter, Odoo, Meta) |
| `scripts/` | Cron triggers and utility scripts |
| `sessions/` | Persistent browser sessions (LinkedIn) |
| `.env` | API credentials (NEVER COMMIT) |
| `credentials.json` | Gmail OAuth credentials |
| `token_gmail.json` | Gmail refresh token (auto-generated) |
| `pyproject.toml` | UV package manager configuration |
| `uv.lock` | Dependency lock file |

### AI_Employee_Vault/ Directory

| Directory/File | Purpose |
|----------------|---------|
| `Inbox/` | Raw data storage (emails, files, messages) |
| `Needs_Action/` | Task queue (watchers create TASK_*.md here) |
| `Plans/` | Execution strategies (PLAN_*.md) |
| `Pending_Approval/` | Awaiting human review |
| `Approved/` | Approved, ready to execute |
| `Rejected/` | Human-rejected actions |
| `Done/` | Completed tasks with summaries |
| `Failed/` | Dead letter queue (failed watcher items) |
| `Logs/` | System logs, debug info, state files |
| `Accounting/` | Financial records, Rates.md |
| `Content_To_Post/` | Social media queue (queued/, posted/) |
| `Briefings/` | Daily context files for Claude |
| `.claude/skills/` | Agent skill definitions |
| `Company_Handbook.md` | Rules and approval thresholds |
| `Dashboard.md` | System status and recent activity |
| `AGENTS.md` | Agent behavior instructions |
| `Business_Goals.md` | Business objectives |
| `.mcp.json` | MCP server configurations |

---

## Setup & Installation

### Prerequisites

- **Python 3.13+**
- **UV package manager** (`pip install uv`)
- **Claude Code** (Anthropic's CLI tool)
- **Obsidian** (optional, for vault visualization)

### Initial Setup

```bash
# 1. Clone or navigate to project
cd /path/to/hackathon-0/save-1

# 2. Install Python dependencies
cd ai_employee_scripts
uv sync

# 3. Install Playwright browsers (for LinkedIn)
uv run playwright install chromium

# 4. Copy .env.example to .env
cp .env.example .env

# 5. Edit .env with your credentials
# Add: Gmail, LinkedIn, Twitter, Odoo, Meta credentials as needed

# 6. Set up Gmail API (if using GmailWatcher)
# - Go to https://console.cloud.google.com
# - Create project, enable Gmail API
# - Create OAuth credentials (Desktop app)
# - Download credentials.json to ai_employee_scripts/

# 7. First-time authentication (will trigger OAuth flows)
python main.py gmail    # Will open browser for Gmail auth
```

### Credential Configuration

```bash
# ai_employee_scripts/.env

# Gmail (OAuth 2.0)
# No env vars needed - uses credentials.json

# LinkedIn API (OAuth 2.0)
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
LINKEDIN_ACCESS_TOKEN=your_access_token

# Twitter/X (OAuth 1.0a)
X_API_KEY=your_api_key
X_API_SECRET=your_api_secret
X_ACCESS_TOKEN=your_access_token
X_ACCESS_TOKEN_SECRET=your_access_token_secret

# Odoo (JSON-RPC)
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USER=admin@example.com
ODOO_PASSWORD=your_password

# Meta Graph API
META_ACCESS_TOKEN=your_long_lived_token
META_PAGE_ID=your_page_id
```

---

## Running the System

### Development Mode (Single Watcher)

```bash
cd ai_employee_scripts

# Run specific watcher
python main.py filesystem    # File drop monitoring
python main.py gmail         # Email monitoring
python main.py linkedin      # LinkedIn messaging
```

### Production Mode (24/7)

```bash
cd ai_employee_scripts

# Start orchestrator (manages all watchers)
python orchestrator.py

# OR start with watchdog (auto-restarts orchestrator)
python watchdog.py
```

### Cron Jobs (Scheduled Tasks)

```bash
# crontab -e

# LinkedIn content generation (daily 2 AM)
0 2 * * * cd "/path/to/ai_employee_scripts" && uv run python scripts/linkedin_cron_trigger.py

# Twitter content generation (daily 3 AM)
0 3 * * * cd "/path/to/ai_employee_scripts" && uv run python scripts/twitter_cron_trigger.py

# Weekly business audit (Sunday 9 PM)
0 21 * * 0 cd "/path/to/ai_employee_scripts" && uv run python scripts/weekly_audit_cron.py
```

### Using Claude Code Skills

```bash
# From within the vault directory
cd AI_Employee_Vault

# Start file watcher
/start-watcher

# Process pending tasks
/process-tasks

# Execute approved actions
/execute-approved

# Create invoice
/create-invoice

# Check accounting status
/check-accounting
```

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **Watchers not creating tasks** | Check `Logs/watcher.log`, verify credentials, check API access |
| **Orchestrator not starting** | Check `Logs/orchestrator_*.log`, verify vault path exists |
| **MCP servers not loading** | Check `AI_Employee_Vault/.mcp.json` paths, restart Claude Code |
| **Gmail auth failing** | Delete `token_gmail.json`, re-run `python main.py gmail` |
| **LinkedIn session expired** | Delete `sessions/linkedin_mcp/`, re-login |
| **Odoo connection failed** | Verify Odoo is running: `docker-compose ps` |
| **Files stuck in Needs_Action** | Run `/process-tasks` skill manually |

### Log Locations

| Log File | Contents |
|----------|----------|
| `Logs/orchestrator_YYYYMMDD.log` | Orchestrator activity |
| `Logs/watchdog.log` | Watchdog restart events |
| `Logs/watcher.log` | Watcher errors and status |
| `Logs/process_events.jsonl` | Process start/stop events |
| `Logs/watcher_restarts.jsonl` | Watcher restart history |
| `Failed/{watcher_name}/` | Dead letter queue items |

### Debug Mode

```bash
# Run orchestrator with verbose output
cd ai_employee_scripts
python orchestrator.py  # Logs to console and file

# Check specific watcher logs
tail -f AI_Employee_Vault/Logs/orchestrator_$(date +%Y%m%d).log

# Check MCP server status
# In Claude Code, MCP servers log on startup
```

---

## Tier Completion Status

| Tier | Requirements | Status |
|------|--------------|--------|
| **Bronze** | FileSystemWatcher, Agent Skills | ✅ Complete |
| **Silver** | GmailWatcher, Gmail MCP, LinkedIn API MCP | ✅ Complete |
| **Gold** | LinkedInWatcher, LinkedIn MCP (Playwright), Twitter MCP, Odoo MCP, Meta MCP | ✅ Complete |
| **Platinum** | Cloud 24/7 hosting, multiple work zones | ⏸️ Pending |

---

## Key Design Decisions

### Why Polling Instead of Events?

**Decision:** All watchers use polling instead of event-based systems (inotify, webhooks).

**Reason:**
1. **WSL Compatibility:** WSL doesn't support inotify reliably
2. **Simplicity:** Polling works everywhere without complex setup
3. **Predictability:** Fixed intervals are easier to reason about
4. **Low Overhead:** 2-second polling for files, 2-5 min for APIs is negligible

### Why Separate Orchestrator and Watchdog?

**Decision:** Two-layer monitoring (watchdog → orchestrator → watchers).

**Reason:**
1. **Separation of Concerns:** Orchestrator manages watchers, watchdog monitors orchestrator
2. **Resilience:** If orchestrator crashes, watchdog can restart it
3. **Testing:** Can test orchestrator without watchdog interference
4. **Flexibility:** Can run orchestrator standalone for development

### Why MCP Servers Instead of Direct API Calls?

**Decision:** All external actions go through MCP servers.

**Reason:**
1. **Standardization:** MCP is Claude Code's integration protocol
2. **Isolation:** Credentials stay in MCP server, not in skills
3. **Reusability:** Multiple skills can use same MCP server
4. **Testability:** Can test MCP servers independently

### Why Obsidian Vault for Storage?

**Decision:** Use Obsidian vault as system memory.

**Reason:**
1. **Human-Readable:** Markdown files are easy to inspect
2. **Local-First:** No cloud dependency or sync issues
3. **Visualization:** Obsidian app provides graph view and search
4. **Portability:** Vault works on any system with Obsidian

---

## Next Steps

### For Bronze Tier (Basic Setup)
1. ✅ Set up FileSystemWatcher
2. ✅ Configure agent skills
3. ✅ Test file drop workflow

### For Silver Tier (Email + LinkedIn)
1. ✅ Set up GmailWatcher with OAuth
2. ✅ Configure Gmail MCP
3. ✅ Set up LinkedIn API MCP
4. ✅ Test email processing workflow

### For Gold Tier (Full Automation)
1. ✅ Set up LinkedInWatcher (Playwright)
2. ✅ Configure LinkedIn MCP for messaging
3. ✅ Set up Twitter MCP
4. ✅ Set up Odoo for accounting
5. ✅ Set up Meta MCP (Facebook/Instagram)

### For Platinum Tier (Cloud 24/7)
1. ⏸️ Deploy to cloud server (AWS/GCP/DigitalOcean)
2. ⏸️ Set up domain and SSL
3. ⏸️ Configure multiple work zones
4. ⏸️ Set up monitoring and alerting

---

*This documentation is maintained as part of the Personal AI Employee Hackathon 0 project.*
*For specific component documentation, see the `documentation/watchers/` and `documentation/mcp/` directories.*
