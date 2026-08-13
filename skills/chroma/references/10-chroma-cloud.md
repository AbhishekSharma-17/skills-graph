# Chroma — Chroma Cloud

> Source: [docs.trychroma.com/cloud](https://docs.trychroma.com/cloud)

## Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
- [Client Setup](#client-setup)
- [Search API](#search-api)
- [K Expressions](#k-expressions)
- [KNN Ranking](#knn-ranking)
- [Hybrid Search with RRF](#hybrid-search-with-rrf)
- [Group By and Aggregation](#group-by-and-aggregation)
- [Batch Operations](#batch-operations)
- [Collection Forking](#collection-forking)
- [Sync Features](#sync-features)
- [Regions and Pricing](#regions-and-pricing)
- [Common Pitfalls](#common-pitfalls)

## Overview

Chroma Cloud is the managed, serverless vector search platform. It provides features beyond the open-source version:

| Feature | Open Source | Cloud |
|---------|-----------|-------|
| Vector search (KNN) | Yes | Yes |
| Full-text search | Basic ($contains) | Advanced (tokenized) |
| Hybrid search (RRF) | No | Yes |
| Sparse vectors | No | Yes |
| Group by / aggregation | No | Yes |
| Batch operations | No | Yes |
| Custom ranking | No | Yes |
| Collection forking | No | Yes |
| SOC 2 Type II | No | Yes |
| Index type | HNSW | SPANN |

## Getting Started

1. Sign up at [trychroma.com/signup](https://trychroma.com/signup)
2. Create a database in the dashboard
3. Generate an API key
4. Connect using `CloudClient`

## Client Setup

### Python

```python
import chromadb

client = chromadb.CloudClient(
    tenant="your-tenant-id",
    database="your-database-name",
    api_key="your-api-key",
)

# Or use environment variables
# CHROMA_API_KEY, CHROMA_TENANT, CHROMA_DATABASE
client = chromadb.CloudClient()
```

### TypeScript

```typescript
import { ChromaClient } from "chromadb";

const client = new ChromaClient({
  host: "api.trychroma.com",
  ssl: true,
  apiKey: process.env.CHROMA_API_KEY,
  tenant: "your-tenant-id",
  database: "your-database-name",
});
```

## Search API

The Search API is a unified interface exclusive to Chroma Cloud. It replaces separate `query()` and `get()` methods with a composable, chainable API.

### Basic Search

```python
from chromadb import Search, K, Knn

search = (
    Search()
    .where(K("category") == "science")
    .rank(Knn(query="machine learning"))
    .limit(10)
    .select(K.DOCUMENT, K.SCORE)
)

results = collection.search(search)
```

### Filtered Search

```python
from chromadb import Search, K, Knn

search = (
    Search()
    .where((K("category") == "science") & (K("year") >= 2020))
    .rank(Knn(query="deep learning breakthroughs"))
    .limit(20)
    .select(K.DOCUMENT, K.SCORE, "title", "year")
)

results = collection.search(search)
```

## K Expressions

`K()` expressions provide type-safe filtering with IDE autocomplete.

```python
from chromadb import K

# Equality
K("field") == "value"

# Comparison
K("score") >= 0.8
K("year") > 2020

# Logical operators
(K("category") == "science") & (K("year") >= 2020)  # AND
(K("source") == "arxiv") | (K("source") == "pubmed")  # OR

# Special selectors
K.DOCUMENT   # Select document text
K.SCORE      # Select similarity score
K.EMBEDDING  # Select embedding vector
```

## KNN Ranking

```python
from chromadb import Knn

# Text query (auto-embedded)
rank = Knn(query="machine learning")

# With custom key (for sparse embeddings)
rank = Knn(query="machine learning", key="sparse_embedding")

# Pre-computed embedding
rank = Knn(embedding=[0.1, 0.2, 0.3, ...])

# Limit candidates for performance
rank = Knn(query="search term", limit=500)
```

## Hybrid Search with RRF

Reciprocal Rank Fusion combines multiple ranking strategies. It uses rank positions rather than raw scores, making it effective when merging dense and sparse search results.

### RRF Formula

```
score = -Σ(wᵢ / (k + rᵢ))
```

Where `wᵢ` = weight, `rᵢ` = rank position, `k` = smoothing parameter (default 60).

### Dense + Sparse Search

```python
from chromadb import Search, K, Knn, Rrf

hybrid_rank = Rrf(
    ranks=[
        Knn(query="machine learning", return_rank=True),
        Knn(query="machine learning", key="sparse_embedding", return_rank=True),
    ],
    weights=[0.7, 0.3],  # 70% semantic, 30% keyword
    k=60,
)

search = (
    Search()
    .where((K("language") == "en") & (K("year") >= 2020))
    .rank(hybrid_rank)
    .limit(10)
    .select(K.DOCUMENT, K.SCORE, "title")
)

results = collection.search(search)
```

### RRF Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ranks` | `list[Rank]` | Required | Ranking expressions with `return_rank=True` |
| `k` | `int` | `60` | Smoothing. Higher = less emphasis on top ranks |
| `weights` | `list[float]` | Equal | Relative importance of each ranking |
| `normalize` | `bool` | `False` | Normalize weights to sum to 1.0 |

### k Parameter Effect

| k Value | Behavior |
|---------|----------|
| 10 (small) | Heavy weighting toward top results |
| 60 (default) | Balanced emphasis across ranks |
| 100+ (large) | More uniform distribution |

## Group By and Aggregation

Group results by a field and return the top match per group.

```python
from chromadb import Search, K, Knn

search = (
    Search()
    .rank(Knn(query="python tutorial"))
    .group_by("category")
    .limit(5)
    .select(K.DOCUMENT, K.SCORE, "category")
)

results = collection.search(search)
```

## Batch Operations

Execute multiple searches in a single API call.

```python
from chromadb import Search, K, Knn

searches = [
    Search().rank(Knn(query="python")).limit(5),
    Search().rank(Knn(query="typescript")).limit(5),
    Search().rank(Knn(query="rust")).limit(5),
]

results = collection.search_many(searches)
```

## Collection Forking

Create a copy of a collection for experimentation without affecting the original.

```python
forked = client.fork_collection(
    source="production_docs",
    name="experiment_v2",
)

# Modify the fork freely
forked.add(ids=["new1"], documents=["experimental data"])

# Original collection is unchanged
```

## Sync Features

Chroma Cloud can automatically sync data from external sources:

| Source | Description |
|--------|-------------|
| **S3 Sync** | Automatically index files from S3 buckets |
| **GitHub Sync** | Index repository contents and keep in sync |
| **Web Sync** | Crawl and index web pages |
| **File Upload** | Upload and index individual files |

## Regions and Pricing

**Regions:**

| Region | Endpoint |
|--------|----------|
| AWS US East (Virginia) | `api.trychroma.com` (default) |
| GCP Europe West (Belgium) | `europe-west1.gcp.trychroma.com` |

**Pricing:** Free tier available. Pay-as-you-go for production workloads. See [trychroma.com/pricing](https://trychroma.com/pricing) for current rates.

## Common Pitfalls

1. **Search API is Cloud-only** — The `Search()`, `K()`, `Knn()`, `Rrf()` APIs are exclusive to Chroma Cloud. Self-hosted uses `query()` and `get()`.

2. **return_rank=True required for RRF** — Every `Knn` expression inside `Rrf` must have `return_rank=True`. Without it, the RRF computation fails.

3. **Scores are negative** — Chroma Cloud uses ascending score order (lower = better). RRF scores are negative.

4. **Cold collection latency** — First query to an inactive collection is slower due to loading from cold storage. Send warm-up queries before production traffic.

5. **SPANN is not configurable** — Cloud uses SPANN instead of HNSW. You cannot tune SPANN parameters (they are managed by Chroma).
