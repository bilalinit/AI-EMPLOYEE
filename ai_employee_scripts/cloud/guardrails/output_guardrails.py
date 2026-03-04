"""
Output Guardrails for Cloud Agents

Safety checks before agent responses reach the user.
Part B: Advanced Workflows - Output Guardrails
"""

import re
from typing import List

from agents import Agent, GuardrailFunctionOutput, output_guardrail
from cloud.bots.models import OutputCheck, RiskLevel


# ============================================================================
# OUTPUT VALIDATION FUNCTIONS
# ============================================================================

def _check_for_pii(content: str) -> List[str]:
    """
    Check for potential PII (Personally Identifiable Information) leaks.

    Args:
        content: Content to check

    Returns:
        List of issues found
    """
    issues = []

    # Check for credit card patterns (basic)
    if re.search(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', content):
        issues.append("Possible credit card number detected")

    # Check for SSN patterns
    if re.search(r'\b\d{3}-\d{2}-\d{4}\b', content):
        issues.append("Possible SSN pattern detected")

    # Check for API keys (basic pattern)
    if re.search(r'(api[_-]?key|token|secret)[\s:=]+["\']?[\w-]{20,}', content, re.IGNORECASE):
        issues.append("Possible API key or secret in output")

    return issues


def _check_for_inappropriate_content(content: str) -> List[str]:
    """
    Check for inappropriate or harmful content.

    Args:
        content: Content to check

    Returns:
        List of issues found
    """
    issues = []

    # Words/phrases that should not be in AI outputs
    inappropriate_patterns = [
        (r'\b(hate|kill|harm|hurt|destroy)\b', "Harmful language detected"),
        (r'i\s+(can\s+)?not\s+(help|do|assist)', "Unhelpful refusal"),
        (r'(as\s+(an?\s+)?ai|language\s+model).{0,100}(not\s+able|cannot)', "AI disclosure in response"),
    ]

    for pattern, issue in inappropriate_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            issues.append(issue)

    return issues


def _check_for_policy_violations(content: str) -> List[str]:
    """
    Check for violations of company policies.

    Args:
        content: Content to check

    Returns:
        List of issues found
    """
    issues = []

    # Things cloud agent should NEVER output
    forbidden = [
        (r'(password|credential|secret).{0,50}["\']?\w+["\']?', "Credentials in output"),
        (r'(bank\s+account|routing\s+number).{0,30}\d', "Banking info in output"),
        (r'\bx?[a-z0-9]{32,}\b', "Possible token/key in output"),
    ]

    for pattern, issue in forbidden:
        if re.search(pattern, content, re.IGNORECASE):
            issues.append(issue)

    return issues


def _validate_response_quality(content: str) -> List[str]:
    """
    Check response quality and completeness.

    Args:
        content: Content to check

    Returns:
        List of issues found
    """
    issues = []

    # Check for empty response
    if not content or len(content.strip()) < 10:
        issues.append("Response too short or empty")
        return issues  # Don't check further if empty

    # Check for excessive repetition
    words = content.split()
    if len(words) > 50:
        # Count word frequency
        word_counts = {}
        for word in words:
            word_counts[word.lower()] = word_counts.get(word.lower(), 0) + 1

        # Flag if any word appears > 30% of time
        for word, count in word_counts.items():
            if count / len(words) > 0.3 and len(word) > 2:
                issues.append(f"Excessive repetition of word '{word}'")
                break

    # Check for AI-sounding phrases (brand voice violation)
    ai_sounding = [
        "as an ai language model",
        "as an artificial intelligence",
        "i don't have personal opinions",
        "i'm not capable of",
    ]

    content_lower = content.lower()
    for phrase in ai_sounding:
        if phrase in content_lower:
            issues.append("AI-sounding language detected (should match brand voice)")
            break

    return issues


def _check_structured_output_format(output: str, expected_fields: List[str] = None) -> List[str]:
    """
    Check if output follows expected structured format.

    Args:
        output: Output to check
        expected_fields: List of expected field names (optional)

    Returns:
        List of issues found
    """
    issues = []

    # Check for frontmatter
    if '---' not in output:
        issues.append("Missing frontmatter format")

    # Check for expected sections
    if expected_fields:
        for field in expected_fields:
            if field.lower() not in output.lower():
                issues.append(f"Missing expected field: {field}")

    return issues


# ============================================================================
# OUTPUT GUARDRAIL AGENT
# ============================================================================

def create_output_guardrail_agent(model=None):
    """
    Create the output guardrail agent for response validation.

    Args:
        model: The model to use (default: None, will be set by orchestrator)

    Returns:
        Agent: Configured output guardrail agent
    """
    instructions = """You are an Output Guardrail Agent. Your job is to check if agent responses are appropriate before they reach the human.

Check for:
1. PII or sensitive information leaks
2. Inappropriate or harmful content
3. Policy violations (credentials, banking info)
4. Response quality issues
5. Proper formatting

Be thorough but not overly strict. Flag genuine issues, allow legitimate work to proceed."""

    return Agent(
        name="OutputGuardrail",
        instructions=instructions,
        output_type=OutputCheck,
        model=model
    )


# ============================================================================
# OUTPUT GUARDRAIL FUNCTION
# ============================================================================

@output_guardrail
async def output_safety_check(context, agent, output_text: str) -> GuardrailFunctionOutput:
    """
    Output guardrail that validates agent responses.

    This implements Part B: Advanced Workflows - Output Guardrails
    from the OpenAI Agents SDK.

    Args:
        context: Agent context
        agent: The agent whose output is being checked
        output_text: The generated output

    Returns:
        GuardrailFunctionOutput: Whether to tripwire (block) the output
    """
    issues = []

    # Run all checks
    issues.extend(_check_for_pii(output_text))
    issues.extend(_check_for_inappropriate_content(output_text))
    issues.extend(_check_for_policy_violations(output_text))
    issues.extend(_validate_response_quality(output_text))

    # Determine if blocking is needed
    critical_issues = [i for i in issues if any(
        keyword in i.lower() for keyword in ['credential', 'password', 'bank', 'ssn', 'credit card', 'harmful']
    )]

    if critical_issues:
        return GuardrailFunctionOutput(
            output_info=OutputCheck(
                is_appropriate=False,
                reasoning=f"Critical issues found: {'; '.join(critical_issues)}",
                issues=issues
            ),
            tripwire_triggered=True
        )

    if issues:
        return GuardrailFunctionOutput(
            output_info=OutputCheck(
                is_appropriate=True,
                reasoning=f"Minor issues found but output acceptable: {'; '.join(issues[:3])}",
                issues=issues
            ),
            tripwire_triggered=False
        )

    return GuardrailFunctionOutput(
        output_info=OutputCheck(
            is_appropriate=True,
            reasoning="Output validation passed",
            issues=[]
        ),
        tripwire_triggered=False
    )


# ============================================================================
# SIMPLE FUNCTION (NO AI NEEDED)
# ============================================================================

def check_output_safety_simple(content: str) -> OutputCheck:
    """
    Simple output safety check without running guardrail agent.

    Use this for lightweight validation.

    Args:
        content: Content to validate

    Returns:
        OutputCheck: Validation result
    """
    issues = []

    # Run all checks
    issues.extend(_check_for_pii(content))
    issues.extend(_check_for_inappropriate_content(content))
    issues.extend(_check_for_policy_violations(content))
    issues.extend(_validate_response_quality(content))

    # Check for critical issues
    critical_keywords = ['credential', 'password', 'bank', 'ssn', 'credit card', 'harmful', 'secret', 'api key']
    has_critical = any(keyword in ' '.join(issues).lower() for keyword in critical_keywords)

    if has_critical:
        return OutputCheck(
            is_appropriate=False,
            reasoning=f"Critical issues: {'; '.join(issues)}",
            issues=issues
        )

    return OutputCheck(
        is_appropriate=True,
        reasoning=f"Validation passed. {'Minor notes: ' + '; '.join(issues) if issues else 'No issues.'}",
        issues=issues
    )
