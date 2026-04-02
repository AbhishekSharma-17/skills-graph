# Qdrant — Hybrid Search

> Source: [qdrant.tech/documentation/concepts/hybrid-queries](https://qdrant.tech/documentation/concepts/hybrid-queries/) | v1.17.1

## Overview

Hybrid search combines multiple retrieval strategies (e.g., sparse keyword search + dense semantic search) to improve result quality. Qdrant implements this through the **prefetch** mechanism in the Query API, where sub-queries execute first and their results are fused by the main query.

**Architecture:**
```
prefetch[0]: sparse search → top 20
prefetch[1]: dense search  → top 20
                    ↓
           main query: RRF fusion → top 10
```

## Setup: Collection with Sparse + Dense Vectors

```python
from qdrant_client import QdrantClient, models

client = QdrantClient("localhost", port=6333)

client.create_collection(
    collection_name="hybrid",
    vectors_config={
        "dense": models.VectorParams(
            size=768,
            distance=models.Distance.COSINE,
        ),
    },
    sparse_vectors_config={
        "sparse": models.SparseVectorParams(
            modifier=models.Modifier.IDF,  # automatic IDF weighting
        ),
    },
)
```

### Upsert Hybrid Points

```python
client.upsert(
    collection_name="hybrid",
    points=[
        models.PointStruct(
            id=1,
            vector={
                "dense": [0.05, 0.61, 0.76, 0.74] + [0.0] * 764,
                "sparse": models.SparseVector(
                    indices=[1, 42, 103, 784],     # token indices
                    values=[0.22, 0.8, 0.51, 0.3], # token weights
                ),
            },
            payload={"title": "Introduction to Vector Search"},
        ),
    ],
)
```

## Fusion Methods

### RRF — Reciprocal Rank Fusion

Combines results by rank position, not raw scores. Robust when score scales differ across search types.

**Formula:** `score = Σ (weight / (k + rank_i))` where k defaults to 2.

```python
results = client.query_points(
    collection_name="hybrid",
    prefetch=[
        models.Prefetch(
            query=models.SparseVector(
                indices=[1, 42, 103],
                values=[0.22, 0.8, 0.51],
            ),
            using="sparse",
            limit=20,
        ),
        models.Prefetch(
            query=[0.05, 0.61, 0.76, 0.74] + [0.0] * 764,
            using="dense",
            limit=20,
        ),
    ],
    query=models.FusionQuery(fusion=models.Fusion.RRF),
    limit=10,
)
```

### Weighted RRF (v1.17.0+)

Assign different weights to each prefetch query:

```python
results = client.query_points(
    collection_name="hybrid",
    prefetch=[
        models.Prefetch(
            query=models.SparseVector(indices=[1, 42], values=[0.22, 0.8]),
            using="sparse",
            limit=20,
        ),
        models.Prefetch(
            query=[0.05, 0.61, 0.76, 0.74] + [0.0] * 764,
            using="dense",
            limit=20,
        ),
    ],
    query=models.RrfQuery(
        rrf=models.Rrf(
            weights=[1.0, 3.0],  # weight dense 3x more than sparse
        )
    ),
    limit=10,
)
```

### DBSF — Distribution-Based Score Fusion (v1.11.0+)

Normalizes scores using statistical distribution (mean ± 3 std devs) before summing. Better when you want to respect score magnitudes.

```python
results = client.query_points(
    collection_name="hybrid",
    prefetch=[
        models.Prefetch(
            query=models.SparseVector(indices=[1, 42], values=[0.22, 0.8]),
            using="sparse",
            limit=20,
        ),
        models.Prefetch(
            query=[0.05, 0.61, 0.76, 0.74] + [0.0] * 764,
            using="dense",
            limit=20,
        ),
    ],
    query=models.FusionQuery(fusion=models.Fusion.DBSF),
    limit=10,
)
```

### Choosing a Fusion Method

| Method | Best For | Notes |
|--------|----------|-------|
| RRF | General hybrid search | Rank-based, ignores score scale |
| Weighted RRF | Tuning relative importance | v1.17.0+, per-prefetch weights |
| DBSF | Score-aware fusion | Normalizes distributions, respects magnitude |

## Multi-Stage Retrieval

Use coarse-to-fine search for large collections — first search with smaller/faster vectors, then re-rank with full-precision vectors.

### Two-Stage: Byte → Full Precision

```python
results = client.query_points(
    collection_name="my_collection",
    prefetch=models.Prefetch(
        query=[1, 23, 45, 67],    # byte-quantized vector
        using="mrl_byte",
        limit=1000,               # cast wide net
    ),
    query=[0.01, 0.299, 0.45, 0.67],  # full-precision vector
    using="full",
    limit=10,                     # final results
)
```

### Three-Stage: Byte → Medium → Full

```python
results = client.query_points(
    collection_name="my_collection",
    prefetch=models.Prefetch(
        prefetch=models.Prefetch(
            query=[1, 23, 45, 67],      # coarsest (byte)
            using="mrl_byte",
            limit=1000,
        ),
        query=[0.01, 0.45, 0.67],      # medium precision
        using="medium",
        limit=100,
    ),
    query=[0.01, 0.299, 0.45, 0.67],   # full precision
    using="full",
    limit=10,
)
```

### ColBERT-Style Late Interaction

```python
results = client.query_points(
    collection_name="my_collection",
    prefetch=models.Prefetch(
        query=[0.01, 0.45, 0.67],
        using="dense",
        limit=100,
    ),
    query=[                    # multi-vector query
        [0.17, 0.23, 0.52],
        [0.22, 0.11, 0.63],
        [0.86, 0.93, 0.12],
    ],
    using="colbert",
    limit=10,
)
```

## Prefetch with Filters

Each prefetch can have its own filter:

```python
results = client.query_points(
    collection_name="hybrid",
    prefetch=[
        models.Prefetch(
            query=models.SparseVector(indices=[1, 42], values=[0.22, 0.8]),
            using="sparse",
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="category",
                        match=models.MatchValue(value="technical"),
                    )
                ]
            ),
            limit=20,
        ),
        models.Prefetch(
            query=[0.05, 0.61, 0.76, 0.74] + [0.0] * 764,
            using="dense",
            limit=20,
        ),
    ],
    query=models.FusionQuery(fusion=models.Fusion.RRF),
    query_filter=models.Filter(  # additional filter on final results
        must=[
            models.FieldCondition(
                key="active", match=models.MatchValue(value=True),
            )
        ]
    ),
    limit=10,
)
```

## REST API Example

```http
POST /collections/hybrid/points/query
{
    "prefetch": [
        {
            "query": {"indices": [1, 42], "values": [0.22, 0.8]},
            "using": "sparse",
            "limit": 20
        },
        {
            "query": [0.05, 0.61, 0.76, 0.74],
            "using": "dense",
            "limit": 20
        }
    ],
    "query": {"fusion": "rrf"},
    "limit": 10
}
```

## Common Pitfalls

1. **Prefetch limit** — Set prefetch `limit` higher than final `limit`. A good ratio is 2-4x the final limit.
2. **offset in prefetch** — The `offset` parameter is ignored in prefetch queries. It only applies to the main query.
3. **Score interpretation** — Fusion scores are synthetic (rank-based for RRF, normalized for DBSF). Don't compare across queries.
4. **IDF modifier** — Enable `modifier=Modifier.IDF` on sparse vectors for automatic term weighting. Without it, all terms are weighted equally.
5. **Sparse vector distance** — Sparse vectors always use dot product distance. No distance parameter is needed or allowed.
6. **Nested prefetch depth** — Prefetches can be nested arbitrarily deep, but each level adds latency. 2-3 levels is practical maximum.

## Related Topics

- Search & Query API → `references/03-search-query.md`
- Recommendation → `references/08-recommendation.md`
- Indexing → `references/05-indexing.md`
