---
name: start-watcher
description: Start the File System Watcher to monitor the drop folder for new files
---

# Start File System Watcher

Start the File System Watcher to monitor the drop folder for new files and automatically create tasks in the AI Employee vault.

## Usage

Run this command to start the watcher:

```bash
cd /mnt/d/coding\ Q4/hackathon-0/save-1/ai_employee_scripts
uv run python watchers/filesystem_watcher.py
```

## What It Does

1. Monitors `drop_folder/` for new files
2. Copies dropped files to `/Inbox/`
3. Creates task files in `/Needs_Action/`
4. Logs all activity

## Workflow

```
Drop file → Inbox (copy) → Needs_Action (task) → Claude processes
```

## Stopping the Watcher

Press `Ctrl+C` to stop the watcher.

## Notes

- Uses polling mode (checks every 2 seconds) for WSL compatibility
- Ignores hidden files (starting with `.`)
- Creates timestamped filenames to avoid conflicts
