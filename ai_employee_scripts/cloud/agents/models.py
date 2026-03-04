"""
Structured Output Models for Cloud Agents

Pydantic models for type-safe agent outputs using OpenAI Agents SDK.
Part A: Core Basics - Structured Outputs
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class Priority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Category(str, Enum):
    """Task categories for routing."""
    EMAIL = "email"
    SOCIAL = "social"
    FINANCE = "finance"
    PERSONAL = "personal"
    UNKNOWN = "unknown"


# ============================================================================
# EMAIL AGENT MODELS
# ============================================================================

class EmailDraft(BaseModel):
    """Structured output for email draft generation."""

    to: str = Field(description="Recipient email address")
    subject: str = Field(description="Email subject line")
    body: str = Field(description="Email body content")
    confidence: float = Field(description="Confidence score (0-1)", ge=0, le=1)
    needs_approval: bool = Field(description="Whether this requires human approval")
    priority: Priority = Field(description="Email priority level")
    reasoning: str = Field(description="Explanation of the response strategy")


# ============================================================================
# SOCIAL AGENT MODELS
# ============================================================================

class SocialPlatform(str, Enum):
    """Social media platforms."""
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"


class SocialPost(BaseModel):
    """Structured output for social media content generation."""

    platform: SocialPlatform = Field(description="Target platform")
    content: str = Field(description="Post content (body text)")
    hashtags: List[str] = Field(description="Hashtags for the post", default_factory=list)
    scheduled_time: Optional[str] = Field(
        description="Suggested posting time (ISO format or 'immediate')",
        default=None
    )
    image_url: Optional[str] = Field(
        description="Image URL for Instagram/visual posts",
        default=None
    )
    confidence: float = Field(description="Confidence score (0-1)", ge=0, le=1)
    needs_approval: bool = Field(description="Whether this requires human approval")
    reasoning: str = Field(description="Explanation of content strategy")


# ============================================================================
# FINANCE AGENT MODELS
# ============================================================================

class FinanceActionType(str, Enum):
    """Types of finance actions."""
    CREATE_INVOICE = "create_invoice"
    PAYMENT_RECEIVED = "payment_received"
    EXPENSE_CATEGORIZE = "expense_categorize"
    REPORT_GENERATE = "report_generate"
    ANOMALY_DETECTED = "anomaly_detected"


class RiskLevel(str, Enum):
    """Financial risk levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FinanceAction(BaseModel):
    """Structured output for financial task processing."""

    action_type: FinanceActionType = Field(description="Type of financial action")
    amount: Optional[float] = Field(description="Amount in USD", default=None)
    currency: str = Field(description="Currency code", default="USD")
    description: str = Field(description="Description of the action/item")
    risk_level: RiskLevel = Field(description="Risk assessment level")
    customer_name: Optional[str] = Field(description="Customer name for invoices", default=None)
    confidence: float = Field(description="Confidence score (0-1)", ge=0, le=1)
    needs_approval: bool = Field(description="Whether this requires human approval")
    reasoning: str = Field(description="Explanation of the financial assessment")


# ============================================================================
# TRIAGE AGENT MODELS
# ============================================================================

class TriageDecision(BaseModel):
    """Structured output for task triage and routing."""

    category: Category = Field(description="Determined task category")
    priority: Priority = Field(description="Task priority level")
    confidence: float = Field(description="Confidence in classification (0-1)", ge=0, le=1)
    needs_specialist: bool = Field(description="Whether this needs a specialist agent")
    recommended_agent: Optional[str] = Field(
        description="Which agent should handle this (email_agent, social_agent, finance_agent, or None for auto-complete)",
        default=None
    )
    reasoning: str = Field(description="Explanation of the triage decision")
    can_auto_complete: bool = Field(description="Whether this can be handled without human review")


# ============================================================================
# GENERIC AGENT RESPONSE
# ============================================================================

class AgentResponse(BaseModel):
    """Generic response wrapper for all agents."""

    success: bool = Field(description="Whether the operation succeeded")
    message: str = Field(description="Human-readable message")
    data: Optional[str] = Field(description="Additional data or output", default=None)
    needs_approval: bool = Field(description="Whether human approval is required")
    next_action: Optional[str] = Field(description="Suggested next action", default=None)


# ============================================================================
# INPUT GUARDRAIL MODELS
# ============================================================================

class GuardrailCheck(BaseModel):
    """Guardrail output for input validation."""

    should_block: bool = Field(description="Whether to block this input")
    reasoning: str = Field(description="Explanation of why it was blocked or allowed")
    risk_level: RiskLevel = Field(description="Assessed risk level")


# ============================================================================
# OUTPUT GUARDRAIL MODELS
# ============================================================================

class OutputCheck(BaseModel):
    """Guardrail output for response validation."""

    is_appropriate: bool = Field(description="Whether the output is appropriate")
    reasoning: str = Field(description="Explanation of the validation")
    issues: List[str] = Field(description="List of any issues found", default_factory=list)
