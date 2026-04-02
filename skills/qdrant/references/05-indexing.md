# Qdrant — Indexing

> Source: [qdrant.tech/documentation/concepts/indexing](https://qdrant.tech/documentation/concepts/indexing/) | v1.17.1

## Table of Contents

- [Overview](#overview)
- [Payload Index Types](#payload-index-types)
- [Creating Payload Indexes](#creating-payload-indexes)
- [Full-Text Index](#full-text-index)
- [Tenant and Principal Indexes](#tenant-and-principal-indexes)
- [HNSW Vector Index](#hnsw-vector-index)
- [Sparse Vector Index](#sparse-vector-index)
- [Common Pitfalls](#common-pitfalls)

## Overview

Qdrant uses two types of indexes:
1. **Payload indexes** — Index JSON payload fields for fast filtering
2. **Vector indexes** — HNSW graph for approximate nearest neighbor (ANN) search

Without payload indexes, filter conditions trigger full scans. Always create indexes on fields used in filters.

## Payload Index Types

| Type | Supports | Version |
|------|----------|---------|
| `keyword` | Exact match, MatchAny, MatchExcept | v1.0+ |
| `integer` | Match, range (configurable) | v1.0+ (parameterized v1.8+) |
| `float` | Range filtering | v1.0+ |
| `bool` | Match filtering | v1.4+ |
| `geo` | Bounding box, radius, polygon | v1.0+ |
| `datetime` | Range filtering (RFC 3339) | v1.8+ |
| `text` | Full-text tokenized search | v1.0+ |
| `uuid` | Optimized keyword-like matching | v1.11+ |

## Creating Payload Indexes

### Basic Index Creation

```python
from qdrant_client import QdrantClient, models

client = QdrantClient("localhost", port=6333)

# Keyword index
client.create_payload_index(
    collection_name="my_collection",
    field_name="category",
    field_schema="keyword",
)

# Integer index (with full configuration, v1.8.0+)
client.create_payload_index(
    collection_name="my_collection",
    field_name="price",
    field_schema=models.IntegerIndexParams(
        type="integer",
        lookup=True,    # enable exact match
        range=True,     # enable range queries
    ),
)

# Float index
client.create_payload_index(
    collection_name="my_collection",
    field_name="score",
    field_schema="float",
)

# Boolean index
client.create_payload_index(
    collection_name="my_collection",
    field_name="active",
    field_schema="bool",
)

# Datetime index
client.create_payload_index(
    collection_name="my_collection",
    field_name="created_at",
    field_schema="datetime",
)

# UUID index (v1.11.0+)
client.create_payload_index(
    collection_name="my_collection",
    field_name="doc_id",
    field_schema="uuid",
)

# Geo index
client.create_payload_index(
    collection_name="my_collection",
    field_name="location",
    field_schema="geo",
)
```

**REST equivalent:**
```http
PUT /collections/my_collection/index
{
    "field_name": "category",
    "field_schema": "keyword"
}
```

### On-Disk Index (v1.11.0+)

Store payload indexes on disk to save RAM (increases latency):

```python
client.create_payload_index(
    collection_name="my_collection",
    field_name="category",
    field_schema=models.KeywordIndexParams(
        type="keyword",
        on_disk=True,
    ),
)
```

### Delete Index

```python
client.delete_payload_index(
    collection_name="my_collection",
    field_name="category",
)
```

### Nested Field Indexes

```python
# Index nested fields using dot notation
client.create_payload_index(
    collection_name="my_collection",
    field_name="address.city",
    field_schema="keyword",
)

# Array element fields
client.create_payload_index(
    collection_name="my_collection",
    field_name="tags[].name",
    field_schema="keyword",
)
```

## Full-Text Index

### Basic Full-Text Index

```python
client.create_payload_index(
    collection_name="my_collection",
    field_name="description",
    field_schema=models.TextIndexParams(
        type="text",
        tokenizer=models.TokenizerType.WORD,
        min_token_len=2,
        max_token_len=15,
        lowercase=True,
    ),
)
```

### Tokenizer Options

| Tokenizer | Behavior |
|-----------|----------|
| `WORD` | Splits on whitespace and punctuation |
| `WHITESPACE` | Splits on whitespace only |
| `PREFIX` | Generates prefix tokens for autocomplete |
| `MULTILINGUAL` | Unicode-aware tokenization |

### Advanced Full-Text Configuration

```python
client.create_payload_index(
    collection_name="my_collection",
    field_name="content",
    field_schema=models.TextIndexParams(
        type="text",
        tokenizer=models.TokenizerType.WORD,
        min_token_len=2,
        max_token_len=20,
        lowercase=True,
        # Stemming (v1.15.0+)
        stemmer=models.StemmerType.ENGLISH,  # language-specific stemming
        # Stop words
        stopwords=["the", "a", "an", "is", "are"],
        # ASCII folding (accented chars → ASCII)
        ascii_folding=True,
        # Phrase matching support (v1.15.0+)
        phrase_matching=True,  # required for MatchPhrase filter
    ),
)
```

### Querying Full-Text

```python
# AND search — both tokens must appear
results = client.query_points(
    collection_name="my_collection",
    query=[0.2, 0.1, 0.9, 0.7],
    query_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="content",
                match=models.MatchText(text="vector database"),
            )
        ]
    ),
    limit=10,
)

# OR search (v1.16.0+) — any token can appear
results = client.query_points(
    collection_name="my_collection",
    query=[0.2, 0.1, 0.9, 0.7],
    query_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="content",
                match=models.MatchTextAny(text_any="vector database search"),
            )
        ]
    ),
    limit=10,
)
```

## Tenant and Principal Indexes

### Tenant Index (v1.11.0+)

Optimizes multi-tenant collections by structuring storage for tenant-specific queries:

```python
client.create_payload_index(
    collection_name="my_collection",
    field_name="tenant_id",
    field_schema=models.KeywordIndexParams(
        type="keyword",
        is_tenant=True,  # mark as tenant identifier
    ),
)
```

**Supported types:** `keyword`, `uuid` only.

Qdrant restructures internal storage to colocate data per tenant, dramatically improving filtered search performance for tenant-scoped queries.

### Principal Index (v1.11.0+)

Optimizes for a primary ordering/filtering field (e.g., timestamps):

```python
client.create_payload_index(
    collection_name="my_collection",
    field_name="created_at",
    field_schema=models.DatetimeIndexParams(
        type="datetime",
        is_principal=True,
    ),
)
```

**Supported types:** `integer`, `float`, `datetime`.

## HNSW Vector Index

HNSW (Hierarchical Navigable Small World) is the default vector index algorithm.

### Configuration

Set at collection creation:

```python
client.create_collection(
    collection_name="my_collection",
    vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
    hnsw_config=models.HnswConfigDiff(
        m=16,                     # edges per node (default: 16)
        ef_construct=100,         # neighbors during build (default: 100)
        full_scan_threshold=10000, # below this KB, brute force used
    ),
)
```

### HNSW Parameters

| Parameter | Default | Effect |
|-----------|---------|--------|
| `m` | 16 | Graph connectivity. Higher = better recall, more memory |
| `ef_construct` | 100 | Build-time beam. Higher = better index, slower build |
| `full_scan_threshold` | 10000 | KB threshold for switching to brute force |

**Tuning guidelines:**
- Increase `m` to 32-64 for higher recall requirements
- Increase `ef_construct` to 200-400 for large datasets
- Keep `full_scan_threshold` at 10000 unless you have very small collections
- At query time, tune `hnsw_ef` in `SearchParams` (defaults to `ef_construct`)

### Filterable HNSW

Qdrant automatically extends the HNSW graph with edges based on payload indexes. This enables efficient pre-filtering during ANN search for mid-selectivity filters.

### Disable HNSW Extra Edges (v1.17.0+)

For payload indexes only used with sparse vectors:

```python
client.create_payload_index(
    collection_name="my_collection",
    field_name="sparse_tag",
    field_schema=models.KeywordIndexParams(
        type="keyword",
        enable_hnsw=False,  # skip HNSW graph extension
    ),
)
```

## Sparse Vector Index

Sparse vectors use an inverted index (exact search, no approximation):

```python
client.create_collection(
    collection_name="my_collection",
    vectors_config={},
    sparse_vectors_config={
        "sparse": models.SparseVectorParams(
            index=models.SparseIndexParams(
                on_disk=False,  # True to store index on disk
            ),
            modifier=models.Modifier.IDF,  # IDF weighting (v1.10.0+)
        ),
    },
)
```

**IDF modifier (v1.10.0+):** Automatically weights query terms by inverse document frequency, boosting rare terms and dampening common ones.

## Common Pitfalls

1. **Create indexes before data** — Create payload indexes immediately after collection creation, before upserting data, for optimal index building.
2. **Index only what you filter** — Each index uses memory. Only index fields that appear in filter conditions.
3. **High cardinality fields** — Indexes work best on fields with many distinct values. A boolean field with 50/50 distribution won't benefit much.
4. **Tenant index is critical** — For multi-tenant collections, always mark the tenant field with `is_tenant=True`. Without it, tenant-filtered searches scan all data.
5. **Full-text != vector search** — Full-text indexes are for exact token matching, not semantic similarity. Use vectors for semantic search.
6. **Phrase matching flag** — `MatchPhrase` requires `phrase_matching=True` on the text index configuration. Without it, phrase queries won't work.

## Related Topics

- Filtering → `references/04-filtering.md`
- Quantization → `references/06-quantization.md`
- Multitenancy → `references/11-multitenancy.md`
