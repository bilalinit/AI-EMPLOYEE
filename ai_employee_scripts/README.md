# AI Employee Scripts

Python scripts for the Personal AI Employee - Bronze Tier and beyond.

## Project Structure

```
ai_employee_scripts/
├── watchers/              # Monitor external sources
│   ├── base_watcher.py           # Abstract base class
│   ├── filesystem_watcher.py     # File drop monitoring (Bronze)
│   ├── gmail_watcher.py          # Gmail integration (Silver)
│   └── linkedin_watcher.py       # LinkedIn messages (Silver)
├── mcp_servers/           # Model Context Protocol servers
│   ├── gmail_mcp.py              # Gmail send/read/search (Silver)
│   └── linkedin_mcp.py           # LinkedIn post/reply/fetch (Silver)
├── orchestrator.py         # Master process control (Silver)
├── sessions/              # Persistent browser sessions
│   ├── linkedin_watcher/         # LinkedIn watcher session
│   └── linkedin_mcp/             # LinkedIn MCP session (separate!)
├── .env.example           # Configuration template
└── pyproject.toml         # UV project config
```

## Prerequisites

- Python 3.13+
- [UV](https://github.com/astral-sh/uv) package manager
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

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

## Usage

### File System Watcher (Bronze Tier)

Monitors a drop folder for new files and creates action items.

```bash
# Run with UV
uv run python watchers/filesystem_watcher.py

# Or specify custom vault path
uv run python watchers/filesystem_watcher.py /path/to/vault
```

**How it works:**
1. Drop a file into `AI_Employee_Vault/Drop_Folder/`
2. Watcher detects the file
3. Creates an action file in `AI_Employee_Vault/Needs_Action/`
4. Claude Code processes the action file

### MCP Servers (Silver Tier)

Model Context Protocol servers provide tools for Claude Code to execute external actions.

#### Gmail MCP Server

```bash
# Test Gmail MCP (first run will prompt for OAuth)
uv run python mcp_servers/gmail_mcp.py
```

Tools available:
- `send_email` - Send emails via Gmail
- `read_email` - Read specific email
- `search_emails` - Search Gmail
- `list_emails` - List emails from a label
- `draft_email` - Create email drafts

#### LinkedIn MCP Server

```bash
# Test LinkedIn MCP (first run will open browser for login)
uv run python mcp_servers/linkedin_mcp.py
```

Tools available:
- `post_content` - Post to LinkedIn feed
- `reply_message` - Reply to LinkedIn messages
- `get_messages` - Fetch LinkedIn conversations
- `verify_connection` - Check login status

**Note:** LinkedIn MCP uses a separate session from `linkedin_watcher.py` for isolation.

## Hackathon Progress

| Tier | Status | Scripts |
|------|--------|---------|
| **Bronze** | ✅ Complete | File System Watcher, Agent Skills |
| **Silver** | 🟡 In Progress | Gmail Watcher ✅, Gmail MCP ✅, LinkedIn Watcher ✅, LinkedIn MCP ✅, Orchestrator ✅ |
| **Gold** | ⏸️ Pending | WhatsApp Watcher, Odoo MCP |
| **Platinum** | ⏸️ Pending | Cloud deployment |

## Development

### Adding a New Watcher

1. Inherit from `BaseWatcher` in `watchers/base_watcher.py`
2. Implement the abstract methods:
   - `check_for_updates()` - Return list of new items
   - `create_action_file(item)` - Create .md in Needs_Action
   - `get_item_id(item)` - Return unique identifier

### Running Tests

```bash
# (Coming soon)
uv run pytest
```

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

## License

MIT License - Part of Personal AI Employee Hackathon 0
