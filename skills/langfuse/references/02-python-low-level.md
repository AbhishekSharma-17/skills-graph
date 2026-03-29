# Python SDK — Low-Level Instrumentation

> Source: [langfuse.com/docs/sdk/python/low-level-sdk](https://langfuse.com/docs/sdk/python/low-level-sdk)

## Table of Contents

- [Overview](#overview)
- [Client Initialization](#client-initialization)
- [Creating Traces](#creating-traces)
- [Creating Spans](#creating-spans)
- [Creating Generations](#creating-generations)
- [Context Managers](#context-managers)
- [Updating Observations](#updating-observations)
- [Scoring Traces](#scoring-traces)
- [Flushing Events](#flushing-events)
- [Configuration Options](#configuration-options)
- [Common Patterns](#common-patterns)
- [Pitfalls](#pitfalls)

---

## Overview

The low-level Python SDK provides manual control over trace creation when the `@observe` decorator isn't suitable — for example, in non-function-based code, complex async workflows, or when you need fine-grained control over observation lifecycle.

## Client Initialization

```python
from langfuse import get_client

# Singleton — returns the same instance across your app
langfuse = get_client()
```

The client reads configuration from environment variables:

```bash
LANGFUSE_SECRET_KEY="sk-lf-..."
LANGFUSE_PUBLIC_KEY="pk-lf-..."
LANGFUSE_BASE_URL="https://cloud.langfuse.com"
```

Or configure explicitly:

```python
from langfuse import Langfuse

langfuse = Langfuse(
    secret_key="sk-lf-...",
    public_key="pk-lf-...",
    host="https://cloud.langfuse.com",
)
```

## Creating Traces

A trace represents a single end-to-end request:

```python
trace = langfuse.trace(
    name="chat-request",
    user_id="user-123",
    session_id="session-456",
    input={"query": "What is Langfuse?"},
    tags=["production", "chat"],
    metadata={"version": "2.0", "region": "us-east"},
    release="v2.0.1",
)

# After processing
trace.update(output={"response": "Langfuse is an LLM observability platform."})
```

### Trace Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Trace identifier |
| `user_id` | `str` | Associated user |
| `session_id` | `str` | Session for multi-turn grouping |
| `input` | `any` | Trace input (serializable) |
| `output` | `any` | Trace output (serializable) |
| `tags` | `list[str]` | Filterable tags |
| `metadata` | `dict` | Arbitrary key-value metadata |
| `release` | `str` | App version/release |
| `public` | `bool` | Make trace publicly accessible via link |

## Creating Spans

Spans represent non-LLM operations (retrieval, processing, tool calls):

```python
trace = langfuse.trace(name="pipeline")

# Create a span within the trace
span = trace.span(
    name="document-retrieval",
    input={"query": "Langfuse features"},
    metadata={"source": "pinecone"},
)

# Do work...
results = vector_db.search(query)

# Update span with results
span.update(output={"documents": len(results)})
span.end()
```

### Nested Spans

```python
trace = langfuse.trace(name="rag-pipeline")

retrieval_span = trace.span(name="retrieval")
embedding_span = retrieval_span.span(name="embedding")
embedding_span.update(output={"dimensions": 1536})
embedding_span.end()

search_span = retrieval_span.span(name="vector-search")
search_span.update(output={"results": 5})
search_span.end()

retrieval_span.end()
```

## Creating Generations

Generations specifically track LLM calls with model-specific metadata:

```python
trace = langfuse.trace(name="chat")

generation = trace.generation(
    name="answer-generation",
    model="gpt-4o",
    model_parameters={"temperature": 0.7, "max_tokens": 500},
    input=[
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "What is Langfuse?"},
    ],
)

# Call your LLM
response = openai.chat.completions.create(...)

# Record the output and usage
generation.update(
    output=response.choices[0].message.content,
    usage={
        "input": response.usage.prompt_tokens,
        "output": response.usage.completion_tokens,
        "total": response.usage.total_tokens,
    },
)
generation.end()
```

### Generation Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Generation name |
| `model` | `str` | Model identifier (e.g., "gpt-4o") |
| `model_parameters` | `dict` | Temperature, max_tokens, etc. |
| `input` | `any` | Prompt/messages sent to the model |
| `output` | `any` | Model response |
| `usage` | `dict` | Token counts: `input`, `output`, `total` |
| `metadata` | `dict` | Additional metadata |

## Context Managers

Context managers auto-close observations and handle nesting:

```python
langfuse = get_client()

with langfuse.start_as_current_observation(
    as_type="span", name="request-handler"
) as span:
    span.update(input={"endpoint": "/api/chat"})

    with langfuse.start_as_current_observation(
        as_type="generation", name="llm-call", model="gpt-4o"
    ) as gen:
        response = openai.chat.completions.create(...)
        gen.update(
            output=response.choices[0].message.content,
            usage={"input": 100, "output": 50},
        )

    span.update(output={"status": "success"})
# Observations auto-closed on context exit
```

## Updating Observations

All observation types support `.update()`:

```python
span.update(
    name="updated-name",
    input={"new": "input"},
    output={"new": "output"},
    metadata={"key": "value"},
    level="WARNING",  # DEBUG, DEFAULT, WARNING, ERROR
    status_message="Rate limited, retrying...",
)
```

## Scoring Traces

Attach scores to traces or observations for evaluation:

```python
trace = langfuse.trace(name="qa-request")
# ... processing ...

# Score the trace
trace.score(
    name="user-feedback",
    value=1,  # Numeric or boolean
    comment="User clicked thumbs up",
)

# Score a specific generation
generation.score(
    name="relevance",
    value=0.85,
    comment="Automated relevance check",
)
```

### Score Types

| Type | Value | Use Case |
|------|-------|----------|
| Numeric | `float` | Quality scores (0-1), relevance, etc. |
| Boolean | `0` or `1` | Pass/fail, thumbs up/down |
| Categorical | `str` | Labels like "good", "bad", "hallucination" |

## Flushing Events

The SDK batches events and sends them asynchronously. In short-lived processes, explicitly flush:

```python
# In scripts, lambdas, or at app shutdown
langfuse.flush()
```

For web servers (FastAPI, Flask), the SDK handles flushing automatically. But add a shutdown hook for clean exits:

```python
import atexit

langfuse = get_client()
atexit.register(langfuse.flush)
```

## Configuration Options

```python
langfuse = Langfuse(
    secret_key="sk-lf-...",
    public_key="pk-lf-...",
    host="https://cloud.langfuse.com",
    release="v2.0.1",            # Default release for all traces
    debug=False,                  # Enable debug logging
    threads=4,                    # Background thread pool size
    flush_at=15,                  # Flush after N events
    flush_interval=0.5,           # Flush interval in seconds
    max_retries=3,                # Retry failed requests
    timeout=20,                   # HTTP timeout in seconds
    enabled=True,                 # Disable SDK entirely (for testing)
    sample_rate=1.0,              # Sampling rate (0.0-1.0)
)
```

### Sampling

Reduce costs in high-traffic production environments:

```python
langfuse = Langfuse(sample_rate=0.1)  # Trace 10% of requests
```

Or via environment variable:

```bash
LANGFUSE_SAMPLE_RATE=0.1
```

## Common Patterns

### FastAPI Middleware

```python
from fastapi import FastAPI, Request
from langfuse import get_client

app = FastAPI()
langfuse = get_client()

@app.middleware("http")
async def langfuse_middleware(request: Request, call_next):
    trace = langfuse.trace(
        name=f"{request.method} {request.url.path}",
        metadata={"method": request.method, "path": str(request.url)},
    )
    request.state.langfuse_trace = trace

    response = await call_next(request)

    trace.update(output={"status_code": response.status_code})
    return response
```

### Batch Processing

```python
langfuse = get_client()

for item in items:
    trace = langfuse.trace(
        name="batch-process",
        input=item,
        metadata={"batch_id": batch_id},
    )
    result = process(item)
    trace.update(output=result)

langfuse.flush()  # Flush after batch completes
```

## Pitfalls

1. **Not flushing** — The most common issue. Always call `langfuse.flush()` in scripts, lambdas, and batch jobs. Without it, events may be lost.

2. **Blocking the event loop** — `langfuse.flush()` is synchronous. In async code, run it in a thread or use `atexit`.

3. **Missing `end()`** — If not using context managers, call `.end()` on spans/generations to record accurate duration. Forgetting this makes timing data unreliable.

4. **Client instantiation** — Use `get_client()` for the singleton pattern. Creating multiple `Langfuse()` instances wastes resources and may cause duplicate traces.

5. **Large inputs/outputs** — Very large payloads (>1MB) slow down ingestion. Truncate or summarize large data before attaching to observations.
