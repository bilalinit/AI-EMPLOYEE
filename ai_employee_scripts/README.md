# AI Employee Scripts

Python scripts for the Personal AI Employee - Gold Tier Complete.

## Project Structure

```
ai_employee_scripts/
├── watchers/              # Monitor external sources
│   ├── base_watcher.py           # Abstract base class with error recovery
│   ├── filesystem_watcher.py     # File drop monitoring
│   ├── gmail_watcher.py          # Gmail integration
│   └── linkedin_watcher.py       # LinkedIn messages
├── mcp_servers/           # Model Context Protocol servers
│   ├── gmail_mcp.py              # Gmail send/read/search
│   ├── linkedin_api_mcp.py       # LinkedIn posting via REST API
│   ├── linkedin_mcp.py           # LinkedIn via Playwright (browser)
│   ├── meta_mcp.py               # Facebook/Instagram posting
│   ├── twitter_mcp.py            # Twitter/X posting
│   └── odoo_mcp.py               # Odoo accounting
├── scripts/               # Cron trigger scripts
│   ├── linkedin_cron_trigger.py
│   ├── meta_cron_trigger.py
│   ├── twitter_cron_trigger.py
│   └── weekly_cron_trigger.py
├── orchestrator.py        # Master process controller (24/7)
├── watchdog.py            # External watchdog for orchestrator
├── error_recovery.py      # Retry, circuit breaker, dead letter queue
├── sessions/              # Persistent browser sessions
├── .env.example           # Configuration template
├── pyproject.toml         # UV project config
└── uv.lock                # Dependency lock file
```

## Prerequisites

- Python 3.13+
- [UV](https://github.com/astral-sh/uv) package manager
- [Docker](https://www.docker.com/) & Docker Compose (for Odoo)
- Obsidian vault at `../AI_Employee_Vault/`

## Setup

1. **Clone/navigate to project:**
   ```bash
   cd ai_employee_scripts
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Install Playwright browsers:**
   ```bash
   uv run playwright install chromium
   ```

4. **Start Odoo (accounting system):**
   ```bash
   cd ..
   docker-compose up -d
   # Access at http://localhost:8069 (admin/admin)
   ```

5. **Configure environment:**
   ```bash
   cd ai_employee_scripts
   cp .env.example .env
   # Edit .env with your API keys and credentials
   ```

6. **Get LinkedIn access token:**
   ```bash
   python get_token.py
   # Copy the token to .env as LINKEDIN_ACCESS_TOKEN
   ```

## Usage

### Start the Orchestrator (24/7 Operation)

```bash
# Option 1: Start orchestrator directly
uv run python orchestrator.py ../AI_Employee_Vault

# Option 2: Start with watchdog (recommended for 24/7)
uv run python watchdog.py
```

The orchestrator:
- Runs all watchers (FileSystem, Gmail, LinkedIn)
- Monitors `Needs_Action/` and `Approved/` folders
- Automatically triggers Claude Code when tasks arrive
- Has built-in watchdog to restart crashed watchers
- Implements 3-layer error recovery

### Individual Watchers

#### File System Watcher
```bash
uv run python watchers/filesystem_watcher.py
```
Monitors `drop_folder/` for new files → creates tasks in `Needs_Action/`

#### Gmail Watcher
```bash
uv run python watchers/gmail_watcher.py
```
Monitors Gmail for new emails → creates tasks in `Needs_Action/`

#### LinkedIn Watcher
```bash
uv run python watchers/linkedin_watcher.py
```
Monitors LinkedIn for unread messages → creates tasks in `Needs_Action/`

### MCP Servers

All MCP servers provide tools for Claude Code to execute external actions.

#### Gmail MCP
```bash
uv run python mcp_servers/gmail_mcp.py
```
Tools: `send_email`, `read_email`, `search_emails`, `list_emails`

#### LinkedIn API MCP (REST API)
```bash
uv run python mcp_servers/linkedin_api_mcp.py
```
Tools: `post_to_linkedin`, `get_linkedin_profile`

#### LinkedIn MCP (Playwright)
```bash
uv run python mcp_servers/linkedin_mcp.py
```
Tools: `post_content`, `reply_message`, `get_messages`, `verify_connection`

#### Meta MCP (Facebook/Instagram)
```bash
uv run python mcp_servers/meta_mcp.py
```
Tools: `post_to_facebook`, `post_to_instagram`, `post_to_both`, `get_meta_profile`

#### Twitter/X MCP
```bash
uv run python mcp_servers/twitter_mcp.py
```
Tools: `post_tweet`, `post_business_update`, `get_twitter_profile`

#### Odoo MCP
```bash
uv run python mcp_servers/odoo_mcp.py
```
Tools: `create_draft_invoice`, `post_invoice`, `get_invoices`, `get_payments`, `get_revenue`, `get_expenses`

## Hackathon Progress

| Tier | Status | Features |
|------|--------|----------|
| **Bronze** | ✅ Complete | File System Watcher, Agent Skills, Task Pipeline |
| **Silver** | ✅ Complete | Gmail Watcher, Gmail/LinkedIn MCPs, Orchestrator |
| **Gold** | ✅ Complete | 6 MCP Servers, Odoo Accounting, Meta/Twitter, Weekly Briefing, 3-Layer Error Recovery |
| **Platinum** | ⏸️ Pending | Cloud 24/7 deployment, Work-zone specialization |

## Environment Variables

See `.env.example` for all required variables:

- **LinkedIn:** `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`
- **Meta:** `META_ACCESS_TOKEN`, `META_PAGE_ID`
- **Twitter/X:** `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET`
- **Odoo:** `ODOO_URL`, `ODOO_DB`, `ODOO_USER`, `ODOO_PASSWORD`

## Architecture

The AI Employee follows a **Perception → Reasoning → Action** pattern:

```
┌─────────────────┐
│  Perception     │  Watchers detect changes
│  (Watchers)     │  → Create files in Needs_Action
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Reasoning      │  Claude Code reads files
│  (Claude Code)  │  → Plans action → Creates approval request
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Action         │  Human approves → MCP executes
│  (MCP Servers)  │  → Logs to Done
└─────────────────┘
```

## Error Recovery

3-layer error recovery architecture:

1. **External Watchdog** (`watchdog.py`) - Monitors and restarts orchestrator
2. **Internal Watchdog** - Orchestrator restarts crashed watchers
3. **Operation Level** - Retry with exponential backoff, circuit breaker, dead letter queue

## Development

### Adding a New Watcher

1. Inherit from `BaseWatcher` in `watchers/base_watcher.py`
2. Implement abstract methods:
   - `check_for_updates()` - Return list of new items
   - `create_action_file(item)` - Create .md in Needs_Action
   - `get_item_id(item)` - Return unique identifier

### Adding a New MCP Server

1. Create file in `mcp_servers/`
2. Implement stdio protocol with tools
3. Add to orchestrator's MCP server list

## License

MIT License - Part of Personal AI Employee Hackathon 0
