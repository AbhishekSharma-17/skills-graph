# Getting Started with Microsoft Agent Framework

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Authentication](#authentication)
4. [Your First Agent (Python)](#your-first-agent-python)
5. [Your First Agent (.NET)](#your-first-agent-net)
6. [Provider-Specific Setup](#provider-specific-setup)
7. [Development Environment](#development-environment)
8. [Running Samples](#running-samples)

---

## Prerequisites

**Python:**
- Python 3.10+ (3.11+ recommended)
- pip package manager
- Azure CLI (`az`) installed

**.NET:**
- .NET 8.0 SDK or later
- Azure CLI (`az`) installed

**Azure Resources (for Azure OpenAI):**
- Azure subscription
- Azure AI Foundry project with an OpenAI model deployment
- Deployment name (e.g., `gpt-4o`, `gpt-4o-mini`)

---

## Installation

### Python

```bash
# Full framework (recommended — installs all sub-packages)
pip install agent-framework --pre

# Individual packages (for minimal installs)
pip install agent-framework-core --pre          # Core types and runtime
pip install agent-framework-azure-ai --pre      # Azure AI Foundry integration
pip install agent-framework-openai --pre        # OpenAI integration
pip install agent-framework-anthropic --pre     # Anthropic Claude
pip install agent-framework-ollama --pre        # Local Ollama
pip install agent-framework-devui --pre         # Development UI
```

### .NET

```bash
dotnet add package Microsoft.Agents.AI --prerelease
dotnet add package Microsoft.Agents.AI.OpenAI --prerelease
dotnet add package Azure.AI.OpenAI --prerelease
dotnet add package Azure.Identity
```

### Package Structure

```
agent-framework/
├── agent-framework-core         # Base types, Agent, Workflow, Session
├── agent-framework-azure-ai     # Azure AI Foundry client
├── agent-framework-openai       # OpenAI client
├── agent-framework-anthropic    # Anthropic Claude client
├── agent-framework-ollama       # Ollama local client
├── agent-framework-devui        # VS Code-integrated dev UI
├── agent-framework-ag-ui        # Client-side UI framework
└── agent-framework-durabletask  # Azure Durable Functions support
```

---

## Authentication

### Azure CLI (Development — Recommended)

```bash
# Login once
az login

# Verify
az account show
```

Then use `AzureCliCredential` in code — no API keys needed:

```python
from azure.identity import AzureCliCredential
credential = AzureCliCredential()
```

### API Key (Alternative)

```bash
export AZURE_OPENAI_API_KEY="your-key-here"
```

### Managed Identity (Production)

```python
from azure.identity import DefaultAzureCredential
credential = DefaultAzureCredential()
```

`DefaultAzureCredential` tries multiple auth methods in order: environment variables, managed identity, Azure CLI, etc.

### Service Principal (CI/CD)

```bash
export AZURE_TENANT_ID="..."
export AZURE_CLIENT_ID="..."
export AZURE_CLIENT_SECRET="..."
```

---

## Your First Agent (Python)

### Environment Variables

```bash
export AZURE_AI_PROJECT_ENDPOINT="https://your-project.openai.azure.com"
export AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME="gpt-4o"
```

### Minimal Agent

```python
import asyncio
import os
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential

async def main():
    client = AzureOpenAIResponsesClient(
        project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
        deployment_name=os.environ["AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME"],
        credential=AzureCliCredential(),
    )

    agent = client.as_agent(
        name="HelloAgent",
        instructions="You are a friendly assistant. Keep your answers brief.",
    )

    # Non-streaming
    result = await agent.run("What is the capital of France?")
    print(f"Agent: {result}")

    # Streaming
    print("\nStreaming: ", end="")
    async for chunk in agent.run("Tell me a fun fact.", stream=True):
        if chunk.text:
            print(chunk.text, end="", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Your First Agent (.NET)

```csharp
using Azure.AI.OpenAI;
using Azure.Identity;
using Microsoft.Agents.AI;

var endpoint = Environment.GetEnvironmentVariable("AZURE_OPENAI_ENDPOINT")!;
var deploymentName = Environment.GetEnvironmentVariable("AZURE_OPENAI_DEPLOYMENT_NAME") ?? "gpt-4o-mini";

AIAgent agent = new AzureOpenAIClient(new Uri(endpoint), new AzureCliCredential())
    .GetChatClient(deploymentName)
    .AsAIAgent(
        instructions: "You are a friendly assistant.",
        name: "HelloAgent"
    );

// Non-streaming
Console.WriteLine(await agent.RunAsync("What is the largest city in France?"));

// Streaming
await foreach (var update in agent.RunStreamingAsync("Tell me a joke."))
{
    Console.Write(update);
}
```

---

## Provider-Specific Setup

### GitHub Models (Free — Great for Testing)

```bash
export GITHUB_TOKEN="your-github-personal-access-token"
export GITHUB_MODEL="gpt-4o"
```

```python
from agent_framework.github import GitHubModelsChatClient

client = GitHubModelsChatClient(
    token=os.environ["GITHUB_TOKEN"],
    model=os.environ.get("GITHUB_MODEL", "gpt-4o"),
)
agent = client.as_agent(name="GitHubAgent", instructions="You are helpful.")
```

### OpenAI Direct

```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL="gpt-4o-mini"
```

```python
from openai import OpenAIClient

client = OpenAIClient(api_key=os.environ["OPENAI_API_KEY"])
chat_client = client.get_chat_client(os.environ.get("OPENAI_MODEL", "gpt-4o-mini"))
agent = chat_client.as_agent(name="OpenAIAgent", instructions="You are helpful.")
```

### Anthropic Claude

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

```python
from agent_framework.anthropic import AnthropicChatClient

client = AnthropicChatClient(
    api_key=os.environ["ANTHROPIC_API_KEY"],
    model="claude-3-5-sonnet-20241022",
)
agent = client.as_agent(name="ClaudeAgent", instructions="You are helpful.")
```

### Ollama (Local)

```bash
# Install and start Ollama first
ollama pull llama3.1
ollama serve
```

```python
from agent_framework.ollama import OllamaChatClient

client = OllamaChatClient(
    base_url="http://localhost:11434",
    model="llama3.1",
)
agent = client.as_agent(name="LocalAgent", instructions="You are helpful.")
```

---

## Development Environment

### Recommended Setup

```bash
# Clone framework (optional — for samples)
git clone https://github.com/microsoft/agent-framework.git
cd agent-framework/python

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install
pip install agent-framework --pre
pip install python-dotenv  # For .env file support

# For development
pip install pytest pytest-asyncio
```

### Project .env File

```bash
# .env
AZURE_AI_PROJECT_ENDPOINT=https://your-project.openai.azure.com
AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME=gpt-4o
```

Load in code:
```python
from dotenv import load_dotenv
load_dotenv()
```

---

## Running Samples

```bash
# Clone samples repo
git clone https://github.com/microsoft/Agent-Framework-Samples.git
cd Agent-Framework-Samples

# Progressive tutorial
cd python/samples/01-get-started
python 01_hello_agent.py     # Basic agent
python 02_add_tools.py       # Function tools
python 03_multi_turn.py      # Sessions
python 04_memory.py          # Context providers
python 05_first_workflow.py  # Workflows
python 06_host_your_agent.py # Deployment

# Advanced samples
cd ../02-agents               # Agent patterns
cd ../03-workflows            # Workflow patterns
cd ../04-hosting              # Deployment patterns
cd ../05-end-to-end           # Full applications
```

### Official Sample Repositories

| Repository | Focus |
|-----------|-------|
| `microsoft/agent-framework` | SDK source + basic samples |
| `microsoft/Agent-Framework-Samples` | Comprehensive tutorial samples |
| `Azure-Samples/python-ai-agent-frameworks-demos` | Azure-specific demos |

---

## Troubleshooting First Agent

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `ModuleNotFoundError: agent_framework` | Package not installed | `pip install agent-framework --pre` |
| `InvalidAuthenticationTokenError` | Not logged in | `az login` |
| `ResourceNotFoundError` | Wrong endpoint/deployment | Copy exact values from Azure Portal |
| `Connection refused` (Ollama) | Ollama not running | `ollama serve` |
| `GITHUB_TOKEN not set` | Missing env var | Create GitHub PAT and export it |
| Hangs on first call | Network/firewall issue | Check proxy settings |
