#!/usr/bin/env python3
"""
Simple Email Agent Test
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

    print(f"Model: {model_name}")
    print(f"Base URL: {base_url}")

    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    model = OpenAIChatCompletionsModel(model=model_name, openai_client=client)
    config = RunConfig(model=model, model_provider=client)

    agent = Agent(
        name="EmailAgent",
        instructions="""You are an email drafting assistant.
Draft a professional reply to the following email.
Keep it brief and professional.
End with a clear next step.""",
        model=model
    )

    test_email = """
From: john@acme.com
Subject: AI Automation Services

Hi,

We're interested in your Digital FTE services.
Can you provide pricing and timeline?

Thanks,
John
"""

    print("\n🤖 Drafting email response...")
    result = await Runner.run(agent, test_email, run_config=config)

    print(f"\n✅ Draft:")
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
