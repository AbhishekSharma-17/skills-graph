# Middleware & Observability

## Table of Contents
1. [Middleware Overview](#middleware-overview)
2. [Creating Middleware](#creating-middleware)
3. [Common Middleware Patterns](#common-middleware-patterns)
4. [Observability & Telemetry](#observability--telemetry)
5. [Debugging](#debugging)
6. [DevUI](#devui)

---

## Middleware Overview

Middleware intercepts agent execution at defined points — before the LLM call, after the response, or around tool execution. Middleware functions form a pipeline (stack).

### Execution Order

```
Request → Middleware A (pre) → Middleware B (pre) → Agent/LLM → Middleware B (post) → Middleware A (post) → Response
```

Middleware executes in registration order for pre-processing, and reverse order for post-processing (like a stack).

---

## Creating Middleware

### Basic Middleware

```python
async def LoggingMiddleware(req):
    """Log all agent interactions"""
    print(f"[INPUT] {req.message}")

    result = await req.invoke()  # Call next handler

    print(f"[OUTPUT] {result}")
    return result

# Apply to agent
agent = original_agent.as_builder()\
    .use(runFunc=LoggingMiddleware)\
    .build()
```

### Middleware with State

```python
class MetricsMiddleware:
    def __init__(self):
        self.call_count = 0
        self.total_time = 0

    async def __call__(self, req):
        self.call_count += 1
        start = time.time()

        result = await req.invoke()

        self.total_time += time.time() - start
        print(f"Call #{self.call_count}, Avg time: {self.total_time/self.call_count:.2f}s")
        return result

metrics = MetricsMiddleware()
agent = original_agent.as_builder()\
    .use(runFunc=metrics)\
    .build()
```

### Streaming Middleware

```python
async def StreamLoggingMiddleware(req):
    """Middleware for streaming responses"""
    print(f"[STREAM START] {req.message}")

    async for chunk in req.invoke():
        # Can inspect/modify each chunk
        print(f"[CHUNK] {chunk.text}", end="")
        yield chunk

    print("\n[STREAM END]")

agent = original_agent.as_builder()\
    .use(runStreamingFunc=StreamLoggingMiddleware)\
    .build()
```

### Multiple Middleware

```python
agent = original_agent.as_builder()\
    .use(runFunc=AuthMiddleware)\
    .use(runFunc=LoggingMiddleware)\
    .use(runFunc=RetryMiddleware)\
    .use(runFunc=CacheMiddleware)\
    .build()
```

---

## Common Middleware Patterns

### Input Validation

```python
async def InputValidationMiddleware(req):
    """Validate and sanitize input before agent processes it"""
    message = req.message

    # Check for empty input
    if not message or not message.strip():
        return "Please provide a message."

    # Check length
    if len(message) > 10000:
        return "Message too long. Please keep it under 10,000 characters."

    # Sanitize PII (basic example)
    import re
    message = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN REDACTED]', message)

    req.message = message
    return await req.invoke()
```

### Retry with Backoff

```python
async def RetryMiddleware(req):
    """Retry on transient failures with exponential backoff"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return await req.invoke()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait = 2 ** attempt
            print(f"Retry {attempt + 1}/{max_retries} in {wait}s: {e}")
            await asyncio.sleep(wait)
```

### Response Caching

```python
from functools import lru_cache
import hashlib

cache = {}

async def CacheMiddleware(req):
    """Cache identical requests"""
    key = hashlib.sha256(req.message.encode()).hexdigest()

    if key in cache:
        print("[CACHE HIT]")
        return cache[key]

    result = await req.invoke()
    cache[key] = result
    return result
```

### Rate Limiting

```python
import asyncio
from collections import deque

class RateLimiter:
    def __init__(self, max_calls: int, period: float):
        self.max_calls = max_calls
        self.period = period
        self.calls = deque()

    async def __call__(self, req):
        now = asyncio.get_event_loop().time()

        # Remove old calls
        while self.calls and self.calls[0] < now - self.period:
            self.calls.popleft()

        if len(self.calls) >= self.max_calls:
            wait = self.calls[0] + self.period - now
            await asyncio.sleep(wait)

        self.calls.append(now)
        return await req.invoke()

rate_limiter = RateLimiter(max_calls=10, period=60)  # 10 calls per minute
```

### Content Filtering

```python
async def ContentFilterMiddleware(req):
    """Filter inappropriate content from responses"""
    result = await req.invoke()

    # Check response for policy violations
    if contains_prohibited_content(result):
        return "I'm unable to provide that information. Let me help with something else."

    return result
```

### Audit Logging

```python
async def AuditMiddleware(req):
    """Log all interactions for compliance"""
    import json
    from datetime import datetime

    audit_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "input": req.message,
        "session_id": req.session.id if req.session else None,
    }

    result = await req.invoke()

    audit_entry["output"] = str(result)[:500]  # Truncate for storage
    await audit_log.write(json.dumps(audit_entry))

    return result
```

---

## Observability & Telemetry

### OpenTelemetry Integration

The framework has built-in OpenTelemetry support. Traces are automatically created for agent runs, tool calls, and workflow steps.

### Enable Tracing

```python
import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Configure OpenTelemetry
provider = TracerProvider()
provider.add_span_processor(
    SimpleSpanProcessor(OTLPSpanExporter(endpoint="http://localhost:4317"))
)
trace.set_tracer_provider(provider)

# Enable logging
logging.basicConfig(level=logging.DEBUG)
```

### What Gets Traced

| Span | Attributes |
|------|-----------|
| `agent.run` | agent name, message, session ID |
| `agent.tool_call` | tool name, parameters, result |
| `workflow.execute` | workflow name, unit name |
| `middleware.execute` | middleware name, duration |
| `llm.chat` | model, tokens used, latency |

### Azure Monitor Integration

```python
from azure.monitor.opentelemetry import configure_azure_monitor

configure_azure_monitor(
    connection_string=os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"],
)
```

### Custom Metrics

```python
from opentelemetry import metrics

meter = metrics.get_meter("agent-framework")
request_counter = meter.create_counter("agent.requests")
latency_histogram = meter.create_histogram("agent.latency")

async def MetricsMiddleware(req):
    request_counter.add(1, {"agent": req.agent_name})
    start = time.time()

    result = await req.invoke()

    latency = time.time() - start
    latency_histogram.record(latency, {"agent": req.agent_name})
    return result
```

---

## Debugging

### Enable Debug Logging

```python
import logging

# See all framework internals
logging.basicConfig(level=logging.DEBUG)

# Or target specific loggers
logging.getLogger("agent_framework").setLevel(logging.DEBUG)
logging.getLogger("agent_framework.tools").setLevel(logging.DEBUG)
```

### Debug Middleware

```python
async def DebugMiddleware(req):
    """Print detailed execution info"""
    print(f"=== Agent: {req.agent_name} ===")
    print(f"Message: {req.message}")
    print(f"Session: {req.session.id if req.session else 'None'}")
    print(f"Tools: {[t.__name__ for t in req.tools]}")

    result = await req.invoke()

    print(f"Result type: {type(result)}")
    print(f"Result: {str(result)[:200]}")
    print("=" * 40)
    return result
```

### Debugging Checklist

1. Environment variables set correctly?
2. Authentication working (`az login`)?
3. Deployment name matches Azure portal?
4. Tools have docstrings and type hints?
5. Session is being passed (if multi-turn)?
6. Middleware not blocking execution?
7. Log level set to DEBUG?
8. Network/firewall allowing connections?

---

## DevUI

The Agent Framework DevUI is a VS Code extension for interactive debugging.

### Setup

```bash
pip install agent-framework-devui --pre
```

### Features

- Interactive agent playground
- Message streaming visualization
- Tool call inspection
- Execution graph visualization
- Session state inspection
- Performance metrics dashboard

### Launch DevUI

```python
from agent_framework.devui import launch_devui

# Opens browser-based debugging UI
await launch_devui(agent, port=8080)
```

The DevUI shows real-time agent execution, tool calls, token usage, and allows interactive testing.
