# Grafana — Provisioning & Configuration as Code

> Source: [grafana.com/docs/grafana/latest/administration/provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/) — Grafana 13.0

## Table of Contents

- [Data Source Provisioning](#data-source-provisioning) — YAML configuration for data sources
- [Dashboard Provisioning](#dashboard-provisioning) — Provider config and JSON files
- [Alerting Provisioning](#alerting-provisioning) — Alert rules, contact points, policies
- [Terraform Provider](#terraform-provider) — HCL-based Grafana resource management
- [GitOps Workflow](#gitops-workflow) — Version-controlled dashboard deployment
- [Common Pitfalls](#common-pitfalls)

## Overview

Provisioning lets you define Grafana resources (data sources, dashboards, alerting rules, contact points, notification policies) as YAML files that are loaded at startup. This enables version control, reproducible environments, and Infrastructure as Code workflows.

## Directory Structure

```
/etc/grafana/provisioning/
├── datasources/
│   └── datasources.yaml
├── dashboards/
│   └── dashboards.yaml        # Provider config (points to JSON files)
├── alerting/
│   ├── alert-rules.yaml
│   └── notifications.yaml
├── plugins/
│   └── plugins.yaml
└── access-control/
    └── roles.yaml              # Enterprise only
```

The provisioning path is configured in `grafana.ini`:
```ini
[paths]
provisioning = /etc/grafana/provisioning
```

## Data Source Provisioning

```yaml
# /etc/grafana/provisioning/datasources/datasources.yaml
apiVersion: 1

deleteDatasources:
  - name: Old Prometheus
    orgId: 1

datasources:
  - name: Prometheus
    type: prometheus
    uid: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
    jsonData:
      timeInterval: "15s"
      httpMethod: POST
      exemplarTraceIdDestinations:
        - name: traceID
          datasourceUid: tempo

  - name: Loki
    type: loki
    uid: loki
    access: proxy
    url: http://loki:3100
    jsonData:
      maxLines: 1000
      derivedFields:
        - datasourceUid: tempo
          matcherRegex: '"traceID":"(\\w+)"'
          name: TraceID
          url: "$${__value.raw}"

  - name: Tempo
    type: tempo
    uid: tempo
    access: proxy
    url: http://tempo:3200
    jsonData:
      tracesToLogsV2:
        datasourceUid: loki
        tags: ["service.name"]
        filterByTraceID: true

  - name: PostgreSQL
    type: postgres
    uid: postgres
    url: db-host:5432
    user: grafana_reader
    secureJsonData:
      password: "$__env{POSTGRES_PASSWORD}"
    jsonData:
      database: production
      sslmode: require
      maxOpenConns: 10
      postgresVersion: 1500
```

### Key Fields

| Field | Required | Purpose |
|-------|----------|---------|
| `name` | Yes | Display name |
| `type` | Yes | Plugin type (prometheus, loki, postgres, etc.) |
| `uid` | No | Stable unique ID for cross-references |
| `url` | Yes | Backend URL |
| `access` | No | `proxy` (default) or `direct` |
| `isDefault` | No | Default data source for new panels |
| `editable` | No | Allow UI edits (false = read-only) |
| `jsonData` | No | Type-specific non-secret config |
| `secureJsonData` | No | Encrypted secrets |

### Environment Variable Substitution

Use `$__env{VAR_NAME}` in provisioning files:

```yaml
secureJsonData:
  password: "$__env{DB_PASSWORD}"
  token: "$__env{API_TOKEN}"
```

## Dashboard Provisioning

Dashboard provisioning has two parts: a provider config (YAML) and the dashboard JSON files.

### Provider Configuration

```yaml
# /etc/grafana/provisioning/dashboards/dashboards.yaml
apiVersion: 1

providers:
  - name: Default
    orgId: 1
    folder: "Provisioned"
    folderUid: provisioned
    type: file
    disableDeletion: false
    editable: true
    updateIntervalSeconds: 30
    allowUiUpdates: false
    options:
      path: /var/lib/grafana/dashboards
      foldersFromFilesStructure: true
```

### Provider Options

| Option | Purpose | Default |
|--------|---------|---------|
| `path` | Directory containing dashboard JSON files | Required |
| `foldersFromFilesStructure` | Create folders matching subdirectory structure | `false` |
| `updateIntervalSeconds` | How often to scan for changes | `10` |
| `disableDeletion` | Prevent deleting provisioned dashboards | `false` |
| `allowUiUpdates` | Allow saving changes via UI | `false` |

### Dashboard JSON Files

Place dashboard JSON files in the configured path:

```
/var/lib/grafana/dashboards/
├── infrastructure/
│   ├── node-exporter.json
│   └── docker.json
├── applications/
│   ├── api-overview.json
│   └── api-errors.json
└── business/
    └── revenue.json
```

With `foldersFromFilesStructure: true`, subdirectories become Grafana folders.

### Exporting Dashboard JSON

```bash
# Via API
curl -s http://localhost:3000/api/dashboards/uid/my-dashboard \
  -H "Authorization: Bearer $TOKEN" | jq '.dashboard' > dashboard.json

# Via UI
# Dashboard → Share → Export → Save to file
```

## Alerting Provisioning

### Alert Rules

```yaml
# /etc/grafana/provisioning/alerting/alert-rules.yaml
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
        for: 5m
        labels:
          severity: critical
          team: platform
        annotations:
          summary: "High error rate on {{ $labels.service }}"
          runbook_url: https://wiki.example.com/runbooks/high-error-rate
        data:
          - refId: A
            relativeTimeRange: { from: 600, to: 0 }
            datasourceUid: prometheus
            model:
              expr: sum(rate(http_requests_total{status=~"5.."}[5m])) by (service)
          - refId: B
            datasourceUid: __expr__
            model:
              type: reduce
              expression: A
              reducer: last
          - refId: C
            datasourceUid: __expr__
            model:
              type: threshold
              expression: B
              conditions:
                - evaluator: { type: gt, params: [10] }
```

### Contact Points and Policies

```yaml
# /etc/grafana/provisioning/alerting/notifications.yaml
apiVersion: 1

contactPoints:
  - orgId: 1
    name: slack-platform
    receivers:
      - uid: slack-platform-1
        type: slack
        settings:
          recipient: "#platform-alerts"
          token: "$__env{SLACK_BOT_TOKEN}"

  - orgId: 1
    name: pagerduty-critical
    receivers:
      - uid: pd-critical-1
        type: pagerduty
        settings:
          integrationKey: "$__env{PAGERDUTY_KEY}"
          severity: critical

policies:
  - orgId: 1
    receiver: slack-platform
    group_by: [alertname]
    group_wait: 30s
    group_interval: 5m
    repeat_interval: 4h
    routes:
      - receiver: pagerduty-critical
        matchers:
          - severity = critical

muteTimes:
  - orgId: 1
    name: weekends
    time_intervals:
      - weekdays: [saturday, sunday]
```

## Terraform Provider

The Grafana Terraform provider manages Grafana resources declaratively.

### Setup

```hcl
terraform {
  required_providers {
    grafana = {
      source  = "grafana/grafana"
      version = "~> 3.0"
    }
  }
}

provider "grafana" {
  url  = "http://localhost:3000"
  auth = var.grafana_api_key
}
```

### Data Source

```hcl
resource "grafana_data_source" "prometheus" {
  type = "prometheus"
  name = "Prometheus"
  uid  = "prometheus"
  url  = "http://prometheus:9090"

  json_data_encoded = jsonencode({
    timeInterval = "15s"
    httpMethod   = "POST"
  })
}
```

### Dashboard

```hcl
resource "grafana_dashboard" "api_overview" {
  folder      = grafana_folder.production.id
  config_json = file("dashboards/api-overview.json")

  depends_on = [grafana_data_source.prometheus]
}

resource "grafana_folder" "production" {
  title = "Production"
  uid   = "production"
}
```

### Alert Rule

```hcl
resource "grafana_rule_group" "api_health" {
  name             = "api-health"
  folder_uid       = grafana_folder.production.uid
  interval_seconds = 60
  org_id           = 1

  rule {
    name      = "High Error Rate"
    condition = "C"
    for       = "5m"

    labels = {
      severity = "critical"
    }

    annotations = {
      summary = "High error rate on {{ $labels.service }}"
    }

    data {
      ref_id         = "A"
      datasource_uid = grafana_data_source.prometheus.uid

      relative_time_range {
        from = 600
        to   = 0
      }

      model = jsonencode({
        expr = "sum(rate(http_requests_total{status=~\"5..\"}[5m])) by (service)"
      })
    }

    data {
      ref_id         = "B"
      datasource_uid = "__expr__"

      relative_time_range {
        from = 600
        to   = 0
      }

      model = jsonencode({
        type       = "reduce"
        expression = "A"
        reducer    = "last"
      })
    }

    data {
      ref_id         = "C"
      datasource_uid = "__expr__"

      relative_time_range {
        from = 600
        to   = 0
      }

      model = jsonencode({
        type       = "threshold"
        expression = "B"
        conditions = [{
          evaluator = { type = "gt", params = [10] }
        }]
      })
    }
  }
}
```

### Contact Point and Policy

```hcl
resource "grafana_contact_point" "slack" {
  name = "platform-slack"

  slack {
    recipient = "#platform-alerts"
    token     = var.slack_token
  }
}

resource "grafana_notification_policy" "default" {
  group_by      = ["alertname"]
  contact_point = grafana_contact_point.slack.name

  policy {
    contact_point = "pagerduty-critical"
    matcher {
      label = "severity"
      match = "="
      value = "critical"
    }
  }
}
```

## GitOps Workflow

```
1. Export dashboards → git repo
2. Edit JSON/YAML in code review
3. Merge to main
4. CI/CD deploys updated provisioning files
5. Grafana auto-loads changes on restart (or via updateInterval)
```

Grafana 13 adds native 2-way Git workflows for GitHub, GitLab, and Bitbucket.

## Common Pitfalls

- **Missing UIDs** — Always set explicit `uid` values; auto-generated UIDs break cross-references between environments
- **Secrets in YAML** — Use `$__env{VAR}` or external secret management; never commit plain secrets
- **editable: false confusion** — Provisioned data sources with `editable: false` cannot be modified via UI, which frustrates users; set `editable: true` during development
- **Dashboard JSON drift** — When `allowUiUpdates: true`, UI changes are lost on restart; commit changes back to git
- **Missing folder** — Dashboard providers require the target folder to exist; use `folderUid` to ensure consistent folder references
- **Terraform state** — Grafana Terraform provider stores dashboard JSON in state; use `config_json = file(...)` to keep state manageable
