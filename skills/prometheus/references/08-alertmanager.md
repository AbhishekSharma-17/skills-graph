# Prometheus — Alertmanager

> Source: [prometheus.io/docs/alerting/latest/configuration](https://prometheus.io/docs/alerting/latest/configuration/)

## Table of Contents

- [Architecture](#architecture)
- [Configuration Structure](#configuration-structure)
- [Route Tree](#route-tree)
- [Receivers](#receivers)
- [Inhibition Rules](#inhibition-rules)
- [Silences](#silences)
- [Time Intervals](#time-intervals)
- [Templates](#templates)
- [High Availability](#high-availability)
- [Common Patterns](#common-patterns)

## Architecture

Alertmanager handles alerts sent by Prometheus server instances. It provides:

- **Deduplication** — identical alerts from multiple Prometheus servers are deduplicated
- **Grouping** — related alerts are batched into single notifications
- **Routing** — alerts are directed to the right receiver based on labels
- **Inhibition** — suppressing alerts when related higher-severity alerts are active
- **Silencing** — muting alerts for a specified time window

```
Prometheus ──▶ Alertmanager ──▶ Receivers
                  │
                  ├── Dedup
                  ├── Group
                  ├── Route
                  ├── Inhibit
                  └── Silence
```

### Installation

```bash
# Docker
docker run -d -p 9093:9093 -v ./alertmanager.yml:/etc/alertmanager/alertmanager.yml prom/alertmanager:v0.28.0

# Binary
wget https://github.com/prometheus/alertmanager/releases/download/v0.28.0/alertmanager-0.28.0.linux-amd64.tar.gz
tar xvfz alertmanager-*.tar.gz && cd alertmanager-* && ./alertmanager
```

### Prometheus Configuration

```yaml
# prometheus.yml
alerting:
  alertmanagers:
    - static_configs:
        - targets: ["alertmanager:9093"]
```

## Configuration Structure

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m
  smtp_smarthost: "smtp.example.com:587"
  smtp_from: "alerts@example.com"
  smtp_auth_username: "alerts@example.com"
  smtp_auth_password: "secret"
  slack_api_url: "https://hooks.slack.com/services/T.../B.../xxx"

templates:
  - "/etc/alertmanager/templates/*.tmpl"

route:
  <route_config>

receivers:
  - <receiver_config>

inhibit_rules:
  - <inhibit_rule>

time_intervals:
  - <time_interval>
```

Reload config: send `SIGHUP` or `POST /-/reload`.

Validate: `amtool check-config alertmanager.yml`

## Route Tree

The route tree determines how alerts flow to receivers. Routes are hierarchical — child routes inherit parent settings unless overridden.

```yaml
route:
  # Default receiver
  receiver: "slack-default"

  # Labels to group alerts by
  group_by: ["alertname", "cluster", "service"]

  # Wait before sending first notification for a new group
  group_wait: 30s

  # Wait between notifications for the same group
  group_interval: 5m

  # Wait before re-sending a notification
  repeat_interval: 4h

  # Child routes
  routes:
    # Critical alerts go to PagerDuty
    - matchers:
        - severity = "critical"
      receiver: "pagerduty-critical"
      group_wait: 10s
      repeat_interval: 1h

    # Database alerts to the DBA team
    - matchers:
        - team = "database"
      receiver: "slack-dba"
      routes:
        # Critical DB alerts also page
        - matchers:
            - severity = "critical"
          receiver: "pagerduty-dba"

    # Warning alerts to Slack
    - matchers:
        - severity = "warning"
      receiver: "slack-warnings"
      repeat_interval: 12h

    # Info alerts — low-priority
    - matchers:
        - severity = "info"
      receiver: "slack-info"
      repeat_interval: 24h
      group_by: ["alertname"]
```

### Matching

```yaml
matchers:
  # Exact match
  - severity = "critical"

  # Not equal
  - environment != "test"

  # Regex match
  - service =~ "api|web"

  # Regex non-match
  - alertname !~ "Info.*"
```

### Timing Parameters

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `group_wait` | 30s | Wait to buffer alerts before first notification |
| `group_interval` | 5m | Wait between updates for the same group |
| `repeat_interval` | 4h | Wait before re-sending if nothing changed |
| `continue` | false | If true, keep evaluating sibling routes after match |

### Disable Grouping

```yaml
# Send each alert individually (no batching)
group_by: ['...']
```

## Receivers

### Slack

```yaml
receivers:
  - name: "slack-critical"
    slack_configs:
      - channel: "#alerts-critical"
        title: '{{ .GroupLabels.alertname }}'
        text: |
          {{ range .Alerts }}
          *Alert:* {{ .Annotations.summary }}
          *Instance:* {{ .Labels.instance }}
          *Severity:* {{ .Labels.severity }}
          {{ end }}
        send_resolved: true
```

### Email

```yaml
receivers:
  - name: "email-team"
    email_configs:
      - to: "team@example.com"
        send_resolved: true
        headers:
          Subject: '[{{ .Status | toUpper }}] {{ .GroupLabels.alertname }}'
```

### PagerDuty

```yaml
receivers:
  - name: "pagerduty-critical"
    pagerduty_configs:
      - routing_key: "<integration-key>"
        severity: '{{ if eq .GroupLabels.severity "critical" }}critical{{ else }}warning{{ end }}'
        description: '{{ .CommonAnnotations.summary }}'
```

### Webhook (Generic)

```yaml
receivers:
  - name: "webhook"
    webhook_configs:
      - url: "http://alert-handler:8080/webhook"
        send_resolved: true
        max_alerts: 10
```

### OpsGenie

```yaml
receivers:
  - name: "opsgenie"
    opsgenie_configs:
      - api_key: "<api-key>"
        message: '{{ .GroupLabels.alertname }}: {{ .CommonAnnotations.summary }}'
        priority: '{{ if eq .GroupLabels.severity "critical" }}P1{{ else }}P3{{ end }}'
```

### Discord

```yaml
receivers:
  - name: "discord"
    discord_configs:
      - webhook_url: "https://discord.com/api/webhooks/..."
        title: '{{ .GroupLabels.alertname }}'
        message: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
```

### Telegram

```yaml
receivers:
  - name: "telegram"
    telegram_configs:
      - bot_token: "<bot-token>"
        chat_id: 123456789
        message: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
```

## Inhibition Rules

Suppress alerts when a related higher-severity alert is active:

```yaml
inhibit_rules:
  # Critical inhibits warning for the same alertname+cluster
  - source_matchers:
      - severity = "critical"
    target_matchers:
      - severity = "warning"
    equal: ["alertname", "cluster"]

  # InstanceDown inhibits all other alerts for that instance
  - source_matchers:
      - alertname = "InstanceDown"
    target_matchers:
      - severity =~ "warning|info"
    equal: ["instance"]
```

**How it works:**
- `source_matchers` — the inhibiting (higher-priority) alert
- `target_matchers` — the alert to suppress
- `equal` — labels that must match between source and target

## Silences

Silences mute alerts matching specific criteria for a defined time window. Managed via the Alertmanager web UI (`http://localhost:9093/#/silences`) or `amtool`:

```bash
# Create a silence
amtool silence add alertname="DeploymentInProgress" --duration=2h \
  --comment="Deploying v2.0" --author="deploy-bot"

# List active silences
amtool silence query

# Expire a silence
amtool silence expire <silence-id>
```

## Time Intervals

Define named time periods for muting or activating routes:

```yaml
time_intervals:
  - name: business-hours
    time_intervals:
      - times:
          - start_time: "09:00"
            end_time: "17:00"
        weekdays: ["monday:friday"]
        location: "America/New_York"

  - name: weekends
    time_intervals:
      - weekdays: ["saturday", "sunday"]

  - name: maintenance-window
    time_intervals:
      - times:
          - start_time: "02:00"
            end_time: "04:00"
        weekdays: ["sunday"]
```

Use in routes:

```yaml
route:
  routes:
    - matchers:
        - severity = "warning"
      receiver: "slack-warnings"
      mute_time_intervals: ["weekends", "maintenance-window"]

    - matchers:
        - severity = "critical"
      receiver: "pagerduty-critical"
      active_time_intervals: ["business-hours"]
```

## Templates

Custom notification templates using Go's `text/template`:

```
{{ define "slack.custom.title" -}}
[{{ .Status | toUpper }}{{ if eq .Status "firing" }}:{{ .Alerts.Firing | len }}{{ end }}] {{ .GroupLabels.alertname }}
{{- end }}

{{ define "slack.custom.text" -}}
{{ range .Alerts -}}
*Alert:* {{ .Annotations.summary }}
*Severity:* {{ .Labels.severity }}
*Instance:* {{ .Labels.instance }}
*Description:* {{ .Annotations.description }}
{{ end }}
{{- end }}
```

### Available Template Data

| Field | Description |
|-------|-------------|
| `.Status` | `"firing"` or `"resolved"` |
| `.Alerts` | All alerts in the group |
| `.Alerts.Firing` | Currently firing alerts |
| `.Alerts.Resolved` | Resolved alerts |
| `.GroupLabels` | Labels used for grouping |
| `.CommonLabels` | Labels common to all alerts |
| `.CommonAnnotations` | Annotations common to all alerts |
| `.ExternalURL` | Alertmanager's external URL |

## High Availability

Run multiple Alertmanager instances in a cluster for redundancy:

```bash
# Instance 1
alertmanager --config.file=alertmanager.yml \
  --cluster.listen-address=0.0.0.0:9094 \
  --cluster.peer=alertmanager2:9094

# Instance 2
alertmanager --config.file=alertmanager.yml \
  --cluster.listen-address=0.0.0.0:9094 \
  --cluster.peer=alertmanager1:9094
```

Instances communicate via a gossip protocol to deduplicate notifications. Configure Prometheus to send alerts to all instances:

```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - "alertmanager1:9093"
            - "alertmanager2:9093"
```

## Common Patterns

### Escalation

```yaml
route:
  routes:
    - matchers: [severity="critical"]
      receiver: slack-critical
      continue: true           # Keep evaluating
    - matchers: [severity="critical"]
      receiver: pagerduty
```

### Dead Man's Switch

A continuously-firing alert used to verify the alerting pipeline is working:

```yaml
# Alerting rule (Prometheus)
- alert: DeadMansSwitch
  expr: vector(1)
  labels:
    severity: none
  annotations:
    summary: "Alerting pipeline heartbeat"

# Route to a receiver that expects this alert (e.g., Healthchecks.io)
```

## Common Pitfalls

| Pitfall | Impact | Fix |
|---------|--------|-----|
| No `group_by` | All alerts in one notification | Group by `alertname` + key labels |
| `repeat_interval` too short | Alert fatigue | Set to 4h+ for non-critical |
| Missing `send_resolved: true` | No "resolved" notifications | Enable on critical receivers |
| No inhibition rules | Redundant alerts during outages | Inhibit warnings when critical fires |
| Single Alertmanager | SPOF | Run clustered (2-3 instances) |

## Related Topics

- Alerting rules in Prometheus → `07-rules.md`
- Prometheus configuration for Alertmanager → `03-configuration.md`
- Deployment patterns → `12-deployment.md`
