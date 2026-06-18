# Grafana — Prometheus & PromQL

> Source: [grafana.com/docs/grafana/latest/datasources/prometheus](https://grafana.com/docs/grafana/latest/datasources/prometheus/) — Grafana 13.0

## Overview

Prometheus is the most widely used metrics backend with Grafana. Grafana provides a rich query editor with both Builder and Code modes for writing PromQL queries. Understanding PromQL is essential for building effective dashboards.

## Data Source Configuration

```yaml
# Provisioning YAML
datasources:
  - name: Prometheus
    type: prometheus
    uid: prometheus
    url: http://prometheus:9090
    access: proxy
    isDefault: true
    jsonData:
      timeInterval: "15s"        # Minimum scrape interval
      httpMethod: POST           # POST for large queries
      exemplarTraceIdDestinations:
        - name: traceID
          datasourceUid: tempo
```

### Key Settings

| Setting | Purpose | Default |
|---------|---------|---------|
| `timeInterval` | Minimum step for `$__rate_interval` | `15s` |
| `httpMethod` | GET or POST for queries | `POST` |
| `queryTimeout` | Max query execution time | `60s` |
| `incrementalQuerying` | Cache and reuse partial results | `false` |
| `disableRecordingRules` | Hide recording rules from autocomplete | `false` |

## Query Editor Modes

### Builder Mode

Visual query construction — ideal for learning PromQL:

1. **Metric** — Select a metric name from autocomplete
2. **Label filters** — Add `job="api"`, `status=~"5.."` etc.
3. **Operations** — Add functions: Rate, Sum, Avg, etc.
4. **Options** — Legend format, min step, instant/range

### Code Mode

Write raw PromQL with autocomplete and syntax highlighting:

```promql
sum(rate(http_requests_total{job="api", status=~"5.."}[5m])) by (path)
```

### Explain Toggle

Enable the **Explain** toggle to see a step-by-step breakdown of each query component.

## PromQL Fundamentals

### Data Types

| Type | Description | Example |
|------|-------------|---------|
| **Instant vector** | Single sample per series at one timestamp | `http_requests_total` |
| **Range vector** | Multiple samples per series over a time window | `http_requests_total[5m]` |
| **Scalar** | Single numeric value | `42`, `3.14` |
| **String** | String value (rarely used) | `"hello"` |

### Selectors

```promql
# Exact match
http_requests_total{job="api"}

# Regex match
http_requests_total{status=~"5.."}

# Negative match
http_requests_total{method!="OPTIONS"}

# Negative regex
http_requests_total{path!~"/health|/ready"}
```

### Range Vector Selectors

```promql
# Last 5 minutes of samples
http_requests_total[5m]

# With offset (look back 1 hour)
http_requests_total[5m] offset 1h

# At a specific time
http_requests_total @ 1609459200
```

## Essential Functions

### Rate Functions

```promql
# Per-second rate over 5m window (use for counters)
rate(http_requests_total[5m])

# Total increase over 5m window
increase(http_requests_total[5m])

# Per-second rate using last two samples (more responsive, noisier)
irate(http_requests_total[5m])
```

**Rule of thumb:** Use `rate()` for dashboards, `irate()` for high-resolution ad-hoc analysis.

### Aggregation Operators

```promql
# Sum across all instances
sum(rate(http_requests_total[5m]))

# Sum grouped by label
sum(rate(http_requests_total[5m])) by (method, path)

# Average across instances
avg(node_cpu_seconds_total{mode="idle"}) by (instance)

# Min/Max
min(node_filesystem_avail_bytes) by (instance, mountpoint)
max(node_memory_MemTotal_bytes) by (instance)

# Count number of series
count(up{job="api"})

# Top 5 by value
topk(5, sum(rate(http_requests_total[5m])) by (path))

# Bottom 5
bottomk(5, node_filesystem_avail_bytes)

# Quantile (50th percentile)
quantile(0.5, rate(http_requests_total[5m]))
```

### Histogram Functions

```promql
# P95 request duration from histogram
histogram_quantile(0.95,
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le)
)

# P99 grouped by endpoint
histogram_quantile(0.99,
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le, path)
)
```

### Math and Comparison

```promql
# Percentage
100 * (1 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) by (instance))

# Comparison (returns only matching series)
http_requests_total > 1000

# Comparison (returns 1/0 for all series)
http_requests_total > bool 1000

# Clamping values
clamp_min(free_memory_bytes, 0)
clamp_max(cpu_percent, 100)
```

### Label Functions

```promql
# Replace label values
label_replace(up, "short_instance", "$1", "instance", "(.*):.*")

# Join labels from another metric
group_left: vector1 * on(instance) group_left(region) vector2
```

## Grafana-Specific Variables

Use these in PromQL queries for dynamic behavior:

| Variable | Purpose | Example Value |
|----------|---------|---------------|
| `$__rate_interval` | Safe rate interval (≥ 4× scrape interval) | `1m` |
| `$__interval` | Auto-calculated step interval | `15s` |
| `$__range` | Dashboard time range duration | `6h` |
| `$__from` / `$__to` | Time range bounds (epoch ms) | `1718700000000` |
| `${variable_name}` | Dashboard variable value | `production` |

### Best Practices for Rate Intervals

```promql
# GOOD — use $__rate_interval (auto-adjusts to avoid gaps)
rate(http_requests_total[$__rate_interval])

# BAD — hardcoded interval may miss scrapes
rate(http_requests_total[5m])

# GOOD — for increase() use $__range for full-range totals
increase(http_requests_total[$__range])
```

## Common Dashboard Queries

### RED Method (Rate, Errors, Duration)

```promql
# Request Rate
sum(rate(http_requests_total[$__rate_interval])) by (service)

# Error Rate (%)
100 * sum(rate(http_requests_total{status=~"5.."}[$__rate_interval]))
  / sum(rate(http_requests_total[$__rate_interval]))

# Duration (P95)
histogram_quantile(0.95,
  sum(rate(http_request_duration_seconds_bucket[$__rate_interval])) by (le, service)
)
```

### USE Method (Utilization, Saturation, Errors)

```promql
# CPU Utilization
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[$__rate_interval])) by (instance) * 100)

# Memory Utilization
100 * (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)

# Disk Saturation (I/O wait)
avg(rate(node_cpu_seconds_total{mode="iowait"}[$__rate_interval])) by (instance) * 100

# Network Errors
rate(node_network_receive_errs_total[$__rate_interval])
```

### Kubernetes Queries

```promql
# Pod CPU usage
sum(rate(container_cpu_usage_seconds_total{namespace="$namespace"}[$__rate_interval])) by (pod)

# Pod Memory
sum(container_memory_working_set_bytes{namespace="$namespace"}) by (pod)

# Pod Restart Count
sum(increase(kube_pod_container_status_restarts_total{namespace="$namespace"}[$__range])) by (pod)
```

## Query Options

| Option | Purpose |
|--------|---------|
| **Legend** | Format series name: `{{method}} {{path}}` |
| **Min step** | Minimum resolution step |
| **Format** | Time series, Table, Heatmap |
| **Type** | Both, Range, Instant |
| **Exemplars** | Show trace exemplar links on data points |

## Recording Rules

Pre-compute expensive queries as new time series:

```yaml
# prometheus/rules.yml
groups:
  - name: api_rules
    interval: 30s
    rules:
      - record: api:http_requests:rate5m
        expr: sum(rate(http_requests_total{job="api"}[5m])) by (method, path)

      - record: api:http_errors:ratio
        expr: |
          sum(rate(http_requests_total{job="api", status=~"5.."}[5m]))
          / sum(rate(http_requests_total{job="api"}[5m]))
```

Use recording rules in Grafana dashboards for faster queries and lower Prometheus load.

## Common Pitfalls

- **Using `irate()` in dashboards** — `irate()` is noisy and resolution-dependent; prefer `rate()` for dashboard panels
- **Hardcoded rate intervals** — Always use `$__rate_interval` instead of `[5m]` to avoid gaps at different zoom levels
- **Missing `by` clause** — `sum(rate(...))` without `by()` collapses everything into one line
- **Histogram without `le`** — `histogram_quantile` requires `by (le)` in the inner aggregation
- **Counter resets** — `rate()` handles resets automatically; never use `increase()` on a gauge
- **High cardinality** — Avoid queries that expand to thousands of series (e.g., `by (user_id)`)
