#!/usr/bin/env python3
"""
Ralph Wiggum Stop Hook - Verified Version
Fires every time Claude tries to stop.
Checks if Needs_Action/ still has unprocessed files.
If yes -> block exit and tell Claude to keep going.
If no  -> allow exit.
"""
import sys
import json
from pathlib import Path

# Vault path for this project
VAULT_PATH = Path("/mnt/d/coding Q4/hackathon-0/save-1/AI_Employee_Vault")
NEEDS_ACTION = VAULT_PATH / "Needs_Action"
STOP_FILE = VAULT_PATH / "stop_ralph"  # emergency exit


def main():
    # Emergency exit - touch stop_ralph file to allow immediate exit
    if STOP_FILE.exists():
        STOP_FILE.unlink()
        sys.exit(0)

    # Read Claude's input
    try:
        hook_input = json.loads(sys.stdin.read())
        # stop_hook_active is a real Claude Code flag - step aside to prevent infinite loop
        if hook_input.get("stop_hook_active", False):
            sys.exit(0)
    except Exception:
        pass

    # Check for unprocessed files in Needs_Action/
    if not NEEDS_ACTION.exists():
        sys.exit(0)

    pending = [f for f in NEEDS_ACTION.glob("*.md") if f.is_file()]

    if pending:
        file_list = "\n".join(f"  - {f.name}" for f in pending[:5])
        print(json.dumps({
            "decision": "block",
            "reason": (
                f"There are still {len(pending)} unprocessed file(s) in Needs_Action/:\n"
                f"{file_list}\n\n"
                f"Process each file using /process-tasks skill, "
                f"move completed tasks to Done/. "
                f"Do not stop until Needs_Action/ is empty."
            )
        }))

    sys.exit(0)


if __name__ == "__main__":
    main()
