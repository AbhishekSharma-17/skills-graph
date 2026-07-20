# Instructor — Core Usage

> Source: https://python.useinstructor.com | v1.15.4

## Table of Contents

- [Creating Clients](#creating-clients)
- [The from_provider API](#the-from_provider-api)
- [Response Models](#response-models)
- [The create Method](#the-create-method)
- [Manual Patching](#manual-patching)
- [Async Clients](#async-clients)
- [Raw Response Access](#raw-response-access)
- [Context Parameter](#context-parameter)
- [Common Patterns](#common-patterns)

## Creating Clients

The recommended way to create an Instructor client is `from_provider()`, which auto-detects the provider from a model string and applies optimal defaults:

```python
import instructor

# OpenAI
client = instructor.from_provider("openai/gpt-4o-mini")

# Anthropic
client = instructor.from_provider("anthropic/claude-4-5-haiku-latest")

# Ollama (local)
client = instructor.from_provider("ollama/llama3.1")

# Google Gemini
client = instructor.from_provider("google/gemini-2.5-flash")

# Mistral
client = instructor.from_provider("mistral/mistral-large-latest")
```

The model string format is `provider/model-name`. Instructor resolves the correct SDK, authentication, and default mode automatically.

## The from_provider API

```python
client = instructor.from_provider(
    model: str,                    # "provider/model-name"
    mode: instructor.Mode = None,  # Override extraction mode
    async_client: bool = False,    # Return async client
    max_retries: int = 0,          # Default retry count
    retry_delay: float = 0,        # Delay between retries (seconds)
    **kwargs,                      # Passed to underlying SDK client
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `str` | required | Provider and model in `provider/model` format |
| `mode` | `Mode` | auto | Extraction mode (TOOLS, JSON, etc.) |
| `async_client` | `bool` | `False` | Create async client for await-based usage |
| `max_retries` | `int` | `0` | Default retries for validation failures |
| `retry_delay` | `float` | `0` | Seconds between retry attempts |

### Mode Auto-Selection

When `mode` is not specified, Instructor selects the optimal mode per provider:

| Provider | Default Mode |
|----------|-------------|
| OpenAI | `Mode.TOOLS` |
| Anthropic | `Mode.TOOLS` |
| Google | `Mode.TOOLS` |
| Ollama (tool-capable models) | `Mode.TOOLS` |
| Ollama (other models) | `Mode.JSON` |
| Mistral | `Mode.TOOLS` |

## Response Models

Response models are standard Pydantic `BaseModel` classes. They define the schema the LLM must produce:

```python
from pydantic import BaseModel, Field

class UserProfile(BaseModel):
    name: str = Field(description="Full legal name")
    age: int = Field(ge=0, le=150, description="Age in years")
    email: str = Field(description="Primary email address")
    bio: str | None = Field(default=None, description="Short biography")
```

### Field Descriptions Matter

Descriptions in `Field()` are included in the schema sent to the LLM. They guide extraction accuracy:

```python
class Invoice(BaseModel):
    vendor: str = Field(description="Company or person who issued the invoice")
    total: float = Field(description="Total amount due in USD")
    date: str = Field(description="Invoice date in YYYY-MM-DD format")
    line_items: list[LineItem] = Field(description="Individual charges")
```

### Nested Models

Compose complex schemas by nesting Pydantic models:

```python
class Address(BaseModel):
    street: str
    city: str
    state: str
    zip_code: str

class Company(BaseModel):
    name: str
    industry: str
    headquarters: Address
    founded_year: int
```

## The create Method

The patched `create()` method is the primary extraction interface:

```python
result = client.create(
    response_model=UserProfile,
    messages=[
        {"role": "system", "content": "Extract user information accurately."},
        {"role": "user", "content": "John Doe, 32, john@example.com"},
    ],
    max_retries=2,
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `response_model` | `type[BaseModel]` | Pydantic model for output structure |
| `messages` | `list[dict]` | Chat messages (system, user, assistant) |
| `max_retries` | `int` | Override client-level retry count |
| `context` | `dict` | Runtime data for Pydantic validators |
| `stream` | `bool` | Enable streaming (use with Iterable or Partial) |

All other parameters (temperature, max_tokens, etc.) pass through to the underlying provider.

### Return Value

Returns a validated instance of `response_model`:

```python
user = client.create(response_model=UserProfile, messages=[...])
assert isinstance(user, UserProfile)
print(user.name)        # Typed attribute access
print(user.model_dump()) # Convert to dict
print(user.model_dump_json()) # Convert to JSON string
```

## Manual Patching

For fine-grained control, patch an existing client directly:

```python
import openai
import instructor

openai_client = openai.OpenAI(api_key="sk-...")
client = instructor.patch(openai_client, mode=instructor.Mode.TOOLS)

# Now use client.chat.completions.create() with response_model
result = client.chat.completions.create(
    model="gpt-4o-mini",
    response_model=UserProfile,
    messages=[{"role": "user", "content": "..."}],
)
```

Manual patching preserves the provider's original API surface while adding `response_model`, `max_retries`, and `context`.

### Provider-Specific Constructors (Legacy)

These still work but `from_provider()` is preferred:

```python
# OpenAI
client = instructor.from_openai(openai.OpenAI())

# Anthropic
import anthropic
client = instructor.from_anthropic(anthropic.Anthropic())

# Ollama (via OpenAI compat)
client = instructor.from_openai(
    openai.OpenAI(base_url="http://localhost:11434/v1", api_key="ollama"),
    mode=instructor.Mode.JSON,
)
```

## Async Clients

Create async clients for `asyncio`-based applications:

```python
import asyncio
import instructor
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int

async def main():
    client = instructor.from_provider(
        "openai/gpt-4o-mini",
        async_client=True,
    )
    user = await client.create(
        response_model=User,
        messages=[{"role": "user", "content": "Extract: Jason is 25"}],
    )
    print(user)

asyncio.run(main())
```

Async clients support all the same features: streaming, retries, hooks, context.

## Raw Response Access

Every parsed model includes `_raw_response` for accessing the original provider response:

```python
user = client.create(
    response_model=User,
    messages=[{"role": "user", "content": "Extract: Jason is 25"}],
)

raw = user._raw_response
print(raw.usage.prompt_tokens)
print(raw.usage.completion_tokens)
```

This is useful for cost tracking, debugging, and logging.

## Context Parameter

Pass runtime data to Pydantic validators via `context`:

```python
from pydantic import field_validator, ValidationInfo

class Citation(BaseModel):
    quote: str
    source: str

    @field_validator("quote")
    @classmethod
    def quote_must_exist_in_source(cls, v: str, info: ValidationInfo) -> str:
        ctx = info.context
        if ctx and v not in ctx.get("source_text", ""):
            raise ValueError(f"Quote not found in source text")
        return v

result = client.create(
    response_model=Citation,
    messages=[{"role": "user", "content": "Find a quote from this text..."}],
    context={"source_text": "The original document text here..."},
    max_retries=3,
)
```

On validation failure, Instructor feeds the error back to the LLM and retries.

## Common Patterns

### Optional Fields with Defaults

```python
class EventInfo(BaseModel):
    title: str
    date: str
    location: str | None = None
    attendees: list[str] = Field(default_factory=list)
```

### Constrained Fields

```python
class Product(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    price: float = Field(gt=0)
    rating: float = Field(ge=0, le=5)
    category: str
```

### Model with Docstring (Guides LLM)

```python
class SupportTicket(BaseModel):
    """Classify and extract details from a customer support message.
    Focus on identifying the core issue and urgency level."""

    subject: str = Field(description="Brief summary of the issue")
    category: str = Field(description="Issue category")
    urgency: int = Field(ge=1, le=5, description="1=low, 5=critical")
    customer_name: str
```

The model's docstring is included in the schema and acts as a system-level instruction.

### Chaining Extractions

```python
summary = client.create(
    response_model=DocumentSummary,
    messages=[{"role": "user", "content": long_document}],
)

entities = client.create(
    response_model=Iterable[Entity],
    messages=[{
        "role": "user",
        "content": f"Extract entities from: {summary.key_points}",
    }],
)
```
