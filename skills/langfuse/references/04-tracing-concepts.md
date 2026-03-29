# Tracing Concepts

> Source: [langfuse.com/docs/observability/overview](https://langfuse.com/docs/observability/overview)

## Table of Contents

- [Core Model](#core-model)
- [Traces](#traces)
- [Observations](#observations)
- [Spans](#spans)
- [Generations](#generations)
- [Events](#events)
- [Sessions](#sessions)
- [Users](#users)
- [Tags and Metadata](#tags-and-metadata)
- [Environments](#environments)
- [Levels](#levels)
- [Cost Tracking](#cost-tracking)
- [Latency Tracking](#latency-tracking)

---

## Core Model

Langfuse organizes observability data in a hierarchical model:

```
Project
└── Traces (one per request/invocation)
    ├── Spans (non-LLM operations)
    │   └── Spans (nested)
    ├── Generations (LLM calls)
    └── Events (point-in-time markers)
```

Each trace belongs to a project. Traces contain observations (spans, generations, events) that can be nested to any depth.

## Traces

A **trace** represents a single end-to-end execution — an API request, a user message, a batch job item, or an agent run.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | `str` | Unique identifier (auto-generated or custom) |
| `name` | `str` | Descriptive name (e.g., "chat-request", "rag-pipeline") |
| `input` | `any` | The input to the traced operation |
| `output` | `any` | The output of the traced operation |
| `user_id` | `str` | Associated user identifier |
| `session_id` | `str` | Session identifier for multi-turn grouping |
| `tags` | `list[str]` | Filterable string tags |
| `metadata` | `dict` | Arbitrary key-value metadata |
| `release` | `str` | Application version/release |
| `public` | `bool` | Whether the trace has a public share link |

### Custom Trace IDs

Use custom IDs to correlate Langfuse traces with your internal request IDs:

```python
trace = langfuse.trace(
    id="my-custom-request-id-123",
    name="api-request",
)
```

### Updating Traces

Traces can be updated after creation — useful when you don't know the output upfront:

```python
trace = langfuse.trace(name="pipeline", input=query)
# ... processing ...
trace.update(output=result, metadata={"duration_ms": elapsed})
```

## Observations

Observations are the building blocks within a trace. Three types exist:

### Spans

Non-LLM operations: data retrieval, transformations, tool calls, business logic.

```python
span = trace.span(
    name="document-retrieval",
    input={"query": "Langfuse features"},
    metadata={"source": "pinecone", "top_k": 5},
)
span.update(output={"doc_count": 5})
span.end()
```

### Generations

LLM calls with model-specific tracking (tokens, cost, model parameters):

```python
generation = trace.generation(
    name="answer-gen",
    model="gpt-4o",
    model_parameters={"temperature": 0.7},
    input=[{"role": "user", "content": "Hello"}],
)
generation.update(
    output="Hi there!",
    usage={"input": 10, "output": 5},
)
generation.end()
```

### Events

Point-in-time markers without duration — for logging decisions, state changes, or checkpoints:

```python
trace.event(
    name="cache-hit",
    input={"key": "user-123-query"},
    metadata={"cache_type": "redis"},
)
```

## Sessions

Sessions group related traces — typically for multi-turn conversations or user interactions across multiple requests.

```python
# All traces with the same session_id are grouped
trace1 = langfuse.trace(name="turn-1", session_id="conv-123")
trace2 = langfuse.trace(name="turn-2", session_id="conv-123")
trace3 = langfuse.trace(name="turn-3", session_id="conv-123")
```

In the Langfuse UI, sessions show:
- All traces in chronological order
- Aggregate metrics (total cost, latency, tokens)
- Session-level scoring

## Users

Track per-user metrics by setting `user_id`:

```python
trace = langfuse.trace(
    name="chat",
    user_id="user-abc-123",
)
```

The Langfuse dashboard aggregates metrics per user:
- Total traces, cost, tokens
- Average latency
- Quality scores

## Tags and Metadata

### Tags

String labels for filtering in the UI:

```python
trace = langfuse.trace(
    name="request",
    tags=["production", "experiment-a", "gpt-4o"],
)
```

Use tags for: environments, experiments, features, model names, teams.

### Metadata

Arbitrary key-value pairs for context. Top-level keys are filterable in dashboards:

```python
trace = langfuse.trace(
    name="request",
    metadata={
        "user_plan": "enterprise",  # Filterable
        "request_source": "api",    # Filterable
        "debug_info": {"internal": "data"},  # Nested, not filterable
    },
)
```

## Environments

Separate traces across deployment stages:

```python
# Set via environment variable
# LANGFUSE_TRACING_ENVIRONMENT=staging

# Or per-trace via tags
trace = langfuse.trace(
    name="request",
    tags=["staging"],
)
```

## Levels

Observations have severity levels for filtering:

| Level | Use Case |
|-------|----------|
| `DEBUG` | Detailed internal state |
| `DEFAULT` | Normal operations |
| `WARNING` | Rate limits, fallbacks, degraded performance |
| `ERROR` | Failures, exceptions, timeouts |

```python
span.update(level="WARNING", status_message="Rate limited, using fallback model")
```

## Cost Tracking

Langfuse automatically calculates costs for known models. For custom models, provide cost data:

```python
generation = trace.generation(
    name="custom-model",
    model="my-fine-tuned-model",
    usage={
        "input": 500,
        "output": 200,
    },
    # Custom cost (in USD)
    usage_details={
        "input_cost": 0.001,
        "output_cost": 0.002,
    },
)
```

### Supported Models (Auto-Cost)

Langfuse maintains a model cost registry that includes:
- OpenAI (GPT-4o, GPT-4, GPT-3.5, etc.)
- Anthropic (Claude 3.5, Claude 3, etc.)
- Google (Gemini Pro, etc.)
- AWS Bedrock models
- Azure OpenAI models
- Many open-source models

## Latency Tracking

Latency is computed from observation start/end times:

- **End-to-end latency**: Trace start to trace end
- **LLM latency**: Generation start to generation end
- **Time-to-first-token**: For streaming generations

```python
# Latency tracked automatically via start/end timing
with langfuse.start_as_current_observation(
    as_type="generation", name="streaming-llm"
) as gen:
    # First token latency captured when first output arrives
    for chunk in stream:
        gen.update(output=chunk)  # Incrementally update
```

Dashboard breakdowns:
- P50, P90, P95, P99 latency per model
- Latency trends over time
- Per-endpoint latency analysis
