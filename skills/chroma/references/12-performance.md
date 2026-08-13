# Chroma — Performance & Optimization

> Source: [docs.trychroma.com/guides/performance](https://docs.trychroma.com/guides/performance)

## Table of Contents

- [HNSW Tuning](#hnsw-tuning)
- [Batch Operations](#batch-operations)
- [Embedding Strategy](#embedding-strategy)
- [Query Optimization](#query-optimization)
- [Memory Management](#memory-management)
- [Cold Storage and Warm-Up](#cold-storage-and-warm-up)
- [Collection Design](#collection-design)
- [Monitoring and Benchmarking](#monitoring-and-benchmarking)
- [Scaling Strategies](#scaling-strategies)
- [Common Pitfalls](#common-pitfalls)

## HNSW Tuning

HNSW (Hierarchical Navigable Small World) parameters control the trade-off between search quality (recall) and speed.

### Key Parameters

| Parameter | Default | Effect of Increase | Use Case |
|-----------|---------|-------------------|----------|
| `ef_construction` | 100 | Better recall, slower build | One-time cost at data ingestion |
| `ef_search` | 100 | Better recall, slower query | Tunable at query time |
| `max_neighbors` | 16 | More connections, more memory | Dense datasets |

### Recommended Configurations

**High Recall (quality priority):**

```python
collection = client.create_collection(
    name="high_recall",
    configuration={
        "hnsw": {
            "space": "cosine",
            "ef_construction": 200,
            "ef_search": 200,
            "max_neighbors": 32,
        }
    },
)
```

**Balanced (default for most use cases):**

```python
collection = client.create_collection(
    name="balanced",
    configuration={
        "hnsw": {
            "space": "cosine",
            "ef_construction": 128,
            "ef_search": 100,
            "max_neighbors": 16,
        }
    },
)
```

**Low Latency (speed priority):**

```python
collection = client.create_collection(
    name="fast",
    configuration={
        "hnsw": {
            "space": "cosine",
            "ef_construction": 64,
            "ef_search": 50,
            "max_neighbors": 12,
        }
    },
)
```

### Tuning ef_search at Runtime

`ef_search` is the only HNSW parameter modifiable after collection creation:

```python
collection.modify(
    configuration={"hnsw": {"ef_search": 200}},
)
```

Increase `ef_search` when you need better recall; decrease when you need faster queries.

## Batch Operations

### Optimal Batch Sizes

Large insertions should be batched for performance and memory efficiency.

```python
def batch_add(collection, ids, documents, metadatas, batch_size=1000):
    for i in range(0, len(ids), batch_size):
        end = min(i + batch_size, len(ids))
        collection.add(
            ids=ids[i:end],
            documents=documents[i:end],
            metadatas=metadatas[i:end] if metadatas else None,
        )

# Usage
batch_add(collection, all_ids, all_docs, all_meta, batch_size=1000)
```

**Recommended batch sizes:**
- Local embedding (sentence-transformers): 100–500
- API embedding (OpenAI, Cohere): 500–2000 (limited by API rate limits)
- Pre-computed embeddings: 1000–5000

### Upsert for Idempotent Ingestion

```python
# Safe for re-runs — updates existing, adds new
for batch in chunks(data, 1000):
    collection.upsert(
        ids=batch["ids"],
        documents=batch["documents"],
        metadatas=batch["metadatas"],
    )
```

## Embedding Strategy

### API vs Local Embeddings

| Strategy | Pros | Cons |
|----------|------|------|
| **API (OpenAI, Cohere)** | High quality, no GPU needed | API costs, rate limits, latency |
| **Local (sentence-transformers)** | Free, private, no network | GPU recommended, model download |
| **Ollama** | Free, private, flexible models | Slower than GPU-accelerated |

### Serverless Environments

In AWS Lambda, Cloud Functions, or Vercel:
- Use `chromadb-client` (thin client) to avoid heavy model dependencies
- Rely on the Chroma server or API-based embedding functions
- Or pre-compute embeddings before inserting

```python
# Serverless function — thin client, pre-computed embeddings
import chromadb

client = chromadb.HttpClient(host="chroma.example.com", port=8000)
collection = client.get_collection(name="docs")

# Embeddings pre-computed elsewhere
collection.add(
    ids=["id1"],
    embeddings=[[0.1, 0.2, ...]],
    documents=["text"],
)
```

## Query Optimization

### Filter Before Similarity

Metadata filters narrow the search space before HNSW traversal, improving performance:

```python
# Fast: filter first, then rank
results = collection.query(
    query_texts=["search term"],
    n_results=10,
    where={"category": "science"},  # Reduces candidates
)
```

### Limit n_results

Request only what you need. Larger `n_results` requires more HNSW traversal:

```python
# Good: request what you need
results = collection.query(query_texts=["search"], n_results=5)

# Avoid: requesting far more than needed
results = collection.query(query_texts=["search"], n_results=1000)
```

### Include Only Needed Fields

Omit `embeddings` from results to save bandwidth:

```python
# Skip embeddings (large vectors)
results = collection.query(
    query_texts=["search"],
    n_results=10,
    include=["documents", "metadatas", "distances"],
)
```

### Pre-Compute Query Embeddings

For repeated queries, compute the embedding once:

```python
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

ef = OpenAIEmbeddingFunction(model_name="text-embedding-3-small")
query_embedding = ef(["common search query"])[0]

# Reuse for multiple queries
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=10,
)
```

## Memory Management

### Embedding Dimension Impact

| Model | Dimensions | Memory per 1M Records |
|-------|-----------|----------------------|
| all-MiniLM-L6-v2 | 384 | ~1.5 GB |
| text-embedding-3-small | 1536 | ~6 GB |
| text-embedding-3-large | 3072 | ~12 GB |

### Collection Size Guidelines

- **< 100K records:** In-memory client works well
- **100K – 1M records:** Use PersistentClient or client-server
- **1M – 10M records:** Client-server with dedicated hardware
- **> 10M records:** Consider Chroma Cloud or sharding across collections

## Cold Storage and Warm-Up

On Chroma Cloud, inactive collections are moved to cold storage. The first query to a cold collection incurs additional latency as data is loaded.

### Warm-Up Pattern

```python
# Send a warm-up query before production traffic
collection.query(
    query_texts=["warm up"],
    n_results=1,
)
# Subsequent queries will be fast
```

## Collection Design

### Single vs Multiple Collections

**Single collection:** When all data shares the same schema and embedding model. Simpler to manage.

**Multiple collections:** When data has different embedding models, schemas, or access patterns.

```python
# Separate by data type
code_collection = client.create_collection(name="code_embeddings")
docs_collection = client.create_collection(name="doc_embeddings")

# Separate by tenant
for tenant_id in tenant_ids:
    client.create_collection(name=f"tenant_{tenant_id}")
```

### Metadata for Partitioning

Instead of creating many collections, use metadata fields to partition data within a single collection:

```python
# Add with partition metadata
collection.add(
    ids=["doc1"],
    documents=["content"],
    metadatas=[{"tenant_id": "acme", "doc_type": "invoice"}],
)

# Query specific partition
results = collection.query(
    query_texts=["search"],
    where={"tenant_id": "acme"},
    n_results=10,
)
```

## Monitoring and Benchmarking

### Basic Metrics

```python
# Collection statistics
count = collection.count()
sample = collection.peek()

print(f"Total records: {count}")
print(f"Sample IDs: {sample['ids'][:5]}")
```

### Query Latency Measurement

```python
import time

start = time.perf_counter()
results = collection.query(
    query_texts=["benchmark query"],
    n_results=10,
)
elapsed_ms = (time.perf_counter() - start) * 1000
print(f"Query latency: {elapsed_ms:.1f}ms")
```

### OpenTelemetry Integration

See `references/09-deployment.md` for OTEL setup to trace operations across the Chroma server.

## Scaling Strategies

| Strategy | When | How |
|----------|------|-----|
| **Vertical** | < 10M records | More RAM, faster disk |
| **Collection sharding** | Multiple data types | Separate collections per domain |
| **Chroma Cloud** | > 10M records | Managed, auto-scaling |
| **Thin client** | Serverless/edge | Minimal footprint, server-side compute |

## Common Pitfalls

1. **ef_construction is permanent** — Set it right at collection creation. To change it, you must recreate the collection and re-index all data.

2. **Large batch + local embeddings = OOM** — Batch sizes > 5000 with sentence-transformers can exhaust memory. Use smaller batches or stream processing.

3. **Metadata bloat** — Large metadata values (long strings, large arrays) increase storage and slow queries. Keep metadata concise and structured.

4. **No index on metadata** — Chroma's metadata filtering is a post-retrieval filter, not an indexed lookup. Highly selective filters on large collections may be slow.

5. **Cosine vs L2 default** — The default distance function is L2, not cosine. For normalized text embeddings, explicitly set `space: "cosine"` for meaningful similarity scores.
