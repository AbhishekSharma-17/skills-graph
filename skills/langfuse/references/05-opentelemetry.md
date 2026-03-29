# OpenTelemetry Integration

> Source: [langfuse.com/integrations/native/opentelemetry](https://langfuse.com/integrations/native/opentelemetry)

## Table of Contents

- [Overview](#overview)
- [OTLP Endpoint Configuration](#otlp-endpoint-configuration)
- [Authentication](#authentication)
- [Python OTEL Setup](#python-otel-setup)
- [TypeScript OTEL Setup](#typescript-otel-setup)
- [OpenTelemetry Collector](#opentelemetry-collector)
- [Trace-Level Attribute Mapping](#trace-level-attribute-mapping)
- [Observation-Level Attribute Mapping](#observation-level-attribute-mapping)
- [Attribute Propagation with Baggage](#attribute-propagation-with-baggage)
- [Span Filtering](#span-filtering)
- [GenAI Instrumentation Libraries](#genai-instrumentation-libraries)
- [Supported Protocols](#supported-protocols)
- [Common Patterns](#common-patterns)
- [Pitfalls](#pitfalls)

---

## Overview

Langfuse operates as an OpenTelemetry backend, accepting traces via its OTLP endpoint (`/api/public/otel`). This enables:

- Language-agnostic tracing (any OTEL-supported language)
- Standards-based instrumentation
- Integration with existing OTEL infrastructure
- Use of third-party GenAI instrumentation libraries (OpenLIT, OpenLLMetry, etc.)

The Langfuse SDK v3 is built as a thin layer on top of the official OpenTelemetry client.

## OTLP Endpoint Configuration

```bash
# EU Region
OTEL_EXPORTER_OTLP_ENDPOINT="https://cloud.langfuse.com/api/public/otel"
OTEL_EXPORTER_OTLP_HEADERS="Authorization=Basic ${AUTH_STRING},x-langfuse-ingestion-version=4"

# US Region
OTEL_EXPORTER_OTLP_ENDPOINT="https://us.cloud.langfuse.com/api/public/otel"
OTEL_EXPORTER_OTLP_HEADERS="Authorization=Basic ${AUTH_STRING},x-langfuse-ingestion-version=4"

# Self-Hosted (requires v3.22.0+)
OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:3000/api/public/otel"
OTEL_EXPORTER_OTLP_HEADERS="Authorization=Basic ${AUTH_STRING},x-langfuse-ingestion-version=4"
```

For signal-specific configuration:

```bash
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT="https://cloud.langfuse.com/api/public/otel/v1/traces"
OTEL_EXPORTER_OTLP_TRACES_HEADERS="Authorization=Basic ${AUTH_STRING},x-langfuse-ingestion-version=4"
```

## Authentication

Base64-encode your API key pair:

```bash
# Linux/macOS
echo -n "pk-lf-1234567890:sk-lf-1234567890" | base64

# GNU systems (prevent line wrapping)
echo -n "pk-lf-1234567890:sk-lf-1234567890" | base64 -w 0
```

Format: `Basic <base64(public_key:secret_key)>`

## Python OTEL Setup

Using the Langfuse OTEL-native SDK:

```python
from langfuse import get_client, observe

# SDK auto-initializes OTEL behind the scenes
langfuse = get_client()

@observe()
def my_function():
    pass
```

Using raw OpenTelemetry with Langfuse as exporter:

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

# Configure OTLP exporter pointing to Langfuse
exporter = OTLPSpanExporter(
    endpoint="https://cloud.langfuse.com/api/public/otel/v1/traces",
    headers={
        "Authorization": f"Basic {auth_string}",
        "x-langfuse-ingestion-version": "4",
    },
)

provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(exporter))
trace.set_tracer_provider(provider)

tracer = trace.get_tracer("my-app")
```

## TypeScript OTEL Setup

```typescript
import { NodeSDK } from "@opentelemetry/sdk-node";
import { LangfuseSpanProcessor } from "@langfuse/otel";

const sdk = new NodeSDK({
  spanProcessors: [new LangfuseSpanProcessor()],
});

sdk.start();
```

Or with raw OTEL exporter:

```typescript
import { NodeSDK } from "@opentelemetry/sdk-node";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";

const exporter = new OTLPTraceExporter({
  url: "https://cloud.langfuse.com/api/public/otel/v1/traces",
  headers: {
    Authorization: `Basic ${authString}`,
    "x-langfuse-ingestion-version": "4",
  },
});

const sdk = new NodeSDK({ traceExporter: exporter });
sdk.start();
```

## OpenTelemetry Collector

Deploy a collector for centralized trace collection:

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
  memory_limiter:
    limit_mib: 1500
    spike_limit_mib: 512
    check_interval: 5s

exporters:
  otlphttp/langfuse:
    endpoint: "https://cloud.langfuse.com/api/public/otel"
    headers:
      Authorization: "Basic ${AUTH_STRING}"
      x-langfuse-ingestion-version: "4"

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlphttp/langfuse]
```

## Trace-Level Attribute Mapping

Map OpenTelemetry span attributes to Langfuse trace properties:

| Langfuse Field | OTel Attribute |
|----------------|---------------|
| `name` | `langfuse.trace.name` or root span name |
| `userId` | `langfuse.user.id` or `user.id` |
| `sessionId` | `langfuse.session.id` or `session.id` |
| `release` | `langfuse.release` |
| `public` | `langfuse.trace.public` |
| `tags` | `langfuse.trace.tags` (array) |
| `metadata` | `langfuse.trace.metadata.*` |
| `input` | `langfuse.trace.input` |
| `output` | `langfuse.trace.output` |

## Observation-Level Attribute Mapping

| Langfuse Field | OTel Attribute |
|----------------|---------------|
| `type` | `langfuse.observation.type` ("span"/"generation"/"event") |
| `level` | `langfuse.observation.level` or inferred from `span.status.code` |
| `statusMessage` | `langfuse.observation.status_message` |
| `metadata` | `langfuse.observation.metadata.*` |
| `input` | `langfuse.observation.input` or `gen_ai.prompt` |
| `output` | `langfuse.observation.output` or `gen_ai.completion` |
| `model` | `gen_ai.request.model` or `llm.model_name` |
| `modelParameters` | `gen_ai.request.*` or `llm.invocation_parameters.*` |
| `usage` | `gen_ai.usage.*` or `llm.token_count.*` |
| `cost` | `langfuse.observation.cost_details` |

## Attribute Propagation with Baggage

Use OTEL Baggage to propagate attributes across service boundaries:

```python
from opentelemetry import baggage, context
from opentelemetry.baggage.propagation import BaggageSpanProcessor

# Set baggage at trace start
ctx = baggage.set_baggage("langfuse.user.id", "user-123")
ctx = baggage.set_baggage("langfuse.session.id", "session-456", context=ctx)

# BaggageSpanProcessor copies baggage to span attributes
```

**Security note:** Baggage propagates across service boundaries. Never put sensitive data in baggage.

## Span Filtering

Use the OTEL Collector filterprocessor to selectively forward spans:

```yaml
processors:
  filter/openai-only:
    error_mode: ignore
    traces:
      span:
        - 'attributes["gen_ai.system"] != "openai"'

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [filter/openai-only]
      exporters: [otlphttp/langfuse]
```

## GenAI Instrumentation Libraries

Third-party libraries that emit OTEL-compatible GenAI spans:

| Library | Description |
|---------|-------------|
| **OpenLIT** | Auto-instrumentation for 50+ LLM providers |
| **OpenLLMetry** | Traceloop's open-source LLM telemetry |
| **Arize Phoenix** | LLM observability with OTEL export |
| **MLflow** | ML lifecycle management with OTEL traces |

These libraries emit spans following the OpenTelemetry GenAI semantic conventions, which Langfuse automatically maps to its observation model.

## Supported Protocols

- OTLP over HTTP with `HTTP/JSON`
- OTLP over HTTP with `HTTP/protobuf`
- gRPC: **not yet supported** (use the OTEL Collector as a proxy if needed)

## Common Patterns

### Multi-Service Tracing

```python
# Service A: sets trace context
span.set_attribute("langfuse.trace.name", "cross-service-request")
span.set_attribute("langfuse.user.id", "user-123")
# OTEL propagation carries trace context to Service B

# Service B: inherits trace context
# Spans from Service B appear as children in the same Langfuse trace
```

### Dual Export (Langfuse + Jaeger)

```yaml
exporters:
  otlphttp/langfuse:
    endpoint: "https://cloud.langfuse.com/api/public/otel"
    headers:
      Authorization: "Basic ${AUTH_STRING}"
  otlphttp/jaeger:
    endpoint: "http://jaeger:4318"

service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [otlphttp/langfuse, otlphttp/jaeger]
```

## Pitfalls

1. **Missing `x-langfuse-ingestion-version` header** — Without this header set to "4", traces may not appear in the real-time view.

2. **gRPC not supported** — Langfuse only accepts HTTP-based OTLP. Use the OTEL Collector if your app emits gRPC.

3. **Unmapped attributes** — OTel attributes not matching the Langfuse mapping end up nested under `metadata.attributes` and are not filterable in the dashboard.

4. **Clock skew** — If sending from multiple services, ensure clocks are synchronized. Langfuse uses span timestamps for ordering.

5. **Large batch sizes** — Default OTEL batch sizes may be too large for Langfuse's ingestion endpoint. Use the memory_limiter processor in the Collector.
