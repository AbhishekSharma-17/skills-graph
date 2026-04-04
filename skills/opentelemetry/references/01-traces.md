# OpenTelemetry — Traces

> Source: [opentelemetry.io/docs/concepts/signals/traces](https://opentelemetry.io/docs/concepts/signals/traces/)

## Table of Contents

- [What Are Traces](#what-are-traces)
- [Spans](#spans)
- [Span Context](#span-context)
- [Span Kinds](#span-kinds)
- [Attributes](#attributes)
- [Events](#events)
- [Links](#links)
- [Span Status](#span-status)
- [Tracer Provider and Tracer](#tracer-provider-and-tracer)
- [Span Processors](#span-processors)
- [Trace Exporters](#trace-exporters)
- [Creating Traces in Python](#creating-traces-in-python)
- [Creating Traces in Node.js](#creating-traces-in-nodejs)
- [Best Practices](#best-practices)
- [Common Pitfalls](#common-pitfalls)

---

## What Are Traces

A trace represents the complete journey of a request through a distributed system. It is composed of one or more **spans** arranged in a parent-child hierarchy, forming a directed acyclic graph (DAG) that shows how the request propagated across services.

```
Trace (trace_id: abc123)
│
├── [Server] POST /api/orders (200ms)
│   ├── [Internal] validate_input (5ms)
│   ├── [Client] DB: INSERT orders (50ms)
│   │   └── [Server] PostgreSQL query (45ms)
│   └── [Client] HTTP: POST /payments (120ms)
│       └── [Server] process_payment (110ms)
```

Every span in a trace shares the same `trace_id`. The root span has no parent. Child spans reference their parent via `parent_span_id`.

## Spans

A span represents a single unit of work with:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Operation name (e.g., `HTTP GET /users`) |
| `context` | SpanContext | Trace ID, Span ID, flags, state |
| `parent_span_id` | string | Parent span's ID (empty for root) |
| `start_time` | timestamp | When the operation began |
| `end_time` | timestamp | When the operation completed |
| `kind` | SpanKind | Client, Server, Internal, Producer, Consumer |
| `attributes` | map | Key-value metadata |
| `events` | list | Timestamped annotations |
| `links` | list | References to spans in other traces |
| `status` | Status | Unset, Ok, or Error |

**Example span JSON:**

```json
{
  "name": "GET /api/users",
  "context": {
    "trace_id": "7bba9f33312b3dbb8b2c2c62bb7abe2d",
    "span_id": "086e83747d0e381e"
  },
  "parent_id": "a]b1c2d3e4f5a6b7c",
  "start_time": "2026-01-01T00:00:00.000Z",
  "end_time": "2026-01-01T00:00:00.150Z",
  "kind": "SERVER",
  "attributes": {
    "http.method": "GET",
    "http.route": "/api/users",
    "http.status_code": 200
  },
  "status": { "code": "STATUS_CODE_UNSET" }
}
```

## Span Context

SpanContext is an immutable object carried across process boundaries:

| Field | Description |
|-------|-------------|
| `trace_id` | 16-byte globally unique trace identifier |
| `span_id` | 8-byte unique span identifier within the trace |
| `trace_flags` | Bit field — currently only `sampled` flag (bit 0) |
| `trace_state` | Vendor-specific key-value pairs (W3C standard) |

SpanContext is what enables distributed tracing — it propagates via HTTP headers, gRPC metadata, or message queue attributes to correlate spans across service boundaries.

## Span Kinds

SpanKind helps trace visualization tools assemble spans correctly:

| Kind | Use Case | Example |
|------|----------|---------|
| `CLIENT` | Synchronous outgoing call | HTTP request to another service, DB query |
| `SERVER` | Synchronous incoming call | Handling an HTTP request, gRPC method |
| `INTERNAL` | In-process operation | Function call, middleware, computation |
| `PRODUCER` | Creates async job | Publishing to a queue, emitting an event |
| `CONSUMER` | Processes async job | Consuming from Kafka, processing a queue message |

**Matching rules:**

- A `CLIENT` span on one service should correspond to a `SERVER` span on the target
- A `PRODUCER` span should correspond to a `CONSUMER` span (potentially much later)
- `INTERNAL` spans are never matched with remote spans

## Attributes

Key-value pairs that annotate spans with metadata:

```python
# String, bool, int, float, or arrays thereof
span.set_attribute("user.id", "usr_12345")
span.set_attribute("cache.hit", True)
span.set_attribute("retry.count", 3)
span.set_attribute("request.sizes", [100, 200, 50])
```

**Rules:**

- Keys must be non-null, non-empty strings
- Values: string, bool, int, float, or homogeneous arrays of these
- Use semantic conventions for standard operations (see `08-semantic-conventions.md`)
- Set attributes before the span ends — attributes set after `end()` are dropped

**Common semantic attributes:**

```python
from opentelemetry.semconv.trace import SpanAttributes

span.set_attribute(SpanAttributes.HTTP_METHOD, "GET")
span.set_attribute(SpanAttributes.HTTP_URL, "https://api.example.com/users")
span.set_attribute(SpanAttributes.HTTP_STATUS_CODE, 200)
span.set_attribute(SpanAttributes.DB_SYSTEM, "postgresql")
span.set_attribute(SpanAttributes.DB_STATEMENT, "SELECT * FROM users WHERE id = $1")
```

## Events

Timestamped annotations within a span, useful for marking meaningful moments:

```python
span.add_event("cache.miss", {"cache.key": "user:123"})

# With explicit timestamp
from datetime import datetime
span.add_event("retry.attempt", {"attempt": 2}, timestamp=datetime.now())
```

**When to use events vs. attributes:**

- **Events**: When the timestamp matters (cache miss at T+50ms, retry at T+100ms)
- **Attributes**: When only the value matters (total retry count, final status)

**When to use events vs. child spans:**

- **Events**: Quick annotations, no duration needed
- **Child spans**: Operations with meaningful duration that should be visible in the trace timeline

## Links

Create causal relationships between spans, especially across traces:

```python
# Link to a span that triggered this work
link = trace.Link(
    previous_span_context,
    attributes={"link.type": "triggered_by"}
)
with tracer.start_as_current_span("process-batch", links=[link]):
    pass
```

**Use cases:**

- Batch processing: link consumer spans to multiple producer spans
- Fan-out: link each downstream span to the originating span
- Retries: link retry spans to the original failed span
- Workflows: link steps that span multiple traces

## Span Status

Three possible status codes:

| Code | Meaning | When to Set |
|------|---------|-------------|
| `UNSET` | Default — operation succeeded or status not explicitly set | Don't set — this is the default |
| `ERROR` | Operation failed | On exceptions, error responses, timeouts |
| `OK` | Explicitly marked successful | Only when you want to override `UNSET` |

```python
from opentelemetry.trace import Status, StatusCode

try:
    result = do_work()
except Exception as ex:
    span.set_status(Status(StatusCode.ERROR, str(ex)))
    span.record_exception(ex)  # Adds an event with exception details
    raise
```

**Important:** `UNSET` does NOT mean error — it means no explicit status was set. Most spans should remain `UNSET`. Only set `ERROR` on actual failures.

## Tracer Provider and Tracer

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource

# TracerProvider: configured once at application startup
resource = Resource.create({
    "service.name": "order-service",
    "service.version": "2.1.0",
    "deployment.environment": "production",
})
provider = TracerProvider(resource=resource)
trace.set_tracer_provider(provider)

# Tracer: obtained per module/library
tracer = trace.get_tracer(
    "order.processing",         # instrumentation scope name
    "1.0.0",                    # instrumentation scope version (optional)
)
```

## Span Processors

Processors handle spans between creation and export:

| Processor | Behavior | Use Case |
|-----------|----------|----------|
| `SimpleSpanProcessor` | Exports synchronously on span end | Development, debugging |
| `BatchSpanProcessor` | Batches and exports asynchronously | **Production** (always use this) |

```python
from opentelemetry.sdk.trace.export import BatchSpanProcessor

provider.add_span_processor(
    BatchSpanProcessor(
        exporter,
        max_queue_size=2048,          # Max spans queued
        max_export_batch_size=512,    # Max spans per export
        schedule_delay_millis=5000,   # Export interval
        export_timeout_millis=30000,  # Export timeout
    )
)
```

## Trace Exporters

| Exporter | Package | Protocol |
|----------|---------|----------|
| Console | `opentelemetry-sdk` | stdout |
| OTLP/gRPC | `opentelemetry-exporter-otlp-proto-grpc` | gRPC |
| OTLP/HTTP | `opentelemetry-exporter-otlp-proto-http` | HTTP/protobuf |
| Jaeger | `opentelemetry-exporter-jaeger` | Thrift/gRPC |
| Zipkin | `opentelemetry-exporter-zipkin` | HTTP/JSON |

## Creating Traces in Python

```python
from opentelemetry import trace

tracer = trace.get_tracer("my.service")

# Context manager (recommended)
def handle_request(request):
    with tracer.start_as_current_span("handle_request") as span:
        span.set_attribute("http.method", request.method)
        user = get_user(request.user_id)
        return build_response(user)

# Decorator
@tracer.start_as_current_span("get_user")
def get_user(user_id):
    return db.query(f"SELECT * FROM users WHERE id = {user_id}")

# Nested spans (automatic parent-child)
def process_order(order):
    with tracer.start_as_current_span("process_order") as parent:
        with tracer.start_as_current_span("validate"):
            validate(order)
        with tracer.start_as_current_span("charge"):
            charge(order)
        with tracer.start_as_current_span("fulfill"):
            fulfill(order)
```

## Creating Traces in Node.js

```typescript
import { trace } from "@opentelemetry/api";

const tracer = trace.getTracer("my.service");

// Context manager style
function handleRequest(req: Request) {
  return tracer.startActiveSpan("handle_request", (span) => {
    try {
      span.setAttribute("http.method", req.method);
      const result = processRequest(req);
      return result;
    } catch (err) {
      span.setStatus({ code: SpanStatusCode.ERROR, message: String(err) });
      throw err;
    } finally {
      span.end();  // MUST call end() explicitly in JS
    }
  });
}
```

## Best Practices

1. **Name spans after the operation, not the function** — `HTTP GET /users/:id` is better than `getUserById`
2. **Keep attribute counts reasonable** — 10-20 attributes per span is plenty; avoid dumping entire request bodies
3. **Use semantic conventions** — Standard attribute names enable cross-service analysis
4. **Record exceptions** — `span.record_exception(ex)` adds structured error details as an event
5. **Set meaningful span kinds** — Helps visualization tools correctly render service maps
6. **Avoid high-cardinality attribute values** — User IDs are fine; full URLs with query params can be problematic

## Common Pitfalls

1. **Forgetting `span.end()` in JavaScript** — Unlike Python's context manager, JS requires explicit `span.end()`. Missed ends leak memory and produce incomplete traces.
2. **Creating spans for every function** — Over-instrumentation adds overhead and noise. Instrument service boundaries and significant operations only.
3. **Setting status OK everywhere** — Leave status as `UNSET` for successful operations. Only set `ERROR` on failures and `OK` when you explicitly want to override.
4. **Not propagating context in async code** — In Node.js, use `context.with()` to maintain trace context across async boundaries.
