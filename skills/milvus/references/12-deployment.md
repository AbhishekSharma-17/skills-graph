# Milvus — Deployment

> Source: [milvus.io/docs/install-overview.md](https://milvus.io/docs/install-overview.md) | Version: 3.0-beta

## Table of Contents

- [Deployment Tiers](#deployment-tiers)
- [Milvus Lite](#milvus-lite)
- [Standalone (Docker)](#standalone-docker)
- [Distributed (Kubernetes)](#distributed-kubernetes)
- [Zilliz Cloud (Managed)](#zilliz-cloud-managed)
- [Environment Portability](#environment-portability)
- [Health Checks](#health-checks)
- [Common Pitfalls](#common-pitfalls)

## Deployment Tiers

| Tier | Scale | Infrastructure | Data Persistence | Best For |
|------|-------|---------------|-----------------|----------|
| **Milvus Lite** | < ~1M vectors | None (embedded Python) | Local file | Prototyping, CI, notebooks |
| **Standalone** | < ~100M vectors | Docker on single host | Docker volumes | Small production, dev |
| **Distributed** | Billions of vectors | Kubernetes cluster | Object storage (S3/MinIO) | Large-scale production |
| **Zilliz Cloud** | Any scale | Managed | Managed | Zero-ops production |

## Milvus Lite

### Installation

```bash
pip install -U "pymilvus[milvus-lite]"
```

### Usage

```python
from pymilvus import MilvusClient

client = MilvusClient("./my_database.db")
```

Creates a local SQLite-style database file. All pymilvus operations work identically.

### Platform Support

- Ubuntu 20.04+ (x86_64, arm64)
- macOS 11.0+ (Apple Silicon M1/M2, x86_64)

### Limitations

- FLAT index only (no HNSW, IVF, DiskANN)
- No partitions
- No users/roles/RBAC
- No aliases
- No partition keys
- Single-process only

### Migration to Standalone

```bash
pip install -U "pymilvus[bulk_writer]"

# Export data
milvus-lite dump -d ./my_database.db -c my_collection -p ./export_dir

# Import into Standalone/Distributed
# Use bulk_import API with the exported JSON files
```

## Standalone (Docker)

### Prerequisites

- Docker Engine 19.03+
- Docker Compose v2
- Linux host recommended (macOS works for development)

### Quick Start

```bash
# Download compose file
wget https://github.com/milvus-io/milvus/releases/download/v3.0-beta/milvus-standalone-docker-compose.yml -O docker-compose.yml

# Start services
docker compose up -d
```

### What Gets Started

| Container | Purpose | Port | Storage |
|-----------|---------|------|---------|
| `milvus-standalone` | Database engine | 19530 (gRPC), 9091 (web UI) | `volumes/milvus` |
| `milvus-etcd` | Metadata storage | Internal | `volumes/etcd` |
| `milvus-minio` | Object storage | 9000, 9001 | `volumes/minio` |

### Connect

```python
from pymilvus import MilvusClient

client = MilvusClient(
    uri="http://localhost:19530",
    token="root:Milvus",
)
```

### Web UI

Access at `http://localhost:9091/webui/` for collection browsing, query playground, and system monitoring.

### Custom Configuration

```bash
# Enter the container
docker exec -it milvus-standalone bash

# Edit configuration
cat << 'EOF' > /milvus/configs/user.yaml
proxy:
  maxTaskNum: 2048
  healthCheckTimeout: 1000
queryNode:
  gracefulStopTimeout: 30
EOF

# Restart to apply
docker restart milvus-standalone
```

### Common Configuration Options

```yaml
# user.yaml
proxy:
  maxTaskNum: 1024             # max concurrent operations
  maxUserNum: 100              # max users for RBAC
  healthCheckTimeout: 3000     # health check timeout (ms)

common:
  security:
    authorizationEnabled: true  # enable auth/RBAC
    tlsMode: 0                  # 0=off, 1=one-way, 2=mutual

queryNode:
  enableDisk: true              # enable DiskANN index
  gracefulStopTimeout: 30

dataCoord:
  segment:
    maxSize: 1024               # segment size (MB)
    sealProportion: 0.12        # auto-seal threshold
```

### Persistent Storage

Data is stored in `./volumes/` by default. To use a custom path:

```yaml
# In docker-compose.yml, modify volume mappings
volumes:
  - /data/milvus/etcd:/etcd
  - /data/milvus/minio:/minio_data
  - /data/milvus/milvus:/var/lib/milvus
```

### Stop and Clean Up

```bash
# Stop services (data preserved)
docker compose down

# Stop and remove all data
docker compose down
rm -rf volumes/
```

## Distributed (Kubernetes)

### Prerequisites

- Kubernetes 1.20+
- Helm 3.0+
- StorageClass with dynamic provisioning
- Sufficient resources (minimum 16GB RAM for small clusters)

### Helm Installation

```bash
# Add Milvus Helm repository
helm repo add milvus https://zilliztech.github.io/milvus-helm/
helm repo update

# Install with defaults
helm install milvus milvus/milvus

# Install with custom values
helm install milvus milvus/milvus -f values.yaml
```

### Custom values.yaml

```yaml
# values.yaml
cluster:
  enabled: true

# Component replicas
proxy:
  replicas: 2
  resources:
    requests:
      cpu: "1"
      memory: "2Gi"

queryNode:
  replicas: 3
  resources:
    requests:
      cpu: "2"
      memory: "8Gi"

dataNode:
  replicas: 2
  resources:
    requests:
      cpu: "1"
      memory: "4Gi"

indexNode:
  replicas: 1
  resources:
    requests:
      cpu: "4"
      memory: "8Gi"

# External etcd (production)
etcd:
  replicaCount: 3
  persistence:
    size: 10Gi

# External MinIO/S3
minio:
  mode: distributed
  replicas: 4
  persistence:
    size: 100Gi

# Or use AWS S3
externalS3:
  enabled: true
  host: s3.amazonaws.com
  port: 443
  accessKey: "your-access-key"
  secretKey: "your-secret-key"
  bucketName: "milvus-data"
  region: "us-east-1"
  useSSL: true
```

### Connect to Distributed Milvus

```bash
# Port-forward the proxy service
kubectl port-forward svc/milvus 19530:19530
```

```python
client = MilvusClient(
    uri="http://localhost:19530",
    token="root:Milvus",
)
```

### Scaling Components

```bash
# Scale query nodes for more search throughput
kubectl scale deployment milvus-querynode --replicas=5

# Scale data nodes for more write throughput
kubectl scale deployment milvus-datanode --replicas=4
```

### Monitoring

```bash
# Install with Prometheus/Grafana monitoring
helm install milvus milvus/milvus \
  --set metrics.enabled=true \
  --set metrics.serviceMonitor.enabled=true
```

Milvus exposes metrics on port 9091 in Prometheus format.

## Zilliz Cloud (Managed)

### Connection

```python
from pymilvus import MilvusClient

client = MilvusClient(
    uri="https://your-cluster-id.serverless.zillizcloud.com",
    token="your-api-key",
)
```

### Features

- Fully managed — no infrastructure to maintain
- Auto-scaling compute and storage
- Built-in monitoring and alerting
- SOC 2 Type II compliance
- Multi-region availability

## Environment Portability

The same application code works across all deployment tiers:

```python
import os
from pymilvus import MilvusClient

MILVUS_URI = os.getenv("MILVUS_URI", "./local.db")
MILVUS_TOKEN = os.getenv("MILVUS_TOKEN", "")

client = MilvusClient(uri=MILVUS_URI, token=MILVUS_TOKEN)
```

```bash
# Development
export MILVUS_URI="./dev.db"

# Staging
export MILVUS_URI="http://milvus-staging:19530"
export MILVUS_TOKEN="staging_user:password"

# Production
export MILVUS_URI="https://prod.zillizcloud.com"
export MILVUS_TOKEN="prod-api-key"
```

## Health Checks

### Docker Standalone

```bash
# Container health
docker compose ps

# Milvus health endpoint
curl http://localhost:9091/healthz
```

### Kubernetes

```bash
# Pod status
kubectl get pods -l app.kubernetes.io/name=milvus

# Logs
kubectl logs -l app.kubernetes.io/instance=milvus -c milvus --tail=100
```

### From SDK

```python
from pymilvus import connections

connections.connect(host="localhost", port="19530")
# If no exception is raised, connection is healthy
```

## Common Pitfalls

- **Docker on macOS** — performance is significantly lower than Linux; use for development only
- **Insufficient memory for Standalone** — Milvus needs at least 4GB RAM; 8GB+ recommended
- **Forgetting to persist Docker volumes** — data is lost if `docker compose down` removes volumes
- **Using Milvus Lite in production** — it's designed for prototyping, not production workloads
- **Not monitoring disk usage on MinIO** — object storage grows continuously; set up alerts
- **Kubernetes without resource limits** — Milvus components can consume all node resources
