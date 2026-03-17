# Documentation Index

**Personal AI Employee - Hackathon 0**
**Last Updated:** March 2026

---

## Quick Start

| Document | Purpose |
|----------|---------|
| [Getting Started Guide](getting-started.md) | Installation and first-time setup |
| [Configuration Reference](configuration-reference.md) | All config files and environment variables |
| [Security & Credentials Guide](security-credentials.md) | OAuth setup and credential management |

---

## Core Documentation

### Project Overview

| Document | Description |
|----------|-------------|
| [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) | Comprehensive system overview |
| [Vault Structure Guide](vault-structure.md) | Detailed vault organization |
| [Agent Skills Reference](agent-skills-reference.md) | All 12 skills documented |
| [Error Recovery Reference](error-recovery-reference.md) | 3-layer error handling architecture |

### Deployment

| Document | Description |
|----------|-------------|
| [Cloud Deployment Guide](cloud-deployment.md) | Platinum tier cloud setup, PM2, vault sync |
| [Cron Jobs Reference](cron-jobs-reference.md) | Scheduled tasks configuration |

---

## MCP Server Documentation

| Document | MCP Server | Purpose |
|----------|------------|---------|
| [gmail-mcp.md](mcp/gmail-mcp.md) | `ai-gmail` | Gmail operations (send, read, search) |
| [linkedin-mcp.md](mcp/linkedin-mcp.md) | `linkedin-api` | LinkedIn posting via REST API |
| [linkedin-playwright-mcp.md](mcp/linkedin-playwright-mcp.md) | `linkedin-mcp` | LinkedIn via Playwright |
| [meta-api-mcp.md](mcp/meta-api-mcp.md) | `meta` | Facebook/Instagram posting |
| [twitter-mcp.md](mcp/twitter-mcp.md) | `twitter-api` | Twitter/X posting |
| [odoo-mcp.md](mcp/odoo-mcp.md) | `odoo` | Odoo accounting operations |

---

## Watcher Documentation

| Document | Watcher | Purpose |
|----------|---------|---------|
| [base-watcher.md](watchers/base-watcher.md) | `BaseWatcher` | Abstract base class |
| [filesystem-watcher.md](watchers/filesystem-watcher.md) | `FileSystemWatcher` | File drop monitoring |
| [gmail-watcher.md](watchers/gmail-watcher.md) | `GmailWatcher` | Gmail email monitoring |
| [linkedin-watcher.md](watchers/linkedin-watcher.md) | `LinkedInWatcher` | LinkedIn message monitoring |

---

## By Tier

### Bronze Tier
- [Getting Started Guide](getting-started.md)
- [Vault Structure Guide](vault-structure.md)
- [filesystem-watcher.md](watchers/filesystem-watcher.md)

### Silver Tier
- [gmail-mcp.md](mcp/gmail-mcp.md)
- [gmail-watcher.md](watchers/gmail-watcher.md)
- [linkedin-mcp.md](mcp/linkedin-mcp.md)
- [Security & Credentials Guide](security-credentials.md)

### Gold Tier
- [linkedin-playwright-mcp.md](mcp/linkedin-playwright-mcp.md)
- [linkedin-watcher.md](watchers/linkedin-watcher.md)
- [meta-api-mcp.md](mcp/meta-api-mcp.md)
- [twitter-mcp.md](mcp/twitter-mcp.md)
- [odoo-mcp.md](mcp/odoo-mcp.md)
- [Error Recovery Reference](error-recovery-reference.md)
- [Cron Jobs Reference](cron-jobs-reference.md)
- [Agent Skills Reference](agent-skills-reference.md)

### Platinum Tier
- [Cloud Deployment Guide](cloud-deployment.md)
- [Configuration Reference](configuration-reference.md)

---

## By Topic

### Setup & Installation
- [Getting Started Guide](getting-started.md)
- [Configuration Reference](configuration-reference.md)
- [Security & Credentials Guide](security-credentials.md)

### Architecture
- [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)
- [Vault Structure Guide](vault-structure.md)
- [Error Recovery Reference](error-recovery-reference.md)

### MCP Servers
- [gmail-mcp.md](mcp/gmail-mcp.md)
- [linkedin-mcp.md](mcp/linkedin-mcp.md)
- [linkedin-playwright-mcp.md](mcp/linkedin-playwright-mcp.md)
- [meta-api-mcp.md](mcp/meta-api-mcp.md)
- [twitter-mcp.md](mcp/twitter-mcp.md)
- [odoo-mcp.md](mcp/odoo-mcp.md)

### Watchers
- [base-watcher.md](watchers/base-watcher.md)
- [filesystem-watcher.md](watchers/filesystem-watcher.md)
- [gmail-watcher.md](watchers/gmail-watcher.md)
- [linkedin-watcher.md](watchers/linkedin-watcher.md)

### Skills & Automation
- [Agent Skills Reference](agent-skills-reference.md)
- [Cron Jobs Reference](cron-jobs-reference.md)

### Deployment
- [Cloud Deployment Guide](cloud-deployment.md)

---

## Quick Reference Cards

### File Locations

| Type | Location |
|------|----------|
| Credentials | `ai_employee_scripts/.env` |
| MCP Config | `AI_Employee_Vault/.mcp.json` |
| Logs | `AI_Employee_Vault/Logs/` |
| Tasks | `AI_Employee_Vault/Needs_Action/` |
| Approvals | `AI_Employee_Vault/Pending_Approval/` |

### Key Commands

```bash
# Start orchestrator
uv run python orchestrator.py ../AI_Employee_Vault

# Start with PM2
./start_pm2.sh local

# Process tasks
/process-tasks

# Execute approved
/execute-approved
```

### MCP Tools

| MCP | Key Tools |
|-----|-----------|
| ai-gmail | `send_email`, `search_emails` |
| linkedin-api | `post_to_linkedin` |
| meta | `post_to_facebook`, `post_to_instagram` |
| twitter-api | `post_tweet` |
| odoo | `create_draft_invoice`, `get_revenue` |

---

## Troubleshooting Quick Links

| Issue | Documentation |
|-------|---------------|
| Installation problems | [Getting Started Guide](getting-started.md#troubleshooting-installation) |
| OAuth errors | [Security & Credentials Guide](security-credentials.md#troubleshooting) |
| MCP not loading | [Configuration Reference](configuration-reference.md#updating-mcp-paths) |
| Watcher crashing | [Error Recovery Reference](error-recovery-reference.md#recovery-procedures) |
| Cron not running | [Cron Jobs Reference](cron-jobs-reference.md#troubleshooting) |
| Cloud deployment issues | [Cloud Deployment Guide](cloud-deployment.md#troubleshooting) |

---

## Project Status

For current implementation status, see:
- `PROJECT_PROGRESS.md` - Detailed feature completion status
- `AI_Employee_Vault/Dashboard.md` - System status overview

---

**Part of:** Personal AI Employee Hackathon 0
**Repository:** platinum-tier branch