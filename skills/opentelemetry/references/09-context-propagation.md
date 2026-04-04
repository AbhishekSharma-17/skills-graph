# OpenTelemetry — Context Propagation

> Source: [opentelemetry.io/docs/concepts/context-propagation](https://opentelemetry.io/docs/concepts/context-propagation/)

## Table of Contents

- [What Is Context Propagation](#what-is-context-propagation)
- [How It Works](#how-it-works)
- [Propagation Formats](#propagation-formats)
- [W3C TraceContext](#w3c-tracecontext)
- [W3C Baggage](#w3c-baggage)
- [B3 Propagation](#b3-propagation)
- [Configuring Propagators](#configuring-propagators)
- [Manual Propagation in Python](#manual-propagation-in-python)
- [Manual Propagation in Node.js](#manual-propagation-in-nodejs)
- [Propagation Across Message Queues](#propagation-across-message-queues)
- [Baggage API](#baggage-api)
- [Best Practices](#best-practices)
- [Common Pitfalls](#common-pitfalls)

---

## What Is Context Propagation

Context propagation is the mechanism that connects spans across service boundaries into a single trace. When Service A calls Service B, the trace context (trace ID, parent span ID, flags) must travel with the request so Service B can create a child span in the same trace.

```
Service A                    Service B
┌─────────────┐              ┌─────────────┐
│ Span: /api  │──HTTP GET──▶│ Span: /data  │
│ trace: abc  │  headers:    │ trace: abc   │ ← Same trace!
│ span: 111   │  traceparent │ parent: 111  │ ← Child of A
└─────────────┘              └─────────────┘
```

Without context propagation, each service creates independent traces that cannot be correlated.

## How It Works

1. **Inject**: Before making an outgoing request, the SDK injects trace context into the carrier (HTTP headers, message attributes, etc.)
2. **Extract**: On receiving a request, the SDK extracts trace context from the carrier
3. **Continue**: The extracted context becomes the parent for new spans

```
┌─────────┐    inject()     ┌────────────┐    extract()    ┌─────────┐
│ Service │ ──────────────▶ │   Carrier  │ ──────────────▶ │ Service │
│    A    │  (add headers)  │  (headers) │  (read headers) │    B    │
└─────────┘                 └────────────┘                 └─────────┘
```

**Carriers** are the transport mechanism:

| Transport | Carrier | Common Format |
|-----------|---------|---------------|
| HTTP | Headers | W3C TraceContext |
| gRPC | Metadata | W3C TraceContext |
| Kafka | Message headers | W3C TraceContext or B3 |
| AMQP | Message properties | W3C TraceContext |

## Propagation Formats

| Format | Header(s) | Use Case |
|--------|----------|----------|
| **W3C TraceContext** | `traceparent`, `tracestate` | Default, industry standard |
| **W3C Baggage** | `baggage` | Cross-service key-value data |
| **B3 Single** | `b3` | Zipkin-compatible (single header) |
| **B3 Multi** | `X-B3-TraceId`, `X-B3-SpanId`, etc. | Zipkin-compatible (multi header) |
| **Jaeger** | `uber-trace-id` | Jaeger-native (legacy) |
| **AWS X-Ray** | `X-Amzn-Trace-Id` | AWS services |

## W3C TraceContext

The default and recommended format. Uses two headers:

### traceparent

```
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
             ^^-^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^-^^^^^^^^^^^^^^^^-^^
             |  |                                |                |
             |  trace-id (32 hex chars)         span-id          flags
             version                            (16 hex chars)   01=sampled
```

| Field | Length | Description |
|-------|--------|-------------|
| `version` | 2 hex | Always `00` |
| `trace-id` | 32 hex | 128-bit unique trace identifier |
| `parent-id` | 16 hex | 64-bit span identifier of the caller |
| `trace-flags` | 2 hex | `00` = not sampled, `01` = sampled |

### tracestate

Vendor-specific data, comma-separated key=value pairs:

```
tracestate: vendor1=value1,vendor2=value2
```

Used by vendors to pass proprietary context alongside the standard trace context.

## W3C Baggage

Propagates arbitrary key-value pairs across service boundaries:

```
baggage: userId=abc123,serverNode=web-01,isVIP=true
```

**Important:** Baggage is NOT exported as telemetry data. It's propagated context that can be read and used by downstream services.

## B3 Propagation

Used when interoperating with Zipkin-based systems:

### Single header

```
b3: {TraceId}-{SpanId}-{SamplingState}-{ParentSpanId}
b3: 80f198ee56343ba864fe8b2a57d3eff7-e457b5a2e4d86bd1-1-05e3ac9a4f6e3b90
```

### Multi header

```
X-B3-TraceId: 80f198ee56343ba864fe8b2a57d3eff7
X-B3-SpanId: e457b5a2e4d86bd1
X-B3-ParentSpanId: 05e3ac9a4f6e3b90
X-B3-Sampled: 1
```

## Configuring Propagators

### Environment Variable (all languages)

```bash
# Default: W3C TraceContext + Baggage
OTEL_PROPAGATORS="tracecontext,baggage"

# Add B3 for Zipkin compatibility
OTEL_PROPAGATORS="tracecontext,baggage,b3multi"

# Jaeger format
OTEL_PROPAGATORS="jaeger"

# AWS X-Ray
OTEL_PROPAGATORS="xray"
```

### Python SDK

```python
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.propagators.b3 import B3MultiFormat
from opentelemetry.trace.propagation import TraceContextTextMapPropagator
from opentelemetry.baggage.propagation import W3CBaggagePropagator

# Composite propagator: support multiple formats
set_global_textmap(CompositePropagator([
    TraceContextTextMapPropagator(),
    W3CBaggagePropagator(),
    B3MultiFormat(),
]))
```

### Node.js SDK

```typescript
import { CompositePropagator, W3CTraceContextPropagator, W3CBaggagePropagator } from "@opentelemetry/core";
import { B3Propagator } from "@opentelemetry/propagator-b3";

const sdk = new NodeSDK({
  textMapPropagator: new CompositePropagator({
    propagators: [
      new W3CTraceContextPropagator(),
      new W3CBaggagePropagator(),
      new B3Propagator(),
    ],
  }),
});
```

## Manual Propagation in Python

```python
from opentelemetry.propagate import inject, extract
from opentelemetry import context, trace
import requests

tracer = trace.get_tracer("my.service")

# --- Outgoing request (inject) ---
def call_downstream(url, payload):
    with tracer.start_as_current_span("call_downstream") as span:
        headers = {}
        inject(headers)  # Adds traceparent, baggage headers
        response = requests.post(url, json=payload, headers=headers)
        return response

# --- Incoming request (extract) ---
def handle_request(request):
    # Extract context from incoming headers
    ctx = extract(request.headers)

    # Start a span as child of the extracted context
    with tracer.start_as_current_span("handle_request", context=ctx) as span:
        return process(request)

# --- Manual context management ---
ctx = extract(incoming_headers)
token = context.attach(ctx)
try:
    with tracer.start_as_current_span("work"):
        do_work()
finally:
    context.detach(token)
```

## Manual Propagation in Node.js

```typescript
import { propagation, context, trace } from "@opentelemetry/api";

const tracer = trace.getTracer("my.service");

// --- Outgoing request (inject) ---
function callDownstream(url: string, payload: any) {
  return tracer.startActiveSpan("call_downstream", async (span) => {
    const headers: Record<string, string> = {};
    propagation.inject(context.active(), headers);

    const response = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify(payload),
    });
    span.end();
    return response;
  });
}

// --- Incoming request (extract) ---
function handleRequest(req: Request) {
  const ctx = propagation.extract(context.active(), req.headers);

  return context.with(ctx, () => {
    return tracer.startActiveSpan("handle_request", (span) => {
      const result = process(req);
      span.end();
      return result;
    });
  });
}
```

## Propagation Across Message Queues

```python
# Producer: inject context into message headers
def publish_message(topic, message):
    with tracer.start_as_current_span("publish", kind=trace.SpanKind.PRODUCER) as span:
        headers = {}
        inject(headers)
        kafka_producer.send(topic, value=message, headers=headers)

# Consumer: extract context from message headers
def consume_message(message):
    ctx = extract(dict(message.headers))
    # Link to producer span instead of making it a direct parent
    link = trace.Link(trace.get_current_span(ctx).get_span_context())

    with tracer.start_as_current_span(
        "process",
        kind=trace.SpanKind.CONSUMER,
        links=[link],  # Use links for async relationships
    ) as span:
        process(message)
```

## Baggage API

Baggage propagates key-value pairs across services without being exported as telemetry:

```python
from opentelemetry import baggage, context

# Set baggage
ctx = baggage.set_baggage("user.id", "usr_123")
ctx = baggage.set_baggage("tenant.id", "acme", context=ctx)
token = context.attach(ctx)

# Read baggage (in any downstream service)
user_id = baggage.get_baggage("user.id")
all_baggage = baggage.get_all()

# Use baggage values as span attributes
span.set_attribute("user.id", baggage.get_baggage("user.id"))

context.detach(token)
```

**Use cases for baggage:**

- Tenant ID for multi-tenant systems
- User ID for request attribution
- Feature flags for distributed A/B tests
- Request priority for downstream routing

## Best Practices

1. **Use W3C TraceContext as default** — It's the industry standard and works everywhere
2. **Add B3 only when needed** — Only if you integrate with Zipkin-based systems
3. **Be careful with baggage** — It's sent with every request, adding overhead. Keep it small.
4. **Let auto-instrumentation handle propagation** — HTTP client/server instrumentations inject/extract automatically
5. **Use links for async relationships** — Don't make queue consumers direct children of producers; use links instead

## Common Pitfalls

1. **Mismatched propagators** — If Service A injects B3 but Service B only extracts W3C, the trace breaks. All services must support the same format.
2. **Baggage leaking sensitive data** — Baggage is sent as plain-text HTTP headers. Never put PII, tokens, or secrets in baggage.
3. **Breaking propagation with proxies** — Some proxies or API gateways strip unknown headers. Ensure `traceparent` and `tracestate` are forwarded.
4. **Context not propagating in custom HTTP clients** — Auto-instrumentation patches standard libraries. If you use a custom HTTP client, you must inject manually.
