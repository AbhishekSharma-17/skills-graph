# Milvus — Data Operations

> Source: [milvus.io/docs/insert-update-delete.md](https://milvus.io/docs/insert-update-delete.md) | Version: 3.0-beta

## Overview

Milvus supports four core data operations: **insert** (add new entities), **upsert** (insert or update), **delete** (remove entities), and **query** (retrieve by filter). Data is organized as entities — dictionaries matching the collection schema.

## Insert

### Basic Insert

```python
from pymilvus import MilvusClient

client = MilvusClient("./demo.db")

data = [
    {"id": 1, "vector": [0.1, 0.2, 0.3, 0.4, 0.5], "title": "Doc A", "category": "tech"},
    {"id": 2, "vector": [0.5, 0.4, 0.3, 0.2, 0.1], "title": "Doc B", "category": "science"},
    {"id": 3, "vector": [0.3, 0.1, 0.4, 0.5, 0.2], "title": "Doc C", "category": "tech"},
]

res = client.insert(collection_name="articles", data=data)
print(res)
# {'insert_count': 3, 'ids': [1, 2, 3]}
```

### Insert with Auto-ID

When `auto_id=True`, omit the primary key field:

```python
data = [
    {"vector": [0.1, 0.2, 0.3, 0.4, 0.5], "title": "Doc A"},
    {"vector": [0.5, 0.4, 0.3, 0.2, 0.1], "title": "Doc B"},
]

res = client.insert(collection_name="articles", data=data)
# Milvus generates IDs automatically
print(res["ids"])  # [449208390848498385, 449208390848498386]
```

### Insert into a Partition

```python
res = client.insert(
    collection_name="articles",
    partition_name="tech_docs",
    data=data,
)
```

### Batch Insert (Large Datasets)

For large datasets, insert in batches of 1,000–10,000 entities:

```python
import numpy as np

batch_size = 5000
total = 100_000
dim = 768

for i in range(0, total, batch_size):
    batch = [
        {
            "vector": np.random.rand(dim).tolist(),
            "title": f"Document {j}",
            "category": "batch",
        }
        for j in range(i, min(i + batch_size, total))
    ]
    client.insert(collection_name="articles", data=batch)
    print(f"Inserted {min(i + batch_size, total)}/{total}")
```

### Insert with Dynamic Fields

When `enable_dynamic_field=True`, include any extra fields:

```python
data = [
    {
        "id": 1,
        "vector": [0.1, 0.2, 0.3],
        "title": "Doc A",
        "author": "Alice",       # dynamic field — not in schema
        "year": 2024,            # dynamic field
        "tags": ["ml", "ai"],    # dynamic field
    },
]

client.insert(collection_name="articles", data=data)
```

Dynamic fields are stored internally in a `$meta` JSON column and are queryable.

## Upsert

Upsert inserts new entities or updates existing ones (matched by primary key):

```python
data = [
    {"id": 1, "vector": [0.11, 0.22, 0.33, 0.44, 0.55], "title": "Doc A Updated", "category": "tech"},
    {"id": 4, "vector": [0.9, 0.8, 0.7, 0.6, 0.5], "title": "Doc D New", "category": "art"},
]

res = client.upsert(collection_name="articles", data=data)
print(res)
# {'upsert_count': 2}
```

**Important:** Upsert is a delete-then-insert operation internally. It is more expensive than plain insert. Use `insert` when you know entities are new.

## Delete

### Delete by IDs

```python
res = client.delete(
    collection_name="articles",
    ids=[1, 2, 3],
)
print(res)
# {'delete_count': 3}
```

### Delete by Filter

```python
res = client.delete(
    collection_name="articles",
    filter="category == 'tech' and score < 0.5",
)
```

### Delete from a Partition

```python
res = client.delete(
    collection_name="articles",
    partition_name="tech_docs",
    ids=[1, 2],
)
```

## Query (Scalar Retrieval)

Query retrieves entities by filter expression without vector similarity:

```python
results = client.query(
    collection_name="articles",
    filter="category == 'tech'",
    output_fields=["title", "category", "score"],
    limit=100,
)

for entity in results:
    print(entity)
```

### Query by IDs

```python
results = client.query(
    collection_name="articles",
    ids=[1, 2, 3],
    output_fields=["title", "category"],
)
```

### Query with Offset (Pagination)

```python
results = client.query(
    collection_name="articles",
    filter="category == 'tech'",
    output_fields=["title"],
    limit=10,
    offset=20,  # skip first 20 results
)
```

### Count Entities

```python
results = client.query(
    collection_name="articles",
    filter="",
    output_fields=["count(*)"],
)
total = results[0]["count(*)"]
```

## Query Aggregation (v3.0+)

Server-side aggregation for analytics:

```python
results = client.query(
    collection_name="products",
    filter="category == 'electronics'",
    output_fields=["count(*)", "sum(price)", "avg(rating)", "min(price)", "max(price)"],
)
```

## Get (by Primary Key)

```python
results = client.get(
    collection_name="articles",
    ids=[1, 2],
    output_fields=["title", "category"],
)
```

## Data Import (Bulk Insert)

For very large datasets (millions of entities), use bulk import from files:

```python
from pymilvus.bulk_writer import LocalBulkWriter, BulkFileType

writer = LocalBulkWriter(
    schema=schema,
    local_path="./bulk_data",
    file_type=BulkFileType.JSON_RB,
)

for i in range(1_000_000):
    writer.append_row({
        "vector": np.random.rand(768).tolist(),
        "title": f"Document {i}",
    })

writer.commit()

# Import files
client.bulk_import(
    collection_name="articles",
    files=writer.batch_files,
)
```

## Common Pitfalls

- **Insert without index** — data inserts succeed, but search fails until an index is created and the collection is loaded
- **Using insert when upsert is needed** — `insert` does NOT check for duplicate primary keys; duplicates cause undefined behavior
- **Deleting without filter or IDs** — at least one must be specified
- **Large single inserts** — inserting millions in one call can timeout; batch into 5K-10K chunks
- **Forgetting `output_fields` in query** — returns only IDs by default
- **Not accounting for eventual consistency** — recently inserted data may not appear in queries immediately if using `Eventually` consistency
