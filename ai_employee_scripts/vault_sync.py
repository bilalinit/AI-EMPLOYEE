#!/usr/bin/env python3
"""
Vault Sync Script - Platinum Tier

Automatically sync AI_Employee_Vault between local and cloud via Git.

This script runs on BOTH local and cloud machines:
- Local (WSL): Syncs your changes to GitHub
- Cloud (VM): Syncs cloud agent changes to GitHub

Both sides pull → make changes → push, with GitHub as the middleman.

Usage:
    python vault_sync.py              # Run once (default for cron)
    python vault_sync.py --daemon     # Run continuously
    python vault_sync.py --dry-run    # Test without making changes
    python vault_sync.py --status     # Check git status only

Cron setup (every 5 minutes):
    */5 * * * * cd /path/to/ai_employee_scripts && uv run python vault_sync.py
"""

import subprocess
import time
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================

# Detect if we're on local or cloud by checking paths
SCRIPT_PATH = Path(__file__).resolve()
# Project root is one level up from scripts folder
PROJECT_ROOT = SCRIPT_PATH.parent.parent

# Vault path (works for both local and cloud)
VAULT_PATH = PROJECT_ROOT / "AI_Employee_Vault"

# Log file
LOG_FILE = VAULT_PATH / "Logs" / "vault_sync.log"

# Sync settings
SYNC_INTERVAL = 300  # 5 minutes
GIT_REMOTE = "origin"
GIT_BRANCH = "platinum-tier"  # Your current branch

# Commit message templates
COMMIT_MESSAGE_LOCAL = "[Local] Vault sync {timestamp}"
COMMIT_MESSAGE_CLOUD = "[Cloud Agent] Vault sync {timestamp}"


# =============================================================================
# LOGGING SETUP
# =============================================================================

def setup_logging():
    """Setup logging to both file and console."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger("vault_sync")
    logger.setLevel(logging.INFO)

    # Clear existing handlers
    logger.handlers = []

    # File handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Initialize logger
logger = setup_logging()


# =============================================================================
# GIT FUNCTIONS
# =============================================================================

def git_cmd(cmd, cwd=None, dry_run=False):
    """Run git command."""
    try:
        if dry_run:
            logger.info(f"[DRY-RUN] Would run: git {' '.join(cmd)}")
            return 0, "", ""

        result = subprocess.run(
            ["git"] + cmd,
            cwd=cwd or PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        logger.error("Git command timeout")
        return -1, "", "Command timeout"
    except Exception as e:
        logger.error(f"Git command error: {e}")
        return -1, "", str(e)


def detect_environment():
    """Detect if running on local or cloud."""
    # Check for cloud indicators
    is_cloud = (
        "/home/ubuntu/" in str(PROJECT_ROOT) or
        "/home/ec2-user/" in str(PROJECT_ROOT) or
        Path("/home/ubuntu").exists()
    )
    return "cloud" if is_cloud else "local"


def has_changes():
    """Check if there are uncommitted changes."""
    code, stdout, stderr = git_cmd(["status", "--porcelain"])
    if code != 0:
        logger.error(f"Git status failed: {stderr}")
        return False
    return stdout.strip() != ""


def get_changed_files():
    """Get list of changed files."""
    code, stdout, stderr = git_cmd(["status", "--porcelain"])
    if code != 0:
        return []

    files = []
    for line in stdout.strip().split("\n"):
        if line:
            # Parse git status output: XY filename
            status = line[:2]
            filepath = line[3:]
            files.append((status, filepath))

    return files


def fetch():
    """Fetch changes from remote."""
    logger.info("Fetching from remote...")
    code, stdout, stderr = git_cmd(["fetch", GIT_REMOTE])

    if code != 0:
        logger.error(f"Fetch failed: {stderr}")
        return False

    logger.info(f"Fetch successful")
    return True


def pull(rebase=False):
    """Pull changes from remote."""
    env = detect_environment()

    if rebase:
        logger.info(f"Pulling with rebase ({GIT_BRANCH})...")
        # Use pull --rebase for cleaner history
        code, stdout, stderr = git_cmd([
            "pull",
            "--rebase",
            GIT_REMOTE,
            GIT_BRANCH
        ])
    else:
        logger.info(f"Pulling ({GIT_BRANCH})...")
        code, stdout, stderr = git_cmd([
            "pull",
            GIT_REMOTE,
            GIT_BRANCH
        ])

    if code != 0:
        logger.error(f"Pull failed: {stderr}")

        # Try to recover from merge conflict
        if "CONFLICT" in stderr or "Merge conflict" in stderr:
            logger.warning("Merge conflict detected, aborting...")
            git_cmd(["merge", "--abort"])
            git_cmd(["rebase", "--abort"])

        return False

    logger.info(f"Pull successful")
    if stdout:
        logger.debug(f"Pull output: {stdout}")
    return True


def add_changes(files=None):
    """Stage changes for commit."""
    if files:
        # Add specific files
        for filepath in files:
            logger.debug(f"Adding: {filepath}")
            git_cmd(["add", filepath])
    else:
        # Add all changes
        logger.info("Staging all changes...")
        git_cmd(["add", "-A"])


def commit_changes(dry_run=False):
    """Commit staged changes."""
    env = detect_environment()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Choose commit message based on environment
    if env == "cloud":
        message = COMMIT_MESSAGE_CLOUD.format(timestamp=timestamp)
    else:
        message = COMMIT_MESSAGE_LOCAL.format(timestamp=timestamp)

    logger.info(f"Committing: {message}")

    if dry_run:
        return True

    code, stdout, stderr = git_cmd(["commit", "-m", message])

    if code != 0:
        # Check if nothing to commit
        if "nothing to commit" in stdout or "no changes added" in stdout:
            logger.debug("Nothing to commit")
            return True

        logger.error(f"Commit failed: {stderr}")
        return False

    logger.info(f"Commit successful")
    return True


def push(dry_run=False):
    """Push changes to remote."""
    logger.info(f"Pushing to {GIT_REMOTE}/{GIT_BRANCH}...")

    if dry_run:
        logger.info(f"[DRY-RUN] Would push to {GIT_REMOTE}/{GIT_BRANCH}")
        return True

    code, stdout, stderr = git_cmd(["push", GIT_REMOTE, GIT_BRANCH])

    if code != 0:
        # Check if push was rejected (remote has new changes)
        if "rejected" in stderr.lower() or "non-fast-forward" in stderr.lower():
            logger.warning("Push rejected - remote has new changes")
            return False

        logger.error(f"Push failed: {stderr}")
        return False

    logger.info(f"Push successful")
    return True


def get_status():
    """Get current git status."""
    code, stdout, stderr = git_cmd(["status", "-sb"])
    return stdout


def check_git_repo():
    """Verify we're in a git repository."""
    git_dir = PROJECT_ROOT / ".git"
    if not git_dir.exists():
        logger.error(f"Not a git repository: {PROJECT_ROOT}")
        logger.error("Initialize git first:")
        logger.error(f"  cd {PROJECT_ROOT}")
        logger.error("  git init")
        logger.error(f"  git remote add origin <your-repo-url>")
        return False
    return True


# =============================================================================
# SYNC OPERATIONS
# =============================================================================

def sync(dry_run=False, rebase=False):
    """
    Perform one sync cycle.

    Pattern: PULL → Check changes → PUSH if needed

    1. Pull latest from remote (get other side's changes)
    2. Check if we have local changes
    3. If yes: commit and push

    Returns:
        bool: True if sync successful, False otherwise
    """
    env = detect_environment()
    logger.info(f"Starting sync cycle ({env})")
    logger.info(f"Vault: {VAULT_PATH}")
    logger.info(f"Branch: {GIT_BRANCH}")

    if not check_git_repo():
        return False

    try:
        # Step 1: Fetch first (check if there are remote changes)
        if not fetch():
            return False

        # Step 2: Pull changes (get updates from other side)
        if not pull(rebase=rebase):
            logger.warning("Pull failed, will retry next cycle")
            # Continue anyway - we might still have local changes to push

        # Step 3: Check for local changes
        if has_changes():
            files = get_changed_files()
            logger.info(f"Found {len(files)} changed file(s)")

            # Log what changed
            for status, filepath in files[:10]:  # First 10 files
                logger.debug(f"  {status} {filepath}")
            if len(files) > 10:
                logger.debug(f"  ... and {len(files) - 10} more")

            # Step 4: Commit changes
            if not commit_changes(dry_run=dry_run):
                logger.error("Commit failed, skipping push")
                return False

            # Step 5: Push changes
            if not push(dry_run=dry_run):
                logger.warning("Push failed - will retry next cycle")
                return False
        else:
            logger.info("No local changes to push")

        logger.info(f"Sync cycle complete ({env})")
        return True

    except Exception as e:
        logger.error(f"Sync error: {e}")
        return False


def run_daemon(dry_run=False, rebase=False):
    """Run sync continuously in daemon mode."""
    env = detect_environment()
    logger.info("=" * 60)
    logger.info(f"Vault Sync Daemon Starting ({env})")
    logger.info("=" * 60)
    logger.info(f"Sync interval: {SYNC_INTERVAL}s ({SYNC_INTERVAL // 60} minutes)")
    logger.info(f"Vault path: {VAULT_PATH}")
    logger.info(f"Branch: {GIT_BRANCH}")
    logger.info(f"Remote: {GIT_REMOTE}")
    logger.info(f"Press Ctrl+C to stop")
    logger.info("=" * 60)
    logger.info("")

    while True:
        try:
            sync(dry_run=dry_run, rebase=rebase)
            logger.info(f"Waiting {SYNC_INTERVAL}s until next sync...")
            logger.info("")
            time.sleep(SYNC_INTERVAL)
        except KeyboardInterrupt:
            logger.info("")
            logger.info("=" * 60)
            logger.info("Daemon stopped by user")
            logger.info("=" * 60)
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            logger.info(f"Retrying in {SYNC_INTERVAL}s...")
            time.sleep(SYNC_INTERVAL)


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Sync AI_Employee_Vault via git",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run once (for cron)
  python vault_sync.py

  # Run continuously
  python vault_sync.py --daemon

  # Test without making changes
  python vault_sync.py --dry-run

  # Use rebase for cleaner history
  python vault_sync.py --rebase

Cron setup (every 5 minutes):
  */5 * * * * cd /path/to/ai_employee_scripts && uv run python vault_sync.py
        """
    )

    parser.add_argument(
        "--daemon", "-d",
        action="store_true",
        help="Run continuously as daemon"
    )
    parser.add_argument(
        "--once", "-o",
        action="store_true",
        help="Run once and exit (default behavior)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test without making actual changes"
    )
    parser.add_argument(
        "--rebase", "-r",
        action="store_true",
        help="Use pull --rebase for cleaner history"
    )
    parser.add_argument(
        "--status", "-s",
        action="store_true",
        help="Show git status and exit"
    )

    args = parser.parse_args()

    # Check vault exists
    if not VAULT_PATH.exists():
        logger.error(f"ERROR: Vault not found at {VAULT_PATH}")
        sys.exit(1)

    # Handle --status
    if args.status:
        if not check_git_repo():
            sys.exit(1)

        print("\n" + "=" * 60)
        print("GIT STATUS")
        print("=" * 60)
        print(get_status())
        print("=" * 60)

        if has_changes():
            files = get_changed_files()
            print(f"\nChanged files: {len(files)}")
            for status, filepath in files:
                print(f"  {status} {filepath}")
        else:
            print("\nNo local changes")

        print("\nEnvironment:", detect_environment().upper())
        print("Branch:", GIT_BRANCH)
        print("=" * 60)
        sys.exit(0)

    # Run sync
    if args.daemon:
        run_daemon(dry_run=args.dry_run, rebase=args.rebase)
    else:
        # Run once (default for cron)
        success = sync(dry_run=args.dry_run, rebase=args.rebase)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
