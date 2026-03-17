# Configuration Reference

**Part of:** Personal AI Employee - Gold/Platinum Tier
**Last Updated:** March 2026

---

## Overview

This guide documents all configuration files and environment variables used in the AI Employee system.

---

## Configuration Files

### Environment Variables (`.env`)

**Location:** `ai_employee_scripts/.env`

```bash
# ========================================
# AI Employee Configuration
# ========================================

# ------------------------------
# Agent Configuration
# ------------------------------
AGENT_TYPE=local              # local | cloud
VAULT_PATH=/path/to/AI_Employee_Vault

# ------------------------------
# Gmail Configuration
# ------------------------------
# OAuth credentials are stored in credentials.json
# Token is auto-generated in token_gmail.json
# No env vars needed for Gmail MCP

# Cloud Gmail Watcher (optional)
GMAIL_CREDENTIALS_PATH=./credentials.json
GMAIL_USER_EMAIL=me@example.com

# ------------------------------
# LinkedIn Configuration
# ------------------------------
# LinkedIn REST API
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
LINKEDIN_ACCESS_TOKEN=your_access_token
LINKEDIN_URN=urn:li:person:your_urn

# LinkedIn Playwright MCP uses browser session
# No env vars needed - uses stored session

# ------------------------------
# Twitter/X Configuration
# ------------------------------
X_API_KEY=your_api_key
X_API_SECRET=your_api_secret
X_ACCESS_TOKEN=your_access_token
X_ACCESS_TOKEN_SECRET=your_access_token_secret

# ------------------------------
# Meta (Facebook/Instagram) Configuration
# ------------------------------
META_ACCESS_TOKEN=your_long_lived_token
META_PAGE_ID=your_page_id
META_IG_ACCOUNT_ID=your_instagram_account_id  # optional

# ------------------------------
# Odoo Configuration
# ------------------------------
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USER=admin@example.com
ODOO_PASSWORD=your_password

# ------------------------------
# Cloud Agent Configuration (Platinum)
# ------------------------------
OPENAI_API_KEY=your_openai_key
XIAOMI_API_KEY=your_xiaomi_key
MODEL_NAME=glm-4.7-flash

# ------------------------------
# Optional Integrations
# ------------------------------
# WhatsApp (optional)
WHATSAPP_API_KEY=your_key
```

---

### MCP Configuration (`.mcp.json`)

**Location:** `AI_Employee_Vault/.mcp.json`

```json
{
  "mcpServers": {
    "ai-gmail": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts",
        "run",
        "mcp_servers/gmail_mcp.py"
      ],
      "env": {
        "PYTHONPATH": "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts"
      }
    },
    "linkedin-api": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts",
        "run",
        "mcp_servers/linkedin_api_mcp.py"
      ],
      "env": {
        "PYTHONPATH": "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts"
      }
    },
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
        "PYTHONPATH": "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts"
      }
    },
    "twitter-api": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts",
        "run",
        "mcp_servers/twitter_mcp.py"
      ],
      "env": {
        "PYTHONPATH": "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts"
      }
    },
    "odoo": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts",
        "run",
        "mcp_servers/odoo_mcp.py"
      ],
      "env": {
        "PYTHONPATH": "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts"
      }
    },
    "meta": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts",
        "run",
        "mcp_servers/meta_mcp.py"
      ],
      "env": {
        "PYTHONPATH": "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts"
      }
    }
  }
}
```

**Important:** Update paths to match your project location.

---

### PM2 Configuration

**Local Config (`ecosystem.local.config.js`):**

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

**Cloud Config (`ecosystem.cloud.config.js`):**

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
        OPENAI_API_KEY: 'your_key',
        XIAOMI_API_KEY: 'your_key'
      }
    }
  ]
};
```

---

### Docker Compose

**Location:** `docker-compose.yml`

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: odoo-postgres
    environment:
      - POSTGRES_USER=odoo
      - POSTGRES_PASSWORD=odoo
      - POSTGRES_DB=postgres
    volumes:
      - postgres-data:/var/lib/postgresql/data
    restart: unless-stopped

  odoo:
    image: odoo:19.0
    container_name: odoo
    depends_on:
      - postgres
    ports:
      - "8069:8069"
      - "8071:8071"
      - "8072:8072"
    environment:
      - HOST=postgres
      - USER=odoo
      - PASSWORD=odoo
    volumes:
      - odoo-data:/var/lib/odoo
      - ./addons:/mnt/extra-addons
    restart: unless-stopped

volumes:
  postgres-data:
  odoo-data:
```

---

### Python Dependencies

**Location:** `ai_employee_scripts/pyproject.toml`

```toml
[project]
name = "ai-employee"
version = "1.0.0"
requires-python = ">=3.13"
dependencies = [
    "mcp>=1.2.0",
    "httpx>=0.27.0",
    "google-api-python-client>=2.189.0",
    "google-auth>=2.48.0",
    "google-auth-oauthlib>=1.2.4",
    "playwright>=1.58.0",
    "watchdog>=6.0.0",
    "odoorpc>=0.10.1",
    "tweepy>=4.14.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

---

### Claude Code Settings

**Location:** `.claude/settings.local.json`

```json
{
  "mcpServers": {
    "ai-gmail": {
      "type": "stdio",
      "command": "uv",
      "args": ["--directory", "./ai_employee_scripts", "run", "mcp_servers/gmail_mcp.py"]
    }
  },
  "hooks": {
    "user-prompt-submit": [
      {
        "command": "python",
        "args": [".claude/hooks/ralph_wiggum.py"]
      }
    ]
  }
}
```

---

## Environment Variable Reference

### Agent Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `AGENT_TYPE` | local or cloud mode | local | No |
| `VAULT_PATH` | Path to AI_Employee_Vault | (auto-detected) | Cloud only |

### Gmail

| Variable | Description | Required |
|----------|-------------|----------|
| `GMAIL_CREDENTIALS_PATH` | Path to credentials.json | Cloud only |
| `GMAIL_USER_EMAIL` | Gmail email for cloud watcher | Cloud only |

### LinkedIn

| Variable | Description | Required |
|----------|-------------|----------|
| `LINKEDIN_CLIENT_ID` | LinkedIn app client ID | Yes |
| `LINKEDIN_CLIENT_SECRET` | LinkedIn app secret | Yes |
| `LINKEDIN_ACCESS_TOKEN` | OAuth access token | Yes |
| `LINKEDIN_URN` | User URN for posting | Yes |

### Twitter/X

| Variable | Description | Required |
|----------|-------------|----------|
| `X_API_KEY` | Twitter API key | Yes |
| `X_API_SECRET` | Twitter API secret | Yes |
| `X_ACCESS_TOKEN` | User access token | Yes |
| `X_ACCESS_TOKEN_SECRET` | User access token secret | Yes |

### Meta

| Variable | Description | Required |
|----------|-------------|----------|
| `META_ACCESS_TOKEN` | Long-lived page token | Yes |
| `META_PAGE_ID` | Facebook Page ID | Yes |
| `META_IG_ACCOUNT_ID` | Instagram account ID | For IG posting |

### Odoo

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ODOO_URL` | Odoo server URL | http://localhost:8069 | Yes |
| `ODOO_DB` | Database name | odoo | Yes |
| `ODOO_USER` | Admin username | - | Yes |
| `ODOO_PASSWORD` | Admin password | - | Yes |

### Cloud Agent

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key | Cloud only |
| `XIAOMI_API_KEY` | Xiaomi/GLM API key | Cloud only |
| `MODEL_NAME` | Model to use | Cloud only |

---

## File Paths

### Credential Files

| File | Location | Purpose |
|------|----------|---------|
| `.env` | `ai_employee_scripts/` | Environment variables |
| `credentials.json` | `ai_employee_scripts/` | Gmail OAuth client secrets |
| `token_gmail.json` | `ai_employee_scripts/` | Gmail OAuth tokens |
| `.mcp.json` | `AI_Employee_Vault/` | MCP server configs |

### State Files

| File | Location | Purpose |
|------|----------|---------|
| `gmail_processed_ids.txt` | `Logs/` | Processed email IDs |
| `circuit_breakers.json` | `Logs/` | Circuit breaker states |
| `health_status.json` | `Logs/` | Component health |

### Log Files

| File | Location | Purpose |
|------|----------|---------|
| `orchestrator_*.log` | `Logs/` | Daily orchestrator logs |
| `watchdog.log` | `Logs/` | Watchdog events |
| `vault_sync.log` | `Logs/` | Git sync activity |

---

## Updating Configuration

### Updating MCP Paths

1. Edit `AI_Employee_Vault/.mcp.json`
2. Update all paths to match your project location
3. Restart Claude Code

### Adding New MCP Server

1. Create MCP server in `ai_employee_scripts/mcp_servers/`
2. Add entry to `.mcp.json`:
   ```json
   "my-new-mcp": {
     "type": "stdio",
     "command": "uv",
     "args": ["--directory", "/path/to/scripts", "run", "mcp_servers/my_new_mcp.py"]
   }
   ```
3. Restart Claude Code

### Updating Environment Variables

1. Edit `ai_employee_scripts/.env`
2. Add or modify variables
3. Restart any running processes

---

## Security Notes

1. **Never commit `.env`** - Contains sensitive credentials
2. **Never commit `credentials.json`** - OAuth client secrets
3. **Never commit `token_*.json`** - OAuth tokens
4. **Use `.gitignore`** - Ensure sensitive files are excluded
5. **Rotate tokens regularly** - Especially if compromised

---

**Related Documentation:**
- [Security & Credentials Guide](security-credentials.md)
- [Getting Started Guide](getting-started.md)
- [Cloud Deployment Guide](cloud-deployment.md)