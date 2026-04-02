# Qdrant — Quantization

> Source: [qdrant.tech/documentation/guides/quantization](https://qdrant.tech/documentation/guides/quantization/) | v1.17.1

## Overview

Quantization reduces memory footprint by compressing vector representations. Qdrant supports three quantization methods, each trading accuracy for memory and speed differently.

| Method | Compression | Speed | Accuracy | RAM Reduction |
|--------|-------------|-------|----------|---------------|
| **Scalar (INT8)** | 4x | 2x faster | ~99% | 75% |
| **Binary (1-bit)** | 32x | up to 40x faster | ~95%* | 97% |
| **Product (PQ)** | up to 64x | 0.5x (slower) | ~70-90% | 94-98% |

*Binary accuracy depends on vector dimensions and model. Best with high-dimensional models (768+).

## Scalar Quantization (v1.1.0+)

Converts float32 to uint8 (8-bit integers). The safest and most universally applicable method.

### Enable at Collection Creation

```python
from qdrant_client import QdrantClient, models

client = QdrantClient("localhost", port=6333)

client.create_collection(
    collection_name="my_collection",
    vectors_config=models.VectorParams(
        size=768,
        distance=models.Distance.COSINE,
    ),
    quantization_config=models.ScalarQuantization(
        scalar=models.ScalarQuantizationConfig(
            type=models.ScalarType.INT8,
            quantile=0.99,       # exclude top 1% outliers for better range
            always_ram=True,     # keep quantized vectors in RAM always
        ),
    ),
)
```

### Enable on Existing Collection

```python
client.update_collection(
    collection_name="my_collection",
    quantization_config=models.ScalarQuantization(
        scalar=models.ScalarQuantizationConfig(
            type=models.ScalarType.INT8,
            quantile=0.99,
            always_ram=True,
        ),
    ),
)
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `type` | `INT8` | Only INT8 supported currently |
| `quantile` | `0.99` | Percentile for value range clipping (0.5-1.0) |
| `always_ram` | `False` | Keep quantized vectors in RAM even if originals are on disk |

**Recommendation:** Always set `always_ram=True` when using on-disk vector storage. This keeps fast quantized vectors in RAM while full-precision vectors stay on disk for rescoring.

## Binary Quantization (v1.5.0+)

Reduces each vector component to a single bit. Extreme compression but requires compatible models.

```python
client.create_collection(
    collection_name="my_collection",
    vectors_config=models.VectorParams(
        size=1536,
        distance=models.Distance.COSINE,
    ),
    quantization_config=models.BinaryQuantization(
        binary=models.BinaryQuantizationConfig(
            always_ram=True,
        ),
    ),
)
```

### Compatible Models

Binary quantization works best with high-dimensional models that produce well-distributed vectors:

| Model | Dimensions | Works Well? |
|-------|-----------|-------------|
| OpenAI text-embedding-ada-002 | 1536 | Yes |
| OpenAI text-embedding-3-small | 1536 | Yes |
| Cohere embed-english-v2.0 | 4096 | Yes |
| Cohere embed-multilingual-v3.0 | 1024 | Yes |
| sentence-transformers/all-MiniLM-L6-v2 | 384 | Marginal |

**Rule of thumb:** Binary quantization is best with dimensions >= 768. Always test with your specific model and dataset — accuracy varies significantly.

## Product Quantization (v1.2.0+)

Divides vectors into sub-vectors, encodes each with k-means centroids. Maximum compression but slowest search.

```python
client.create_collection(
    collection_name="my_collection",
    vectors_config=models.VectorParams(
        size=768,
        distance=models.Distance.COSINE,
    ),
    quantization_config=models.ProductQuantization(
        product=models.ProductQuantizationConfig(
            compression=models.CompressionRatio.X16,  # X4, X8, X16, X32, X64
            always_ram=True,
        ),
    ),
)
```

### Compression Ratios

| Ratio | Bytes per Sub-Vector | Use Case |
|-------|---------------------|----------|
| X4 | 1 byte per 4 floats | Moderate compression |
| X8 | 1 byte per 8 floats | Good balance |
| X16 | 1 byte per 16 floats | High compression |
| X32 | 1 byte per 32 floats | Very high compression |
| X64 | 1 byte per 64 floats | Maximum compression |

**Note:** PQ requires sufficient data to train good centroids. Works poorly with < 10,000 vectors.

## Search with Quantization

Control quantization behavior at query time:

```python
results = client.query_points(
    collection_name="my_collection",
    query=[0.2, 0.1, 0.9, 0.7],
    search_params=models.SearchParams(
        quantization=models.QuantizationSearchParams(
            ignore=False,       # False = use quantized vectors (default)
            rescore=True,       # re-score top results with original vectors
            oversampling=2.0,   # fetch 2x candidates before rescoring
        ),
    ),
    limit=10,
)
```

### Search Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `ignore` | `False` | `True` to skip quantization and use full-precision vectors |
| `rescore` | `True` (if quantized) | Re-rank top candidates with original vectors |
| `oversampling` | `1.0` | Multiplier for candidate pool before rescoring |

### Rescoring Strategy

```
Query → Search quantized vectors (fast) → Get N × oversampling candidates
      → Re-score with full-precision vectors → Return top N results
```

**Example:** With `limit=10` and `oversampling=2.0`, Qdrant searches for 20 candidates using quantized vectors, then re-ranks them with full-precision vectors and returns the top 10.

## Hybrid Storage Strategy

The recommended production pattern: quantized vectors in RAM + full-precision vectors on disk.

```python
client.create_collection(
    collection_name="production",
    vectors_config=models.VectorParams(
        size=768,
        distance=models.Distance.COSINE,
        on_disk=True,  # full-precision vectors on disk
    ),
    quantization_config=models.ScalarQuantization(
        scalar=models.ScalarQuantizationConfig(
            type=models.ScalarType.INT8,
            always_ram=True,  # quantized vectors always in RAM
        ),
    ),
)
```

**Memory calculation example:**
- 1M vectors × 768 dimensions × 4 bytes (float32) = **3 GB** (full precision)
- 1M vectors × 768 dimensions × 1 byte (INT8) = **0.75 GB** (scalar quantized)
- Savings: **75% RAM reduction** with ~1% accuracy loss

## Disable Quantization

```python
client.update_collection(
    collection_name="my_collection",
    quantization_config=models.Disabled,
)
```

## Choosing a Quantization Method

```
Need maximum accuracy?
  → Scalar (INT8): safest, ~1% accuracy loss, 4x compression

Need maximum speed?
  → Binary (1-bit): 40x speedup, but test your model first
  → Requires: high-dim vectors (768+), always use rescoring

Need minimum memory?
  → Product (PQ): up to 64x compression, but slower search
  → Requires: 10,000+ vectors for good centroid training
```

**Default recommendation:** Start with Scalar Quantization. It works with any model and provides a good balance of speed, accuracy, and compression.

## Common Pitfalls

1. **Binary + low dimensions** — Binary quantization degrades badly with < 512 dimensions. Always test before deploying.
2. **PQ training data** — Product quantization needs enough data to learn good centroids. Poor with < 10,000 vectors.
3. **Rescoring cost** — Rescoring requires reading full-precision vectors from disk. High oversampling values increase disk I/O.
4. **Always test accuracy** — Quantization impact varies by model and data distribution. Benchmark on your actual dataset before deploying.
5. **quantile parameter** — Setting `quantile` too low (e.g., 0.5) clips too many values. Keep at 0.95-0.99.

## Related Topics

- Collections → `references/01-collections.md`
- Search parameters → `references/03-search-query.md`
- Optimizer → `references/09-optimizer.md`
