# Grafana — Alerting

> Source: [grafana.com/docs/grafana/latest/alerting](https://grafana.com/docs/grafana/latest/alerting/) — Grafana 13.0

## Overview

Grafana Alerting provides a unified alerting system that can evaluate alert rules against any data source. It supports two types of alert rules: Grafana-managed (recommended) and data-source-managed (for Prometheus/Mimir/Loki). Alert rules are organized into evaluation groups and can trigger notifications via contact points and notification policies.

## Alert Rule Types

### Grafana-Managed Alert Rules (Recommended)

- Query any data source (Prometheus, Loki, SQL, CloudWatch, etc.)
- Multi-dimensional alerts from a single rule
- Server-side evaluation
- Support for expressions (reduce, math, threshold, classic condition)
- Stored in Grafana's database

### Data-Source-Managed Alert Rules

- Rules stored and evaluated by the data source itself (Prometheus, Mimir, Loki)
- Written in PromQL or LogQL
- Useful when rules must run even if Grafana is down
- Compatible with Prometheus recording rules

## Creating a Grafana-Managed Alert Rule

### Step 1: Define the Query

```
Query A: Prometheus
  sum(rate(http_requests_total{status=~"5.."}[$__rate_interval])) by (service)
```

### Step 2: Add Expressions

```
Expression B: Reduce
  Function: Last
  Input: A
  Mode: Strict

Expression C: Threshold
  Input: B
  Is Above: 10
```

### Step 3: Set Evaluation Behavior

| Setting | Purpose | Example |
|---------|---------|---------|
| **Folder** | Organize alert rules | `Production Alerts` |
| **Evaluation group** | Group rules with same evaluation interval | `api-checks` |
| **Evaluation interval** | How often the rule is evaluated | `1m` |
| **Pending period** | How long condition must be true before firing | `5m` |

### Step 4: Configure Labels and Annotations

```yaml
labels:
  severity: critical
  team: platform
  service: api

annotations:
  summary: "High error rate on {{ $labels.service }}"
  description: |
    Error rate is {{ $values.B }} errors/sec on service {{ $labels.service }}.
    This exceeds the threshold of 10 errors/sec.
  runbook_url: "https://wiki.example.com/runbooks/high-error-rate"
  dashboard_uid: "api-overview"
  panel_id: "4"
```

## Alert Rule Expressions

### Reduce Expression

Collapse a time series into a single value:

| Function | Description |
|----------|-------------|
| `Last` | Most recent value |
| `Mean` | Average over the evaluation window |
| `Min` | Minimum value |
| `Max` | Maximum value |
| `Sum` | Sum of all values |
| `Count` | Number of data points |

### Math Expression

Perform arithmetic on query/expression results:

```
$B * 100 / $A          # Error percentage
$B - $C                # Difference
$B > 90 ? 1 : 0        # Conditional
```

### Threshold Expression

Compare against a value:

```
Input: B
Condition: Is Above
Value: 10
```

Conditions: `Is Above`, `Is Below`, `Is Within Range`, `Is Outside Range`.

### Classic Condition (Legacy)

Single expression combining query, reducer, and evaluator:

```
WHEN avg() OF query(A, 5m, now) IS ABOVE 80
```

## Alert States

| State | Meaning |
|-------|---------|
| **Normal** | Condition is not met |
| **Pending** | Condition met but pending period not elapsed |
| **Alerting** (Firing) | Condition met and pending period elapsed |
| **No Data** | Query returned no data |
| **Error** | Query evaluation failed |

### No Data and Error Handling

Configure behavior when the query returns no data or errors:

| Option | No Data | Error |
|--------|---------|-------|
| **Alerting** | Treat as firing (default for No Data) | Treat as firing |
| **OK** | Treat as resolved | Treat as resolved |
| **No Data** | Keep No Data state | Keep Error state |
| **Keep Last State** | Maintain previous state | Maintain previous state |

## Multi-Dimensional Alerts

A single rule can fire multiple alert instances — one per label combination:

```promql
# This query returns one series per (service, method) combination
sum(rate(http_requests_total{status=~"5.."}[5m])) by (service, method)
```

Each unique `{service, method}` combination becomes its own alert instance, evaluated independently.

## Evaluation Groups

Rules in the same evaluation group share an evaluation interval and are evaluated sequentially:

```yaml
groups:
  - name: api-health
    interval: 1m
    rules:
      - alert: HighErrorRate
        # ...
      - alert: HighLatency
        # ...

  - name: infrastructure
    interval: 5m
    rules:
      - alert: DiskSpaceLow
        # ...
```

## Recording Rules

Pre-compute expensive queries and store as new time series:

```yaml
groups:
  - name: api_recording_rules
    interval: 30s
    rules:
      - record: api:http_requests:rate5m
        expr: sum(rate(http_requests_total{job="api"}[5m])) by (service)

      - record: api:http_error_ratio
        expr: |
          sum(rate(http_requests_total{job="api", status=~"5.."}[5m])) by (service)
          / sum(rate(http_requests_total{job="api"}[5m])) by (service)
```

Use recording rules in alert rules for faster evaluation:

```promql
# Alert on the pre-computed metric
api:http_error_ratio > 0.05
```

## Provisioning Alert Rules

```yaml
# /etc/grafana/provisioning/alerting/alerts.yaml
apiVersion: 1

groups:
  - orgId: 1
    name: api-health
    folder: Production Alerts
    interval: 1m
    rules:
      - uid: high-error-rate
        title: High Error Rate
        condition: C
        data:
          - refId: A
            relativeTimeRange:
              from: 600
              to: 0
            datasourceUid: prometheus
            model:
              expr: sum(rate(http_requests_total{status=~"5.."}[5m])) by (service)
              instant: false
              range: true
          - refId: B
            relativeTimeRange:
              from: 600
              to: 0
            datasourceUid: __expr__
            model:
              type: reduce
              expression: A
              reducer: last
          - refId: C
            relativeTimeRange:
              from: 600
              to: 0
            datasourceUid: __expr__
            model:
              type: threshold
              expression: B
              conditions:
                - evaluator:
                    type: gt
                    params: [10]
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate on {{ $labels.service }}"
```

## Common Alert Rule Patterns

### High Error Rate

```promql
# Query
sum(rate(http_requests_total{status=~"5.."}[$__rate_interval])) by (service)
  / sum(rate(http_requests_total[$__rate_interval])) by (service) > 0.05

# Fires when > 5% of requests are 5xx errors
```

### High Latency

```promql
histogram_quantile(0.95,
  sum(rate(http_request_duration_seconds_bucket[$__rate_interval])) by (le, service)
) > 2.0
```

### Disk Space Low

```promql
100 * (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) < 10
```

### Pod Crash Looping

```promql
increase(kube_pod_container_status_restarts_total[1h]) > 5
```

### SSL Certificate Expiry

```promql
(probe_ssl_earliest_cert_expiry - time()) / 86400 < 30
```

## Common Pitfalls

- **No pending period** — Set `for: 5m` to avoid alert flapping on brief spikes
- **Alerts without labels** — Always add `severity` and `team` labels for routing
- **Missing annotations** — Include `summary` and `description` with template variables for actionable alerts
- **No Data = Alerting** — Consider using "Keep Last State" for intermittent data sources
- **Too many alert instances** — Multi-dimensional alerts can create hundreds of instances; use recording rules to pre-aggregate
- **Missing runbook_url** — Always link to a runbook in annotations for operational alerts
