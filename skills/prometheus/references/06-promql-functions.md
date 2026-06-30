# Prometheus — PromQL Functions

> Source: [prometheus.io/docs/prometheus/latest/querying/functions](https://prometheus.io/docs/prometheus/latest/querying/functions/)

## Table of Contents

- [Rate Functions](#rate-functions)
- [Histogram Functions](#histogram-functions)
- [Aggregation Over Time](#aggregation-over-time)
- [Label Manipulation](#label-manipulation)
- [Prediction and Regression](#prediction-and-regression)
- [Math Functions](#math-functions)
- [Time Functions](#time-functions)
- [Comparison and Detection](#comparison-and-detection)
- [Sorting and Selection](#sorting-and-selection)
- [Utility Functions](#utility-functions)
- [Function Selection Guide](#function-selection-guide)

## Rate Functions

### rate(v range-vector)

Per-second average rate of increase over the range window. Automatically adjusts for counter resets. **The most commonly used function.**

```promql
# Request rate per second over 5 minutes
rate(http_requests_total[5m])

# Error rate per job
sum by (job) (rate(http_requests_total{status=~"5.."}[5m]))
```

**Guidelines:**
- Range window should be at least 4× the scrape interval for reliability
- Use for alerting and slow-moving counters
- Always use with counters, never with gauges

### irate(v range-vector)

Instantaneous rate based on the **last two data points** in the range. More responsive to sudden changes but noisier.

```promql
# Instantaneous CPU rate
irate(node_cpu_seconds_total{mode="idle"}[5m])
```

**When to use:** Dashboards showing volatile, fast-moving counters. **Avoid for alerting** — too noisy.

### increase(v range-vector)

Total increase over the range. Syntactic sugar for `rate(v) × range_seconds`. Extrapolates to cover the full range.

```promql
# Total requests in the last hour
increase(http_requests_total[1h])

# Errors in the last 24 hours
increase(http_errors_total[24h])
```

### delta(v range-vector)

Difference between the first and last sample in a range. For **gauges** only.

```promql
# Temperature change over 2 hours
delta(temperature_celsius[2h])
```

### idelta(v range-vector)

Difference between the last two samples. The gauge equivalent of `irate()`.

```promql
idelta(temperature_celsius[5m])
```

## Histogram Functions

### histogram_quantile(φ scalar, b instant-vector)

Calculates the φ-quantile (0 ≤ φ ≤ 1) from histogram buckets.

```promql
# 90th percentile request duration
histogram_quantile(0.9, rate(http_request_duration_seconds_bucket[10m]))

# 99th percentile by endpoint
histogram_quantile(0.99,
  sum by (endpoint, le) (rate(http_request_duration_seconds_bucket[10m]))
)

# Median (50th percentile)
histogram_quantile(0.5, rate(http_request_duration_seconds_bucket[5m]))

# With native histograms (no _bucket suffix needed)
histogram_quantile(0.95, rate(http_request_duration_seconds[5m]))
```

**Important:** When aggregating, always preserve the `le` label in `sum by`:

```promql
# CORRECT — preserves le
histogram_quantile(0.9, sum by (job, le) (rate(duration_bucket[5m])))

# WRONG — drops le, breaks quantile calculation
histogram_quantile(0.9, sum by (job) (rate(duration_bucket[5m])))
```

### histogram_count(v instant-vector)

Observation count from a native histogram.

```promql
histogram_count(rate(http_request_duration_seconds[5m]))
```

### histogram_sum(v instant-vector)

Sum of observations from a native histogram.

```promql
histogram_sum(rate(http_request_duration_seconds[5m]))
```

### histogram_avg(v instant-vector)

Arithmetic mean from a native histogram.

```promql
histogram_avg(rate(http_request_duration_seconds[5m]))
```

### histogram_fraction(lower, upper, v instant-vector)

Estimated fraction of observations between bounds.

```promql
# Fraction of requests between 100ms and 500ms
histogram_fraction(0.1, 0.5, rate(http_request_duration_seconds[5m]))
```

### histogram_stddev / histogram_stdvar

Standard deviation and variance from native histogram observations.

## Aggregation Over Time

Apply aggregation functions across a range of samples for each time series:

| Function | Description |
|----------|-------------|
| `avg_over_time(v[d])` | Average value over range |
| `min_over_time(v[d])` | Minimum value over range |
| `max_over_time(v[d])` | Maximum value over range |
| `sum_over_time(v[d])` | Sum of all values in range |
| `count_over_time(v[d])` | Count of samples in range |
| `quantile_over_time(φ, v[d])` | φ-quantile over range |
| `stddev_over_time(v[d])` | Population standard deviation |
| `stdvar_over_time(v[d])` | Population variance |
| `last_over_time(v[d])` | Most recent sample |
| `first_over_time(v[d])` | Oldest sample |
| `present_over_time(v[d])` | Returns 1 if any sample exists |

```promql
# Average CPU over the last hour
avg_over_time(node_cpu_seconds_total{mode="idle"}[1h])

# Peak memory in the last day
max_over_time(process_resident_memory_bytes[1d])

# 95th percentile latency over 30 minutes
quantile_over_time(0.95, http_request_duration_seconds[30m])

# Count of samples (useful for detecting gaps)
count_over_time(up[1h])
```

## Label Manipulation

### label_replace(v, dst, replacement, src, regex)

Regex match on a source label, write result to a destination label:

```promql
# Extract service name from instance label
label_replace(up, "service", "$1", "instance", "(.*):.*")
# instance="api-server:8080" → service="api-server"

# Add a static label
label_replace(up, "env", "production", "", "")

# Rename a label
label_replace(metric, "pod_name", "$1", "pod", "(.*)")
```

### label_join(v, dst, separator, src1, src2, ...)

Concatenate multiple label values:

```promql
# Join namespace and pod name
label_join(up, "full_name", "/", "namespace", "pod")
# namespace="default", pod="web-1" → full_name="default/web-1"
```

## Prediction and Regression

### predict_linear(v range-vector, t scalar)

Predict the value `t` seconds from now using simple linear regression:

```promql
# Predict disk space in 4 hours
predict_linear(node_filesystem_avail_bytes{mountpoint="/"}[6h], 4*3600)

# Alert if disk will fill in 24 hours
predict_linear(node_filesystem_avail_bytes{mountpoint="/"}[6h], 24*3600) < 0
```

### deriv(v range-vector)

Per-second derivative using linear regression. For **gauges** only.

```promql
# Rate of memory change
deriv(process_resident_memory_bytes[15m])
```

## Math Functions

| Function | Description | Example |
|----------|-------------|---------|
| `abs(v)` | Absolute value | `abs(deriv(temp[1h]))` |
| `ceil(v)` | Round up | `ceil(request_duration)` |
| `floor(v)` | Round down | `floor(request_duration)` |
| `round(v [, to])` | Round to nearest (default 1) | `round(cpu_usage, 0.01)` |
| `sqrt(v)` | Square root | `sqrt(variance_metric)` |
| `exp(v)` | e^x | `exp(log_metric)` |
| `ln(v)` | Natural log | `ln(growth_metric)` |
| `log2(v)` | Log base 2 | `log2(memory_bytes)` |
| `log10(v)` | Log base 10 | `log10(large_counter)` |
| `sgn(v)` | Sign (-1, 0, 1) | `sgn(deriv(temp[1h]))` |
| `clamp(v, min, max)` | Clamp to range | `clamp(cpu, 0, 1)` |
| `clamp_min(v, min)` | Floor at minimum | `clamp_min(free_bytes, 0)` |
| `clamp_max(v, max)` | Cap at maximum | `clamp_max(ratio, 1)` |
| `pi()` | π constant | `pi()` |

Trigonometric functions: `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `sinh`, `cosh`, `tanh`, `asinh`, `acosh`, `atanh`, `deg`, `rad`.

## Time Functions

| Function | Returns |
|----------|---------|
| `time()` | Current Unix timestamp (seconds) |
| `timestamp(v)` | Timestamp of each sample |
| `year(v)` | Year from timestamp |
| `month(v)` | Month (1-12) |
| `day_of_month(v)` | Day of month (1-31) |
| `day_of_week(v)` | Day of week (0=Sunday) |
| `day_of_year(v)` | Day of year (1-366) |
| `hour(v)` | Hour (0-23) |
| `minute(v)` | Minute (0-59) |
| `days_in_month(v)` | Days in the month |

```promql
# Time since last scrape
time() - timestamp(up)

# Time since last successful batch
time() - batch_last_success_timestamp_seconds

# Filter by business hours (9-17, Monday-Friday)
up and on() (hour() >= 9 < 17) and on() (day_of_week() >= 1 <= 5)
```

## Comparison and Detection

### absent(v instant-vector)

Returns a 1-element vector if the input is empty. Essential for alerting on missing metrics:

```promql
# Alert if no "up" metric exists for a job
absent(up{job="api-server"})

# Alert if a specific target is completely gone
absent(node_cpu_seconds_total{instance="web-1:9100"})
```

### absent_over_time(v range-vector)

Returns 1 if no samples exist in the range:

```promql
absent_over_time(up{job="api-server"}[5m])
```

### changes(v range-vector)

Number of times a value changed in the range:

```promql
# Detect frequent config reloads
changes(process_start_time_seconds[1h]) > 5
```

### resets(v range-vector)

Number of counter resets (decreases) in the range:

```promql
# Detect frequent restarts
resets(process_start_time_seconds[1h])
```

## Sorting and Selection

| Function | Description |
|----------|-------------|
| `sort(v)` | Sort by value ascending |
| `sort_desc(v)` | Sort by value descending |
| `sort_by_label(v, label...)` | Sort by label value ascending |
| `sort_by_label_desc(v, label...)` | Sort by label value descending |

```promql
# Top consumers sorted by memory
sort_desc(process_resident_memory_bytes)

# Sort by pod name
sort_by_label(up, "pod")
```

## Utility Functions

### vector(s scalar) / scalar(v instant-vector)

```promql
# Convert scalar to vector
vector(1)

# Convert single-element vector to scalar
scalar(count(up))
```

### info(v instant-vector) [experimental]

Enrich metrics with labels from info-type series sharing the same `instance` and `job`.

## Function Selection Guide

| I want to... | Function |
|--------------|----------|
| Request rate from counter | `rate()` |
| Spike detection | `irate()` |
| Total count over time | `increase()` |
| Latency percentiles | `histogram_quantile()` |
| Average over time | `avg_over_time()` |
| Predict future value | `predict_linear()` |
| Detect missing metric | `absent()` |
| Change rate of a gauge | `deriv()` |
| Rename/create labels | `label_replace()` |
| Detect restarts | `resets()` or `changes()` |
| Time since event | `time() - timestamp()` |

## Related Topics

- PromQL basics and selectors → `04-promql-basics.md`
- PromQL operators → `05-promql-operators.md`
- Recording rules for pre-computing expensive queries → `07-rules.md`
