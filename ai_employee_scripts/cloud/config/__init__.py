"""
Cloud Agent Configuration

Configuration for the OpenAI Agents SDK with GLM (Zhipu AI) model.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from agents import OpenAIChatCompletionsModel, RunConfig, AsyncOpenAI

# Load environment variables
load_dotenv()

# Agent type identification
AGENT_TYPE = os.environ.get("AGENT_TYPE", "cloud")

# Paths
VAULT_PATH = Path(os.environ.get("VAULT_PATH", Path(__file__).parent.parent.parent.parent / "AI_Employee_Vault"))
GIT_REMOTE = os.environ.get("GIT_REMOTE", "origin")

# =============================================================================
# GLM API Configuration (ZAI)
# =============================================================================
GLM_API_KEY = os.environ.get("GLM_API_KEY", "")
GLM_BASE_URL = os.environ.get("GLM_BASE_URL", "https://api.z.ai/api/paas/v4/")

# Model Configuration
MODEL_NAME = os.environ.get("MODEL_NAME", "glm-4.7-flash")

# Polling intervals (seconds)
NEEDS_ACTION_CHECK_INTERVAL = int(os.environ.get("NEEDS_ACTION_CHECK_INTERVAL", "30"))
GIT_SYNC_INTERVAL = int(os.environ.get("GIT_SYNC_INTERVAL", "300"))

# Logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")


def get_xiaomi_client() -> AsyncOpenAI:
    """Create and return an AsyncOpenAI client configured for GLM."""
    api_key = GLM_API_KEY
    if not api_key:
        raise ValueError("GLM_API_KEY environment variable is required")

    return AsyncOpenAI(
        api_key=api_key,
        base_url=GLM_BASE_URL
    )


def get_model(client: AsyncOpenAI) -> OpenAIChatCompletionsModel:
    """Create and return a model instance for GLM."""
    return OpenAIChatCompletionsModel(
        model=MODEL_NAME,
        openai_client=client
    )


def get_run_config(model: OpenAIChatCompletionsModel, client: AsyncOpenAI) -> RunConfig:
    """Create and return a RunConfig for agent execution."""
    return RunConfig(
        model=model,
        model_provider=client,
    )


# Vault folder paths
def get_vault_folders(vault_path: Path = None) -> dict:
    """Get all vault folder paths."""
    base = vault_path or VAULT_PATH

    return {
        "base": base,
        "inbox": base / "Inbox",
        "needs_action": base / "Needs_Action",
        "in_progress_cloud": base / "In_Progress" / "cloud",
        "updates": base / "Updates",
        "pending_approval": base / "Pending_Approval",
        "approved": base / "Approved",
        "done": base / "Done",
        "failed": base / "Failed",
        "logs": base / "Logs",
        "accounting": base / "Accounting",
        "briefings": base / "Briefings",
        "content_queued": base / "Content_To_Post" / "queued",
    }
