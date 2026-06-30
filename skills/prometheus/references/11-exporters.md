# Prometheus — Exporters

> Source: [prometheus.io/docs/instrumenting/writing_exporters](https://prometheus.io/docs/instrumenting/writing_exporters/)

## Table of Contents

- [What Are Exporters](#what-are-exporters)
- [Common Exporters](#common-exporters)
- [Writing Custom Exporters](#writing-custom-exporters)
- [Multi-Target Exporter Pattern](#multi-target-exporter-pattern)
- [Pushgateway](#pushgateway)
- [Common Pitfalls](#common-pitfalls)

## What Are Exporters

Exporters bridge the gap between systems that don't natively expose Prometheus metrics and Prometheus's pull-based collection model. They translate metrics from external systems into Prometheus exposition format.

```
┌─────────────┐     HTTP /metrics      ┌──────────┐
│  Prometheus  │ ────────────────────▶ │ Exporter  │
│  Server      │ ◀──────────────────── │           │
│              │    Prometheus format   │  ┌──────┐ │
└─────────────┘                        │  │Target│ │
                                       │  │System│ │
                                       │  └──────┘ │
                                       └──────────┘
```

## Common Exporters

### Infrastructure

| Exporter | Port | What It Monitors |
|----------|------|------------------|
| **node_exporter** | 9100 | Linux host metrics (CPU, memory, disk, network) |
| **windows_exporter** | 9182 | Windows host metrics |
| **cAdvisor** | 8080 | Container metrics (CPU, memory, I/O per container) |
| **kube-state-metrics** | 8080 | Kubernetes object state (pods, deployments, nodes) |
| **blackbox_exporter** | 9115 | Endpoint probing (HTTP, TCP, DNS, ICMP) |

### Databases

| Exporter | Port | What It Monitors |
|----------|------|------------------|
| **mysqld_exporter** | 9104 | MySQL server metrics |
| **postgres_exporter** | 9187 | PostgreSQL metrics |
| **redis_exporter** | 9121 | Redis server metrics |
| **mongodb_exporter** | 9216 | MongoDB metrics |
| **elasticsearch_exporter** | 9114 | Elasticsearch cluster metrics |

### Message Queues & Services

| Exporter | Port | What It Monitors |
|----------|------|------------------|
| **rabbitmq_exporter** | 9419 | RabbitMQ queues and connections |
| **kafka_exporter** | 9308 | Kafka brokers, topics, consumer groups |
| **nginx_exporter** | 9113 | NGINX connections and requests |
| **haproxy_exporter** | 9101 | HAProxy frontend/backend stats |

### Network & Hardware

| Exporter | Port | What It Monitors |
|----------|------|------------------|
| **snmp_exporter** | 9116 | SNMP-enabled network devices |
| **ipmi_exporter** | 9290 | IPMI hardware sensors |

### Installing node_exporter

```bash
# Docker
docker run -d --name node-exporter \
  --net="host" \
  --pid="host" \
  -v "/:/host:ro,rslave" \
  prom/node-exporter:latest \
  --path.rootfs=/host

# Binary
wget https://github.com/prometheus/node_exporter/releases/download/v1.9.0/node_exporter-1.9.0.linux-amd64.tar.gz
tar xvfz node_exporter-*.tar.gz
cd node_exporter-* && ./node_exporter

# Verify
curl http://localhost:9100/metrics | head
```

### Key node_exporter Metrics

```promql
# CPU usage
1 - avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m]))

# Memory usage
1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)

# Disk usage
1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)

# Network throughput
rate(node_network_receive_bytes_total[5m])
rate(node_network_transmit_bytes_total[5m])

# Load average
node_load1 / count without (cpu, mode) (node_cpu_seconds_total{mode="idle"})
```

## Writing Custom Exporters

### Design Principles

1. **One exporter per application** — deploy alongside the monitored service
2. **Pull on demand** — collect metrics only when Prometheus scrapes, not on a timer
3. **Don't set timestamps** — let Prometheus handle timing
4. **Create new metrics each scrape** — avoid stale label values from previous scrapes
5. **Zero configuration** — aim for sensible defaults without config files

### Python Custom Exporter

```python
from prometheus_client import start_http_server, Gauge, Counter, Info
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY
import time

class MyAppCollector:
    """Custom collector that gathers metrics on each scrape."""

    def collect(self):
        # Gather data from your application
        stats = self._get_app_stats()

        # Yield metric families
        queue_size = GaugeMetricFamily(
            "myapp_queue_size",
            "Current queue depth",
            labels=["queue_name"]
        )
        queue_size.add_metric(["default"], stats["default_queue"])
        queue_size.add_metric(["priority"], stats["priority_queue"])
        yield queue_size

        processed = CounterMetricFamily(
            "myapp_processed_total",
            "Total items processed",
            labels=["status"]
        )
        processed.add_metric(["success"], stats["success_count"])
        processed.add_metric(["failure"], stats["failure_count"])
        yield processed

    def _get_app_stats(self):
        # Query your application for current state
        return {
            "default_queue": 42,
            "priority_queue": 7,
            "success_count": 15000,
            "failure_count": 23,
        }

# Register the collector
REGISTRY.register(MyAppCollector())

# Start HTTP server
start_http_server(9101)
```

### Go Custom Exporter

```go
package main

import (
    "net/http"
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promhttp"
)

type MyCollector struct {
    queueSize *prometheus.Desc
    uptime    *prometheus.Desc
}

func NewMyCollector() *MyCollector {
    return &MyCollector{
        queueSize: prometheus.NewDesc(
            "myapp_queue_size",
            "Current queue depth",
            []string{"queue"}, nil,
        ),
        uptime: prometheus.NewDesc(
            "myapp_uptime_seconds",
            "Application uptime",
            nil, nil,
        ),
    }
}

func (c *MyCollector) Describe(ch chan<- *prometheus.Desc) {
    ch <- c.queueSize
    ch <- c.uptime
}

func (c *MyCollector) Collect(ch chan<- prometheus.Metric) {
    // Gather fresh data each scrape
    ch <- prometheus.MustNewConstMetric(c.queueSize, prometheus.GaugeValue, 42, "default")
    ch <- prometheus.MustNewConstMetric(c.uptime, prometheus.GaugeValue, 3600)
}

func main() {
    prometheus.MustRegister(NewMyCollector())
    http.Handle("/metrics", promhttp.Handler())
    http.ListenAndServe(":9101", nil)
}
```

### Exporter Guidelines

| Guideline | Detail |
|-----------|--------|
| **Metric naming** | Prefix with exporter name: `haproxy_up`, `redis_commands_total` |
| **Naming style** | Convert `camelCase` to `snake_case` |
| **Units** | Use base units (seconds, bytes) — no milliseconds or kilobytes |
| **Reserved suffixes** | Don't use `_sum`, `_count`, `_bucket`, `_total` unless it's that type |
| **Label cardinality** | Keep low — don't put unbounded values in labels |
| **Up metric** | Expose `<exporter>_up` gauge (0/1) for scrape health |
| **Landing page** | Serve HTML at `/` linking to `/metrics` |
| **Scrape duration** | Expose `<exporter>_scrape_duration_seconds` |
| **Failed scrapes** | Return HTTP 5xx or set `up` gauge to 0 |

## Multi-Target Exporter Pattern

For monitoring remote systems where you can't deploy an agent (network devices, external endpoints):

```
Prometheus ──▶ Exporter ──▶ Target A
                  │──▶ Target B
                  └──▶ Target C
```

### Prometheus Config

```yaml
scrape_configs:
  - job_name: "blackbox-http"
    metrics_path: /probe
    params:
      module: [http_2xx]
    static_configs:
      - targets:
          - https://example.com
          - https://api.example.com
          - https://status.example.com
    relabel_configs:
      # Pass the target URL as a parameter
      - source_labels: [__address__]
        target_label: __param_target

      # Set the instance label to the target URL
      - source_labels: [__param_target]
        target_label: instance

      # Point scrape at the exporter itself
      - target_label: __address__
        replacement: blackbox-exporter:9115
```

### Blackbox Exporter Config

```yaml
# blackbox.yml
modules:
  http_2xx:
    prober: http
    timeout: 5s
    http:
      valid_http_versions: ["HTTP/1.1", "HTTP/2.0"]
      valid_status_codes: [200]
      follow_redirects: true
      preferred_ip_protocol: "ip4"

  http_post_2xx:
    prober: http
    http:
      method: POST
      body: '{"test": true}'

  tcp_connect:
    prober: tcp
    timeout: 5s

  icmp:
    prober: icmp
    timeout: 5s

  dns_soa:
    prober: dns
    dns:
      query_name: "example.com"
      query_type: "SOA"
```

### Key Blackbox Metrics

```promql
# Probe success (1 = up, 0 = down)
probe_success

# Probe duration
probe_duration_seconds

# SSL certificate expiry
probe_ssl_earliest_cert_expiry - time()

# HTTP status code
probe_http_status_code

# DNS lookup duration
probe_dns_lookup_time_seconds
```

## Pushgateway

For short-lived batch jobs that can't be scraped:

```bash
# Run Pushgateway
docker run -d -p 9091:9091 prom/pushgateway

# Push metrics via CLI
echo "batch_job_records_processed 1500" | curl --data-binary @- http://pushgateway:9091/metrics/job/etl_nightly

# Push with instance label
cat <<EOF | curl --data-binary @- http://pushgateway:9091/metrics/job/etl_nightly/instance/worker-1
batch_job_duration_seconds 45.2
batch_job_records_processed 1500
batch_job_last_success_timestamp $(date +%s)
EOF

# Delete pushed metrics
curl -X DELETE http://pushgateway:9091/metrics/job/etl_nightly
```

**Scrape config:**

```yaml
scrape_configs:
  - job_name: "pushgateway"
    honor_labels: true      # Preserve job/instance from pushed metrics
    static_configs:
      - targets: ["pushgateway:9091"]
```

**When to use:** Only for batch jobs with defined start/end. Never for long-running services.

## Common Pitfalls

| Pitfall | Impact | Fix |
|---------|--------|-----|
| Persistent metrics in collectors | Stale labels from dead targets | Create new metrics each scrape |
| Setting timestamps on metrics | Breaks staleness detection | Let Prometheus handle timestamps |
| Exporter exposes machine metrics | Duplicates node_exporter | Only export application-specific metrics |
| Pushgateway for long-running services | Stale metrics, no staleness detection | Use pull-based scraping |
| No `up` gauge | Can't detect scrape failures | Always expose `<exporter>_up` |
| Timer-based collection | Metrics may be stale at scrape time | Collect synchronously on scrape |

## Related Topics

- Metric types and naming → `01-data-model.md`, `02-metric-types.md`
- Client library instrumentation → `10-instrumentation.md`
- Configuration for scraping → `03-configuration.md`
- Service discovery → `12-deployment.md`
