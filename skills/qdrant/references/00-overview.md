# Qdrant — Overview & Setup

> Source: [qdrant.tech/documentation](https://qdrant.tech/documentation/) | v1.17.1 | Apache 2.0

## What is Qdrant?

Qdrant (pronounced "quadrant") is an open-source, AI-native vector similarity search engine and database written in Rust. It provides a production-ready service for storing, searching, and managing high-dimensional vectors with rich payload filtering.

**Key strengths:**
- Written in Rust with SIMD acceleration and async I/O (io_uring)
- Custom storage engine (Gridstore) optimized for vector workloads
- Rich payload filtering with 8 index types
- Hybrid search (sparse + dense vectors)
- Quantization options (scalar, binary, product) for memory optimization
- Distributed architecture with sharding and replication
- ~30,000 GitHub stars, Apache 2.0 license

## Architecture

```
┌─────────────────────────────────────────┐
│               Qdrant Server             │
│                                         │
│  ┌─────────┐  ┌─────────┐  ┌────────┐  │
│  │REST API  │  │gRPC API │  │Web UI  │  │
│  │:6333     │  │:6334    │  │:6333   │  │
│  └────┬─────┘  └────┬────┘  └───┬────┘  │
│       └──────┬───────┘          │        │
│         ┌────▼─────┐            │        │
│         │ Engine   │            │        │
│         └────┬─────┘            │        │
│    ┌─────────┼─────────┐       │        │
│  ┌─▼──┐  ┌──▼──┐  ┌──▼──┐    │        │
│  │Coll │  │Coll │  │Coll │    │        │
│  │  A  │  │  B  │  │  C  │    │        │
│  └─┬───┘  └─────┘  └─────┘    │        │
│  ┌─▼───────────────────┐      │        │
│  │ Segments             │      │        │
│  │ ┌───────┐ ┌───────┐ │      │        │
│  │ │ HNSW  │ │Payload│ │      │        │
│  │ │ Index │ │ Index │ │      │        │
│  │ └───────┘ └───────┘ │      │        │
│  │ ┌───────┐ ┌───────┐ │      │        │
│  │ │Vectors│ │  WAL  │ │      │        │
│  │ └───────┘ └───────┘ │      │        │
│  └──────────────────────┘      │        │
└─────────────────────────────────────────┘
```

**Core components:**
- **Collections** — Named groups of points sharing vector configuration
- **Points** — Vectors + optional JSON payloads + unique IDs
- **Segments** — Internal storage units; optimization happens at segment level
- **HNSW Index** — Hierarchical Navigable Small World graph for ANN search
- **WAL** — Write-Ahead Log for data durability

**API interfaces:**
- REST API on port 6333 (OpenAPI 3.0 spec)
- gRPC API on port 6334 (higher throughput)
- Web Dashboard at `http://localhost:6333/dashboard`
- Port 6335 for distributed internal communication

## Distance Metrics

| Metric | Description | Use Case |
|--------|-------------|----------|
| `Cosine` | Normalized dot product (0 to 2) | Text embeddings, general purpose |
| `Dot` | Raw dot product | Pre-normalized vectors, recommendation |
| `Euclid` | L2 distance | Image features, spatial data |
| `Manhattan` | L1 distance | Sparse features, certain ML models |

**Note:** Cosine distance is implemented internally by normalizing vectors and using dot product. If your vectors are already normalized, use `Dot` for a small performance gain.

## Installation

### Docker (recommended for development)

```bash
docker pull qdrant/qdrant
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_data:/qdrant/storage \
    qdrant/qdrant
```

### Docker Compose

```yaml
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - 6333:6333
      - 6334:6334
    volumes:
      - ./qdrant_data:/qdrant/storage:z
    restart: unless-stopped
```

### Kubernetes (Helm)

```bash
helm repo add qdrant https://qdrant.to/helm
helm install qdrant qdrant/qdrant
```

### From Source (Rust)

```bash
cargo build --release --bin qdrant
./target/release/qdrant
```

### System Requirements

- Architecture: x86_64 or AArch64
- Filesystem: POSIX-compliant (SSD/NVMe recommended)
- NOT compatible with NFS or object storage for data directories
- Memory: depends on collection size and quantization strategy

## Python Client Setup

```bash
# Basic client
pip install qdrant-client

# With local embedding support (FastEmbed)
pip install 'qdrant-client[fastembed]'

# With GPU-accelerated embeddings
pip install 'qdrant-client[fastembed-gpu]'
```

**Requires Python >= 3.10**

### Client Initialization

```python
from qdrant_client import QdrantClient, models

# --- Development / Testing ---

# In-memory (no persistence, great for tests)
client = QdrantClient(":memory:")

# Local file-based (no server needed)
client = QdrantClient(path="./qdrant_data")

# --- Production ---

# Remote server
client = QdrantClient("localhost", port=6333)
client = QdrantClient(url="http://localhost:6333")

# Qdrant Cloud
client = QdrantClient(
    url="https://xyz-abc.aws.cloud.qdrant.io:6333",
    api_key="your-api-key",
)
```

### Async Client

```python
from qdrant_client import AsyncQdrantClient

async_client = AsyncQdrantClient("localhost", port=6333)

# All methods mirror sync client with async/await
results = await async_client.query_points(
    collection_name="my_collection",
    query=[0.2, 0.1, 0.9, 0.7],
    limit=10,
)
```

## Quickstart — End to End

```python
from qdrant_client import QdrantClient, models

client = QdrantClient(":memory:")

# 1. Create collection
client.create_collection(
    collection_name="docs",
    vectors_config=models.VectorParams(
        size=384,
        distance=models.Distance.COSINE,
    ),
)

# 2. Insert points
client.upsert(
    collection_name="docs",
    points=[
        models.PointStruct(
            id=1,
            vector=[0.05, 0.61, 0.76, 0.74] + [0.0] * 380,
            payload={"title": "Intro to Qdrant", "category": "tutorial"},
        ),
        models.PointStruct(
            id=2,
            vector=[0.19, 0.81, 0.75, 0.11] + [0.0] * 380,
            payload={"title": "Advanced Search", "category": "guide"},
        ),
    ],
)

# 3. Search with filter
results = client.query_points(
    collection_name="docs",
    query=[0.05, 0.61, 0.76, 0.74] + [0.0] * 380,
    query_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="category",
                match=models.MatchValue(value="tutorial"),
            )
        ]
    ),
    limit=5,
)

for point in results.points:
    print(f"ID: {point.id}, Score: {point.score:.4f}, Title: {point.payload['title']}")
```

## FastEmbed Quickstart (No External Embeddings Needed)

```python
from qdrant_client import QdrantClient

client = QdrantClient(":memory:")

# Automatic embedding with FastEmbed
client.add(
    collection_name="demo",
    documents=["Qdrant is a vector search engine", "It is written in Rust"],
    metadata=[{"source": "docs"}, {"source": "docs"}],
    ids=[1, 2],
)

results = client.query(
    collection_name="demo",
    query_text="vector database",
    limit=5,
)

for result in results:
    print(f"Score: {result.score:.4f}, Doc: {result.document}")
```

## Common Patterns

### Health Check

```python
# REST: GET http://localhost:6333/healthz
info = client.get_collections()
print(f"Collections: {len(info.collections)}")
```

### Collection Info

```python
info = client.get_collection("my_collection")
print(f"Points: {info.points_count}")
print(f"Status: {info.status}")  # green, yellow, red
print(f"Vectors: {info.config.params.vectors}")
```

### Error Handling

```python
from qdrant_client.http.exceptions import UnexpectedResponse

try:
    client.get_collection("nonexistent")
except UnexpectedResponse as e:
    print(f"Status: {e.status_code}, Reason: {e.reason_phrase}")
```

## Related Topics

- Collections → `references/01-collections.md`
- Points & payloads → `references/02-points.md`
- Search & Query API → `references/03-search-query.md`
- Filtering → `references/04-filtering.md`
- Deployment → `references/12-deployment.md`
