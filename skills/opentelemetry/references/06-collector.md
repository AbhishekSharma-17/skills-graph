# OpenTelemetry — Collector Architecture

> Source: [opentelemetry.io/docs/collector](https://opentelemetry.io/docs/collector/)

## Table of Contents

- [What Is the Collector](#what-is-the-collector)
- [When to Use a Collector](#when-to-use-a-collector)
- [Pipeline Architecture](#pipeline-architecture)
- [Component Types](#component-types)
- [Deployment Patterns](#deployment-patterns)
- [Collector Distributions](#collector-distributions)
- [Installation Methods](#installation-methods)
- [Health and Observability](#health-and-observability)
- [Scaling Strategies](#scaling-strategies)
- [Best Practices](#best-practices)
- [Common Pitfalls](#common-pitfalls)

---

## What Is the Collector

The OpenTelemetry Collector is a vendor-agnostic middleware that receives, processes, and exports telemetry data. It acts as a centralized pipeline between your applications and observability backends.

```
Applications ──OTLP──▶ Collector ──▶ Jaeger (traces)
                                  ──▶ Prometheus (metrics)
                                  ──▶ Loki (logs)
```

**Key capabilities:**

- Receives telemetry in multiple formats (OTLP, Jaeger, Prometheus, Zipkin, etc.)
- Processes data (batching, filtering, sampling, enrichment)
- Exports to multiple backends simultaneously
- Runs as an agent (sidecar) or gateway (centralized)
- Self-monitoring with health checks and internal metrics

## When to Use a Collector

| Scenario | Direct Export | Collector |
|----------|-------------|-----------|
| Development / prototyping | Simpler setup | Overkill |
| Production single backend | Works fine | Adds retry + buffering |
| Production multi-backend | Complex app config | Clean separation |
| Need data transformation | Not possible | Filter, enrich, sample |
| Need protocol translation | Not possible | Convert between formats |
| Fleet-wide config changes | Redeploy all apps | Update collector config |

**Rule of thumb:** Use direct export for development, use a Collector for production.

## Pipeline Architecture

The Collector processes telemetry through **pipelines**, each consisting of:

```
Pipeline: traces
┌──────────┐    ┌───────────┐    ┌──────────┐
│ Receiver │───▶│ Processor │───▶│ Exporter │
│ (OTLP)   │    │ (batch)   │    │ (Jaeger) │
└──────────┘    └───────────┘    └──────────┘

Pipeline: metrics
┌──────────┐    ┌───────────┐    ┌──────────┐
│ Receiver │───▶│ Processor │───▶│ Exporter │
│ (Prom)   │    │ (filter)  │    │ (OTLP)   │
└──────────┘    └───────────┘    └──────────┘
```

**Pipeline types:** `traces`, `metrics`, `logs`

**Rules:**

- A pipeline has exactly one signal type
- It can have multiple receivers, processors, and exporters
- A receiver/exporter can be shared across pipelines
- Processors execute in the order listed

## Component Types

### Receivers

Accept telemetry data from external sources:

| Receiver | Protocol | Push/Pull |
|----------|----------|-----------|
| `otlp` | OTLP (gRPC + HTTP) | Push |
| `jaeger` | Jaeger (Thrift, gRPC) | Push |
| `prometheus` | Prometheus scrape | Pull |
| `zipkin` | Zipkin HTTP | Push |
| `filelog` | File tailing | Pull |
| `hostmetrics` | System metrics | Pull |
| `kafka` | Kafka consumer | Pull |

### Processors

Transform data in-flight:

| Processor | Purpose |
|-----------|---------|
| `batch` | Batches data for efficient export |
| `memory_limiter` | Prevents OOM by dropping data |
| `attributes` | Add, remove, or modify attributes |
| `filter` | Drop unwanted telemetry |
| `resource` | Modify resource attributes |
| `transform` | General-purpose OTTL transformations |
| `tail_sampling` | Sample based on complete traces |
| `probabilistic_sampler` | Random head sampling |
| `span` | Rename spans, extract attributes |
| `redaction` | Remove sensitive data |

### Exporters

Send data to backends:

| Exporter | Destination |
|----------|------------|
| `otlp` | Any OTLP endpoint (gRPC/HTTP) |
| `otlphttp` | OTLP over HTTP |
| `prometheus` | Prometheus scrape endpoint |
| `jaeger` | Jaeger backend |
| `zipkin` | Zipkin backend |
| `loki` | Grafana Loki |
| `debug` | Console output (development) |
| `file` | Local files |

### Connectors

Link two pipelines, acting as both exporter and receiver:

```yaml
connectors:
  spanmetrics:  # Generates metrics from trace spans
    histogram:
      explicit:
        buckets: [10ms, 50ms, 100ms, 500ms, 1s]

service:
  pipelines:
    traces:
      exporters: [spanmetrics]  # Connector as exporter
    metrics:
      receivers: [spanmetrics]  # Same connector as receiver
```

### Extensions

Add non-pipeline functionality:

| Extension | Purpose |
|-----------|---------|
| `health_check` | HTTP health endpoint (/13133) |
| `pprof` | Go profiling endpoint |
| `zpages` | Debug pages for pipeline status |
| `basicauth` | Basic auth for receivers |
| `oauth2client` | OAuth2 for exporters |
| `file_storage` | Persistent queue storage |

## Deployment Patterns

### Agent Pattern (Sidecar)

```
┌───────────────────────┐  ┌───────────────────────┐
│ Pod                   │  │ Pod                   │
│ ┌─────┐  ┌─────────┐ │  │ ┌─────┐  ┌─────────┐ │
│ │ App │─▶│Collector│ │  │ │ App │─▶│Collector│ │
│ └─────┘  └────┬────┘ │  │ └─────┘  └────┬────┘ │
└───────────────┼───────┘  └───────────────┼───────┘
                │                          │
                └──────────┬───────────────┘
                           ▼
                    ┌─────────────┐
                    │   Backend   │
                    └─────────────┘
```

- One collector per application/pod
- Low latency, fast data offloading
- Use for: basic batching, retry, auth

### Gateway Pattern (Centralized)

```
┌───────┐  ┌───────┐  ┌───────┐
│ App 1 │  │ App 2 │  │ App 3 │
└───┬───┘  └───┬───┘  └───┬───┘
    │          │          │
    └────── OTLP ─────────┘
               │
    ┌──────────▼──────────┐
    │   Gateway Collector  │
    │  (centralized)       │
    └──────────┬──────────┘
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
 Jaeger   Prometheus    Loki
```

- Single collector for multiple applications
- Central processing, sampling, routing
- Use for: tail sampling, complex transformations, multi-backend routing

### Hybrid Pattern

```
Apps ──▶ Agent Collectors ──▶ Gateway Collector ──▶ Backends
         (per pod/host)       (centralized)
```

- Agents handle batching and retry
- Gateway handles sampling, transformation, routing
- **Recommended for production at scale**

## Collector Distributions

| Distribution | Includes |
|-------------|----------|
| `otelcol` | Core components only |
| `otelcol-contrib` | Core + community components (most common) |
| Custom build | Only what you need (via OCB — OpenTelemetry Collector Builder) |

```bash
# Use contrib for most use cases
docker pull otel/opentelemetry-collector-contrib

# Build custom collector with only needed components
go install go.opentelemetry.io/collector/cmd/builder@latest
builder --config=builder-config.yaml
```

## Installation Methods

```bash
# Docker
docker run -p 4317:4317 -p 4318:4318 \
  -v $(pwd)/config.yaml:/etc/otelcol/config.yaml \
  otel/opentelemetry-collector-contrib

# Kubernetes (Helm)
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
helm install otel-collector open-telemetry/opentelemetry-collector \
  --set mode=deployment  # or daemonset for agent pattern

# Kubernetes Operator
kubectl apply -f https://github.com/open-telemetry/opentelemetry-operator/releases/latest/download/opentelemetry-operator.yaml

# systemd service (Linux)
wget https://github.com/open-telemetry/opentelemetry-collector-releases/releases/latest/download/otelcol-contrib_linux_amd64.deb
dpkg -i otelcol-contrib_linux_amd64.deb
systemctl start otelcol-contrib
```

## Health and Observability

The Collector itself is observable:

```yaml
extensions:
  health_check:
    endpoint: 0.0.0.0:13133
  zpages:
    endpoint: 0.0.0.0:55679

service:
  extensions: [health_check, zpages]
  telemetry:
    logs:
      level: info
    metrics:
      address: 0.0.0.0:8888  # Internal metrics endpoint
```

- **Health check:** `curl http://localhost:13133/`
- **zPages:** `http://localhost:55679/debug/tracez` (active spans, errors)
- **Internal metrics:** Prometheus format at `:8888/metrics`

## Scaling Strategies

1. **Vertical scaling** — Increase CPU/memory for single collector
2. **Horizontal scaling** — Multiple collector replicas behind a load balancer
3. **Sharding** — Route specific tenants/services to specific collectors
4. **Persistent queues** — Use `file_storage` extension to survive restarts

```yaml
exporters:
  otlp:
    endpoint: backend:4317
    sending_queue:
      enabled: true
      num_consumers: 10
      queue_size: 5000
      storage: file_storage  # Persist queue to disk
    retry_on_failure:
      enabled: true
      initial_interval: 5s
      max_interval: 30s
      max_elapsed_time: 300s
```

## Best Practices

1. **Always use `memory_limiter`** — Prevents OOM. Place it first in processor chain.
2. **Always use `batch` processor** — Reduces export overhead dramatically.
3. **Use contrib distribution** — Unless you need a minimal binary, contrib has everything.
4. **Monitor the collector** — Scrape its internal metrics with Prometheus.
5. **Use persistent queues** — For production, enable file-backed queues to survive restarts.
6. **Separate agent and gateway** — Agents for buffering, gateways for processing.

## Common Pitfalls

1. **Configuring but not enabling** — Adding a receiver to the config doesn't enable it. It must also appear in a `service.pipelines` entry.
2. **Processor ordering** — `memory_limiter` should be first, `batch` should be last before exporters.
3. **Resource exhaustion** — Without `memory_limiter`, the collector can OOM under load.
4. **Missing TLS in production** — Configure TLS for all receiver and exporter connections.
5. **Using core distribution** — The core collector lacks most useful receivers/exporters. Use `contrib`.
