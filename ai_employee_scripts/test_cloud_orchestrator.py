#!/usr/bin/env python3
"""
Quick Cloud Agent Test
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Set vault path to correct location
os.environ["VAULT_PATH"] = str(Path(__file__).parent.parent / "AI_Employee_Vault")

from cloud.config import get_xiaomi_client, get_model, get_run_config
from cloud.agents.email_agent import create_email_agent
from cloud.tools.file_tools import read_task
from agents import Runner


async def test_ai_agent():
    """Test AI agent."""
    print("\n" + "=" * 60)
    print("  AI AGENT TEST")
    print("=" * 60)

    # Debug: print env vars
    print(f"\n🔧 Debug:")
    print(f"   GLM_API_KEY: {os.environ.get('GLM_API_KEY', 'NOT SET')[:20]}...")
    print(f"   GLM_BASE_URL: {os.environ.get('GLM_BASE_URL', 'NOT SET')}")
    print(f"   MODEL_NAME: {os.environ.get('MODEL_NAME', 'NOT SET')}")

    try:
        # Initialize
        client = get_xiaomi_client()
        model = get_model(client)
        config = get_run_config(model, client)

        print(f"\n🔧 Config:")
        print(f"   Client base_url: {client.base_url}")
        print(f"   Model name: {model.model}")

        # Create agent
        agent = create_email_agent(model)

        # Read task
        content = await read_task("TASK_test_cloud_agent_001.md")

        print(f"\n🤖 Running Email Agent...")

        result = await Runner.run(
            agent,
            input=content,
            run_config=config
        )

        draft = result.final_output
        print(f"\n✅ Email Draft Generated:")
        print(f"   To: {draft.to}")
        print(f"   Subject: {draft.subject}")
        print(f"   Confidence: {draft.confidence:.2f}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_ai_agent())
