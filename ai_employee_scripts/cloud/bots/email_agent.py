"""
Email Agent

Drafts email replies and handles email-related tasks.
Part A: Core Basics - Agent with Tools
"""

from agents import Agent
from cloud.bots.models import EmailDraft, Priority
from cloud.bots.base_agent import create_base_agent, get_common_tools


# ============================================================================
# EMAIL AGENT INSTRUCTIONS
# ============================================================================

EMAIL_INSTRUCTIONS = """
You are the Email Agent. Your job is to draft professional email responses.

YOUR PROCESS:
1. Use get_task_content() to read the task
2. Use get_original_file() to read the original email
3. Use read_context_file("Handbook", "") to read Company_Handbook.md for approval rules
4. Analyze the email and determine appropriate response

EMAIL WRITING RULES:
- Match the tone: formal for business, casual for known contacts
- Keep responses concise and actionable
- Include a clear call-to-action when needed
- Be helpful but professional
- Do NOT include credentials or sensitive data

ASSESSMENT:
- Set confidence based on how well you understand the context
- Set needs_approval=True for all emails (safety rule)
- Set priority: CRITICAL for urgent/lost business, HIGH for clients, MEDIUM for standard
- Provide reasoning for your response strategy

DRAFT FORMAT:
Use the save_draft() tool with draft_type="email"
Include proper frontmatter and email formatting.

When done:
1. Save the draft using save_draft()
2. Complete the task using complete_task()
3. Sync to git using sync_to_git()
"""


# ============================================================================
# CREATE EMAIL AGENT
# ============================================================================

def create_email_agent(model=None) -> Agent:
    """
    Create the email agent for drafting email responses.

    This implements Part A: Core Basics from the OpenAI Agents SDK.

    Note: GLM API doesn't support structured output well, so we parse manually.

    Args:
        model: The model to use (default: None, will be set by orchestrator)

    Returns:
        Agent: Configured email agent (no structured output for GLM compatibility)
    """
    return create_base_agent(
        name="EmailAgent",
        instructions=EMAIL_INSTRUCTIONS,
        tools=get_common_tools(),
        model=model,
        output_type=None  # No structured output for GLM
    )


# ============================================================================
# EMAIL DRAFT TEMPLATE GENERATOR
# ============================================================================

def create_email_draft_template(
    to: str,
    subject: str,
    body: str,
    in_reply_to: str = None
) -> str:
    """
    Create a formatted email draft.

    Args:
        to: Recipient email
        subject: Email subject
        body: Email body
        in_reply_to: Original message being replied to

    Returns:
        str: Formatted email draft
    """
    draft = f"""---
type: email_draft
to: {to}
subject: {subject}
"""

    if in_reply_to:
        draft += f"in_reply_to: {in_reply_to}\n"

    draft += f"""
---

**To:** {to}
**Subject:** {subject}

{body}

---
*Drafted by AI Employee Cloud Agent*
*Awaiting human approval before sending*
"""

    return draft
