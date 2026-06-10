# Models and Providers

> Source: [pydantic.dev/docs/ai/models/overview](https://pydantic.dev/docs/ai/models/overview/)

## Table of Contents

- [Overview](#overview)
- [Model String Format](#model-string-format)
- [Native Providers](#native-providers)
- [OpenAI-Compatible Providers](#openai-compatible-providers)
- [Explicit Model Configuration](#explicit-model-configuration)
- [Fallback Models](#fallback-models)
- [Concurrency Limiting](#concurrency-limiting)
- [Model Settings](#model-settings)
- [Overriding Models Per Run](#overriding-models-per-run)
- [Common Pitfalls](#common-pitfalls)

## Overview

Pydantic AI abstracts model providers behind a unified interface. Models are specified as `provider:model_name` strings or as explicit model class instances. The framework handles authentication, request formatting, and response parsing for each provider.

Key terms:
- **Model** — vendor-specific class that handles API communication
- **Provider** — authentication and connection handler
- **Profile** — request construction specification

## Model String Format

The simplest way to specify a model:

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-5.2')
agent = Agent('anthropic:claude-sonnet-4-6')
agent = Agent('google:gemini-3-flash-preview')
```

Format: `provider:model_name`

## Native Providers

### OpenAI

```python
agent = Agent('openai:gpt-5.2')
agent = Agent('openai:gpt-5-mini')
agent = Agent('openai:o3')
```

Set `OPENAI_API_KEY` environment variable, or pass via provider config.

### Anthropic

```python
agent = Agent('anthropic:claude-opus-4-6')
agent = Agent('anthropic:claude-sonnet-4-6')
agent = Agent('anthropic:claude-haiku-4-5')
```

Set `ANTHROPIC_API_KEY` environment variable.

### Google Gemini

```python
agent = Agent('google:gemini-3-flash-preview')
agent = Agent('google:gemini-2.5-pro-preview')
```

Set `GOOGLE_API_KEY` or use Application Default Credentials.

### xAI / Grok

```python
agent = Agent('xai:grok-3')
```

### AWS Bedrock

```python
agent = Agent('bedrock:us.anthropic.claude-sonnet-4-6')
```

Uses boto3 credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION).

### Groq

```python
agent = Agent('groq:llama-4-scout')
```

### Mistral

```python
agent = Agent('mistral:mistral-large')
```

### Cohere

```python
agent = Agent('cohere:command-r-plus')
```

### Ollama (Local)

```python
agent = Agent('ollama:llama3.3')
```

Requires Ollama running locally on port 11434.

### Hugging Face

```python
agent = Agent('huggingface:meta-llama/Llama-3.3-70B-Instruct')
```

## OpenAI-Compatible Providers

Services that implement the OpenAI API work via `OpenAIChatModel` with a custom `base_url`:

```python
from pydantic_ai.models.openai import OpenAIChatModel

# DeepSeek
model = OpenAIChatModel(
    'deepseek-chat',
    provider='deepseek',
)
agent = Agent(model)

# Together AI
model = OpenAIChatModel(
    'meta-llama/Llama-3.3-70B-Instruct',
    provider='together-ai',
)

# Azure OpenAI
model = OpenAIChatModel(
    'gpt-4o',
    provider='azure',
)
```

Compatible services: Azure AI Foundry, DeepSeek, Fireworks AI, Together AI, OpenRouter, LiteLLM, Perplexity, SambaNova, Nebius, GitHub Models.

## Explicit Model Configuration

For fine-grained control:

```python
from pydantic_ai.models.openai import OpenAIChatModel
from openai import AsyncOpenAI

client = AsyncOpenAI(
    api_key='sk-...',
    base_url='https://custom-endpoint.com/v1',
)
model = OpenAIChatModel('gpt-5.2', openai_client=client)
agent = Agent(model)
```

### Anthropic With Custom Client

```python
from pydantic_ai.models.anthropic import AnthropicModel
from anthropic import AsyncAnthropic

client = AsyncAnthropic(api_key='sk-ant-...')
model = AnthropicModel('claude-sonnet-4-6', anthropic_client=client)
agent = Agent(model)
```

## Fallback Models

Automatically fall back to another provider on failure:

```python
from pydantic_ai.models.fallback import FallbackModel

model = FallbackModel(
    'openai:gpt-5.2',
    'anthropic:claude-sonnet-4-6',
)
agent = Agent(model)
```

Tries models in order — if the first fails, falls back to the next.

## Concurrency Limiting

Limit concurrent requests to a model:

```python
from pydantic_ai import ConcurrencyLimitedModel

model = ConcurrencyLimitedModel('openai:gpt-5.2', limiter=5)
agent = Agent(model)
```

Useful for rate-limited APIs or controlling costs.

## Model Settings

Control generation parameters:

```python
from pydantic_ai import Agent, ModelSettings

agent = Agent(
    'openai:gpt-5.2',
    model_settings=ModelSettings(
        temperature=0.0,
        max_tokens=1000,
        top_p=0.9,
        timeout=30,
    )
)
```

### Common Settings

| Setting | Type | Description |
|---------|------|-------------|
| `temperature` | `float` | Randomness (0.0 = deterministic) |
| `max_tokens` | `int` | Max output tokens |
| `top_p` | `float` | Nucleus sampling |
| `timeout` | `float` | Request timeout in seconds |
| `thinking` | `str` | Thinking effort level (for supported models) |
| `extra_body` | `dict` | Provider-specific parameters |

### Dynamic Settings

```python
from pydantic_ai import RunContext

agent = Agent(
    'openai:gpt-5.2',
    model_settings=lambda ctx: ModelSettings(
        temperature=0.0 if ctx.run_step <= 1 else 0.5
    )
)
```

## Overriding Models Per Run

```python
agent = Agent('openai:gpt-5-mini')  # Default: cheap model

# Override for a specific run
result = agent.run_sync(
    'Complex analysis task',
    model='openai:gpt-5.2',  # Use expensive model
)
```

## Common Pitfalls

- **Missing API keys** — set the provider's environment variable (e.g., `OPENAI_API_KEY`) or pass via client config
- **Model string typos** — it's `openai:gpt-5.2`, not `gpt-5.2` or `openai/gpt-5.2`
- **Ollama not running** — Ollama models require the Ollama server running locally
- **Native features** — not all models support all features (e.g., native structured output, thinking); check provider docs
- **FallbackModel ordering** — place the preferred model first; fallback models are tried in order
- **Rate limits** — use `ConcurrencyLimitedModel` when making many parallel requests

## Related

- `01-agents.md` — Agent creation with model configuration
- `00-overview.md` — Provider support table
- `12-logfire-observability.md` — Monitoring model calls
