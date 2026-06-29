# Milvus — Overview & Setup

> Source: [milvus.io/docs](https://milvus.io/docs) | Version: 3.0-beta

## What Is Milvus

Milvus is an open-source, cloud-native vector database designed for billion-scale approximate nearest neighbor (ANN) search. Built primarily in Go and C++, it powers AI applications that need to store, index, and query vector embeddings alongside scalar metadata.

Key differentiators:
- **Distributed architecture** — separates compute, storage, and coordination for independent scaling
- **Multiple index types** — HNSW, IVF_FLAT, IVF_SQ8, IVF_PQ, DiskANN, GPU-accelerated indexes
- **Hybrid retrieval** — combines dense vectors, sparse vectors, and BM25 full-text search
- **Multi-tenancy** — database, collection, partition, and partition-key isolation strategies
- **Milvus Lite** — embedded mode for local development with zero infrastructure

## Architecture

Milvus follows a disaggregated architecture with four layers:

```
┌─────────────────────────────────────────────┐
│              Access Layer (Proxy)            │
│   API gateway, request routing, load balance│
├─────────────────────────────────────────────┤
│           Coordinator Service               │
│   Root Coord · Data Coord · Query Coord     │
├──────────────────┬──────────────────────────┤
│   Worker Nodes   │    Streaming Node (v3)   │
│  Query · Data ·  │   WAL · Real-time ingest │
│  Index Nodes     │   Pub/Sub channels       │
├──────────────────┴──────────────────────────┤
│              Object Storage (S3/MinIO)      │
│         + etcd (metadata) + MQ (log)        │
└─────────────────────────────────────────────┘
```

**Three deployment tiers:**

| Mode | Scale | Infrastructure | Use Case |
|------|-------|---------------|----------|
| **Milvus Lite** | Millions of vectors | None (embedded) | Prototyping, notebooks, CI tests |
| **Standalone** | ~100M vectors | Single Docker host | Small production, development |
| **Distributed** | Billions of vectors | Kubernetes cluster | Large-scale production |

## Installation

### Milvus Lite (Embedded — Zero Infrastructure)

```bash
pip install -U "pymilvus[milvus-lite]"
```

```python
from pymilvus import MilvusClient

client = MilvusClient("./milvus_demo.db")
```

### Milvus Standalone (Docker)

```bash
wget https://github.com/milvus-io/milvus/releases/download/v3.0-beta/milvus-standalone-docker-compose.yml -O docker-compose.yml
docker compose up -d
```

Starts three containers: `milvus-etcd` (metadata), `milvus-minio` (object storage), `milvus-standalone` (database engine). Access on port **19530** (gRPC) and **9091** (web UI).

```python
from pymilvus import MilvusClient

client = MilvusClient(uri="http://localhost:19530", token="root:Milvus")
```

### Milvus Distributed (Kubernetes)

```bash
# Using Helm
helm repo add milvus https://zilliztech.github.io/milvus-helm/
helm repo update
helm install milvus milvus/milvus
```

### SDKs

| Language | Package | Install |
|----------|---------|---------|
| Python | `pymilvus` | `pip install pymilvus` |
| Node.js | `@zilliz/milvus2-sdk-node` | `npm install @zilliz/milvus2-sdk-node` |
| Java | `io.milvus:milvus-sdk-java` | Maven/Gradle |
| Go | `github.com/milvus-io/milvus-sdk-go` | `go get` |
| C# | `Milvus.Client` | NuGet |
| RESTful | Built-in | `curl http://localhost:19530/v2/...` |

## Quickstart

```python
from pymilvus import MilvusClient
import numpy as np

# Connect (Milvus Lite for local dev)
client = MilvusClient("./quickstart.db")

# Create a collection with auto-schema
client.create_collection(
    collection_name="articles",
    dimension=384,
)

# Prepare data
data = [
    {"id": 1, "vector": np.random.rand(384).tolist(), "title": "Introduction to AI", "category": "tech"},
    {"id": 2, "vector": np.random.rand(384).tolist(), "title": "Machine Learning Basics", "category": "tech"},
    {"id": 3, "vector": np.random.rand(384).tolist(), "title": "Cooking with Python", "category": "food"},
]

# Insert
client.insert(collection_name="articles", data=data)

# Search — find similar vectors
results = client.search(
    collection_name="articles",
    data=[np.random.rand(384).tolist()],
    limit=2,
    output_fields=["title", "category"],
)

for hits in results:
    for hit in hits:
        print(f"  id={hit['id']}, distance={hit['distance']:.4f}, title={hit['entity']['title']}")

# Query with filter
results = client.query(
    collection_name="articles",
    filter="category == 'tech'",
    output_fields=["title"],
)

# Delete
client.delete(collection_name="articles", filter="category == 'food'")

# Drop collection
client.drop_collection("articles")
```

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Collection** | Table equivalent — fixed schema with vector and scalar fields |
| **Entity** | Row in a collection — one data record |
| **Field** | Column — typed (vector, scalar, or composite) |
| **Schema** | Collection structure definition with field types and constraints |
| **Index** | Data structure for fast ANN search (HNSW, IVF, DiskANN) |
| **Partition** | Subset of a collection for data isolation or performance |
| **Segment** | Internal storage unit — data chunk within a partition |
| **Shard** | Horizontal slice for write throughput distribution |
| **Consistency Level** | Trade-off between data freshness and query latency |

## Consistency Levels

| Level | Guarantee | Latency | Use Case |
|-------|-----------|---------|----------|
| **Strong** | Reads see all committed writes | Highest | Financial, compliance |
| **Bounded Staleness** | Reads lag by configurable bound | Medium | Near-real-time dashboards |
| **Session** | Reads see own writes | Low | User-facing applications |
| **Eventually** | Reads may lag | Lowest | Analytics, batch processing |

## Connection URI Patterns

```python
# Milvus Lite (local file)
client = MilvusClient("./local.db")

# Standalone (Docker)
client = MilvusClient(uri="http://localhost:19530", token="root:Milvus")

# Distributed (Kubernetes)
client = MilvusClient(uri="http://milvus-proxy:19530", token="user:password")

# Zilliz Cloud (managed)
client = MilvusClient(
    uri="https://your-cluster.zillizcloud.com",
    token="your-api-key",
)
```

The same application code works across all deployment tiers — only the URI changes.

## Version History

| Version | Release | Highlights |
|---------|---------|------------|
| v3.0-beta | May 2026 | Storage V3, external collections, entity TTL, query aggregation, null vectors |
| v2.6.x | 2025-2026 | Storage V2, BM25 full-text search, JSON processing, FP16 auto-conversion |
| v2.5.x | 2024-2025 | Sparse vectors, hybrid search, text match, clustering compaction |
| v2.4.x | 2024 | Multi-vector search, partition keys, GPU indexing |
