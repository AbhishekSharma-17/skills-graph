# Microsoft Agent Framework Overview

Microsoft Agent Framework is an open-source Python SDK for building AI agents. It unifies AutoGen's multi-agent orchestration with Semantic Kernel's enterprise features.

## Core Architecture

```
Agent = LLM Client + Instructions + Tools + Memory + Middleware
Workflow = Graph of Agents/Functions connected by Edges
```

**Two building blocks:**
- **Agents** — Individual AI entities: one LLM + tools + memory. Use for open-ended tasks.
- **Workflows** — Graph-based orchestration of multiple agents/functions. Use for defined processes.

## Canonical Pattern (Python)

```python
import asyncio, os
from azure.identity.aio import AzureCliCredential
from agent_framework.azure import AzureOpenAIResponsesClient
from agent_framework import tool
from typing import Annotated

@tool
def get_weather(location: Annotated[str, "City name"]) -> str:
    """Get weather for a location."""
    return f"Sunny, 72°F in {location}"

async def main():
    client = AzureOpenAIResponsesClient(
        project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
        deployment_name=os.environ["AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME"],
        credential=AzureCliCredential(),
    )
    agent = client.as_agent(
        name="Assistant",
        instructions="You are a helpful assistant.",
        tools=[get_weather],
    )

    # Non-streaming
    result = await agent.run("What's the weather in Seattle?")
    print(result.text)

    # Streaming
    async for chunk in agent.run("Tell me about Seattle", stream=True):
        if chunk.text:
            print(chunk.text, end="", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
```

## Provider Feature Matrix

| Provider | Client Class | Tools | Structured Output | Code Interpreter | File Search | MCP | Background |
|---|---|:-:|:-:|:-:|:-:|:-:|:-:|
| **Azure OpenAI Responses** | `AzureOpenAIResponsesClient` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **OpenAI Responses** | `OpenAIResponsesClient` | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| **Azure AI Foundry** | `AzureAIAgentClient` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Anthropic Claude** | `AnthropicChatClient` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Ollama** | `OllamaChatClient` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **GitHub Copilot** | `GitHubCopilotClient` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |

## Critical Rules

1. **All operations are async** — always use `async/await` and `asyncio.run(main())`
2. **Tools MUST have**: `@tool` decorator + docstring + type hints + `Annotated` descriptions
3. **Sessions required for multi-turn** — without session, no memory between `agent.run()` calls
4. **Use `AzureCliCredential`** in dev, `DefaultAzureCredential` in production
5. **Framework is Public Preview** — pin version in `requirements.txt`
6. **Only one history provider** should use `load_messages=True`

## Installation

```bash
pip install agent-framework --pre
az login  # For Azure authentication
```

```bash
# Required environment variables (Azure OpenAI)
export AZURE_AI_PROJECT_ENDPOINT="https://your-project.openai.azure.com"
export AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME="gpt-4o"
```

## Common Errors

| Error | Fix |
|---|---|
| `InvalidAuthenticationTokenError` | Run `az login` |
| `ResourceNotFoundError` | Check endpoint and deployment name env vars |
| `RateLimitError` | Wait or upgrade Azure plan |
| Tool missing docstring | Add `"""docstring"""` to every `@tool` function |
| Tool missing type hints | Use `Annotated[type, "description"]` on all params |
| No memory between turns | Pass `session=session` to `agent.run()` |
| Middleware not running | Check registration: agent-level vs run-level |
