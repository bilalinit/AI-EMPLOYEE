"""
File Tools for Cloud Agents

Function tools that allow agents to read and write files in the vault.
Part A: Core Basics - Function Tools
"""

from pathlib import Path
from datetime import datetime
import aiofiles
import asyncio
from typing import Optional

from cloud.config import get_vault_folders


# ============================================================================
# VAULT FILE OPERATIONS
# ============================================================================

async def read_task(task_filename: str) -> str:
    """
    Read a task file from Needs_Action folder.

    Args:
        task_filename: Name of the task file (e.g., TASK_123.md)

    Returns:
        str: Content of the task file

    Raises:
        FileNotFoundError: If task file doesn't exist
    """
    folders = get_vault_folders()
    task_path = folders["needs_action"] / task_filename

    if not task_path.exists():
        raise FileNotFoundError(f"Task file not found: {task_filename}")

    async with aiofiles.open(task_path, mode="r") as f:
        content = await f.read()

    return content


async def read_inbox_file(filename: str) -> str:
    """
    Read an original file from Inbox folder.

    Args:
        filename: Name of the file in Inbox

    Returns:
        str: Content of the file

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    folders = get_vault_folders()
    file_path = folders["inbox"] / filename

    if not file_path.exists():
        raise FileNotFoundError(f"Inbox file not found: {filename}")

    async with aiofiles.open(file_path, mode="r") as f:
        content = await f.read()

    return content


async def write_draft(
    content: str,
    original_task: str,
    draft_type: str = "draft"
) -> str:
    """
    Write a draft to the Updates folder for local processing.

    Args:
        content: The draft content to write
        original_task: Original task filename for reference
        draft_type: Type of draft (email, social, finance, etc.)

    Returns:
        str: Path to the created draft file
    """
    folders = get_vault_folders()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create filename
    filename = f"{draft_type.upper()}_DRAFT_{timestamp}.md"
    draft_path = folders["updates"] / filename

    # Ensure Updates folder exists
    folders["updates"].mkdir(parents=True, exist_ok=True)

    # Create frontmatter and content
    frontmatter = f"""---
type: draft
source: cloud_agent
created: {datetime.now().isoformat()}
original_task: {original_task}
draft_type: {draft_type}
status: pending_review
---

"""

    async with aiofiles.open(draft_path, mode="w") as f:
        await f.write(frontmatter + content)

    return str(draft_path)


async def move_to_in_progress(task_filename: str, agent: str = "cloud") -> str:
    """
    Move a task from Needs_Action to In_Progress for locking.

    Args:
        task_filename: Name of the task file
        agent: Which agent is claiming it (cloud or local)

    Returns:
        str: New path of the moved file

    Raises:
        FileNotFoundError: If task doesn't exist
    """
    folders = get_vault_folders()

    # Determine source and destination
    source = folders["needs_action"] / task_filename

    if agent == "cloud":
        dest_folder = folders["in_progress_cloud"]
    else:
        dest_folder = folders["base"] / "In_Progress" / agent

    # Ensure destination exists
    dest_folder.mkdir(parents=True, exist_ok=True)

    if not source.exists():
        raise FileNotFoundError(f"Task not found: {task_filename}")

    destination = dest_folder / task_filename

    # Read original content
    async with aiofiles.open(source, mode="r") as f:
        content = await f.read()

    # Write to destination
    async with aiofiles.open(destination, mode="w") as f:
        await f.write(content)

    # Remove from source
    source.unlink()

    return str(destination)


async def write_to_done(
    original_task: str,
    summary: str,
    status: str = "completed"
) -> str:
    """
    Write a completion summary to Done folder.

    Args:
        original_task: Original task filename
        summary: Summary of what was done
        status: Status (completed, failed, etc.)

    Returns:
        str: Path to the done file
    """
    folders = get_vault_folders()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Extract base name from original task
    base_name = original_task.replace("TASK_", "").replace(".md", "")
    filename = f"DONE_{base_name}_{timestamp}.md"
    done_path = folders["done"] / filename

    # Create summary content
    content = f"""---
type: task_completion
source: cloud_agent
created: {datetime.now().isoformat()}
original_task: {original_task}
status: {status}
---

# Task Completion Summary

**Original Task:** {original_task}
**Status:** {status}
**Completed:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Summary

{summary}
"""

    async with aiofiles.open(done_path, mode="w") as f:
        await f.write(content)

    return str(done_path)


async def read_vault_file(
    folder_name: str,
    filename: str
) -> str:
    """
    Read a file from any vault folder.

    Args:
        folder_name: Name of the folder (e.g., "Handbook", "Business_Goals")
        filename: Name of the file (can include subdirectories)

    Returns:
        str: File content

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    folders = get_vault_folders()
    base = folders["base"]

    # Handle special cases
    if folder_name == "Handbook":
        file_path = base / "Company_Handbook.md"
    elif folder_name == "Business_Goals":
        file_path = base / "Business_Goals.md"
    elif folder_name == "Accounting":
        file_path = folders["accounting"] / filename
    else:
        file_path = base / folder_name / filename

    if not file_path.exists():
        raise FileNotFoundError(f"Vault file not found: {file_path}")

    async with aiofiles.open(file_path, mode="r") as f:
        content = await f.read()

    return content


# ============================================================================
# FUNCTION TOOL WRAPPERS FOR AGENTS
# ============================================================================

from agents import function_tool


@function_tool
async def get_task_content(task_filename: str) -> str:
    """Get the content of a task file from Needs_Action.

    Args:
        task_filename: The filename of the task (e.g., TASK_123.md)

    Returns:
        The full content of the task file
    """
    return await read_task(task_filename)


@function_tool
async def get_original_file(filename: str) -> str:
    """Get the original file content from Inbox folder.

    Args:
        filename: The name of the file in Inbox

    Returns:
        The full content of the original file
    """
    return await read_inbox_file(filename)


@function_tool
async def save_draft(
    content: str,
    original_task: str,
    draft_type: str
) -> str:
    """Save a generated draft to Updates folder for human review.

    Args:
        content: The draft content to save
        original_task: The original task filename
        draft_type: Type of draft (email, social, finance, etc.)

    Returns:
        Path to the created draft file
    """
    return await write_draft(content, original_task, draft_type)


@function_tool
async def claim_task(task_filename: str) -> str:
    """Claim a task by moving it to In_Progress (prevents double-processing).

    Args:
        task_filename: The task filename to claim

    Returns:
        New path of the claimed task
    """
    return await move_to_in_progress(task_filename, agent="cloud")


@function_tool
async def complete_task(original_task: str, summary: str) -> str:
    """Mark a task as completed by writing summary to Done folder.

    Args:
        original_task: The original task filename
        summary: Summary of what was accomplished

    Returns:
        Path to the completion summary file
    """
    return await write_to_done(original_task, summary)


@function_tool
async def read_context_file(folder: str, filename: str) -> str:
    """Read context files like Company Handbook, Business Goals, etc.

    Args:
        folder: The folder name (e.g., "Handbook", "Business_Goals", "Accounting")
        filename: The filename (use "" for single-file folders)

    Returns:
        The file content
    """
    if not filename:
        filename = ""
    return await read_vault_file(folder, filename)
