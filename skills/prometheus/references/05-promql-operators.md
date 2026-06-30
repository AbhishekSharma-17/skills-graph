# Prometheus — PromQL Operators

> Source: [prometheus.io/docs/prometheus/latest/querying/operators](https://prometheus.io/docs/prometheus/latest/querying/operators/)

## Table of Contents

- [Arithmetic Operators](#arithmetic-operators)
- [Comparison Operators](#comparison-operators)
- [Logical/Set Operators](#logicalset-operators)
- [Vector Matching](#vector-matching)
- [Aggregation Operators](#aggregation-operators)
- [Operator Precedence](#operator-precedence)
- [Practical Patterns](#practical-patterns)

## Arithmetic Operators

| Operator | Operation |
|----------|-----------|
| `+` | Addition |
| `-` | Subtraction |
| `*` | Multiplication |
| `/` | Division |
| `%` | Modulo |
| `^` | Exponentiation |

Behavior by operand types:

| Left | Right | Result |
|------|-------|--------|
| scalar | scalar | scalar |
| vector | scalar | vector (applied to each sample) |
| scalar | vector | vector (applied to each sample) |
| vector | vector | vector (matched by labels) |

```promql
# Scalar arithmetic
2 + 3                    # 5

# Vector-scalar: convert bytes to MiB
node_memory_MemTotal_bytes / 1024 / 1024

# Vector-vector: memory usage percentage
(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes)
  / node_memory_MemTotal_bytes * 100
```

## Comparison Operators

| Operator | Meaning |
|----------|---------|
| `==` | Equal |
| `!=` | Not equal |
| `>` | Greater than |
| `<` | Less than |
| `>=` | Greater or equal |
| `<=` | Less or equal |

**Default behavior (filter):** Drop samples that don't match.

```promql
# Keep only series where value > 0.9
http_request_duration_seconds > 0.9

# Keep instances with less than 10% disk free
(node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.1
```

**Bool modifier:** Return 0 or 1 instead of filtering.

```promql
# Returns 1 where up == 1, 0 where up != 1
up == bool 1

# Binary health indicator
(node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) > bool 0.2
```

## Logical/Set Operators

Work exclusively between two instant vectors:

| Operator | Behavior |
|----------|----------|
| `and` | **Intersection** — returns left elements that have matching label sets on right |
| `or` | **Union** — all left elements, plus right elements not in left |
| `unless` | **Complement** — left elements without matching label sets on right |

```promql
# Intersection: only show rates for series that are "up"
rate(http_requests_total[5m]) and on(instance) up

# Union: combine two metrics
node_cpu_seconds_total{mode="idle"} or node_cpu_seconds_total{mode="system"}

# Complement: all instances except those with high error rate
up unless on(instance) (rate(http_errors_total[5m]) > 0.1)
```

## Vector Matching

When binary operators combine two instant vectors, Prometheus must decide which series on the left match which series on the right.

### One-to-One Matching

By default, series match when all labels are identical (after dropping `__name__`).

```promql
# Only matches if both sides have the same label set
method_code:http_errors:rate5m / method:http_requests:rate5m
```

Modify matching with `on()` or `ignoring()`:

```promql
# Match only on 'method' label
method_code:http_errors:rate5m
  / ignoring(code) method:http_requests:rate5m

# Equivalent: match on specific labels
method_code:http_errors:rate5m
  / on(method) method:http_requests:rate5m
```

### Many-to-One / One-to-Many

When one side has more label combinations, use `group_left` or `group_right`:

```promql
# Left side has more series (multiple 'code' values per 'method')
method_code:http_errors:rate5m
  / ignoring(code) group_left method:http_requests:rate5m

# group_left can copy labels from the "one" side
method_code:http_errors:rate5m
  / ignoring(code) group_left(handler) method:http_requests:rate5m
```

**Rules:**
- `group_left` — the left vector has higher cardinality (many-to-one)
- `group_right` — the right vector has higher cardinality (one-to-many)
- The "one" side must have exactly one match per label set
- Optional label list in `group_left(label1, label2)` copies those labels from the "one" side

### Matching Summary

```
# One-to-one (default)
<vector> <op> <vector>

# Modified matching
<vector> <op> ignoring(<labels>) <vector>
<vector> <op> on(<labels>) <vector>

# Many-to-one
<vector> <op> ignoring(<labels>) group_left(<copy_labels>) <vector>
<vector> <op> on(<labels>) group_left(<copy_labels>) <vector>

# One-to-many
<vector> <op> ignoring(<labels>) group_right(<copy_labels>) <vector>
```

## Aggregation Operators

Reduce the dimensions of an instant vector, grouping by specified labels.

### Syntax

```promql
# Keep specified labels
<aggr-op> by (<label_list>) (<vector>)

# Remove specified labels
<aggr-op> without (<label_list>) (<vector>)

# Parameter-based (topk, bottomk, quantile, count_values)
<aggr-op>(<parameter>, <vector>) by (<label_list>)
```

### Available Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `sum` | Sum of values | `sum by (job) (rate(http_requests_total[5m]))` |
| `avg` | Average of values | `avg by (instance) (cpu_usage)` |
| `min` | Minimum value | `min by (job) (up)` |
| `max` | Maximum value | `max by (instance) (node_memory_MemTotal_bytes)` |
| `count` | Count of elements | `count by (job) (up)` |
| `group` | Returns 1 per group | `group by (job) (up)` |
| `stddev` | Population standard deviation | `stddev by (job) (request_duration)` |
| `stdvar` | Population variance | `stdvar by (job) (request_duration)` |
| `topk` | Largest k elements | `topk(5, rate(http_requests_total[5m]))` |
| `bottomk` | Smallest k elements | `bottomk(3, rate(http_errors_total[5m]))` |
| `quantile` | φ-quantile over values | `quantile(0.95, rate(http_requests_total[5m]))` |
| `count_values` | Count of each unique value | `count_values("version", build_info)` |
| `limitk` | Sample k elements | `limitk(10, up)` |
| `limit_ratio` | Sample ratio of elements | `limit_ratio(0.1, up)` |

### Examples

```promql
# Total request rate per job
sum by (job) (rate(http_requests_total[5m]))

# Average memory per namespace (Kubernetes)
avg by (namespace) (container_memory_usage_bytes)

# Request rate, dropping instance detail
sum without (instance) (rate(http_requests_total[5m]))

# Top 10 endpoints by request rate
topk(10, sum by (handler) (rate(http_requests_total[5m])))

# 95th percentile request rate across all instances
quantile(0.95, rate(http_requests_total[5m]))

# Count unique Go versions in the cluster
count_values("go_version", go_info)

# Number of targets per job
count by (job) (up)
```

## Operator Precedence

From highest to lowest:

| Precedence | Operators | Associativity |
|------------|-----------|---------------|
| 1 (highest) | `^` | Right |
| 2 | `*`, `/`, `%`, `atan2` | Left |
| 3 | `+`, `-` | Left |
| 4 | `==`, `!=`, `<=`, `<`, `>=`, `>` | Left |
| 5 | `and`, `unless` | Left |
| 6 (lowest) | `or` | Left |

Use parentheses to override:

```promql
# Without parens: (a * b) + c
a * b + c

# With parens: a * (b + c)
a * (b + c)
```

## Practical Patterns

### Error Rate Calculation

```promql
# Error ratio (0-1)
sum by (job) (rate(http_requests_total{status=~"5.."}[5m]))
  / sum by (job) (rate(http_requests_total[5m]))

# Error percentage
sum by (job) (rate(http_requests_total{status=~"5.."}[5m]))
  / sum by (job) (rate(http_requests_total[5m])) * 100
```

### SLI / SLO Queries

```promql
# Availability SLI (proportion of successful requests)
sum(rate(http_requests_total{status!~"5.."}[30d]))
  / sum(rate(http_requests_total[30d]))

# Latency SLI (proportion of requests under 300ms)
sum(rate(http_request_duration_seconds_bucket{le="0.3"}[30d]))
  / sum(rate(http_request_duration_seconds_count[30d]))

# Remaining error budget
1 - (
  (1 - sum(rate(http_requests_total{status!~"5.."}[30d]))
       / sum(rate(http_requests_total[30d])))
  / (1 - 0.999)  # 99.9% SLO target
)
```

### Resource Saturation

```promql
# CPU saturation
1 - avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m]))

# Memory saturation
1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)

# Disk saturation
1 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})
```

## Common Pitfalls

| Pitfall | Impact | Fix |
|---------|--------|-----|
| Missing `on()` / `ignoring()` | No matches between vectors | Specify which labels to match |
| `group_left` on wrong side | Error or unexpected cardinality | Put `group_left` on the higher-cardinality side |
| `topk` output varies | Different series each evaluation | Expected behavior — use recording rules for stability |
| `sum` without `by` | All labels dropped | Always specify `by (label1, label2)` |
| Comparing vectors with different labels | Empty result | Use `on()` to align label sets |

## Related Topics

- PromQL basics and selectors → `04-promql-basics.md`
- PromQL functions → `06-promql-functions.md`
- Recording rules for pre-computing → `07-rules.md`
