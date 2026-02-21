# Model Providers — Configuration & Capabilities

## Table of Contents
1. [Provider Overview](#provider-overview)
2. [Azure OpenAI (Recommended)](#azure-openai)
3. [OpenAI Direct](#openai-direct)
4. [Anthropic Claude](#anthropic-claude)
5. [Ollama (Local)](#ollama-local)
6. [GitHub Models (Free)](#github-models)
7. [Azure AI Foundry](#azure-ai-foundry)
8. [Provider Selection Guide](#provider-selection-guide)

---

## Provider Overview

| Provider | Package | Function Tools | Streaming | Structured Output | Code Interpreter | File Search | MCP |
|----------|---------|:-:|:-:|:-:|:-:|:-:|:-:|
| **Azure OpenAI Responses** | `agent-framework-azure-ai` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Azure OpenAI Chat** | `agent-framework-azure-ai` | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| **OpenAI** | `agent-framework-openai` | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| **Anthropic Claude** | `agent-framework-anthropic` | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| **Ollama** | `agent-framework-ollama` | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| **GitHub Models** | Built-in | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |

---

## Azure OpenAI

The recommended provider for production. Two client types available:

### Responses API Client (Recommended)

```python
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential

client = AzureOpenAIResponsesClient(
    project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
    deployment_name=os.environ["AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME"],
    credential=AzureCliCredential(),
    api_version="2024-12-01",  # Optional
)

agent = client.as_agent(
    name="AzureAgent",
    instructions="You are a helpful assistant.",
    tools=[my_tool],
)
```

**Environment Variables:**
```bash
AZURE_AI_PROJECT_ENDPOINT=https://your-project.openai.azure.com
AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2024-12-01  # Optional
```

### Chat Completions Client

```python
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential

client = AzureOpenAIChatClient(
    endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    deployment_name=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
    credential=AzureCliCredential(),
)
```

### Authentication Options

```python
# Development: Azure CLI
from azure.identity import AzureCliCredential
credential = AzureCliCredential()

# Production: Managed Identity
from azure.identity import DefaultAzureCredential
credential = DefaultAzureCredential()

# CI/CD: Service Principal
from azure.identity import ClientSecretCredential
credential = ClientSecretCredential(
    tenant_id=os.environ["AZURE_TENANT_ID"],
    client_id=os.environ["AZURE_CLIENT_ID"],
    client_secret=os.environ["AZURE_CLIENT_SECRET"],
)

# API Key (not recommended)
from azure.core.credentials import AzureKeyCredential
credential = AzureKeyCredential(os.environ["AZURE_OPENAI_API_KEY"])
```

---

## OpenAI Direct

```python
from openai import OpenAIClient

client = OpenAIClient(api_key=os.environ["OPENAI_API_KEY"])
chat_client = client.get_chat_client(os.environ.get("OPENAI_MODEL", "gpt-4o-mini"))

agent = chat_client.as_agent(
    name="OpenAIAgent",
    instructions="You are a helpful assistant.",
    tools=[my_tool],
)
```

**Environment Variables:**
```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini  # or gpt-4o, gpt-4-turbo, etc.
```

**Available Models:** gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo, o1, o1-mini, o3-mini

---

## Anthropic Claude

```python
from agent_framework.anthropic import AnthropicChatClient

client = AnthropicChatClient(
    api_key=os.environ["ANTHROPIC_API_KEY"],
    model="claude-3-5-sonnet-20241022",
)

agent = client.as_agent(
    name="ClaudeAgent",
    instructions="You are a helpful assistant.",
    tools=[my_tool],
)
```

**Environment Variables:**
```bash
ANTHROPIC_API_KEY=sk-ant-...
```

**Available Models:** claude-3-5-sonnet-20241022, claude-3-opus-20240229, claude-3-haiku-20240307

**Limitations:** No code interpreter, no file search, no MCP (use function tools instead).

---

## Ollama (Local)

Run models locally with no API costs.

### Setup

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama3.1
ollama pull codellama
ollama pull mistral

# Start server
ollama serve
```

### Usage

```python
from agent_framework.ollama import OllamaChatClient

client = OllamaChatClient(
    base_url="http://localhost:11434",
    model="llama3.1",
)

agent = client.as_agent(
    name="LocalAgent",
    instructions="You are a helpful assistant.",
    tools=[my_tool],
)
```

**Environment Variables:**
```bash
OLLAMA_ENDPOINT=http://localhost:11434
OLLAMA_MODEL=llama3.1
```

**Good for:** Development, testing, offline use, privacy-sensitive data.

**Limitations:** No code interpreter, no file search, no MCP. Tool calling quality depends on model.

---

## GitHub Models

Free tier for testing and prototyping.

```python
from agent_framework.github import GitHubModelsChatClient

client = GitHubModelsChatClient(
    token=os.environ["GITHUB_TOKEN"],
    model=os.environ.get("GITHUB_MODEL", "gpt-4o"),
)

agent = client.as_agent(
    name="GitHubAgent",
    instructions="You are a helpful assistant.",
    tools=[my_tool],
)
```

**Environment Variables:**
```bash
GITHUB_TOKEN=ghp_...  # GitHub Personal Access Token
GITHUB_MODEL=gpt-4o   # Supports: gpt-4o, gpt-4o-mini, o3-mini, etc.
```

**Limitations:** Rate-limited, no structured output, no code interpreter.

---

## Azure AI Foundry

Fully managed agents with server-side persistence.

```python
from agent_framework.azure import AzureAIAgentClient
from azure.identity import AzureCliCredential

client = AzureAIAgentClient(
    project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
    credential=AzureCliCredential(),
)

# Create agent with Foundry-managed tools
agent = client.as_agent(
    name="FoundryAgent",
    instructions="You are an enterprise assistant.",
    tools=[my_tool],
    mcp_servers=["web-search", "file-search"],  # Hosted MCP
)

# Sessions are automatically persisted server-side
session = await agent.create_session()
result = await agent.run("Analyze our quarterly results", session=session)
```

**Key Advantages:**
- Server-side agent persistence (no local state management)
- Built-in MCP hosting
- OpenTelemetry observability
- Compliance and governance features
- Model routing across 11,000+ models

---

## Provider Selection Guide

| Scenario | Recommended Provider |
|----------|---------------------|
| Production enterprise app | Azure OpenAI Responses |
| Rapid prototyping (free) | GitHub Models |
| Local development / offline | Ollama |
| Multi-model flexibility | OpenAI Direct |
| Strong reasoning tasks | Anthropic Claude |
| Managed agent hosting | Azure AI Foundry |
| Privacy-sensitive data | Ollama (local) |
| Cost optimization | GitHub Models → Ollama |

### Cost Tiers

```
Free:       GitHub Models (rate-limited), Ollama (local compute)
Low cost:   gpt-4o-mini, Claude Haiku
Mid cost:   gpt-4o, Claude Sonnet
High cost:  gpt-4-turbo, Claude Opus, o1
```

### Switching Providers

The agent API is provider-agnostic. To switch providers, change only the client:

```python
# Switch from Azure to OpenAI — only the client changes
# client = AzureOpenAIResponsesClient(...)  # Before
client = OpenAIClient(api_key=os.environ["OPENAI_API_KEY"])  # After

# Agent code stays identical
agent = client.as_agent(
    name="MyAgent",
    instructions="You are helpful.",
    tools=[my_tool],
)
```
