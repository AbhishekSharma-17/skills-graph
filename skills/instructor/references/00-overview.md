# Instructor — Overview

> Source: https://python.useinstructor.com | v1.15.4

## What Is Instructor

Instructor is the most popular Python library for extracting structured, validated data from Large Language Models. It uses Pydantic models to define output schemas and automatically handles validation, retries, and error recovery. With 13.6K+ GitHub stars and 3M+ monthly PyPI downloads, it is trusted by teams at OpenAI, Google, Microsoft, and AWS.

Instructor is not a full agent framework — it focuses on one thing: getting typed, validated data out of LLMs reliably. It sits between your code and the LLM provider, intercepting completions to enforce structure.

## When to Use Instructor

Use Instructor when you need to:

- Extract structured data from unstructured text (names, addresses, entities)
- Classify text into categories with type-safe enums
- Parse complex documents (invoices, resumes, contracts) into typed models
- Build data pipelines that consume LLM outputs
- Generate validated JSON from natural language
- Process multimodal inputs (images, PDFs, audio) into structured data

Do not use Instructor when you need:

- Multi-step agent workflows (use LangGraph, CrewAI, or similar)
- Prompt chaining and orchestration (use LangChain, Mastra)
- RAG pipelines (use LlamaIndex, Haystack)
- Model serving infrastructure (use vLLM, Ollama)

## Core Value Proposition

```python
# Without Instructor — manual parsing, no validation, brittle
import openai
import json

response = openai.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Extract: Jason is 25"}],
    response_format={"type": "json_object"},
)
data = json.loads(response.choices[0].message.content)
name = data.get("name")  # No type safety, no validation
age = data.get("age")    # Could be string, null, missing

# With Instructor — typed, validated, automatic retries
import instructor
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int

client = instructor.from_provider("openai/gpt-4o-mini")
user = client.create(
    response_model=User,
    messages=[{"role": "user", "content": "Extract: Jason is 25"}],
)
print(user.name)  # "Jason" — guaranteed str
print(user.age)   # 25 — guaranteed int
```

## Installation

```bash
# Core (includes OpenAI support)
pip install instructor

# With specific provider extras
pip install "instructor[anthropic]"
pip install "instructor[google-generativeai]"
pip install "instructor[litellm]"
pip install "instructor[cohere]"
pip install "instructor[mistral]"
pip install "instructor[vertexai]"
```

## Architecture Overview

Instructor implements a layered pipeline:

1. **Patching Layer** — wraps the provider's `create()` method, adding `response_model`, `max_retries`, and `context` parameters
2. **Schema Conversion** — transforms Pydantic models into provider-specific formats (tool schemas, JSON schemas)
3. **Provider Dispatch** — routes to mode-specific handlers (TOOLS, JSON, MD_JSON)
4. **Response Parsing** — converts LLM output back into Pydantic model instances
5. **Validation** — runs Pydantic validators on parsed output
6. **Retry Loop** — on validation failure, reformulates messages with error context and retries

```
User Code → from_provider() → Patched Client
    ↓
client.create(response_model=Model)
    ↓
Schema Conversion (Pydantic → Tool/JSON schema)
    ↓
LLM API Call (OpenAI, Anthropic, etc.)
    ↓
Response Parsing (JSON → Pydantic)
    ↓
Validation (field validators, model validators)
    ↓
Pass → Return typed Model instance
Fail → Reask with error context → Retry
```

## Key Concepts at a Glance

| Concept | Description |
|---------|-------------|
| `from_provider()` | Unified client constructor for any LLM provider |
| `response_model` | Pydantic model defining expected output structure |
| `max_retries` | Automatic retry count on validation failure |
| `Mode` | Extraction strategy: TOOLS, JSON, MD_JSON, etc. |
| `create_partial()` | Stream partial model snapshots for real-time UI |
| `create_iterable()` | Stream multiple objects one at a time |
| `Iterable[T]` | Extract lists of typed objects |
| Hooks | Event callbacks for logging and monitoring |
| `context` | Pass runtime data to Pydantic validators |

## Supported Providers

| Provider | Package | Modes |
|----------|---------|-------|
| OpenAI | `openai` | TOOLS, JSON, TOOLS_STRICT, MD_JSON |
| Anthropic | `anthropic` | TOOLS, JSON |
| Google Gemini | `google-generativeai` | TOOLS, JSON |
| Ollama | (via openai compat) | TOOLS, JSON |
| Mistral | `mistralai` | TOOLS, JSON |
| Cohere | `cohere` | TOOLS, JSON |
| DeepSeek | (via openai compat) | TOOLS, JSON |
| LiteLLM | `litellm` | TOOLS, JSON |
| Vertex AI | `vertexai` | TOOLS, JSON |
| AWS Bedrock | `boto3` | TOOLS, JSON |
| Fireworks | (via openai compat) | TOOLS, JSON |
| Together | (via openai compat) | JSON |
| Cerebras | (via openai compat) | JSON |

## Quick Start Patterns

### Simple Extraction

```python
import instructor
from pydantic import BaseModel

class Contact(BaseModel):
    name: str
    email: str
    phone: str | None = None

client = instructor.from_provider("openai/gpt-4o-mini")
contact = client.create(
    response_model=Contact,
    messages=[{
        "role": "user",
        "content": "Reach me at jane@acme.com, I'm Jane Smith, 555-0123",
    }],
)
```

### Classification

```python
from enum import Enum

class Sentiment(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class Analysis(BaseModel):
    sentiment: Sentiment
    confidence: float

result = client.create(
    response_model=Analysis,
    messages=[{"role": "user", "content": "I love this product!"}],
)
```

### Multi-Object Extraction

```python
from typing import Iterable

class Person(BaseModel):
    name: str
    age: int

people = client.create(
    response_model=Iterable[Person],
    messages=[{
        "role": "user",
        "content": "Jason is 25, Sarah is 30, Mike is 28",
    }],
)
for person in people:
    print(f"{person.name}: {person.age}")
```
