"""
Social Agent

Drafts social media content for LinkedIn, Twitter, Facebook, Instagram.
Part A: Core Basics - Agent with Tools
"""

from agents import Agent
from cloud.bots.models import SocialPost, SocialPlatform, Priority
from cloud.bots.base_agent import create_base_agent, get_common_tools


# ============================================================================
# SOCIAL AGENT INSTRUCTIONS
# ============================================================================

SOCIAL_INSTRUCTIONS = """
You are the Social Media Agent. Your job is to draft engaging social media content.

BUSINESS CONTEXT:
- Industries: AI Automation (Digital FTEs, Custom Agents) + Animation/Visual Content
- Topics: AI agents, Digital FTEs, 3D animation, future of work, automation
- Brand Voice: Professional but approachable, tech-savvy but not overly technical
- Call-to-Action: Encourage comments and engagement

PLATFORM-SPECIFIC GUIDELINES:

LINKEDIN:
- Professional tone
- 3-5 paragraphs max
- Include relevant hashtags (e.g., #AI #Automation #DigitalFTE)
- Focus on business value and insights
- Ask questions to encourage engagement

TWITTER:
- Concise (under 280 characters normally)
- One main point per tweet
- Use 2-3 relevant hashtags
- Can be more casual but still professional
- Thread format for longer content

FACEBOOK:
- Friendly and conversational
- Can be longer than Twitter
- Include hashtags
- Good for behind-the-scenes content

INSTAGRAM:
- Visual-first (caption should mention visual content)
- Short, engaging caption
- Use emojis appropriately
- Include relevant hashtags
- Image URL required for posts

CONTENT IDEAS:
- AI agents replacing traditional employees
- Digital FTEs and the future of work
- Building AI-powered automation
- 3D animation tips and trends
- Behind-the-scenes of AI/animation work
- Workflow efficiency through AI

YOUR PROCESS:
1. Use get_task_content() to read the task
2. Use read_context_file("Business_Goals", "") to understand the business
3. Draft content appropriate for the platform
4. Use save_draft() with appropriate draft_type
5. Complete and sync

ALWAYS:
- Set needs_approval=True (all social posts require approval)
- Match brand voice
- Include engagement call-to-action
- Keep platform-specific constraints in mind
"""


# ============================================================================
# CREATE SOCIAL AGENT
# ============================================================================

def create_social_agent(model=None) -> Agent:
    """
    Create the social media agent for drafting posts.

    This implements Part A: Core Basics from the OpenAI Agents SDK.

    Note: GLM API doesn't support structured output well, so we parse manually.

    Args:
        model: The model to use (default: None, will be set by orchestrator)

    Returns:
        Agent: Configured social agent (no structured output for GLM compatibility)
    """
    return create_base_agent(
        name="SocialAgent",
        instructions=SOCIAL_INSTRUCTIONS,
        tools=get_common_tools(),
        model=model,
        output_type=None  # No structured output for GLM
    )


# ============================================================================
# SOCIAL POST TEMPLATE GENERATOR
# ============================================================================

def create_social_post_template(
    platform: SocialPlatform,
    content: str,
    hashtags: list = None,
    image_url: str = None
) -> str:
    """
    Create a formatted social media post draft.

    Args:
        platform: Target platform
        content: Post content
        hashtags: List of hashtags
        image_url: Image URL for Instagram

    Returns:
        str: Formatted social post draft
    """
    hashtag_str = " ".join(hashtags) if hashtags else ""

    draft = f"""---
type: social_post
platform: {platform.value}
"""

    if image_url:
        draft += f"image_url: {image_url}\n"

    draft += f"""
---

**Platform:** {platform.value}

{content}

{hashtag_str}

---
*Drafted by AI Employee Cloud Agent*
*Awaiting human approval before posting*
"""

    return draft


# ============================================================================
# PLATFORM-SPECIFIC HELPERS
# ============================================================================

def truncate_for_twitter(content: str, max_length: int = 280) -> str:
    """
    Truncate content for Twitter character limit.

    Args:
        content: Content to truncate
        max_length: Maximum character length

    Returns:
        str: Truncated content with ellipsis if needed
    """
    if len(content) <= max_length:
        return content

    # Truncate and add ellipsis
    return content[:max_length - 3] + "..."


def generate_linkedin_hashtags(topic: str) -> list:
    """
    Generate relevant LinkedIn hashtags based on topic.

    Args:
        topic: Content topic

    Returns:
        list: Relevant hashtags
    """
    topic_lower = topic.lower()

    hashtag_map = {
        'ai': ['#AI', '#ArtificialIntelligence', '#MachineLearning', '#Automation'],
        'automation': ['#Automation', '#DigitalFTE', '#FutureOfWork', '#Productivity'],
        'agent': ['#AIAgents', '#DigitalEmployees', '#BusinessAutomation'],
        'animation': ['#3DAnimation', '#VFX', '#MotionGraphics', '#Animation'],
        'freelance': ['#Freelance', '#BusinessOwner', '#Entrepreneur'],
    }

    hashtags = ['#AI', '#Automation']  # Default

    for keyword, tags in hashtag_map.items():
        if keyword in topic_lower:
            hashtags.extend(tags)

    return list(set(hashtags))[:5]  # Max 5 hashtags


def generate_twitter_engagement() -> str:
    """
    Generate a Twitter engagement prompt.

    Returns:
        str: Engagement question
    """
    options = [
        "What's your take?",
        "Agree or disagree?",
        "Thoughts?",
        "Let me know below!",
        "Would love to hear your thoughts!",
    ]

    return options[hash(str(options)) % len(options)]  # Simple hash for variety
