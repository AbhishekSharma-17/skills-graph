# Milvus — Collections

> Source: [milvus.io/docs/manage-collections.md](https://milvus.io/docs/manage-collections.md) | Version: 3.0-beta

## Overview

A collection is the primary data container in Milvus — analogous to a table in a relational database. Each collection has a fixed schema of typed fields and stores entities (rows) as vectors with metadata. Collections must be loaded into memory before they can be searched.

## Creating Collections

### Quick Creation (Auto-Schema)

```python
from pymilvus import MilvusClient

client = MilvusClient("./demo.db")

# Minimal — just specify name and dimension
client.create_collection(
    collection_name="articles",
    dimension=768,
)
```

Auto-schema creates: `id` (INT64, primary, auto_id), `vector` (FLOAT_VECTOR), plus a dynamic field for metadata. The collection is automatically loaded.

### Custom Schema Creation

```python
from pymilvus import MilvusClient, DataType

client = MilvusClient(uri="http://localhost:19530", token="root:Milvus")
schema = client.create_schema()

schema.add_field("doc_id", DataType.INT64, is_primary=True, auto_id=True)
schema.add_field("embedding", DataType.FLOAT_VECTOR, dim=768)
schema.add_field("title", DataType.VARCHAR, max_length=512)
schema.add_field("category", DataType.VARCHAR, max_length=64)

# Prepare index parameters
index_params = client.prepare_index_params()
index_params.add_index(field_name="embedding", index_type="HNSW", metric_type="COSINE",
                       params={"M": 16, "efConstruction": 256})
index_params.add_index(field_name="category", index_type="Trie")

# Create with schema and index
client.create_collection(
    collection_name="documents",
    schema=schema,
    index_params=index_params,
)
```

### Collection Parameters

```python
client.create_collection(
    collection_name="my_collection",
    schema=schema,
    index_params=index_params,
    num_shards=2,                    # write throughput parallelism (default: 1)
    consistency_level="Session",     # Strong | Bounded | Session | Eventually
)
```

## Listing Collections

```python
collections = client.list_collections()
# ['articles', 'documents']
```

## Describing Collections

```python
info = client.describe_collection(collection_name="documents")
# Returns: collection_name, schema, num_shards, consistency_level, etc.
```

## Checking Existence

```python
exists = client.has_collection(collection_name="documents")
# True
```

## Loading and Releasing

Collections must be loaded into memory before search/query operations.

### Load a Collection

```python
client.load_collection(collection_name="documents")
```

### Load Specific Partitions

```python
client.load_partitions(
    collection_name="documents",
    partition_names=["partition_a", "partition_b"],
)
```

### Release (Free Memory)

```python
client.release_collection(collection_name="documents")
```

Release unused collections to free memory for other workloads. Released collections cannot be searched until loaded again.

## Dropping Collections

```python
client.drop_collection(collection_name="documents")
```

This permanently deletes all data. No confirmation prompt — use carefully.

## Collection Aliases

Aliases let you reference a collection by multiple names — useful for zero-downtime reindexing.

### Create an Alias

```python
client.create_alias(
    collection_name="documents_v2",
    alias="documents",
)
```

### List Aliases

```python
aliases = client.list_aliases(collection_name="documents_v2")
```

### Reassign an Alias

```python
client.alter_alias(
    collection_name="documents_v3",
    alias="documents",
)
```

### Drop an Alias

```python
client.drop_alias(alias="documents")
```

**Pattern — Blue-Green Reindexing:**
1. Create `articles_v2` with new schema/index
2. Populate `articles_v2`
3. `alter_alias(collection_name="articles_v2", alias="articles")`
4. Drop `articles_v1`

## Consistency Levels

Set at collection creation or per-search:

```python
# At creation
client.create_collection(
    collection_name="orders",
    schema=schema,
    index_params=index_params,
    consistency_level="Strong",
)

# Per-search override
results = client.search(
    collection_name="orders",
    data=[query_vector],
    limit=10,
    consistency_level="Eventually",  # override for this query
)
```

| Level | Behavior | Latency |
|-------|----------|---------|
| `Strong` | All writes visible before read returns | Highest |
| `Bounded` | Writes visible within configurable staleness window | Medium |
| `Session` | Client sees its own writes immediately | Low |
| `Eventually` | No freshness guarantee | Lowest |

## Shards

Shards distribute write operations across nodes for throughput:

```python
client.create_collection(
    collection_name="high_throughput",
    schema=schema,
    index_params=index_params,
    num_shards=4,  # parallel write channels
)
```

Guidelines:
- Default `num_shards=1` is fine for most workloads
- Increase shards when write throughput is the bottleneck
- More shards = more parallel writes but higher coordination overhead
- Cannot be changed after creation — plan ahead

## Collection Renaming

```python
client.rename_collection(
    old_name="old_collection",
    new_name="new_collection",
)
```

## Getting Collection Statistics

```python
stats = client.get_collection_stats(collection_name="documents")
# Returns entity count, storage size
```

## Common Pitfalls

- **Searching an unloaded collection** — raises an error; always `load_collection()` first
- **Forgetting to create indexes** — vector fields require an index before loading
- **Setting too many shards** — increases coordination overhead; start with 1-2
- **Not releasing unused collections** — wastes memory that could serve active workloads
- **Dropping instead of releasing** — `drop_collection` deletes data permanently; use `release_collection` to just free memory
