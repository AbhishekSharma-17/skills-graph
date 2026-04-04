# OpenTelemetry — Deployment

> Source: [opentelemetry.io/docs/collector/deployment](https://opentelemetry.io/docs/collector/deployment/)

## Table of Contents

- [Deployment Overview](#deployment-overview)
- [Docker Deployment](#docker-deployment)
- [Docker Compose Stack](#docker-compose-stack)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Kubernetes Operator](#kubernetes-operator)
- [Agent Pattern (DaemonSet)](#agent-pattern-daemonset)
- [Gateway Pattern (Deployment)](#gateway-pattern-deployment)
- [Hybrid Architecture](#hybrid-architecture)
- [Production Checklist](#production-checklist)
- [Monitoring the Collector](#monitoring-the-collector)
- [Scaling Guidelines](#scaling-guidelines)
- [Common Pitfalls](#common-pitfalls)

---

## Deployment Overview

| Pattern | Infrastructure | Best For |
|---------|---------------|----------|
| **Direct export** | No collector | Dev, prototyping |
| **Docker sidecar** | Docker Compose | Single-host apps |
| **K8s DaemonSet** | Kubernetes | Agent per node |
| **K8s Deployment** | Kubernetes | Centralized gateway |
| **Hybrid** | Kubernetes | Production at scale |

## Docker Deployment

### Minimal Collector

```bash
# Run with default config
docker run -d --name otel-collector \
  -p 4317:4317 \
  -p 4318:4318 \
  -p 13133:13133 \
  otel/opentelemetry-collector-contrib

# Run with custom config
docker run -d --name otel-collector \
  -p 4317:4317 \
  -p 4318:4318 \
  -v $(pwd)/otel-config.yaml:/etc/otelcol-contrib/config.yaml \
  otel/opentelemetry-collector-contrib
```

### Sidecar Pattern

```dockerfile
# Dockerfile for your app
FROM python:3.12-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["opentelemetry-instrument", "python", "app.py"]
```

## Docker Compose Stack

Complete observability stack with Grafana, Tempo, Prometheus, and Loki:

```yaml
version: "3.9"

services:
  app:
    build: .
    environment:
      OTEL_SERVICE_NAME: my-service
      OTEL_EXPORTER_OTLP_ENDPOINT: http://otel-collector:4317
      OTEL_EXPORTER_OTLP_INSECURE: "true"
    depends_on: [otel-collector]

  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    ports:
      - "4317:4317"   # OTLP gRPC
      - "4318:4318"   # OTLP HTTP
      - "13133:13133" # Health check
      - "8888:8888"   # Internal metrics
    volumes:
      - ./otel-config.yaml:/etc/otelcol-contrib/config.yaml

  tempo:
    image: grafana/tempo:latest
    ports:
      - "3200:3200"   # Tempo query
    volumes:
      - ./tempo-config.yaml:/etc/tempo/config.yaml
    command: ["-config.file=/etc/tempo/config.yaml"]

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yaml:/etc/prometheus/prometheus.yml

  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      GF_AUTH_ANONYMOUS_ENABLED: "true"
      GF_AUTH_ANONYMOUS_ORG_ROLE: Admin
    volumes:
      - ./grafana-datasources.yaml:/etc/grafana/provisioning/datasources/datasources.yaml
```

### Collector config for Docker Compose:

```yaml
receivers:
  otlp:
    protocols:
      grpc: { endpoint: 0.0.0.0:4317 }
      http: { endpoint: 0.0.0.0:4318 }

processors:
  memory_limiter:
    check_interval: 5s
    limit_mib: 512
  batch:
    send_batch_size: 512
    timeout: 5s

exporters:
  otlp/tempo:
    endpoint: tempo:4317
    tls: { insecure: true }
  otlp/loki:
    endpoint: loki:3100
    tls: { insecure: true }
  prometheus:
    endpoint: 0.0.0.0:8889

extensions:
  health_check: { endpoint: 0.0.0.0:13133 }

service:
  extensions: [health_check]
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlp/tempo]
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [prometheus]
    logs:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlp/loki]
```

## Kubernetes Deployment

### Helm Chart Installation

```bash
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
helm repo update

# DaemonSet mode (agent per node)
helm install otel-agent open-telemetry/opentelemetry-collector \
  --set mode=daemonset \
  --set config.receivers.otlp.protocols.grpc.endpoint="0.0.0.0:4317" \
  --set config.exporters.otlp.endpoint="otel-gateway:4317"

# Deployment mode (centralized gateway)
helm install otel-gateway open-telemetry/opentelemetry-collector \
  --set mode=deployment \
  --set replicaCount=3 \
  --values gateway-values.yaml
```

### Custom Values File

```yaml
# gateway-values.yaml
mode: deployment
replicaCount: 3

config:
  receivers:
    otlp:
      protocols:
        grpc: { endpoint: 0.0.0.0:4317 }
        http: { endpoint: 0.0.0.0:4318 }
  processors:
    memory_limiter:
      check_interval: 5s
      limit_percentage: 80
    batch:
      send_batch_size: 1024
      timeout: 10s
    tail_sampling:
      decision_wait: 10s
      policies:
        - { name: errors, type: status_code, status_code: { status_codes: [ERROR] } }
        - { name: sample, type: probabilistic, probabilistic: { sampling_percentage: 10 } }
  exporters:
    otlp:
      endpoint: tempo.monitoring:4317
      tls: { insecure: true }
  service:
    pipelines:
      traces:
        receivers: [otlp]
        processors: [memory_limiter, tail_sampling, batch]
        exporters: [otlp]

resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 2
    memory: 4Gi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
```

## Kubernetes Operator

The OTel Operator provides CRDs for managing collectors and auto-instrumentation:

```bash
# Install operator
kubectl apply -f https://github.com/open-telemetry/opentelemetry-operator/releases/latest/download/opentelemetry-operator.yaml
```

```yaml
# OpenTelemetryCollector CRD
apiVersion: opentelemetry.io/v1beta1
kind: OpenTelemetryCollector
metadata:
  name: otel-collector
spec:
  mode: deployment  # deployment, daemonset, sidecar, statefulset
  replicas: 3
  config:
    receivers:
      otlp:
        protocols:
          grpc: {}
          http: {}
    processors:
      batch: {}
    exporters:
      otlp:
        endpoint: tempo:4317
    service:
      pipelines:
        traces:
          receivers: [otlp]
          processors: [batch]
          exporters: [otlp]
```

### Auto-Instrumentation with Operator

```yaml
# Instrumentation CRD — auto-injects OTel into pods
apiVersion: opentelemetry.io/v1alpha1
kind: Instrumentation
metadata:
  name: auto-instrumentation
spec:
  exporter:
    endpoint: http://otel-collector:4317
  propagators:
    - tracecontext
    - baggage
  python:
    image: ghcr.io/open-telemetry/opentelemetry-operator/autoinstrumentation-python:latest
  nodejs:
    image: ghcr.io/open-telemetry/opentelemetry-operator/autoinstrumentation-nodejs:latest
```

```yaml
# Annotate pods for auto-instrumentation
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    metadata:
      annotations:
        instrumentation.opentelemetry.io/inject-python: "true"
        # or: inject-nodejs, inject-java, inject-dotnet
    spec:
      containers:
        - name: app
          image: my-app:latest
```

## Agent Pattern (DaemonSet)

One collector per node. Lightweight, low-latency data offloading:

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: otel-agent
spec:
  selector:
    matchLabels: { app: otel-agent }
  template:
    metadata:
      labels: { app: otel-agent }
    spec:
      containers:
        - name: collector
          image: otel/opentelemetry-collector-contrib
          resources:
            requests: { cpu: 100m, memory: 256Mi }
            limits: { cpu: 500m, memory: 512Mi }
          ports:
            - containerPort: 4317
              hostPort: 4317  # Apps connect to localhost:4317
```

## Gateway Pattern (Deployment)

Centralized collector(s) receiving from agents or directly from apps:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: otel-gateway
spec:
  replicas: 3
  selector:
    matchLabels: { app: otel-gateway }
  template:
    spec:
      containers:
        - name: collector
          image: otel/opentelemetry-collector-contrib
          resources:
            requests: { cpu: 1, memory: 2Gi }
            limits: { cpu: 4, memory: 8Gi }
```

## Hybrid Architecture

```
┌────────────────────────────────────────────────────────┐
│  Kubernetes Cluster                                     │
│                                                        │
│  ┌──────┐  ┌──────┐  ┌──────┐                        │
│  │ App  │  │ App  │  │ App  │  (pods with apps)      │
│  └──┬───┘  └──┬───┘  └──┬───┘                        │
│     │OTLP     │         │                              │
│     ▼         ▼         ▼                              │
│  ┌──────────────────────────┐  (DaemonSet agents)     │
│  │ Agent Collectors (per node)│                        │
│  │ - Batch                   │                        │
│  │ - Memory limiter          │                        │
│  └──────────┬───────────────┘                         │
│             │ OTLP                                     │
│             ▼                                          │
│  ┌──────────────────────────┐  (Deployment gateway)   │
│  │ Gateway Collectors (3x)   │                        │
│  │ - Tail sampling           │                        │
│  │ - Attribute processing    │                        │
│  │ - Multi-backend export    │                        │
│  └─────┬────────┬──────┬───┘                         │
│        │        │      │                              │
└────────┼────────┼──────┼──────────────────────────────┘
         ▼        ▼      ▼
      Tempo   Prometheus  Loki
```

## Production Checklist

- [ ] Set `service.name` on all services
- [ ] Use `BatchSpanProcessor` (never Simple in production)
- [ ] Configure `memory_limiter` on all collectors
- [ ] Enable TLS for all connections
- [ ] Set resource limits on collector pods
- [ ] Monitor collector health (`:13133/health`)
- [ ] Scrape collector internal metrics (`:8888/metrics`)
- [ ] Configure persistent sending queues
- [ ] Set up alerting on `otelcol_exporter_send_failed_spans`
- [ ] Enable retry on failure for all exporters
- [ ] Test collector config with `otelcol validate --config=config.yaml`
- [ ] Configure sampling appropriate to traffic volume
- [ ] Set `OTEL_RESOURCE_ATTRIBUTES` in deployment manifests

## Monitoring the Collector

Key metrics to watch:

| Metric | Alert When |
|--------|-----------|
| `otelcol_receiver_accepted_spans` | Drops to zero |
| `otelcol_receiver_refused_spans` | Increases |
| `otelcol_exporter_send_failed_spans` | > 0 sustained |
| `otelcol_exporter_queue_size` | Approaching capacity |
| `otelcol_processor_dropped_spans` | Increases unexpectedly |
| `process_runtime_total_alloc_bytes` | Approaching limit |

## Scaling Guidelines

| Traffic (spans/sec) | Collector Setup | Resources |
|---------------------|----------------|-----------|
| < 1,000 | Single instance | 0.5 CPU, 512Mi |
| 1,000 - 10,000 | 2-3 replicas | 1 CPU, 2Gi each |
| 10,000 - 100,000 | Agent + Gateway | Agent: 0.5 CPU; Gateway: 2-4 CPU |
| > 100,000 | Sharded fleet | Multiple gateways, load balanced |

## Common Pitfalls

1. **No resource limits** — Collector without limits can consume all node resources under load.
2. **Sidecar mode overhead** — One collector per pod wastes resources. Use DaemonSet for agent pattern.
3. **Not validating config** — Run `otelcol validate` before deploying. Invalid config crashes the collector.
4. **Health check not exposed** — Without health checks, Kubernetes can't restart unhealthy collectors.
5. **Missing HPA** — High-traffic gateways need horizontal pod autoscaling to handle load spikes.
