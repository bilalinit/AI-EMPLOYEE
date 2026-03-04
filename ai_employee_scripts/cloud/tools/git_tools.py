"""
Git Tools for Cloud Agents

Function tools for git operations (sync with local).
Part A: Core Basics - Function Tools
"""

import subprocess
import asyncio
from pathlib import Path
from typing import Optional
from datetime import datetime

from cloud.config import get_vault_folders, VAULT_PATH


# ============================================================================
# GIT OPERATIONS
# ============================================================================

async def git_status() -> dict:
    """
    Get git status of the vault.

    Returns:
        dict: Git status information
    """
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(VAULT_PATH),
        capture_output=True,
        text=True
    )

    lines = result.stdout.strip().split("\n") if result.stdout.strip() else []

    return {
        "has_changes": len(lines) > 0,
        "changed_files": [line.split()[-1] for line in lines if line],
        "raw_output": result.stdout
    }


async def git_add(file_path: str) -> bool:
    """
    Add a file to git staging.

    Args:
        file_path: Path to file relative to vault root

    Returns:
        bool: True if successful
    """
    result = subprocess.run(
        ["git", "add", file_path],
        cwd=str(VAULT_PATH),
        capture_output=True,
        text=True
    )

    return result.returncode == 0


async def git_commit(message: str) -> bool:
    """
    Commit staged changes.

    Args:
        message: Commit message

    Returns:
        bool: True if successful
    """
    # Format message with timestamp
    full_message = f"[Cloud Agent] {message} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    result = subprocess.run(
        ["git", "commit", "-m", full_message],
        cwd=str(VAULT_PATH),
        capture_output=True,
        text=True
    )

    return result.returncode == 0


async def git_push(remote: str = "origin", branch: str = "platinum-tier") -> bool:
    """
    Push commits to remote.

    Args:
        remote: Git remote name
        branch: Branch name

    Returns:
        bool: True if successful
    """
    result = subprocess.run(
        ["git", "push", remote, branch],
        cwd=str(VAULT_PATH),
        capture_output=True,
        text=True,
        timeout=60  # 60 second timeout
    )

    return result.returncode == 0


async def git_pull(remote: str = "origin", branch: str = "platinum-tier") -> dict:
    """
    Pull changes from remote.

    Args:
        remote: Git remote name
        branch: Branch name

    Returns:
        dict: Pull result with status and info
    """
    result = subprocess.run(
        ["git", "pull", remote, branch],
        cwd=str(VAULT_PATH),
        capture_output=True,
        text=True,
        timeout=60
    )

    return {
        "success": result.returncode == 0,
        "output": result.stdout,
        "error": result.stderr
    }


async def git_sync_commit(message: str) -> bool:
    """
    Add, commit, and push in one operation.

    Args:
        message: Commit message

    Returns:
        bool: True if all operations succeeded
    """
    # Stage all changes
    subprocess.run(
        ["git", "add", "-A"],
        cwd=str(VAULT_PATH),
        capture_output=True
    )

    # Commit
    commit_result = await git_commit(message)
    if not commit_result:
        return False

    # Push
    push_result = await git_push()
    return push_result


# ============================================================================
# FUNCTION TOOL WRAPPERS FOR AGENTS
# ============================================================================

from agents import function_tool


@function_tool
async def sync_to_git(message: str) -> str:
    """Commit and push changes to git for local to receive.

    Args:
        message: Description of what was changed

    Returns:
        Status message indicating success or failure
    """
    success = await git_sync_commit(message)

    if success:
        return f"✅ Synced to git: {message}"
    else:
        return f"❌ Failed to sync to git: {message}"


@function_tool
async def pull_from_git() -> str:
    """Pull latest changes from remote (get updates from local).

    Returns:
        Status message with pull results
    """
    result = await git_pull()

    if result["success"]:
        return f"✅ Pulled from git successfully"
    else:
        return f"❌ Failed to pull from git: {result.get('error', 'Unknown error')}"


@function_tool
async def check_git_status() -> str:
    """Check if there are uncommitted changes.

    Returns:
        Status message with current git state
    """
    status = await git_status()

    if status["has_changes"]:
        files = ", ".join(status["changed_files"][:5])
        more = f" and {len(status['changed_files']) - 5} more" if len(status["changed_files"]) > 5 else ""
        return f"📝 Uncommitted changes: {files}{more}"
    else:
        return "✅ Working directory clean"
