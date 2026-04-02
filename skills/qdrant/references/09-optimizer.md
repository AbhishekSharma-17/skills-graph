# Qdrant — Optimizer & Performance

> Source: [qdrant.tech/documentation/concepts/optimizer](https://qdrant.tech/documentation/concepts/optimizer/) | v1.17.1

## Overview

Qdrant continuously optimizes data storage in the background through three optimizer types. Understanding optimizer behavior is key to achieving peak performance, especially during bulk ingestion and for large-scale collections.

## Optimizer Types

### 1. Vacuum Optimizer

Removes accumulated deleted records from segments.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `deleted_threshold` | 0.2 | Trigger cleanup when 20% of segment is deleted |
| `vacuum_min_vector_number` | 1000 | Minimum vectors before vacuuming kicks in |

### 2. Merge Optimizer

Reduces excessive small segments by merging them.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `default_segment_number` | 0 (auto) | Target segments per shard (0 = auto based on CPU) |
| `max_segment_size_kb` | null (auto) | Maximum segment size before it's left alone |

### 3. Indexing Optimizer

Enables HNSW indexes when data exceeds thresholds.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `indexing_threshold_kb` | 10000 | KB threshold to enable vector index |
| `memmap_threshold` | 200000 | KB threshold to switch to memmap storage |

## Configuring Optimizers

### At Collection Creation

```python
from qdrant_client import QdrantClient, models

client = QdrantClient("localhost", port=6333)

client.create_collection(
    collection_name="my_collection",
    vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
    optimizers_config=models.OptimizersConfigDiff(
        deleted_threshold=0.2,
        vacuum_min_vector_number=1000,
        default_segment_number=0,
        indexing_threshold=10000,
        memmap_threshold=200000,
        flush_interval_sec=5,
        max_optimization_threads=0,  # 0 = auto (half of CPU cores)
    ),
)
```

### Dynamic Update

```python
client.update_collection(
    collection_name="my_collection",
    optimizers_config=models.OptimizersConfigDiff(
        indexing_threshold=50000,
    ),
)
```

**Important:** Parameter updates only affect newly created segments. Existing segments retain their configuration until merged or re-optimized.

## Bulk Upload Pattern

For large data imports, disable indexing during ingestion:

```python
# 1. Disable indexing for fast writes
client.update_collection(
    collection_name="my_collection",
    optimizers_config=models.OptimizersConfigDiff(
        indexing_threshold=0,  # disable indexing
    ),
)

# 2. Bulk upsert data
for batch in batches:
    client.upsert(
        collection_name="my_collection",
        points=batch,
        wait=False,  # async writes for throughput
    )

# 3. Re-enable indexing
client.update_collection(
    collection_name="my_collection",
    optimizers_config=models.OptimizersConfigDiff(
        indexing_threshold=20000,  # re-enable
    ),
)

# 4. Wait for optimization to complete
import time
while True:
    info = client.get_collection("my_collection")
    if info.status == models.CollectionStatus.GREEN:
        break
    time.sleep(5)
```

### Using upload_points for Bulk Import

```python
client.upload_points(
    collection_name="my_collection",
    points=points_list,
    batch_size=256,
    parallel=4,
    wait=True,
)
```

## Prevent Unoptimized Reads (v1.17.1+)

Hide deferred (not yet indexed) points from search results:

```python
client.update_collection(
    collection_name="my_collection",
    optimizers_config=models.OptimizersConfigDiff(
        prevent_unoptimized=True,
    ),
)
```

**Warning:** When combined with `wait=True` on writes, this can cause timeouts because the write waits for the point to become searchable, which requires optimization to complete.

## Monitoring Optimizations (v1.17.0+)

```http
GET /collections/my_collection/optimizations
```

Returns:
- Queued optimizations (pending)
- Currently running optimizations
- Recently completed optimizations
- Idle segment information

## Memory Management

### Memmap Storage

For collections larger than available RAM:

```python
# Enable memmap at collection creation
client.create_collection(
    collection_name="large_collection",
    vectors_config=models.VectorParams(
        size=768,
        distance=models.Distance.COSINE,
        on_disk=True,  # vectors stored as memmap
    ),
    optimizers_config=models.OptimizersConfigDiff(
        memmap_threshold=100000,  # KB threshold for memmap segments
    ),
    on_disk_payload=True,  # payloads also on disk
)
```

### Memory Estimation

```
Vector memory = num_vectors × dimensions × 4 bytes (float32)
Payload memory = depends on payload size and on_disk_payload setting
HNSW memory = num_vectors × m × 2 × 8 bytes (graph links)
```

**Example for 1M vectors × 768 dims:**
- Vectors: 1M × 768 × 4 = 3.07 GB
- HNSW (m=16): 1M × 16 × 2 × 8 = 256 MB
- Total (in-RAM): ~3.3 GB
- With scalar quantization (always_ram): ~1.0 GB vectors + 256 MB HNSW = ~1.3 GB

## WAL Configuration

```python
client.create_collection(
    collection_name="my_collection",
    vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
    wal_config=models.WalConfigDiff(
        wal_capacity_mb=32,       # WAL segment size
        wal_segments_ahead=0,     # pre-allocated segments
    ),
)
```

## Performance Tuning Checklist

1. **Create payload indexes** — Index all fields used in filters before data ingestion
2. **Use batch operations** — `upload_points` with `batch_size=256, parallel=4`
3. **Disable indexing for bulk loads** — Set `indexing_threshold=0` during import
4. **Quantization** — Use scalar quantization (INT8) as default for 4x memory reduction
5. **Hybrid storage** — Quantized vectors in RAM + full vectors on disk
6. **Tune hnsw_ef at query time** — Higher ef = better recall at the cost of latency
7. **Use gRPC** — Port 6334 for higher throughput vs REST on 6333
8. **Async client** — `AsyncQdrantClient` for concurrent operations
9. **Memmap for large data** — `on_disk=True` when data exceeds RAM
10. **Monitor deferred points** — Track optimization status during write-heavy workloads

## Common Pitfalls

1. **Forgetting to re-enable indexing** — After bulk upload, always restore `indexing_threshold` to a positive value.
2. **wait=True + prevent_unoptimized** — This combination can cause request timeouts. Use one or the other.
3. **Parameter update scope** — Changes to optimizer config only affect NEW segments. Existing segments need re-optimization.
4. **flush_interval_sec** — Too low values (< 1s) increase disk I/O. Default 5s is good for most workloads.
5. **Optimization during search** — Background optimization uses copy-on-write, so search remains available. But heavy optimization can impact search latency.

## Related Topics

- Collections → `references/01-collections.md`
- Quantization → `references/06-quantization.md`
- Deployment → `references/12-deployment.md`
