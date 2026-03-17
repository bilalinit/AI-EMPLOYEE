# Getting Started Guide

**Part of:** Personal AI Employee - Gold/Platinum Tier
**Last Updated:** March 2026

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Installation Steps](#installation-steps)
- [First-Time Setup](#first-time-setup)
- [Verifying Installation](#verifying-installation)
- [Next Steps](#next-steps)

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| **Python** | 3.13+ | Runtime environment |
| **UV Package Manager** | Latest | Dependency management |
| **Claude Code** | Latest | AI reasoning engine |
| **Git** | 2.x | Version control |
| **Docker** | Latest | Odoo + PostgreSQL (optional) |

### Optional Software

| Software | Purpose |
|----------|---------|
| **Obsidian** | Visualize vault as knowledge graph |
| **PM2** | 24/7 process management |
| **Playwright** | LinkedIn browser automation |

### System Requirements

- **OS:** Linux (WSL2), macOS, or Windows with WSL
- **RAM:** 4GB minimum, 8GB recommended
- **Disk:** 2GB for project + Docker images if using Odoo

---

## Quick Start

```bash
# 1. Navigate to project
cd "/mnt/d/coding Q4/hackathon-0/save-1"

# 2. Install Python dependencies
cd ai_employee_scripts && uv sync

# 3. Install Playwright browsers
uv run playwright install chromium

# 4. Copy environment template
cp .env.example .env

# 5. Edit .env with your credentials
nano .env

# 6. Start the orchestrator
uv run python orchestrator.py ../AI_Employee_Vault
```

---

## Installation Steps

### Step 1: Clone/Navigate to Project

```bash
cd "/mnt/d/coding Q4/hackathon-0/save-1"
```

### Step 2: Install UV Package Manager

```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via pip
pip install uv
```

### Step 3: Install Python Dependencies

```bash
cd ai_employee_scripts
uv sync
```

This installs all dependencies defined in `pyproject.toml`:

```toml
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
```

### Step 4: Install Playwright Browsers

Required for LinkedIn MCP (Playwright-based):

```bash
uv run playwright install chromium
```

### Step 5: Set Up Credentials

Copy the example environment file and add your credentials:

```bash
cp .env.example .env
nano .env
```

See [Security & Credentials Guide](security-credentials.md) for detailed setup.

### Step 6: Gmail OAuth Setup (Optional)

If using GmailWatcher:

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create project → Enable Gmail API
3. Configure OAuth consent screen
4. Create OAuth 2.0 credentials (Desktop app)
5. Download `credentials.json` to `ai_employee_scripts/`

First run will trigger browser authentication.

### Step 7: Start Odoo (Optional)

If using accounting features:

```bash
cd /path/to/project
docker-compose up -d
```

Wait 2-3 minutes for Odoo to initialize, then:
1. Open http://localhost:8069
2. Create database
3. Install Accounting module

---

## First-Time Setup

### Authentication Flow

When you first run components that require OAuth, they will:

1. **Display an authorization URL**
2. **Start a local server** on port 8080
3. **Wait for you to authorize** in your browser
4. **Save tokens** automatically

```bash
# Test Gmail authentication
cd ai_employee_scripts
uv run python mcp_servers/gmail_mcp.py
```

Expected output:

```
📧 Gmail MCP Server - Authentication
✅ Found credentials.json
🔐 Starting OAuth flow...
🌐 Opening browser for authorization...
✅ Authentication successful!
💾 Token saved to: token_gmail.json
🚀 Starting MCP server...
```

### MCP Server Configuration

MCP servers are configured in `AI_Employee_Vault/.mcp.json`:

```json
{
  "mcpServers": {
    "ai-gmail": {
      "type": "stdio",
      "command": "uv",
      "args": ["--directory", "/path/to/ai_employee_scripts", "run", "mcp_servers/gmail_mcp.py"]
    },
    "odoo": { ... },
    "linkedin-api": { ... },
    "linkedin-mcp": { ... },
    "twitter-api": { ... },
    "meta": { ... }
  }
}
```

**Important:** Update paths in `.mcp.json` to match your project location.

---

## Verifying Installation

### Check Dependencies

```bash
cd ai_employee_scripts
uv run python -c "import mcp; print('MCP OK')"
uv run python -c "import google.auth; print('Google Auth OK')"
uv run python -c "import playwright; print('Playwright OK')"
```

### Check MCP Servers

```bash
# Start each MCP server to verify
uv run python mcp_servers/gmail_mcp.py &
uv run python mcp_servers/odoo_mcp.py &
```

### Check Odoo Connection

```bash
curl http://localhost:8069
```

Should return Odoo HTML page.

### Test File System Watcher

```bash
cd ai_employee_scripts
uv run python watchers/filesystem_watcher.py
```

Drop a file in `drop_folder/` and verify task appears in `Needs_Action/`.

---

## Starting the System

### Development Mode (Single Component)

```bash
cd ai_employee_scripts

# Run individual watchers
uv run python watchers/filesystem_watcher.py
uv run python watchers/gmail_watcher.py
uv run python watchers/linkedin_watcher.py
```

### Production Mode (Full System)

```bash
cd ai_employee_scripts

# Start orchestrator (manages all watchers)
uv run python orchestrator.py ../AI_Employee_Vault

# OR start with watchdog (auto-restart on crash)
uv run python watchdog.py
```

### PM2 Mode (24/7 Operation)

```bash
cd ai_employee_scripts

# Start all services
./start_pm2.sh local

# View logs
pm2 logs

# Stop services
./stop_pm2.sh local
```

---

## Project Structure

```
/mnt/d/coding Q4/hackathon-0/save-1/
├── AI_Employee_Vault/         # Obsidian vault (data/memory)
│   ├── Inbox/                 # Raw data storage
│   ├── Needs_Action/          # Task queue
│   ├── Plans/                 # Execution plans
│   ├── Pending_Approval/      # Human approval queue
│   ├── Approved/              # Approved actions
│   ├── Done/                  # Completed tasks
│   ├── Logs/                  # System logs
│   └── .mcp.json              # MCP configuration
├── ai_employee_scripts/       # Python code
│   ├── watchers/              # Background monitors
│   ├── mcp_servers/           # MCP implementations
│   ├── scripts/               # Cron triggers
│   ├── cloud/                 # Cloud agent architecture
│   ├── orchestrator.py        # Master controller
│   ├── watchdog.py            # Process monitor
│   └── .env                   # Credentials
├── drop_folder/               # External input
├── docker-compose.yml         # Odoo containers
└── documentation/             # This documentation
```

---

## Next Steps

1. **Configure Credentials** - See [Security & Credentials Guide](security-credentials.md)
2. **Learn the Vault** - See [Vault Structure Guide](vault-structure.md)
3. **Use Agent Skills** - See [Agent Skills Reference](agent-skills-reference.md)
4. **Set Up Cron Jobs** - See [Cron Jobs Reference](cron-jobs-reference.md)
5. **Deploy to Cloud** - See [Cloud Deployment Guide](cloud-deployment.md)

---

## Troubleshooting Installation

### "uv: command not found"

```bash
# Add UV to PATH
export PATH="$HOME/.local/bin:$PATH"

# Or add to ~/.bashrc
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### "Python version too old"

```bash
# Check Python version
python3 --version

# Install Python 3.13+ if needed
# Ubuntu/Debian
sudo apt update && sudo apt install python3.13

# Or use pyenv
pyenv install 3.13
pyenv global 3.13
```

### "Playwright browsers not found"

```bash
# Install Chromium
uv run playwright install chromium

# Or install all browsers
uv run playwright install
```

### "Docker not running"

```bash
# Start Docker
sudo systemctl start docker

# Or on WSL
sudo service docker start
```

### "Permission denied" on scripts

```bash
chmod +x ai_employee_scripts/*.sh
```

---

**Related Documentation:**
- [Security & Credentials Guide](security-credentials.md)
- [Configuration Reference](configuration-reference.md)
- [Vault Structure Guide](vault-structure.md)