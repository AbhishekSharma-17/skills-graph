# Model Providers — Azure OpenAI, OpenAI, Anthropic, Ollama, GitHub, Custom

## Provider Overview

| Provider | Package | Best For |
|---|---|---|
| **Azure OpenAI Responses** | `agent-framework-azure-ai` | Production Azure apps (recommended) |
| **OpenAI Responses** | `agent-framework-openai` | Direct OpenAI API |
| **Azure AI Foundry** | `agent-framework-azure-ai` | Managed agents, enterprise |
| **Anthropic Claude** | `agent-framework-anthropic` | Claude models |
| **Ollama** | `agent-framework-ollama` | Local/private LLMs |
| **GitHub Copilot** | built-in | Free tier, GitHub integration |
| **Amazon Bedrock** | `agent-framework-bedrock` | AWS integration |

## Azure OpenAI Responses (Recommended)

```python
import os
from azure.identity.aio import AzureCliCredential
from agent_framework.azure import AzureOpenAIResponsesClient

client = AzureOpenAIResponsesClient(
    project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
    deployment_name=os.environ["AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME"],
    credential=AzureCliCredential(),
)

agent = client.as_agent(
    name="AzureAgent",
    instructions="You are a helpful assistant.",
    tools=[get_weather],
)
```

**Environment variables:**
```bash
AZURE_AI_PROJECT_ENDPOINT=https://your-project.openai.azure.com
AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME=gpt-4o
```

**Features:** Function tools ✅ | Structured output ✅ | Code interpreter ✅ | File search ✅ | MCP ✅ | Background ✅

## OpenAI Responses

```python
from agent_framework.openai import OpenAIResponsesClient

client = OpenAIResponsesClient()  # Uses OPENAI_API_KEY env var

agent = client.as_agent(
    name="OpenAIAgent",
    instructions="You are a helpful assistant.",
)
```

**Environment variables:**
```bash
OPENAI_API_KEY=sk-...
```

**Features:** Function tools ✅ | Structured output ✅ | Code interpreter ✅ | File search ✅ | MCP ❌ | Background ✅

## Azure AI Foundry Agent Service

Managed agent hosting with server-side persistence:

```python
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import DefaultAzureCredential

async with AzureAIAgentClient(
    async_credential=DefaultAzureCredential(),
) as client:
    agent = client.as_agent(
        name="FoundryAgent",
        instructions="You are a helpful assistant.",
        tools=["code_interpreter", "file_search"],
    )

    result = await agent.run("Analyze this data")
```

**Environment variables:**
```bash
AZURE_AI_PROJECT_ENDPOINT=https://your-foundry-project.services.ai.azure.com
```

**Features:** Function tools ✅ | Structured output ✅ | Code interpreter ✅ | File search ✅ | MCP ✅ | Background ✅

## Anthropic Claude

```python
from agent_framework.anthropic import AnthropicChatClient

client = AnthropicChatClient()  # Uses ANTHROPIC_API_KEY env var

agent = client.as_agent(
    name="ClaudeAgent",
    instructions="You are a helpful assistant.",
    tools=[get_weather],
)
```

**Environment variables:**
```bash
ANTHROPIC_API_KEY=sk-ant-...
```

**Features:** Function tools ✅ | Structured output ✅ | Code interpreter ❌ | File search ❌ | MCP ❌ | Background ❌

## Ollama (Local)

```python
from agent_framework.ollama import OllamaChatClient

client = OllamaChatClient(
    endpoint="http://localhost:11434/v1",
    model="llama3.1",
)

agent = client.as_agent(
    name="LocalAgent",
    instructions="You are a helpful assistant.",
)
```

**Setup:**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull model
ollama pull llama3.1

# Start server
ollama serve
```

**Features:** Function tools ✅ | Structured output ✅ | Code interpreter ❌ | File search ❌ | MCP ❌ | Background ❌

## GitHub Models (Free)

```python
from agent_framework.github import GitHubModelsChatClient

client = GitHubModelsChatClient(
    token=os.environ["GITHUB_TOKEN"],
    model="gpt-4o",
)

agent = client.as_agent(
    name="GitHubAgent",
    instructions="You are a helpful assistant.",
)
```

**Environment variables:**
```bash
GITHUB_TOKEN=ghp_...
```

**Supported models:** gpt-4o, gpt-4o-mini, o3-mini, and more.

**Features:** Function tools ✅ | Structured output ❌ | Code interpreter ❌ | File search ❌ | MCP ❌ | Background ❌

**Note:** GitHub Models is rate-limited on the free tier.

## Azure OpenAI Chat Completions (Legacy)

```python
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential

client = AzureOpenAIChatClient(
    credential=AzureCliCredential(),
)

agent = client.as_agent(
    name="ChatAgent",
    instructions="You are a helpful assistant.",
)
```

**Note:** Use Azure OpenAI Responses instead for new projects (more features).

## Switching Providers

The agent API is provider-agnostic. To switch providers, only change the client:

```python
# Azure OpenAI
client = AzureOpenAIResponsesClient(credential=cred, ...)
agent = client.as_agent(name="Bot", instructions="...", tools=[my_tool])

# Switch to OpenAI — same agent config
client = OpenAIResponsesClient()
agent = client.as_agent(name="Bot", instructions="...", tools=[my_tool])

# Switch to Ollama — same agent config
client = OllamaChatClient(endpoint="http://localhost:11434/v1", model="llama3.1")
agent = client.as_agent(name="Bot", instructions="...", tools=[my_tool])
```

Tools, instructions, sessions, and middleware work the same across all providers.

## Choosing a Provider

| Scenario | Recommended Provider |
|---|---|
| Production Azure app | Azure OpenAI Responses |
| Managed enterprise agents | Azure AI Foundry |
| Direct OpenAI usage | OpenAI Responses |
| Privacy / local LLMs | Ollama |
| Free tier / prototyping | GitHub Models |
| Claude models | Anthropic |
| AWS infrastructure | Amazon Bedrock |

## Custom Providers

See `17-custom-agents.md` for implementing custom chat clients.
