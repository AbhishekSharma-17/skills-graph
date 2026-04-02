# Qdrant — Deployment

> Source: [qdrant.tech/documentation/guides/installation](https://qdrant.tech/documentation/guides/installation/) | v1.17.1

## Overview

Qdrant can be deployed as a single node for development or as a distributed cluster for production. This reference covers all deployment options, configuration, and distributed mode.

## Docker Deployment

### Basic Docker

```bash
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_data:/qdrant/storage:z \
    qdrant/qdrant:v1.17.1
```

### Docker Compose (Recommended)

```yaml
version: "3.8"
services:
  qdrant:
    image: qdrant/qdrant:v1.17.1
    ports:
      - "6333:6333"  # REST + Dashboard
      - "6334:6334"  # gRPC
    volumes:
      - qdrant_data:/qdrant/storage:z
      - ./config.yaml:/qdrant/config/production.yaml
    environment:
      - QDRANT__SERVICE__API_KEY=your-secret-key
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 4G

volumes:
  qdrant_data:
```

### Docker with Custom Config

```bash
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_data:/qdrant/storage:z \
    -v $(pwd)/config.yaml:/qdrant/config/production.yaml \
    qdrant/qdrant:v1.17.1
```

## Kubernetes Deployment

### Helm Chart

```bash
helm repo add qdrant https://qdrant.to/helm
helm repo update

# Single node
helm install qdrant qdrant/qdrant

# With custom values
helm install qdrant qdrant/qdrant -f values.yaml
```

### Helm Values Example

```yaml
# values.yaml
replicaCount: 3

resources:
  limits:
    cpu: "4"
    memory: "8Gi"
  requests:
    cpu: "2"
    memory: "4Gi"

persistence:
  enabled: true
  size: 50Gi
  storageClassName: gp3

config:
  service:
    api_key: "${QDRANT_API_KEY}"
  storage:
    performance:
      max_search_threads: 0
```

## Configuration

### Configuration File (config.yaml)

```yaml
# config.yaml — place at /qdrant/config/production.yaml
service:
  host: "0.0.0.0"
  http_port: 6333
  grpc_port: 6334
  api_key: "your-secret-api-key"     # enable API key auth
  read_only_api_key: "read-only-key" # separate read-only key

storage:
  storage_path: ./storage
  snapshots_path: ./snapshots

  performance:
    max_search_threads: 0     # 0 = auto (all cores)
    max_optimization_threads: 0

  optimizers:
    indexing_threshold_kb: 20000
    memmap_threshold_kb: 200000
    flush_interval_sec: 5

  hnsw_index:
    m: 16
    ef_construct: 100
    full_scan_threshold_kb: 10000

  wal:
    wal_capacity_mb: 32
    wal_segments_ahead: 0

# TLS configuration
tls:
  cert: ./tls/cert.pem
  key: ./tls/key.pem
  ca_cert: ./tls/ca.pem  # for mutual TLS
```

### Environment Variable Override

Any config can be overridden via environment variables using double-underscore notation:

```bash
# service.api_key → QDRANT__SERVICE__API_KEY
export QDRANT__SERVICE__API_KEY="my-secret-key"

# storage.performance.max_search_threads → QDRANT__STORAGE__PERFORMANCE__MAX_SEARCH_THREADS
export QDRANT__STORAGE__PERFORMANCE__MAX_SEARCH_THREADS=4
```

## API Key Authentication

### Server-Side

```yaml
# config.yaml
service:
  api_key: "your-secret-api-key"
  read_only_api_key: "read-only-key"  # optional
```

### Client-Side

```python
from qdrant_client import QdrantClient

# With API key
client = QdrantClient(
    url="http://localhost:6333",
    api_key="your-secret-api-key",
)

# With TLS + API key
client = QdrantClient(
    url="https://localhost:6333",
    api_key="your-secret-api-key",
    https=True,
)
```

## Distributed Mode

### Cluster Setup

Qdrant uses the Raft consensus protocol for cluster coordination. Port 6335 is used for internal cluster communication.

```yaml
# Node 1 — bootstrap node
cluster:
  enabled: true
  p2p:
    port: 6335

# Node 2 — joins cluster
cluster:
  enabled: true
  p2p:
    port: 6335
```

Start nodes:

```bash
# Bootstrap node
./qdrant --uri http://node1:6335

# Joining node
./qdrant --uri http://node2:6335 --bootstrap http://node1:6335
```

### Sharding

```python
# Create collection with custom shard count
client.create_collection(
    collection_name="distributed",
    vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE),
    shard_number=6,           # distribute across nodes
    replication_factor=2,     # 2 copies of each shard
    write_consistency_factor=1,
)
```

### Replication

| Parameter | Description |
|-----------|-------------|
| `shard_number` | Total shards (distribute across nodes) |
| `replication_factor` | Copies per shard |
| `write_consistency_factor` | Min replicas for write success |

## Qdrant Cloud

Managed service with automatic scaling, backups, and monitoring.

```python
client = QdrantClient(
    url="https://xyz-abc.aws.cloud.qdrant.io:6333",
    api_key="your-cloud-api-key",
)
```

**Cloud features:**
- Automatic backups (use Backups instead of snapshots)
- Horizontal scaling
- Monitoring dashboard
- SSO and RBAC (Enterprise)
- Available on AWS, GCP, Azure

## Health Checks

```bash
# HTTP health check
curl http://localhost:6333/healthz

# Readiness check
curl http://localhost:6333/readyz

# Cluster info (distributed mode)
curl http://localhost:6333/cluster
```

```python
# Python health check
try:
    client.get_collections()
    print("Qdrant is healthy")
except Exception as e:
    print(f"Qdrant is down: {e}")
```

## Production Checklist

1. **API key authentication** — Always enable in production
2. **TLS** — Enable for encrypted communication
3. **Persistent storage** — Mount volume for `/qdrant/storage`
4. **Resource limits** — Set memory and CPU limits
5. **Monitoring** — Prometheus metrics at `GET /metrics`
6. **Backups** — Schedule regular snapshots or use Cloud backups
7. **SSD/NVMe storage** — Required for good performance
8. **Network** — Ensure ports 6333, 6334, 6335 (cluster) are accessible
9. **Quantization** — Enable for production memory optimization
10. **Payload indexes** — Create before ingesting data

## Common Pitfalls

1. **NFS storage** — Qdrant is NOT compatible with NFS or object storage for data directories. Use local SSD/NVMe.
2. **Missing volume mount** — Without persistent storage, data is lost on container restart.
3. **Port conflicts** — Ensure 6333, 6334, 6335 are available.
4. **API key in logs** — Don't log or expose API keys. Use environment variables.
5. **Memory limits** — Set Docker/K8s memory limits above expected data size to avoid OOM kills.

## Related Topics

- Collections → `references/01-collections.md`
- Optimizer → `references/09-optimizer.md`
- Snapshots → `references/10-snapshots.md`
