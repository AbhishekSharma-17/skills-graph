# Grafana — Plugins & HTTP API

> Source: [grafana.com/docs/grafana/latest/developer-resources](https://grafana.com/docs/grafana/latest/developer-resources/) — Grafana 13.0

## Table of Contents

- [Plugins Overview](#plugins-overview) — Types, installation, community plugins, development
- [HTTP API](#http-api) — Authentication, dashboard/folder/data source/alerting/annotation APIs
- [API Patterns](#api-patterns) — CI/CD deployment, annotations automation
- [Common Pitfalls](#common-pitfalls)

## Plugins Overview

Grafana's functionality is extended through three types of plugins:

| Type | Purpose | Examples |
|------|---------|---------|
| **Data source** | Connect to external backends | ClickHouse, MongoDB, Datadog, Snowflake |
| **Panel** | Custom visualizations | Pie chart, Flow chart, Flamegraph, Clock |
| **App** | Bundle multiple features with pages | OnCall, SLO, k6, Incident |

## Installing Plugins

### Via grafana-cli

```bash
# Install a plugin
grafana-cli plugins install grafana-clock-panel

# Install specific version
grafana-cli plugins install grafana-clock-panel 2.1.3

# List installed plugins
grafana-cli plugins ls

# Update a plugin
grafana-cli plugins update grafana-clock-panel

# Remove a plugin
grafana-cli plugins remove grafana-clock-panel
```

### Via Environment Variable

```bash
# Install plugins on container startup
GF_INSTALL_PLUGINS=grafana-clock-panel,grafana-piechart-panel,grafana-worldmap-panel
```

### Via Docker Compose

```yaml
services:
  grafana:
    image: grafana/grafana-oss:13.0.2
    environment:
      - GF_INSTALL_PLUGINS=grafana-clock-panel,grafana-piechart-panel
    volumes:
      - grafana-plugins:/var/lib/grafana/plugins
```

### Via Provisioning

```yaml
# /etc/grafana/provisioning/plugins/plugins.yaml
apiVersion: 1

apps:
  - type: grafana-oncall-app
    org_id: 1
    disabled: false
    jsonData:
      stackId: 1
      orgId: 1
```

## Popular Community Plugins

### Data Sources

| Plugin | Purpose |
|--------|---------|
| `grafana-clickhouse-datasource` | ClickHouse analytics database |
| `grafana-mongodb-datasource` | MongoDB (Enterprise) |
| `grafana-bigquery-datasource` | Google BigQuery |
| `grafana-snowflake-datasource` | Snowflake data warehouse |
| `grafana-athena-datasource` | AWS Athena |
| `redis-datasource` | Redis key-value store |
| `yesoreyeram-infinity-datasource` | JSON, CSV, XML, GraphQL APIs |

### Panels

| Plugin | Purpose |
|--------|---------|
| `grafana-clock-panel` | Clock/countdown display |
| `grafana-piechart-panel` | Pie/donut charts |
| `marcusolsson-treemap-panel` | Treemap visualization |
| `marcusolsson-json-datasource` | JSON API datasource |
| `volkovlabs-form-panel` | Data input forms |
| `volkovlabs-variable-panel` | Enhanced variable selector |

## Plugin Development

### Scaffolding

```bash
# Create a new plugin project
npx @grafana/create-plugin@latest

# Follow prompts:
# - Plugin type: panel | datasource | app
# - Plugin name
# - Organization
```

### Project Structure

```
my-plugin/
├── src/
│   ├── module.ts          # Plugin entry point
│   ├── plugin.json        # Plugin metadata
│   ├── components/        # React components
│   └── types.ts           # TypeScript types
├── package.json
├── docker-compose.yaml    # Dev environment
├── jest.config.ts
└── provisioning/          # Dev provisioning
```

### Development Workflow

```bash
# Start development
npm install
npm run dev

# Start Grafana with the plugin
docker compose up -d

# Run tests
npm run test

# Build for production
npm run build

# Sign the plugin
npx @grafana/sign-plugin@latest
```

---

## HTTP API

Grafana provides a comprehensive REST API for automation, integration, and programmatic management.

### Authentication

#### Service Accounts (Recommended)

```bash
# Create service account via UI:
# Administration → Service accounts → Add service account

# Create token
curl -X POST http://localhost:3000/api/serviceaccounts/1/tokens \
  -H "Authorization: Basic admin:admin" \
  -H "Content-Type: application/json" \
  -d '{"name": "ci-token"}'

# Use token
curl http://localhost:3000/api/dashboards/home \
  -H "Authorization: Bearer <service-account-token>"
```

#### Basic Authentication

```bash
curl http://localhost:3000/api/org \
  -u admin:admin
```

#### API Keys (Legacy — Deprecated)

```bash
# Prefer service accounts instead
curl http://localhost:3000/api/org \
  -H "Authorization: Bearer <api-key>"
```

### Dashboard API

```bash
# Get dashboard by UID
curl http://localhost:3000/api/dashboards/uid/my-dashboard \
  -H "Authorization: Bearer $TOKEN"

# Create or update dashboard
curl -X POST http://localhost:3000/api/dashboards/db \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dashboard": {
      "uid": "my-dashboard",
      "title": "API Dashboard",
      "panels": [],
      "schemaVersion": 39
    },
    "folderUid": "production",
    "overwrite": true,
    "message": "Updated via API"
  }'

# Delete dashboard
curl -X DELETE http://localhost:3000/api/dashboards/uid/my-dashboard \
  -H "Authorization: Bearer $TOKEN"

# Search dashboards
curl "http://localhost:3000/api/search?query=api&type=dash-db&tag=production" \
  -H "Authorization: Bearer $TOKEN"
```

### Folder API

```bash
# Create folder
curl -X POST http://localhost:3000/api/folders \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"uid": "prod", "title": "Production"}'

# List folders
curl http://localhost:3000/api/folders \
  -H "Authorization: Bearer $TOKEN"

# Get folder
curl http://localhost:3000/api/folders/prod \
  -H "Authorization: Bearer $TOKEN"
```

### Data Source API

```bash
# List all data sources
curl http://localhost:3000/api/datasources \
  -H "Authorization: Bearer $TOKEN"

# Get by UID
curl http://localhost:3000/api/datasources/uid/prometheus \
  -H "Authorization: Bearer $TOKEN"

# Create data source
curl -X POST http://localhost:3000/api/datasources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Prometheus",
    "type": "prometheus",
    "url": "http://prometheus:9090",
    "access": "proxy"
  }'

# Test connection
curl -X POST http://localhost:3000/api/datasources/uid/prometheus/health \
  -H "Authorization: Bearer $TOKEN"
```

### Alerting API

```bash
# List alert rules
curl http://localhost:3000/api/v1/provisioning/alert-rules \
  -H "Authorization: Bearer $TOKEN"

# Get alert rule by UID
curl http://localhost:3000/api/v1/provisioning/alert-rules/my-rule-uid \
  -H "Authorization: Bearer $TOKEN"

# List contact points
curl http://localhost:3000/api/v1/provisioning/contact-points \
  -H "Authorization: Bearer $TOKEN"

# Get notification policies
curl http://localhost:3000/api/v1/provisioning/policies \
  -H "Authorization: Bearer $TOKEN"
```

### Organization API

```bash
# Get current org
curl http://localhost:3000/api/org \
  -H "Authorization: Bearer $TOKEN"

# List users in org
curl http://localhost:3000/api/org/users \
  -H "Authorization: Bearer $TOKEN"

# Add user to org
curl -X POST http://localhost:3000/api/org/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"loginOrEmail": "user@example.com", "role": "Viewer"}'
```

### Annotation API

```bash
# Create annotation
curl -X POST http://localhost:3000/api/annotations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dashboardUID": "my-dashboard",
    "time": 1718700000000,
    "text": "Deployed v2.3.1",
    "tags": ["deployment", "api"]
  }'

# Query annotations
curl "http://localhost:3000/api/annotations?from=1718700000000&to=1718703600000&tags=deployment" \
  -H "Authorization: Bearer $TOKEN"
```

### Health Check

```bash
# Grafana health
curl http://localhost:3000/api/health
# Returns: {"commit":"abc123","database":"ok","version":"13.0.2"}
```

## API Patterns

### CI/CD Dashboard Deployment

```bash
#!/bin/bash
GRAFANA_URL="http://localhost:3000"
TOKEN="$GRAFANA_API_TOKEN"

for file in dashboards/*.json; do
  dashboard=$(cat "$file")
  curl -s -X POST "$GRAFANA_URL/api/dashboards/db" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"dashboard\": $dashboard,
      \"folderUid\": \"production\",
      \"overwrite\": true,
      \"message\": \"CI deploy $(date -u +%Y-%m-%dT%H:%M:%SZ)\"
    }"
  echo "Deployed: $(basename "$file")"
done
```

### Deployment Annotations

```bash
# Post annotation after deployment
curl -X POST "$GRAFANA_URL/api/annotations" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"text\": \"Deployed $SERVICE v$VERSION\",
    \"tags\": [\"deployment\", \"$SERVICE\"],
    \"time\": $(date +%s000)
  }"
```

## Common Pitfalls

- **API keys are deprecated** — Use service accounts with tokens instead
- **Missing organization header** — For multi-org setups, include `X-Grafana-Org-Id` header
- **Dashboard versioning** — Always include a `message` field when updating dashboards via API
- **Unsigned plugins** — Custom plugins require signing or setting `allow_loading_unsigned_plugins` in config
- **Plugin compatibility** — Check plugin compatibility with your Grafana version before installing
- **Rate limiting** — Grafana Cloud applies API rate limits; batch operations and cache responses
