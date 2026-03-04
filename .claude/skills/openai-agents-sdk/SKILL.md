---
name: openai-agents-sdk-2
description: |
  Complete reference for OpenAI Agents SDK (Python) with Xiaomi "mimo-v2-flash" model. Organized into:
  - Part A: Core Basics (Agents, Tools)
  - Part B: Advanced Workflows (Handoffs, Guardrails, Structured Outputs)
  - Part C: Realtime & Voice (Voice Agents)
  - Part D: Integration & Deployment (Xiaomi, FastAPI, Errors, Production)

  Use this skill to implement specific components based on user request.
---

# OpenAI Agents SDK - Master Skill Reference (Xiaomi Edition)

This document is organized into 4 distinct parts. Use the relevant part based on the user's specific request.

---

## Part A: Core Basics

### 1. Installation
```bash
# Recommended (uv)
uv add openai-agents
# Optional: uv add 'openai-agents[voice]'

# Pip
pip install openai-agents
```

### 2. Basic Agent (Hello World)
The simplest agent with just instructions and a model.
```python
from agents import Agent, Runner

agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant.",
    model="mimo-v2-flash"
)

async def main():
    await Runner.run(agent, "Hello, who are you?")
```

### 3. Basic Function Tools
Tools allow agents to perform actions. Use the `@function_tool` decorator.
```python
from agents import function_tool

@function_tool
def get_weather(location: str) -> str:
    """Get the current weather for a specific location."""
    # Logic to fetch weather
    return "Sunny, 25C"

agent = Agent(
    name="WeatherBot",
    tools=[get_weather],
    model="mimo-v2-flash"
)
```

---

## Part B: Advanced Workflows & Guardrails

### 1. Multi-Agent Handoffs
Delegate tasks between specialized agents. Handoffs allow an agent to delegate tasks to another agent. This is particularly useful in scenarios where different agents specialize in distinct areas. For example, a customer support app might have agents that each specifically handle tasks like order status, refunds, FAQs, etc. The handoff happens automatically based on the agent's instructions - we don't need to write additional routing logic. When a handoff occurs, it's as though the new agent takes over the conversation, and gets to see the entire previous conversation history.
```python
from agents import Agent

# Specialized agents
billing_agent = Agent(name="Billing", instructions="Handle refunds.")
tech_agent = Agent(name="TechSupport", instructions="Handle technical issues.")

# Triage agent that can hand off to others
triage_agent = Agent(
    name="Triage",
    instructions="Route users to the right department.",
    handoffs=[billing_agent, tech_agent]
)
```

### 2. Guardrails (Safety & Validation)
There are two kinds of guardrails: Input guardrails run on the initial user input. Output guardrails run on the final agent output. Guardrails enable you to do checks and validations of user input and agent output. For example, imagine you have an agent that uses a very smart (and hence slow/expensive) model to help with customer requests. You wouldn't want malicious users to ask the model to help them with their math homework. So, you can run a guardrail with a model. If the guardrail detects malicious usage, it can immediately raise an error and prevent the model from running, saving you time and money. Validate inputs using specialized guardrail agents with structured outputs.

```python
from pydantic import BaseModel
from agents import Agent, Runner, input_guardrail, GuardrailFunctionOutput, ModelSettings

class GuardrailCheck(BaseModel):
    """Guardrail to check user input"""
    should_block: bool
    reasoning: str

# Create guardrail agent
guardrail_agent = Agent(
    name="GuardrailAgent",
    instructions="Check if user input should be blocked",
    model=model,
    output_type=GuardrailCheck,
)

@input_guardrail
async def guardrail_check(context, agent, input_text: str) -> GuardrailFunctionOutput:
    result = await Runner.run(guardrail_agent, input=input_text, run_config=config)
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.should_block
    )

# Use with main agent
main_agent = Agent(
    name="MainAgent",
    input_guardrails=[guardrail_check]
)

# Run with guardrails
async def main():
    try:
        response = await Runner.run(main_agent, "User input here", run_config=config)
        print(response.final_output)
    except Exception as e:
        print(f"Input guardrail blocked request: {e}")
```

### 3. Output Guardrails
Validate agent responses before they reach the user.

```python
from pydantic import BaseModel
from agents import Agent, Runner, output_guardrail, GuardrailFunctionOutput, ModelSettings

class OutputCheck(BaseModel):
    """Guardrail to validate agent output"""
    is_appropriate: bool
    reasoning: str

# Create output guardrail agent
output_guardrail_agent = Agent(
    name="OutputGuardrailAgent",
    instructions="Check if agent response is appropriate",
    model=model,
    output_type=OutputCheck,
    model_settings=ModelSettings(tool_choice="required")
)

@output_guardrail
async def output_check(context, agent, output_text: str) -> GuardrailFunctionOutput:
    result = await Runner.run(output_guardrail_agent, input=output_text, run_config=config)
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=not result.final_output.is_appropriate
    )

# Use with main agent
main_agent = Agent(
    name="MainAgent",
    output_guardrails=[output_check]
)

# Run with output guardrails
async def main():
    try:
        response = await Runner.run(main_agent, "User input here", run_config=config)
        print(response.final_output)
    except Exception as e:
        print(f"Guardrail blocked response: {e}")
```

### 4. Structured Outputs
Ensure the agent returns JSON-like structured data using Pydantic.
```python
from pydantic import BaseModel

class SentimentAnalysis(BaseModel):
    sentiment: str
    confidence: float

agent = Agent(
    name="Analyst",
    output_type=SentimentAnalysis
)
```

---

## Part C: Realtime & Voice

### 1. Realtime Runner
For low-latency voice-to-voice interactions.

```python
from agents import RealtimeRunner

runner = RealtimeRunner(
    instructions="You are a helpful voice assistant.",
    model="mimo-v2-flash",
)

# Connect and run session
# Requires handling audio streams in production environment
```

---

## Part D: Integration & Deployment

### 1. Xiaomi Integration & Custom Clients
Use Xiaomi "mimo-v2-flash" model via the OpenAI-compatible endpoint.

```python
import os
from dotenv import load_dotenv
from agents import (
    Agent, OpenAIChatCompletionsModel, RunConfig, AsyncOpenAI
)

# Load environment variables from .env file
load_dotenv()

# Get the API key from environment variables
API_KEY = os.environ["XIAOMI_API_KEY"]
if not API_KEY:
    raise ValueError("XIAOMI_API_KEY not found in .env file")

# Create the OpenAI client with Xiaomi's OpenAI-compatible endpoint
client = AsyncOpenAI(
    api_key=API_KEY,
    base_url="https://api.xiaomimimo.com/v1/"
)

# Define the Xiaomi model
model = OpenAIChatCompletionsModel(
    model="mimo-v2-flash",
    openai_client=client
)

# Configure the run settings
config = RunConfig(
    model=model,
    model_provider=client,
)

# Use with agent
agent = Agent(name="XiaomiBot", instructions="You are a helpful assistant.", model=model)

# Run the agent output
response = await Runner.run(agent, user_input, run_config=config)
print(response.final_output)
```

### 2. Common Error Handling
Always handle these exceptions in production.

```python
from agents import OutputGuardrailTripwireTriggered

try:
    await Runner.run(agent, user_input)
except OutputGuardrailTripwireTriggered:
    print("Response blocked by safety guardrails.")
except Exception as e:
    print(f"Agent execution failed: {e}")
```

### 3. Production Checklist
- [ ] Set `XIAOMI_API_KEY` or `OPENAI_API_KEY` securely.
- [ ] Implement rate limiting on your API endpoint.
- [ ] Use `AsyncOpenAI` for non-blocking I/O.
- [ ] Add `input_guardrails` to prevent prompt injection.