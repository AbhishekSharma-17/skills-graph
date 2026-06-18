# Grafana — Dashboards

> Source: [grafana.com/docs/grafana/latest/dashboards](https://grafana.com/docs/grafana/latest/dashboards/) — Grafana 13.0

## Overview

Dashboards are the primary interface in Grafana. A dashboard is a set of panels organized in rows, each panel visualizing data from one or more data sources. Dashboards support variables for interactivity, annotations for event markers, and links for navigation.

## Creating a Dashboard

### From the UI

1. Click **Dashboards** in the left sidebar → **New** → **New Dashboard**
2. Click **Add visualization** to add your first panel
3. Select a data source and write a query
4. Choose a visualization type (time series, stat, gauge, etc.)
5. Configure panel options (title, description, thresholds, legends)
6. Click **Apply** to save the panel
7. Click the **Save** icon (disk) to save the dashboard

### From JSON

```json
{
  "dashboard": {
    "id": null,
    "uid": null,
    "title": "My Dashboard",
    "tags": ["production", "api"],
    "timezone": "browser",
    "schemaVersion": 39,
    "panels": [
      {
        "type": "timeseries",
        "title": "Request Rate",
        "gridPos": { "h": 8, "w": 12, "x": 0, "y": 0 },
        "datasource": { "type": "prometheus", "uid": "prometheus" },
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{path}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "reqps",
            "thresholds": {
              "steps": [
                { "color": "green", "value": null },
                { "color": "red", "value": 1000 }
              ]
            }
          }
        }
      }
    ]
  },
  "overwrite": false
}
```

## Panel Layout

### Grid System

Panels are positioned on a 24-column grid using `gridPos`:

```json
{
  "gridPos": {
    "h": 8,   // height in grid units
    "w": 12,  // width (out of 24 columns)
    "x": 0,   // horizontal position
    "y": 0    // vertical position
  }
}
```

| Layout | Columns | Use Case |
|--------|---------|----------|
| Full width | `w: 24` | Single panel per row (logs, large graphs) |
| Half width | `w: 12` | Two panels side by side |
| Third width | `w: 8` | Three panels per row (stat panels) |
| Quarter width | `w: 6` | Four panels per row (compact stats) |

### Rows

Group panels logically with collapsible rows:

1. Click **Add** → **Row** on the dashboard
2. Drag panels under the row header
3. Click the row title to collapse/expand
4. Rows support repeat-by-variable for dynamic sections

## Dashboard Settings

Access via the gear icon (top right) or **Dashboard settings**:

| Setting | Purpose |
|---------|---------|
| **General** | Title, description, tags, folder, editable flag |
| **Annotations** | Event markers from data sources (deployments, incidents) |
| **Variables** | Template variables for dynamic dashboards |
| **Links** | Navigation links to other dashboards or external URLs |
| **JSON Model** | Raw JSON editor for the dashboard definition |
| **Permissions** | Access control (Viewer, Editor, Admin per user/team) |
| **Versions** | Version history with diff and restore |
| **Time settings** | Time zone, auto-refresh interval, time range picker |

## Annotations

Annotations overlay event markers on time series panels.

### Query-Based Annotations

```yaml
# Example: show deployments from Loki
- name: Deployments
  datasource: Loki
  enable: true
  iconColor: blue
  query: '{app="deployer"} |= "deployed"'
  tagKeys: version,environment
```

### Manual Annotations

1. Hold **Ctrl** (or **Cmd**) and click a point on a time series panel
2. Add a description and tags
3. The annotation appears as a vertical line on all panels sharing the same time range

## Sharing Dashboards

### Export Options

| Method | How | Use Case |
|--------|-----|----------|
| **Share link** | Dashboard → Share → Link | Send to team members with Grafana access |
| **Snapshot** | Dashboard → Share → Snapshot | Public point-in-time view (no live data) |
| **Export JSON** | Dashboard → Share → Export | Backup, version control, migration |
| **Embed** | Dashboard → Share → Embed | IFrame in external pages |
| **PDF Report** | Dashboard → Share → Report | Scheduled email reports (Enterprise) |

### Import Dashboards

1. Click **Dashboards** → **New** → **Import**
2. Paste a dashboard JSON, upload a file, or enter a Grafana.com dashboard ID
3. Map data sources and variables
4. Click **Import**

Popular community dashboards:
- **Node Exporter Full** (ID: 1860) — Linux server metrics
- **Docker and System Monitoring** (ID: 893) — Container metrics
- **Kubernetes Cluster** (ID: 315) — K8s overview
- **NGINX** (ID: 12708) — Web server metrics

## Library Panels

Reusable panels shared across multiple dashboards:

1. Create a panel normally
2. Click panel title → **More** → **Create library panel**
3. Name it and save to a folder
4. On other dashboards: **Add** → **Add a panel from the panel library**

Changes to a library panel propagate to all dashboards using it.

## Dashboard Links

### Dashboard-to-Dashboard

```json
{
  "links": [
    {
      "title": "Service Details",
      "type": "link",
      "url": "/d/service-detail/service-detail?var-service=$service",
      "targetBlank": false
    }
  ]
}
```

### Data Links (Panel-Level)

Add clickable links on data points that pass values to the target:

```
URL: /d/traces/trace-detail?var-traceID=${__data.fields.traceID}
```

Built-in variables for data links:
- `${__data.fields.<name>}` — field value from the clicked row
- `${__value.raw}` — raw value
- `${__from}` / `${__to}` — current time range (epoch ms)
- `${__url.path}` — current dashboard path

## Dashboard JSON Model

Key top-level fields:

| Field | Type | Purpose |
|-------|------|---------|
| `uid` | string | Unique identifier (auto-generated or custom) |
| `title` | string | Dashboard title |
| `tags` | string[] | Filterable tags |
| `panels` | array | Panel definitions |
| `templating.list` | array | Variable definitions |
| `annotations.list` | array | Annotation queries |
| `time` | object | Default time range (`from`, `to`) |
| `timepicker` | object | Refresh intervals |
| `schemaVersion` | number | Dashboard schema version |
| `version` | number | Dashboard version (auto-incremented on save) |

## Folders

Organize dashboards into folders for access control and navigation:

```bash
# Create via API
curl -X POST http://localhost:3000/api/folders \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"uid": "prod-services", "title": "Production Services"}'
```

Folder permissions control who can view/edit dashboards within them.

## Common Pitfalls

- **Dashboard sprawl** — Use folders, tags, and naming conventions (`team-service-aspect`) to stay organized
- **Over-querying** — Set appropriate refresh intervals (10s for real-time, 1m for overview dashboards)
- **No version control** — Export dashboard JSON to Git; use provisioning for critical dashboards
- **Missing time zone** — Set dashboard time zone explicitly rather than relying on browser defaults
- **Broken imports** — When importing, always remap data source UIDs to your local sources
