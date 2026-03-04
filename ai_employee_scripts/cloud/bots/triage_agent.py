"""
Triage Agent

Routes incoming tasks to specialized agents.
Part B: Advanced Workflows - Multi-Agent Handoffs
"""

from agents import Agent
from cloud.bots.models import TriageDecision, Category, Priority
from cloud.bots.base_agent import create_base_agent, get_common_tools


# ============================================================================
# TRIAGE INSTRUCTIONS
# ============================================================================

TRIAGE_INSTRUCTIONS = """
You are the Triage Agent. Your job is to analyze incoming tasks and route them to the right specialist.

CATEGORIZE tasks into:
- EMAIL: Email replies, email drafts, email responses
- SOCIAL: Social media posts, replies, content for LinkedIn/Twitter/Facebook/Instagram
- FINANCE: Invoices, payments, expenses, accounting tasks
- PERSONAL: Personal correspondence, non-business tasks
- UNKNOWN: Cannot determine category

ASSESS PRIORITY:
- CRITICAL: Payment failures, urgent client messages, time-sensitive issues
- HIGH: Invoice requests, meeting prep, important client communications
- MEDIUM: Standard emails, routine business tasks
- LOW: Newsletter, non-urgent updates

ROUTING LOGIC:
- Email tasks → Email Agent
- Social media tasks → Social Agent
- Finance tasks → Finance Agent
- Personal tasks → Mark for Done (no action needed)
- Unknown → Ask for clarification

Set can_auto_complete=true for:
- Personal correspondence that needs no reply
- Automated notifications
- Spam/malicious messages

Set can_auto_complete=false for:
- Anything requiring a draft response
- Business inquiries
- Financial tasks
- Social media interactions
"""


# ============================================================================
# CREATE TRIAGE AGENT
# ============================================================================

def create_triage_agent(model=None) -> Agent:
    """
    Create the triage agent for task routing.

    This implements Part B: Multi-Agent Handoffs from the OpenAI Agents SDK.

    Note: GLM API doesn't support structured output well, so we parse manually.

    Args:
        model: The model to use (default: None, will be set by orchestrator)

    Returns:
        Agent: Configured triage agent (no structured output for GLM compatibility)
    """
    return create_base_agent(
        name="TriageAgent",
        instructions=TRIAGE_INSTRUCTIONS,
        tools=get_common_tools(),
        model=model,
        output_type=None  # No structured output for GLM
    )


# ============================================================================
# TRIAGE WITH HANDOFFS (Alternative Implementation)
# ============================================================================

def create_triage_agent_with_handoffs(
    email_agent: Agent,
    social_agent: Agent,
    finance_agent: Agent,
    model=None
) -> Agent:
    """
    Create a triage agent that can hand off to specialist agents.

    This implements Part B: Multi-Agent Handoffs using agent handoff feature.

    Args:
        email_agent: The Email Agent
        social_agent: The Social Agent
        finance_agent: The Finance Agent
        model: The model to use

    Returns:
        Agent: Triage agent with handoff configuration
    """
    handoff_instructions = """
You are the Triage Agent with handoff capability.

Analyze the task and HAND OFF to the appropriate specialist:
- Email tasks → handoff to EmailAgent
- Social media tasks → handoff to SocialAgent
- Finance tasks → handoff to FinanceAgent

The specialist agent will take over and handle the complete task.
Do NOT try to handle it yourself - use handoffs.
"""

    return Agent(
        name="TriageAgent",
        instructions=handoff_instructions,
        handoffs=[email_agent, social_agent, finance_agent],
        tools=get_common_tools(),
        model=model
    )


# ============================================================================
# SIMPLE TRIAGE FUNCTION (No AI)
# ============================================================================

def simple_triage(task_content: str) -> TriageDecision:
    """
    Simple rule-based triage without running the AI agent.

    Use this for quick categorization when AI is not needed.

    Args:
        task_content: The task content to categorize

    Returns:
        TriageDecision: Categorization decision
    """
    content_lower = task_content.lower()

    # Check for email indicators
    if any(kw in content_lower for kw in ['email', 'reply to', 'respond to', 'from:', 'subject:', 'to:']):
        return TriageDecision(
            category=Category.EMAIL,
            priority=Priority.MEDIUM,
            confidence=0.8,
            needs_specialist=True,
            recommended_agent="email_agent",
            reasoning="Contains email indicators",
            can_auto_complete=False
        )

    # Check for social media indicators
    if any(kw in content_lower for kw in ['linkedin', 'twitter', 'facebook', 'instagram', 'post', 'tweet', 'social']):
        return TriageDecision(
            category=Category.SOCIAL,
            priority=Priority.MEDIUM,
            confidence=0.8,
            needs_specialist=True,
            recommended_agent="social_agent",
            reasoning="Contains social media indicators",
            can_auto_complete=False
        )

    # Check for finance indicators
    if any(kw in content_lower for kw in ['invoice', 'payment', 'expense', 'revenue', 'finance', 'accounting', '$', 'usd']):
        return TriageDecision(
            category=Category.FINANCE,
            priority=Priority.HIGH,
            confidence=0.8,
            needs_specialist=True,
            recommended_agent="finance_agent",
            reasoning="Contains financial indicators",
            can_auto_complete=False
        )

    # Check for personal/casual indicators
    if any(kw in content_lower for kw in ['hi', 'hello', 'thanks', 'personal', 'casual', 'friend']):
        return TriageDecision(
            category=Category.PERSONAL,
            priority=Priority.LOW,
            confidence=0.7,
            needs_specialist=False,
            recommended_agent=None,
            reasoning="Appears to be personal correspondence",
            can_auto_complete=True
        )

    # Default: unknown
    return TriageDecision(
        category=Category.UNKNOWN,
        priority=Priority.MEDIUM,
        confidence=0.3,
        needs_specialist=True,
        recommended_agent=None,
        reasoning="Could not categorize - needs AI review",
        can_auto_complete=False
    )
