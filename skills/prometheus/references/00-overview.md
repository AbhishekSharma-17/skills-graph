# Prometheus — Overview & Architecture

> Source: [prometheus.io/docs/introduction/overview](https://prometheus.io/docs/introduction/overview/)

## What Is Prometheus

Prometheus is an open-source systems monitoring and alerting toolkit originally built at SoundCloud in 2012. It joined the Cloud Native Computing Foundation (CNCF) in 2016 as the second hosted project after Kubernetes and graduated in 2018. Prometheus has become the de facto standard for metrics-based monitoring in cloud-native environments.

## Key Features

- **Multi-dimensional data model** — time series identified by metric name and key-value label pairs
- **PromQL** — flexible query language for slicing and aggregating dimensional data
- **No distributed storage dependency** — single server nodes are autonomous
- **Pull-based collection** — scrapes metrics over HTTP at configured intervals
- **Push support** — via an intermediary pushgateway for short-lived jobs
- **Service discovery** — targets found via Kubernetes, Consul, DNS, file-based configs, or static lists
- **Multiple visualization modes** — built-in expression browser, Grafana integration, console templates
- **Alerting** — rules evaluated on the server, notifications managed by Alertmanager

## Architecture

```
┌──────────────┐     ┌──────────────────┐     ┌────────────────┐
│  Prometheus   │────▶│  Alertmanager     │────▶│  PagerDuty /   │
│  Server       │     │  (dedup, group,   │     │  Slack / Email │
│               │     │   route, silence) │     └────────────────┘
│  ┌──────────┐ │     └──────────────────┘
│  │ TSDB     │ │
│  │ (storage)│ │     ┌──────────────────┐
│  └──────────┘ │────▶│  Grafana /        │
│  ┌──────────┐ │     │  Web UI           │
│  │ PromQL   │ │     └──────────────────┘
│  │ engine   │ │
│  └──────────┘ │
└───────┬───────┘
        │ HTTP scrape (pull)
        │
┌───────┴───────────────────────────────────┐
│                                           │
▼               ▼               ▼           ▼
┌─────────┐ ┌─────────┐ ┌──────────┐ ┌───────────┐
│ App with │ │ Node    │ │ Exporter │ │ Pushgateway│
│ /metrics │ │ Exporter│ │ (MySQL,  │ │ (short-   │
│ endpoint │ │         │ │  Redis)  │ │  lived    │
└─────────┘ └─────────┘ └──────────┘ │  jobs)    │
                                      └───────────┘
```

### Core Components

| Component | Purpose |
|-----------|---------|
| **Prometheus Server** | Scrapes and stores time series data, evaluates rules, fires alerts |
| **Client Libraries** | Instrument application code (Go, Java, Python, Ruby, Rust) |
| **Pushgateway** | Accepts metrics pushed by short-lived batch jobs |
| **Exporters** | Bridge metrics from third-party systems (node, MySQL, Redis, etc.) |
| **Alertmanager** | Deduplicates, groups, routes, and silences alert notifications |
| **promtool** | CLI for validating configs, rules, and querying Prometheus |

## When to Use Prometheus

**Good fit:**
- Machine-centric and microservice monitoring
- Numeric time series data (counters, gauges, histograms)
- Multi-dimensional data with flexible querying
- Environments where reliability matters more than 100% accuracy
- Kubernetes and cloud-native workloads

**Not ideal for:**
- Per-request billing or scenarios requiring 100% accuracy
- Event logging or distributed tracing (use Loki, Jaeger, Tempo)
- Long-term storage beyond weeks (use Thanos, Cortex, Mimir, or remote write)

## Quick Start

### Minimal Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]
```

### Run with Docker

```bash
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus:v3.12.0
```

### Run from Binary

```bash
# Download and extract
curl -LO https://github.com/prometheus/prometheus/releases/download/v3.12.0/prometheus-3.12.0.linux-amd64.tar.gz
tar xvfz prometheus-*.tar.gz
cd prometheus-*

# Start
./prometheus --config.file=prometheus.yml

# Verify
curl http://localhost:9090/-/healthy
```

### Docker Compose with Node Exporter

```yaml
services:
  prometheus:
    image: prom/prometheus:v3.12.0
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.retention.time=30d"

  node-exporter:
    image: prom/node-exporter:latest
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - "--path.procfs=/host/proc"
      - "--path.sysfs=/host/sys"
      - "--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)"

volumes:
  prometheus-data:
```

Update `prometheus.yml` to scrape the node exporter:

```yaml
scrape_configs:
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]

  - job_name: "node"
    static_configs:
      - targets: ["node-exporter:9100"]
```

## Key URLs

| Resource | URL |
|----------|-----|
| Expression browser | `http://localhost:9090/graph` |
| Targets page | `http://localhost:9090/targets` |
| Config page | `http://localhost:9090/config` |
| Rules page | `http://localhost:9090/rules` |
| Alerts page | `http://localhost:9090/alerts` |
| Health check | `http://localhost:9090/-/healthy` |
| Readiness | `http://localhost:9090/-/ready` |
| Reload config | `POST http://localhost:9090/-/reload` |
| TSDB status | `http://localhost:9090/tsdb-status` |

## CLI — promtool

```bash
# Validate configuration
promtool check config prometheus.yml

# Validate rules
promtool check rules rules.yml

# Test rules against data
promtool test rules test.yml

# Query Prometheus from CLI
promtool query instant http://localhost:9090 'up'
promtool query range http://localhost:9090 'rate(http_requests_total[5m])' --start=1h

# Create TSDB blocks from OpenMetrics data
promtool tsdb create-blocks-from openmetrics input.txt

# TSDB analysis
promtool tsdb analyze ./data
```

## Related Topics

- Data model and metric naming → `01-data-model.md`
- Metric types (Counter, Gauge, Histogram) → `02-metric-types.md`
- Configuration reference → `03-configuration.md`
- PromQL query language → `04-promql-basics.md`
- Alerting pipeline → `07-rules.md`, `08-alertmanager.md`
- Grafana integration → Grafana skill
