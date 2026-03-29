# Best Practices

> Source: [langfuse.com/docs](https://langfuse.com/docs)

## Table of Contents

- [Instrumentation Best Practices](#instrumentation-best-practices)
- [Naming Conventions](#naming-conventions)
- [Production Configuration](#production-configuration)
- [Performance Optimization](#performance-optimization)
- [Error Handling](#error-handling)
- [Migration Guide](#migration-guide)
- [Testing with Langfuse](#testing-with-langfuse)
- [Team Workflows](#team-workflows)
- [Anti-Patterns](#anti-patterns)

---

## Instrumentation Best Practices

### Start with the @observe Decorator

Use decorators for most instrumentation. Switch to low-level SDK only when needed:

```python
# Preferred: decorator-based
@observe()
def my_pipeline(query: str) -> str:
    docs = retrieve(query)
    return generate(query, docs)

# Low-level: only for complex control flow
with langfuse.start_as_current_observation(as_type="span", name="complex-flow") as span:
    # Dynamic branching, retries, etc.
    pass
```

### Trace the Right Granularity

```python
# Good: meaningful operations
@observe()
def rag_pipeline(query: str) -> str: ...

@observe()
def retrieve_documents(query: str) -> list[str]: ...

@observe(as_type="generation")
def generate_answer(query: str, context: list[str]) -> str: ...

# Bad: too granular — noise
@observe()
def strip_whitespace(text: str) -> str: ...

@observe()
def split_into_words(text: str) -> list[str]: ...
```

### Always Set User and Session IDs

```python
@observe()
def handle_request(user_id: str, session_id: str, query: str):
    with propagate_attributes(
        user_id=user_id,
        session_id=session_id,
    ):
        return pipeline(query)
```

This enables per-user analytics, session grouping, and cost attribution.

### Use Meaningful Trace Names

```python
# Good: descriptive, hierarchical
trace = langfuse.trace(name="api/v2/chat")
trace = langfuse.trace(name="rag-pipeline/customer-support")

# Bad: generic
trace = langfuse.trace(name="request")
trace = langfuse.trace(name="process")
```

## Naming Conventions

| Entity | Convention | Example |
|--------|-----------|---------|
| Trace name | `feature/sub-feature` | `chat/customer-support` |
| Span name | `action-noun` | `document-retrieval` |
| Generation name | `model-purpose` | `gpt4o-answer-gen` |
| Score name | `category-metric` | `quality-relevance` |
| Tag | `lowercase-hyphen` | `production`, `experiment-a` |
| Metadata key | `snake_case` | `user_plan`, `request_source` |

## Production Configuration

### Environment Variables

```bash
# Required
LANGFUSE_SECRET_KEY="sk-lf-..."
LANGFUSE_PUBLIC_KEY="pk-lf-..."
LANGFUSE_BASE_URL="https://cloud.langfuse.com"

# Recommended for production
LANGFUSE_SAMPLE_RATE="1.0"       # Adjust based on volume
LANGFUSE_RELEASE="v2.0.1"        # Track deployments
LANGFUSE_ENABLED="true"          # Disable in tests
```

### Sampling Strategy

| Traffic Level | Recommended Sample Rate |
|--------------|------------------------|
| <1K traces/day | 1.0 (100%) |
| 1K-10K/day | 0.5-1.0 (50-100%) |
| 10K-100K/day | 0.1-0.5 (10-50%) |
| >100K/day | 0.01-0.1 (1-10%) |

```python
langfuse = Langfuse(sample_rate=0.1)
```

### Release Tracking

Tag every trace with the deployment version:

```python
import os

langfuse = Langfuse(release=os.getenv("GIT_SHA", "dev"))
```

This enables:
- Before/after deployment comparison
- Regression detection
- Rollback decisions based on quality metrics

## Performance Optimization

### SDK Performance

The SDK is designed for zero impact on application latency:

1. **Async batching** — events queued in memory, flushed in background threads
2. **No blocking** — `@observe()` adds <1ms overhead per call
3. **Graceful degradation** — SDK errors never crash your app
4. **Connection pooling** — reuses HTTP connections

### Reduce Payload Size

```python
# Don't log large embeddings or binary data
@observe(capture_input=False, capture_output=False)
def generate_embeddings(texts: list[str]) -> list[list[float]]:
    embeddings = model.encode(texts)
    # Log summary instead
    langfuse.update_current_span(
        metadata={"num_texts": len(texts), "dimensions": len(embeddings[0])},
    )
    return embeddings
```

### Batch Processing

```python
for batch in chunks(items, size=100):
    for item in batch:
        trace = langfuse.trace(name="batch-process", input=item)
        result = process(item)
        trace.update(output=result)

    langfuse.flush()  # Flush per batch, not per item
```

## Error Handling

### Trace Errors

```python
@observe()
def pipeline(query: str) -> str:
    try:
        result = process(query)
        return result
    except Exception as e:
        # Error auto-captured by @observe
        # But add context for debugging
        langfuse.update_current_span(
            level="ERROR",
            status_message=str(e),
            metadata={"error_type": type(e).__name__},
        )
        raise
```

### Fallback on SDK Failure

```python
from langfuse import get_client

try:
    langfuse = get_client()
except Exception:
    # SDK initialization failed — app continues without tracing
    langfuse = None

def maybe_trace(name, **kwargs):
    if langfuse:
        return langfuse.trace(name=name, **kwargs)
    return None
```

### Retry with Different Models

```python
@observe()
def resilient_generation(prompt: str) -> str:
    models = ["gpt-4o", "gpt-4o-mini", "claude-3.5-sonnet"]

    for model in models:
        try:
            return call_model(prompt, model=model)
        except Exception as e:
            langfuse.update_current_span(
                metadata={f"error_{model}": str(e)},
            )
            continue

    raise RuntimeError("All models failed")
```

## Migration Guide

### From No Observability

1. Install SDK: `pip install langfuse`
2. Set environment variables
3. Add `@observe()` to top-level request handlers
4. Add `@observe(as_type="generation")` to LLM calls
5. Deploy and verify traces appear in the dashboard

### From Custom Logging

Replace custom logging with Langfuse:

```python
# Before: custom logging
logger.info(f"LLM call: model={model}, tokens={tokens}, cost={cost}")

# After: structured Langfuse tracing
@observe(as_type="generation")
def call_llm(prompt: str):
    response = openai.chat.completions.create(...)
    langfuse.update_current_generation(
        model=response.model,
        usage={"input": response.usage.prompt_tokens, "output": response.usage.completion_tokens},
    )
    return response
```

### From LangSmith

1. Install Langfuse: `pip install langfuse`
2. Replace `LANGCHAIN_API_KEY` with `LANGFUSE_SECRET_KEY` + `LANGFUSE_PUBLIC_KEY`
3. Replace `LANGCHAIN_TRACING_V2=true` with Langfuse callback handler
4. Replace LangSmith datasets with Langfuse datasets
5. Update evaluation workflows

## Testing with Langfuse

### Disable in Tests

```python
# In conftest.py or test setup
import os
os.environ["LANGFUSE_ENABLED"] = "false"
```

### Mock the SDK

```python
from unittest.mock import patch

@patch("langfuse.get_client")
def test_pipeline(mock_langfuse):
    mock_langfuse.return_value = MagicMock()
    result = my_pipeline("test query")
    assert result is not None
```

## Team Workflows

### Developer Workflow

1. Develop locally with `LANGFUSE_ENABLED=true` pointed at a dev project
2. Review traces in dashboard during development
3. Run experiments against datasets before merging
4. PR review includes Langfuse experiment results

### Prompt Engineering Workflow

1. Product/domain team edits prompts in Langfuse UI
2. Label new version as "staging"
3. Run experiments against test datasets
4. If quality meets threshold, promote to "production"
5. Monitor production metrics in dashboard

### Incident Response

1. Alert triggers from quality score drop
2. Filter dashboard by time range around the alert
3. Inspect individual failing traces
4. Identify root cause (bad prompt, model issue, data problem)
5. Fix and verify with experiments

## Anti-Patterns

1. **Over-instrumentation** — Don't trace every function. Focus on meaningful operations (LLM calls, retrieval, tool execution, top-level handlers).

2. **Logging sensitive data** — Always mask PII before sending to Langfuse. Use `capture_input=False` for sensitive functions.

3. **Ignoring costs** — Monitor costs early. A misconfigured loop can generate thousands of traces in minutes.

4. **No sampling in production** — High-traffic apps should sample. 100% tracing at 1M requests/day is expensive.

5. **Not using sessions** — For chatbots and multi-turn apps, always set `session_id`. Without it, you lose conversation context.

6. **Hardcoding API keys** — Use environment variables. Never commit keys to version control.

7. **Not flushing in scripts** — The #1 cause of "my traces don't appear." Always call `langfuse.flush()` before script exit.
