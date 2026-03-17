# Personal AI Employee

**A fully autonomous AI employee that monitors your digital life and handles business operations automatically.**

Built for the **Personal AI Employee Hackathon 0** - Platinum Tier In Progress (~85% Complete)

---

## Hackathon Progress

### Tier Completion Status

```
███████████████████████████████████████████  BRONZE  ███████████████████████████████████████████
███████████████████████████████████████████  SILVER  ███████████████████████████████████████████
███████████████████████████████████████████   GOLD   ███████████████████████████████████████████
██████████████████████████████████████░░░░ PLATINUM ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
```

| Tier | Status | Requirements | Completion Date |
|------|--------|--------------|-----------------|
| **Bronze** | ✅ Complete | 4/4 | February 15, 2026 |
| **Silver** | ✅ Complete | 4/4 | February 21, 2026 |
| **Gold** | ✅ Complete | 12/12 | February 26, 2026 |
| **Platinum** | 🔄 In Progress | ~85% | March 2026 |

### Overall Progress: **3.85 of 4 Tiers Complete**

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

#### Platinum Tier 🔄 (~85% Complete)
- ✅ Cloud Orchestrator with task monitoring
- ✅ Triage Agent with SDK handoffs to specialists
- ✅ Email, Social, Finance agents
- ✅ Input/Output guardrails
- ✅ Odoo MCP server integration (all 5 tools tested)
- ✅ Per-request MCP lifecycle
- ✅ PM2 Process Manager (24/7 operation)
- ✅ Vault Git Sync (Cloud ↔ Local via GitHub)
- ⬜ Cloud deployment (Oracle VM setup)
- ⬜ Work-zone specialization (Cloud drafts, Local approves)

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Cloud Agent Architecture](#cloud-agent-architecture-platinum-tier)
- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [PM2 Process Management](#pm2-process-management)
- [Components](#components)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Documentation](#documentation)
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
| **Cloud (Platinum)** | 24/7 cloud operation with local approval workflow |

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
                    ║  4. Cloud Orchestrator (Platinum Tier)     ║
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

---

## Cloud Agent Architecture (Platinum Tier)

### Work-Zone Specialization

The Platinum tier introduces **Cloud + Local** work zones:

```
┌─────────────────────────────────┐    ┌─────────────────────────────┐
│         CLOUD ZONE              │    │        LOCAL ZONE           │
│   (Oracle VM / AWS / GCP)       │    │   (WSL / Development PC)    │
├─────────────────────────────────┤    ├─────────────────────────────┤
│                                 │    │                             │
│  ┌─────────────────────────┐    │    │    ┌─────────────────┐      │
│  │     PM2 Process         │    │    │    │  PM2 Process    │      │
│  │  ai-employee-cloud      │    │    │    │ ai-employee-local│     │
│  └───────────┬─────────────┘    │    │    └────────┬────────┘      │
│              │                   │    │             │               │
│  ┌───────────▼─────────────┐    │    │    ┌────────▼────────┐      │
│  │  Cloud Orchestrator     │    │    │    │   Orchestrator  │      │
│  │  (cloud_orchestrator.py)│    │    │    │  (orchestrator.py)│     │
│  └───────────┬─────────────┘    │    │    └────────┬────────┘      │
│              │                   │    │             │               │
│  ┌───────────▼─────────────┐    │    │    ┌────────▼────────┐      │
│  │  Cloud Agents           │    │    │    │  Claude Code    │      │
│  │  - TriageAgent          │    │    │    │  (Human Review) │      │
│  │  - EmailAgent           │────┼────┼───▶│                 │      │
│  │  - SocialAgent          │    │    │    │  /process-tasks │      │
│  │  - FinanceAgent         │    │    │    │  /execute-approved│    │
│  └───────────┬─────────────┘    │    │    └─────────────────┘      │
│              │                   │    │                             │
│  ┌───────────▼─────────────┐    │    │                             │
│  │  Pending_Approval/      │    │    │                             │
│  │  (Drafts from cloud)    │────┼───▶│  Human reviews & approves   │
│  └─────────────────────────┘    │    │                             │
│                                 │    │                             │
│  ┌─────────────────────────┐    │    │                             │
│  │   vault_sync.py         │◄───┼───▶│  vault_sync.py              │
│  │   (Git-based sync)      │    │    │  (Git-based sync)           │
│  └─────────────────────────┘    │    │                             │
│                                 │    │                             │
└─────────────────────────────────┘    └─────────────────────────────┘
                  │                                    │
                  └──────────── GitHub ────────────────┘
                        (platinum-tier branch)
```

### Cloud Agent Components

| Component | File | Purpose |
|-----------|------|---------|
| **TriageAgent** | `cloud/bots/triage_agent.py` | Routes tasks to specialists |
| **EmailAgent** | `cloud/bots/email_agent.py` | Drafts email responses |
| **SocialAgent** | `cloud/bots/social_agent.py` | Creates social content |
| **FinanceAgent** | `cloud/bots/finance_agent.py` | Odoo operations, invoices |
| **InputGuardrails** | `cloud/guardrails/input_guardrails.py` | Blocks prompt injection |
| **OutputGuardrails** | `cloud/guardrails/output_guardrails.py` | Filters sensitive output |

### Agent Handoff Flow

```
Task arrives in Needs_Action/
              │
              ▼
    ┌─────────────────┐
    │  TriageAgent    │
    │  (Task Router)  │
    └────────┬────────┘
             │
    ┌────────┼────────┐
    │        │        │
    ▼        ▼        ▼
┌───────┐ ┌───────┐ ┌───────────┐
│ Email │ │Social │ │  Finance  │
│ Agent │ │ Agent │ │   Agent   │
└───┬───┘ └───┬───┘ └─────┬─────┘
    │         │           │
    └─────────┴───────────┘
              │
              ▼
    Pending_Approval/ (Human reviews)
```

---

## Features

### All Tiers

#### Bronze Tier ✅
- FileSystemWatcher for drop folder monitoring
- Task processing pipeline (Needs_Action → Plans → Done)
- 4 core agent skills
- Obsidian vault for memory and dashboard
- Company handbook with approval rules

#### Silver Tier ✅
- GmailWatcher for email monitoring
- MCP servers for Gmail and LinkedIn
- LinkedIn posting skill
- Email processing and categorization
- Human approval workflow

#### Gold Tier ✅
- Full cross-domain integration (Personal + Business)
- Odoo Accounting (self-hosted, local, MCP)
- Facebook/Instagram posting via Meta Graph API
- Twitter/X posting
- 6 MCP servers
- Weekly CEO Briefing with automatic email delivery
- 3-layer error recovery
- Comprehensive audit logging
- Ralph Wiggum stop hook
- 12 Agent Skills

#### Platinum Tier 🔄
- Cloud Orchestrator for 24/7 operation
- Specialist agents (Email, Social, Finance)
- SDK automatic handoffs
- Input/Output guardrails
- PM2 process management
- Vault Git sync (Cloud ↔ Local)
- Work-zone specialization

---

## Quick Start

### Prerequisites

- **Python 3.13+** (managed via UV)
- **Docker & Docker Compose** (for Odoo)
- **Claude Code CLI** (with Claude 4.6)
- **PM2** (for 24/7 process management)
- API credentials for: LinkedIn, Meta, Twitter, Gmail

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

### 3. Start Odoo (Accounting)

```bash
cd "/mnt/d/coding Q4/hackathon-0/save-1"
docker-compose up -d

# Access Odoo at http://localhost:8069
```

### 4. Start the AI Employee

#### Local Mode (Development)
```bash
cd ai_employee_scripts
uv run python orchestrator.py ../AI_Employee_Vault
```

#### PM2 Mode (24/7 Operation)
```bash
cd ai_employee_scripts

# Start local services
./start_pm2.sh local

# View logs
pm2 logs ai-employee-local
```

#### Cloud Mode (Platinum)
```bash
# On cloud VM
./start_pm2.sh cloud
```

### 5. Setup Cron Jobs (Automated Posting)

```bash
crontab -e
```

Add:
```bash
# LinkedIn post daily at 2 AM
0 2 * * * cd "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts" && uv run python scripts/linkedin_cron_trigger.py >> ../AI_Employee_Vault/Logs/cron.log 2>&1

# Meta post daily at 3 AM
0 3 * * * cd "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts" && uv run python scripts/meta_cron_trigger.py >> ../AI_Employee_Vault/Logs/meta_cron.log 2>&1

# Twitter post daily at 4 AM
0 4 * * * cd "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts" && uv run python scripts/twitter_cron_trigger.py >> ../AI_Employee_Vault/Logs/twitter_cron.log 2>&1

# Weekly CEO Briefing Sunday at 5 AM
0 5 * * 0 cd "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts" && uv run python scripts/weekly_cron_trigger.py >> ../AI_Employee_Vault/Logs/weekly_cron.log 2>&1

# Vault sync every 5 minutes (Platinum)
*/5 * * * * cd "/mnt/d/coding Q4/hackathon-0/save-1" && uv run python ai_employee_scripts/vault_sync.py >> AI_Employee_Vault/Logs/vault_sync.log 2>&1
```

---

## Installation

### Step-by-Step Setup

#### 1. LinkedIn OAuth Setup

```bash
python get_token.py
# Follow prompts, add token to .env
```

#### 2. Gmail OAuth Setup

Get credentials from: https://console.cloud.google.com/
Place `credentials.json` in `ai_employee_scripts/`

#### 3. Meta (Facebook/Instagram) Setup

1. Create Meta Developer Account
2. Create Facebook Page
3. Generate Page Access Token
4. Add to `.env`

#### 4. Twitter/X Setup

1. Create Twitter Developer Account
2. Generate API keys
3. Add to `.env`

#### 5. Odoo Setup

```bash
docker-compose up -d
# Access http://localhost:8069
# Create database, install Invoicing
```

---

## Configuration

### MCP Server Configuration

Located in `AI_Employee_Vault/.mcp.json`:

```json
{
  "mcpServers": {
    "ai-gmail": { ... },
    "linkedin-api": { ... },
    "linkedin-mcp": { ... },
    "twitter-api": { ... },
    "odoo": { ... },
    "meta": { ... }
  }
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
├── In_Progress/        # Work-in-progress (Platinum)
├── Logs/               # System logs
├── Accounting/         # Financial records
├── Briefings/          # CEO briefings
├── Content_To_Post/    # Queued social media content
├── Company_Handbook.md # Rules and approval thresholds
├── Dashboard.md        # System status overview
└── Business_Goals.md   # Business objectives
```

---

## Usage

### Agent Skills

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

---

## PM2 Process Management

### Configuration Files

| File | Environment |
|------|-------------|
| `ecosystem.local.config.js` | Local (WSL) |
| `ecosystem.cloud.config.js` | Cloud (Oracle VM) |

### Commands

```bash
# Start services
./start_pm2.sh local    # Local environment
./start_pm2.sh cloud    # Cloud environment

# View status
pm2 list
pm2 logs ai-employee-local

# Stop services
./stop_pm2.sh local

# Auto-start on boot
pm2 save
pm2 startup systemd
```

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
| **gmail_mcp.py** | send_email, read_email, search_emails | Gmail operations |
| **linkedin_api_mcp.py** | post_to_linkedin | LinkedIn posting via API |
| **linkedin_mcp.py** | post_content, reply_message | LinkedIn via Playwright |
| **meta_mcp.py** | post_to_facebook, post_to_instagram | FB/IG posting |
| **twitter_mcp.py** | post_tweet | Twitter/X posting |
| **odoo_mcp.py** | create_draft_invoice, get_revenue | Odoo Accounting |

### Cloud Agents (4 Total - Platinum)

| Agent | Purpose |
|-------|---------|
| **TriageAgent** | Routes tasks to specialists |
| **EmailAgent** | Drafts email responses |
| **SocialAgent** | Creates social content |
| **FinanceAgent** | Odoo operations |

### Error Recovery (3 Layers)

| Layer | Component | Purpose |
|-------|-----------|---------|
| 1 | watchdog.py | Monitors orchestrator, auto-restart |
| 2 | orchestrator.py | Restarts crashed watchers |
| 3 | error_recovery.py | Retry, circuit breaker, DLQ |

---

## Development

### Project Structure

```
/mnt/d/coding Q4/hackathon-0/save-1/
├── AI_Employee_Vault/         # Obsidian vault (data/memory)
├── ai_employee_scripts/       # Python code
│   ├── watchers/              # Watcher scripts
│   ├── mcp_servers/           # MCP server implementations
│   ├── scripts/               # Cron trigger scripts
│   ├── cloud/                 # Cloud agent architecture (Platinum)
│   │   ├── bots/              # Agent implementations
│   │   ├── guardrails/        # Input/output guardrails
│   │   ├── tools/             # File and git tools
│   │   └── mcp_servers/       # Cloud MCP servers
│   ├── cloud_watchers/        # Cloud-specific watchers
│   ├── orchestrator.py        # Local master controller
│   ├── cloud_orchestrator.py  # Cloud master controller
│   ├── watchdog.py            # External watchdog
│   ├── vault_sync.py          # Git-based vault sync
│   ├── error_recovery.py      # Error handling utilities
│   └── .env                   # API credentials
├── drop_folder/               # External input staging
├── .claude/                   # Claude Code configuration
│   └── skills/                # Agent skill definitions (12)
├── documentation/             # Project documentation
├── docker-compose.yml         # Odoo + PostgreSQL
└── README.md                  # This file
```

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **Watchdog says "already running"** | `rm /tmp/ai_employee_orchestrator.pid` |
| **Gmail auth fails** | `rm token_gmail.json`, re-auth |
| **Odoo connection refused** | `docker-compose up -d` |
| **LinkedIn 401** | Run `python get_token.py`, update .env |
| **Twitter 402** | Check X API credits |
| **Ralph Wiggum blocking** | `touch AI_Employee_Vault/stop_ralph` |
| **Circuit breaker open** | Wait 60s or `rm Logs/circuit_breakers.json` |
| **PM2 won't start** | Check paths in ecosystem.*.config.js |

---

## Documentation

Full documentation available in `documentation/`:

| Document | Purpose |
|----------|---------|
| [INDEX.md](documentation/INDEX.md) | Documentation navigation |
| [getting-started.md](documentation/getting-started.md) | Setup guide |
| [cloud-deployment.md](documentation/cloud-deployment.md) | Platinum tier deployment |
| [agent-skills-reference.md](documentation/agent-skills-reference.md) | All 12 skills |
| [vault-structure.md](documentation/vault-structure.md) | Vault organization |
| [configuration-reference.md](documentation/configuration-reference.md) | Config files |
| [security-credentials.md](documentation/security-credentials.md) | Credential setup |
| [error-recovery-reference.md](documentation/error-recovery-reference.md) | Error handling |
| [cron-jobs-reference.md](documentation/cron-jobs-reference.md) | Scheduled tasks |

---

## Statistics

| Metric | Count |
|--------|-------|
| **Tiers Completed** | 3 + Platinum (85%) |
| **Watchers** | 3 |
| **MCP Servers** | 6 |
| **Agent Skills** | 12 |
| **Cloud Agents** | 4 |
| **Cron Jobs** | 5 (4 daily + vault sync) |
| **Error Recovery Layers** | 3 |

---

## License

This project is part of the Personal AI Employee Hackathon 0.

---

**Built with:** Claude Code, Python, UV, Docker, Odoo, Obsidian, OpenAI Agents SDK

**Last Updated:** March 2026

**Project Status:** Platinum Tier In Progress (~85% Complete)