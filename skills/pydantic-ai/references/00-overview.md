# Pydantic AI — Overview

> Source: [pydantic.dev/docs/ai/overview](https://pydantic.dev/docs/ai/overview/) | v1.107.0

## Table of Contents

- [What Is Pydantic AI](#what-is-pydantic-ai)
- [Core Architecture](#core-architecture)
- [Key Concepts](#key-concepts)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Provider Support](#provider-support)
- [When to Use Pydantic AI](#when-to-use-pydantic-ai)
- [Comparison With Other Frameworks](#comparison-with-other-frameworks)

## What Is Pydantic AI

Pydantic AI is a Python agent framework from the Pydantic team that brings FastAPI-style developer ergonomics to GenAI application development. It provides type-safe agents, structured outputs validated by Pydantic, dependency injection, function tools, lifecycle hooks, and a capabilities system — all with full IDE autocomplete and static type checking.

Key differentiators:

- **Built by the Pydantic team** — leverages the validation library used across OpenAI SDK, Anthropic SDK, LangChain, and most AI frameworks
- **Model-agnostic** — native support for OpenAI, Anthropic, Google Gemini, Groq, Mistral, Ollama, Bedrock, and 20+ providers
- **Type-safe** — agents are generic over dependency and output types, caught at write-time by mypy/pyright
- **Structured outputs** — Pydantic models as output types with automatic validation and retry
- **Dependency injection** — typed `RunContext` provides runtime data to tools, prompts, and validators
- **Capabilities** — composable bundles of tools, hooks, and instructions (on-demand loading for token efficiency)
- **MCP support** — both as client (connect to MCP servers) and server (expose agents as MCP tools)
- **Integrated observability** — first-class Logfire/OpenTelemetry integration for traces, spans, and debugging
- **Evaluation framework** — Pydantic Evals for systematic testing with datasets, evaluators, and online monitoring

## Core Architecture

```
Agent
├── Model (provider abstraction)
├── Instructions / System Prompts
├── Dependencies (typed, injected via RunContext)
├── Tools (function tools, native tools, MCP tools)
├── Capabilities (reusable behavior bundles)
├── Hooks (lifecycle interceptors)
├── Output Type (Pydantic model / scalar / union / function)
└── Run Methods
    ├── run()              — async
    ├── run_sync()         — synchronous
    ├── run_stream()       — streaming text/structured
    ├── run_stream_events() — all events
    └── iter()             — node-by-node iteration
```

An **Agent** is the primary interface. It encapsulates model configuration, instructions, tools, dependencies, and output types. Agents are created once and reused across multiple runs — they are stateless containers for configuration.

A **Run** is a single invocation of an agent with a user prompt and optional dependencies. The agent loop sends messages to the model, processes tool calls, validates outputs, and returns a typed result.

## Key Concepts

| Concept | Purpose |
|---------|---------|
| **Agent** | Container for model, instructions, tools, deps, output type |
| **RunContext** | Typed access to dependencies during tool execution and prompt generation |
| **Tool** | Function the model can call to retrieve information or perform actions |
| **Capability** | Reusable bundle of tools + hooks + instructions |
| **Output Type** | Pydantic model or scalar that the agent must return (validated) |
| **Hooks** | Lifecycle interceptors for model requests, tool calls, and output validation |
| **ModelSettings** | Temperature, max_tokens, timeout, and other generation parameters |

## Installation

```bash
# Full install — all providers + Logfire
pip install pydantic-ai

# Slim install — core only, add provider extras individually
pip install pydantic-ai-slim
pip install 'pydantic-ai-slim[openai]'
pip install 'pydantic-ai-slim[anthropic]'
pip install 'pydantic-ai-slim[google]'

# Optional extras
pip install 'pydantic-ai[ui]'       # Web chat UI (Starlette)
pip install 'pydantic-ai[evals]'    # Pydantic Evals framework
pip install 'pydantic-ai[dbos]'     # DBOS durable execution
pip install 'pydantic-ai[prefect]'  # Prefect durable execution
pip install 'pydantic-ai[a2a]'      # Agent-to-Agent protocol
```

Requires Python >= 3.10.

## Quick Start

### Minimal Agent

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-5.2')
result = agent.run_sync('What is the capital of France?')
print(result.output)
# Paris
```

### Structured Output

```python
from pydantic import BaseModel
from pydantic_ai import Agent

class CityLocation(BaseModel):
    city: str
    country: str

agent = Agent('openai:gpt-5.2', output_type=CityLocation)
result = agent.run_sync('Where were the 2012 Olympics held?')
print(result.output)
# city='London' country='United Kingdom'
```

### Agent With Tools and Dependencies

```python
from dataclasses import dataclass
import httpx
from pydantic_ai import Agent, RunContext

@dataclass
class Deps:
    client: httpx.AsyncClient
    api_key: str

agent = Agent('anthropic:claude-sonnet-4-6', deps_type=Deps)

@agent.tool
async def search_api(ctx: RunContext[Deps], query: str) -> str:
    """Search the external API."""
    resp = await ctx.deps.client.get(
        'https://api.example.com/search',
        params={'q': query},
        headers={'Authorization': f'Bearer {ctx.deps.api_key}'},
    )
    resp.raise_for_status()
    return resp.text

async def main():
    async with httpx.AsyncClient() as client:
        result = await agent.run(
            'Find info about Pydantic',
            deps=Deps(client=client, api_key='sk-...'),
        )
        print(result.output)
```

## Provider Support

### Native Providers

| Provider | Model String | Example |
|----------|-------------|---------|
| OpenAI | `openai:gpt-5.2` | `Agent('openai:gpt-5.2')` |
| Anthropic | `anthropic:claude-sonnet-4-6` | `Agent('anthropic:claude-sonnet-4-6')` |
| Google Gemini | `google:gemini-3-flash-preview` | `Agent('google:gemini-3-flash-preview')` |
| xAI / Grok | `xai:grok-3` | `Agent('xai:grok-3')` |
| AWS Bedrock | `bedrock:...` | `Agent('bedrock:us.anthropic.claude-sonnet-4-6')` |
| Groq | `groq:llama-4-scout` | `Agent('groq:llama-4-scout')` |
| Mistral | `mistral:mistral-large` | `Agent('mistral:mistral-large')` |
| Cohere | `cohere:command-r-plus` | `Agent('cohere:command-r-plus')` |
| Ollama | `ollama:llama3.3` | `Agent('ollama:llama3.3')` |

### OpenAI-Compatible Providers

Azure AI Foundry, DeepSeek, Fireworks AI, Together AI, OpenRouter, LiteLLM, Perplexity, SambaNova, and more — all work via `OpenAIChatModel` with custom `base_url`.

## When to Use Pydantic AI

**Good fit:**
- Python-first AI agent development
- Applications requiring validated, structured LLM output
- Multi-model systems that need provider abstraction
- Teams already using Pydantic/FastAPI patterns
- Production agents needing observability and evals

**Consider alternatives when:**
- You need a JavaScript/TypeScript framework (use Vercel AI SDK or Mastra)
- You want a low-code/visual agent builder (use LangGraph Studio or CrewAI)
- Your use case is pure RAG without agents (LlamaIndex may be more focused)

## Comparison With Other Frameworks

| Feature | Pydantic AI | LangChain | CrewAI |
|---------|-------------|-----------|--------|
| Type safety | Full generic typing | Partial | Minimal |
| Output validation | Native Pydantic | Via output parsers | Basic |
| Dependency injection | Built-in RunContext | Manual | None |
| Capabilities system | Yes (on-demand) | Chains/tools | Agents/tasks |
| MCP support | Client + server | Client only | None |
| Observability | Logfire + OTel | LangSmith | Basic logging |
| Testing | TestModel + FunctionModel | Manual mocking | Manual |

## Common Pitfalls

- **Forgetting `deps=`** — if your agent has `deps_type`, you must pass `deps=` to every run call
- **Sync vs async confusion** — `run_sync()` works even with async tools (they run in the event loop); use `run()` in async contexts
- **Model string typos** — model strings are `provider:model_name` (e.g., `openai:gpt-5.2`, not `gpt-5.2`)
- **Output type without instructions** — structured output works better with clear instructions explaining what to extract

## Related

- `01-agents.md` — Agent creation and configuration
- `02-dependencies.md` — Dependency injection patterns
- `08-models.md` — Model provider configuration
