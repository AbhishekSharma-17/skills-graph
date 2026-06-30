# Prometheus — Configuration

> Source: [prometheus.io/docs/prometheus/latest/configuration](https://prometheus.io/docs/prometheus/latest/configuration/configuration/)

## Configuration File

Prometheus configuration is written in YAML and loaded at startup via `--config.file`. Reload without restart by sending `SIGHUP` or `POST /-/reload` (requires `--web.enable-lifecycle`).

```bash
# Validate before applying
promtool check config prometheus.yml

# Reload running server
kill -HUP $(pidof prometheus)
# or
curl -X POST http://localhost:9090/-/reload
```

## Global Settings

```yaml
global:
  # How often to scrape targets (default: 1m)
  scrape_interval: 15s

  # How often to evaluate recording/alerting rules (default: 1m)
  evaluation_interval: 15s

  # Timeout for individual scrape requests (default: 10s)
  scrape_timeout: 10s

  # Labels added to all time series and alerts sent to external systems
  external_labels:
    cluster: "production"
    region: "us-east-1"

  # Per-scrape limit on accepted samples (0 = no limit)
  sample_limit: 0

  # Per-scrape limit on label count per sample
  label_limit: 0

  # Per-scrape limit on label name length
  label_name_length_limit: 0

  # Per-scrape limit on label value length
  label_value_length_limit: 0

  # Per-target limit on time series created
  target_limit: 0
```

## Scrape Configuration

Each `scrape_config` defines a set of targets and how to scrape them:

```yaml
scrape_configs:
  - job_name: "my-app"

    # Override global scrape interval for this job
    scrape_interval: 10s
    scrape_timeout: 5s

    # HTTP path and scheme
    metrics_path: /metrics
    scheme: https

    # Basic auth
    basic_auth:
      username: prometheus
      password: secret

    # Bearer token
    bearer_token_file: /etc/prometheus/token

    # TLS configuration
    tls_config:
      ca_file: /etc/prometheus/ca.pem
      cert_file: /etc/prometheus/cert.pem
      key_file: /etc/prometheus/key.pem
      insecure_skip_verify: false

    # Static target list
    static_configs:
      - targets:
          - "app1:8080"
          - "app2:8080"
        labels:
          environment: "production"
          team: "backend"

    # Relabeling — applied before scrape
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance

    # Metric relabeling — applied after scrape
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: "go_.*"
        action: drop
```

## Service Discovery

Prometheus supports multiple service discovery mechanisms to find scrape targets dynamically.

### File-Based SD

Watches JSON or YAML files for target changes — simplest dynamic discovery:

```yaml
scrape_configs:
  - job_name: "file-sd"
    file_sd_configs:
      - files:
          - "/etc/prometheus/targets/*.json"
        refresh_interval: 30s
```

Target file format:

```json
[
  {
    "targets": ["host1:9090", "host2:9090"],
    "labels": {
      "env": "production",
      "team": "platform"
    }
  }
]
```

### Kubernetes SD

```yaml
scrape_configs:
  - job_name: "kubernetes-pods"
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names: ["default", "monitoring"]

    relabel_configs:
      # Only scrape pods with annotation prometheus.io/scrape=true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: "true"

      # Use annotation for custom metrics path
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)

      # Use annotation for custom port
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__

      # Copy pod name and namespace as labels
      - source_labels: [__meta_kubernetes_pod_name]
        target_label: pod
      - source_labels: [__meta_kubernetes_namespace]
        target_label: namespace
```

Kubernetes SD roles:

| Role | Discovers | Key Meta Labels |
|------|-----------|-----------------|
| `node` | Cluster nodes | `__meta_kubernetes_node_name`, `_label_*` |
| `pod` | All pods | `__meta_kubernetes_pod_name`, `_namespace`, `_annotation_*` |
| `service` | Services | `__meta_kubernetes_service_name`, `_port_name` |
| `endpoints` | Endpoint targets | `__meta_kubernetes_endpoint_*`, pod/service labels |
| `endpointslice` | EndpointSlice targets | Same as endpoints, preferred in newer K8s |
| `ingress` | Ingress rules | `__meta_kubernetes_ingress_name`, `_host`, `_path` |

### Consul SD

```yaml
scrape_configs:
  - job_name: "consul"
    consul_sd_configs:
      - server: "consul.example.com:8500"
        services: ["web", "api"]
        tags: ["production"]
```

### DNS SD

```yaml
scrape_configs:
  - job_name: "dns-sd"
    dns_sd_configs:
      - names: ["_prometheus._tcp.example.com"]
        type: SRV
        refresh_interval: 30s
```

### Other SD Mechanisms

| Mechanism | Config Key | Use Case |
|-----------|-----------|----------|
| AWS EC2 | `ec2_sd_configs` | EC2 instances by tag/region |
| Azure | `azure_sd_configs` | Azure VMs |
| GCE | `gce_sd_configs` | Google Compute instances |
| Docker | `docker_sd_configs` | Docker containers |
| DigitalOcean | `digitalocean_sd_configs` | Droplets |
| Eureka | `eureka_sd_configs` | Netflix Eureka registry |
| HTTP | `http_sd_configs` | Custom HTTP endpoint returning targets |

## Relabeling

Relabeling transforms labels before or after scraping. It's Prometheus's most powerful configuration feature.

### Actions

| Action | Purpose |
|--------|---------|
| `replace` | Regex match source labels, write to target label (default) |
| `keep` | Drop targets whose source labels don't match regex |
| `drop` | Drop targets whose source labels match regex |
| `hashmod` | Set target label to modulus of source label hash |
| `labelmap` | Copy labels whose names match regex |
| `labeldrop` | Drop labels whose names match regex |
| `labelkeep` | Keep only labels whose names match regex |

### Common Patterns

```yaml
relabel_configs:
  # Rename a label
  - source_labels: [__meta_kubernetes_pod_name]
    target_label: pod

  # Filter targets by label value
  - source_labels: [__meta_kubernetes_namespace]
    action: keep
    regex: "(production|staging)"

  # Drop specific metrics after scrape
  metric_relabel_configs:
    - source_labels: [__name__]
      regex: "go_(gc|memstats)_.*"
      action: drop

  # Add a static label
  - target_label: cluster
    replacement: "us-east-1"

  # Hash-based sharding across multiple Prometheus instances
  - source_labels: [__address__]
    modulus: 3
    target_label: __tmp_hash
    action: hashmod
  - source_labels: [__tmp_hash]
    regex: "0"         # This instance handles shard 0
    action: keep
```

## Alerting Configuration

```yaml
# Point to Alertmanager instances
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - "alertmanager1:9093"
            - "alertmanager2:9093"
      # Or use service discovery
      # kubernetes_sd_configs:
      #   - role: pod
      #     namespaces:
      #       names: ["monitoring"]

# Load rule files
rule_files:
  - "/etc/prometheus/rules/*.yml"
  - "/etc/prometheus/alerts/*.yml"
```

## Remote Write / Read

```yaml
# Send metrics to remote storage (Thanos, Mimir, Cortex, VictoriaMetrics)
remote_write:
  - url: "http://mimir:9009/api/v1/push"
    queue_config:
      max_samples_per_send: 1000
      batch_send_deadline: 5s
      max_shards: 30
    write_relabel_configs:
      - source_labels: [__name__]
        regex: "unwanted_.*"
        action: drop

# Read from remote storage
remote_read:
  - url: "http://mimir:9009/api/v1/read"
    read_recent: true
```

## Key Command-Line Flags

| Flag | Default | Purpose |
|------|---------|---------|
| `--config.file` | `prometheus.yml` | Config file path |
| `--storage.tsdb.path` | `data/` | TSDB data directory |
| `--storage.tsdb.retention.time` | `15d` | How long to keep data |
| `--storage.tsdb.retention.size` | — | Maximum storage size |
| `--web.listen-address` | `0.0.0.0:9090` | HTTP listen address |
| `--web.enable-lifecycle` | `false` | Enable `/-/reload` and `/-/quit` |
| `--web.enable-admin-api` | `false` | Enable admin endpoints |
| `--web.external-url` | — | Externally reachable URL |
| `--log.level` | `info` | Log level |
| `--enable-feature` | — | Comma-separated feature flags |

## Common Pitfalls

| Pitfall | Impact | Fix |
|---------|--------|-----|
| `scrape_timeout` > `scrape_interval` | Overlapping scrapes | Keep timeout < interval |
| Missing `metric_relabel_configs` | Storing unwanted high-cardinality metrics | Drop noisy metrics at ingest |
| No `sample_limit` | Single target can overload TSDB | Set reasonable per-job limits |
| Forgetting `external_labels` | No cluster/region info in federated setups | Always set in production |
| Static targets for dynamic infra | Stale targets, gaps | Use service discovery |

## Related Topics

- Service discovery in Kubernetes → `12-deployment.md`
- Relabeling for exporters → `11-exporters.md`
- Recording and alerting rules → `07-rules.md`
- Remote storage → `09-storage.md`
