# Milvus — Indexing

> Source: [milvus.io/docs/index-vector-fields.md](https://milvus.io/docs/index-vector-fields.md) | Version: 3.0-beta

## Overview

Indexes are data structures that accelerate approximate nearest neighbor (ANN) search. Without an index, Milvus performs brute-force search (FLAT), which is accurate but slow at scale. Choosing the right index type is critical for balancing search speed, recall accuracy, memory usage, and build time.

## Index Types for Float Vectors

| Index | Algorithm | Memory | Build Speed | Search Speed | Recall | Best For |
|-------|-----------|--------|-------------|--------------|--------|----------|
| **FLAT** | Brute-force | High | N/A | Slow | 100% | Small datasets, ground truth |
| **IVF_FLAT** | Inverted file | Medium | Fast | Medium | High | Balanced speed/recall |
| **IVF_SQ8** | IVF + scalar quantization | Low | Fast | Fast | Good | Memory-constrained |
| **IVF_PQ** | IVF + product quantization | Very low | Slow | Fast | Moderate | Very large datasets |
| **HNSW** | Hierarchical navigable small world | High | Slow | Very fast | Very high | Production search |
| **DISKANN** | Disk-based ANN | Low (disk) | Slow | Fast | High | Billion-scale on disk |
| **SCANN** | Score-aware quantization | Medium | Medium | Fast | High | Google-style search |

## Index Types for GPU

| Index | Description | Notes |
|-------|-------------|-------|
| **GPU_IVF_FLAT** | IVF_FLAT on GPU | Requires NVIDIA GPU |
| **GPU_IVF_PQ** | IVF_PQ on GPU | Best for massive throughput |

## Index Types for Binary Vectors

| Index | Metrics | Use Case |
|-------|---------|----------|
| **BIN_FLAT** | JACCARD, HAMMING | Small binary datasets |
| **BIN_IVF_FLAT** | JACCARD, HAMMING | Large binary datasets |

## Index for Sparse Vectors

| Index | Metrics | Notes |
|-------|---------|-------|
| **SPARSE_INVERTED_INDEX** | IP, BM25 | Standard for sparse/BM25 |

## Similarity Metrics

| Metric | Vector Type | Interpretation | Range | Use Case |
|--------|-------------|---------------|-------|----------|
| **L2** | Float | Lower = more similar | [0, ∞) | Spatial data, default |
| **IP** | Float | Higher = more similar | [-1, 1] | Non-normalized embeddings |
| **COSINE** | Float | Higher = more similar | [-1, 1] | Text embeddings, NLP |
| **JACCARD** | Binary | Lower = more similar | [0, 1] | Set comparison |
| **HAMMING** | Binary | Lower = more similar | [0, dim] | Binary fingerprints |
| **BM25** | Sparse | Higher = more relevant | [0, ∞) | Full-text search |

## Creating Indexes

### Step 1: Prepare Index Parameters

```python
from pymilvus import MilvusClient

client = MilvusClient(uri="http://localhost:19530", token="root:Milvus")

index_params = client.prepare_index_params()
```

### Step 2: Add Index Definitions

```python
# HNSW index on vector field
index_params.add_index(
    field_name="embedding",
    index_type="HNSW",
    metric_type="COSINE",
    params={
        "M": 16,              # max connections per node (4-64, default 16)
        "efConstruction": 256, # build-time search width (8-512, default 256)
    },
)

# Scalar index for filtering
index_params.add_index(
    field_name="category",
    index_type="Trie",  # for VARCHAR fields
)

index_params.add_index(
    field_name="score",
    index_type="STL_SORT",  # for numeric fields
)
```

### Step 3: Create the Index

```python
client.create_index(
    collection_name="documents",
    index_params=index_params,
    sync=True,  # wait for completion (default: True)
)
```

### Step 4: Verify

```python
indexes = client.list_indexes(collection_name="documents")
# ['embedding', 'category', 'score']

details = client.describe_index(
    collection_name="documents",
    index_name="embedding",
)
```

## HNSW Parameters

The most popular index type for production:

```python
index_params.add_index(
    field_name="embedding",
    index_type="HNSW",
    metric_type="COSINE",
    params={
        "M": 16,               # connections per node — higher = better recall, more memory
        "efConstruction": 256,  # build quality — higher = better recall, slower build
    },
)
```

**Search-time parameter:**

```python
results = client.search(
    collection_name="documents",
    data=[query_vector],
    limit=10,
    search_params={
        "metric_type": "COSINE",
        "params": {
            "ef": 128,  # search width — higher = better recall, slower search
        },
    },
)
```

| Parameter | Range | Effect |
|-----------|-------|--------|
| `M` | 4–64 | More connections = higher recall + more memory |
| `efConstruction` | 8–512 | Higher = better graph quality, slower build |
| `ef` (search) | ≥ limit | Higher = better recall, slower search |

## IVF_FLAT Parameters

Good balance of speed and recall:

```python
index_params.add_index(
    field_name="embedding",
    index_type="IVF_FLAT",
    metric_type="L2",
    params={
        "nlist": 128,  # number of cluster centroids (16-65536)
    },
)
```

**Search-time parameter:**

```python
search_params = {
    "params": {
        "nprobe": 16,  # clusters to search (1-nlist)
    },
}
```

## IVF_PQ Parameters

Compressed vectors for large-scale:

```python
index_params.add_index(
    field_name="embedding",
    index_type="IVF_PQ",
    metric_type="L2",
    params={
        "nlist": 128,
        "m": 8,       # sub-vector count (dim must be divisible by m)
        "nbits": 8,   # bits per sub-vector code (default 8)
    },
)
```

## DiskANN Parameters

Disk-based for billion-scale without all vectors in RAM:

```python
index_params.add_index(
    field_name="embedding",
    index_type="DISKANN",
    metric_type="COSINE",
)
```

**Search-time parameter:**

```python
search_params = {
    "params": {
        "search_list": 64,  # candidate list size (must be > limit)
    },
}
```

## AUTOINDEX

Let Milvus choose the best index type automatically:

```python
index_params.add_index(
    field_name="embedding",
    index_type="AUTOINDEX",
    metric_type="COSINE",
)
```

Typically resolves to HNSW for in-memory or DiskANN for disk-based.

## Scalar Field Indexes

```python
# VARCHAR — Trie index (prefix matching)
index_params.add_index(field_name="title", index_type="Trie")

# Numeric — sorted index
index_params.add_index(field_name="score", index_type="STL_SORT")

# General inverted index (good for filtering)
index_params.add_index(field_name="category", index_type="INVERTED")
```

## Sparse Vector Index

```python
index_params.add_index(
    field_name="sparse_embedding",
    index_type="SPARSE_INVERTED_INDEX",
    metric_type="IP",
    params={
        "inverted_index_algo": "DAAT_MAXSCORE",  # or DAAT_WAND, TAAT_NAIVE
    },
)
```

For BM25 full-text search:

```python
index_params.add_index(
    field_name="text_sparse",
    index_type="SPARSE_INVERTED_INDEX",
    metric_type="BM25",
    params={
        "inverted_index_algo": "DAAT_MAXSCORE",
        "bm25_k1": 1.2,
        "bm25_b": 0.75,
    },
)
```

## Dropping Indexes

```python
client.drop_index(
    collection_name="documents",
    index_name="embedding",
)
```

## Index Selection Guide

| Scenario | Recommended Index | Why |
|----------|------------------|-----|
| < 1M vectors, need best recall | FLAT | Exact search, no approximation |
| 1M–100M, production search | HNSW | Best recall/speed trade-off |
| 1M–100M, memory-constrained | IVF_SQ8 or IVF_PQ | Quantized, lower memory |
| > 100M, disk-based | DISKANN | Billion-scale with SSD |
| GPU available, max throughput | GPU_IVF_FLAT | Massive parallel search |
| Sparse/BM25 vectors | SPARSE_INVERTED_INDEX | Only option for sparse |

## Common Pitfalls

- **Only one index per field** — creating a new index on a field drops the old one
- **Forgetting scalar indexes** — filtered search is slow without indexes on filter fields
- **Setting `ef` < `limit`** — HNSW search returns fewer results than requested
- **Using FLAT beyond ~1M vectors** — brute-force becomes impractically slow
- **Mismatched metric types** — index metric must match search metric
