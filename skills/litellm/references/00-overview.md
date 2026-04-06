# LiteLLM — Overview & Quickstart

> Source: https://docs.litellm.ai • Written for litellm v1.52.x

## What it is

LiteLLM is a Python library and proxy server that gives you a **single, OpenAI-compatible interface for 100+ LLM providers** — OpenAI, Anthropic, Azure OpenAI, AWS Bedrock, Google Vertex AI, Cohere, Mistral, Groq, Together, Ollama, vLLM, Hugging Face, Replicate, and many more.

You write your code against `litellm.completion(...)` once. To switch providers you change a model string — no other code changes.

## Two ways to use it

There are two distinct usage modes. Pick based on your architecture.

### 1. SDK mode (`pip install litellm`)
Import `litellm` directly into your Python app and call `completion()` / `acompletion()`. Best for:
- Single-application backends
- Scripts and notebooks
- Agent frameworks already running in Python

### 2. Proxy mode (`pip install 'litellm[proxy]'`)
Run `litellm` as a standalone HTTP server. Your apps (any language) call it as if it were OpenAI:
```
POST http://localhost:4000/v1/chat/completions
```
Best for:
- Multi-language stacks (TypeScript, Go, etc. talking to one gateway)
- Centralized key management, budgets, rate limits
- Multi-tenant systems with virtual API keys
- Logging/observability across all teams

## Install

```bash
# SDK
pip install litellm

# Proxy (includes server, DB, auth)
pip install 'litellm[proxy]'

# Specific provider extras (optional — most providers work with base install)
pip install 'litellm[extra_proxy]'
```

## Quickstart — SDK

```python
import os
from litellm import completion

os.environ["OPENAI_API_KEY"] = "sk-..."
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-..."

# OpenAI
resp = completion(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello"}],
)
print(resp.choices[0].message.content)

# Anthropic — same code, different model string
resp = completion(
    model="anthropic/claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": "Hello"}],
)
```

The response object is **always OpenAI-shaped** — `choices[0].message.content`, `usage.prompt_tokens`, etc. — regardless of provider.

## Quickstart — Proxy

Create `config.yaml`:
```yaml
model_list:
  - model_name: gpt-4o-mini
    litellm_params:
      model: openai/gpt-4o-mini
      api_key: os.environ/OPENAI_API_KEY

  - model_name: claude-sonnet
    litellm_params:
      model: anthropic/claude-3-5-sonnet-20241022
      api_key: os.environ/ANTHROPIC_API_KEY
```

Run it:
```bash
litellm --config config.yaml --port 4000
```

Call it like OpenAI:
```python
from openai import OpenAI

client = OpenAI(api_key="anything", base_url="http://localhost:4000")
client.chat.completions.create(
    model="claude-sonnet",  # the alias from config.yaml
    messages=[{"role": "user", "content": "Hello"}],
)
```

## Core concepts

- **Model string** — Always `provider/model_id` (e.g. `anthropic/claude-3-5-sonnet`, `bedrock/anthropic.claude-3-sonnet-20240229-v1:0`). For OpenAI the prefix is optional.
- **Unified response** — All providers return an OpenAI `ChatCompletion`-shaped object.
- **Unified params** — `temperature`, `max_tokens`, `tools`, `response_format`, etc. are translated per-provider automatically.
- **Drop-in replacement** — `from litellm import completion` swaps cleanly with `openai.chat.completions.create`.
- **Router** (SDK) — Load-balance one logical model name across multiple deployments.
- **Proxy** — Same router logic, but as a network gateway.

## When to use which

| Need | Use |
|------|-----|
| Switching one app between providers | SDK |
| Adding fallbacks to a single Python service | SDK or Router |
| Multi-language apps sharing one gateway | Proxy |
| Centralized cost/budget per team | Proxy |
| Local dev tinkering | SDK |
| Production multi-tenant LLM platform | Proxy |

## Common pitfalls

- **Forgetting the provider prefix** — `completion(model="claude-3-5-sonnet")` will fail; use `anthropic/claude-3-5-sonnet-20241022`.
- **Mixing env vars** — Each provider needs its own env var (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `AWS_ACCESS_KEY_ID`, etc.). LiteLLM does NOT alias them.
- **Not pinning version** — LiteLLM ships frequently; pin `litellm==1.52.x` or similar in production.
- **Using SDK retries AND Router retries** — They compound; pick one layer.

## Related references
- Completion API → `01-completion-api.md`
- Provider-specific setup → `02-providers.md`
- Proxy deployment → `06-proxy-server.md`
