#!/usr/bin/env python3
"""
Direct GLM API Test
"""

import asyncio
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment variables
load_dotenv()

async def test_glm_direct():
    """Test GLM API directly."""
    api_key = os.environ.get("GLM_API_KEY")

    print(f"API Key: {api_key[:20]}...{api_key[-10:]}")

    # Try different models
    models = ["glm-4-flash", "glm-4-plus", "glm-4", "glm-4.7-flash"]
    base_url = "https://api.z.ai/api/paas/v4/"

    for model in models:
        print(f"\n🔄 Trying model={model}")

        client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )

        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": "Say hello!"}
                ],
                timeout=10.0
            )

            print(f"✅ SUCCESS with model={model}")
            print(f"Response: {response.choices[0].message.content}")
            return  # Success!

        except Exception as e:
            error_str = str(e)
            if "400" in error_str or "1211" in error_str:
                print(f"   ❌ Model not found")
            elif "429" in error_str or "1113" in error_str:
                print(f"   ⚠️  No balance/credits")
            else:
                print(f"   ❌ {error_str[:100]}")

    print("\n❌ All models failed")


if __name__ == "__main__":
    asyncio.run(test_glm_direct())
