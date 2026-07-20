# Instructor — Provider Integrations

> Source: https://python.useinstructor.com/integrations | v1.15.4

## Table of Contents

- [Provider Overview](#provider-overview)
- [OpenAI](#openai)
- [Anthropic (Claude)](#anthropic-claude)
- [Ollama (Local Models)](#ollama-local-models)
- [Google Gemini](#google-gemini)
- [LiteLLM (Universal Proxy)](#litellm-universal-proxy)
- [Other Providers](#other-providers)
- [Provider-Specific Tips](#provider-specific-tips)

## Provider Overview

Instructor uses a unified `from_provider()` API. The model string format is `provider/model-name`:

```python
import instructor

# Each creates a client with provider-optimal defaults
openai_client = instructor.from_provider("openai/gpt-4o-mini")
claude_client = instructor.from_provider("anthropic/claude-4-5-haiku-latest")
ollama_client = instructor.from_provider("ollama/llama3.1")
gemini_client = instructor.from_provider("google/gemini-2.5-flash")
```

## OpenAI

### Installation

```bash
pip install instructor  # OpenAI included by default
```

### Setup

```python
import instructor

# Uses OPENAI_API_KEY env var
client = instructor.from_provider("openai/gpt-4o-mini")

# Or explicit key
import openai
oai = openai.OpenAI(api_key="sk-...")
client = instructor.from_openai(oai)
```

### Recommended Modes

| Mode | Use Case |
|------|----------|
| `TOOLS` (default) | Most structured output tasks |
| `TOOLS_STRICT` | Guaranteed schema conformance |
| `RESPONSES_TOOLS` | Responses API features (web search, etc.) |
| `JSON_O1` | O1 reasoning models |

### Structured Outputs (TOOLS_STRICT)

```python
from instructor import Mode

client = instructor.from_provider("openai/gpt-4o-mini", mode=Mode.TOOLS_STRICT)

# Response is guaranteed to match the schema — no format retries needed
user = client.create(
    response_model=User,
    messages=[{"role": "user", "content": "Extract: Jason, 25"}],
)
```

### Batch Processing

```python
from instructor.batch import BatchProcessor

processor = BatchProcessor("openai/gpt-4o-mini", User)
# 50% cost savings for non-urgent requests
```

### Model Recommendations

| Model | When to Use |
|-------|------------|
| `gpt-4o-mini` | Cost-efficient, simple to moderate schemas |
| `gpt-4o` | Complex schemas, high accuracy needed |
| `o1` / `o3` | Complex reasoning before extraction |

## Anthropic (Claude)

### Installation

```bash
pip install "instructor[anthropic]"
```

### Setup

```python
import instructor

# Uses ANTHROPIC_API_KEY env var
client = instructor.from_provider("anthropic/claude-4-5-haiku-latest")

# Async
async_client = instructor.from_provider(
    "anthropic/claude-4-5-haiku-latest",
    async_client=True,
)
```

### Supported Modes

- `Mode.TOOLS` (default) — uses Claude's tool use API
- `Mode.JSON` — text-based JSON extraction

### Parallel Tools (Auto-Detected)

When using `Iterable[Union[...]]` response models, `Mode.TOOLS` automatically enables parallel tool calls:

```python
from typing import Union, Iterable

class Weather(BaseModel):
    location: str
    temp: float

class Event(BaseModel):
    name: str
    date: str

results = client.create(
    response_model=Iterable[Union[Weather, Event]],
    messages=[{"role": "user", "content": "NYC is 72F. Conference on March 5."}],
)
```

### Extended Thinking

Enable Claude's extended thinking for complex reasoning before structured output:

```python
result = client.create(
    response_model=ComplexAnalysis,
    messages=[{"role": "user", "content": "Analyze this data..."}],
    thinking={"type": "enabled", "budget_tokens": 1024},
)
```

### Prompt Caching

Cache expensive inputs (images, PDFs, long context) to reduce costs:

```python
from instructor.multimodal import ImageWithCacheControl, PdfWithCacheControl

response = client.create(
    response_model=Invoice,
    messages=[{
        "role": "user",
        "content": [
            "Extract invoice data",
            PdfWithCacheControl.from_path("invoice.pdf"),
        ],
    }],
)
```

### Model Recommendations

| Model | When to Use |
|-------|------------|
| `claude-4-5-haiku-latest` | Fast, cost-efficient extraction |
| `claude-4-5-sonnet-latest` | Complex schemas, nuanced extraction |
| `claude-4-5-opus-latest` | Highest accuracy, complex reasoning |

## Ollama (Local Models)

### Installation

```bash
# Install Ollama: https://ollama.com
ollama pull llama3.1
pip install instructor
```

### Setup

```python
import instructor

client = instructor.from_provider("ollama/llama3.1")

user = client.create(
    response_model=User,
    messages=[{"role": "user", "content": "Extract: Jason is 25"}],
    max_retries=2,
    timeout=30.0,  # Important for local models
)
```

### Mode Auto-Selection

Instructor detects model capabilities:

| Model | Auto Mode |
|-------|-----------|
| llama3.1, llama3.2 | TOOLS |
| mistral-nemo | TOOLS |
| qwen2.5 | TOOLS |
| llama2, phi3 | JSON |

Override manually:

```python
client = instructor.from_provider("ollama/phi3", mode=instructor.Mode.JSON)
```

### Timeout Handling

Timeouts apply across all retry attempts combined:

```python
client = instructor.from_provider("ollama/llama3.1")
result = client.create(
    response_model=User,
    messages=[...],
    max_retries=2,
    timeout=30.0,  # Total 30s across all attempts
)
```

### Async Ollama

```python
async_client = instructor.from_provider("ollama/llama3.1", async_client=True)
user = await async_client.create(response_model=User, messages=[...])
```

## Google Gemini

### Installation

```bash
pip install "instructor[google-generativeai]"
```

### Setup

```python
import instructor

# Uses GOOGLE_API_KEY env var
client = instructor.from_provider("google/gemini-2.5-flash")

user = client.create(
    response_model=User,
    messages=[{"role": "user", "content": "Extract: Jason is 25"}],
)
```

## LiteLLM (Universal Proxy)

LiteLLM provides a unified interface to 100+ LLM providers. Use it when you need provider-agnostic code:

### Installation

```bash
pip install "instructor[litellm]"
```

### Setup

```python
import instructor

# Routes to any LiteLLM-supported provider
client = instructor.from_provider("litellm/openai/gpt-4o-mini")
client = instructor.from_provider("litellm/anthropic/claude-4-5-haiku-latest")
client = instructor.from_provider("litellm/bedrock/anthropic.claude-v2")
```

## Other Providers

| Provider | Install | Model String |
|----------|---------|-------------|
| Mistral | `pip install "instructor[mistral]"` | `mistral/mistral-large-latest` |
| Cohere | `pip install "instructor[cohere]"` | `cohere/command-r-plus` |
| DeepSeek | (OpenAI compat) | `openai/deepseek-chat` with base_url |
| Fireworks | (OpenAI compat) | `openai/accounts/fireworks/...` |
| Together | (OpenAI compat) | `openai/meta-llama/...` |
| AWS Bedrock | `pip install "instructor[bedrock]"` | `bedrock/anthropic.claude-v2` |
| Vertex AI | `pip install "instructor[vertexai]"` | `vertexai/gemini-2.5-flash` |

## Provider-Specific Tips

1. **OpenAI** — use `TOOLS_STRICT` for production pipelines requiring 100% schema compliance
2. **Anthropic** — enable prompt caching for repeated large-context tasks; use extended thinking for complex reasoning
3. **Ollama** — always set `timeout`; use tool-capable models (llama3.1+) for best results
4. **Google** — Gemini Flash models offer the best cost/performance for simple schemas
5. **LiteLLM** — great for multi-provider failover, but adds a dependency layer
6. **All providers** — start with `from_provider()` (auto-mode), override mode only when needed
