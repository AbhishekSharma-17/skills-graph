# Instructor — Extraction Modes

> Source: https://python.useinstructor.com/modes-comparison | v1.15.4

## Table of Contents

- [Mode Overview](#mode-overview)
- [TOOLS Mode](#tools-mode)
- [JSON Mode](#json-mode)
- [MD_JSON Mode](#md_json-mode)
- [TOOLS_STRICT Mode](#tools_strict-mode)
- [PARALLEL_TOOLS Mode](#parallel_tools-mode)
- [RESPONSES_TOOLS Mode](#responses_tools-mode)
- [JSON_O1 Mode](#json_o1-mode)
- [JSON_SCHEMA Mode](#json_schema-mode)
- [Provider Support Matrix](#provider-support-matrix)
- [Mode Selection Guide](#mode-selection-guide)

## Mode Overview

Modes control how Instructor communicates the desired output schema to the LLM and how it parses the response. The right mode depends on your provider, model capabilities, and use case.

```python
import instructor

# Explicit mode
client = instructor.from_provider("openai/gpt-4o-mini", mode=instructor.Mode.TOOLS)

# Auto-detected (recommended for most cases)
client = instructor.from_provider("openai/gpt-4o-mini")
```

All modes are accessed via `instructor.Mode`:

```python
from instructor import Mode

Mode.TOOLS           # Function/tool calling
Mode.JSON            # JSON response format
Mode.MD_JSON         # JSON in markdown code blocks
Mode.TOOLS_STRICT    # OpenAI structured outputs (constrained grammar)
Mode.PARALLEL_TOOLS  # Multiple tool calls in one response
Mode.RESPONSES_TOOLS # OpenAI Responses API
Mode.JSON_O1         # For O1/reasoning models
Mode.JSON_SCHEMA     # Native JSON schema enforcement
```

## TOOLS Mode

Uses the provider's native function/tool calling API. The Pydantic model is converted into a tool schema, and the LLM responds by "calling" that tool with structured arguments.

```python
client = instructor.from_provider("openai/gpt-4o-mini", mode=Mode.TOOLS)

user = client.create(
    response_model=User,
    messages=[{"role": "user", "content": "Extract: Jason is 25"}],
)
```

**Strengths:**
- Most accurate for complex, nested schemas
- Best schema enforcement across providers
- Supports all Pydantic types and constraints

**Limitations:**
- Slightly more tokens than JSON modes
- Not all models support tool calling

**Best for:** Most use cases. This is the recommended default.

## JSON Mode

Instructs the LLM to output raw JSON matching the schema. Uses provider-specific JSON mode settings (e.g., `response_format={"type": "json_object"}` for OpenAI).

```python
client = instructor.from_provider("openai/gpt-4o-mini", mode=Mode.JSON)

user = client.create(
    response_model=User,
    messages=[{"role": "user", "content": "Extract: Jason is 25"}],
)
```

**Strengths:**
- Token-efficient
- Works across most providers and models
- Simpler API surface

**Limitations:**
- Less reliable for complex nested schemas
- Schema enforcement is hint-based, not grammar-constrained

**Best for:** Simple schemas, token-sensitive applications, models without tool support.

## MD_JSON Mode

Extracts JSON from markdown code blocks in the response. The LLM wraps its JSON output in ````json ... ``` fences.

```python
client = instructor.from_provider("openai/gpt-4o-mini", mode=Mode.MD_JSON)
```

**Strengths:**
- Works with models that don't support JSON mode or tools
- Compatible with vision models and some niche providers

**Limitations:**
- Least reliable extraction — depends on model formatting
- Can fail on malformed markdown

**Best for:** Fallback when TOOLS and JSON are unavailable.

## TOOLS_STRICT Mode

OpenAI-specific mode using constrained grammar sampling. The output is guaranteed to conform to the JSON schema — no validation retries needed for structural issues.

```python
client = instructor.from_provider("openai/gpt-4o-mini", mode=Mode.TOOLS_STRICT)

user = client.create(
    response_model=User,
    messages=[{"role": "user", "content": "Extract: Jason is 25"}],
)
```

**Strengths:**
- Guaranteed structural conformance (100% schema compliance)
- No retries needed for format errors
- Best accuracy for OpenAI models

**Limitations:**
- OpenAI only
- Restricts to a subset of JSON schema (no recursive types, limited unions)
- First request with a new schema may have higher latency

**Best for:** Production OpenAI pipelines where structural correctness is critical.

## PARALLEL_TOOLS Mode

Enables the LLM to make multiple tool calls in a single response. Useful for extracting multiple different types simultaneously.

```python
from typing import Union, Iterable

class Weather(BaseModel):
    location: str
    temp: float

class Stock(BaseModel):
    ticker: str
    price: float

client = instructor.from_provider("openai/gpt-4o-mini", mode=Mode.PARALLEL_TOOLS)

results = client.create(
    response_model=Iterable[Union[Weather, Stock]],
    messages=[{
        "role": "user",
        "content": "NYC weather is 72F. AAPL is at 198.50.",
    }],
)
```

**Note:** With Anthropic, `Mode.TOOLS` automatically detects when parallel tools are needed for `Iterable[Union[...]]` response models.

## RESPONSES_TOOLS Mode

Uses OpenAI's newer Responses API instead of Chat Completions. Offers improved caching and stateful context.

```python
client = instructor.from_provider("openai/gpt-4o-mini", mode=Mode.RESPONSES_TOOLS)
```

**Best for:** OpenAI applications that need Responses API features (web search, file search, computer use).

## JSON_O1 Mode

Designed for OpenAI's O1 reasoning models, which lack system message and tool support:

```python
client = instructor.from_provider("openai/o1", mode=Mode.JSON_O1)
```

**Best for:** O1 and O1-mini models only.

## JSON_SCHEMA Mode

Uses native JSON Schema enforcement when the provider supports it at the API level:

```python
client = instructor.from_provider("openai/gpt-4o-mini", mode=Mode.JSON_SCHEMA)
```

**Best for:** Providers with native schema enforcement, similar to TOOLS_STRICT.

## Provider Support Matrix

| Mode | OpenAI | Anthropic | Google | Ollama | Mistral | Cohere |
|------|--------|-----------|--------|--------|---------|--------|
| TOOLS | Yes | Yes | Yes | Yes* | Yes | Yes |
| JSON | Yes | Yes | Yes | Yes | Yes | Yes |
| MD_JSON | Yes | Yes | Yes | Yes | Yes | Yes |
| TOOLS_STRICT | Yes | — | — | — | — | — |
| PARALLEL_TOOLS | Yes | Auto** | Yes | — | — | — |
| RESPONSES_TOOLS | Yes | — | — | — | — | — |
| JSON_O1 | Yes | — | — | — | — | — |

\* Ollama TOOLS mode requires tool-capable models (llama3.1+, mistral-nemo, qwen2.5)
\** Anthropic auto-detects parallel tools when using Mode.TOOLS with Union types

## Mode Selection Guide

```
Start Here
    │
    ├── OpenAI?
    │   ├── Need guaranteed schema? → TOOLS_STRICT
    │   ├── O1 model? → JSON_O1
    │   ├── Responses API features? → RESPONSES_TOOLS
    │   └── Otherwise → TOOLS (default)
    │
    ├── Anthropic?
    │   └── TOOLS (default, auto-handles parallel)
    │
    ├── Google Gemini?
    │   └── TOOLS (default)
    │
    ├── Ollama?
    │   ├── Tool-capable model? → TOOLS
    │   └── Other model → JSON
    │
    └── Other / Unknown?
        ├── Has tool support? → TOOLS
        ├── Has JSON mode? → JSON
        └── Fallback → MD_JSON
```

## Legacy Mode Mappings

Deprecated modes auto-convert with warnings:

| Deprecated | Maps To |
|-----------|---------|
| `FUNCTIONS` | `TOOLS` |
| `ANTHROPIC_JSON` | `MD_JSON` |
| `ANTHROPIC_TOOLS` | `TOOLS` |
| `GEMINI_JSON` | `JSON` |
| `GEMINI_TOOLS` | `TOOLS` |
