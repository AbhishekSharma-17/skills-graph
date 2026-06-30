# Prometheus — Recording and Alerting Rules

> Source: [prometheus.io/docs/prometheus/latest/configuration/recording_rules](https://prometheus.io/docs/prometheus/latest/configuration/recording_rules/)

## Overview

Prometheus supports two types of rules evaluated at regular intervals:

- **Recording rules** — pre-compute expensive expressions and save as new time series
- **Alerting rules** — evaluate conditions and fire alerts to Alertmanager

Both are defined in YAML files referenced by `rule_files` in `prometheus.yml`.

## Rule File Structure

```yaml
groups:
  - name: <group_name>        # Unique within file
    interval: <duration>       # Override global evaluation_interval
    limit: <int>               # Max alerts/series per rule (0 = unlimited)
    query_offset: <duration>   # Offset evaluation into the past
    labels:                    # Labels added to all rules in group
      <labelname>: <labelvalue>
    rules:
      - <recording_rule | alerting_rule>
```

Rules within a group are evaluated **sequentially** — a recording rule defined first can be referenced by later rules in the same group. Groups themselves run concurrently.

## Recording Rules

Pre-compute expensive PromQL expressions and save them as new time series. Querying the pre-computed result is much faster than executing the original expression.

### Syntax

```yaml
rules:
  - record: <metric_name>     # Must be a valid metric name
    expr: <PromQL_expression>
    labels:
      <labelname>: <labelvalue>  # Additional or overriding labels
```

### Naming Convention

Recording rules should follow: `level:metric:operations`

| Component | Meaning | Examples |
|-----------|---------|----------|
| `level` | Aggregation level / labels | `job`, `instance`, `path` |
| `metric` | Original metric name (minus `_total`, `_seconds`) | `http_requests`, `cpu` |
| `operations` | Functions applied, in order | `rate5m`, `sum`, `avg` |

### Examples

```yaml
groups:
  - name: http-recording-rules
    interval: 30s
    rules:
      # Request rate by job and method
      - record: job_method:http_requests:rate5m
        expr: sum by (job, method) (rate(http_requests_total[5m]))

      # Error ratio by job
      - record: job:http_errors:ratio_rate5m
        expr: |
          sum by (job) (rate(http_requests_total{status=~"5.."}[5m]))
          / sum by (job) (rate(http_requests_total[5m]))

      # 99th percentile latency by job
      - record: job:http_request_duration_seconds:p99_rate5m
        expr: |
          histogram_quantile(0.99,
            sum by (job, le) (rate(http_request_duration_seconds_bucket[5m]))
          )

  - name: node-recording-rules
    rules:
      # CPU usage per instance
      - record: instance:node_cpu:usage_rate5m
        expr: |
          1 - avg by (instance) (
            rate(node_cpu_seconds_total{mode="idle"}[5m])
          )

      # Memory usage percentage
      - record: instance:node_memory:usage_ratio
        expr: |
          1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)

      # Disk usage percentage
      - record: instance_mountpoint:node_filesystem:usage_ratio
        expr: |
          1 - (
            node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"}
            / node_filesystem_size_bytes{fstype!~"tmpfs|overlay"}
          )
```

### When to Use Recording Rules

| Scenario | Benefit |
|----------|---------|
| Dashboard queries running every refresh | Avoid re-computing expensive aggregations |
| Cross-job aggregations | Pre-compute once, query cheaply |
| Alerting on complex expressions | Faster alert evaluation |
| Federation | Ship pre-aggregated metrics to central Prometheus |
| SLO calculations | Pre-compute error budgets |

## Alerting Rules

Evaluate PromQL expressions and fire alerts when conditions are met.

### Syntax

```yaml
rules:
  - alert: <alert_name>             # Must be a valid label value
    expr: <PromQL_expression>        # Condition to evaluate
    for: <duration>                  # Wait before firing (default: 0s)
    keep_firing_for: <duration>      # Continue firing after condition clears
    labels:
      <labelname>: <tmpl_string>     # Labels attached to the alert
    annotations:
      <labelname>: <tmpl_string>     # Non-identifying metadata
```

### Key Fields

| Field | Purpose |
|-------|---------|
| `expr` | PromQL expression — alert fires when it returns results |
| `for` | Duration the condition must hold before the alert transitions from `pending` to `firing` |
| `keep_firing_for` | Duration the alert continues firing after the condition resolves (prevents flapping) |
| `labels` | Labels that identify the alert instance; used for routing in Alertmanager |
| `annotations` | Metadata like `summary` and `description`; support Go templating |

### Alert States

```
inactive ──(expr returns results)──▶ pending ──(for duration elapsed)──▶ firing
                                        │                                  │
                                        └──(expr no longer returns)───────▶ inactive
                                                                           │
                                        (with keep_firing_for)─────────────┘
```

### Examples

```yaml
groups:
  - name: availability-alerts
    rules:
      # Instance down for more than 5 minutes
      - alert: InstanceDown
        expr: up == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Instance {{ $labels.instance }} is down"
          description: "{{ $labels.instance }} of job {{ $labels.job }} has been down for more than 5 minutes."

      # High error rate
      - alert: HighErrorRate
        expr: |
          sum by (job) (rate(http_requests_total{status=~"5.."}[5m]))
          / sum by (job) (rate(http_requests_total[5m])) > 0.05
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High error rate for {{ $labels.job }}"
          description: "Error rate is {{ $value | humanizePercentage }} for {{ $labels.job }}."

  - name: resource-alerts
    rules:
      # Disk space prediction — fills in 24 hours
      - alert: DiskWillFillIn24Hours
        expr: |
          predict_linear(
            node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"}[6h], 24*3600
          ) < 0
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "Disk {{ $labels.mountpoint }} on {{ $labels.instance }} predicted full in 24h"

      # High memory usage
      - alert: HighMemoryUsage
        expr: |
          (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) > 0.9
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Memory usage above 90% on {{ $labels.instance }}"
          description: "Current usage: {{ $value | humanizePercentage }}"

      # Too many restarts
      - alert: FrequentRestarts
        expr: changes(process_start_time_seconds[1h]) > 3
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "{{ $labels.job }}/{{ $labels.instance }} restarted {{ $value }} times in the last hour"

  - name: slo-alerts
    rules:
      # SLO burn rate (Multi-window, multi-burn-rate)
      - alert: SLOBurnRateHigh
        expr: |
          (
            job:http_errors:ratio_rate5m{job="api"} > (14.4 * 0.001)
            and
            job:http_errors:ratio_rate1h{job="api"} > (14.4 * 0.001)
          )
        for: 2m
        labels:
          severity: critical
          slo: "api-availability"
        annotations:
          summary: "API error budget burning too fast"
```

### Template Variables

| Variable | Description |
|----------|-------------|
| `$labels` | Label values of the alert instance |
| `$value` | Current evaluation value |
| `$externalLabels` | Global external labels |
| `{{ $labels.instance }}` | Access specific label |
| `{{ $value \| humanize }}` | Format number |
| `{{ $value \| humanizePercentage }}` | Format as percentage |
| `{{ $value \| humanizeDuration }}` | Format as duration |

## Validation

```bash
# Check rule file syntax
promtool check rules /etc/prometheus/rules/*.yml

# Test rules against recorded data
promtool test rules test-rules.yml

# Unit test file format
rule_files:
  - rules.yml
evaluation_interval: 1m
tests:
  - interval: 1m
    input_series:
      - series: 'up{job="api", instance="web-1:8080"}'
        values: "1 1 1 0 0 0 0 0 0 0"
    alert_rule_test:
      - eval_time: 9m
        alertname: InstanceDown
        exp_alerts:
          - exp_labels:
              job: api
              instance: "web-1:8080"
              severity: critical
```

## Performance Considerations

- If rule evaluation exceeds `interval`, the next evaluation is skipped — monitor `rule_group_iterations_missed_total`
- Use `limit` to cap series generated by a single rule
- Recording rules that reference other recording rules must be in the same group (evaluated sequentially)
- Keep recording rule names under the naming convention for discoverability

## Common Pitfalls

| Pitfall | Impact | Fix |
|---------|--------|-----|
| `for: 0s` on flappy metrics | Alert storm | Set `for: 5m` minimum |
| No `for` clause on predictions | False positives | Require sustained prediction |
| Recording rule references across groups | Stale data (group parallel execution) | Put dependent rules in the same group |
| Template syntax errors | Alert silently fails | Validate with `promtool check rules` |
| Too many recording rules | TSDB bloat | Only pre-compute what dashboards/alerts need |

## Related Topics

- PromQL for writing expressions → `04-promql-basics.md`, `06-promql-functions.md`
- Alertmanager routing and notifications → `08-alertmanager.md`
- Configuration and rule_files → `03-configuration.md`
