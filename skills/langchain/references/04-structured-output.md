# Structured Output

> Source: https://docs.langchain.com/oss/python/langchain/structured-output

## Table of Contents

- [Overview](#overview)
- [with_structured_output](#with_structured_output)
- [Schema Types](#schema-types)
- [Provider Strategy vs Tool Strategy](#provider-strategy-vs-tool-strategy)
- [In Agents (response_format)](#in-agents-response_format)
- [Error Handling](#error-handling)
- [Union Types](#union-types)
- [Best Practices](#best-practices)

## Overview

Structured output constrains model responses to follow a defined schema, returning validated objects instead of free-form text. LangChain supports two strategies: provider-native (API-enforced) and tool-calling (model-driven). Since v1.1.0, LangChain auto-selects the best strategy based on model capabilities.

## with_structured_output

The primary method on chat models for structured output:

```python
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

class MovieReview(BaseModel):
    title: str = Field(description="Movie title")
    rating: int = Field(description="Rating 1-10", ge=1, le=10)
    summary: str = Field(description="Brief summary")

model = ChatOpenAI(model="gpt-4o")
structured = model.with_structured_output(MovieReview)

result = structured.invoke("Review The Matrix")
print(result.title)    # "The Matrix"
print(result.rating)   # 9
print(result.summary)  # "A groundbreaking sci-fi..."
```

### Parameters

```python
structured = model.with_structured_output(
    schema,                  # Pydantic, TypedDict, or JSON Schema
    method="function_calling",  # or "json_mode", "json_schema"
    include_raw=False,       # Return raw AIMessage alongside parsed
    strict=None,             # Strict schema adherence (provider-specific)
)
```

### include_raw

Get both the parsed result and raw model response:

```python
structured = model.with_structured_output(MovieReview, include_raw=True)
result = structured.invoke("Review Inception")

print(result["parsed"])       # MovieReview instance
print(result["raw"])          # AIMessage
print(result["parsing_error"])  # None or Exception
```

## Schema Types

### Pydantic Models (Recommended)

```python
from pydantic import BaseModel, Field
from typing import Literal

class Sentiment(BaseModel):
    """Sentiment analysis result."""
    text: str = Field(description="Original text")
    sentiment: Literal["positive", "negative", "neutral"]
    confidence: float = Field(ge=0.0, le=1.0)
    keywords: list[str] = Field(description="Key terms")

structured = model.with_structured_output(Sentiment)
```

### TypedDict

```python
from typing_extensions import TypedDict, Annotated

class Sentiment(TypedDict):
    """Sentiment analysis result."""
    text: Annotated[str, "Original text"]
    sentiment: Annotated[str, "positive, negative, or neutral"]
    confidence: Annotated[float, "0.0 to 1.0"]

structured = model.with_structured_output(Sentiment)
result = structured.invoke("I love this product!")
print(result)  # {'text': '...', 'sentiment': 'positive', 'confidence': 0.95}
```

### JSON Schema

```python
schema = {
    "title": "Sentiment",
    "description": "Sentiment analysis result",
    "type": "object",
    "properties": {
        "text": {"type": "string", "description": "Original text"},
        "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
        "confidence": {"type": "number"}
    },
    "required": ["text", "sentiment", "confidence"]
}

structured = model.with_structured_output(schema)
```

## Provider Strategy vs Tool Strategy

### Provider Strategy (Native)

Uses the model provider's native structured output API. Higher reliability, faster execution.

**Supported providers:** OpenAI, Anthropic, Google, xAI

```python
from langchain.agents.structured_output import ProviderStrategy

agent = create_agent(
    model="openai:gpt-4o",
    response_format=ProviderStrategy(MovieReview, strict=True)
)
```

### Tool Strategy (Universal)

Uses tool calling to achieve structured output. Works with any tool-capable model.

```python
from langchain.agents.structured_output import ToolStrategy

agent = create_agent(
    model="anthropic:claude-sonnet-4-6",
    tools=[search],
    response_format=ToolStrategy(MovieReview)
)
```

### Comparison

| Aspect | Provider Strategy | Tool Strategy |
|--------|------------------|---------------|
| Reliability | Higher (API-enforced) | Good (with retries) |
| Speed | Faster (single pass) | May need retries |
| Union types | Limited | Full support |
| Model coverage | Specific providers | All tool-capable models |
| Validation | Server-side | Client-side |

### Auto-Selection

When you pass a schema type directly to `response_format`, LangChain checks the model's profile and selects the best strategy:

```python
agent = create_agent(
    model="openai:gpt-4o",
    response_format=MovieReview  # Auto-selects ProviderStrategy
)
```

## In Agents (response_format)

```python
from pydantic import BaseModel, Field
from langchain.agents import create_agent

class ResearchResult(BaseModel):
    summary: str = Field(description="Research summary")
    sources: list[str] = Field(description="Source URLs")
    confidence: float = Field(ge=0.0, le=1.0)

agent = create_agent(
    model="anthropic:claude-sonnet-4-6",
    tools=[search_tool],
    response_format=ResearchResult
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "Research latest AI trends"}]
})
print(result["structured_response"])  # ResearchResult instance
```

## Error Handling

### ToolStrategy Error Handling

```python
from langchain.agents.structured_output import ToolStrategy

agent = create_agent(
    model="openai:gpt-4o",
    response_format=ToolStrategy(
        schema=MovieReview,
        handle_errors=True  # Auto-retry on validation failure
    )
)
```

### Custom Error Handler

```python
def handle_error(error: Exception) -> str:
    return f"Invalid format. Please provide rating 1-10. Error: {error}"

agent = create_agent(
    model="openai:gpt-4o",
    response_format=ToolStrategy(
        schema=MovieReview,
        handle_errors=handle_error
    )
)
```

### Custom Tool Message

```python
agent = create_agent(
    model="openai:gpt-4o",
    response_format=ToolStrategy(
        schema=MovieReview,
        tool_message_content="Review captured successfully!"
    )
)
```

## Union Types

Return different schemas based on input context:

```python
from typing import Union

class ProductReview(BaseModel):
    rating: int = Field(ge=1, le=5)
    sentiment: Literal["positive", "negative"]
    key_points: list[str]

class CustomerComplaint(BaseModel):
    issue_type: Literal["product", "service", "shipping"]
    severity: Literal["low", "medium", "high"]
    description: str

agent = create_agent(
    model="openai:gpt-4o",
    response_format=ToolStrategy(Union[ProductReview, CustomerComplaint])
)
```

## Best Practices

1. **Use Pydantic models** over TypedDict/JSON Schema for field validation and type safety
2. **Add Field descriptions** — They act as instructions telling the model what each field should contain
3. **Use Literal types** for constrained values (enums, categories)
4. **Prefer ProviderStrategy** when the model supports it — faster and more reliable
5. **Enable error handling** for ToolStrategy — validation errors trigger automatic retries
6. **Keep schemas focused** — One schema per task, not monolithic catch-all schemas
7. **Use strict mode** with OpenAI for guaranteed schema compliance
