# Grafana — Data Sources

> Source: [grafana.com/docs/grafana/latest/datasources](https://grafana.com/docs/grafana/latest/datasources/) — Grafana 13.0

## Overview

A data source in Grafana is a connection to a storage backend that holds your data. Grafana ships with built-in support for major backends and supports 170+ additional sources through plugins. Data sources provide custom query editors tailored to each backend's query language.

## Built-in Data Sources

### Metrics & Time Series

| Data Source | Query Language | Use Case |
|-------------|---------------|----------|
| **Prometheus** | PromQL | Cloud-native metrics, Kubernetes monitoring |
| **Graphite** | Graphite query | Legacy metrics systems |
| **InfluxDB** | Flux / InfluxQL | IoT, time series analytics |
| **OpenTSDB** | OpenTSDB query | Large-scale metrics |

### Logs

| Data Source | Query Language | Use Case |
|-------------|---------------|----------|
| **Loki** | LogQL | Cloud-native log aggregation |
| **Elasticsearch** | Lucene / KQL | Full-text search, log analytics |

### Traces

| Data Source | Query Language | Use Case |
|-------------|---------------|----------|
| **Tempo** | TraceQL | Distributed tracing (Grafana stack) |
| **Jaeger** | Jaeger query | Distributed tracing |
| **Zipkin** | Zipkin query | Distributed tracing |

### Profiles

| Data Source | Query Language | Use Case |
|-------------|---------------|----------|
| **Pyroscope** | Pyroscope query | Continuous profiling |
| **Parca** | Parca query | Continuous profiling |

### SQL Databases

| Data Source | Query Language | Use Case |
|-------------|---------------|----------|
| **PostgreSQL** | SQL | Relational data, business metrics |
| **MySQL** | SQL | Relational data |
| **MSSQL** | T-SQL | Microsoft SQL Server |

### Cloud

| Data Source | Query Language | Use Case |
|-------------|---------------|----------|
| **CloudWatch** | CloudWatch query | AWS monitoring |
| **Azure Monitor** | KQL | Azure monitoring |
| **Google Cloud Monitoring** | MQL | GCP monitoring |

### Special

| Data Source | Purpose |
|-------------|---------|
| **Alertmanager** | View and manage Prometheus Alertmanager alerts |
| **TestData** | Generate synthetic data for testing dashboards |
| **Mixed** | Combine queries from multiple data sources in one panel |

## Adding a Data Source

### Via UI

1. Navigate to **Connections** → **Data sources** → **Add data source**
2. Select the data source type
3. Configure connection settings (URL, authentication)
4. Click **Save & test** to verify the connection

### Via Provisioning (YAML)

```yaml
# /etc/grafana/provisioning/datasources/datasources.yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    uid: prometheus
    url: http://prometheus:9090
    access: proxy
    isDefault: true
    jsonData:
      timeInterval: "15s"
      httpMethod: POST

  - name: Loki
    type: loki
    uid: loki
    url: http://loki:3100
    access: proxy
    jsonData:
      derivedFields:
        - datasourceUid: tempo
          matcherRegex: "traceID=(\\w+)"
          name: TraceID
          url: "$${__value.raw}"

  - name: Tempo
    type: tempo
    uid: tempo
    url: http://tempo:3200
    access: proxy

  - name: PostgreSQL
    type: postgres
    uid: postgres
    url: postgres-host:5432
    user: grafana_reader
    secureJsonData:
      password: "$__env{PG_PASSWORD}"
    jsonData:
      database: myapp
      sslmode: require
      maxOpenConns: 10
      maxIdleConns: 5
```

### Via API

```bash
curl -X POST http://localhost:3000/api/datasources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Prometheus",
    "type": "prometheus",
    "url": "http://prometheus:9090",
    "access": "proxy",
    "isDefault": true
  }'
```

## Access Modes

| Mode | How It Works | When to Use |
|------|-------------|-------------|
| **Server (proxy)** | Grafana backend proxies requests | Default, recommended. Data source not exposed to browser |
| **Browser (direct)** | Browser queries data source directly | When Grafana backend cannot reach the data source |

Always prefer **Server (proxy)** — it keeps credentials server-side and avoids CORS issues.

## Key Configuration Fields

```yaml
datasources:
  - name: MySource             # Display name
    type: prometheus            # Plugin type ID
    uid: my-prometheus          # Unique ID for references
    url: http://host:9090       # Backend URL
    access: proxy               # proxy (server) or direct (browser)
    isDefault: true             # Default for new panels
    editable: true              # Allow UI edits
    jsonData:                   # Type-specific config (not secret)
      timeInterval: "15s"
      httpMethod: POST
    secureJsonData:             # Encrypted secrets
      password: secret
      tlsCACert: |
        -----BEGIN CERTIFICATE-----
        ...
```

## Data Source Permissions

Control who can query, edit, or admin each data source:

| Role | Can Query | Can Edit | Can Admin |
|------|-----------|----------|-----------|
| **Viewer** | Yes (if granted) | No | No |
| **Editor** | Yes | Yes (if granted) | No |
| **Admin** | Yes | Yes | Yes |

Restrict data sources to specific teams:
1. Go to **Connections** → **Data sources** → select source → **Permissions**
2. Add users or teams with specific roles

## Correlations

Link related data across data sources for investigation workflows.

### Trace-to-Log

Connect Tempo traces to Loki logs:

```yaml
# In Tempo data source config
jsonData:
  tracesToLogs:
    datasourceUid: loki
    tags: ["service.name", "hostname"]
    filterByTraceID: true
    filterBySpanID: true
```

### Log-to-Trace

Connect Loki logs to Tempo traces via derived fields:

```yaml
# In Loki data source config
jsonData:
  derivedFields:
    - datasourceUid: tempo
      matcherRegex: "traceID=(\\w+)"
      name: TraceID
      url: "$${__value.raw}"
```

### Metric-to-Log

From a Prometheus panel, add a data link to Loki:

```
URL: /explore?left={"datasource":"loki","queries":[{"expr":"{service=\"${__field.labels.service}\"}"}],"range":{"from":"${__from}","to":"${__to}"}}
```

## Mixed Data Source

Query multiple data sources in a single panel:

1. Select **Mixed** as the panel data source
2. Each query (A, B, C) can target a different data source
3. Use transformations to merge/join results

```
Query A: Prometheus → rate(http_requests_total[5m])
Query B: PostgreSQL → SELECT timestamp, revenue FROM sales
Transform: Join by time field
```

## Common Pitfalls

- **Wrong access mode** — Use "Server (proxy)" unless you have a specific reason for direct browser access
- **Missing UID** — Always set explicit UIDs in provisioning; auto-generated UIDs break cross-references
- **Secrets in jsonData** — Use `secureJsonData` for passwords, tokens, and certificates
- **No connection test** — Always click "Save & test" after configuration
- **Stale connections** — Monitor data source health; set query timeouts to prevent hanging panels
- **Mixed source ordering** — When using Mixed, ensure time fields align or use the merge transform
