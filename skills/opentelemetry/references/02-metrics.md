# OpenTelemetry — Metrics

> Source: [opentelemetry.io/docs/concepts/signals/metrics](https://opentelemetry.io/docs/concepts/signals/metrics/)

## Table of Contents

- [What Are Metrics](#what-are-metrics)
- [Meter Provider and Meter](#meter-provider-and-meter)
- [Instrument Types](#instrument-types)
- [Synchronous Instruments](#synchronous-instruments)
- [Asynchronous Instruments](#asynchronous-instruments)
- [Attributes on Metrics](#attributes-on-metrics)
- [Aggregation](#aggregation)
- [Views](#views)
- [Metric Exporters](#metric-exporters)
- [Python Examples](#python-examples)
- [Node.js Examples](#nodejs-examples)
- [Best Practices](#best-practices)
- [Common Pitfalls](#common-pitfalls)

---

## What Are Metrics

Metrics are quantitative measurements captured at runtime. Unlike traces (which capture individual requests), metrics provide statistical aggregates about system behavior — request rates, error counts, latency distributions, resource utilization.

**Key differences from traces:**

| Aspect | Traces | Metrics |
|--------|--------|---------|
| Granularity | Per-request | Aggregated |
| Cardinality | High (one per request) | Low (one per time series) |
| Cost | Higher (more data) | Lower (pre-aggregated) |
| Use case | Debugging, request flow | Alerting, dashboards, SLOs |

## Meter Provider and Meter

```python
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.resources import Resource

# MeterProvider: configured once at startup
resource = Resource.create({"service.name": "my-service"})
reader = PeriodicExportingMetricReader(
    ConsoleMetricExporter(),
    export_interval_millis=10000,  # Export every 10 seconds
)
provider = MeterProvider(resource=resource, metric_readers=[reader])
metrics.set_meter_provider(provider)

# Meter: obtained per module
meter = metrics.get_meter("my.module", "1.0.0")
```

## Instrument Types

| Instrument | Sync/Async | Monotonic | Use Case |
|------------|-----------|-----------|----------|
| **Counter** | Sync | Yes (only increases) | Request count, bytes sent |
| **UpDownCounter** | Sync | No (increases and decreases) | Active connections, queue depth |
| **Gauge** | Sync | No | Current temperature, CPU usage |
| **Histogram** | Sync | N/A (records distributions) | Request latency, response sizes |
| **Observable Counter** | Async | Yes | Total CPU time, page faults |
| **Observable UpDownCounter** | Async | No | Process memory, thread count |
| **Observable Gauge** | Async | No | Current CPU %, disk usage |

**Decision tree:**

```
Is the measurement taken at a specific code point?
├── Yes → Synchronous instrument
│   ├── Value only goes up? → Counter
│   ├── Value goes up and down? → UpDownCounter
│   ├── Need distribution (p50, p99)? → Histogram
│   └── Snapshot of current value? → Gauge
└── No → Asynchronous instrument (callback-based)
    ├── Value only goes up? → Observable Counter
    ├── Value goes up and down? → Observable UpDownCounter
    └── Snapshot of current value? → Observable Gauge
```

## Synchronous Instruments

### Counter

```python
# Counts things that only increase
request_counter = meter.create_counter(
    name="http.server.request.count",
    unit="1",
    description="Total HTTP requests received",
)

def handle_request(method, route, status):
    request_counter.add(1, {
        "http.method": method,
        "http.route": route,
        "http.status_code": status,
    })
```

### UpDownCounter

```python
# Tracks values that increase AND decrease
active_connections = meter.create_up_down_counter(
    name="http.server.active_connections",
    unit="1",
    description="Number of active HTTP connections",
)

def on_connect():
    active_connections.add(1)

def on_disconnect():
    active_connections.add(-1)
```

### Histogram

```python
# Records distributions of values (latency, sizes, etc.)
request_duration = meter.create_histogram(
    name="http.server.request.duration",
    unit="ms",
    description="HTTP request duration in milliseconds",
)

def handle_request(request):
    start = time.time()
    try:
        response = process(request)
    finally:
        duration_ms = (time.time() - start) * 1000
        request_duration.record(duration_ms, {
            "http.method": request.method,
            "http.route": request.path,
        })
```

### Gauge

```python
# Records current values (snapshots)
temperature_gauge = meter.create_gauge(
    name="system.temperature",
    unit="Cel",
    description="Current CPU temperature",
)

def update_temperature(value):
    temperature_gauge.set(value, {"cpu.core": "0"})
```

## Asynchronous Instruments

Async instruments use callbacks that are invoked during metric collection:

```python
import psutil
from opentelemetry.metrics import CallbackOptions, Observation

# Observable Gauge — CPU usage
def cpu_usage_callback(options: CallbackOptions):
    for i, pct in enumerate(psutil.cpu_percent(percpu=True)):
        yield Observation(pct, {"cpu.core": str(i)})

meter.create_observable_gauge(
    name="system.cpu.utilization",
    callbacks=[cpu_usage_callback],
    unit="1",
    description="CPU utilization per core (0-100)",
)

# Observable Counter — cumulative process CPU time
def cpu_time_callback(options: CallbackOptions):
    times = psutil.cpu_times()
    yield Observation(times.user, {"cpu.mode": "user"})
    yield Observation(times.system, {"cpu.mode": "system"})

meter.create_observable_counter(
    name="process.cpu.time",
    callbacks=[cpu_time_callback],
    unit="s",
    description="Cumulative CPU time",
)

# Observable UpDownCounter — memory usage
def memory_callback(options: CallbackOptions):
    mem = psutil.virtual_memory()
    yield Observation(mem.used, {"state": "used"})
    yield Observation(mem.available, {"state": "available"})

meter.create_observable_up_down_counter(
    name="system.memory.usage",
    callbacks=[memory_callback],
    unit="By",
    description="Memory usage by state",
)
```

## Attributes on Metrics

Attributes on metrics create distinct time series. Each unique combination of attribute values is a separate series.

```python
# These create 3 separate time series:
counter.add(1, {"method": "GET", "status": 200})
counter.add(1, {"method": "POST", "status": 201})
counter.add(1, {"method": "GET", "status": 404})
```

**Cardinality warning:** Every unique attribute combination creates a new time series. High-cardinality attributes (user IDs, request IDs) cause metric explosion. Use bounded values only.

## Aggregation

Aggregation combines multiple measurements into statistical summaries:

| Instrument | Default Aggregation | What You Get |
|------------|-------------------|--------------|
| Counter | Sum | Cumulative total |
| UpDownCounter | Sum | Current value |
| Gauge | LastValue | Most recent reading |
| Histogram | ExplicitBucketHistogram | Bucket counts + sum + min + max |

**Default histogram bucket boundaries:**

```
[0, 5, 10, 25, 50, 75, 100, 250, 500, 750, 1000, 2500, 5000, 7500, 10000]
```

## Views

Views customize how metrics are processed by the SDK:

```python
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.view import View, ExplicitBucketHistogramAggregation

# Custom histogram buckets for latency
latency_view = View(
    instrument_name="http.server.request.duration",
    aggregation=ExplicitBucketHistogramAggregation(
        boundaries=[0, 1, 5, 10, 25, 50, 100, 250, 500, 1000]
    ),
)

# Drop an attribute to reduce cardinality
drop_user_agent_view = View(
    instrument_name="http.server.request.count",
    attribute_keys=["http.method", "http.route"],  # only keep these
)

provider = MeterProvider(
    metric_readers=[reader],
    views=[latency_view, drop_user_agent_view],
)
```

## Metric Exporters

| Exporter | Package | Backend |
|----------|---------|---------|
| Console | `opentelemetry-sdk` | stdout |
| OTLP/gRPC | `opentelemetry-exporter-otlp-proto-grpc` | Collector/OTLP backend |
| OTLP/HTTP | `opentelemetry-exporter-otlp-proto-http` | Collector/OTLP backend |
| Prometheus | `opentelemetry-exporter-prometheus` | Prometheus scrape endpoint |

## Python Examples

```python
# Complete metrics setup
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    PeriodicExportingMetricReader,
)
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

exporter = OTLPMetricExporter(endpoint="localhost:4317", insecure=True)
reader = PeriodicExportingMetricReader(exporter, export_interval_millis=10000)
provider = MeterProvider(metric_readers=[reader])
metrics.set_meter_provider(provider)

meter = metrics.get_meter("my.app")
request_counter = meter.create_counter("requests")
request_duration = meter.create_histogram("request_duration", unit="ms")
```

## Node.js Examples

```typescript
import { MeterProvider, PeriodicExportingMetricReader } from "@opentelemetry/sdk-metrics";
import { OTLPMetricExporter } from "@opentelemetry/exporter-metrics-otlp-grpc";

const exporter = new OTLPMetricExporter({ url: "http://localhost:4317" });
const reader = new PeriodicExportingMetricReader({ exporter, exportIntervalMillis: 10000 });
const provider = new MeterProvider({ readers: [reader] });

const meter = provider.getMeter("my.app");
const counter = meter.createCounter("requests");
const histogram = meter.createHistogram("request_duration", { unit: "ms" });

// Record measurements
counter.add(1, { "http.method": "GET" });
histogram.record(42.5, { "http.route": "/api/users" });
```

## Best Practices

1. **Use semantic conventions** for metric names and attributes
2. **Keep cardinality bounded** — use fixed sets of attribute values
3. **Choose the right instrument** — Counter for totals, Histogram for distributions
4. **Set appropriate export intervals** — 10-60s for production, shorter for development
5. **Name metrics with dots** — `http.server.request.duration` follows OTel conventions
6. **Include units** — Always specify the unit (`ms`, `By`, `1`) for clarity

## Common Pitfalls

1. **High-cardinality attributes** — Adding user IDs or full URLs as metric attributes creates millions of time series, overwhelming backends.
2. **Using Counter for values that decrease** — Use UpDownCounter or Gauge instead. Counter only goes up.
3. **Not configuring histogram buckets** — Default buckets may not match your latency distribution. Use Views to set appropriate boundaries.
4. **Forgetting metric readers** — Without a reader attached to MeterProvider, no metrics are collected or exported.
