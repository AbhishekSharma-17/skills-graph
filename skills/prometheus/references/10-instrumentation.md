# Prometheus — Instrumentation & Client Libraries

> Source: [prometheus.io/docs/instrumenting](https://prometheus.io/docs/instrumenting/clientlibs/) | [prometheus.github.io/client_python](https://prometheus.github.io/client_python/)

## Table of Contents

- [Official Client Libraries](#official-client-libraries)
- [Python Client](#python-client)
- [Go Client](#go-client)
- [Instrumentation Best Practices](#instrumentation-best-practices)
- [What to Instrument](#what-to-instrument)
- [Common Pitfalls](#common-pitfalls)

## Official Client Libraries

| Language | Package | Install |
|----------|---------|---------|
| **Go** | `github.com/prometheus/client_golang` | `go get github.com/prometheus/client_golang/prometheus` |
| **Java** | `io.prometheus:prometheus-metrics-core` | Maven/Gradle dependency |
| **Python** | `prometheus-client` | `pip install prometheus-client` |
| **Ruby** | `prometheus-client` | `gem install prometheus-client` |
| **Rust** | `prometheus` | `cargo add prometheus` |

Notable third-party clients: Node.js (`prom-client`), .NET (`prometheus-net`), C++ (`prometheus-cpp`), PHP, Elixir, Erlang.

## Python Client

### Quick Start

```python
from prometheus_client import start_http_server, Counter, Gauge, Histogram, Summary
import time

# Define metrics
REQUEST_COUNT = Counter(
    "myapp_requests_total",
    "Total requests",
    ["method", "endpoint"]
)

REQUEST_DURATION = Histogram(
    "myapp_request_duration_seconds",
    "Request duration",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

ACTIVE_REQUESTS = Gauge(
    "myapp_active_requests",
    "Active requests in flight"
)

# Start metrics server on port 8000
start_http_server(8000)
```

### Counter

```python
from prometheus_client import Counter

ERRORS = Counter("myapp_errors_total", "Total errors", ["type"])

# Increment
ERRORS.labels(type="timeout").inc()
ERRORS.labels(type="validation").inc(5)

# Count exceptions
@ERRORS.labels(type="unhandled").count_exceptions()
def risky_function():
    pass
```

### Gauge

```python
from prometheus_client import Gauge

QUEUE_SIZE = Gauge("myapp_queue_size", "Items in queue", ["queue_name"])
TEMPERATURE = Gauge("myapp_temperature_celsius", "Current temperature")

# Set, increment, decrement
QUEUE_SIZE.labels(queue_name="default").set(42)
QUEUE_SIZE.labels(queue_name="default").inc()
QUEUE_SIZE.labels(queue_name="default").dec(3)

# Track in-progress
IN_PROGRESS = Gauge("myapp_in_progress_requests", "Requests in progress")

@IN_PROGRESS.track_inprogress()
def process_request():
    pass

# Set to current time
LAST_SUCCESS = Gauge("myapp_last_success_timestamp_seconds", "Last success")
LAST_SUCCESS.set_to_current_time()
```

### Histogram

```python
from prometheus_client import Histogram

DURATION = Histogram(
    "myapp_request_duration_seconds",
    "Request duration",
    ["method"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Observe a value
DURATION.labels(method="GET").observe(0.235)

# Time a function
@DURATION.labels(method="POST").time()
def handle_post():
    pass

# Context manager
with DURATION.labels(method="PUT").time():
    do_work()
```

### Summary

```python
from prometheus_client import Summary

LATENCY = Summary(
    "myapp_request_latency_seconds",
    "Request latency",
    ["endpoint"]
)

LATENCY.labels(endpoint="/api").observe(0.12)

@LATENCY.labels(endpoint="/health").time()
def health_check():
    pass
```

### Framework Integration

**FastAPI:**

```python
from fastapi import FastAPI, Request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import time

app = FastAPI()

REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests",
    ["method", "endpoint", "status"]
)
REQUEST_DURATION = Histogram(
    "http_request_duration_seconds", "Request duration",
    ["method", "endpoint"]
)

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

**Flask:**

```python
from flask import Flask
from prometheus_client import make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware

app = Flask(__name__)
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    "/metrics": make_wsgi_app()
})
```

**Django:**

```python
# urls.py
from django.urls import path
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from django.http import HttpResponse

def metrics_view(request):
    return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)

urlpatterns = [
    path("metrics", metrics_view),
]
```

### Multiprocess Mode

Required when running with gunicorn (multiple workers):

```python
import os
os.environ["PROMETHEUS_MULTIPROC_DIR"] = "/tmp/prometheus_multiproc"

from prometheus_client import CollectorRegistry, multiprocess, generate_latest

def metrics():
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    return generate_latest(registry)
```

```bash
# Create the multiprocess directory
mkdir -p /tmp/prometheus_multiproc

# Gunicorn with cleanup on worker exit
gunicorn --config gunicorn.conf.py app:app
```

### Pushgateway Integration

For short-lived batch jobs:

```python
from prometheus_client import CollectorRegistry, Counter, push_to_gateway

registry = CollectorRegistry()
counter = Counter("batch_records_processed_total", "Records processed", registry=registry)

counter.inc(1500)
push_to_gateway("pushgateway:9091", job="nightly-etl", registry=registry)
```

## Go Client

```go
package main

import (
    "net/http"
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
    requestCount = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "myapp_http_requests_total",
            Help: "Total HTTP requests",
        },
        []string{"method", "path", "status"},
    )
    requestDuration = prometheus.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "myapp_http_request_duration_seconds",
            Help:    "Request duration",
            Buckets: prometheus.DefBuckets,
            // For native histograms:
            // NativeHistogramBucketFactor: 1.1,
        },
        []string{"method", "path"},
    )
)

func init() {
    prometheus.MustRegister(requestCount, requestDuration)
}

func main() {
    http.Handle("/metrics", promhttp.Handler())
    http.ListenAndServe(":8080", nil)
}
```

## Instrumentation Best Practices

### What to Instrument

**Every service should expose at minimum:**

| Metric | Type | Description |
|--------|------|-------------|
| `<name>_requests_total` | Counter | Total requests/operations |
| `<name>_errors_total` | Counter | Total errors |
| `<name>_duration_seconds` | Histogram | Request/operation latency |
| `<name>_in_progress` | Gauge | Current in-flight operations |

### By Service Type

**Online-Serving (HTTP APIs, databases):**
- Request count, error count, latency
- Monitor both client and server side
- Count at request completion (not start)

**Offline Processing (queues, pipelines):**
- Items entering, in-progress, completed
- Stage durations
- Last processing timestamp (for stall detection)

**Batch Jobs:**
- Last success timestamp
- Total items processed
- Job duration
- Use Pushgateway for push-based reporting

### Library Instrumentation

```python
# Libraries should expose metrics without requiring user configuration
class DatabaseClient:
    QUERY_DURATION = Histogram(
        "db_query_duration_seconds",
        "Database query duration",
        ["operation", "table"]
    )
    QUERY_ERRORS = Counter(
        "db_query_errors_total",
        "Database query errors",
        ["operation", "table", "error_type"]
    )

    def query(self, sql, table):
        with self.QUERY_DURATION.labels(operation="select", table=table).time():
            try:
                return self._execute(sql)
            except Exception as e:
                self.QUERY_ERRORS.labels(
                    operation="select", table=table, error_type=type(e).__name__
                ).inc()
                raise
```

### Label Strategy

- Keep cardinality **below 10** per metric typically
- **Never** use unbounded values as labels (user IDs, email, UUIDs, IP addresses)
- Investigate if cardinality approaches 100+
- Use labels for dimensions you will filter and aggregate

```python
# GOOD — bounded cardinality
REQUEST_COUNT.labels(method="GET", status="200")

# BAD — unbounded cardinality
REQUEST_COUNT.labels(user_id="abc-123-def")  # Millions of series!
```

### Performance

- In hot paths (>100K calls/second), cache label lookups
- Avoid creating metrics inside request handlers — define at module level
- Export zero-value defaults for expected series to prevent gaps

```python
# Pre-initialize expected label combinations
for method in ["GET", "POST", "PUT", "DELETE"]:
    for status in ["200", "400", "404", "500"]:
        REQUEST_COUNT.labels(method=method, status=status)
```

## Common Pitfalls

| Pitfall | Impact | Fix |
|---------|--------|-----|
| Metrics defined inside functions | New metric registered per call, memory leak | Define at module/package level |
| Missing multiprocess setup | Metrics incorrect with gunicorn workers | Set `PROMETHEUS_MULTIPROC_DIR` |
| Labels with user IDs | Cardinality explosion | Use bounded values only |
| Missing error counters | Can't compute error rates | Always pair request counter with error counter |
| Not using `.time()` | Manual timing prone to bugs | Use decorator/context manager |
| Histograms without relevant buckets | Poor quantile accuracy | Set buckets around your SLO thresholds |

## Related Topics

- Metric types in detail → `02-metric-types.md`
- Naming conventions → `01-data-model.md`
- Writing exporters → `11-exporters.md`
- PromQL for querying instrumented metrics → `04-promql-basics.md`
