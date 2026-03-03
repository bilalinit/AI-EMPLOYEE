---
name: stop-watcher
description: Stop the File System Watcher if it's running
---

# Stop File System Watcher

Stop the File System Watcher that is currently monitoring the drop folder.

## Usage

```
/stop-watcher
```

## What It Does

1. Checks for running watcher processes
2. Stops the watcher gracefully
3. Confirms shutdown

## How to Stop

The watcher runs as a background process. To stop it:

**Option 1: Use this skill**
- Invoke `/stop-watcher` to stop the background process

**Option 2: Manual stop**
- If running in a terminal, press `Ctrl+C`
- Find the process ID: `ps aux | grep filesystem_watcher`
- Kill the process: `kill <PID>`

## Notes

- The watcher will complete processing any file currently being handled before stopping
- Files already processed will remain in Inbox/Needs_Action
- Tasks created will not be lost
