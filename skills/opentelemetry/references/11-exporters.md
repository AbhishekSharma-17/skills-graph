# OpenTelemetry — Exporters

> Source: [opentelemetry.io/docs/specs/otel/protocol](https://opentelemetry.io/docs/specs/otel/protocol/)

## Table of Contents

- [What Are Exporters](#what-are-exporters)
- [OTLP Protocol](#otlp-protocol)
- [OTLP Exporter Configuration](#otlp-exporter-configuration)
- [Jaeger Exporter](#jaeger-exporter)
- [Prometheus Exporter](#prometheus-exporter)
- [Zipkin Exporter](#zipkin-exporter)
- [Console Exporter](#console-exporter)
- [Multiple Exporters](#multiple-exporters)
- [Environment Variable Configuration](#environment-variable-configuration)
- [Backend Compatibility Matrix](#backend-compatibility-matrix)
- [Best Practices](#best-practices)
- [Common Pitfalls](#common-pitfalls)

---

## What Are Exporters

Exporters ship telemetry data from the SDK to observability backends. Each exporter implements a specific protocol and data format.

**Two export paths:**

```
Direct: App SDK ──exporter──▶ Backend (Jaeger, Prometheus, etc.)
Via Collector: App SDK ──OTLP──▶ Collector ──exporter──▶ Backend
```

**Recommendation:** Use OTLP to a Collector in production. Use direct exporters for development or simple setups.

## OTLP Protocol

OTLP (OpenTelemetry Protocol) is the native protocol for OTel. It's the most efficient and fully-featured option.

**Transports:**

| Transport | Port | Use Case |
|-----------|------|----------|
| gRPC | 4317 | High throughput, streaming, bidirectional |
| HTTP/protobuf | 4318 | Broader compatibility, simpler infra |
| HTTP/JSON | 4318 | Debugging, lower performance |

**Endpoints:**

| Signal | gRPC | HTTP |
|--------|------|------|
| Traces | `localhost:4317` | `localhost:4318/v1/traces` |
| Metrics | `localhost:4317` | `localhost:4318/v1/metrics` |
| Logs | `localhost:4317` | `localhost:4318/v1/logs` |

## OTLP Exporter Configuration

### Python

```python
# gRPC (recommended for high throughput)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter

trace_exporter = OTLPSpanExporter(
    endpoint="localhost:4317",
    insecure=True,                    # No TLS (dev only)
    headers={"Authorization": "Bearer token123"},
    timeout=10,                       # seconds
    compression=Compression.Gzip,     # Optional compression
)

# HTTP/protobuf (broader compatibility)
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as HTTPExporter

trace_exporter = HTTPExporter(
    endpoint="http://localhost:4318/v1/traces",
    headers={"Authorization": "Bearer token123"},
)
```

### Node.js

```typescript
// gRPC
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-grpc";
const exporter = new OTLPTraceExporter({
  url: "http://localhost:4317",
  headers: { Authorization: "Bearer token123" },
  timeoutMillis: 10000,
});

// HTTP/protobuf
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
const exporter = new OTLPTraceExporter({
  url: "http://localhost:4318/v1/traces",
});

// Metrics
import { OTLPMetricExporter } from "@opentelemetry/exporter-metrics-otlp-grpc";
const metricExporter = new OTLPMetricExporter({
  url: "http://localhost:4317",
});
```

## Jaeger Exporter

Sends traces directly to Jaeger (for setups without a Collector):

```python
# Python — via OTLP (Jaeger supports OTLP natively since v1.35)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Jaeger accepts OTLP on port 4317
exporter = OTLPSpanExporter(endpoint="jaeger:4317", insecure=True)
```

```typescript
// Node.js — Jaeger via OTLP
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-grpc";
const exporter = new OTLPTraceExporter({ url: "http://jaeger:4317" });
```

**Note:** The legacy Jaeger Thrift exporter is deprecated. Use OTLP exporter pointed at Jaeger's OTLP endpoint instead.

## Prometheus Exporter

Prometheus uses a pull model — the exporter exposes a scrape endpoint:

```python
# Python
from opentelemetry.exporter.prometheus import PrometheusMetricReader

reader = PrometheusMetricReader()  # Exposes :9464/metrics by default
provider = MeterProvider(metric_readers=[reader])
```

```typescript
// Node.js
import { PrometheusExporter } from "@opentelemetry/exporter-prometheus";

const exporter = new PrometheusExporter({ port: 9464 });
const provider = new MeterProvider({
  readers: [exporter],
});
```

```yaml
# Prometheus scrape config
scrape_configs:
  - job_name: "my-service"
    scrape_interval: 15s
    static_configs:
      - targets: ["my-service:9464"]
```

## Zipkin Exporter

```python
# Python
from opentelemetry.exporter.zipkin.json import ZipkinExporter

exporter = ZipkinExporter(endpoint="http://zipkin:9411/api/v2/spans")
```

```typescript
// Node.js
import { ZipkinExporter } from "@opentelemetry/exporter-zipkin";
const exporter = new ZipkinExporter({ url: "http://zipkin:9411/api/v2/spans" });
```

## Console Exporter

For development and debugging — prints telemetry to stdout:

```python
# Python
from opentelemetry.sdk.trace.export import ConsoleSpanExporter
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter
from opentelemetry.sdk._logs.export import ConsoleLogRecordExporter

trace_provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
```

```typescript
// Node.js
import { ConsoleSpanExporter } from "@opentelemetry/sdk-trace-node";
const sdk = new NodeSDK({ traceExporter: new ConsoleSpanExporter() });
```

## Multiple Exporters

You can send data to multiple backends simultaneously:

```python
from opentelemetry.sdk.trace.export import BatchSpanProcessor

provider = TracerProvider(resource=resource)

# Send traces to both Collector and console
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint="collector:4317")))
provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
```

## Environment Variable Configuration

Configure exporters without code changes:

```bash
# Exporter selection
OTEL_TRACES_EXPORTER=otlp          # otlp, jaeger, zipkin, console, none
OTEL_METRICS_EXPORTER=otlp         # otlp, prometheus, console, none
OTEL_LOGS_EXPORTER=otlp            # otlp, console, none

# OTLP endpoint (applies to all signals)
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# Per-signal endpoints
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://traces-collector:4317
OTEL_EXPORTER_OTLP_METRICS_ENDPOINT=http://metrics-collector:4317
OTEL_EXPORTER_OTLP_LOGS_ENDPOINT=http://logs-collector:4317

# Protocol
OTEL_EXPORTER_OTLP_PROTOCOL=grpc   # grpc, http/protobuf, http/json

# Headers (authentication)
OTEL_EXPORTER_OTLP_HEADERS=api-key=secret,org-id=my-org

# Compression
OTEL_EXPORTER_OTLP_COMPRESSION=gzip

# Timeout (milliseconds)
OTEL_EXPORTER_OTLP_TIMEOUT=10000

# TLS certificate
OTEL_EXPORTER_OTLP_CERTIFICATE=/path/to/ca.crt
OTEL_EXPORTER_OTLP_CLIENT_KEY=/path/to/client.key
OTEL_EXPORTER_OTLP_CLIENT_CERTIFICATE=/path/to/client.crt
```

## Backend Compatibility Matrix

| Backend | Traces | Metrics | Logs | Protocol |
|---------|--------|---------|------|----------|
| **Jaeger** | OTLP | — | — | OTLP/gRPC |
| **Grafana Tempo** | OTLP | — | — | OTLP/gRPC, OTLP/HTTP |
| **Prometheus** | — | Pull/OTLP | — | Prometheus scrape, OTLP |
| **Grafana Mimir** | — | OTLP | — | OTLP/gRPC, OTLP/HTTP |
| **Grafana Loki** | — | — | OTLP | OTLP/gRPC, OTLP/HTTP |
| **Datadog** | OTLP | OTLP | OTLP | OTLP/gRPC, OTLP/HTTP |
| **New Relic** | OTLP | OTLP | OTLP | OTLP/gRPC, OTLP/HTTP |
| **Honeycomb** | OTLP | OTLP | OTLP | OTLP/gRPC, OTLP/HTTP |
| **Elastic APM** | OTLP | OTLP | OTLP | OTLP/gRPC, OTLP/HTTP |
| **Splunk** | OTLP | OTLP | OTLP | OTLP/gRPC, OTLP/HTTP |
| **Zipkin** | Zipkin | — | — | HTTP/JSON |
| **AWS X-Ray** | OTLP | — | — | OTLP (via Collector) |

## Best Practices

1. **Use OTLP** — It's the most efficient and future-proof protocol
2. **Use gRPC for high throughput** — gRPC is more efficient than HTTP/protobuf
3. **Enable compression** — `gzip` reduces bandwidth significantly
4. **Use BatchSpanProcessor** — Never SimpleSpanProcessor in production
5. **Configure timeouts** — Prevent SDK from blocking on slow backends
6. **Export via Collector** — Adds retry, buffering, and protocol flexibility

## Common Pitfalls

1. **Wrong port** — gRPC is 4317, HTTP is 4318. Mixing them up causes connection failures.
2. **Missing `insecure=True` for dev** — gRPC defaults to TLS. Without certs, you need `insecure=True`.
3. **Not flushing on shutdown** — Call `provider.shutdown()` to export buffered data before process exit.
4. **Prometheus exporter with Collector** — Don't use PrometheusMetricReader in the SDK if you're also sending to a Collector. Use OTLP to the Collector, and let the Collector expose Prometheus.
5. **Headers format** — Environment variable `OTEL_EXPORTER_OTLP_HEADERS` uses `key=value,key2=value2` (comma-separated), not JSON.
