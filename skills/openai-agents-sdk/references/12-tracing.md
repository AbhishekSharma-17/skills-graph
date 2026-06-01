# Tracing — Observability & Debugging

> Source: [openai.github.io/openai-agents-python/tracing](https://openai.github.io/openai-agents-python/tracing/)

## Overview

The SDK includes built-in tracing that collects a comprehensive record of events during agent runs: LLM generations, tool calls, handoffs, guardrails, and custom events. Traces can be viewed in the OpenAI Traces dashboard for debugging, visualization, and production monitoring.

## Core Concepts

| Concept | Description |
|---------|-------------|
| **Trace** | End-to-end workflow operation container |
| **Span** | Individual operation within a trace (timed, hierarchical) |
| **trace_id** | Unique identifier (format: `trace_<32_alphanumeric>`) |
| **group_id** | Optional field linking related traces |
| **workflow_name** | Logical workflow identifier |

## Default Tracing Behavior

The SDK automatically creates spans for:

| Operation | Span Function |
|-----------|--------------|
| `Runner.run()` call | Entire trace |
| Agent execution | `agent_span()` |
| LLM calls | `generation_span()` |
| Tool invocations | `function_span()` |
| Guardrail checks | `guardrail_span()` |
| Agent transfers | `handoff_span()` |
| Speech-to-text | `transcription_span()` |
| Text-to-speech | `speech_span()` |

## Configuring Traces

### Via RunConfig

```python
from agents import RunConfig

result = await Runner.run(
    agent, "Hello",
    run_config=RunConfig(
        workflow_name="customer-support",
        trace_id="trace_custom_abc123",
        group_id="session_456",
        trace_include_sensitive_data=False,
    ),
)
```

### Custom Trace Boundaries

```python
from agents import trace

with trace("My Workflow") as my_trace:
    result1 = await Runner.run(agent1, "Step 1")
    result2 = await Runner.run(agent2, "Step 2")
    # Both runs appear under the same trace
```

Manual lifecycle management:

```python
from agents import trace

my_trace = trace("Manual Workflow")
my_trace.start()
try:
    result = await Runner.run(agent, "Hello")
finally:
    my_trace.finish()
```

## Custom Spans

Add application-specific spans to traces:

```python
from agents import custom_span

with custom_span("data_processing"):
    data = load_data()
    processed = transform(data)
    
with custom_span("validation", data={"records": len(processed)}):
    validate(processed)
```

## Disabling Tracing

Three methods:

```python
# Method 1: Environment variable
# export OPENAI_AGENTS_DISABLE_TRACING=1

# Method 2: Code — global
from agents import set_tracing_disabled
set_tracing_disabled(True)

# Method 3: Per-run
from agents import RunConfig
result = await Runner.run(
    agent, "Hello",
    run_config=RunConfig(tracing_disabled=True),
)
```

## Sensitive Data Control

The SDK captures potentially sensitive data in generation and function spans. Control this behavior:

```python
# Via RunConfig (default: True — sensitive data included)
config = RunConfig(trace_include_sensitive_data=False)

# Via environment variable
# export OPENAI_AGENTS_TRACE_INCLUDE_SENSITIVE_DATA=false

# For voice pipelines
# VoicePipelineConfig(trace_include_sensitive_audio_data=False)
```

When disabled, LLM inputs/outputs and tool call arguments are excluded from traces.

## Custom Trace Processors

### Add Supplementary Processing

```python
from agents import add_trace_processor

class LoggingProcessor:
    def process_trace(self, trace):
        print(f"Trace: {trace.trace_id} — {trace.workflow_name}")

    def process_span(self, span):
        print(f"Span: {span.span_id} — {span.span_type}")

    def shutdown(self):
        pass

add_trace_processor(LoggingProcessor())
```

### Replace Default Processors

```python
from agents import set_trace_processors

set_trace_processors([MyCustomProcessor()])
```

## Flushing Traces

For background workers and long-running processes, ensure traces are exported:

```python
from agents import flush_traces, trace

try:
    with trace("background_task"):
        result = await Runner.run(agent, "Process data")
finally:
    flush_traces()  # Synchronous — blocks until export completes
```

The default `BatchTraceProcessor` exports periodically. `flush_traces()` forces immediate export.

## Tracing with Non-OpenAI Models

When using non-OpenAI models, set a separate OpenAI key for trace export:

```python
from agents import set_tracing_export_api_key
import os

set_tracing_export_api_key(os.environ["OPENAI_API_KEY"])
```

Or per-run:

```python
config = RunConfig(tracing={"api_key": "sk-..."})
```

## Ecosystem Integrations

The tracing system integrates with major observability platforms:

| Platform | Type |
|----------|------|
| **Weights & Biases** | ML experiment tracking |
| **Arize Phoenix** | ML observability |
| **MLflow** | ML lifecycle management |
| **Braintrust** | LLM evaluation |
| **Pydantic Logfire** | Python observability |
| **LangSmith** | LLM application tracing |
| **Langfuse** | LLM engineering platform |
| **Datadog** | Infrastructure monitoring |
| **PostHog** | Product analytics |

## Trace Visualization

View traces in the OpenAI dashboard:
1. Navigate to the Traces tab in the OpenAI platform
2. Filter by `workflow_name`, `trace_id`, or `group_id`
3. Inspect individual spans, timings, and token usage
4. Debug agent behavior through the span hierarchy

## Production Tracing Pattern

```python
from agents import Agent, Runner, RunConfig, trace, flush_traces
import logging

logger = logging.getLogger(__name__)

async def handle_request(user_id: str, message: str):
    config = RunConfig(
        workflow_name="production-support",
        group_id=f"user_{user_id}",
        trace_include_sensitive_data=False,
    )

    try:
        with trace(f"support-request-{user_id}"):
            result = await Runner.run(agent, message, run_config=config)
            return result.final_output
    except Exception as e:
        logger.error(f"Agent error for user {user_id}: {e}")
        raise
    finally:
        flush_traces()
```

## Common Pitfalls

- **Forgetting to flush**: In background workers, traces may be lost if the process exits before the batch processor exports
- **Sensitive data in production**: Default `trace_include_sensitive_data=True` captures LLM I/O — disable for production with PII
- **Non-OpenAI tracing**: Without `set_tracing_export_api_key`, traces from non-OpenAI models silently fail to export
- **Custom processor shutdown**: Implement `shutdown()` in custom processors to flush pending data on exit

## Related Topics

- **Running Agents:** `03-running-agents.md` — RunConfig tracing settings
- **Models:** `09-models.md` — Tracing with non-OpenAI models
- **Guardrails:** `05-guardrails.md` — Guardrail spans in traces
