# FileSystemWatcher Documentation

## Overview

The FileSystemWatcher monitors a "drop folder" for new files and automatically creates action items in the AI Employee vault. This is the **Bronze Tier** recommended watcher as it requires no external API setup.

## Architecture

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   User drops    │      │   Watcher       │      │    Vault        │
│   file in       │─────▶│   detects       │─────▶│   stores        │
│  drop_folder/   │      │   new file      │      │   task + file   │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

### Workflow

```
1. User drops file → drop_folder/
   │
2. Watcher detects (polling every 2 seconds)
   │
3. Copy to Inbox → Inbox/TIMESTAMP_filename
   │
4. Create task → Needs_Action/TASK_TIMESTAMP_filename.md
   │
5. Claude processes task → Reads Inbox file, takes action
   │
6. Move to Done → Completed task stored
```

## Key Features

### Polling-Based Design (WSL Compatible)

Unlike watchdog's event-based approach, this watcher uses polling:
- **Check interval:** 2 seconds
- **Why polling?** WSL and network filesystems don't support inotify events reliably
- **Performance:** Minimal overhead, only scans drop_folder

### Dual File Creation

For each dropped file, TWO files are created:

| File | Location | Purpose |
|------|----------|---------|
| **Inbox Copy** | `Inbox/TIMESTAMP_filename` | Original content storage |
| **Task File** | `Needs_Action/TASK_TIMESTAMP_filename.md` | Instructions for Claude |

### File Processing

```
DropFolderHandler._process_file():
│
├── 1. Sanitize filename
├── 2. Copy to Inbox with timestamp
├── 3. Create task file with:
│   ├── YAML frontmatter
│   ├── File information (size, type)
│   ├── Content preview (for text files)
│   └── Action checklist
└── 4. Log completion
```

## Constructor

```python
FileSystemWatcher(
    vault_path: str,              # Path to AI_Employee_Vault
    drop_folder: str = None,      # Path to monitor (default: ../drop_folder)
    check_interval: int = 60      # Not used (polling is fixed at 2s)
)
```

### Default Drop Folder

If not specified, defaults to a sibling of the vault:
```
/mnt/d/project/
├── AI_Employee_Vault/    # vault_path
└── drop_folder/          # default drop_folder
```

## Task File Format

```yaml
---
type: task
source: FilesystemWatcher
created: 2026-02-28T10:30:45
status: pending
priority: medium
original_file: 20260228_103045_document.pdf
---

# Task: Process Dropped File

## File Information
- **Original Name:** document.pdf
- **Size:** 1.2 MB
- **Type:** .pdf
- **Inbox Copy:** `20260228_103045_document.pdf`

## What Claude Should Do

1. **Read the file** from `/Inbox/20260228_103045_document.pdf`
2. **Analyze the content** and determine what action is needed
3. **Create a plan** in `/Plans/` if multi-step action is required
4. **Execute or request approval** based on Company_Handbook.md rules

## File Content Preview
```
(Text preview for .txt, .md, .py, .js, .json, .yaml, .yml files)
```

## Quick Actions
- [ ] Read full file from Inbox
- [ ] Determine required action
- [ ] Create plan if needed
- [ ] Execute or request approval

---
*This task was automatically created by the File System Watcher*
```

## File Detection Rules

### Ignored Files

The watcher skips:
- Hidden files (starting with `.`)
- Temporary files (starting with `~`)
- Directories
- Empty files (0 bytes)

### Supported Text Previews

Text content is extracted for preview (first 500 chars):

| Extension | Preview |
|-----------|---------|
| `.txt` | ✅ Yes |
| `.md` | ✅ Yes |
| `.py` | ✅ Yes |
| `.js` | ✅ Yes |
| `.json` | ✅ Yes |
| `.yaml`, `.yml` | ✅ Yes |
| Other | Binary or unreadable |

## Running the Watcher

### Direct Execution

```bash
cd ai_employee_scripts
python watchers/filesystem_watcher.py
```

### With Custom Vault Path

```bash
python watchers/filesystem_watcher.py /path/to/AI_Employee_Vault
```

### Using UV

```bash
cd ai_employee_scripts
uv run python watchers/filesystem_watcher.py
```

## Startup Output

```
2026-02-28 10:30:00 | FileSystemWatcher | INFO | Starting FileSystemWatcher (polling mode)
2026-02-28 10:30:00 | FileSystemWatcher | INFO | Drop folder: /mnt/d/project/drop_folder
2026-02-28 10:30:00 | FileSystemWatcher | INFO | Vault: /mnt/d/project/AI_Employee_Vault
2026-02-28 10:30:00 | FileSystemWatcher | INFO |
2026-02-28 10:30:00 | FileSystemWatcher | INFO | Workflow:
2026-02-28 10:30:00 | FileSystemWatcher | INFO |   1. Drop file in Drop_Zone
2026-02-28 10:30:00 | FileSystemWatcher | INFO |   2. Copy to /Inbox/
2026-02-28 10:30:00 | FileSystemWatcher | INFO |   3. Create task in /Needs_Action/
2026-02-28 10:30:00 | FileSystemWatcher | INFO |   4. Claude processes the task
2026-02-28 10:30:00 | FileSystemWatcher | INFO |
2026-02-28 10:30:00 | FileSystemWatcher | INFO | Press Ctrl+C to stop
2026-02-28 10:30:00 | FileSystemWatcher | INFO | ==================================================
2026-02-28 10:30:00 | FileSystemWatcher | INFO | DROP FILES HERE:
2026-02-28 10:30:00 | FileSystemWatcher | INFO |   /mnt/d/project/drop_folder
2026-02-28 10:30:00 | FileSystemWatcher | INFO | ==================================================
```

## File Processing Example

When you drop `contract.pdf`:

```
2026-02-28 10:30:15 | FileSystemWatcher | INFO | New file detected: contract.pdf
2026-02-28 10:30:15 | DropFolderHandler | INFO | Step 1: Copied to Inbox → 20260228_103015_contract.pdf
2026-02-28 10:30:15 | DropFolderHandler | INFO | Step 2: Created task → TASK_20260228_103015_contract.pdf.md
2026-02-28 10:30:15 | DropFolderHandler | INFO | ✅ Complete: contract.pdf
```

## Filename Sanitization

Special characters are replaced with underscores:

| Original | Sanitized |
|----------|-----------|
| `my file.txt` | `my_file.txt` |
| `file/name.txt` | `file_name.txt` |
| `file:name.txt` | `file_name.txt` |
| `file..txt` | `file_.txt` |
| `file<script>.txt` | `file_script_.txt` |

## Integration with Agent Skills

The watcher integrates with the `/start-watcher` and `/stop-watcher` skills:

```bash
# Start the watcher
/start-watcher

# Stop the watcher
/stop-watcher

# Process created tasks
/process-tasks
```

## Troubleshooting

### Files Not Being Detected

1. **Check drop_folder path:**
   ```bash
   # Watcher logs the drop folder path on startup
   # Ensure files are placed in the correct location
   ```

2. **Verify file has content:**
   - Empty files (0 bytes) are skipped
   - Wait for file to finish copying before dropping

3. **Check hidden files:**
   - Files starting with `.` are ignored

### Files Not Being Processed

1. **Check permissions:**
   ```bash
   ls -la drop_folder/
   ls -la AI_Employee_Vault/Inbox/
   ls -la AI_Employee_Vault/Needs_Action/
   ```

2. **Check Logs:**
   ```bash
   tail -f AI_Employee_Vault/Logs/watcher.log
   ```

## Configuration

### Environment Variables

No environment variables required for FileSystemWatcher.

### Dependencies

```toml
[tool.poetry.dependencies]
python = "^3.13"
watchdog = "^6.0"
```

Install:
```bash
cd ai_employee_scripts
uv sync
```

## File Size Display

Human-readable sizes are calculated:

| Size | Display |
|------|---------|
| < 1 KB | `123 B` |
| < 1 MB | `45.6 KB` |
| ≥ 1 MB | `2.3 MB` |

## Comparison with Other Watchers

| Feature | FileSystemWatcher | GmailWatcher | LinkedInWatcher |
|---------|-------------------|--------------|-----------------|
| **Setup Difficulty** | Easy (no API) | Medium (OAuth) | Hard (browser) |
| **Data Source** | Local files | Gmail API | LinkedIn Web |
| **Authentication** | None | OAuth 2.0 | Browser session |
| **Polling Interval** | 2 seconds | 120 seconds | 300 seconds |
| **WSL Compatible** | ✅ Yes | ✅ Yes | ✅ Yes |

## Related Files

- `watchers/base_watcher.py` - Abstract base class
- `watchers/gmail_watcher.py` - Gmail monitoring
- `watchers/linkedin_watcher.py` - LinkedIn monitoring
- `.claude/skills/start-watcher/SKILL.md` - Start watcher skill
- `.claude/skills/stop-watcher/SKILL.md` - Stop watcher skill
