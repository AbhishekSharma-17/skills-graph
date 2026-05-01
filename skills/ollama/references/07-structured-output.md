# Ollama — Structured Output

> Source: [docs.ollama.com/capabilities/structured-outputs](https://docs.ollama.com/capabilities/structured-outputs) | Version: 0.22.x

## Table of Contents

- [Overview](#overview)
- [JSON Mode](#json-mode)
- [Schema-Enforced Mode](#schema-enforced-mode)
- [Python Library Examples](#python-library-examples)
- [OpenAI SDK Structured Output](#openai-sdk-structured-output)
- [Using with Pydantic](#using-with-pydantic)
- [Using with Instructor](#using-with-instructor)
- [Complex Schema Patterns](#complex-schema-patterns)
- [Best Practices](#best-practices)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

Structured output constrains model responses to follow a specific JSON format. Ollama uses GBNF grammars internally to enforce valid JSON output, guaranteeing the response parses correctly.

Two modes are available:

| Mode | Format Value | Guarantee |
|------|-------------|-----------|
| **JSON mode** | `"json"` | Valid JSON, but schema not enforced |
| **Schema mode** | JSON Schema object | Valid JSON matching the exact schema |

Schema mode (available since Ollama v0.5) is strongly recommended over basic JSON mode.

## JSON Mode

Basic JSON mode ensures the response is valid JSON but doesn't enforce a specific structure:

```bash
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.2",
  "messages": [
    {"role": "user", "content": "List 3 programming languages as JSON"}
  ],
  "format": "json",
  "stream": false
}'
```

The prompt should mention JSON to guide the model:

```bash
# Good — prompt mentions JSON
"List 3 programming languages. Respond in JSON with a 'languages' array."

# Bad — model may not know what structure to use
"List 3 programming languages"
```

## Schema-Enforced Mode

Pass a JSON Schema object to `format` to enforce exact structure:

```bash
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.2",
  "messages": [
    {"role": "user", "content": "Tell me about Canada"}
  ],
  "format": {
    "type": "object",
    "properties": {
      "name": {"type": "string"},
      "capital": {"type": "string"},
      "population": {"type": "integer"},
      "languages": {
        "type": "array",
        "items": {"type": "string"}
      }
    },
    "required": ["name", "capital", "population", "languages"]
  },
  "stream": false
}'

# Guaranteed response format:
# {
#   "name": "Canada",
#   "capital": "Ottawa",
#   "population": 38000000,
#   "languages": ["English", "French"]
# }
```

## Python Library Examples

### Basic Schema

```python
from ollama import chat

schema = {
    "type": "object",
    "properties": {
        "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
        "confidence": {"type": "number"},
        "summary": {"type": "string"},
    },
    "required": ["sentiment", "confidence", "summary"],
}

response = chat(
    model="llama3.2",
    messages=[
        {"role": "user", "content": "Analyze: 'This product is amazing, best purchase ever!'"}
    ],
    format=schema,
    options={"temperature": 0},
)
import json
result = json.loads(response.message.content)
print(f"Sentiment: {result['sentiment']} ({result['confidence']})")
```

### Array of Objects

```python
from ollama import chat
import json

schema = {
    "type": "object",
    "properties": {
        "todos": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                    "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                    "estimated_hours": {"type": "number"},
                },
                "required": ["task", "priority", "estimated_hours"],
            },
        }
    },
    "required": ["todos"],
}

response = chat(
    model="qwen3:8b",
    messages=[
        {"role": "user", "content": "Create a todo list for building a REST API"}
    ],
    format=schema,
    options={"temperature": 0},
)
todos = json.loads(response.message.content)
for todo in todos["todos"]:
    print(f"[{todo['priority']}] {todo['task']} ({todo['estimated_hours']}h)")
```

## OpenAI SDK Structured Output

```python
from openai import OpenAI
import json

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

response = client.chat.completions.create(
    model="llama3.2",
    messages=[
        {"role": "user", "content": "Extract: John Smith, age 30, engineer at Google"}
    ],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "person",
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"},
                    "company": {"type": "string"},
                    "role": {"type": "string"},
                },
                "required": ["name", "age", "company", "role"],
            },
        },
    },
)
person = json.loads(response.choices[0].message.content)
```

## Using with Pydantic

Pydantic models can generate JSON Schema for Ollama:

```python
from pydantic import BaseModel
from ollama import chat
import json

class CodeReview(BaseModel):
    file_path: str
    issues: list[str]
    severity: str
    suggestion: str

response = chat(
    model="qwen3:8b",
    messages=[
        {"role": "user", "content": "Review this code: def add(a,b): return a+b"}
    ],
    format=CodeReview.model_json_schema(),
    options={"temperature": 0},
)
review = CodeReview.model_validate_json(response.message.content)
print(f"File: {review.file_path}")
print(f"Issues: {review.issues}")
```

## Using with Instructor

The `instructor` library provides a higher-level interface:

```python
import instructor
from openai import OpenAI
from pydantic import BaseModel

client = instructor.from_openai(
    OpenAI(base_url="http://localhost:11434/v1", api_key="ollama"),
    mode=instructor.Mode.JSON,
)

class UserInfo(BaseModel):
    name: str
    age: int
    email: str

user = client.chat.completions.create(
    model="llama3.2",
    messages=[
        {"role": "user", "content": "Extract: Jane Doe, 25 years old, jane@example.com"}
    ],
    response_model=UserInfo,
)
print(f"{user.name}, {user.age}, {user.email}")
```

## Complex Schema Patterns

### Nested Objects

```python
schema = {
    "type": "object",
    "properties": {
        "company": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "departments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "head_count": {"type": "integer"},
                        },
                    },
                },
            },
        }
    },
}
```

### Enum Constraints

```python
schema = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["active", "inactive", "pending"]},
        "priority": {"type": "integer", "minimum": 1, "maximum": 5},
    },
}
```

## Best Practices

1. **Use temperature 0** — minimizes randomness and maximizes schema adherence
2. **Include JSON in the prompt** — even with schema enforcement, mentioning "respond in JSON" improves quality
3. **Use `required`** — always specify required fields to ensure they're present
4. **Prefer schema mode over JSON mode** — schema mode guarantees structure, JSON mode only guarantees valid JSON
5. **Use Pydantic** — generate schemas from Python classes for type safety and validation
6. **Keep schemas simple** — deeply nested schemas may reduce output quality with smaller models

## Common Pitfalls

1. **Forgetting to parse** — `response.message.content` is a JSON string, not a dict. Use `json.loads()`
2. **Schema too complex** — Very complex schemas with many nested levels can confuse smaller models. Simplify or use larger models
3. **Missing enum values** — If the model's knowledge doesn't match enum constraints, it may produce unexpected but valid enum values
4. **Streaming with structured output** — Streaming returns partial JSON chunks. Wait for the complete response to parse
5. **Boolean fields** — Some models may output `"true"` (string) instead of `true` (boolean). Schema mode handles this correctly
