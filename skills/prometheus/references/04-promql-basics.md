# Prometheus — PromQL Basics

> Source: [prometheus.io/docs/prometheus/latest/querying/basics](https://prometheus.io/docs/prometheus/latest/querying/basics/)

## Table of Contents

- [Expression Data Types](#expression-data-types)
- [Literals](#literals)
- [Instant Vector Selectors](#instant-vector-selectors)
- [Range Vector Selectors](#range-vector-selectors)
- [Label Matchers](#label-matchers)
- [Offset Modifier](#offset-modifier)
- [At Modifier](#at-modifier)
- [Subqueries](#subqueries)
- [Practical Query Patterns](#practical-query-patterns)
- [Common Pitfalls](#common-pitfalls)

## Expression Data Types

PromQL has four value types:

| Type | Description | Example |
|------|-------------|---------|
| **Instant vector** | Set of time series, each with a single sample at one timestamp | `http_requests_total` |
| **Range vector** | Set of time series, each with a range of samples over time | `http_requests_total[5m]` |
| **Scalar** | Simple numeric floating-point value | `42`, `3.14`, `NaN` |
| **String** | Simple string value (currently unused in practice) | `"hello"` |

Instant queries accept any of the four types. Range queries (used by graphs) only accept instant vectors and scalars.

## Literals

### String Literals

```promql
# Single quotes (Go-style escaping)
'hello world'

# Double quotes (Go-style escaping)
"hello\nworld"

# Backticks (raw string, no escaping)
`no\escape\here`
```

### Float Literals

```promql
42
3.14
-0.5
1.5e3       # 1500
0xFF        # 255 (hex)
1_000_000   # underscores for readability
NaN
+Inf
-Inf
```

### Duration Literals

| Unit | Meaning |
|------|---------|
| `ms` | milliseconds |
| `s` | seconds |
| `m` | minutes |
| `h` | hours |
| `d` | days (24h) |
| `w` | weeks (7d) |
| `y` | years (365d) |

Durations are concatenated in descending order:

```promql
5m          # 5 minutes
1h30m       # 1 hour 30 minutes
2d12h       # 2 days 12 hours
```

Durations must use integers — `1.5h` is invalid, use `1h30m` instead.

## Instant Vector Selectors

Select the most recent sample from matching time series at the evaluation timestamp.

```promql
# By metric name
http_requests_total

# With label filters
http_requests_total{job="api-server", method="GET"}

# By __name__ label (equivalent)
{__name__="http_requests_total", job="api-server"}

# Without metric name (match by labels only)
{job="api-server"}

# UTF-8 metric name
{"http.requests.total", job="api-server"}
```

A selector must specify at least one label matcher that does not match the empty string, or a metric name.

## Range Vector Selectors

Append a duration in square brackets to select all samples within a time range ending at the evaluation timestamp.

```promql
# All samples from the last 5 minutes
http_requests_total{job="api-server"}[5m]

# Last 1 hour
node_cpu_seconds_total[1h]

# Last 30 seconds
process_resident_memory_bytes[30s]
```

Range vectors cannot be graphed directly — they must be passed to a function like `rate()` or `avg_over_time()` that returns an instant vector.

**Boundary behavior:** Samples at the left boundary (oldest) are excluded; samples at the right boundary (newest) are included.

## Label Matchers

Four matching operators are available:

| Operator | Meaning | Example |
|----------|---------|---------|
| `=` | Exact match | `{job="api"}` |
| `!=` | Not equal | `{job!="test"}` |
| `=~` | Regex match | `{job=~"api\|web"}` |
| `!~` | Regex non-match | `{status!~"2.."}` |

**Regex rules:**
- Regexes are **fully anchored** — `{job=~"api"}` matches only `"api"`, not `"api-server"`
- Use `.*` for partial matches: `{job=~"api.*"}`
- RE2 syntax (no lookaheads/lookbehinds)
- Alternation: `{method=~"GET|POST|PUT"}`

```promql
# All non-200 responses
http_requests_total{status!="200"}

# All 5xx errors across all jobs
http_requests_total{status=~"5.."}

# Exclude test and staging environments
http_requests_total{environment!~"test|staging"}

# Match any metric starting with "http_"
{__name__=~"http_.*"}
```

## Offset Modifier

Shift the evaluation time into the past:

```promql
# Current value
http_requests_total

# Value 5 minutes ago
http_requests_total offset 5m

# Value 1 hour ago
http_requests_total offset 1h

# With range vector — rate 5 minutes ago
rate(http_requests_total[5m] offset 1h)

# Negative offset (into the future, requires --enable-feature=promql-negative-offset)
http_requests_total offset -5m
```

## At Modifier

Evaluate at a specific Unix timestamp:

```promql
# Value at a specific time
http_requests_total @ 1609746000

# With range vector
rate(http_requests_total[5m]) @ 1609746000

# Use start/end of range query
http_requests_total @ start()
http_requests_total @ end()

# Combine with offset
rate(http_requests_total[5m] @ 1609746000 offset 1h)
```

Modifier precedence: `@` is applied first, then `offset` shifts from there.

## Subqueries

Evaluate an instant query over a range, producing a range vector:

```promql
# Syntax
<instant_query> '[' <range> ':' [<resolution>] ']' [offset <duration>]

# Rate over 5m, evaluated every 1m for the last 30m
rate(http_requests_total[5m])[30m:1m]

# Max of a rate over the last hour, sampled every minute
max_over_time(rate(http_requests_total[5m])[1h:1m])

# Default resolution (= global evaluation_interval)
rate(http_requests_total[5m])[30m:]

# Nested — max of derivative of rate
max_over_time(
  deriv(
    rate(distance_covered_total[5s])[30s:5s]
  )[10m:]
)
```

## Practical Query Patterns

### Rate and Increase

```promql
# Per-second rate (smoothed over 5m window)
rate(http_requests_total[5m])

# Instantaneous rate (based on last 2 points)
irate(http_requests_total[5m])

# Total increase over 1 hour
increase(http_requests_total[1h])
```

### Filtering and Aggregation

```promql
# Sum by job
sum by (job) (rate(http_requests_total[5m]))

# Average by instance
avg by (instance) (node_cpu_seconds_total{mode="idle"})

# Top 5 by request rate
topk(5, sum by (handler) (rate(http_requests_total[5m])))

# Count of instances
count by (job) (up)
```

### Arithmetic

```promql
# Memory usage percentage
(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes)
  / node_memory_MemTotal_bytes * 100

# Error ratio
sum(rate(http_requests_total{status=~"5.."}[5m]))
  / sum(rate(http_requests_total[5m]))

# Available disk in GiB
node_filesystem_avail_bytes / (1024^3)
```

### Absence Detection

```promql
# Returns 1 if no matching series exists (good for alerting on missing targets)
absent(up{job="my-app"})

# Returns 1 if no samples exist in a range
absent_over_time(up{job="my-app"}[5m])
```

### Timestamp and Staleness

```promql
# How long since last scrape succeeded
time() - max by (instance) (timestamp(up))

# Time since last successful batch job
time() - batch_last_success_timestamp_seconds
```

## Common Pitfalls

| Pitfall | Why It Fails | Fix |
|---------|-------------|-----|
| Graphing a range vector | `http_requests_total[5m]` can't be plotted | Wrap in `rate()` or `avg_over_time()` |
| Using `rate()` on a gauge | Rate assumes monotonically increasing | Use `deriv()` for gauges |
| Too-short range for `rate()` | Need at least 2 samples | Range ≥ 2× scrape interval |
| `irate()` for alerting | Too volatile, misses spikes | Use `rate()` for alerts |
| Regex without `.*` | `=~"api"` matches only exact "api" | Use `=~"api.*"` for prefix |
| `sum` without `by` | Loses all labels | Add `by (label1, label2)` |
| Duration with floats | `1.5h` is invalid | Use `1h30m` |

## Related Topics

- Operators and aggregation → `05-promql-operators.md`
- Functions reference → `06-promql-functions.md`
- Recording rules for pre-computed queries → `07-rules.md`
