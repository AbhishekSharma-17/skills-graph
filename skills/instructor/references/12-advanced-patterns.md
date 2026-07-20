# Instructor — Advanced Patterns

> Source: https://python.useinstructor.com | v1.15.4

## Table of Contents

- [Jinja Templating](#jinja-templating)
- [Complex Nested Schemas](#complex-nested-schemas)
- [Chain of Thought Extraction](#chain-of-thought-extraction)
- [Self-Correction Patterns](#self-correction-patterns)
- [Dynamic Models](#dynamic-models)
- [Recursive Structures](#recursive-structures)
- [Production Best Practices](#production-best-practices)
- [Testing Strategies](#testing-strategies)
- [Common Pitfalls](#common-pitfalls)

## Jinja Templating

Instructor integrates Jinja for dynamic prompt generation. Use `{{ variable }}` syntax in messages and pass values via `context`:

```python
import instructor
from pydantic import BaseModel

class Summary(BaseModel):
    key_points: list[str]
    tone: str

client = instructor.from_provider("openai/gpt-4o-mini")

result = client.create(
    response_model=Summary,
    messages=[{
        "role": "user",
        "content": "Summarize the following {{ doc_type }} document: {{ text }}",
    }],
    context={"doc_type": "legal", "text": "This agreement between..."},
)
```

### Conditionals and Loops

```python
template = """Analyze the following data:

{% for item in items %}
- Item {{ loop.index }}: {{ item.name }} ({{ item.value }})
{% endfor %}

{% if include_summary %}
Provide a summary paragraph after the analysis.
{% endif %}

Focus on: {{ focus_area }}
"""

result = client.create(
    response_model=Analysis,
    messages=[{"role": "user", "content": template}],
    context={
        "items": [
            {"name": "Revenue", "value": "$1.2M"},
            {"name": "Costs", "value": "$800K"},
        ],
        "include_summary": True,
        "focus_area": "profitability trends",
    },
)
```

### Security

Instructor uses `SandboxedEnvironment` to prevent code injection in templates. Still sanitize user-provided inputs before passing them as context values.

## Complex Nested Schemas

Build deep schema hierarchies for document parsing:

```python
from pydantic import BaseModel, Field

class ContactInfo(BaseModel):
    email: str
    phone: str | None = None
    address: str | None = None

class Experience(BaseModel):
    company: str
    title: str
    start_date: str
    end_date: str | None = Field(default=None, description="None if current")
    responsibilities: list[str]

class Education(BaseModel):
    institution: str
    degree: str
    field: str
    graduation_year: int

class Resume(BaseModel):
    """Parse a resume into structured sections."""
    name: str
    contact: ContactInfo
    summary: str = Field(description="Professional summary in 2-3 sentences")
    experience: list[Experience] = Field(min_length=1)
    education: list[Education]
    skills: list[str]
    languages: list[str] = Field(default_factory=list)
```

### Deeply Nested with Cross-References

```python
class APIEndpoint(BaseModel):
    path: str
    method: str
    description: str
    parameters: list[Parameter]
    responses: list[Response]

class APISection(BaseModel):
    name: str
    description: str
    endpoints: list[APIEndpoint]

class APIDocumentation(BaseModel):
    title: str
    version: str
    base_url: str
    sections: list[APISection]
    authentication: AuthInfo
```

## Chain of Thought Extraction

Force the model to reason before extracting:

```python
class ReasonedClassification(BaseModel):
    """First reason about the input, then classify it."""
    chain_of_thought: str = Field(
        description="Step-by-step reasoning about the classification"
    )
    category: Literal["spam", "ham", "uncertain"]
    confidence: float = Field(ge=0.0, le=1.0)
```

The `chain_of_thought` field forces the model to articulate reasoning before committing to a category, improving accuracy on ambiguous inputs.

### Multi-Step Reasoning

```python
class MathSolution(BaseModel):
    problem_understanding: str = Field(
        description="Restate the problem in your own words"
    )
    approach: str = Field(description="Describe the solution strategy")
    steps: list[str] = Field(description="Numbered solution steps")
    answer: float
    unit: str
```

## Self-Correction Patterns

Combine validators with retries for self-correcting extraction:

```python
from pydantic import BaseModel, field_validator, ValidationInfo

class FactCheck(BaseModel):
    claim: str
    evidence: str
    verdict: Literal["true", "false", "unverifiable"]

    @field_validator("evidence")
    @classmethod
    def evidence_supports_verdict(cls, v: str, info: ValidationInfo) -> str:
        if len(v) < 20:
            raise ValueError(
                "Evidence must be substantive (at least 20 characters). "
                "Provide specific supporting details."
            )
        return v

# With max_retries, the model learns from its mistakes
result = client.create(
    response_model=FactCheck,
    messages=[{"role": "user", "content": "Fact-check: Python is faster than C"}],
    max_retries=3,
)
```

## Dynamic Models

Create response models at runtime:

```python
from pydantic import create_model

def make_extractor(fields: dict[str, type]) -> type:
    """Create a dynamic Pydantic model from a field dict."""
    return create_model(
        "DynamicExtractor",
        **{name: (typ, ...) for name, typ in fields.items()},
    )

# Build model from config
ExtractorModel = make_extractor({
    "name": str,
    "age": int,
    "email": str,
})

result = client.create(
    response_model=ExtractorModel,
    messages=[{"role": "user", "content": "Extract: Jason, 25, jason@test.com"}],
)
```

### From JSON Schema

```python
import json

schema = {
    "name": {"type": "str"},
    "revenue": {"type": "float"},
    "employees": {"type": "int"},
}

type_map = {"str": str, "int": int, "float": float, "bool": bool}

fields = {k: (type_map[v["type"]], ...) for k, v in schema.items()}
Model = create_model("ConfigModel", **fields)
```

## Recursive Structures

Model tree-like data (note: TOOLS_STRICT does not support recursive types):

```python
from __future__ import annotations

class TreeNode(BaseModel):
    label: str
    value: str | None = None
    children: list[TreeNode] = Field(default_factory=list)

class DocumentOutline(BaseModel):
    title: str
    sections: list[TreeNode]

# Use Mode.TOOLS or Mode.JSON for recursive schemas
client = instructor.from_provider("openai/gpt-4o-mini", mode=instructor.Mode.TOOLS)

outline = client.create(
    response_model=DocumentOutline,
    messages=[{
        "role": "user",
        "content": "Create an outline for a Python tutorial",
    }],
)
```

## Production Best Practices

### 1. Model Fallback Chain

```python
async def extract_with_fallback(text: str) -> User:
    models = ["openai/gpt-4o-mini", "anthropic/claude-4-5-haiku-latest"]
    for model in models:
        try:
            client = instructor.from_provider(model, async_client=True)
            return await client.create(
                response_model=User,
                messages=[{"role": "user", "content": f"Extract: {text}"}],
                max_retries=2,
            )
        except Exception:
            continue
    raise RuntimeError("All providers failed")
```

### 2. Cost Tracking

```python
def track_costs(response):
    if hasattr(response, "usage"):
        cost = (
            response.usage.prompt_tokens * 0.00015 / 1000
            + response.usage.completion_tokens * 0.0006 / 1000
        )
        print(f"Cost: ${cost:.6f}")

client.on("completion:response", track_costs)
```

### 3. Structured Logging

```python
import structlog

log = structlog.get_logger()

def log_extraction(*args, **kwargs):
    log.info("instructor.request", model=kwargs.get("model"))

def log_response(response):
    log.info("instructor.response", tokens=getattr(response.usage, "total_tokens", 0))

client.on("completion:kwargs", log_extraction)
client.on("completion:response", log_response)
```

### 4. Caching Responses

```python
import hashlib
import json
from functools import lru_cache

def cache_key(messages: list[dict]) -> str:
    return hashlib.sha256(json.dumps(messages).encode()).hexdigest()

_cache: dict[str, BaseModel] = {}

def cached_extract(client, response_model, messages, **kwargs):
    key = cache_key(messages)
    if key in _cache:
        return _cache[key]
    result = client.create(response_model=response_model, messages=messages, **kwargs)
    _cache[key] = result
    return result
```

## Testing Strategies

### Unit Test Pydantic Models Independently

```python
import pytest
from pydantic import ValidationError

def test_user_valid():
    user = User(name="Jason", age=25)
    assert user.name == "Jason"

def test_user_invalid_age():
    with pytest.raises(ValidationError):
        User(name="Jason", age=-1)
```

### Mock Instructor for Integration Tests

```python
from unittest.mock import AsyncMock, patch

async def test_extract_user():
    mock_client = AsyncMock()
    mock_client.create.return_value = User(name="Jason", age=25)

    with patch("myapp.extract.client", mock_client):
        result = await extract_user_info("Jason is 25")
        assert result.name == "Jason"
        mock_client.create.assert_called_once()
```

### Test with Real API (Sparingly)

```python
@pytest.mark.integration
def test_real_extraction():
    client = instructor.from_provider("openai/gpt-4o-mini")
    user = client.create(
        response_model=User,
        messages=[{"role": "user", "content": "Extract: Jason is 25"}],
    )
    assert user.name == "Jason"
    assert user.age == 25
```

## Common Pitfalls

1. **Missing `max_retries`** — validators without retries raise on first failure instead of self-correcting
2. **Overly complex schemas** — models with 20+ fields or deep nesting reduce extraction accuracy; split into multiple calls
3. **No `Field(description=...)` ** — the LLM relies on descriptions to understand what to extract; vague names produce vague results
4. **Ignoring `_raw_response`** — skipping token/cost tracking leads to surprise bills
5. **Sync client in async code** — blocks the event loop; always use `async_client=True` in async contexts
6. **Recursive types with TOOLS_STRICT** — not supported; use TOOLS or JSON mode instead
7. **No error handling** — always catch `InstructorRetryException` in production
8. **Hardcoded model names** — use config/settings; models deprecate and pricing changes
