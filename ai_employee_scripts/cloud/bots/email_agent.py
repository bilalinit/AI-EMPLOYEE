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

IMPORTANT: You have tools available (get_task_content, get_original_file, read_context_file) but you should ONLY use them to READ information.
DO NOT try to call save_draft, complete_task, or any other save/write tools.
Just read the information and output your email draft.

YOUR PROCESS:
1. Read the task content using get_task_content()
2. Read the original email using get_original_file() if needed
3. Draft your email response internally (don't call any tools for drafting)
4. Output your final email as plain text

EMAIL WRITING RULES:
- Match the tone: formal for business, casual for known contacts
- Keep responses concise and actionable
- Include a clear call-to-action when needed
- Be helpful but professional
- Do NOT include credentials or sensitive data

OUTPUT FORMAT (just output this, no tools):
---
**Subject:** [your subject line]

**Body:**
[your email content here]
---
"""


# ============================================================================
# CREATE EMAIL AGENT
# ============================================================================

def create_email_agent(model=None) -> Agent:
    """
    Create the email agent for drafting email responses.

    This implements Part A: Core Basics from the OpenAI Agents SDK.

    Note: GLM API doesn't support structured output well, so we parse manually.
    The orchestrator will save the draft, so the agent only outputs content.

    Args:
        model: The model to use (default: None, will be set by orchestrator)

    Returns:
        Agent: Configured email agent (no structured output for GLM compatibility)
    """
    return create_base_agent(
        name="EmailAgent",
        instructions=EMAIL_INSTRUCTIONS,
        tools=get_common_tools(),  # Use basic tools without save_draft
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
