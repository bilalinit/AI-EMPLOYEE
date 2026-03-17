# Cloud Deployment Guide

**Part of:** Personal AI Employee - Platinum Tier
**Last Updated:** March 2026

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [PM2 Setup](#pm2-setup)
- [Vault Git Sync](#vault-git-sync)
- [Cloud Agent Architecture](#cloud-agent-architecture)
- [Deployment Steps](#deployment-steps)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

---

## Overview

The Platinum Tier introduces cloud-based 24/7 operation with work-zone specialization:

- **Cloud Zone:** Runs continuously, handles drafting and processing
- **Local Zone:** Human reviews drafts, approves actions

### Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| **PM2** | Both zones | Process management, auto-restart |
| **vault_sync.py** | Both zones | Git-based vault synchronization |
| **Cloud Orchestrator** | Cloud only | Task monitoring and agent coordination |
| **Cloud Watchers** | Cloud only | Gmail, LinkedIn monitoring |

---

## Architecture

### Platinum Tier Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     PLATINUM TIER ARCHITECTURE                       │
└─────────────────────────────────────────────────────────────────────┘

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
│  │  Cloud Watchers         │    │    │    │  Local Watchers │      │
│  │  - CloudGmailWatcher    │    │    │    │  - GmailWatcher │      │
│  │  - CloudLinkedInWatcher │    │    │    │  - LinkedInWatcher│     │
│  └───────────┬─────────────┘    │    │    └────────┬────────┘      │
│              │                   │    │             │               │
│  ┌───────────▼─────────────┐    │    │    ┌────────▼────────┐      │
│  │  Cloud Agents           │    │    │    │  Claude Code    │      │
│  │  - TriageAgent          │    │    │    │  (Human Review) │      │
│  │  - EmailAgent           │    │    │    │                 │      │
│  │  - SocialAgent          │    │    │    │  /process-tasks │      │
│  │  - FinanceAgent         │    │    │    │  /execute-approved│    │
│  └───────────┬─────────────┘    │    │    └────────┬────────┘      │
│              │                   │    │             │               │
│  ┌───────────▼─────────────┐    │    │    ┌────────▼────────┐      │
│  │  Pending_Approval/      │    │    │    │ Pending_Approval/│     │
│  │  (Drafts from cloud)    │────┼────┼───▶│ (Human reviews) │      │
│  └─────────────────────────┘    │    │    └────────┬────────┘      │
│                                 │    │             │               │
│  ┌─────────────────────────┐    │    │    ┌────────▼────────┐      │
│  │   vault_sync.py         │◄───┼────┼───▶│  vault_sync.py  │      │
│  │   (Git-based sync)      │    │    │    │ (Git-based sync)│      │
│  └─────────────────────────┘    │    │    └─────────────────┘      │
│                                 │    │                             │
└─────────────────────────────────┘    └─────────────────────────────┘
                  │                                    │
                  └──────────── GitHub ────────────────┘
                        (platinum-tier branch)
```

### Work Zone Specialization

| Zone | Responsibilities |
|------|------------------|
| **Cloud** | Monitor Gmail/LinkedIn, draft responses, create content, generate invoices |
| **Local** | Review drafts, approve/reject, execute approved actions |

---

## Prerequisites

### Cloud VM Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **CPU** | 2 vCPU | 4 vCPU |
| **RAM** | 4 GB | 8 GB |
| **Storage** | 40 GB SSD | 80 GB SSD |
| **OS** | Ubuntu 22.04 LTS | Ubuntu 24.04 LTS |
| **Network** | Public IP | Static IP |

### Software Requirements

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3.13 python3.13-venv git curl

# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install PM2
sudo npm install -g pm2

# Install Node.js (for PM2)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

---

## PM2 Setup

### Configuration Files

**Local Configuration (`ecosystem.local.config.js`):**

```javascript
module.exports = {
  apps: [
    {
      name: 'ai-employee-local',
      script: 'uv',
      args: 'run python orchestrator.py ../AI_Employee_Vault',
      cwd: '/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts',
      interpreter: 'none',
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      watch: false,
      env: {
        PYTHONPATH: '/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts',
        AGENT_TYPE: 'local'
      }
    }
  ]
};
```

**Cloud Configuration (`ecosystem.cloud.config.js`):**

```javascript
module.exports = {
  apps: [
    {
      name: 'ai-employee-cloud',
      script: 'uv',
      args: 'run python cloud/cloud_orchestrator.py',
      cwd: '/home/ubuntu/ai-employee/ai_employee_scripts',
      interpreter: 'none',
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      watch: false,
      env: {
        PYTHONPATH: '/home/ubuntu/ai-employee/ai_employee_scripts',
        AGENT_TYPE: 'cloud',
        VAULT_PATH: '/home/ubuntu/ai-employee/AI_Employee_Vault',
        MODEL_NAME: 'glm-4.7-flash',
        OPENAI_API_KEY: 'your_openai_key',
        XIAOMI_API_KEY: 'your_xiaomi_key'
      }
    }
  ]
};
```

### Startup Scripts

**start_pm2.sh:**

```bash
#!/bin/bash
# Start AI Employee with PM2
# Usage: ./start_pm2.sh [local|cloud]

ENV=${1:-local}

if [ "$ENV" = "local" ]; then
    pm2 start ecosystem.local.config.js
elif [ "$ENV" = "cloud" ]; then
    pm2 start ecosystem.cloud.config.js
else
    echo "Usage: $0 [local|cloud]"
    exit 1
fi

pm2 save
```

**stop_pm2.sh:**

```bash
#!/bin/bash
# Stop AI Employee PM2 processes
# Usage: ./stop_pm2.sh [local|cloud|all]

ENV=${1:-all}

if [ "$ENV" = "local" ]; then
    pm2 stop ai-employee-local
    pm2 delete ai-employee-local
elif [ "$ENV" = "cloud" ]; then
    pm2 stop ai-employee-cloud
    pm2 delete ai-employee-cloud
elif [ "$ENV" = "all" ]; then
    pm2 stop all
    pm2 delete all
else
    echo "Usage: $0 [local|cloud|all]"
    exit 1
fi

pm2 save
```

### PM2 Commands

```bash
# Start services
./start_pm2.sh local    # Local environment
./start_pm2.sh cloud    # Cloud environment

# View status
pm2 list
pm2 status

# View logs
pm2 logs
pm2 logs ai-employee-local
pm2 logs --lines 100

# Restart
pm2 restart ai-employee-local

# Stop
./stop_pm2.sh local

# Auto-start on boot
pm2 save
pm2 startup systemd
```

---

## Vault Git Sync

### Overview

The `vault_sync.py` script synchronizes the vault between local and cloud via GitHub:

- **Pull** latest changes
- **Check** for local modifications
- **Commit** and **push** if needed
- **Detects** LOCAL vs CLOUD environment automatically

### Script Location

```
ai_employee_scripts/vault_sync.py
```

### Usage

```bash
# One-time sync
uv run python vault_sync.py

# Dry run (test without changes)
uv run python vault_sync.py --dry-run

# Check status only
uv run python vault_sync.py --status

# Continuous mode (daemon)
uv run python vault_sync.py --daemon

# Use rebase instead of merge
uv run python vault_sync.py --rebase
```

### Cron Setup

```bash
# Edit crontab
crontab -e

# Add sync job (every 5 minutes)
*/5 * * * * cd "/mnt/d/coding Q4/hackathon-0/save-1" && uv run python ai_employee_scripts/vault_sync.py >> AI_Employee_Vault/Logs/vault_sync.log 2>&1
```

### Environment Detection

The script automatically detects:

```python
def detect_environment():
    """Detect if running on LOCAL (WSL) or CLOUD (VM)"""
    hostname = socket.gethostname()
    cwd = os.getcwd()

    if 'microsoft' in os.uname().release.lower():
        return 'LOCAL'  # WSL
    elif 'ubuntu' in hostname.lower() or '/home/ubuntu' in cwd:
        return 'CLOUD'  # Oracle VM
    else:
        return 'UNKNOWN'
```

### Log Output

Logs written to: `AI_Employee_Vault/Logs/vault_sync.log`

```
2026-03-14 10:00:00 | INFO | Environment: LOCAL
2026-03-14 10:00:01 | INFO | Pulling latest changes...
2026-03-14 10:00:03 | INFO | Already up to date
2026-03-14 10:00:03 | INFO | No local changes to commit
```

---

## Cloud Agent Architecture

### Directory Structure

```
ai_employee_scripts/cloud/
├── __init__.py
├── cloud_orchestrator.py    # Main cloud controller
├── bots/
│   ├── __init__.py
│   ├── base_agent.py        # Base agent class
│   ├── triage_agent.py      # Task routing
│   ├── email_agent.py       # Email drafting
│   ├── social_agent.py      # Social content
│   ├── finance_agent.py     # Odoo operations
│   └── models.py            # Pydantic models
├── config/
│   └── __init__.py          # GLM/Xiaomi API config
├── guardrails/
│   ├── __init__.py
│   ├── input_guardrails.py  # Input validation
│   └── output_guardrails.py # Output filtering
├── mcp_servers/
│   ├── __init__.py
│   └── odoo_server.py       # Odoo MCP for cloud
└── tools/
    ├── __init__.py
    ├── file_tools.py        # Vault file operations
    └── git_tools.py         # Git operations
```

### Agent Handoff Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLOUD AGENT HANDOFF FLOW                     │
└─────────────────────────────────────────────────────────────────┘

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
    Pending_Approval/
```

### Triage Agent

Routes tasks to specialists based on content:

| Task Pattern | Routed To |
|--------------|-----------|
| `EMAIL_*`, email content | EmailAgent |
| `LINKEDIN_*`, `TWITTER_*`, `META_*` | SocialAgent |
| Invoice, payment, finance terms | FinanceAgent |

### Email Agent

**Capabilities:**
- Read email content from `Inbox/`
- Draft professional responses
- Create drafts in `Pending_Approval/`
- Use Odoo MCP for customer context

### Social Agent

**Capabilities:**
- Generate platform-specific content
- Create posts for LinkedIn, Twitter, Meta
- Use Business_Goals.md for context

### Finance Agent

**Capabilities:**
- Query Odoo for customer data
- Create draft invoices
- Get invoice history and pricing

---

## Deployment Steps

### Step 1: Prepare Cloud VM

```bash
# SSH into your cloud VM
ssh ubuntu@your-vm-ip

# Clone repository
git clone https://github.com/your-username/ai-employee.git
cd ai-employee

# Checkout platinum branch
git checkout platinum-tier
```

### Step 2: Install Dependencies

```bash
cd ai-employee/ai_employee_scripts
uv sync
```

### Step 3: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with cloud credentials
nano .env
```

Add cloud-specific variables:

```bash
# Cloud-specific
AGENT_TYPE=cloud
VAULT_PATH=/home/ubuntu/ai-employee/AI_Employee_Vault
MODEL_NAME=glm-4.7-flash
OPENAI_API_KEY=your_key
XIAOMI_API_KEY=your_key
```

### Step 4: Update Paths

Edit `ecosystem.cloud.config.js` with your cloud paths:

```javascript
cwd: '/home/ubuntu/ai-employee/ai_employee_scripts',
env: {
  PYTHONPATH: '/home/ubuntu/ai-employee/ai_employee_scripts',
  // ...
}
```

### Step 5: Configure MCP

Update `AI_Employee_Vault/.mcp.json` with cloud paths.

### Step 6: Set Up Git Sync

```bash
# Configure git credentials
git config --global user.email "your@email.com"
git config --global user.name "Your Name"

# Set up SSH key for GitHub (if not done)
ssh-keygen -t ed25519 -C "your@email.com"
cat ~/.ssh/id_ed25519.pub  # Add to GitHub
```

### Step 7: Start Services

```bash
# Make scripts executable
chmod +x start_pm2.sh stop_pm2.sh

# Start cloud services
./start_pm2.sh cloud

# Verify
pm2 status
pm2 logs ai-employee-cloud
```

### Step 8: Set Up Cron

```bash
crontab -e

# Add these lines
*/5 * * * * cd /home/ubuntu/ai-employee && uv run python ai_employee_scripts/vault_sync.py >> AI_Employee_Vault/Logs/vault_sync.log 2>&1
```

---

## Monitoring

### PM2 Monitoring

```bash
# Real-time monitoring
pm2 monit

# Process list
pm2 list

# Logs
pm2 logs --lines 200

# Resource usage
pm2 describe ai-employee-cloud
```

### Health Check Files

| File | Location | Purpose |
|------|----------|---------|
| `health_status.json` | `Logs/` | Component health |
| `circuit_breakers.json` | `Logs/` | Circuit breaker states |
| `process_events.jsonl` | `Logs/` | Process lifecycle |
| `vault_sync.log` | `Logs/` | Git sync activity |

### Log Locations

| Log | Location |
|-----|----------|
| PM2 logs | `~/.pm2/logs/` |
| Orchestrator | `Logs/orchestrator_*.log` |
| Vault sync | `Logs/vault_sync.log` |
| Cloud watcher | `Logs/cloud_*.log` |

---

## Troubleshooting

### PM2 Won't Start

```bash
# Check logs
pm2 logs ai-employee-cloud --err

# Common issues:
# 1. Path incorrect in config
# 2. Missing environment variables
# 3. Permission denied

# Test manually
cd ai_employee_scripts
uv run python cloud/cloud_orchestrator.py
```

### Git Sync Failing

```bash
# Check git status
git status

# Test manually
uv run python vault_sync.py --dry-run

# Common issues:
# 1. SSH key not configured
# 2. Wrong branch
# 3. Merge conflicts
```

### Agent Handoff Not Working

```bash
# Check cloud orchestrator logs
tail -f AI_Employee_Vault/Logs/orchestrator_*.log

# Verify MCP server
uv run python cloud/mcp_servers/odoo_server.py
```

### Vault Not Syncing

```bash
# Force sync
uv run python vault_sync.py --rebase

# Check for conflicts
git status
git diff
```

---

**Related Documentation:**
- [Getting Started Guide](getting-started.md)
- [Configuration Reference](configuration-reference.md)
- [Error Recovery Reference](error-recovery-reference.md)