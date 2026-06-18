# Grafana — Loki & LogQL

> Source: [grafana.com/docs/loki/latest/query](https://grafana.com/docs/loki/latest/query/) — Grafana 13.0 / Loki 3.4

## Overview

Grafana Loki is a log aggregation system designed for cost-effective log storage and querying. LogQL is Loki's query language, inspired by PromQL. It supports log queries (returning log lines) and metric queries (computing values from logs). Grafana provides native Loki integration with a dedicated query editor.

## Data Source Configuration

```yaml
datasources:
  - name: Loki
    type: loki
    uid: loki
    url: http://loki:3100
    access: proxy
    jsonData:
      maxLines: 1000
      derivedFields:
        - datasourceUid: tempo
          matcherRegex: '"traceID":"(\\w+)"'
          name: TraceID
          url: "$${__value.raw}"
```

## LogQL Query Structure

```
{stream_selector} | line_filter | parser | label_filter | line_format | ...
```

A LogQL query consists of:
1. **Stream selector** (required) — selects log streams by labels
2. **Log pipeline** (optional) — filters and transforms log lines

## Stream Selectors

```logql
# Exact match
{job="api", namespace="production"}

# Regex match
{service=~"auth|gateway"}

# Negative match
{job!="debug"}

# Negative regex
{namespace!~"test|staging"}
```

**Best practice:** Use the most specific stream selector possible to minimize data scanned.

## Line Filters

Filter log lines by content (distributed grep):

```logql
# Contains string (case-sensitive)
{job="api"} |= "error"

# Does not contain
{job="api"} != "health"

# Regex match
{job="api"} |~ "status=(4|5)\\d\\d"

# Regex does not match
{job="api"} !~ "DEBUG|TRACE"
```

Line filters are the fastest pipeline stage — always apply them before parsers.

## Parsers

Extract labels from log line content:

### JSON Parser

```logql
# Parse JSON log lines
{job="api"} | json

# Extract specific fields
{job="api"} | json level, msg, duration

# Access nested fields
{job="api"} | json response_code="response.code"
```

### Logfmt Parser

```logql
# Parse key=value format
{job="api"} | logfmt

# Extract specific keys
{job="api"} | logfmt level, duration, path
```

### Pattern Parser

```logql
# Extract from structured patterns
{job="nginx"} | pattern `<ip> - - [<_>] "<method> <path> <_>" <status> <size>`
```

### Regexp Parser

```logql
# Extract with named capture groups
{job="api"} | regexp `(?P<level>\w+)\s+(?P<msg>.+)`
```

### Parser Comparison

| Parser | Speed | Best For |
|--------|-------|----------|
| **json** | Fast | JSON-structured logs |
| **logfmt** | Fast | `key=value` structured logs |
| **pattern** | Fast | Fixed-format logs (nginx, access logs) |
| **regexp** | Slow | Complex unstructured logs |

## Label Filters

Filter on extracted or existing labels:

```logql
# After parsing, filter by extracted label
{job="api"} | json | level = "error"

# Numeric comparison
{job="api"} | json | duration > 500

# Regex on label value
{job="api"} | json | path =~ "/api/v2/.*"

# Multiple filters (AND)
{job="api"} | json | level = "error" | status >= 500

# IP comparison
{job="nginx"} | pattern `<ip> <_>` | ip = ip("192.168.1.0/24")
```

## Line Format

Transform the output line:

```logql
# Custom output format
{job="api"} | json | line_format "{{.level}} [{{.duration}}ms] {{.path}}: {{.msg}}"

# Include labels in output
{job="api"} | json | line_format "{{.level | ToUpper}} {{.msg}}"
```

Template functions: `ToUpper`, `ToLower`, `Replace`, `Trim`, `regexReplaceAll`, `printf`.

## Label Format

Rename, modify, or create labels:

```logql
# Rename a label
{job="api"} | json | label_format service=job

# Concatenate labels
{job="api"} | json | label_format endpoint="{{.method}} {{.path}}"
```

## Metric Queries

Compute numeric values from log data:

### Log Range Aggregations

```logql
# Count log lines per second
count_over_time({job="api"} |= "error" [5m])

# Rate of log lines
rate({job="api"} |= "error" [5m])

# Sum of extracted numeric field
sum_over_time({job="api"} | json | unwrap duration [5m])

# Average response time from logs
avg_over_time({job="api"} | json | unwrap duration [5m])

# P95 duration from logs
quantile_over_time(0.95, {job="api"} | json | unwrap duration [5m])

# Bytes rate (log volume)
bytes_rate({job="api"} [5m])

# Bytes processed
bytes_over_time({job="api"} [1h])
```

### Aggregation Operators

```logql
# Total error rate by service
sum(rate({namespace="prod"} |= "error" [5m])) by (service)

# Top 5 noisiest services
topk(5, sum(rate({namespace="prod"} [5m])) by (service))

# Error ratio
sum(rate({job="api"} |= "error" [5m]))
  / sum(rate({job="api"} [5m]))
```

### `unwrap` Expression

Convert extracted label to a numeric value for aggregation:

```logql
# Average request duration from logs
avg_over_time(
  {job="api"} | json | unwrap duration | __error__="" [5m]
) by (path)
```

Always add `| __error__=""` after `unwrap` to filter out unparseable lines.

## Common Query Patterns

### Error Investigation

```logql
# Recent errors with context
{job="api", level="error"} | json | line_format "{{.timestamp}} {{.msg}}\n{{.stacktrace}}"

# Error count by endpoint
sum(count_over_time({job="api"} | json | level="error" [1h])) by (path)

# Error spike detection
rate({job="api"} |= "error" [5m]) > 10
```

### Access Log Analysis

```logql
# Slow requests from nginx
{job="nginx"} | pattern `<ip> - - [<_>] "<method> <path> <_>" <status> <size> "<_>" "<_>" <duration>`
  | duration > 1.0

# Status code distribution
sum(count_over_time({job="nginx"} | pattern `<_> <_> <_> [<_>] "<_>" <status> <_>` [5m])) by (status)

# Top paths by request count
topk(10, sum(rate({job="nginx"} | pattern `<_> <_> <_> [<_>] "<_> <path> <_>" <_>` [5m])) by (path))
```

### Multi-Service Correlation

```logql
# Find all logs for a specific trace
{namespace="prod"} |= "traceID=abc123def456"

# Find logs around a specific timestamp
{job="api"} | json | timestamp >= "2026-06-18T10:00:00Z" | timestamp <= "2026-06-18T10:05:00Z"
```

## Grafana Query Editor for Loki

### Builder Mode

1. Select labels from dropdowns to build stream selector
2. Add pipeline operations (line filter, parser, label filter)
3. Choose query type: Log query or Metric query
4. Set max lines and query options

### Code Mode

Write raw LogQL with autocomplete for label names and values.

### Query Options

| Option | Purpose |
|--------|---------|
| **Max lines** | Limit returned log lines (default: 1000) |
| **Resolution** | Step interval for metric queries |
| **Type** | Range (logs) or Instant (point-in-time) |
| **Legend** | Format metric query legend |
| **Line limit** | Max bytes per line to display |

## Common Pitfalls

- **Missing stream selector** — Every LogQL query must start with `{...}`; you cannot query without labels
- **Wide selectors** — `{job=~".+"}` scans everything; always be as specific as possible
- **Parser before line filter** — Apply `|= "error"` before `| json` — line filters are much faster
- **Unwrap without error filter** — Always add `| __error__=""` after `unwrap` to skip parse failures
- **High cardinality labels** — Avoid label values with high cardinality (user IDs, request IDs); use line filters instead
- **Rate vs count_over_time** — `rate()` gives per-second rate; `count_over_time()` gives total count over the window
