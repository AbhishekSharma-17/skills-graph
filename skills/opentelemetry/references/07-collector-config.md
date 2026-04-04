# OpenTelemetry — Collector Configuration

> Source: [opentelemetry.io/docs/collector/configuration](https://opentelemetry.io/docs/collector/configuration/)

## Table of Contents

- [Configuration Structure](#configuration-structure)
- [Receivers Configuration](#receivers-configuration)
- [Processors Configuration](#processors-configuration)
- [Exporters Configuration](#exporters-configuration)
- [Service and Pipelines](#service-and-pipelines)
- [Extensions Configuration](#extensions-configuration)
- [Environment Variables](#environment-variables)
- [Multiple Instances](#multiple-instances)
- [TLS Configuration](#tls-configuration)
- [Complete Production Config](#complete-production-config)
- [Common Pitfalls](#common-pitfalls)

---

## Configuration Structure

The Collector uses YAML configuration with these top-level sections:

```yaml
receivers:    # How data gets in
processors:   # How data is transformed
exporters:    # Where data goes
connectors:   # Pipeline-to-pipeline bridges
extensions:   # Non-pipeline features (health, auth)
service:      # Wires everything together
```

## Receivers Configuration

### OTLP Receiver (most common)

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317        # gRPC
        max_recv_msg_size_mib: 4       # Max message size (default 4MB)
      http:
        endpoint: 0.0.0.0:4318        # HTTP
        cors:
          allowed_origins: ["*"]        # For browser instrumentation
          allowed_headers: ["*"]
```

### Prometheus Receiver (scrape targets)

```yaml
receivers:
  prometheus:
    config:
      scrape_configs:
        - job_name: "my-service"
          scrape_interval: 15s
          static_configs:
            - targets: ["app:8080"]
          metrics_path: "/metrics"
```

### Filelog Receiver (parse log files)

```yaml
receivers:
  filelog:
    include: [/var/log/myapp/*.log]
    include_file_name: true
    operators:
      - type: json_parser
        timestamp:
          parse_from: attributes.ts
          layout: "%Y-%m-%dT%H:%M:%S.%LZ"
      - type: severity_parser
        parse_from: attributes.level
```

### Host Metrics Receiver

```yaml
receivers:
  hostmetrics:
    collection_interval: 30s
    scrapers:
      cpu: {}
      memory: {}
      disk: {}
      network: {}
      load: {}
      filesystem: {}
      process:
        include:
          match_type: regexp
          names: ["myapp.*"]
```

### Kafka Receiver

```yaml
receivers:
  kafka:
    brokers: ["kafka:9092"]
    topic: "otlp-spans"
    protocol_version: "2.0.0"
    encoding: otlp_proto
```

## Processors Configuration

### Batch Processor (always use in production)

```yaml
processors:
  batch:
    send_batch_size: 1024          # Spans/metrics per batch
    send_batch_max_size: 2048      # Hard upper limit
    timeout: 10s                   # Max wait before sending
```

### Memory Limiter (always use — prevents OOM)

```yaml
processors:
  memory_limiter:
    check_interval: 5s
    limit_mib: 4000                # Hard memory limit
    spike_limit_mib: 500           # Spike tolerance
    limit_percentage: 80           # Alternative: % of total memory
    spike_limit_percentage: 25
```

### Attributes Processor

```yaml
processors:
  attributes:
    actions:
      - key: environment
        value: production
        action: insert              # insert, update, upsert, delete
      - key: internal.debug
        action: delete
      - key: db.statement
        action: hash               # Hash sensitive data
```

### Filter Processor

```yaml
processors:
  filter:
    # Drop traces matching conditions
    traces:
      span:
        - 'attributes["http.route"] == "/health"'
        - 'name == "health-check"'
    # Drop metrics matching conditions
    metrics:
      metric:
        - 'name == "http.server.active_requests" and resource.attributes["service.name"] == "test"'
    # Drop logs matching conditions
    logs:
      log_record:
        - 'severity_number < 9'    # Drop DEBUG and below
```

### Resource Processor

```yaml
processors:
  resource:
    attributes:
      - key: cloud.region
        value: us-east-1
        action: upsert
      - key: service.instance.id
        from_attribute: host.name   # Copy from existing attribute
        action: insert
```

### Transform Processor (OTTL — OTel Transformation Language)

```yaml
processors:
  transform:
    trace_statements:
      - context: span
        statements:
          - set(attributes["http.method"], ConvertCase(attributes["http.method"], "upper"))
          - replace_pattern(name, "password=[^&]*", "password=***")
    metric_statements:
      - context: datapoint
        statements:
          - set(attributes["env"], "prod") where attributes["env"] == nil
```

### Tail Sampling Processor

```yaml
processors:
  tail_sampling:
    decision_wait: 10s              # Wait for all spans in trace
    num_traces: 100000              # Max traces in memory
    policies:
      # Always sample errors
      - name: errors
        type: status_code
        status_code: { status_codes: [ERROR] }
      # Always sample slow traces
      - name: latency
        type: latency
        latency: { threshold_ms: 1000 }
      # Sample 10% of remaining traces
      - name: probabilistic
        type: probabilistic
        probabilistic: { sampling_percentage: 10 }
```

### Probabilistic Sampler Processor (head sampling)

```yaml
processors:
  probabilistic_sampler:
    sampling_percentage: 25         # Sample 25% of traces
```

## Exporters Configuration

### OTLP Exporter

```yaml
exporters:
  otlp/traces:
    endpoint: tempo:4317
    tls:
      insecure: true
    headers:
      Authorization: "Bearer ${env:API_TOKEN}"
    sending_queue:
      enabled: true
      num_consumers: 10
      queue_size: 5000
    retry_on_failure:
      enabled: true
      initial_interval: 5s
      max_interval: 30s

  otlp/metrics:
    endpoint: mimir:4317
    tls:
      insecure: true
```

### Prometheus Exporter (expose scrape endpoint)

```yaml
exporters:
  prometheus:
    endpoint: 0.0.0.0:8889
    namespace: otel
    resource_to_telemetry_conversion:
      enabled: true                  # Promote resource attrs to metric labels
```

### Debug Exporter (development)

```yaml
exporters:
  debug:
    verbosity: detailed              # basic, normal, detailed
    sampling_initial: 5
    sampling_thereafter: 200
```

### Loki Exporter

```yaml
exporters:
  loki:
    endpoint: http://loki:3100/loki/api/v1/push
    labels:
      attributes:
        severity: ""
        service.name: ""
```

## Service and Pipelines

The service section wires components into active pipelines:

```yaml
service:
  extensions: [health_check, zpages]

  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlp/traces]

    metrics:
      receivers: [otlp, prometheus, hostmetrics]
      processors: [memory_limiter, batch]
      exporters: [otlp/metrics, prometheus]

    logs:
      receivers: [otlp, filelog]
      processors: [memory_limiter, filter, batch]
      exporters: [loki]

  telemetry:
    logs:
      level: info                    # Collector's own log level
    metrics:
      level: detailed
      address: 0.0.0.0:8888         # Collector's own metrics
```

## Extensions Configuration

```yaml
extensions:
  health_check:
    endpoint: 0.0.0.0:13133
    path: "/health"

  zpages:
    endpoint: 0.0.0.0:55679

  basicauth:
    htpasswd:
      inline: |
        user1:$apr1$...

  file_storage:
    directory: /var/lib/otelcol/storage
    timeout: 10s
```

## Environment Variables

```yaml
# Reference env vars in config
exporters:
  otlp:
    endpoint: ${env:OTEL_BACKEND_ENDPOINT}
    headers:
      api-key: ${env:API_KEY}

# With defaults
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: ${env:OTLP_GRPC_ENDPOINT:-0.0.0.0:4317}
```

## Multiple Instances

Use `type/name` syntax for multiple instances of the same component:

```yaml
receivers:
  otlp/primary:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
  otlp/secondary:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4327

exporters:
  otlp/tempo:
    endpoint: tempo:4317
  otlp/jaeger:
    endpoint: jaeger:4317

service:
  pipelines:
    traces/primary:
      receivers: [otlp/primary]
      exporters: [otlp/tempo]
    traces/secondary:
      receivers: [otlp/secondary]
      exporters: [otlp/jaeger]
```

## TLS Configuration

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        tls:
          cert_file: /certs/server.crt
          key_file: /certs/server.key
          ca_file: /certs/ca.crt           # For mTLS

exporters:
  otlp:
    endpoint: backend:4317
    tls:
      cert_file: /certs/client.crt
      key_file: /certs/client.key
      ca_file: /certs/ca.crt
      insecure: false                       # Never in production
```

## Complete Production Config

```yaml
receivers:
  otlp:
    protocols:
      grpc: { endpoint: 0.0.0.0:4317 }
      http: { endpoint: 0.0.0.0:4318 }
  hostmetrics:
    collection_interval: 30s
    scrapers: { cpu: {}, memory: {}, disk: {}, network: {} }

processors:
  memory_limiter:
    check_interval: 5s
    limit_percentage: 80
    spike_limit_percentage: 25
  attributes:
    actions:
      - { key: environment, value: "${env:ENVIRONMENT}", action: upsert }
  filter:
    traces:
      span:
        - 'attributes["http.route"] == "/health"'
  batch:
    send_batch_size: 1024
    timeout: 10s

exporters:
  otlp:
    endpoint: ${env:BACKEND_ENDPOINT}
    headers: { api-key: "${env:API_KEY}" }
    sending_queue: { enabled: true, queue_size: 5000 }
    retry_on_failure: { enabled: true }

extensions:
  health_check: { endpoint: 0.0.0.0:13133 }

service:
  extensions: [health_check]
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, filter, attributes, batch]
      exporters: [otlp]
    metrics:
      receivers: [otlp, hostmetrics]
      processors: [memory_limiter, attributes, batch]
      exporters: [otlp]
    logs:
      receivers: [otlp]
      processors: [memory_limiter, attributes, batch]
      exporters: [otlp]
  telemetry:
    logs: { level: info }
    metrics: { address: 0.0.0.0:8888 }
```

## Common Pitfalls

1. **Processor order matters** — `memory_limiter` first, then transformations, then `batch` last. Wrong order can cause data loss or OOM.
2. **Forgetting service.pipelines** — A configured component does nothing unless referenced in a pipeline.
3. **Using `insecure: true` in production** — Always configure proper TLS for production deployments.
4. **Not monitoring the collector** — The collector itself needs monitoring. Scrape its `:8888/metrics` endpoint.
5. **Queue size too small** — Under-sized sending queues cause data loss during backend outages.
