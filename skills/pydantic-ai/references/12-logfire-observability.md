# Logfire and Observability

> Source: [pydantic.dev/docs/ai/integrations/logfire](https://pydantic.dev/docs/ai/integrations/logfire/)

## Table of Contents

- [Overview](#overview)
- [Setup](#setup)
- [Instrumenting Agents](#instrumenting-agents)
- [What Gets Traced](#what-gets-traced)
- [HTTP Request Monitoring](#http-request-monitoring)
- [OpenTelemetry Integration](#opentelemetry-integration)
- [Privacy Controls](#privacy-controls)
- [Instrumentation Versions](#instrumentation-versions)
- [Use Cases](#use-cases)
- [Common Pitfalls](#common-pitfalls)

## Overview

Pydantic Logfire is the observability platform designed for Pydantic AI. Built on OpenTelemetry, it provides detailed traces of agent runs including model API calls, tool executions, token usage, and latency. Logfire comes bundled with `pydantic-ai` (not the slim install).

LLM applications are slow, unreliable, expensive, and non-deterministic — Logfire makes these challenges observable and debuggable.

## Setup

### Installation and Auth

```bash
pip install pydantic-ai   # Logfire included
logfire auth               # Authenticate with Logfire
logfire projects new       # Create a project
```

### Basic Instrumentation

```python
import logfire
from pydantic_ai import Agent

logfire.configure()
logfire.instrument_pydantic_ai()

agent = Agent('openai:gpt-5.2', instructions='Be concise.')
result = agent.run_sync('What is Python?')
```

### Instrument All Agents

```python
from pydantic_ai import Agent

Agent.instrument_all()  # Instrument every agent created
```

## What Gets Traced

When Logfire is enabled, it automatically records:

| Trace | Details |
|-------|---------|
| **Agent run** | Full run lifecycle with duration |
| **Model requests** | Each API call with messages, settings, and response |
| **Tool calls** | Function name, arguments, return value, duration |
| **Token usage** | Input tokens, output tokens, total per request |
| **Retries** | Each retry attempt with the error message |
| **Streaming** | Stream lifecycle with progressive output |
| **Output validation** | Validation attempts and failures |

### Custom Metadata

Attach contextual data to traces:

```python
agent = Agent(
    'openai:gpt-5.2',
    name='support-agent',
    metadata={'team': 'support', 'version': '2.1'},
)
```

## HTTP Request Monitoring

Capture raw HTTP requests to model providers:

```python
import logfire

logfire.configure()
logfire.instrument_httpx(capture_all=True)
logfire.instrument_pydantic_ai()
```

This captures the full request/response cycle to the API, useful for debugging authentication issues, rate limits, and API errors.

## OpenTelemetry Integration

Pydantic AI uses OpenTelemetry Semantic Conventions for GenAI, enabling compatibility with any OTel-compatible backend.

### Alternative Backends

Works with: Langfuse, Weights & Biases Weave, Arize Phoenix, Jaeger, and any OTel collector.

### Raw OpenTelemetry Setup

```python
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry import trace

exporter = OTLPSpanExporter(endpoint='https://otel-collector.example.com/v1/traces')
tracer_provider = TracerProvider()
tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
trace.set_tracer_provider(tracer_provider)

from pydantic_ai import Agent
Agent.instrument_all()
```

### Custom Spans

Add custom spans around your application code:

```python
import logfire

with logfire.span('process_request', user_id='123'):
    result = await agent.run('Process this request')
    logfire.info('Request processed', output_length=len(result.output))
```

## Privacy Controls

Control what data is sent to the observability backend:

```python
from pydantic_ai import InstrumentationSettings

InstrumentationSettings(
    include_content=False,         # Exclude prompts and completions
    include_binary_content=False,  # Exclude binary data (images)
)
```

### Per-Agent Privacy

```python
agent = Agent(
    'openai:gpt-5.2',
    instrumentation_settings=InstrumentationSettings(
        include_content=False,
    ),
)
```

## Instrumentation Versions

Pydantic AI supports multiple instrumentation format versions:

| Version | Changes |
|---------|---------|
| v1 | Original format |
| v2 (default) | Improved attributes |
| v3+ | Spec-compliant span names (`invoke_agent`) |
| v5 | Enhanced deferred tool call handling |

```python
logfire.instrument_pydantic_ai(version=3)
```

## Use Cases

### Debugging Agent Behavior

```python
import logfire

logfire.configure()
logfire.instrument_pydantic_ai()

agent = Agent('openai:gpt-5.2')

@agent.tool_plain
def lookup_user(name: str) -> str:
    logfire.info('Looking up user', name=name)
    return f'User {name} found'

result = agent.run_sync('Find user Alice')
# Full trace visible in Logfire dashboard:
# - Agent run span
#   - Model request span (messages, tokens)
#   - Tool call: lookup_user(name='Alice')
#   - Model request span (final response)
```

### Performance Monitoring

Query Logfire for latency and cost analysis:

- Average response time per agent
- Token usage trends over time
- Tool execution latency
- Error rates by model provider

### Cost Analysis

Track API costs by monitoring token usage across all agent runs:

```python
result = agent.run_sync('Hello')
usage = result.usage()
print(f'Input: {usage.request_tokens}, Output: {usage.response_tokens}')
```

Combined with Logfire, you can aggregate costs across agents, users, and time periods.

## Common Pitfalls

- **Forgetting `logfire.configure()`** — instrumentation does nothing without configuration
- **Sensitive data exposure** — use `include_content=False` for agents handling PII or secrets
- **Slim install** — `pydantic-ai-slim` doesn't include Logfire; install `logfire` separately
- **OTel export errors** — if the OTel collector is unreachable, traces are silently dropped; check exporter logs
- **Version mismatch** — different instrumentation versions produce different span structures; pick one version per deployment

## Related

- `01-agents.md` — Agent configuration with metadata
- `11-testing-evals.md` — Evals that integrate with Logfire
- `08-models.md` — Model provider configuration
