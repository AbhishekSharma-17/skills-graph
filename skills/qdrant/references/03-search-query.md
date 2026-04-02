# Qdrant — Search & Query API

> Source: [qdrant.tech/documentation/concepts/search](https://qdrant.tech/documentation/concepts/search/) | v1.17.1

## Table of Contents

- [Overview](#overview)
- [Universal Query API](#universal-query-api)
- [Search Parameters](#search-parameters)
- [Payload Selection](#payload-selection)
- [Search Groups](#search-groups)
- [Random Sampling](#random-sampling)
- [Order by Payload](#order-by-payload)
- [Batch Search](#batch-search)
- [Legacy Search API](#legacy-search-api)
- [Common Pitfalls](#common-pitfalls)

## Overview

Qdrant provides two search APIs:
- **`query_points`** (recommended) — Universal endpoint supporting all query types
- **`search`** (legacy) — Original search endpoint, still functional

Always prefer `query_points` for new code — it supports vector search, recommendations, discovery, fusion, ordering, and sampling through a single interface.

## Universal Query API

### Basic Vector Search

```python
from qdrant_client import QdrantClient, models

client = QdrantClient("localhost", port=6333)

results = client.query_points(
    collection_name="my_collection",
    query=[0.2, 0.1, 0.9, 0.7],  # query vector
    limit=10,
    with_payload=True,
    with_vectors=False,
)

for point in results.points:
    print(f"ID: {point.id}, Score: {point.score:.4f}")
    print(f"  Payload: {point.payload}")
```

**REST equivalent:**
```http
POST /collections/my_collection/points/query
{
    "query": [0.2, 0.1, 0.9, 0.7],
    "limit": 10,
    "with_payload": true
}
```

### Search with Named Vector

```python
results = client.query_points(
    collection_name="multi_vec",
    query=[0.2, 0.1, 0.9, 0.7],
    using="dense",           # specify which named vector to search
    limit=10,
)
```

### Search with Filter

```python
results = client.query_points(
    collection_name="my_collection",
    query=[0.2, 0.1, 0.9, 0.7],
    query_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="category",
                match=models.MatchValue(value="tutorial"),
            ),
            models.FieldCondition(
                key="rating",
                range=models.Range(gte=4.0),
            ),
        ]
    ),
    limit=10,
)
```

### Search with Score Threshold

```python
results = client.query_points(
    collection_name="my_collection",
    query=[0.2, 0.1, 0.9, 0.7],
    score_threshold=0.5,  # only return points with score >= 0.5
    limit=10,
)
```

### Search by Point ID

Use an existing point's vector as the query:

```python
results = client.query_points(
    collection_name="my_collection",
    query=42,  # point ID — uses this point's vector as query
    limit=10,
)
```

## Search Parameters

Fine-tune search accuracy vs speed:

```python
results = client.query_points(
    collection_name="my_collection",
    query=[0.2, 0.1, 0.9, 0.7],
    search_params=models.SearchParams(
        hnsw_ef=128,       # beam size: higher = more accurate, slower
                           # default: ef_construct value from collection config
        exact=False,       # True for brute-force exact search (slow but precise)
        indexed_only=False, # True to only search indexed segments
        quantization=models.QuantizationSearchParams(
            ignore=False,      # False = use quantized vectors (fast)
            rescore=True,      # re-score top results with original vectors
            oversampling=2.0,  # fetch 2x candidates before rescoring
        ),
    ),
    limit=10,
)
```

**Key parameters:**
| Parameter | Default | Effect |
|-----------|---------|--------|
| `hnsw_ef` | `ef_construct` | Higher = more accurate, slower |
| `exact` | `False` | Brute-force search, 100% recall |
| `rescore` | `True` (if quantized) | Re-rank with full precision vectors |
| `oversampling` | `1.0` | Multiplier for candidates before rescoring |

### ACORN Search (v1.16.0+)

For multi-condition filters where standard HNSW struggles:

```python
search_params=models.SearchParams(
    acorn=True,  # second-hop exploration for strict filters
)
```

## Payload Selection

Control which payload fields are returned:

```python
# Specific fields only
results = client.query_points(
    collection_name="my_collection",
    query=[0.2, 0.1, 0.9, 0.7],
    with_payload=["title", "category"],  # include only these fields
    limit=10,
)

# Exclude specific fields
results = client.query_points(
    collection_name="my_collection",
    query=[0.2, 0.1, 0.9, 0.7],
    with_payload=models.PayloadSelectorExclude(exclude=["embedding_text"]),
    limit=10,
)

# No payload
results = client.query_points(
    collection_name="my_collection",
    query=[0.2, 0.1, 0.9, 0.7],
    with_payload=False,
    limit=10,
)
```

## Search Groups

Group results by a payload field — useful for deduplication:

```python
results = client.query_points_groups(
    collection_name="my_collection",
    query=[0.2, 0.1, 0.9, 0.7],
    group_by="document_id",   # payload field to group by
    limit=4,                  # number of groups
    group_size=2,             # results per group
    with_payload=True,
)

for group in results.groups:
    print(f"Group: {group.id}")
    for point in group.hits:
        print(f"  ID: {point.id}, Score: {point.score:.4f}")
```

**Use case:** When chunked documents produce multiple points per document, group by `document_id` to get the best chunk per document.

## Random Sampling

Return random points (no vector needed):

```python
results = client.query_points(
    collection_name="my_collection",
    query=models.SampleQuery(sample=models.Sample.RANDOM),
    limit=5,
)
```

## Order by Payload

Sort by payload field value without vector similarity:

```python
results = client.query_points(
    collection_name="my_collection",
    query=models.OrderByQuery(
        order_by=models.OrderBy(
            key="timestamp",
            direction=models.Direction.DESC,  # ASC or DESC
        )
    ),
    limit=10,
)
```

## Batch Search

Search multiple queries in a single request:

```python
results = client.query_batch_points(
    collection_name="my_collection",
    requests=[
        models.QueryRequest(
            query=[0.2, 0.1, 0.9, 0.7],
            limit=5,
            with_payload=True,
        ),
        models.QueryRequest(
            query=[0.8, 0.3, 0.1, 0.5],
            limit=5,
            with_payload=True,
        ),
    ],
)

for i, batch in enumerate(results):
    print(f"Query {i}: {len(batch.points)} results")
```

**REST:**
```http
POST /collections/my_collection/points/query/batch
{
    "searches": [
        { "query": [0.2, 0.1, 0.9, 0.7], "limit": 5 },
        { "query": [0.8, 0.3, 0.1, 0.5], "limit": 5 }
    ]
}
```

## Legacy Search API

The older `search` method still works but has fewer features:

```python
results = client.search(
    collection_name="my_collection",
    query_vector=[0.2, 0.1, 0.9, 0.7],
    query_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="category",
                match=models.MatchValue(value="tutorial"),
            )
        ]
    ),
    limit=5,
    with_payload=True,
)
```

**Prefer `query_points` for all new code.**

## Consistency Levels

For distributed deployments, control read consistency:

```python
results = client.query_points(
    collection_name="my_collection",
    query=[0.2, 0.1, 0.9, 0.7],
    consistency=models.ReadConsistency(
        type=models.ReadConsistencyType.MAJORITY,  # MAJORITY, QUORUM, ALL
    ),
    limit=10,
)
```

## Common Pitfalls

1. **Use `query_points` not `search`** — The universal query API supports all query types and is the recommended endpoint.
2. **hnsw_ef tuning** — Default ef equals `ef_construct`. For production, test increasing `hnsw_ef` at query time for better recall.
3. **Below ~10,000 points** — Brute-force (`exact=True`) is often faster than HNSW. The index needs sufficient data to be beneficial.
4. **offset performance** — Large `offset` values are expensive (all preceding results are still computed). Use scroll for iteration.
5. **Score interpretation** — Scores depend on the distance metric. Cosine: higher is better (0-2 range); Euclid: lower is better.
6. **Timeout** — Set `timeout=30` (seconds) for large collections to avoid request timeouts.

## Related Topics

- Filtering → `references/04-filtering.md`
- Hybrid search → `references/07-hybrid-search.md`
- Recommendation → `references/08-recommendation.md`
