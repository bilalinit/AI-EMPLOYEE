#!/usr/bin/env python3
"""
Simple OpenAI Agents SDK Test
"""

import asyncio
import os
from dotenv import load_dotenv
from agents import Agent, Runner, OpenAIChatCompletionsModel, RunConfig, AsyncOpenAI

load_dotenv()

async def main():
    api_key = os.environ.get("GLM_API_KEY")
    base_url = os.environ.get("GLM_BASE_URL", "https://api.z.ai/api/paas/v4/")
    model_name = os.environ.get("MODEL_NAME", "glm-4.7-flash")

    print(f"API Key: {api_key[:20]}...{api_key[-10:]}")
    print(f"Base URL: {base_url}")
    print(f"Model: {model_name}")

    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    model = OpenAIChatCompletionsModel(model=model_name, openai_client=client)
    config = RunConfig(model=model, model_provider=client)

    agent = Agent(
        name="TestAgent",
        instructions="You are a helpful assistant. Keep responses brief.",
        model=model
    )

    print("\n🤖 Running agent...")
    result = await Runner.run(agent, "Say hello in one sentence!", run_config=config)

    print(f"\n✅ Response: {result.final_output}")


if __name__ == "__main__":
    asyncio.run(main())
