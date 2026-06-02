# Weaviate — Vector Configuration

> Source: [docs.weaviate.io](https://docs.weaviate.io/weaviate/manage-collections/vector-config) | Version: v1.37

## Table of Contents
- [Vector Index Types](#vector-index-types)
- [HNSW Index](#hnsw-index)
- [Flat Index](#flat-index)
- [Dynamic Index](#dynamic-index)
- [Distance Metrics](#distance-metrics)
- [Vector Quantization](#vector-quantization)
- [Named Vectors](#named-vectors)
- [Multi-Vector Support](#multi-vector-support)
- [Custom (Bring Your Own) Vectors](#custom-bring-your-own-vectors)
- [Common Pitfalls](#common-pitfalls)

---

## Vector Index Types

Weaviate supports four vector index types, each optimized for different use cases:

| Index | Best For | Trade-off |
|-------|----------|-----------|
| **HNSW** | Production workloads, large datasets | High recall + speed, more memory |
| **Flat** | Small datasets (<10K objects) | Exact search, no approximation |
| **Dynamic** | Growing collections | Starts flat, auto-migrates to HNSW |
| **HFRESH** | Frequently updated data | Optimized for high-churn workloads |

## HNSW Index

Hierarchical Navigable Small World — the default and most common index type.

```python
from weaviate.classes.config import Configure, VectorFilterStrategy

client.collections.create(
    "Article",
    vector_config=Configure.Vectors.text2vec_openai(
        vector_index_config=Configure.VectorIndex.hnsw(
            distance_metric=Configure.VectorDistances.COSINE,
            ef_construction=128,       # Build-time quality (default: 128)
            max_connections=32,        # Graph connectivity (default: 32)
            ef=64,                     # Query-time quality (default: -1 = auto)
            filter_strategy=VectorFilterStrategy.ACORN,  # v1.34+ default
        )
    ),
)
```

### HNSW Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `ef_construction` | 128 | Build quality. Higher = better recall, slower build |
| `max_connections` | 32 | Edges per node. Higher = better recall, more memory |
| `ef` | -1 (auto) | Query quality. Higher = better recall, slower query |
| `filter_strategy` | ACORN | ACORN (v1.34+) or SWEEPING for filtered searches |
| `cleanup_interval_seconds` | 300 | Tombstone cleanup frequency |
| `dynamic_ef_min` | 100 | Min ef when dynamic ef is enabled |
| `dynamic_ef_max` | 500 | Max ef when dynamic ef is enabled |
| `dynamic_ef_factor` | 8 | ef = factor * limit |

## Flat Index

Brute-force exact nearest neighbor search. Best for small collections or when exact results are required.

```python
client.collections.create(
    "SmallDataset",
    vector_config=Configure.Vectors.text2vec_openai(
        vector_index_config=Configure.VectorIndex.flat(
            distance_metric=Configure.VectorDistances.COSINE,
        )
    ),
)
```

## Dynamic Index

Starts as flat, auto-converts to HNSW when the object count exceeds a threshold.

```python
client.collections.create(
    "GrowingDataset",
    vector_config=Configure.Vectors.text2vec_openai(
        vector_index_config=Configure.VectorIndex.dynamic(
            distance_metric=Configure.VectorDistances.COSINE,
            threshold=10000,  # Convert to HNSW at this count
            hnsw=Configure.VectorIndex.hnsw(ef_construction=192),
            flat=Configure.VectorIndex.flat(),
        )
    ),
)
```

## Distance Metrics

| Metric | Enum | Range | Description |
|--------|------|-------|-------------|
| Cosine | `COSINE` | 0–2 | Angular similarity (most common) |
| Dot product | `DOT` | -∞ to +∞ | Dot product similarity |
| L2 (Euclidean) | `L2_SQUARED` | 0 to +∞ | Squared Euclidean distance |
| Hamming | `HAMMING` | 0 to dims | Bit-level differences |
| Manhattan | `MANHATTAN` | 0 to +∞ | Taxicab distance |

```python
vector_index_config=Configure.VectorIndex.hnsw(
    distance_metric=Configure.VectorDistances.DOT,
)
```

For cosine distance: `0` = identical, `2` = opposite. Lower is more similar.

## Vector Quantization

Compression techniques to reduce memory usage while maintaining search quality.

### Product Quantization (PQ)

```python
client.collections.create(
    "Article",
    vector_config=Configure.Vectors.text2vec_openai(
        vector_index_config=Configure.VectorIndex.hnsw(
            quantizer=Configure.VectorIndex.Quantizer.pq(
                segments=128,         # Number of segments
                centroids=256,        # Centroids per segment
                training_limit=100000, # Training sample size
            )
        )
    ),
)
```

### Binary Quantization (BQ)

Fastest compression — reduces each dimension to a single bit. Works best with high-dimensional vectors (>1024).

```python
vector_index_config=Configure.VectorIndex.hnsw(
    quantizer=Configure.VectorIndex.Quantizer.bq(
        rescore_limit=200,  # Candidates for rescoring
    )
)
```

### Scalar Quantization (SQ)

Compresses each dimension to a single byte.

```python
vector_index_config=Configure.VectorIndex.hnsw(
    quantizer=Configure.VectorIndex.Quantizer.sq(
        training_limit=100000,
        rescore_limit=200,
    )
)
```

## Named Vectors

Store multiple vector representations per object, each with independent vectorizer and index settings.

```python
from weaviate.classes.config import Configure, Property, DataType

client.collections.create(
    "ProductReview",
    vector_config=[
        Configure.NamedVectors.text2vec_openai(
            name="title_vector",
            source_properties=["title", "brand"],
            vector_index_config=Configure.VectorIndex.hnsw(
                distance_metric=Configure.VectorDistances.COSINE
            ),
        ),
        Configure.NamedVectors.text2vec_openai(
            name="review_vector",
            source_properties=["review_body"],
            vector_index_config=Configure.VectorIndex.hnsw(
                distance_metric=Configure.VectorDistances.COSINE
            ),
        ),
        Configure.NamedVectors.text2vec_cohere(
            name="multilingual_vector",
            source_properties=["title", "review_body"],
            model="embed-multilingual-v3.0",
        ),
    ],
    properties=[
        Property(name="title", data_type=DataType.TEXT),
        Property(name="brand", data_type=DataType.TEXT),
        Property(name="review_body", data_type=DataType.TEXT),
    ],
)
```

### Querying Named Vectors

```python
reviews = client.collections.use("ProductReview")
response = reviews.query.near_text(
    query="great battery life",
    target_vector="review_vector",
    limit=5,
)
```

New named vectors can be added to existing collections (v1.31+), but existing objects are not automatically revectorized.

## Multi-Vector Support

Multi-vector embeddings (v1.30+) represent objects as 2D matrices rather than 1D arrays. Models like ColBERT and ColPali produce multi-vectors for token-level representations.

```python
Configure.NamedVectors.text2vec_cohere(
    name="colbert_vector",
    source_properties=["text"],
    multi_vector=True,
)
```

Currently only supported with HNSW indexes.

## Custom (Bring Your Own) Vectors

For pre-computed embeddings from external models:

```python
import weaviate.classes as wvc

client.collections.create(
    "Article",
    vector_config=wvc.config.Configure.Vectors.self_provided(),
    properties=[
        wvc.config.Property(name="title", data_type=wvc.config.DataType.TEXT),
    ],
)

# Insert with vector
articles = client.collections.use("Article")
articles.data.insert(
    properties={"title": "AI News"},
    vector=[0.1, 0.2, 0.3, ...]  # Your pre-computed vector
)

# Search with vector
response = articles.query.near_vector(
    near_vector=[0.1, 0.2, 0.3, ...],
    limit=5,
)
```

## Common Pitfalls

1. **Wrong distance metric**: Cosine is the most common default. Using L2 with normalized vectors works but wastes precision. Match the metric to your embedding model's training.

2. **Over-tuning HNSW**: The defaults work well for most cases. Only increase `ef_construction` or `max_connections` if recall benchmarks show issues — each increase costs memory.

3. **Quantization training data**: PQ/SQ need sufficient data to train properly. Don't enable quantization on empty collections — wait until you have at least `training_limit` objects.

4. **Named vector source overlap**: Two named vectors using the same source properties create redundant storage. Ensure each named vector captures a distinct semantic aspect.

5. **Mixing custom and auto vectors**: If using `self_provided()`, you must supply vectors on every insert and query. The collection won't auto-vectorize text.

## Related Topics

- Collections & Schema → `01-collections.md`
- Similarity Search → `04-similarity-search.md`
- Model Providers → `11-model-providers.md`
