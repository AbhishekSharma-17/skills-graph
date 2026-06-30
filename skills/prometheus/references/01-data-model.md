# Prometheus — Data Model

> Source: [prometheus.io/docs/concepts/data_model](https://prometheus.io/docs/concepts/data_model/)

## Core Concept

Prometheus stores all data as **time series** — streams of timestamped values belonging to the same metric and labeled dimensions. Every time series is uniquely identified by its metric name and a set of key-value label pairs.

## Metric Names

Metric names identify what is being measured. They must follow specific conventions:

```
# Recommended pattern
[a-zA-Z_:][a-zA-Z0-9_:]*

# Examples
http_requests_total
node_cpu_seconds_total
process_resident_memory_bytes
```

**Rules:**
- ASCII letters, digits, underscores, and colons are the recommended character set
- Colons (`:`) are reserved for user-defined recording rules — exporters must not use them
- UTF-8 metric names are supported but require quoting in PromQL
- Names should describe the measured feature clearly

## Labels

Labels provide the multi-dimensional data model. Each unique combination of labels for a given metric name creates a distinct time series.

```
http_requests_total{method="GET", handler="/api/users", status="200"}
http_requests_total{method="POST", handler="/api/users", status="201"}
# These are TWO separate time series
```

### Label Rules

| Rule | Detail |
|------|--------|
| Naming pattern | `[a-zA-Z_][a-zA-Z0-9_]*` (recommended) |
| Reserved prefix | `__` (double underscore) is reserved for internal use |
| Empty values | Treated as if the label does not exist |
| UTF-8 support | Available but requires quoting in queries |
| Cardinality | Each unique label combination = new time series |

### Internal Labels

Labels starting with `__` are set by Prometheus during scraping and are not persisted:

| Label | Purpose |
|-------|---------|
| `__address__` | `host:port` of the scrape target |
| `__metrics_path__` | HTTP path for scraping (default `/metrics`) |
| `__scheme__` | HTTP or HTTPS |
| `__name__` | The metric name itself (used internally) |
| `__param_<name>` | URL parameter passed during scrape |

### Automatically Attached Labels

These labels are added by Prometheus to every scraped time series:

| Label | Source |
|-------|--------|
| `job` | The `job_name` from scrape config |
| `instance` | The `__address__` of the target (after relabeling) |

## Samples

Each data point in a time series is a **sample** consisting of:

1. **Value** — a float64 number or a native histogram
2. **Timestamp** — millisecond-precision Unix time

## Time Series Notation

The standard notation for a time series combines the metric name and labels:

```
<metric_name>{<label_name>="<label_value>", ...}
```

Examples:

```
# Standard notation
api_http_requests_total{method="POST", handler="/messages"}

# Using __name__ label (equivalent)
{__name__="api_http_requests_total", method="POST", handler="/messages"}

# UTF-8 metric name (quoted form)
{"api.http.requests.total", method="POST"}
```

## Naming Best Practices

### Metric Name Structure

```
<namespace>_<subsystem>_<name>_<unit>_<suffix>
```

| Component | Example | Purpose |
|-----------|---------|---------|
| Namespace | `prometheus_`, `node_`, `myapp_` | Single-word application prefix |
| Subsystem | `http_`, `disk_`, `cpu_` | Feature area within the app |
| Name | `requests`, `duration`, `size` | What is measured |
| Unit | `_seconds`, `_bytes`, `_total` | Base unit (always use base units) |

### Base Units

| Measurement | Unit | Example |
|-------------|------|---------|
| Time | seconds | `http_request_duration_seconds` |
| Data size | bytes | `http_response_size_bytes` |
| Temperature | celsius | `node_hwmon_temp_celsius` |
| Ratio | ratio (0–1) | `node_filesystem_avail_ratio` |
| Voltage | volts | `node_hwmon_in_volts` |
| Energy | joules | `node_energy_joules_total` |

### Suffixes by Metric Type

| Suffix | Metric Type | Example |
|--------|-------------|---------|
| `_total` | Counter | `http_requests_total` |
| `_seconds` | Duration | `request_duration_seconds` |
| `_bytes` | Size | `response_size_bytes` |
| `_info` | Info (pseudo-metric) | `build_info` |
| `_created` | Created timestamp | `process_start_time_seconds` |
| `_bucket` | Histogram bucket | `request_duration_seconds_bucket` |
| `_sum` | Histogram/Summary sum | `request_duration_seconds_sum` |
| `_count` | Histogram/Summary count | `request_duration_seconds_count` |

### Label Design

```python
# GOOD — use labels for dimensions
http_requests_total{method="GET", status="200"}
http_requests_total{method="POST", status="500"}

# BAD — separate metrics per dimension
http_requests_get_total
http_requests_post_total
```

**Guidelines:**
- `sum()` or `avg()` over all label dimensions should be meaningful
- Avoid labels with unbounded cardinality (user IDs, email addresses, UUIDs)
- Keep cardinality under 10 labels per metric; investigate if approaching 100+
- Don't repeat metric name information in labels
- Use labels for dimensions you'll filter/aggregate on

## Exposition Format

Metrics are exposed as plain text over HTTP:

```
# HELP http_requests_total Total number of HTTP requests.
# TYPE http_requests_total counter
http_requests_total{method="get",code="200"} 1027 1395066363000
http_requests_total{method="post",code="200"} 42 1395066363000

# HELP node_cpu_seconds_total Seconds the CPUs spent in each mode.
# TYPE node_cpu_seconds_total counter
node_cpu_seconds_total{cpu="0",mode="idle"} 362946.26
node_cpu_seconds_total{cpu="0",mode="system"} 7423.18
```

Lines prefixed with `# HELP` provide a description; `# TYPE` declares the metric type.

## Common Pitfalls

| Pitfall | Why It's Bad | Fix |
|---------|--------------|-----|
| High-cardinality labels | Millions of time series, OOM | Use bounded label values |
| Missing `_total` suffix | PromQL `rate()` won't auto-detect counter | Always suffix counters |
| Colons in exporter metrics | Reserved for recording rules | Only use colons in recording rules |
| Metric name in label | Redundant, wastes storage | Use one metric with labels |
| Percentages as metrics | Loses numerator/denominator | Export raw counts, derive in PromQL |

## Related Topics

- Metric types in detail → `02-metric-types.md`
- Naming patterns for exporters → `11-exporters.md`
- PromQL label matching → `04-promql-basics.md`
