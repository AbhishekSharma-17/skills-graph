# Grafana — Explore

> Source: [grafana.com/docs/grafana/latest/explore](https://grafana.com/docs/grafana/latest/explore/) — Grafana 13.0

## Overview

Explore is Grafana's ad-hoc query interface for investigation and debugging. Unlike dashboards (optimized for monitoring), Explore is optimized for iterative querying — write a query, see results, refine, correlate across signals. It supports metrics, logs, traces, and profiles side by side.

## Accessing Explore

1. Click **Explore** (compass icon) in the left sidebar
2. Select a data source from the dropdown
3. Write a query in Builder or Code mode
4. Click **Run query** or press **Shift+Enter**

## Key Features

### Split View

Run two queries side by side for correlation:

1. Click the **Split** button in the top-right
2. Each pane has its own data source, query, and time range
3. Sync time ranges with the **Sync** toggle

**Use cases:**
- Compare metrics (Prometheus) alongside logs (Loki)
- View a trace (Tempo) next to its associated logs
- Compare two time periods for the same metric
- Debug by looking at different data sources simultaneously

### Query History

All queries are saved automatically:

1. Click the **Query history** button (clock icon)
2. Browse recent queries with timestamps
3. Star queries to save them permanently
4. Filter by data source
5. Click a query to load it into the editor

### Time Range Controls

| Feature | Description |
|---------|-------------|
| **Absolute time** | Specific date/time range |
| **Relative time** | `Last 1 hour`, `Last 24 hours`, etc. |
| **Shift time** | Move the window backward/forward with arrows |
| **Zoom** | Click and drag on a graph to zoom in |
| **Quick ranges** | Preset ranges in the time picker |
| **Sync** | Synchronize time range across split panes |

### Query Inspector

Click the **Inspector** button to view:

- **Stats** — Query execution time, data points returned, bytes processed
- **Query** — The exact query sent to the data source (useful for debugging)
- **JSON** — Raw response data
- **Data** — Tabular view of returned data
- **Error** — Detailed error messages

## Metrics Exploration

### Prometheus in Explore

```promql
# Rate of HTTP requests
rate(http_requests_total{job="api"}[5m])

# Error ratio
sum(rate(http_requests_total{status=~"5.."}[5m])) by (service)
/ sum(rate(http_requests_total[5m])) by (service)

# P95 latency
histogram_quantile(0.95,
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service))
```

Features in Explore for Prometheus:
- **Metrics browser** — Browse available metrics with label filters
- **Explain** toggle — Step-by-step query breakdown
- **Exemplars** — Click data points linked to trace IDs
- **Table/Graph toggle** — Switch between time series graph and table view

## Logs Exploration

### Loki in Explore

```logql
# Search for errors
{job="api"} |= "error" | json | level="error"

# Count errors per service
sum(count_over_time({namespace="prod"} |= "error" [5m])) by (service)
```

### Log Features in Explore

| Feature | Description |
|---------|-------------|
| **Log volume** | Bar chart showing log line distribution over time |
| **Log details** | Click a log line to expand and see all labels/fields |
| **Log context** | View surrounding log lines (before/after) |
| **Live tail** | Stream logs in real-time (like `tail -f`) |
| **Detected fields** | Auto-parsed fields shown as filterable columns |
| **Dedup** | Remove duplicate log lines (exact, numbers, signature) |
| **Wrap lines** | Toggle line wrapping for long log lines |
| **Prettify JSON** | Auto-format JSON log content |

### Live Tail

Stream logs in real-time:

1. Write your Loki query
2. Click the **Live** button (play icon) in the time picker
3. Logs stream in real-time
4. Click **Pause** to freeze the stream and inspect
5. Click **Stop** to exit live tail mode

## Traces Exploration

### Tempo in Explore

```
# Search by service and operation
service.name = "api" && name = "GET /users"

# Search by duration
duration > 2s

# Search by status
status = error
```

### Trace Features

| Feature | Description |
|---------|-------------|
| **Trace view** | Flame graph / waterfall view of spans |
| **Span details** | Click a span to see attributes, events, links |
| **Service map** | Visual dependency graph of services |
| **Trace-to-logs** | Jump from a span to associated log lines |
| **Trace-to-metrics** | Jump from a trace to related metrics |
| **Span filters** | Filter spans by service, operation, duration, status |

### Trace-to-Logs Correlation

From a trace span, click the **Logs** icon to jump to Loki with pre-filled filters:

```logql
{service="api", traceID="abc123def456"}
```

This requires configuring the Tempo data source with `tracesToLogs` settings.

## Profiles Exploration

### Pyroscope in Explore

View flame graphs of CPU, memory, and other profiles:

- **Single profile** — View one profile snapshot
- **Diff view** — Compare two profiles side by side
- **Timeline** — Profile data over time

## Explore to Dashboard

Convert an Explore query into a dashboard panel:

1. Run your query in Explore
2. Click the **Add to dashboard** button (top right)
3. Choose: **Open in new dashboard** or **Add to existing dashboard**
4. Select visualization type and configure panel options
5. Save the dashboard

## Correlations

Link data across data sources for seamless investigation:

### Setting Up Correlations

1. Go to **Connections** → **Correlations**
2. Click **Add correlation**
3. Define source (where the link appears) and target (where it goes)
4. Map fields: which field values pass to the target query

### Example: Logs → Traces

```
Source: Loki results
Target: Tempo
Field mapping: traceID → traceID
Link label: "View Trace"
```

When viewing Loki logs in Explore, each line with a `traceID` field gets a clickable link to the corresponding trace in Tempo.

### Example: Metrics → Logs

```
Source: Prometheus results
Target: Loki
Field mapping: service → {service="$value"}
Link label: "View Logs"
```

## Query Patterns for Investigation

### Incident Response Workflow

```
1. Start with metrics (Prometheus) to identify the problem
   rate(http_requests_total{status=~"5.."}[5m])

2. Split view → add logs (Loki) to find root cause
   {service="api"} |= "error" | json

3. Find a trace ID in the logs → click to view trace (Tempo)
   Trace shows slow database span

4. Jump to database metrics to confirm
   rate(pg_stat_activity_count{state="active"}[5m])
```

### Comparing Time Periods

```
1. Run query for current period
2. Click Split to open second pane
3. In the second pane, shift time range back (e.g., 24h ago)
4. Compare the two graphs visually
```

### Discovering Metrics

```
1. Open Explore with Prometheus
2. Use the Metrics browser to browse available metrics
3. Filter by job, instance, or keyword
4. Click a metric to load it into the query editor
5. Add rate(), sum(), or other functions as needed
```

## Common Pitfalls

- **Not using Split view** — Correlating metrics and logs side by side is the core value of Explore
- **Ignoring Query history** — Star useful queries instead of rewriting them
- **Missing correlations** — Set up trace-to-log and log-to-trace links for seamless investigation
- **Live tail without filters** — Always use a specific stream selector; live-tailing broad queries overloads the browser
- **Explore vs Dashboards** — Use Explore for investigation, dashboards for monitoring; don't build dashboards in Explore
- **Forgetting Query inspector** — When a query is slow or returns unexpected results, check the inspector for details
