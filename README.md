# Personal AI Employee

**A fully autonomous AI employee that monitors your digital life and handles business operations automatically.**

Built for the **Personal AI Employee Hackathon 0** - Platinum Tier Complete

---

## Hackathon Progress

### Tier Completion Status

```
███████████████████████████████████████████  BRONZE  ███████████████████████████████████████████
███████████████████████████████████████████  SILVER  ███████████████████████████████████████████
███████████████████████████████████████████   GOLD   ███████████████████████████████████████████
███████████████████████████████████████████ PLATINUM ███████████████████████████████████████████
```

| Tier | Status | Completion Date |
|------|--------|-----------------|
| **Bronze** | Complete | February 15, 2026 |
| **Silver** | Complete | February 21, 2026 |
| **Gold** | Complete | February 26, 2026 |
| **Platinum** | Complete | March 18, 2026 |

### Overall Progress: **4 of 4 Tiers Complete**

#### Bronze Tier
- FileSystemWatcher with drop folder monitoring
- Task processing pipeline (Inbox -> Needs_Action -> Plans -> Done)
- 4 core agent skills
- Obsidian vault with Company Handbook
- Human approval workflow

#### Silver Tier
- GmailWatcher for email monitoring
- MCP servers for Gmail and LinkedIn
- LinkedIn posting automation
- Email categorization and processing
- Integration with Claude Code

#### Gold Tier
- Full cross-domain integration (Personal + Business)
- **6 MCP Servers** (Gmail, LinkedIn API, LinkedIn Playwright, Meta, Twitter, Odoo)
- Odoo Accounting (self-hosted Docker, local MCP)
- Facebook/Instagram posting via Meta Graph API
- Twitter/X posting
- Weekly CEO Briefing with automatic email delivery
- 3-layer error recovery (watchdog, retry, circuit breaker, DLQ)
- Comprehensive audit logging
- **12 Agent Skills** for complete automation

#### Platinum Tier
- **AWS Cloud Deployment** (24/7 operation on EC2 t3.small)
- **Cloud Orchestrator** using OpenAI Agents SDK with GLM model
- **Work-Zone Specialization** (Cloud drafts, Local approves)
- **TriageAgent** with automatic SDK handoffs to specialists
- **EmailAgent, SocialAgent, FinanceAgent** for specialized processing
- Input/Output guardrails for security
- Git-based vault sync (Cloud <-> Local via GitHub)
- PM2 process management with auto-restart
- Deduplication API for local/cloud coordination

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Cloud Agent Architecture](#cloud-agent-architecture-platinum-tier)
- [Features](#features)
- [Quick Start](#quick-start)
- [AWS Cloud Deployment](#aws-cloud-deployment)
- [Configuration](#configuration)
- [Usage](#usage)
- [PM2 Process Management](#pm2-process-management)
- [Components](#components)
- [Documentation](#documentation)
- [Troubleshooting](#troubleshooting)

---

## Overview

The Personal AI Employee is a 24/7 autonomous system that perceives, reasons about, and acts on your personal and business tasks. It combines:

- **Perception:** Watchers monitor Gmail, LinkedIn, and local files
- **Reasoning:** Cloud agents (GLM) or Claude Code process tasks and create drafts
- **Action:** MCP servers execute actions (post content, send emails, create invoices)
- **Memory:** Obsidian vault stores all data, tasks, plans, and logs
- **Safety:** Human-in-the-loop approval for sensitive actions

### What It Does

| Category | Capability |
|----------|------------|
| **Email** | Monitors Gmail, categorizes messages, drafts replies automatically |
| **Social Media** | Generates and posts content to LinkedIn, Facebook, Instagram, Twitter/X |
| **Accounting** | Creates invoices in Odoo, tracks revenue and expenses |
| **Files** | Monitors drop folder for new files and tasks |
| **Reporting** | Generates weekly CEO briefings with financial and activity summaries |
| **Cloud** | 24/7 AWS operation with automatic email processing and draft generation |

---

## Architecture

### System Workflow (Platinum Tier)

```
                         AWS CLOUD (16.16.91.158)
+-------------------------------------------------------------------------+
|                                                                         |
|  PM2 Services:                                                          |
|  +-------------------------+    +------------------------------------+  |
|  | ai-employee-dedup-api  |    |     ai-employee-cloud              |  |
|  |   Port 5000            |    |                                    |  |
|  |   Coordinates          |    |  +------------------------------+ |  |
|  |   local/cloud          |    |  |   Cloud Orchestrator         | |  |
|  +-------------------------+    |  |   (OpenAI Agents SDK + GLM)  | |  |
|                                 |  +------------------------------+ |  |
|                                 |              |                     |  |
|                                 |  +-----------v------------------+ |  |
|                                 |  |   Cloud Watchers             | |  |
|                                 |  |   - Gmail (2 min poll)       | |  |
|                                 |  |   - LinkedIn (5 min poll)    | |  |
|                                 |  +------------------------------+ |  |
|                                 |              |                     |  |
|                                 |  +-----------v------------------+ |  |
|                                 |  |   Specialist Agents          | |  |
|                                 |  |   - EmailAgent               | |  |
|                                 |  |   - SocialAgent              | |  |
|                                 |  |   - FinanceAgent             | |  |
|                                 |  +------------------------------+ |  |
|                                 +------------------------------------+  |
|                                                                         |
|  Cron: git pull && git add && git commit && git push (every 5 min)     |
+-------------------------------------------------------------------------+
                                    |
                                    | Git Sync
                                    v
+-------------------------------------------------------------------------+
|                           LOCAL (Your PC)                               |
|                                                                         |
|  Cron Jobs:                                                             |
|  - Vault sync (every 5 min)                                            |
|  - LinkedIn post (2 AM daily)                                          |
|  - Meta post (3 AM daily)                                              |
|  - Twitter post (4 AM daily)                                           |
|  - CEO Briefing (5 AM Sunday)                                          |
|                                                                         |
|  Services:                                                              |
|  - Odoo Accounting (Docker)                                             |
|  - Claude Code (Human Review)                                          |
|  - Final Action Execution                                               |
+-------------------------------------------------------------------------+
```

### Work-Zone Specialization

| Zone | Owns | Why |
|------|------|-----|
| **Cloud** | Email monitoring, Draft generation, Social content drafts | 24/7 operation |
| **Local** | Approvals, Payments, Odoo, Final send/post | Human-in-the-loop, Security |

---

## Cloud Agent Architecture (Platinum Tier)

### Agent Handoff Flow

```
Email arrives in Gmail
         |
         v
+------------------+
| Gmail Watcher    |  (Cloud, 2 min poll)
| Creates task in  |
| Needs_Action/    |
+--------+---------+
         |
         v
+------------------+
| Cloud            |
| Orchestrator     |  (Checks every 4 min)
| Reads task       |
+--------+---------+
         |
         v
+------------------+
| TriageAgent      |  (GLM Model)
| Routes to        |
| specialist       |
+--------+---------+
         |
    +----+----+
    |    |    |
    v    v    v
+------+ +------+ +----------+
|Email | |Social| | Finance  |
|Agent | |Agent | |  Agent   |
+------+ +------+ +----------+
    |       |         |
    +-------+---------+
            |
            v
+------------------+
| Pending_Approval/|  (Draft created)
| Human reviews    |
+------------------+
            |
            v
       Git Push
            |
            v
      Local Pulls
            |
            v
    Human Approves
            |
            v
      Final Action
```

### Cloud Agent Components

| Component | File | Purpose |
|-----------|------|---------|
| **TriageAgent** | `cloud/bots/triage_agent.py` | Routes tasks to specialists |
| **EmailAgent** | `cloud/bots/email_agent.py` | Drafts email responses |
| **SocialAgent** | `cloud/bots/social_agent.py` | Creates social content |
| **FinanceAgent** | `cloud/bots/finance_agent.py` | Odoo operations, invoices |
| **InputGuardrails** | `cloud/guardrails/input_guardrails.py` | Blocks prompt injection, spam |
| **OutputGuardrails** | `cloud/guardrails/output_guardrails.py` | Filters sensitive output |
| **Dedup API** | `cloud/api_server.py` | Coordinates local/cloud processing |

---

## Features

### Complete Feature List

#### Email Automation
- Automatic email monitoring (Gmail API)
- Smart categorization and priority detection
- Automatic draft replies generated by cloud agents
- Human approval before sending

#### Social Media
- LinkedIn posting (API and Playwright)
- Facebook Page posting
- Instagram Business posting
- Twitter/X posting
- Content queue with scheduled posting

#### Accounting (Odoo)
- Draft invoice creation
- Payment tracking
- Revenue and expense reports
- Weekly CEO briefing generation

#### Cloud Operation (Platinum)
- 24/7 AWS EC2 deployment
- Automatic email processing
- Draft generation without human intervention
- Git-based sync between cloud and local

#### Safety & Security
- Human-in-the-loop approval
- Input guardrails (prompt injection detection)
- Output guardrails (sensitive data filtering)
- Rate limiting per sender
- Audit logging

---

## Quick Start

### Prerequisites

- **Python 3.13+** (managed via UV)
- **Docker & Docker Compose** (for Odoo)
- **Claude Code CLI** (with Claude 4.6)
- **PM2** (for 24/7 process management)
- API credentials for: LinkedIn, Meta, Twitter, Gmail, GLM

### 1. Clone and Install

```bash
git clone https://github.com/bilalinit/AI-EMPLOYEE.git
cd AI-EMPLOYEE/ai_employee_scripts

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

Required environment variables:
```env
# GLM API (for cloud agents)
GLM_API_KEY=your_glm_api_key
MODEL_NAME=glm-4.7
GLM_BASE_URL=https://api.z.ai/api/paas/v4/

# Gmail OAuth
GOOGLE_CREDENTIALS={"installed":{"client_id":"..."}}

# LinkedIn
LINKEDIN_ACCESS_TOKEN=your_token
LINKEDIN_CLIENT_ID=your_id
LINKEDIN_CLIENT_SECRET=your_secret

# Twitter/X
X_API_KEY=your_key
X_API_SECRET=your_secret
X_ACCESS_TOKEN=your_token
X_ACCESS_TOKEN_SECRET=your_secret

# Meta (Facebook/Instagram)
META_ACCESS_TOKEN=your_token
META_PAGE_ID=your_page_id

# Odoo
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USER=your_email
ODOO_PASSWORD=your_password
```

### 3. Start Odoo (Accounting)

```bash
cd ..
docker-compose up -d

# Access Odoo at http://localhost:8069
# Create database, install Invoicing app
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
pm2 start ecosystem.local.config.js
pm2 save
```

### 5. Setup Cron Jobs

```bash
crontab -e
```

Add:
```bash
PATH=/home/YOUR_USER/.local/bin:/usr/local/bin:/usr/bin:/bin

# Vault sync every 5 minutes
*/5 * * * * cd "/path/to/AI-EMPLOYEE" && git pull --rebase && git add -A && git diff --cached --quiet || git commit -m "Local sync" && git push

# LinkedIn post daily at 2 AM
0 2 * * * cd "/path/to/AI-EMPLOYEE/ai_employee_scripts" && uv run python scripts/linkedin_cron_trigger.py

# Meta post daily at 3 AM
0 3 * * * cd "/path/to/AI-EMPLOYEE/ai_employee_scripts" && uv run python scripts/meta_cron_trigger.py

# Twitter post daily at 4 AM
0 4 * * * cd "/path/to/AI-EMPLOYEE/ai_employee_scripts" && uv run python scripts/twitter_cron_trigger.py

# Weekly CEO Briefing Sunday at 5 AM
0 5 * * 0 cd "/path/to/AI-EMPLOYEE/ai_employee_scripts" && uv run python scripts/weekly_cron_trigger.py
```

---

## AWS Cloud Deployment

### Instance Details

| Setting | Value |
|---------|-------|
| **Instance Type** | t3.small (2 vCPU, 2 GB RAM) |
| **OS** | Ubuntu Server 24.04 LTS |
| **Public IP** | 16.16.91.158 |
| **Open Ports** | 22 (SSH), 80, 443, 5000 (API) |
| **Cost** | ~$15/month (fits in $50 credit for 3 months) |

### Deployed Services

| Service | Status | URL |
|---------|--------|-----|
| **Dedup API** | Online | http://16.16.91.158:5000/health |
| **Cloud Orchestrator** | Online | - |
| **Gmail Watcher** | Online | Polls every 2 min |
| **LinkedIn Watcher** | Online | Polls every 5 min |

### AWS Deployment Steps

1. **Create EC2 Instance** (t3.small, Ubuntu 24.04)
2. **Save SSH Key** to `~/.ssh/ai-employee-key-aws.pem`
3. **Connect and Install Dependencies:**
   ```bash
   ssh -i ~/.ssh/ai-employee-key-aws.pem ubuntu@YOUR_IP
   sudo apt update && sudo apt install -y python3 nodejs npm git
   curl -LsSf https://astral.sh/uv/install.sh | sh
   sudo npm install -g pm2
   ```
4. **Clone Repository:**
   ```bash
   git clone https://github.com/bilalinit/AI-EMPLOYEE.git ai-employee
   cd ai-employee/ai_employee_scripts
   uv sync
   uv run playwright install chromium
   ```
5. **Configure .env** (copy from local)
6. **Copy Gmail OAuth Token** from local:
   ```bash
   scp -i ~/.ssh/ai-employee-key-aws.pem \
     sessions/token_cloud_gmail_watcher.json \
     ubuntu@YOUR_IP:~/ai-employee/ai_employee_scripts/sessions/
   ```
7. **Start PM2:**
   ```bash
   pm2 start ecosystem.aws.config.js
   pm2 save
   pm2 startup systemd
   ```
8. **Set up Cron:**
   ```bash
   */5 * * * * cd /home/ubuntu/ai-employee && git pull && git add -A && git diff --cached --quiet || git commit -m "Cloud sync" && git push
   ```

### Cloud SSH Access

```bash
ssh -i ~/.ssh/ai-employee-key-aws.pem ubuntu@16.16.91.158
```

### Cloud Management Commands

```bash
# Check status
pm2 status

# View logs
pm2 logs ai-employee-cloud

# Restart services
pm2 restart all

# Check API health
curl http://localhost:5000/health
```

---

## Configuration

### Vault Structure

```
AI_Employee_Vault/
+-- Inbox/              # Incoming emails and files
+-- Needs_Action/       # Tasks awaiting processing
+-- In_Progress/        # Tasks being worked on
|   +-- cloud/          # Cloud agent tasks
|   +-- local/          # Local tasks
+-- Pending_Approval/   # Drafts awaiting human review
+-- Approved/           # Human-approved actions
+-- Rejected/           # Human-rejected actions
+-- Done/               # Completed tasks
+-- Logs/               # System logs
+-- Accounting/         # Financial records
+-- Content_To_Post/    # Social media queue
|   +-- queued/         # Pending posts
|   +-- posted/         # Published posts
+-- Company_Handbook.md # Rules and approval thresholds
+-- Dashboard.md        # System status
+-- Business_Goals.md   # Business objectives
```

### Approval Rules (Company_Handbook.md)

| Category | Actions |
|----------|---------|
| **Auto-Approve** | Reading, drafting, file organization, logging |
| **Requires Approval** | Emails to new contacts, payments >$50, social posts |
| **Never Allowed** | Payments without approval, sharing credentials, legal advice |

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
| `/execute-approved` | Execute approved posts, invoices, emails |
| `/linkedin-posting` | Generate lead-generating LinkedIn post ideas |
| `/meta-posting` | Generate Facebook/Instagram posts |
| `/twitter-posting` | Generate engaging tweets |
| `/create-invoice` | Create draft invoice in Odoo |
| `/check-accounting` | Query Odoo financial data |
| `/weekly-audit` | Generate CEO Briefing |

### Workflow Example

1. **Email arrives** -> Gmail Watcher creates task
2. **Cloud processes** -> TriageAgent routes to EmailAgent
3. **Draft created** -> Saved in `Pending_Approval/`
4. **Git sync** -> Draft appears locally
5. **Human reviews** -> Edits/approves in Obsidian
6. **Move to Approved/** -> Marked for execution
7. **Git sync** -> Cloud sees approval
8. **Email sent** -> via Gmail MCP

---

## PM2 Process Management

### Local Environment

```bash
cd ai_employee_scripts
pm2 start ecosystem.local.config.js
pm2 save
```

### Cloud Environment

```bash
pm2 start ecosystem.aws.config.js
pm2 save
pm2 startup systemd
```

### Useful Commands

```bash
pm2 status              # Check all processes
pm2 logs                # View all logs
pm2 logs ai-employee-cloud  # View specific logs
pm2 restart all         # Restart everything
pm2 restart --update-env    # Restart with new env
pm2 stop all            # Stop all
pm2 save                # Save current state
```

---

## Components

### Watchers

| Watcher | Location | Purpose | Interval |
|---------|----------|---------|----------|
| **FileSystemWatcher** | Local | Monitors drop_folder/ | Event-based |
| **GmailWatcher** | Local/Cloud | Monitors Gmail | 2 min |
| **LinkedInWatcher** | Local/Cloud | Monitors LinkedIn | 5 min |

### MCP Servers

| MCP Server | Purpose |
|------------|---------|
| **Gmail MCP** | Send, read, search emails |
| **LinkedIn API MCP** | Post via REST API |
| **LinkedIn Playwright MCP** | Browser automation |
| **Meta MCP** | Facebook/Instagram posting |
| **Twitter MCP** | Twitter/X posting |
| **Odoo MCP** | Invoice and accounting operations |

### Cloud Agents

| Agent | Purpose |
|-------|---------|
| **TriageAgent** | Routes tasks to specialists |
| **EmailAgent** | Drafts email responses |
| **SocialAgent** | Creates social content |
| **FinanceAgent** | Odoo operations |

### Error Recovery

| Layer | Component | Purpose |
|-------|-----------|---------|
| 1 | watchdog.py | Monitors orchestrator, auto-restart |
| 2 | orchestrator.py | Restarts crashed watchers |
| 3 | error_recovery.py | Retry, circuit breaker, DLQ |

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

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **Watchdog says "already running"** | `rm /tmp/ai_employee_orchestrator.pid` |
| **Gmail auth fails** | Delete token file, re-authenticate |
| **Odoo connection refused** | `docker-compose up -d` |
| **LinkedIn 401** | Refresh access token |
| **Cloud can't find 'uv'** | Check PATH in ecosystem.aws.config.js |
| **Drafts not appearing locally** | Check git sync cron is running |
| **PM2 won't start** | Verify paths in ecosystem config |

### Cloud-Specific Issues

| Issue | Solution |
|-------|----------|
| **Can't access port 5000** | Add to AWS Security Group inbound rules |
| **Gmail watcher crash** | Copy OAuth token from local machine |
| **Git push fails** | Set up SSH key for GitHub on cloud |

---

## Statistics

| Metric | Count |
|--------|-------|
| **Tiers Completed** | 4/4 (100%) |
| **Watchers** | 3 |
| **MCP Servers** | 6 |
| **Agent Skills** | 12 |
| **Cloud Agents** | 4 |
| **Cron Jobs** | 5 |
| **Error Recovery Layers** | 3 |
| **Cloud VM** | AWS EC2 t3.small |

---

## License

This project is part of the Personal AI Employee Hackathon 0.

---

**Built with:** Claude Code, Python, UV, Docker, Odoo, Obsidian, OpenAI Agents SDK, GLM (Zhipu AI)

**Last Updated:** March 18, 2026

**Project Status:** Platinum Tier Complete