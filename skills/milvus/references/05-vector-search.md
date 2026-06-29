# Milvus — Vector Search

> Source: [milvus.io/docs/single-vector-search.md](https://milvus.io/docs/single-vector-search.md) | Version: 3.0-beta

## Table of Contents

- [Basic Search](#basic-search)
- [Bulk Search](#bulk-search-multiple-queries)
- [Filtered Search](#filtered-search)
- [Search Parameters](#search-parameters)
- [Pagination](#pagination-offset--limit)
- [Search Iterators](#search-iterators-beyond-16k-results)
- [Range Search](#range-search)
- [Grouping Search](#grouping-search)
- [Order By](#order-by-v30)
- [Common Pitfalls](#common-pitfalls)

## Overview

Milvus performs Approximate Nearest Neighbor (ANN) search to find vectors most similar to a query. The search uses pre-built indexes and distance metrics to efficiently scan collections and return the top-K most similar entities.

## Basic Search

```python
from pymilvus import MilvusClient

client = MilvusClient(uri="http://localhost:19530", token="root:Milvus")

query_vector = [0.358, -0.602, 0.184, -0.262, 0.902]

results = client.search(
    collection_name="articles",
    data=[query_vector],
    anns_field="embedding",  # which vector field to search (required if multiple)
    limit=5,
    search_params={"metric_type": "COSINE"},
)

for hits in results:
    for hit in hits:
        print(f"id={hit['id']}, distance={hit['distance']:.4f}")
```

## Bulk Search (Multiple Queries)

```python
query_vectors = [
    [0.1, 0.2, 0.3, 0.4, 0.5],
    [0.5, 0.4, 0.3, 0.2, 0.1],
    [0.3, 0.3, 0.3, 0.3, 0.3],
]

results = client.search(
    collection_name="articles",
    data=query_vectors,
    limit=3,
)

# results[0] = hits for query_vectors[0]
# results[1] = hits for query_vectors[1]
# results[2] = hits for query_vectors[2]
```

## Filtered Search

Combine vector similarity with scalar predicates:

```python
results = client.search(
    collection_name="articles",
    data=[query_vector],
    filter="category == 'tech' and score > 0.8",
    limit=10,
    output_fields=["title", "category", "score"],
)
```

Filter is evaluated before or during the ANN search (depending on the index type), narrowing the candidate set.

### Common Filter Patterns

```python
# Equality
filter="status == 'published'"

# Range
filter="price >= 10 and price <= 100"

# Membership
filter="category in ['tech', 'science', 'ai']"

# Pattern matching
filter="title like 'Introduction%'"

# Logical combination
filter="(category == 'tech' or category == 'science') and year >= 2024"

# JSON field
filter='metadata["source"] == "arxiv"'

# Array contains
filter="array_contains(tags, 'machine-learning')"

# NULL check
filter="description is not null"
```

## Output Fields

Return scalar metadata alongside search results:

```python
results = client.search(
    collection_name="articles",
    data=[query_vector],
    limit=5,
    output_fields=["title", "category", "score", "metadata"],
)

for hits in results:
    for hit in hits:
        print(f"id={hit['id']}, title={hit['entity']['title']}, dist={hit['distance']:.4f}")
```

## Search Parameters

Fine-tune search behavior per-query:

```python
results = client.search(
    collection_name="articles",
    data=[query_vector],
    limit=10,
    search_params={
        "metric_type": "COSINE",
        "params": {
            "ef": 128,           # HNSW search width (higher = better recall)
            # "nprobe": 16,      # IVF cluster probe count
            # "search_list": 64, # DiskANN candidate list
        },
    },
)
```

### Parameters by Index Type

| Index | Parameter | Range | Effect |
|-------|-----------|-------|--------|
| HNSW | `ef` | ≥ limit | Search beam width |
| IVF_FLAT | `nprobe` | 1–nlist | Clusters to search |
| IVF_SQ8 | `nprobe` | 1–nlist | Clusters to search |
| IVF_PQ | `nprobe` | 1–nlist | Clusters to search |
| DiskANN | `search_list` | > limit | Candidate list size |

## Pagination (Offset + Limit)

```python
# Page 1
page1 = client.search(
    collection_name="articles",
    data=[query_vector],
    limit=10,
    search_params={"metric_type": "COSINE", "offset": 0},
)

# Page 2
page2 = client.search(
    collection_name="articles",
    data=[query_vector],
    limit=10,
    search_params={"metric_type": "COSINE", "offset": 10},
)
```

**Constraint:** `limit + offset` must be < 16,384.

## Search Iterators (Beyond 16K Results)

For retrieving more than 16,384 results:

```python
from pymilvus import Collection

collection = Collection("articles")
collection.load()

iterator = collection.search_iterator(
    data=[query_vector],
    anns_field="embedding",
    param={"metric_type": "COSINE", "params": {"ef": 128}},
    limit=1000,
    output_fields=["title"],
)

all_results = []
while True:
    batch = iterator.next()
    if not batch:
        break
    all_results.extend(batch)

iterator.close()
```

## Range Search

Return results within a specific distance range:

```python
results = client.search(
    collection_name="articles",
    data=[query_vector],
    limit=100,
    search_params={
        "metric_type": "COSINE",
        "params": {
            "radius": 0.5,        # minimum distance threshold
            "range_filter": 0.9,  # maximum distance threshold
        },
    },
)
```

For COSINE/IP (higher = more similar): `radius` < `range_filter` — returns results between radius and range_filter.

For L2 (lower = more similar): `radius` > `range_filter` — returns results between range_filter and radius.

## Partition Search

Restrict search to specific partitions for performance:

```python
results = client.search(
    collection_name="articles",
    partition_names=["tech", "science"],
    data=[query_vector],
    limit=10,
)
```

## Primary-Key Search (v2.6.9+)

Search using existing entity vectors by their IDs:

```python
results = client.search(
    collection_name="articles",
    anns_field="embedding",
    ids=[101, 202, 303],  # use these entities' vectors as queries
    limit=5,
    search_params={"metric_type": "COSINE"},
)
```

## Grouping Search

Deduplicate results by a scalar field:

```python
results = client.search(
    collection_name="articles",
    data=[query_vector],
    limit=10,
    group_by_field="category",  # max 1 result per category
    output_fields=["title", "category"],
)
```

## Order By (v3.0+)

Sort results by scalar fields after vector similarity:

```python
results = client.search(
    collection_name="products",
    data=[query_vector],
    limit=20,
    order_by_fields=[
        {"field": "price", "order": "asc"},
        {"field": "rating", "order": "desc"},
    ],
)
```

## Metric Type Interpretation

| Metric | Distance Meaning | Score Ordering |
|--------|-----------------|----------------|
| L2 | Euclidean distance squared | Lower = more similar |
| IP | Inner product | Higher = more similar |
| COSINE | Cosine similarity | Higher = more similar |
| JACCARD | Jaccard distance | Lower = more similar |
| HAMMING | Hamming distance | Lower = more similar |

## Complete Search Example

```python
from pymilvus import MilvusClient
import numpy as np

client = MilvusClient(uri="http://localhost:19530", token="root:Milvus")

query = np.random.rand(768).tolist()

results = client.search(
    collection_name="documents",
    data=[query],
    anns_field="embedding",
    filter="category in ['tech', 'ai'] and year >= 2024",
    limit=20,
    search_params={
        "metric_type": "COSINE",
        "params": {"ef": 256},
    },
    output_fields=["title", "category", "year", "score"],
    consistency_level="Session",
)

for hits in results:
    for rank, hit in enumerate(hits, 1):
        print(f"#{rank} id={hit['id']} dist={hit['distance']:.4f} "
              f"title={hit['entity']['title']}")
```

## Common Pitfalls

- **Not specifying `anns_field`** — required when collection has multiple vector fields
- **Mismatched `metric_type`** — search metric must match the index metric
- **Pagination exceeding 16,384** — use search iterators instead
- **Setting `ef` too low** — returns poor recall; set `ef` ≥ 2× limit for good results
- **Searching unloaded collections** — always `load_collection()` first
- **Expecting exact results** — ANN search is approximate; use FLAT index for exact matching
