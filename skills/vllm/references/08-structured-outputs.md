# Structured Outputs

> Source: [docs.vllm.ai](https://docs.vllm.ai/) — v0.22.1

## Table of Contents
- [Overview](#overview)
- [Constraint Types](#constraint-types)
- [Backend Configuration](#backend-configuration)
- [JSON Schema Constraints](#json-schema-constraints)
- [Regex Constraints](#regex-constraints)
- [Choice Constraints](#choice-constraints)
- [Grammar Constraints](#grammar-constraints)
- [Online Serving API](#online-serving-api)
- [Offline Inference API](#offline-inference-api)
- [Reasoning Model Integration](#reasoning-model-integration)
- [Common Pitfalls](#common-pitfalls)

## Overview

vLLM supports constrained generation (guided decoding) that forces model output to conform to a specified format — JSON schema, regex pattern, fixed choices, or a context-free grammar. This guarantees structurally valid output without post-processing or retries.

Structured outputs use a backend engine (xgrammar or guidance) to mask invalid tokens at each decoding step, ensuring the model can only produce tokens that lead to valid output.

## Constraint Types

| Type | Use Case | Example |
|------|----------|---------|
| **JSON Schema** | Extract structured data | `{"name": "string", "age": "integer"}` |
| **Regex** | Pattern matching | Email, phone numbers, dates |
| **Choice** | Classification | `["positive", "negative", "neutral"]` |
| **Grammar** | Complex languages | SQL queries, code snippets |
| **Structural Tag** | Schema within tags | JSON inside XML-like delimiters |

## Backend Configuration

vLLM supports multiple guided decoding backends:

```bash
# Auto-select (default)
vllm serve model --structured-outputs-config.backend auto

# Force xgrammar
vllm serve model --structured-outputs-config.backend xgrammar

# Force guidance
vllm serve model --structured-outputs-config.backend guidance
```

| Backend | JSON Schema | Regex | Grammar | Speed | Notes |
|---------|:-----------:|:-----:|:-------:|:-----:|-------|
| xgrammar | Yes | Yes | Yes | Fastest | Default, Rust-based regex |
| guidance | Yes | Yes | Yes | Fast | Python `re` module regex |

## JSON Schema Constraints

### With Pydantic Models (Recommended)

```python
from pydantic import BaseModel
from openai import OpenAI

class Person(BaseModel):
    name: str
    age: int
    occupation: str

client = OpenAI(api_key="EMPTY", base_url="http://localhost:8000/v1")

response = client.chat.completions.create(
    model="model-name",
    messages=[{"role": "user", "content": "Tell me about Marie Curie"}],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "person",
            "schema": Person.model_json_schema(),
        },
    },
)

import json
data = json.loads(response.choices[0].message.content)
person = Person(**data)
print(person)  # name='Marie Curie' age=66 occupation='Physicist'
```

### With Raw JSON Schema

```python
response = client.chat.completions.create(
    model="model-name",
    messages=[{"role": "user", "content": "Extract the sentiment"}],
    extra_body={
        "structured_outputs": {
            "json_schema": {
                "type": "object",
                "properties": {
                    "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                },
                "required": ["sentiment", "confidence"],
            }
        }
    },
)
```

### Beta Automatic Parsing

The OpenAI Python SDK's beta parser automatically converts Pydantic models and parses responses:

```python
response = client.beta.chat.completions.parse(
    model="model-name",
    messages=[{"role": "user", "content": "Tell me about Marie Curie"}],
    response_format=Person,
)

person = response.choices[0].message.parsed
print(person.name)  # "Marie Curie"
```

## Regex Constraints

Force output to match a regular expression pattern:

```python
# Email extraction
response = client.chat.completions.create(
    model="model-name",
    messages=[{"role": "user", "content": "Generate a sample email address"}],
    extra_body={
        "structured_outputs": {
            "regex": r"\w+@\w+\.\w+"
        }
    },
)
```

```python
# Date format
response = client.chat.completions.create(
    model="model-name",
    messages=[{"role": "user", "content": "What date is today?"}],
    extra_body={
        "structured_outputs": {
            "regex": r"\d{4}-\d{2}-\d{2}"
        }
    },
)
```

Regex syntax depends on backend: xgrammar uses Rust-style regex, guidance uses Python's `re` module.

## Choice Constraints

Restrict output to one of several predefined options:

```python
response = client.chat.completions.create(
    model="model-name",
    messages=[{"role": "user", "content": "Is this review positive or negative: 'Great product!'"}],
    extra_body={
        "structured_outputs": {
            "choice": ["positive", "negative", "neutral"]
        }
    },
)
# Output guaranteed to be exactly one of the three options
```

## Grammar Constraints

Use EBNF context-free grammar for complex output formats:

```python
# SQL query generation
sql_grammar = '''
    root ::= select_stmt
    select_stmt ::= "SELECT " columns " FROM " table where_clause
    columns ::= column ("," column)*
    column ::= [a-zA-Z_]+
    table ::= [a-zA-Z_]+
    where_clause ::= " WHERE " condition | ""
    condition ::= column " = " value
    value ::= "'" [a-zA-Z0-9_]+ "'"
'''

response = client.chat.completions.create(
    model="model-name",
    messages=[{"role": "user", "content": "Write a SQL query to get all users named John"}],
    extra_body={
        "structured_outputs": {
            "grammar": sql_grammar
        }
    },
)
```

## Online Serving API

### response_format (OpenAI-compatible)

```python
response = client.chat.completions.create(
    model="model-name",
    messages=[...],
    response_format={
        "type": "json_schema",
        "json_schema": {"name": "output", "schema": {...}},
    },
)
```

### extra_body (vLLM-specific)

```python
response = client.chat.completions.create(
    model="model-name",
    messages=[...],
    extra_body={
        "structured_outputs": {
            "json_schema": {...},   # OR
            "regex": "...",          # OR
            "choice": [...],         # OR
            "grammar": "...",        # OR
            "structural_tag": {...},
        }
    },
)
```

## Offline Inference API

Use `StructuredOutputsParams` with `SamplingParams`:

```python
from vllm import LLM, SamplingParams
from vllm.sampling_params import StructuredOutputsParams

llm = LLM(model="model-name")

# Choice constraint
params = SamplingParams(
    temperature=0,
    max_tokens=10,
    structured_outputs=StructuredOutputsParams(
        choice=["Positive", "Negative", "Neutral"]
    ),
)
outputs = llm.generate(["Classify: 'Great movie!'"], params)

# JSON schema constraint
params = SamplingParams(
    temperature=0,
    max_tokens=200,
    structured_outputs=StructuredOutputsParams(
        json_schema={
            "type": "object",
            "properties": {
                "answer": {"type": "string"},
                "confidence": {"type": "number"},
            },
            "required": ["answer", "confidence"],
        }
    ),
)
outputs = llm.generate(["What is 2+2?"], params)
```

## Reasoning Model Integration

Structured outputs work with reasoning models that produce thinking tokens:

```bash
# Enable with DeepSeek-R1 reasoning
vllm serve deepseek-ai/DeepSeek-R1 \
    --reasoning-parser deepseek_r1

# For Qwen3 Coder with reasoning + structured output
vllm serve Qwen/Qwen3-Coder \
    --reasoning-parser qwen3 \
    --structured-outputs-config.enable_in_reasoning=True
```

The reasoning tokens are produced freely, then the structured constraint applies only to the final answer portion.

## Common Pitfalls

1. **Deprecated API fields** — `guided_json`, `guided_regex`, `guided_choice`, `guided_grammar` were replaced by `structured_outputs` in v0.12.0+
2. **strict parameter ignored** — vLLM accepts but ignores OpenAI's `strict` field; constraints are always enforced via token masking
3. **Slow with complex grammars** — very large JSON schemas or grammars can slow down token masking; simplify schemas when possible
4. **Backend differences** — regex syntax differs between backends; test your patterns with the actual backend
5. **Empty output** — if the schema is too restrictive, the model may produce minimal/unexpected output; ensure the schema allows reasonable content
6. **Temperature interaction** — structured outputs work with any temperature, but the quality of content within the structure still depends on good sampling parameters
