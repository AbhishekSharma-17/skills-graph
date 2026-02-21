# Getting Started — First Agent Setup

## Installation

```bash
pip install agent-framework --pre
```

Individual packages (if needed):
- `agent-framework-core` — Base framework
- `agent-framework-azure-ai` — Azure AI Foundry integration
- `agent-framework-openai` — OpenAI integration
- `agent-framework-anthropic` — Anthropic Claude
- `agent-framework-ollama` — Local Ollama
- `agent-framework-devui` — Developer UI for debugging

## Azure Authentication

```bash
# Install Azure CLI and login
az login

# Verify you're logged in
az account show
```

## Environment Variables

```bash
# Azure OpenAI (recommended)
export AZURE_AI_PROJECT_ENDPOINT="https://your-project.openai.azure.com"
export AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME="gpt-4o"

# Optional: override API version
export AZURE_OPENAI_API_VERSION="2024-12-01"
```

For other providers see `10-providers.md`.

## Your First Agent — Complete Code

```python
import asyncio
import os
from azure.identity.aio import AzureCliCredential
from agent_framework.azure import AzureOpenAIResponsesClient

async def main():
    # 1. Create credential and client
    credential = AzureCliCredential()
    client = AzureOpenAIResponsesClient(
        project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
        deployment_name=os.environ["AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME"],
        credential=credential,
    )

    # 2. Create agent
    agent = client.as_agent(
        name="HelloAgent",
        instructions="You are a friendly assistant. Keep your answers brief.",
    )

    # 3. Non-streaming response
    result = await agent.run("What is the capital of France?")
    print(f"Agent: {result}")

    # 4. Streaming response
    print("Agent (streaming): ", end="", flush=True)
    async for chunk in agent.run("Tell me a one-sentence fun fact.", stream=True):
        if chunk.text:
            print(chunk.text, end="", flush=True)
    print()

if __name__ == "__main__":
    asyncio.run(main())
```

## Adding Tools — Quick Example

```python
from agent_framework import tool
from typing import Annotated

@tool
def get_weather(location: Annotated[str, "City name"]) -> str:
    """Get weather for a location."""
    return f"Sunny, 72°F in {location}"

agent = client.as_agent(
    name="WeatherBot",
    instructions="You are a weather assistant.",
    tools=[get_weather],  # Pass tools here
)

result = await agent.run("What's the weather in Seattle?")
```

## Multi-Turn with Session — Quick Example

```python
session = agent.create_session()

r1 = await agent.run("My name is Alice", session=session)
r2 = await agent.run("What's my name?", session=session)
# Agent remembers: "Your name is Alice!"
```

## Project Structure

```
my-agent/
├── main.py              # Entry point
├── tools.py             # @tool functions
├── .env                 # Environment variables
├── requirements.txt     # Dependencies
└── tests/
    └── test_agent.py
```

### requirements.txt
```
agent-framework>=1.0.0b260130
azure-identity>=1.15.0
python-dotenv>=1.0.0
```

### .env
```bash
AZURE_AI_PROJECT_ENDPOINT=https://your-project.openai.azure.com
AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME=gpt-4o
```

## Next Steps

| Want to... | Read |
|---|---|
| Understand streaming vs non-streaming | `02-running-agents.md` |
| Add function tools | `04-tools-function.md` |
| Add MCP/hosted tools | `05-tools-hosted.md` |
| Use a different model provider | `10-providers.md` |
