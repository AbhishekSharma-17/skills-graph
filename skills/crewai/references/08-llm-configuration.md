# CrewAI LLM Configuration

> Source: https://docs.crewai.com/en/concepts/llms

## Overview

CrewAI provides native SDK integrations for OpenAI, Anthropic, Google (Gemini), Azure, and AWS Bedrock. All other providers are supported via LiteLLM. Each agent can use a different model, enabling cost optimization and capability matching.

## LLM Class

```python
from crewai import LLM

llm = LLM(
    model="openai/gpt-4o",
    temperature=0.7,
    max_tokens=4096,
    top_p=0.9,
    frequency_penalty=0.0,
    presence_penalty=0.0,
    seed=42,
    api_key="sk-...",       # Or use env var
    base_url=None,          # Custom endpoint
    timeout=300,
)
```

## Core Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | str | required | Model identifier (provider/model-name) |
| `temperature` | float | 0.7 | Randomness (0.0-2.0) |
| `max_tokens` | int | None | Max output tokens |
| `top_p` | float | 1.0 | Nucleus sampling |
| `frequency_penalty` | float | 0.0 | Penalize repeated tokens |
| `presence_penalty` | float | 0.0 | Penalize repeated topics |
| `seed` | int | None | Reproducible outputs |
| `api_key` | str | None | Provider API key (or env var) |
| `base_url` | str | None | Custom API endpoint |
| `timeout` | int | None | Request timeout in seconds |
| `stop` | list[str] | None | Stop sequences |

## Provider Configuration

### OpenAI

```python
from crewai import LLM

# Using environment variable (recommended)
# export OPENAI_API_KEY="sk-..."
llm = LLM(model="openai/gpt-4o")

# Explicit key
llm = LLM(model="openai/gpt-4o", api_key="sk-...")

# Available models
llm_4o = LLM(model="openai/gpt-4o")
llm_4o_mini = LLM(model="openai/gpt-4o-mini")
llm_o1 = LLM(model="openai/o1")
llm_o1_mini = LLM(model="openai/o1-mini")
```

### Anthropic

```python
# export ANTHROPIC_API_KEY="sk-ant-..."
llm = LLM(
    model="anthropic/claude-sonnet-4-20250514",
    max_tokens=4096,  # Required for Anthropic
)

# Available models
llm_opus = LLM(model="anthropic/claude-opus-4-20250514", max_tokens=4096)
llm_sonnet = LLM(model="anthropic/claude-sonnet-4-20250514", max_tokens=4096)
llm_haiku = LLM(model="anthropic/claude-haiku-4-5-20251001", max_tokens=4096)
```

### Google Gemini

```python
# export GOOGLE_API_KEY="..."
llm = LLM(model="google/gemini-2.0-flash")

# Available models
llm_pro = LLM(model="google/gemini-2.0-pro")
llm_flash = LLM(model="google/gemini-2.0-flash")
```

### Azure OpenAI

```python
# export AZURE_API_KEY="..."
# export AZURE_API_BASE="https://your-resource.openai.azure.com"
# export AZURE_API_VERSION="2024-02-15-preview"
llm = LLM(
    model="azure/your-deployment-name",
    api_key="...",
    base_url="https://your-resource.openai.azure.com",
)
```

### AWS Bedrock

```python
# Requires AWS credentials configured
llm = LLM(
    model="bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0",
)
```

### Ollama (Local)

```python
# Ollama must be running locally
llm = LLM(
    model="ollama/llama3.1",
    base_url="http://localhost:11434",
)

# With custom parameters
llm = LLM(
    model="ollama/mixtral",
    base_url="http://localhost:11434",
    temperature=0.3,
)
```

### Groq

```python
# export GROQ_API_KEY="..."
llm = LLM(model="groq/llama-3.1-70b-versatile")
```

### Together AI

```python
# export TOGETHER_API_KEY="..."
llm = LLM(model="together_ai/meta-llama/Llama-3.1-70B-Instruct-Turbo")
```

### OpenRouter

```python
# export OPENROUTER_API_KEY="..."
llm = LLM(
    model="openrouter/anthropic/claude-sonnet-4-20250514",
    base_url="https://openrouter.ai/api/v1",
)
```

## Environment Variable Configuration

The simplest approach — set environment variables:

```bash
# .env file
OPENAI_API_KEY=sk-...
OPENAI_MODEL_NAME=gpt-4o          # Default model for all agents
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
```

```python
from dotenv import load_dotenv
load_dotenv()

# Agents will use OPENAI_MODEL_NAME by default
agent = Agent(role="...", goal="...", backstory="...")
```

## Per-Agent Model Assignment

```python
from crewai import Agent, LLM

# Cheap model for simple tasks
classifier = Agent(
    role="Classifier",
    goal="Classify incoming requests",
    backstory="Expert at categorization.",
    llm="openai/gpt-4o-mini",  # String shorthand
)

# Powerful model for complex reasoning
analyst = Agent(
    role="Senior Analyst",
    goal="Perform deep analysis",
    backstory="Expert with decades of experience.",
    llm=LLM(model="anthropic/claude-sonnet-4-20250514", max_tokens=4096, temperature=0.2),
)

# Local model for privacy-sensitive tasks
privacy_agent = Agent(
    role="Data Handler",
    goal="Process sensitive data locally",
    backstory="Security-focused data processor.",
    llm=LLM(model="ollama/llama3.1", base_url="http://localhost:11434"),
)
```

## Cost Optimization Strategies

```python
# Strategy 1: Tiered models
cheap_llm = LLM(model="openai/gpt-4o-mini")     # $0.15/1M input
standard_llm = LLM(model="openai/gpt-4o")        # $2.50/1M input
premium_llm = LLM(model="anthropic/claude-sonnet-4-20250514", max_tokens=4096)

# Simple tasks → cheap model
formatter = Agent(role="Formatter", ..., llm=cheap_llm)

# Standard tasks → balanced model
researcher = Agent(role="Researcher", ..., llm=standard_llm)

# Critical tasks → premium model
decision_maker = Agent(role="Decision Maker", ..., llm=premium_llm)
```

## Custom API Endpoints

```python
# Self-hosted model (vLLM, TGI, etc.)
llm = LLM(
    model="openai/my-finetuned-model",
    base_url="http://my-server:8000/v1",
    api_key="not-needed",
)

# LiteLLM proxy
llm = LLM(
    model="openai/gpt-4o",
    base_url="http://localhost:4000",  # LiteLLM proxy
    api_key="sk-proxy-key",
)
```

## Model Selection Guidelines

| Task Type | Recommended Model | Reasoning |
|-----------|------------------|-----------|
| Classification/routing | gpt-4o-mini, Haiku | Fast, cheap, sufficient |
| Research/analysis | gpt-4o, Sonnet | Balanced quality + speed |
| Complex reasoning | o1, Opus | Maximum capability |
| Code generation | gpt-4o, Sonnet | Good at structured output |
| Creative writing | Sonnet, gpt-4o | Creative + coherent |
| Manager (hierarchical) | gpt-4o, Sonnet | Needs strong planning |
| Privacy-sensitive | Ollama/local | Data stays local |

## Common Pitfalls

1. **Missing max_tokens for Anthropic** — Anthropic requires explicit max_tokens
2. **Same expensive model everywhere** — Use tiered models for cost control
3. **Ignoring rate limits** — Set max_rpm on crew or agents
4. **No timeout** — Long-running calls can hang; set timeout
5. **Hardcoded API keys** — Always use environment variables
6. **Wrong model prefix** — Must include provider (openai/, anthropic/, etc.)
