# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Personal AI Employee** system for "Personal AI Employee Hackathon 0" (**Gold Tier - Complete**). The system uses Claude Code as the reasoning engine, an Obsidian vault as memory/dashboard, and Python watchers to monitor external sources.

**Core Architecture:** Perception → Reasoning → Action
- **Perception:** Watchers detect changes (Gmail, LinkedIn, filesystem) → create files in Needs_Action
- **Reasoning:** Claude Code reads files → plans action → creates approval requests
- **Action:** MCP servers execute (post content, send emails, create invoices) → human approves → logs to Done

## Project Structure

```
/mnt/d/coding Q4/hackathon-0/save-1/
├── AI_Employee_Vault/         # Obsidian vault (data/memory)
│   ├── Inbox/                 # Dropped files copied here (storage)
│   ├── Needs_Action/          # Tasks awaiting processing (TASK_*.md)
│   ├── Plans/                 # Execution plans (PLAN_*.md)
│   ├── Pending_Approval/      # Awaiting human approval
│   ├── Approved/              # Human-approved actions
│   ├── Rejected/              # Human-rejected actions
│   ├── Done/                  # Completed tasks/plans/summaries
│   ├── Failed/                # Failed items (dead letter queue)
│   ├── Logs/                  # System logs
│   ├── Accounting/            # Financial records, Rates.md
│   ├── Briefings/             # CEO weekly briefings
│   ├── Content_To_Post/       # Social media content queue
│   │   ├── queued/            # Clean post content backup
│   │   ├── posted/            # Successfully posted content
│   │   └── rejected/          # Rejected posts
│   ├── Company_Handbook.md    # Rules, approval thresholds
│   ├── Dashboard.md           # System status overview
│   ├── Business_Goals.md      # Services, target audience, topics
│   └── AGENTS.md              # Agent configuration
├── ai_employee_scripts/       # Python code (never syncs - has secrets)
│   ├── watchers/              # Watcher scripts
│   │   ├── base_watcher.py        # Abstract base class with error recovery
│   │   ├── filesystem_watcher.py  # File drop monitoring
│   │   ├── gmail_watcher.py       # Gmail email monitoring
│   │   └── linkedin_watcher.py    # LinkedIn message monitoring
│   ├── mcp_servers/           # MCP server implementations
│   │   ├── gmail_mcp.py           # Gmail operations
│   │   ├── linkedin_mcp.py        # LinkedIn via Playwright
│   │   ├── linkedin_api_mcp.py    # LinkedIn via REST API
│   │   ├── meta_mcp.py            # Facebook/Instagram posting
│   │   ├── twitter_mcp.py         # Twitter/X posting
│   │   └── odoo_mcp.py            # Odoo accounting
│   ├── scripts/               # Cron trigger scripts
│   │   ├── linkedin_cron_trigger.py
│   │   ├── meta_cron_trigger.py
│   │   ├── twitter_cron_trigger.py
│   │   └── weekly_cron_trigger.py
│   ├── orchestrator.py        # Master controller (24/7 process)
│   ├── watchdog.py            # External watchdog for orchestrator
│   ├── error_recovery.py      # Error handling utilities
│   ├── main.py                # CLI entry point
│   ├── pyproject.toml         # UV dependencies
│   └── .env                   # API credentials (not in git)
├── drop_folder/                # External input staging (monitored)
├── docker-compose.yml         # Odoo + PostgreSQL
├── .claude/                   # Claude Code configuration
│   ├── skills/                # Agent skill definitions (12 total)
│   │   ├── start-watcher/SKILL.md
│   │   ├── stop-watcher/SKILL.md
│   │   ├── process-tasks/SKILL.md
│   │   ├── create-plan/SKILL.md
│   │   ├── complete-task/SKILL.md
│   │   ├── execute-approved/SKILL.md
│   │   ├── linkedin-posting/SKILL.md
│   │   ├── meta-posting/SKILL.md
│   │   ├── twitter-posting/SKILL.md
│   │   ├── create-invoice/SKILL.md
│   │   ├── check-accounting/SKILL.md
│   │   └── weekly-audit/SKILL.md
│   └── settings.local.json    # MCP server config
└── README.md                  # Full documentation
```

**Important:** The `drop_folder` is OUTSIDE the vault because it's an external input source. The vault itself contains only data; code with secrets lives separately in `ai_employee_scripts/`.

## Running the AI Employee

```bash
cd "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts"

# Install dependencies (first time)
uv sync

# Install Playwright browsers (for LinkedIn MCP)
uv run playwright install chromium

# Start Odoo (accounting system)
docker-compose up -d

# Option 1: Start orchestrator directly (runs all watchers)
uv run python orchestrator.py ../AI_Employee_Vault

# Option 2: Start with watchdog (recommended for 24/7)
uv run python watchdog.py
```

The orchestrator:
- Runs 24/7 as a daemon process
- Manages all watchers (FileSystem, Gmail, LinkedIn)
- Monitors Needs_Action/ and Approved/ folders
- Automatically triggers Claude Code via subprocess when tasks arrive
- Has built-in watchdog to restart crashed watchers
- Implements 3-layer error recovery (external watchdog, internal watchdog, operation-level retry/circuit breaker)

## File Workflow

```
1. User drops file → drop_folder/
2. Watcher detects → copies to Inbox/TIMESTAMP_filename
3. Creates task → Needs_Action/TASK_TIMESTAMP_filename.md
4. Claude processes → reads task + original file
5. Creates plan → Plans/PLAN_TIMESTAMP_filename.md (if multi-step)
6. Executes or requests approval (per Company_Handbook.md)
7. Completes → moves task/plan/summary to Done/
```

## Task File Format

Tasks in `Needs_Action/TASK_*.md` have this frontmatter:

```yaml
---
type: task
source: FilesystemWatcher
created: ISO-8601 timestamp
status: pending
priority: medium|high|critical
original_file: filename_from_Inbox
---
```

## Available Skills

Agent Skills are invoked via slash commands. Full skill definitions are in `.claude/skills/*/SKILL.md`.

### Core Skills

### `/start-watcher`
Start the File System Watcher to monitor `drop_folder/` for new files.
- Polls every 2 seconds (WSL-compatible)
- Copies files to `/Inbox/` with timestamp prefix
- Creates task files in `/Needs_Action/`

### `/stop-watcher`
Stop the File System Watcher if running.

### `/process-tasks`
Process all pending tasks in `/Needs_Action/`.
For each task: reads task file, analyzes content, creates plan if needed, executes or requests approval.

### `/create-plan`
Create a structured execution plan for a specific task.
- Creates `PLAN_{timestamp}_{task_name}.md` in `/Plans/`
- Includes: Objective, Analysis, Steps, Approval Required, Expected Outcome

### `/complete-task`
Mark a task as completed and move to `/Done/`.

### `/execute-approved`
Execute all approved actions in `/Approved/` folder.
- Posts to LinkedIn, Facebook, Instagram, Twitter/X
- Sends emails via Gmail
- Posts Odoo invoices
- Logs results and moves files to Done/

### Content Generation Skills

### `/linkedin-posting`
Generate lead-generating LinkedIn post ideas.
- Creates files in `Content_To_Post/queued/` and `Pending_Approval/`
- Uses Business_Goals.md for context
- Generates engaging hooks with CTAs

### `/meta-posting`
Generate Facebook/Instagram posts for business.
- Creates files in `Content_To_Post/queued/` and `Pending_Approval/`
- Supports Facebook-only, Instagram-only, or both platforms

### `/twitter-posting`
Generate engaging tweets for business growth.
- Creates files in `Content_To_Post/queued/` and `Pending_Approval/`
- Under 280 characters, includes hashtags

### Accounting Skills

### `/create-invoice`
Create a draft invoice in Odoo accounting system.
- Uses Odoo MCP to create draft invoice
- Creates approval request in `Pending_Approval/`
- Requires approval before posting

### `/check-accounting`
Query Odoo for invoices, payments, revenue, and expenses.
- Uses Odoo MCP tools to fetch financial data
- Displays summary of financial status

### `/weekly-audit`
Generate comprehensive weekly CEO briefing.
- Fetches revenue, expenses, invoices, payments from Odoo
- Analyzes social media activity and email logs
- Creates briefing in `Briefings/` folder
- Emails briefing to CEO via Gmail MCP

**Quick Reference:**

| Skill | Purpose |
|-------|---------|
| `/start-watcher` | Start FileSystemWatcher monitoring drop_folder |
| `/stop-watcher` | Stop the File System Watcher |
| `/process-tasks` | Process all pending tasks in Needs_Action |
| `/create-plan` | Create structured execution plan for a task |
| `/complete-task` | Move completed task to Done with summary |
| `/execute-approved` | Execute approved posts/invoices/emails |
| `/linkedin-posting` | Generate LinkedIn post for approval |
| `/meta-posting` | Generate Facebook/Instagram post for approval |
| `/twitter-posting` | Generate tweet for approval |
| `/create-invoice` | Create draft invoice in Odoo |
| `/check-accounting` | Query Odoo financial data |
| `/weekly-audit` | Generate weekly CEO briefing |

## Approval Rules (Company_Handbook.md)

**Auto-Approve:** Reading, drafting, file organization within vault, logging

**Requires Approval:** Emails to new contacts, payments >$50, social posts, deleting files, WhatsApp messages, financial transactions

**Never Allowed:** Payments to new recipients without approval, sharing credentials, legal/medical advice, emotional contexts

## Adding a New Watcher

1. Inherit from `BaseWatcher` in `watchers/base_watcher.py`
2. Implement abstract methods:
   - `check_for_updates()` - Return list of new items
   - `create_action_file(item)` - Create .md in Needs_Action
   - `get_item_id(item)` - Return unique identifier
3. Use polling instead of inotify for WSL compatibility
4. Add to `orchestrator.py` watcher configs with autostart setting

## Watchers (3 Total)

| Watcher | Purpose | Poll Interval |
|---------|---------|---------------|
| **FileSystemWatcher** | Monitors `drop_folder/` for new files | 2 seconds |
| **GmailWatcher** | Monitors Gmail for new emails | 2 minutes |
| **LinkedInWatcher** | Monitors LinkedIn for unread messages | 5 minutes |

## MCP Servers (6 Total)

| MCP Server | Tools Provided | Purpose |
|------------|----------------|---------|
| **gmail_mcp.py** | send_email, read_email, search_emails, list_emails | Gmail operations via OAuth |
| **linkedin_api_mcp.py** | post_to_linkedin, get_linkedin_profile | LinkedIn posting via REST API |
| **linkedin_mcp.py** | post_content, reply_message, get_messages, verify_connection | LinkedIn via Playwright |
| **meta_mcp.py** | post_to_facebook, post_to_instagram, post_to_both, get_meta_profile | Facebook/Instagram posting |
| **twitter_mcp.py** | post_tweet, post_business_update, get_twitter_profile | Twitter/X posting |
| **odoo_mcp.py** | get_invoices, get_payments, get_revenue, get_expenses, create_draft_invoice, post_invoice | Odoo Accounting |

## Tier Progress

- **Bronze:** ✅ Complete (File System Watcher + Agent Skills) - February 15, 2026
- **Silver:** ✅ Complete (Gmail Watcher, MCP Servers, LinkedIn posting) - February 21, 2026
- **Gold:** ✅ Complete (6 MCP servers, Odoo accounting, Meta/Twitter posting, Weekly CEO Briefing, 3-layer error recovery) - February 26, 2026
- **Platinum:** ⏸️ Pending (Cloud 24/7, work-zone specialization)

### Bronze Tier Features ✅
- FileSystemWatcher with drop folder monitoring
- Task processing pipeline (Inbox → Needs_Action → Plans → Done)
- 4 core agent skills
- Obsidian vault with Company Handbook
- Human approval workflow

### Silver Tier Features ✅
- GmailWatcher for email monitoring
- MCP servers for Gmail and LinkedIn
- LinkedIn posting automation
- Email categorization and processing

### Gold Tier Features ✅
- Full cross-domain integration (Personal + Business)
- 6 MCP Servers (Gmail, LinkedIn API, LinkedIn Playwright, Meta, Twitter, Odoo)
- Odoo Accounting (self-hosted Docker, local MCP)
- Facebook/Instagram posting via Meta Graph API
- Twitter/X posting
- Weekly CEO Briefing with automatic email delivery
- 3-layer error recovery (watchdog, retry, circuit breaker, DLQ)
- Comprehensive audit logging
- 12 Agent Skills for complete automation

## Key Files Reference

| File | Purpose |
|------|---------|
| `AI_Employee_Vault/Company_Handbook.md` | Rules of engagement, approval thresholds |
| `AI_Employee_Vault/Business_Goals.md` | Services, target audience, topics to post about |
| `AI_Employee_Vault/Accounting/Rates.md` | Service rates for invoices |
| `AI_Employee_Vault/Dashboard.md` | System status overview, recent activity |
| `ai_employee_scripts/orchestrator.py` | Master controller - runs 24/7 |
| `ai_employee_scripts/watchdog.py` | External watchdog for orchestrator |
| `ai_employee_scripts/error_recovery.py` | Retry, circuit breaker, dead letter queue |
| `ai_employee_scripts/.env.example` | Environment config template |
| `ai_employee_scripts/pyproject.toml` | UV config (Python 3.13+, dependencies) |
| `docker-compose.yml` | Odoo + PostgreSQL containers |

## Error Recovery (3-Layer Architecture)

1. **External Watchdog** (`watchdog.py`) - Monitors and restarts orchestrator if it crashes
2. **Internal Watchdog** (in `orchestrator.py`) - Orchestrator restarts crashed watchers
3. **Operation-Level** (`error_recovery.py`) - Retry with exponential backoff, circuit breaker, dead letter queue

---
