# Prometheus — Deployment & Operations

> Source: [prometheus.io/docs/introduction/overview](https://prometheus.io/docs/introduction/overview/)

## Table of Contents

- [Deployment Models](#deployment-models)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Docker Deployment](#docker-deployment)
- [Federation](#federation)
- [High Availability](#high-availability)
- [Scaling Strategies](#scaling-strategies)
- [Security](#security)
- [Monitoring Prometheus](#monitoring-prometheus)

## Deployment Models

### Single Instance

Suitable for small-to-medium environments (up to ~1M active time series):

```yaml
# docker-compose.yml
services:
  prometheus:
    image: prom/prometheus:v3.12.0
    ports: ["9090:9090"]
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./rules/:/etc/prometheus/rules/
      - prometheus-data:/prometheus
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.retention.time=30d"
      - "--storage.tsdb.retention.size=50GB"
      - "--storage.tsdb.wal-compression"
      - "--web.enable-lifecycle"
      - "--enable-feature=memory-snapshot-on-shutdown"

  alertmanager:
    image: prom/alertmanager:v0.28.0
    ports: ["9093:9093"]
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml

  node-exporter:
    image: prom/node-exporter:latest
    ports: ["9100:9100"]
    pid: host
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - "--path.procfs=/host/proc"
      - "--path.sysfs=/host/sys"
      - "--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)"

  grafana:
    image: grafana/grafana-oss:13.0.2
    ports: ["3000:3000"]
    volumes:
      - grafana-data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

volumes:
  prometheus-data:
  grafana-data:
```

### Multi-Instance (HA Pair)

Two identical Prometheus servers scraping the same targets for redundancy:

```yaml
# prometheus-1.yml and prometheus-2.yml (identical config)
global:
  scrape_interval: 15s
  external_labels:
    replica: "prometheus-1"  # Different per instance

scrape_configs:
  - job_name: "app"
    static_configs:
      - targets: ["app:8080"]
```

Both send alerts to the same Alertmanager cluster, which deduplicates:

```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets: ["alertmanager-1:9093", "alertmanager-2:9093"]
```

## Kubernetes Deployment

### Using Prometheus Operator (Recommended)

The Prometheus Operator manages Prometheus instances via Kubernetes CRDs:

```bash
# Install via Helm (kube-prometheus-stack)
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set prometheus.prometheusSpec.retention=30d \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=100Gi
```

### CRD Resources

```yaml
# ServiceMonitor — auto-discover services to scrape
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: my-app
  namespace: monitoring
  labels:
    release: monitoring
spec:
  selector:
    matchLabels:
      app: my-app
  endpoints:
    - port: metrics
      interval: 15s
      path: /metrics

---
# PodMonitor — scrape pods directly
apiVersion: monitoring.coreos.com/v1
kind: PodMonitor
metadata:
  name: my-app-pods
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: my-app
  podMetricsEndpoints:
    - port: metrics
      interval: 15s

---
# PrometheusRule — alerting and recording rules
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: my-app-rules
  namespace: monitoring
  labels:
    release: monitoring
spec:
  groups:
    - name: my-app
      rules:
        - alert: HighErrorRate
          expr: rate(http_errors_total[5m]) > 0.1
          for: 10m
          labels:
            severity: warning
          annotations:
            summary: "High error rate on {{ $labels.instance }}"
```

### Pod Annotations (Without Operator)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    metadata:
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
    spec:
      containers:
        - name: app
          image: my-app:latest
          ports:
            - containerPort: 8080
              name: metrics
```

## Docker Deployment

### Scraping Docker Containers

```yaml
# prometheus.yml with Docker SD
scrape_configs:
  - job_name: "docker"
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 30s
    relabel_configs:
      # Only scrape containers with prometheus.scrape=true label
      - source_labels: [__meta_docker_container_label_prometheus_scrape]
        regex: "true"
        action: keep

      # Use container name as instance
      - source_labels: [__meta_docker_container_name]
        regex: "/(.*)"
        target_label: instance

      # Use custom port label
      - source_labels: [__meta_docker_container_label_prometheus_port]
        regex: (.+)
        target_label: __address__
        replacement: "${1}"
```

### Container Labels

```bash
docker run -d \
  --label prometheus.scrape=true \
  --label prometheus.port=8080 \
  --label prometheus.path=/metrics \
  my-app:latest
```

## Federation

Federation allows a higher-level Prometheus to scrape aggregated metrics from lower-level instances.

### Hierarchical Federation

```
┌─────────────────────┐
│  Global Prometheus   │  (retains aggregated metrics long-term)
│  (centralized)       │
└───────┬─────────────┘
        │  /federate
  ┌─────┴──────┬──────────────┐
  ▼            ▼              ▼
┌──────┐  ┌──────┐    ┌──────────┐
│ Prom │  │ Prom │    │ Prom     │
│ DC-1 │  │ DC-2 │    │ Cloud    │
└──────┘  └──────┘    └──────────┘
```

### Federation Config

```yaml
# On the global Prometheus
scrape_configs:
  - job_name: "federate-dc1"
    scrape_interval: 60s
    honor_labels: true
    metrics_path: "/federate"
    params:
      "match[]":
        - '{job=~".+"}'                    # All job-level metrics
        - 'job:http_requests:rate5m'       # Pre-computed recording rules
    static_configs:
      - targets: ["prometheus-dc1:9090"]
        labels:
          datacenter: "dc1"

  - job_name: "federate-dc2"
    scrape_interval: 60s
    honor_labels: true
    metrics_path: "/federate"
    params:
      "match[]":
        - 'job:http_requests:rate5m'
        - 'instance:node_cpu:usage_rate5m'
    static_configs:
      - targets: ["prometheus-dc2:9090"]
        labels:
          datacenter: "dc2"
```

**Best practice:** Only federate pre-aggregated recording rules, not raw metrics.

## High Availability

### Prometheus HA

Run two identical Prometheus servers scraping the same targets. They operate independently — no leader election or coordination needed.

```yaml
# Both instances have identical scrape configs
# Differentiated only by external_labels
global:
  external_labels:
    replica: "prom-a"  # or "prom-b"
```

Query both via Grafana data source or a load balancer. Alertmanager handles dedup.

### Alertmanager HA

```bash
# Alertmanager cluster (gossip-based dedup)
alertmanager-1 --cluster.peer=alertmanager-2:9094
alertmanager-2 --cluster.peer=alertmanager-1:9094
```

### Long-Term HA with Thanos

```
Prometheus + Thanos Sidecar ──▶ Object Storage (S3/GCS)
                                      │
                                Thanos Query ◀── Thanos Store
                                      │
                                   Grafana
```

Thanos provides:
- Global query view across multiple Prometheus instances
- Deduplication across HA pairs
- Long-term storage in object storage
- Downsampling for efficient historical queries

## Scaling Strategies

| Challenge | Solution |
|-----------|----------|
| Too many targets for one Prometheus | **Functional sharding** — split by team/service |
| High cardinality | Drop unused labels via `metric_relabel_configs` |
| Long retention needed | **Remote write** to Thanos/Mimir/VictoriaMetrics |
| Global view across clusters | **Federation** or **Thanos Query** |
| Query performance | **Recording rules** to pre-compute expensive queries |
| HA for alerting | **Alertmanager cluster** (2-3 instances) |

### Functional Sharding

```yaml
# prometheus-backend.yml — scrapes backend services
scrape_configs:
  - job_name: "api"
    kubernetes_sd_configs: [{role: pod, namespaces: {names: ["backend"]}}]

# prometheus-frontend.yml — scrapes frontend services
scrape_configs:
  - job_name: "web"
    kubernetes_sd_configs: [{role: pod, namespaces: {names: ["frontend"]}}]
```

### Hashmod Sharding

For horizontally scaling across N Prometheus instances:

```yaml
# Instance 0 of 3
relabel_configs:
  - source_labels: [__address__]
    modulus: 3
    target_label: __tmp_hash
    action: hashmod
  - source_labels: [__tmp_hash]
    regex: "0"
    action: keep
```

## Security

### Authentication

```yaml
# web-config.yml (Prometheus)
basic_auth_users:
  admin: $2y$10$...  # bcrypt hash

# Enable with --web.config.file=web-config.yml
```

### TLS

```yaml
# web-config.yml
tls_server_config:
  cert_file: /etc/prometheus/tls/server.crt
  key_file: /etc/prometheus/tls/server.key
  client_auth_type: RequireAndVerifyClientCert
  client_ca_file: /etc/prometheus/tls/ca.crt
```

### Network Security

- Run Prometheus on internal networks only
- Use reverse proxy (nginx/Envoy) for external access
- Disable `--web.enable-admin-api` unless needed
- Disable `--web.enable-lifecycle` in untrusted environments
- Restrict `/federate` access with authentication

## Monitoring Prometheus

Monitor Prometheus itself with these key metrics:

```promql
# Scrape health
up

# Scrape duration
scrape_duration_seconds

# Samples scraped per target
scrape_samples_scraped

# Active time series
prometheus_tsdb_head_series

# Ingestion rate
rate(prometheus_tsdb_head_samples_appended_total[5m])

# Rule evaluation duration
prometheus_rule_group_duration_seconds

# Missed rule evaluations
prometheus_rule_group_iterations_missed_total

# Config reload success
prometheus_config_last_reload_successful

# Storage size
prometheus_tsdb_storage_blocks_bytes

# Query duration
prometheus_engine_query_duration_seconds

# Target health summary
count by (job) (up == 1) / count by (job) (up)
```

### Alerting on Prometheus Health

```yaml
groups:
  - name: prometheus-self-monitoring
    rules:
      - alert: PrometheusTargetDown
        expr: up == 0
        for: 5m
        labels: {severity: critical}
        annotations:
          summary: "{{ $labels.job }}/{{ $labels.instance }} is down"

      - alert: PrometheusConfigReloadFailed
        expr: prometheus_config_last_reload_successful == 0
        for: 5m
        labels: {severity: warning}

      - alert: PrometheusTSDBCompactionsFailing
        expr: increase(prometheus_tsdb_compactions_failed_total[1h]) > 0
        for: 5m
        labels: {severity: warning}

      - alert: PrometheusRuleEvaluationSlow
        expr: prometheus_rule_group_last_duration_seconds > prometheus_rule_group_interval_seconds
        for: 15m
        labels: {severity: warning}
```

## Common Pitfalls

| Pitfall | Impact | Fix |
|---------|--------|-----|
| Single Prometheus, no HA | Data loss on failure | Run HA pair minimum |
| Federation of raw metrics | Overloads global Prometheus | Only federate recording rules |
| No external_labels | Can't distinguish replicas | Always set cluster/replica labels |
| Admin API exposed | Data deletion, config changes | Disable or restrict access |
| No TSDB size monitoring | Disk fills silently | Alert on `prometheus_tsdb_storage_blocks_bytes` |
| Sharding without Thanos | No global query view | Use Thanos Query for cross-shard queries |

## Related Topics

- Configuration reference → `03-configuration.md`
- Recording rules for federation → `07-rules.md`
- Alertmanager HA → `08-alertmanager.md`
- Storage and retention → `09-storage.md`
