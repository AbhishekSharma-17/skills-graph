# Chat Models

> Source: https://docs.langchain.com/oss/python/langchain/models

## Table of Contents

- [Overview](#overview)
- [Model Initialization](#model-initialization)
- [Invocation Methods](#invocation-methods)
- [Provider Integrations](#provider-integrations)
- [Configuration Options](#configuration-options)
- [Dynamic Model Selection](#dynamic-model-selection)
- [Multimodal Input](#multimodal-input)
- [Reasoning Models](#reasoning-models)
- [Token Usage Tracking](#token-usage-tracking)
- [Rate Limiting](#rate-limiting)
- [Caching](#caching)
- [Common Patterns](#common-patterns)

## Overview

Chat models are the core building block in LangChain. They accept messages as input and return messages as output, providing a unified interface across all providers. Every chat model implements the Runnable interface with `.invoke()`, `.stream()`, `.batch()`, and their async counterparts.

## Model Initialization

### Direct Provider Import

```python
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

openai_model = ChatOpenAI(model="gpt-4o")
anthropic_model = ChatAnthropic(model="claude-sonnet-4-6")
google_model = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
```

### Using init_chat_model (Provider-Agnostic)

```python
from langchain.chat_models import init_chat_model

model = init_chat_model("gpt-4o", model_provider="openai")
model = init_chat_model("claude-sonnet-4-6", model_provider="anthropic")
model = init_chat_model("gemini-2.0-flash", model_provider="google_genai")
```

### String Format in create_agent

```python
from langchain.agents import create_agent

agent = create_agent(model="anthropic:claude-sonnet-4-6", tools=[])
agent = create_agent(model="openai:gpt-4o", tools=[])
```

## Invocation Methods

### invoke — Single Call

```python
response = model.invoke("Explain REST APIs")
print(response.content)
print(response.usage_metadata)
```

### stream — Token Streaming

```python
for chunk in model.stream("Write a poem about coding"):
    print(chunk.content, end="", flush=True)
```

### batch — Parallel Processing

```python
responses = model.batch([
    "Summarize Python",
    "Summarize JavaScript",
    "Summarize Rust"
])
for r in responses:
    print(r.content[:100])
```

### Async Variants

```python
import asyncio

async def main():
    response = await model.ainvoke("Hello")
    
    async for chunk in model.astream("Write a story"):
        print(chunk.content, end="")
    
    results = await model.abatch(["Q1", "Q2", "Q3"])

asyncio.run(main())
```

## Provider Integrations

| Provider | Package | Model Examples |
|----------|---------|----------------|
| OpenAI | `langchain-openai` | gpt-4o, gpt-4o-mini, o1 |
| Anthropic | `langchain-anthropic` | claude-sonnet-4-6, claude-haiku-4-5 |
| Google | `langchain-google-genai` | gemini-2.0-flash, gemini-2.5-pro |
| AWS Bedrock | `langchain-aws` | Various via Bedrock |
| Azure OpenAI | `langchain-openai` | Via AzureChatOpenAI |
| HuggingFace | `langchain-huggingface` | Open-source models |
| Ollama | `langchain-ollama` | Local models |
| OpenRouter | `langchain-openai` | Via base_url override |
| Fireworks | `langchain-fireworks` | Fast inference models |

## Configuration Options

```python
model = ChatOpenAI(
    model="gpt-4o",
    temperature=0.7,
    max_tokens=4096,
    timeout=30,
    max_retries=3,
    api_key="sk-...",
    base_url="https://custom-endpoint.com/v1",
)
```

### Configurable Fields (Runtime Override)

```python
model = ChatOpenAI(model="gpt-4o").configurable_fields(
    model_name=ConfigurableField(id="model_name"),
    temperature=ConfigurableField(id="temperature"),
)

response = model.invoke(
    "Hello",
    config={"configurable": {"model_name": "gpt-4o-mini", "temperature": 0.1}}
)
```

## Dynamic Model Selection

Switch models at runtime using middleware:

```python
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse

@wrap_model_call
def route_by_complexity(request: ModelRequest, handler):
    message_count = len(request.state.get("messages", []))
    if message_count > 10:
        request = request.override(model="anthropic:claude-sonnet-4-6")
    return handler(request)

agent = create_agent(
    model="openai:gpt-4o-mini",
    tools=[],
    middleware=[route_by_complexity]
)
```

## Multimodal Input

### Image Input

```python
from langchain_core.messages import HumanMessage

message = HumanMessage(content=[
    {"type": "text", "text": "Describe this image."},
    {"type": "image_url", "image_url": {"url": "https://example.com/photo.jpg"}}
])
response = model.invoke([message])
```

### Base64 Image

```python
import base64

with open("photo.jpg", "rb") as f:
    b64 = base64.standard_b64encode(f.read()).decode()

message = HumanMessage(content=[
    {"type": "text", "text": "What do you see?"},
    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
])
```

### Audio Input

```python
message = HumanMessage(content=[
    {"type": "text", "text": "Transcribe this audio."},
    {"type": "audio", "base64": audio_b64, "mime_type": "audio/wav"}
])
```

## Reasoning Models

For models with extended thinking (Claude, o1):

```python
from langchain_anthropic import ChatAnthropic

model = ChatAnthropic(
    model="claude-sonnet-4-6",
    thinking={"type": "enabled", "budget_tokens": 5000}
)

response = model.invoke("Solve this complex math problem...")
for block in response.content_blocks:
    if block["type"] == "reasoning":
        print(f"[Thinking] {block['text']}")
    elif block["type"] == "text":
        print(f"[Answer] {block['text']}")
```

## Token Usage Tracking

```python
response = model.invoke("Hello, how are you?")
usage = response.usage_metadata
print(f"Input tokens: {usage['input_tokens']}")
print(f"Output tokens: {usage['output_tokens']}")
print(f"Total tokens: {usage['total_tokens']}")
```

### Aggregate Across Calls

```python
from langchain_core.callbacks import get_openai_callback

with get_openai_callback() as cb:
    model.invoke("First call")
    model.invoke("Second call")
    print(f"Total tokens: {cb.total_tokens}")
    print(f"Total cost: ${cb.total_cost:.4f}")
```

## Rate Limiting

```python
from langchain_core.rate_limiters import InMemoryRateLimiter

limiter = InMemoryRateLimiter(
    requests_per_second=1,
    check_every_n_seconds=0.1,
    max_bucket_size=10,
)

model = ChatOpenAI(model="gpt-4o", rate_limiter=limiter)
```

## Caching

```python
from langchain_core.globals import set_llm_cache
from langchain_core.caches import InMemoryCache

set_llm_cache(InMemoryCache())

response1 = model.invoke("What is LangChain?")  # Calls API
response2 = model.invoke("What is LangChain?")  # Returns cached
```

### SQLite Cache for Persistence

```python
from langchain_community.cache import SQLiteCache

set_llm_cache(SQLiteCache(database_path=".langchain_cache.db"))
```

## Common Patterns

### Bind Tools to Model

```python
model_with_tools = model.bind_tools([search_tool, calc_tool])
response = model_with_tools.invoke("What is 42 * 17?")
print(response.tool_calls)
```

### Structured Output

```python
from pydantic import BaseModel

class Answer(BaseModel):
    summary: str
    confidence: float

structured = model.with_structured_output(Answer)
result = structured.invoke("Summarize quantum computing")
print(result.summary, result.confidence)
```

### Fallback Models

```python
primary = ChatOpenAI(model="gpt-4o")
fallback = ChatAnthropic(model="claude-sonnet-4-6")

model = primary.with_fallbacks([fallback])
response = model.invoke("Hello")
```
