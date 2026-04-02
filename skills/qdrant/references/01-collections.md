# Qdrant — Collections

> Source: [qdrant.tech/documentation/concepts/collections](https://qdrant.tech/documentation/concepts/collections/) | v1.17.1

## Overview

A **collection** is a named set of points (vectors + payloads) that share the same vector configuration. Collections are the primary organizational unit in Qdrant — similar to tables in relational databases.

## Creating Collections

### Basic Collection (Single Vector)

```python
from qdrant_client import QdrantClient, models

client = QdrantClient("localhost", port=6333)

client.create_collection(
    collection_name="my_collection",
    vectors_config=models.VectorParams(
        size=384,                        # vector dimensions
        distance=models.Distance.COSINE, # distance metric
    ),
)
```

**REST equivalent:**
```http
PUT /collections/my_collection
{
    "vectors": {
        "size": 384,
        "distance": "Cosine"
    }
}
```

### Named Vectors (Multi-Vector)

Store multiple vector types per point — useful for multi-modal search or multi-stage retrieval.

```python
client.create_collection(
    collection_name="multi_vec",
    vectors_config={
        "dense": models.VectorParams(size=768, distance=models.Distance.COSINE),
        "small": models.VectorParams(size=256, distance=models.Distance.DOT),
    },
    sparse_vectors_config={
        "sparse": models.SparseVectorParams(),
    },
)
```

### Vector Storage Options

```python
# On-disk vectors (large datasets, saves RAM)
models.VectorParams(
    size=768,
    distance=models.Distance.COSINE,
    on_disk=True,                # memmap-based disk storage
)

# Pre-quantized uint8 vectors (v1.9.0+)
models.VectorParams(
    size=384,
    distance=models.Distance.COSINE,
    datatype=models.Datatype.UINT8,  # store as uint8 directly
)
```

## Distance Metrics

| Metric | Enum | Range | Best For |
|--------|------|-------|----------|
| Cosine | `Distance.COSINE` | 0 to 2 | Text embeddings (default choice) |
| Dot Product | `Distance.DOT` | -∞ to +∞ | Pre-normalized vectors |
| Euclidean | `Distance.EUCLID` | 0 to +∞ | Image features, spatial data |
| Manhattan | `Distance.MANHATTAN` | 0 to +∞ | Sparse features |

**Note:** Cosine is implemented by normalizing vectors internally and using dot product. If vectors are pre-normalized, `DOT` is slightly faster.

## Collection Parameters

```python
client.create_collection(
    collection_name="configured",
    vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
    # HNSW index configuration
    hnsw_config=models.HnswConfigDiff(
        m=16,                    # edges per node (default: 16)
        ef_construct=100,        # neighbors during build (default: 100)
        full_scan_threshold=10000,
    ),
    # Optimizer configuration
    optimizers_config=models.OptimizersConfigDiff(
        indexing_threshold=20000,
        memmap_threshold=200000,
    ),
    # WAL configuration
    wal_config=models.WalConfigDiff(
        wal_capacity_mb=32,
        wal_segments_ahead=0,
    ),
    # Quantization
    quantization_config=models.ScalarQuantization(
        scalar=models.ScalarQuantizationConfig(
            type=models.ScalarType.INT8,
            always_ram=True,
        ),
    ),
    # Sharding (distributed)
    shard_number=1,              # number of shards
    replication_factor=1,        # replicas per shard
    # Payload storage
    on_disk_payload=True,        # store payloads on disk
)
```

## Managing Collections

### Get Collection Info

```python
info = client.get_collection("my_collection")
print(f"Points: {info.points_count}")       # approximate count
print(f"Vectors: {info.vectors_count}")      # approximate count
print(f"Status: {info.status}")              # green, yellow, grey, red
print(f"Segments: {info.segments_count}")
```

**Status values:**
- `green` — All segments optimized, ready for search
- `yellow` — Optimization in progress
- `grey` — Pending optimization
- `red` — Error state

### Check If Collection Exists (v1.8.0+)

```python
exists = client.collection_exists("my_collection")
```

```http
GET /collections/my_collection/exists
```

### List All Collections

```python
collections = client.get_collections()
for c in collections.collections:
    print(c.name)
```

### Update Collection Parameters

```python
client.update_collection(
    collection_name="my_collection",
    optimizers_config=models.OptimizersConfigDiff(
        indexing_threshold=50000,
    ),
    hnsw_config=models.HnswConfigDiff(
        ef_construct=200,
    ),
)
```

**Note:** Parameter updates apply only to new segments. Existing segments retain their configuration until re-optimized.

### Delete Collection

```python
client.delete_collection("my_collection")
```

```http
DELETE /collections/my_collection
```

## Aliases

Aliases provide atomic switching between collections — essential for zero-downtime reindexing.

```python
# Create alias
client.update_collection_aliases(
    change_aliases_operations=[
        models.CreateAliasOperation(
            create_alias=models.CreateAlias(
                collection_name="my_collection_v2",
                alias_name="production",
            )
        )
    ]
)

# Atomic switch (blue-green deployment)
client.update_collection_aliases(
    change_aliases_operations=[
        models.DeleteAliasOperation(
            delete_alias=models.DeleteAlias(alias_name="production")
        ),
        models.CreateAliasOperation(
            create_alias=models.CreateAlias(
                collection_name="my_collection_v3",
                alias_name="production",
            )
        ),
    ]
)

# Rename alias
client.update_collection_aliases(
    change_aliases_operations=[
        models.RenameAliasOperation(
            rename_alias=models.RenameAlias(
                old_alias_name="production",
                new_alias_name="archive",
            )
        )
    ]
)
```

**REST:**
```http
POST /collections/aliases
{
    "actions": [
        { "create_alias": { "collection_name": "my_collection_v2", "alias_name": "production" } }
    ]
}
```

## Collection Metadata (v1.16.0+)

Attach custom key-value pairs to collections for organizational purposes.

```python
client.create_collection(
    collection_name="my_collection",
    vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
    metadata={"team": "ml-platform", "model": "all-MiniLM-L6-v2"},
)
```

## Common Pitfalls

1. **Approximate counts** — `points_count` and `vectors_count` reflect internal storage state, not exact user-inserted counts. Small discrepancies are normal.
2. **Immutable vector config** — You cannot change `size` or `distance` after creation. Create a new collection and migrate data.
3. **Parameter update scope** — Changes to `hnsw_config` or `optimizers_config` only affect newly created segments. Trigger re-optimization for existing segments.
4. **Sparse vectors** — Always use `Distance.DOT` implicitly (no distance parameter needed for sparse).
5. **Collection name limits** — Must match `[a-zA-Z0-9_-]+`, max 255 characters.

## Related Topics

- Points & payloads → `references/02-points.md`
- Indexing configuration → `references/05-indexing.md`
- Quantization → `references/06-quantization.md`
- Deployment → `references/12-deployment.md`
