# Qdrant — Points (Vectors & Payloads)

> Source: [qdrant.tech/documentation/concepts/points](https://qdrant.tech/documentation/concepts/points/) | v1.17.1

## Overview

A **point** is the fundamental data unit in Qdrant, consisting of:
- **ID** — Unique identifier (unsigned 64-bit integer or UUID string)
- **Vector(s)** — One or more embedding vectors (dense and/or sparse)
- **Payload** — Optional JSON metadata for filtering and storage

## Upserting Points

### Basic Upsert

```python
from qdrant_client import QdrantClient, models

client = QdrantClient("localhost", port=6333)

client.upsert(
    collection_name="my_collection",
    wait=True,  # block until operation completes
    points=[
        models.PointStruct(
            id=1,
            vector=[0.05, 0.61, 0.76, 0.74],
            payload={"city": "Berlin", "country": "Germany", "population": 3748148},
        ),
        models.PointStruct(
            id="550e8400-e29b-41d4-a716-446655440000",  # UUID ID
            vector=[0.36, 0.55, 0.47, 0.94],
            payload={"city": "Moscow", "country": "Russia"},
        ),
    ],
)
```

**REST equivalent:**
```http
PUT /collections/my_collection/points
{
    "points": [
        {
            "id": 1,
            "vector": [0.05, 0.61, 0.76, 0.74],
            "payload": {"city": "Berlin", "country": "Germany"}
        }
    ]
}
```

### Upsert with Named Vectors

```python
client.upsert(
    collection_name="multi_vec",
    points=[
        models.PointStruct(
            id=1,
            vector={
                "dense": [0.05, 0.61, 0.76, 0.74],
                "sparse": models.SparseVector(
                    indices=[1, 42, 103],
                    values=[0.22, 0.8, 0.51],
                ),
            },
            payload={"title": "Introduction to Qdrant"},
        ),
    ],
)
```

### The `wait` Parameter

- `wait=True` — Request blocks until write is confirmed on disk (WAL). Safer.
- `wait=False` (default) — Returns immediately; write happens asynchronously. Faster throughput.

Use `wait=True` for critical writes where you need confirmation. Use `wait=False` for bulk ingestion.

## Point ID Types

```python
# Integer IDs (unsigned 64-bit)
models.PointStruct(id=1, vector=[...], payload={})
models.PointStruct(id=18446744073709551615, vector=[...], payload={})  # max uint64

# UUID string IDs
models.PointStruct(id="550e8400-e29b-41d4-a716-446655440000", vector=[...], payload={})
```

**Important:** Do not mix integer and UUID IDs within the same collection. Pick one type and stick with it.

## Payload Data Types

Qdrant supports any valid JSON as payload:

```python
payload = {
    "name": "Example",                           # string
    "count": 42,                                  # integer
    "score": 0.95,                                # float
    "active": True,                               # boolean
    "tags": ["search", "ai"],                     # array of strings
    "nested": {"key": "value", "deep": {"a": 1}}, # nested object
    "nullable": None,                             # null
    "location": {"lat": 52.52, "lon": 13.405},   # geo point
    "created_at": "2024-01-15T10:30:00Z",         # datetime (RFC 3339)
}
```

## Retrieving Points

### Get Points by ID

```python
points = client.get_points(
    collection_name="my_collection",
    ids=[1, 2, 3],
    with_payload=True,
    with_vectors=True,
)

for point in points:
    print(f"ID: {point.id}, Payload: {point.payload}")
```

**REST:**
```http
POST /collections/my_collection/points
{
    "ids": [1, 2, 3],
    "with_payload": true,
    "with_vector": true
}
```

### Scroll (Pagination)

For iterating over large datasets without vector similarity:

```python
result, next_offset = client.scroll(
    collection_name="my_collection",
    scroll_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="country",
                match=models.MatchValue(value="Germany"),
            )
        ]
    ),
    limit=100,
    offset=None,       # pass next_offset from previous call
    with_payload=True,
    with_vectors=False,
    order_by="created_at",  # optional ordering (v1.8.0+)
)

# Iterate through all pages
while next_offset is not None:
    result, next_offset = client.scroll(
        collection_name="my_collection",
        limit=100,
        offset=next_offset,
    )
    # process result
```

### Count Points

```python
count = client.count(
    collection_name="my_collection",
    count_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="country",
                match=models.MatchValue(value="Germany"),
            )
        ]
    ),
    exact=True,  # exact count (slower) vs approximate
)
print(f"Matching points: {count.count}")
```

## Deleting Points

### Delete by IDs

```python
client.delete(
    collection_name="my_collection",
    points_selector=models.PointIdsList(
        points=[1, 2, 3],
    ),
)
```

### Delete by Filter

```python
client.delete(
    collection_name="my_collection",
    points_selector=models.FilterSelector(
        filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="country",
                    match=models.MatchValue(value="Germany"),
                )
            ]
        )
    ),
)
```

**REST:**
```http
POST /collections/my_collection/points/delete
{
    "filter": {
        "must": [
            {"key": "country", "match": {"value": "Germany"}}
        ]
    }
}
```

## Updating Payloads

### Set Payload (Add/Update Fields)

```python
client.set_payload(
    collection_name="my_collection",
    payload={"category": "travel", "rating": 4.5},
    points=[1, 2, 3],
    wait=True,
)
```

Also supports filter-based targeting:

```python
client.set_payload(
    collection_name="my_collection",
    payload={"reviewed": True},
    points=models.FilterSelector(
        filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="status", match=models.MatchValue(value="pending"),
                )
            ]
        )
    ),
)
```

### Overwrite Payload (Replace Entire Payload)

```python
client.overwrite_payload(
    collection_name="my_collection",
    payload={"new_field": "value"},  # replaces ALL existing payload
    points=[1, 2],
)
```

### Delete Payload Keys

```python
client.delete_payload(
    collection_name="my_collection",
    keys=["city", "rating"],  # remove specific keys
    points=[1, 2],
)
```

### Clear All Payload

```python
client.clear_payload(
    collection_name="my_collection",
    points_selector=models.PointIdsList(points=[1, 2]),
)
```

## Batch Operations

### Batch Upsert (Large Datasets)

For large datasets, use batched uploads:

```python
# Using the built-in upload method
client.upload_points(
    collection_name="my_collection",
    points=[
        models.PointStruct(id=i, vector=vectors[i], payload=payloads[i])
        for i in range(len(vectors))
    ],
    batch_size=256,    # points per batch
    parallel=4,        # concurrent upload threads
)
```

### Upload from Iterables

```python
client.upload_collection(
    collection_name="my_collection",
    vectors=vectors_iterable,     # iterable of vectors
    payload=payloads_iterable,    # iterable of payloads
    ids=ids_iterable,             # iterable of IDs
    batch_size=256,
    parallel=4,
)
```

## Common Pitfalls

1. **Mixing ID types** — Never mix integer and UUID IDs in the same collection. Qdrant will accept both but behavior may be unpredictable.
2. **Payload size** — Large payloads increase memory usage. Use `on_disk_payload=True` on the collection for large text fields.
3. **wait=False gotcha** — If you upsert with `wait=False` and immediately search, the point may not be visible yet.
4. **Upsert is idempotent** — Upserting the same ID replaces the existing point entirely (vector + payload).
5. **Vector dimensions** — All vectors must match the `size` specified in the collection's vector config.

## Related Topics

- Collections → `references/01-collections.md`
- Search & Query API → `references/03-search-query.md`
- Filtering → `references/04-filtering.md`
