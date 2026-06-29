# Milvus — Schema Design

> Source: [milvus.io/docs/schema.md](https://milvus.io/docs/schema.md) | Version: 3.0-beta

## Table of Contents

- [Field Types](#field-types)
- [Creating a Schema](#creating-a-schema)
- [Primary Key Options](#primary-key-options)
- [Vector Field Configurations](#vector-field-configurations)
- [Nullable Fields](#nullable-fields)
- [Dynamic Fields](#dynamic-fields)
- [Array Fields](#array-fields)
- [JSON Fields](#json-fields)
- [Schema Design Patterns](#schema-design-patterns)
- [Common Pitfalls](#common-pitfalls)

## Overview

A schema defines the structure of a collection — its fields, types, and constraints. Every collection requires at least one primary key field and one vector field. Well-designed schemas enable efficient storage, precise filtering, and optimal search performance.

## Field Types

### Vector Fields

| DataType | Description | Dimension | Use Case |
|----------|-------------|-----------|----------|
| `FLOAT_VECTOR` | 32-bit float array | Required (`dim`) | Standard dense embeddings |
| `FLOAT16_VECTOR` | 16-bit half-precision | Required (`dim`) | Memory-constrained, GPU inference |
| `BFLOAT16_VECTOR` | Brain float 16-bit | Required (`dim`) | ML training outputs |
| `INT8_VECTOR` | 8-bit signed integers (-128 to 127) | Required (`dim`) | Quantized embeddings (HNSW only) |
| `BINARY_VECTOR` | Binary bit array | Required (`dim`, multiple of 8) | Image fingerprints, hashing |
| `SPARSE_FLOAT_VECTOR` | Sparse key-value pairs | Variable | BM25, learned sparse embeddings (SPLADE) |

### Scalar Fields

| DataType | Size | Range | Notes |
|----------|------|-------|-------|
| `BOOL` | 1 byte | true/false | Flags, toggles |
| `INT8` | 1 byte | -128 to 127 | Small counters |
| `INT16` | 2 bytes | -32,768 to 32,767 | Enum-like values |
| `INT32` | 4 bytes | ±2.1 billion | Standard integers |
| `INT64` | 8 bytes | ±9.2 quintillion | IDs, timestamps |
| `FLOAT` | 4 bytes | IEEE 754 | Scores, coordinates |
| `DOUBLE` | 8 bytes | IEEE 754 | High-precision values |
| `VARCHAR` | Variable | Up to `max_length` | Text, names, URLs |

### Composite Fields

| DataType | Description | Parameters |
|----------|-------------|------------|
| `JSON` | Arbitrary JSON object | None |
| `ARRAY` | Typed array of scalars | `element_type`, `max_capacity` |

## Creating a Schema

```python
from pymilvus import MilvusClient, DataType

client = MilvusClient("./demo.db")
schema = client.create_schema()

# Primary key — INT64 or VARCHAR
schema.add_field(
    field_name="id",
    datatype=DataType.INT64,
    is_primary=True,
    auto_id=False,
)

# Dense vector field
schema.add_field(
    field_name="embedding",
    datatype=DataType.FLOAT_VECTOR,
    dim=768,
)

# Scalar fields for filtering
schema.add_field(
    field_name="title",
    datatype=DataType.VARCHAR,
    max_length=512,
)

schema.add_field(
    field_name="category",
    datatype=DataType.VARCHAR,
    max_length=64,
)

schema.add_field(
    field_name="score",
    datatype=DataType.FLOAT,
)
```

## Primary Key Options

### Auto-Generated IDs

```python
schema.add_field(
    field_name="id",
    datatype=DataType.INT64,
    is_primary=True,
    auto_id=True,  # Milvus generates unique IDs
)
```

With `auto_id=True`, omit the `id` field when inserting data.

### VARCHAR Primary Keys

```python
schema.add_field(
    field_name="doc_id",
    datatype=DataType.VARCHAR,
    is_primary=True,
    auto_id=False,
    max_length=128,
)
```

## Vector Field Configurations

### Multiple Vector Fields (for Hybrid Search)

```python
# Dense text embedding
schema.add_field(
    field_name="text_dense",
    datatype=DataType.FLOAT_VECTOR,
    dim=768,
)

# Sparse text embedding (BM25 or SPLADE)
schema.add_field(
    field_name="text_sparse",
    datatype=DataType.SPARSE_FLOAT_VECTOR,
)

# Image embedding
schema.add_field(
    field_name="image_dense",
    datatype=DataType.FLOAT_VECTOR,
    dim=512,
)
```

### Binary Vectors

```python
schema.add_field(
    field_name="fingerprint",
    datatype=DataType.BINARY_VECTOR,
    dim=256,  # must be multiple of 8
)
```

## Nullable Fields

```python
schema.add_field(
    field_name="description",
    datatype=DataType.VARCHAR,
    max_length=1000,
    nullable=True,  # allows NULL values
)
```

NULL values are skipped during vector search but participate in scalar filtering with `IS NULL` / `IS NOT NULL`.

## Default Values

```python
schema.add_field(
    field_name="status",
    datatype=DataType.VARCHAR,
    max_length=32,
    default_value="active",
)

schema.add_field(
    field_name="priority",
    datatype=DataType.INT32,
    default_value=0,
)
```

## Dynamic Fields

Enable dynamic fields to store arbitrary metadata without predefined schema:

```python
schema = client.create_schema(enable_dynamic_field=True)

# Only define required fields
schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True)
schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=384)

# Extra fields stored in $meta at insert time
data = [
    {"id": 1, "vector": [...], "author": "Alice", "year": 2024},  # author, year are dynamic
    {"id": 2, "vector": [...], "author": "Bob", "tags": ["ml"]},  # tags is dynamic
]
```

Dynamic fields are queryable and filterable like regular fields.

## Array Fields

```python
schema.add_field(
    field_name="tags",
    datatype=DataType.ARRAY,
    element_type=DataType.VARCHAR,
    max_capacity=10,
    max_length=64,
)

schema.add_field(
    field_name="scores",
    datatype=DataType.ARRAY,
    element_type=DataType.FLOAT,
    max_capacity=5,
)
```

Array filtering uses `ARRAY_CONTAINS()`, `ARRAY_CONTAINS_ALL()`, `ARRAY_CONTAINS_ANY()`, and `ARRAY_LENGTH()`.

## JSON Fields

```python
schema.add_field(
    field_name="metadata",
    datatype=DataType.JSON,
)

# Insert with arbitrary JSON
data = [
    {"id": 1, "vector": [...], "metadata": {"source": "web", "confidence": 0.95}},
    {"id": 2, "vector": [...], "metadata": {"source": "pdf", "pages": [1, 5]}},
]

# Filter on JSON keys
results = client.search(
    collection_name="docs",
    data=[query_vector],
    filter='metadata["source"] == "web"',
    limit=10,
)
```

## BM25 Function Fields

For full-text search, define a BM25 function that auto-generates sparse vectors from text:

```python
from pymilvus import Function, FunctionType

schema.add_field(field_name="text", datatype=DataType.VARCHAR, max_length=2000, enable_analyzer=True)
schema.add_field(field_name="text_sparse", datatype=DataType.SPARSE_FLOAT_VECTOR)

bm25_fn = Function(
    name="text_bm25",
    input_field_names=["text"],
    output_field_names=["text_sparse"],
    function_type=FunctionType.BM25,
)
schema.add_function(bm25_fn)
```

## Schema Design Patterns

### RAG Document Store

```python
schema = client.create_schema(enable_dynamic_field=True)
schema.add_field("id", DataType.INT64, is_primary=True, auto_id=True)
schema.add_field("embedding", DataType.FLOAT_VECTOR, dim=1536)
schema.add_field("text", DataType.VARCHAR, max_length=8000)
schema.add_field("source", DataType.VARCHAR, max_length=512)
schema.add_field("chunk_index", DataType.INT32)
```

### E-Commerce Product Catalog

```python
schema = client.create_schema()
schema.add_field("product_id", DataType.VARCHAR, is_primary=True, max_length=32)
schema.add_field("image_embedding", DataType.FLOAT_VECTOR, dim=512)
schema.add_field("text_embedding", DataType.FLOAT_VECTOR, dim=768)
schema.add_field("name", DataType.VARCHAR, max_length=256)
schema.add_field("price", DataType.FLOAT)
schema.add_field("category", DataType.VARCHAR, max_length=64)
schema.add_field("tags", DataType.ARRAY, element_type=DataType.VARCHAR, max_capacity=10, max_length=32)
```

### Multi-Modal Search

```python
schema = client.create_schema()
schema.add_field("id", DataType.INT64, is_primary=True, auto_id=True)
schema.add_field("text_dense", DataType.FLOAT_VECTOR, dim=768)
schema.add_field("text_sparse", DataType.SPARSE_FLOAT_VECTOR)
schema.add_field("image_dense", DataType.FLOAT_VECTOR, dim=512)
schema.add_field("content", DataType.VARCHAR, max_length=5000, enable_analyzer=True)
```

## Common Pitfalls

- **Forgetting `max_length` on VARCHAR** — required, will error without it
- **Wrong `dim` for embeddings** — must match your model's output dimension exactly
- **Using `auto_id=True` then providing IDs** — Milvus ignores provided IDs silently
- **Exceeding `max_capacity` on arrays** — inserts with over-length arrays are rejected
- **Not enabling `enable_analyzer` for BM25** — full-text search won't tokenize the field
