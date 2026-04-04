# OpenTelemetry — Overview & Architecture

> Source: [opentelemetry.io/docs](https://opentelemetry.io/docs/) | Spec v1.55.0 | CNCF Graduated Project

## Table of Contents

- [What is OpenTelemetry](#what-is-opentelemetry)
- [Core Architecture](#core-architecture)
- [Signals Overview](#signals-overview)
- [Component Stack](#component-stack)
- [Installation Quick Reference](#installation-quick-reference)
- [Quickstart: Python](#quickstart-python)
- [Quickstart: Node.js](#quickstart-nodejs)
- [Environment Variables](#environment-variables)
- [When to Use OpenTelemetry](#when-to-use-opentelemetry)
- [Common Pitfalls](#common-pitfalls)

---

## What is OpenTelemetry

OpenTelemetry (OTel) is a vendor-neutral, open-source observability framework for generating, collecting, and exporting telemetry data — traces, metrics, and logs. It is a CNCF graduated project and the industry standard for instrumentation.

**Key properties:**

- **Vendor-neutral**: No backend lock-in — export to Jaeger, Prometheus, Datadog, Grafana, etc.
- **Multi-language**: SDKs for Python, JavaScript, Go, Java, .NET, Rust, C++, Ruby, PHP, and more
- **Three signals**: Traces (distributed request flows), Metrics (quantitative measurements), Logs (timestamped records)
- **Unified context**: All signals share the same context propagation, enabling correlation
- **Separation of concerns**: API (instrumentation) is separate from SDK (implementation)

## Core Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Application │     │  Application │     │  Application │
│  + OTel SDK  │     │  + OTel SDK  │     │  + OTel SDK  │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       │    OTLP/gRPC or OTLP/HTTP              │
       ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────┐
│                   OTel Collector                         │
│  ┌──────────┐  ┌───────────┐  ┌──────────────┐         │
│  │ Receivers│→ │ Processors│→ │  Exporters   │         │
│  └──────────┘  └───────────┘  └──────────────┘         │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   ┌─────────┐   ┌─────────┐   ┌─────────┐
   │ Jaeger  │   │Prometheus│   │ Grafana │
   │  Tempo  │   │  Mimir   │   │  Loki   │
   └─────────┘   └─────────┘   └─────────┘
```

**Layered design:**

1. **API layer** — Interfaces for instrumentation. Safe to use as a dependency in libraries. No-op by default.
2. **SDK layer** — Implementation of the API. Configures processing, sampling, and export. Application-level dependency.
3. **Exporters** — Ship telemetry to backends. One SDK can have multiple exporters.
4. **Collector** — Optional middleware for receiving, processing, and forwarding telemetry.

## Signals Overview

| Signal | Purpose | Status | Key Concepts |
|--------|---------|--------|--------------|
| **Traces** | Distributed request flows | Stable | Spans, SpanContext, Links, Events |
| **Metrics** | Quantitative measurements | Stable | Counter, Gauge, Histogram, Views |
| **Logs** | Timestamped event records | Stable* | LogRecord, Bridge API, Severity |
| **Baggage** | Cross-service key-value data | Stable | Propagated context, not exported |
| **Profiles** | Runtime performance data | Experimental | CPU, memory profiling |

*Logs are stable in spec but SDK maturity varies by language.

## Component Stack

| Component | What It Does | When to Use |
|-----------|-------------|-------------|
| `opentelemetry-api` | Instrumentation interfaces | Always — import in library/app code |
| `opentelemetry-sdk` | API implementation, processing | Application entrypoint setup |
| `opentelemetry-exporter-*` | Backend-specific exporters | One per backend (OTLP, Jaeger, etc.) |
| `opentelemetry-instrumentation-*` | Auto-instrumentation libraries | Per framework (Flask, Django, Express) |
| `otel-collector` | Telemetry pipeline middleware | Production deployments |

## Installation Quick Reference

### Python

```bash
# Core
pip install opentelemetry-api opentelemetry-sdk

# OTLP exporter (most common)
pip install opentelemetry-exporter-otlp

# Auto-instrumentation agent
pip install opentelemetry-distro opentelemetry-instrumentation
opentelemetry-bootstrap -a install  # install all detected instrumentations

# Run with auto-instrumentation
opentelemetry-instrument python myapp.py
```

### Node.js

```bash
# Core
npm install @opentelemetry/api @opentelemetry/sdk-node

# Auto-instrumentation (includes common libraries)
npm install @opentelemetry/auto-instrumentations-node

# OTLP exporter
npm install @opentelemetry/exporter-trace-otlp-grpc
npm install @opentelemetry/exporter-metrics-otlp-grpc
```

### Collector

```bash
# Docker
docker run -p 4317:4317 -p 4318:4318 -p 55679:55679 \
  -v $(pwd)/otel-config.yaml:/etc/otelcol/config.yaml \
  otel/opentelemetry-collector-contrib

# Binary (Linux)
wget https://github.com/open-telemetry/opentelemetry-collector-releases/releases/latest/download/otelcol-contrib_linux_amd64.tar.gz
tar -xzf otelcol-contrib_linux_amd64.tar.gz
./otelcol-contrib --config=otel-config.yaml
```

## Quickstart: Python

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.sdk.resources import Resource

# 1. Configure resource (identifies your service)
resource = Resource.create({"service.name": "my-service", "service.version": "1.0.0"})

# 2. Set up tracer provider with exporter
provider = TracerProvider(resource=resource)
provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(provider)

# 3. Get a tracer and create spans
tracer = trace.get_tracer("my.module")

with tracer.start_as_current_span("parent-operation") as span:
    span.set_attribute("operation.type", "demo")
    with tracer.start_as_current_span("child-operation"):
        print("Hello from instrumented code!")
```

## Quickstart: Node.js

```typescript
import { NodeSDK } from "@opentelemetry/sdk-node";
import { ConsoleSpanExporter } from "@opentelemetry/sdk-trace-node";
import { getNodeAutoInstrumentations } from "@opentelemetry/auto-instrumentations-node";
import { Resource } from "@opentelemetry/resources";
import { ATTR_SERVICE_NAME } from "@opentelemetry/semantic-conventions";

const sdk = new NodeSDK({
  resource: new Resource({ [ATTR_SERVICE_NAME]: "my-service" }),
  traceExporter: new ConsoleSpanExporter(),
  instrumentations: [getNodeAutoInstrumentations()],
});

sdk.start();
```

## Environment Variables

OTel SDKs share a standard set of environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `OTEL_SERVICE_NAME` | `unknown_service` | Service name in resource |
| `OTEL_TRACES_EXPORTER` | `otlp` | Trace exporter (`otlp`, `jaeger`, `console`, `none`) |
| `OTEL_METRICS_EXPORTER` | `otlp` | Metrics exporter |
| `OTEL_LOGS_EXPORTER` | `otlp` | Logs exporter |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` | Collector endpoint (gRPC) |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | `grpc` | Protocol (`grpc`, `http/protobuf`, `http/json`) |
| `OTEL_TRACES_SAMPLER` | `parentbased_always_on` | Sampling strategy |
| `OTEL_TRACES_SAMPLER_ARG` | — | Sampler argument (e.g., ratio for traceidratio) |
| `OTEL_PROPAGATORS` | `tracecontext,baggage` | Context propagation formats |
| `OTEL_RESOURCE_ATTRIBUTES` | — | Extra resource attributes (`key=value,key2=value2`) |
| `OTEL_LOG_LEVEL` | `info` | SDK internal log level |

## When to Use OpenTelemetry

**Use OTel when you need:**

- Distributed tracing across microservices
- Standardized metrics collection without vendor lock-in
- Correlated logs, traces, and metrics
- Auto-instrumentation for common frameworks
- A single telemetry pipeline for multiple backends

**Consider alternatives when:**

- You only need simple application logging (use stdlib logging)
- You're locked into a single APM vendor with its own agent
- Your application is a simple script with no distributed components

## Common Pitfalls

1. **Forgetting to set `service.name`** — Without it, all telemetry shows as `unknown_service`, making it useless in multi-service environments.

2. **Using `SimpleSpanProcessor` in production** — It exports synchronously, blocking your application. Always use `BatchSpanProcessor` in production.

3. **Not calling `shutdown()`** — The SDK buffers data. Without `provider.shutdown()` at exit, you lose the final batch of telemetry.

4. **Importing SDK in libraries** — Libraries should only depend on `opentelemetry-api`, never `opentelemetry-sdk`. The application configures the SDK.

5. **Missing auto-instrumentation bootstrap** — Run `opentelemetry-bootstrap -a install` after installing instrumentations to get all detected library integrations.

6. **Confusing API and SDK** — The API defines interfaces (safe for libraries); the SDK implements them (application-level). A missing SDK means the API is a no-op, not an error.
