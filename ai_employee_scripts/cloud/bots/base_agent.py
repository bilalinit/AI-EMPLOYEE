"""
Base Agent Configuration

Shared configuration and utilities for all cloud agents.
Part A: Core Basics - Agent Creation
"""

from agents import Agent
from cloud.bots.models import TriageDecision
from cloud.tools.file_tools import (
    get_task_content,
    get_original_file,
    save_draft,
    claim_task,
    complete_task,
    read_context_file
)
from cloud.tools.git_tools import (
    sync_to_git,
    pull_from_git,
    check_git_status
)
from cloud.guardrails.input_guardrails import input_safety_check
from cloud.guardrails.output_guardrails import output_safety_check


# ============================================================================
# SHARED INSTRUCTIONS
# ============================================================================

SHARED_CONTEXT = """
You are part of a Personal AI Employee system. Your role is to help manage business operations.

IMPORTANT CONTEXT:
- Business Type: AI Automation (Digital FTEs, Custom Agents) + Animation/Visual Content (3D Reels, 2D VFX)
- Target Audience: Businesses needing AI automation + Content creators needing animation
- Brand Voice: Professional but approachable, tech-savvy but not overly technical
- You are the CLOUD agent - you draft responses for human approval
- Local agent handles execution with credentials

SAFETY RULES:
- NEVER include credentials, passwords, or API keys in your outputs
- NEVER execute actions - only draft for human approval
- Always set needs_approval=True for any external communication
- Match the brand voice from Business_Goals.md

WORKFLOW:
1. Read the task content using get_task_content()
2. Read the original file using get_original_file() if needed
3. Read relevant context using read_context_file()
4. Process according to your specialty
5. Save your draft using save_draft()
6. Mark task complete using complete_task()
7. Sync to git using sync_to_git()
"""


# ============================================================================
# BASE AGENT CREATOR
# ============================================================================

def create_base_agent(
    name: str,
    instructions: str,
    tools: list = None,
    model=None,
    output_type=None,
    with_guardrails: bool = True
) -> Agent:
    """
    Create a base agent with shared configuration.

    Args:
        name: Agent name
        instructions: Agent-specific instructions
        tools: List of function tools
        model: Model to use
        output_type: Structured output type (optional)
        with_guardrails: Whether to attach input/output guardrails (default: True)

    Returns:
        Agent: Configured agent
    """
    full_instructions = f"{SHARED_CONTEXT}\n\nYOUR SPECIFIC ROLE:\n{instructions}"

    # Build agent configuration
    agent_config = {
        "name": name,
        "instructions": full_instructions,
        "tools": tools or [],
        "model": model,
        "output_type": output_type
    }

    # Attach guardrails if requested (SDK Pattern)
    if with_guardrails:
        agent_config["input_guardrails"] = [input_safety_check]
        agent_config["output_guardrails"] = [output_safety_check]

    return Agent(**agent_config)


# ============================================================================
# COMMON TOOLS SET
# ============================================================================

def get_common_tools() -> list:
    """
    Get the set of tools common to all agents.

    Returns:
        list: Common function tools
    """
    return [
        get_task_content,
        get_original_file,
        read_context_file,
    ]


def get_common_tools_with_save() -> list:
    """
    Get tools including save_draft and complete_task for agents that need them.

    Returns:
        list: Common function tools plus save/complete tools
    """
    return [
        get_task_content,
        get_original_file,
        save_draft,
        claim_task,
        complete_task,
        read_context_file,
        sync_to_git,
        pull_from_git,
        check_git_status,
    ]

