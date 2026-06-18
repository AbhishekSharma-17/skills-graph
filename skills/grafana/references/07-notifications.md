# Grafana — Notifications

> Source: [grafana.com/docs/grafana/latest/alerting/configure-notifications](https://grafana.com/docs/grafana/latest/alerting/configure-notifications/) — Grafana 13.0

## Table of Contents

- [Contact Points](#contact-points) — Integrations (Slack, PagerDuty, webhook, email)
- [Notification Policies](#notification-policies) — Routing rules, label matchers, grouping
- [Silences](#silences) — One-time notification suppression
- [Mute Timings](#mute-timings) — Recurring suppression windows
- [Notification Templates](#notification-templates) — Custom message formatting
- [Provisioning Notifications](#provisioning-notifications) — YAML-based configuration
- [Common Pitfalls](#common-pitfalls)

## Overview

Grafana's notification system determines how, when, and where alert notifications are delivered. It consists of three components: contact points (where to send), notification policies (routing rules), and silences/mute timings (suppression). Templates customize the message content.

## Contact Points

A contact point is a list of integrations that receive alert notifications.

### Supported Integrations

| Integration | Type | Use Case |
|-------------|------|----------|
| **Email** | Built-in | Team/individual email alerts |
| **Slack** | Built-in | Channel notifications with rich formatting |
| **PagerDuty** | Built-in | Incident management, on-call escalation |
| **Webhook** | Built-in | Custom HTTP endpoints |
| **OpsGenie** | Built-in | Alert management, on-call routing |
| **Microsoft Teams** | Built-in | Channel notifications |
| **Discord** | Built-in | Community/team alerts |
| **Telegram** | Built-in | Chat notifications |
| **Google Chat** | Built-in | Workspace notifications |
| **Amazon SNS** | Built-in | AWS event notifications |
| **Alertmanager** | Built-in | Forward to external Alertmanager |
| **Kafka** | Built-in | Stream alerts to Kafka topics |
| **LINE** | Built-in | Mobile messaging |
| **OnCall** | Plugin | Grafana OnCall integration |

### Creating a Contact Point

**Via UI:**

1. Go to **Alerting** → **Contact points** → **Add contact point**
2. Name the contact point (e.g., `platform-team-slack`)
3. Select integration type (e.g., Slack)
4. Configure integration-specific settings
5. Optionally add multiple integrations (all receive notifications)
6. Click **Save**

### Slack Configuration

```yaml
name: platform-slack
type: slack
settings:
  recipient: "#platform-alerts"
  token: xoxb-...
  username: Grafana Alerts
  icon_emoji: ":alert:"
  mentionUsers: "U12345,U67890"
  mentionGroups: "S12345"
  text: |
    {{ len .Alerts.Firing }} firing, {{ len .Alerts.Resolved }} resolved
```

### Webhook Configuration

```yaml
name: custom-webhook
type: webhook
settings:
  url: https://api.example.com/alerts
  httpMethod: POST
  username: grafana
  password: secret
  maxAlerts: 10
```

Webhook payload (JSON):
```json
{
  "receiver": "custom-webhook",
  "status": "firing",
  "alerts": [
    {
      "status": "firing",
      "labels": { "alertname": "HighErrorRate", "severity": "critical" },
      "annotations": { "summary": "Error rate above threshold" },
      "startsAt": "2026-06-18T10:00:00Z",
      "endsAt": "0001-01-01T00:00:00Z",
      "fingerprint": "abc123"
    }
  ],
  "groupLabels": { "alertname": "HighErrorRate" },
  "commonLabels": { "severity": "critical" },
  "externalURL": "https://grafana.example.com"
}
```

### PagerDuty Configuration

```yaml
name: pagerduty-critical
type: pagerduty
settings:
  integrationKey: abc123def456
  severity: critical
  class: infrastructure
  component: api
  group: production
```

### Email Configuration

```yaml
name: team-email
type: email
settings:
  addresses: "team@example.com;oncall@example.com"
  singleEmail: true
  message: |
    {{ len .Alerts.Firing }} alert(s) firing.
    {{ range .Alerts.Firing }}
    - {{ .Labels.alertname }}: {{ .Annotations.summary }}
    {{ end }}
```

## Notification Policies

Notification policies route alerts to contact points based on label matchers. They form a tree structure with a default (root) policy.

### Policy Tree

```
Root Policy (catch-all → default-email)
├── severity=critical → pagerduty-critical
│   └── team=platform → platform-slack + pagerduty-critical
├── severity=warning → team-slack
├── team=data → data-team-email
└── alertname=Watchdog → /dev/null (no contact point)
```

### Creating a Notification Policy

**Via UI:**

1. Go to **Alerting** → **Notification policies**
2. Click **New nested policy** on the default policy
3. Add label matchers: `severity = critical`
4. Select contact point: `pagerduty-critical`
5. Configure grouping and timing
6. Click **Save**

### Label Matchers

| Operator | Meaning | Example |
|----------|---------|---------|
| `=` | Exact match | `severity = critical` |
| `!=` | Not equal | `environment != test` |
| `=~` | Regex match | `team =~ "platform\|infra"` |
| `!~` | Regex not match | `alertname !~ "Info.*"` |

### Grouping

Group multiple alert instances into a single notification:

| Setting | Purpose | Example |
|---------|---------|---------|
| **Group by** | Labels to group alerts | `alertname, service` |
| **Group wait** | Wait before sending first notification | `30s` |
| **Group interval** | Wait between updates to a group | `5m` |
| **Repeat interval** | Wait before re-sending if nothing changes | `4h` |

```yaml
# Example: group by alertname, wait 30s, update every 5m, repeat every 4h
group_by: [alertname, service]
group_wait: 30s
group_interval: 5m
repeat_interval: 4h
```

### Continue Matching

By default, an alert stops at the first matching policy. Enable **Continue matching** to send to multiple contact points:

```
severity=critical → pagerduty (continue: true)
severity=critical → slack-critical (continue: false)
```

## Silences

Suppress notifications for a defined time period without stopping alert evaluation.

### Creating a Silence

1. Go to **Alerting** → **Silences** → **Add silence**
2. Set duration (start time, end time)
3. Add label matchers to select which alerts to silence
4. Add a comment explaining why
5. Click **Save**

### Use Cases

- **Maintenance windows** — Silence `instance="server-42"` during planned downtime
- **Known issues** — Silence a specific alert while investigating
- **Deployments** — Silence alerts during rolling deployments

### Via API

```bash
curl -X POST http://localhost:3000/api/alertmanager/grafana/api/v2/silences \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "matchers": [
      { "name": "alertname", "value": "HighErrorRate", "isRegex": false }
    ],
    "startsAt": "2026-06-18T10:00:00Z",
    "endsAt": "2026-06-18T12:00:00Z",
    "createdBy": "admin",
    "comment": "Planned deployment"
  }'
```

## Mute Timings

Recurring time windows when notifications are suppressed (e.g., weekends, off-hours).

### Creating a Mute Timing

```yaml
# Provisioning
muteTimes:
  - name: weekends
    time_intervals:
      - weekdays: ["saturday", "sunday"]

  - name: off-hours
    time_intervals:
      - weekdays: ["monday:friday"]
        times:
          - start_time: "00:00"
            end_time: "08:00"
          - start_time: "18:00"
            end_time: "24:00"

  - name: maintenance-window
    time_intervals:
      - weekdays: ["wednesday"]
        times:
          - start_time: "02:00"
            end_time: "04:00"
```

Attach mute timings to notification policies to suppress notifications during those windows.

## Notification Templates

Customize the message content sent by contact points.

### Template Syntax (Go templates)

```go
{{ define "custom.title" }}
[{{ .Status | toUpper }}] {{ .GroupLabels.alertname }}
{{ end }}

{{ define "custom.message" }}
{{ if .Alerts.Firing }}
🔥 *Firing:*
{{ range .Alerts.Firing }}
• *{{ .Labels.alertname }}* on `{{ .Labels.instance }}`
  {{ .Annotations.summary }}
  Since: {{ .StartsAt.Format "2006-01-02 15:04:05" }}
{{ end }}
{{ end }}

{{ if .Alerts.Resolved }}
✅ *Resolved:*
{{ range .Alerts.Resolved }}
• *{{ .Labels.alertname }}* on `{{ .Labels.instance }}`
{{ end }}
{{ end }}
{{ end }}
```

### Available Template Data

| Field | Type | Description |
|-------|------|-------------|
| `.Status` | string | `"firing"` or `"resolved"` |
| `.Alerts` | list | All alerts in the group |
| `.Alerts.Firing` | list | Currently firing alerts |
| `.Alerts.Resolved` | list | Recently resolved alerts |
| `.GroupLabels` | map | Labels used for grouping |
| `.CommonLabels` | map | Labels shared by all alerts |
| `.CommonAnnotations` | map | Annotations shared by all alerts |
| `.ExternalURL` | string | Grafana URL |
| `.Receiver` | string | Contact point name |

### Per-Alert Fields

| Field | Description |
|-------|-------------|
| `.Labels` | All labels on the alert |
| `.Annotations` | All annotations |
| `.StartsAt` | Time alert started firing |
| `.EndsAt` | Time alert resolved |
| `.Fingerprint` | Unique alert identifier |
| `.GeneratorURL` | Link to the alert rule |
| `.SilenceURL` | Link to create a silence |
| `.DashboardURL` | Link to associated dashboard |
| `.PanelURL` | Link to associated panel |
| `.Values` | Map of expression values |

## Provisioning Notifications

```yaml
# /etc/grafana/provisioning/alerting/notifications.yaml
apiVersion: 1

contactPoints:
  - orgId: 1
    name: platform-slack
    receivers:
      - uid: slack-1
        type: slack
        settings:
          recipient: "#platform-alerts"
          token: "$__env{SLACK_TOKEN}"

policies:
  - orgId: 1
    receiver: default-email
    group_by: [alertname]
    group_wait: 30s
    group_interval: 5m
    repeat_interval: 4h
    routes:
      - receiver: platform-slack
        matchers:
          - severity = critical
        continue: false

muteTimes:
  - orgId: 1
    name: weekends
    time_intervals:
      - weekdays: [saturday, sunday]
```

## Common Pitfalls

- **No default contact point** — The root notification policy must have a contact point; unmatched alerts go there
- **Missing group_by** — Without grouping, each alert instance triggers a separate notification
- **Short repeat_interval** — Setting `repeat_interval` too low causes notification fatigue
- **Silences vs mute timings** — Use silences for one-off suppression, mute timings for recurring windows
- **Template errors** — Test templates in **Alerting → Contact points → Test** before deploying
- **Continue flag** — Without `continue: true`, alerts stop at the first matching policy
