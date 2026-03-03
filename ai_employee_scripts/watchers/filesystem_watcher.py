"""
File System Watcher - Monitors a folder for new files

Monitors a "drop folder" for new files and creates action items
in the AI Employee vault's Needs_Action folder.

Usage:
    python filesystem_watcher.py
"""

import shutil
import logging
from pathlib import Path
from typing import List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent
from base_watcher import BaseWatcher


class DropFolderHandler(FileSystemEventHandler):
    """Handles file system events for the drop folder.

    Workflow:
    1. Drop file in Drop_Zone → Watcher detects
    2. Copy to Inbox → File copied (storage)
    3. Create task in Needs_Action → Task file created (for Claude)
    4. Claude processes the task → Manual
    """

    def __init__(self, vault_path: str, drop_folder: str):
        super().__init__()
        self.vault_path = Path(vault_path)
        self.inbox = self.vault_path / "Inbox"
        self.needs_action = self.vault_path / "Needs_Action"
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.needs_action.mkdir(parents=True, exist_ok=True)
        self.drop_folder = Path(drop_folder)
        self.drop_folder.mkdir(parents=True, exist_ok=True)

        # Setup logger
        self.logger = logging.getLogger("DropFolderHandler")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                fmt="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def on_created(self, event):
        """Called when a file or directory is created."""
        if event.is_directory:
            return

        # Skip hidden files and temporary files
        source = Path(event.src_path)
        if source.name.startswith('.') or source.name.startswith('~'):
            return

        # Wait a moment for file to be fully written
        import time
        time.sleep(0.5)

        # Only process if file exists and has content
        if not source.exists() or source.stat().st_size == 0:
            return

        self._process_file(source)

    def _process_file(self, source: Path):
        """Process a dropped file: copy to Inbox, create task in Needs_Action."""
        try:
            import shutil
            from datetime import datetime

            safe_name = self._sanitize_filename(source.name)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Step 1: Copy original file to Inbox
            inbox_dest = self.inbox / f"{timestamp}_{safe_name}"
            shutil.copy2(source, inbox_dest)
            self.logger.info(f"Step 1: Copied to Inbox → {inbox_dest.name}")

            # Step 2: Create task file in Needs_Action
            task_file = self.needs_action / f"TASK_{timestamp}_{safe_name}.md"
            self._create_task_file(source, inbox_dest, task_file)
            self.logger.info(f"Step 2: Created task → {task_file.name}")

            self.logger.info(f"✅ Complete: {source.name}")

        except Exception as e:
            self.logger.error(f"Error processing {source.name}: {e}")

    def _sanitize_filename(self, filename: str) -> str:
        """Remove problematic characters from filename."""
        # Replace spaces and special chars
        return "".join(c if c.isalnum() or c in '._-' else '_' for c in filename)

    def _create_task_file(self, source: Path, inbox_copy: Path, task_file: Path):
        """Create a task file in Needs_Action for Claude to process."""
        from datetime import datetime

        # Calculate human-readable size
        size_bytes = source.stat().st_size
        if size_bytes < 1024:
            size = f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            size = f"{size_bytes / 1024:.1f} KB"
        else:
            size = f"{size_bytes / (1024 * 1024):.1f} MB"

        # Try to read text content for preview
        content_preview = ""
        try:
            if source.suffix in ['.txt', '.md', '.py', '.js', '.json', '.yaml', '.yml']:
                content_preview = source.read_text()[:500]
                if len(source.read_text()) > 500:
                    content_preview += "\n... (truncated)"
        except:
            content_preview = "<Binary or unreadable file>"

        content = f"""---
type: task
source: FilesystemWatcher
created: {datetime.now().isoformat()}
status: pending
priority: medium
original_file: {inbox_copy.name}
---

# Task: Process Dropped File

## File Information
- **Original Name:** {source.name}
- **Size:** {size}
- **Type:** {source.suffix or 'Unknown'}
- **Inbox Copy:** `{inbox_copy.name}`

## What Claude Should Do

1. **Read the file** from `/Inbox/{inbox_copy.name}`
2. **Analyze the content** and determine what action is needed
3. **Create a plan** in `/Plans/` if multi-step action is required
4. **Execute or request approval** based on Company_Handbook.md rules

## File Content Preview
```
{content_preview}
```

## Quick Actions
- [ ] Read full file from Inbox
- [ ] Determine required action
- [ ] Create plan if needed
- [ ] Execute or request approval

---
*This task was automatically created by the File System Watcher*
"""

        task_file.write_text(content)


class FileSystemWatcher(BaseWatcher):
    """
    File System Watcher - monitors a drop folder for new files.

    This is the recommended Bronze Tier watcher as it requires
    no external API setup.
    """

    def __init__(
        self,
        vault_path: str,
        drop_folder: str = None,
        check_interval: int = 60
    ):
        """
        Initialize the filesystem watcher.

        Args:
            vault_path: Path to AI_Employee_Vault
            drop_folder: Path to folder to monitor (default: ../drop_folder)
            check_interval: Not used for watchdog (event-based)
        """
        super().__init__(vault_path, check_interval, name="FileSystemWatcher")

        # Default drop folder is outside the vault (sibling folder)
        if drop_folder is None:
            self.drop_folder = self.vault_path.parent / "drop_folder"
        else:
            self.drop_folder = Path(drop_folder)

        self.drop_folder.mkdir(parents=True, exist_ok=True)

        # Inbox folder for triage
        self.inbox = self.vault_path / "Inbox"
        self.inbox.mkdir(parents=True, exist_ok=True)

    def check_for_updates(self) -> List:
        """Not used for watchdog - events trigger actions."""
        return []

    def create_action_file(self, item) -> Path:
        """Not used for watchdog - handler creates files directly."""
        pass

    def get_item_id(self, item) -> str:
        """Not used for watchdog."""
        pass

    def run(self):
        """Run the watcher using polling (works on WSL/network filesystems)."""
        self.logger.info(f"Starting FileSystemWatcher (polling mode)")
        self.logger.info(f"Drop folder: {self.drop_folder}")
        self.logger.info(f"Vault: {self.vault_path}")
        self.logger.info("")
        self.logger.info("Workflow:")
        self.logger.info("  1. Drop file in Drop_Zone")
        self.logger.info("  2. Copy to /Inbox/")
        self.logger.info("  3. Create task in /Needs_Action/")
        self.logger.info("  4. Claude processes the task")
        self.logger.info("")
        self.logger.info("Press Ctrl+C to stop")
        self.logger.info("=" * 50)
        self.logger.info("DROP FILES HERE:")
        self.logger.info(f"  {self.drop_folder}")
        self.logger.info("=" * 50)

        # Track seen files
        seen_files = set()
        import time

        try:
            while True:
                # Check for new files
                current_files = set()
                for item in self.drop_folder.iterdir():
                    # Skip directories, hidden files, and processed markers
                    if item.is_dir() or item.name.startswith('.'):
                        continue

                    current_files.add(item.name)

                    # If we haven't seen this file, process it
                    if item.name not in seen_files:
                        self.logger.info(f"New file detected: {item.name}")

                        # Create action file
                        handler = DropFolderHandler(str(self.vault_path), str(self.drop_folder))
                        handler._process_file(item)

                        seen_files.add(item.name)

                # Clean up seen_files for files that are gone
                seen_files = seen_files.intersection(current_files)

                time.sleep(2)  # Check every 2 seconds

        except KeyboardInterrupt:
            self.logger.info("FileSystemWatcher stopped by user")


def main():
    """Entry point for running the watcher directly."""
    import sys

    # Default vault path (save-1/AI_Employee_Vault)
    vault_path = Path(__file__).parent.parent.parent / "AI_Employee_Vault"

    # Allow command line override
    if len(sys.argv) > 1:
        vault_path = Path(sys.argv[1])

    if not vault_path.exists():
        print(f"Error: Vault path not found: {vault_path}")
        print("Usage: python filesystem_watcher.py [vault_path]")
        sys.exit(1)

    watcher = FileSystemWatcher(str(vault_path))
    watcher.run()


if __name__ == "__main__":
    main()
