# Prometheus — Metric Types

> Source: [prometheus.io/docs/concepts/metric_types](https://prometheus.io/docs/concepts/metric_types/)

## Overview

Prometheus client libraries offer four core metric types. The type is encoded in the exposition format metadata and used by the Prometheus server for storage and query optimization.

## Counter

A counter is a cumulative metric that **only increases** or resets to zero on process restart.

### Characteristics

- Monotonically increasing (never decreases)
- Resets to 0 when the process restarts
- PromQL's `rate()` and `increase()` handle resets automatically
- Always suffix with `_total`

### When to Use

- Total HTTP requests served
- Total errors encountered
- Total bytes sent/received
- Total tasks completed
- Total database queries executed

### Examples

```python
# Python
from prometheus_client import Counter

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

def handle_request(method, endpoint, status):
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
```

```go
// Go
httpRequests := prometheus.NewCounterVec(
    prometheus.CounterOpts{
        Name: "http_requests_total",
        Help: "Total HTTP requests",
    },
    []string{"method", "endpoint", "status"},
)
httpRequests.WithLabelValues("GET", "/api/users", "200").Inc()
```

### PromQL with Counters

```promql
# Per-second request rate over 5 minutes
rate(http_requests_total[5m])

# Total increase over the last hour
increase(http_requests_total[1h])

# Error ratio
rate(http_requests_total{status=~"5.."}[5m])
  / rate(http_requests_total[5m])
```

### Anti-patterns

```python
# BAD — don't use a counter for values that decrease
active_connections = Counter("active_connections_total", ...)  # Use Gauge instead

# BAD — don't manually decrement
my_counter.dec()  # Counters don't support dec()
```

## Gauge

A gauge represents a value that **can go up and down** arbitrarily.

### Characteristics

- Current snapshot of a value
- Can increase, decrease, or be set to an arbitrary value
- No automatic reset detection in PromQL

### When to Use

- Current temperature, CPU usage, memory usage
- Number of active connections or in-flight requests
- Queue depth
- Disk space available
- Number of goroutines / threads

### Examples

```python
# Python
from prometheus_client import Gauge

ACTIVE_REQUESTS = Gauge(
    "http_active_requests",
    "Currently active HTTP requests",
    ["method"]
)

# Track in-flight requests
ACTIVE_REQUESTS.labels(method="GET").inc()
# ... handle request ...
ACTIVE_REQUESTS.labels(method="GET").dec()

# Or use as context manager
with ACTIVE_REQUESTS.labels(method="POST").track_inprogress():
    process_request()

# Set to a specific value
TEMPERATURE = Gauge("room_temperature_celsius", "Room temperature")
TEMPERATURE.set(22.5)

# Set to current time
LAST_PROCESSED = Gauge("batch_last_success_timestamp_seconds", "Last success")
LAST_PROCESSED.set_to_current_time()
```

### PromQL with Gauges

```promql
# Current value
node_memory_MemAvailable_bytes

# Average over time
avg_over_time(node_cpu_seconds_total{mode="idle"}[5m])

# Predict value in 4 hours using linear regression
predict_linear(node_filesystem_avail_bytes[1h], 4 * 3600)

# Rate of change for a gauge
deriv(node_memory_MemAvailable_bytes[15m])

# Min/max over the last hour
min_over_time(node_memory_MemAvailable_bytes[1h])
max_over_time(node_memory_MemAvailable_bytes[1h])
```

## Histogram

A histogram samples observations (typically durations or sizes) and counts them in configurable buckets. It also provides a sum of all observed values and a count of observations.

### Classic Histogram

Classic histograms expose multiple time series:

| Series | Format | Purpose |
|--------|--------|---------|
| Buckets | `<name>_bucket{le="<upper_bound>"}` | Cumulative count per bucket |
| Sum | `<name>_sum` | Total sum of observed values |
| Count | `<name>_count` | Total number of observations |

```python
# Python — classic histogram
from prometheus_client import Histogram

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "Request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Observe a duration
REQUEST_DURATION.labels(method="GET", endpoint="/api").observe(0.35)

# Or use as decorator/context manager
@REQUEST_DURATION.labels(method="GET", endpoint="/api").time()
def handle_get_request():
    pass
```

Exposed metrics:

```
http_request_duration_seconds_bucket{method="GET",endpoint="/api",le="0.1"} 24054
http_request_duration_seconds_bucket{method="GET",endpoint="/api",le="0.25"} 33444
http_request_duration_seconds_bucket{method="GET",endpoint="/api",le="0.5"} 100392
http_request_duration_seconds_bucket{method="GET",endpoint="/api",le="+Inf"} 144320
http_request_duration_seconds_sum{method="GET",endpoint="/api"} 53423.21
http_request_duration_seconds_count{method="GET",endpoint="/api"} 144320
```

### Native Histogram (Recommended)

Native histograms are more efficient — no explicit bucket configuration, higher resolution, and single-series atomic transfers.

```go
// Go — native histogram
requestDuration := prometheus.NewHistogram(prometheus.HistogramOpts{
    Name:                        "http_request_duration_seconds",
    Help:                        "Request duration",
    NativeHistogramBucketFactor: 1.1,
})
```

Native histograms require enabling in Prometheus config:

```yaml
global:
  scrape_protocols: [PrometheusProto]
```

### PromQL with Histograms

```promql
# 90th percentile latency (classic)
histogram_quantile(0.9, rate(http_request_duration_seconds_bucket[5m]))

# 90th percentile by handler
histogram_quantile(0.9,
  sum by (handler, le) (rate(http_request_duration_seconds_bucket[5m]))
)

# 99th percentile (native histogram)
histogram_quantile(0.99, rate(http_request_duration_seconds[5m]))

# Average request duration
rate(http_request_duration_seconds_sum[5m])
  / rate(http_request_duration_seconds_count[5m])

# Apdex score (requests < 0.3s + half of requests < 1.2s) / total
(
  sum(rate(http_request_duration_seconds_bucket{le="0.3"}[5m]))
  + sum(rate(http_request_duration_seconds_bucket{le="1.2"}[5m]))
) / 2 / sum(rate(http_request_duration_seconds_count[5m]))

# Fraction of requests between 200ms and 500ms (native)
histogram_fraction(0.2, 0.5, rate(http_request_duration_seconds[5m]))
```

### Bucket Selection Guidelines

| Scenario | Suggested Buckets |
|----------|------------------|
| Fast API endpoints | `0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5` |
| Database queries | `0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1, 5, 10` |
| Batch processing | `1, 5, 10, 30, 60, 120, 300, 600` |
| Response sizes (bytes) | `100, 1000, 10000, 100000, 1000000` |

## Summary

Summaries calculate streaming φ-quantiles on the client side over a configurable sliding time window.

### Characteristics

- Calculates quantiles in the client, not the server
- Cannot be aggregated across instances
- Sliding time window (default 10 minutes, configurable)
- Exposes `<name>{quantile="<φ>"}`, `<name>_sum`, `<name>_count`

```python
from prometheus_client import Summary

REQUEST_DURATION = Summary(
    "http_request_duration_seconds",
    "Request duration",
    ["method"]
)

REQUEST_DURATION.labels(method="GET").observe(0.12)
```

### Histogram vs Summary

| Aspect | Histogram | Summary |
|--------|-----------|---------|
| Quantile calculation | Server-side (PromQL) | Client-side |
| Aggregation | Aggregatable across instances | **Not aggregatable** |
| Accuracy | Depends on bucket boundaries | Configurable error (φ ± ε) |
| Cost | Fixed time series per bucket | Fixed time series per quantile |
| Configuration | Bucket boundaries | Quantile targets, max age, age buckets |
| Recommendation | **Preferred** (use native histograms) | Only when pre-computed quantiles needed |

**General guidance:** Use native histograms when your client library supports them (Go, Java). Fall back to classic histograms when native support is unavailable. Use summaries only when you specifically need client-side quantiles and don't need to aggregate across instances.

## Info and Stateset (Special Types)

### Info

Pseudo-metric for exposing textual information as labels with a constant value of 1:

```
# TYPE build_info info
build_info{version="1.2.3",branch="main",goversion="go1.22"} 1
```

### Stateset

Represents a set of states where exactly one is active:

```
# TYPE feature_flags stateset
feature_flags{feature_flags="dark_mode"} 1
feature_flags{feature_flags="beta_api"} 0
```

## Common Pitfalls

| Pitfall | Impact | Fix |
|---------|--------|-----|
| Too few histogram buckets | Poor quantile accuracy | Add buckets around SLO thresholds |
| Too many histogram buckets | High cardinality, slow queries | Keep under 15 buckets per histogram |
| Using Summary for SLOs | Can't aggregate across pods | Use Histogram instead |
| Forgetting `_total` on counters | `rate()` behavior may differ | Always suffix counters |
| Counter for fluctuating values | Incorrect rate calculations | Use Gauge for current-state metrics |

## Related Topics

- Naming conventions → `01-data-model.md`
- Querying metrics → `04-promql-basics.md`, `06-promql-functions.md`
- Client libraries → `10-instrumentation.md`
