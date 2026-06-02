# Weaviate — Collections & Schema

> Source: [docs.weaviate.io](https://docs.weaviate.io/weaviate/manage-collections) | Version: v1.37

## Table of Contents
- [Core Concepts](#core-concepts)
- [Creating Collections](#creating-collections)
- [Property Data Types](#property-data-types)
- [Reading Collections](#reading-collections)
- [Updating Collections](#updating-collections)
- [Deleting Collections](#deleting-collections)
- [Adding Properties](#adding-properties)
- [Naming Conventions](#naming-conventions)
- [Common Pitfalls](#common-pitfalls)

---

## Core Concepts

A **collection** in Weaviate is analogous to a table in a relational database. Each collection contains:
- **Objects**: Data records with properties and vector embeddings
- **Properties**: Typed fields (text, int, bool, date, etc.)
- **Vector config**: How objects are vectorized and indexed
- **Inverted index**: For keyword search (BM25) and filtering
- **Generative config**: Which LLM to use for RAG queries

## Creating Collections

### Minimal (Auto-Schema)

```python
client.collections.create("Article")
```

```typescript
await client.collections.create({ name: 'Article' });
```

Weaviate auto-detects property types from inserted data. Not recommended for production.

### With Explicit Properties

```python
from weaviate.classes.config import Configure, Property, DataType

client.collections.create(
    "Article",
    properties=[
        Property(name="title", data_type=DataType.TEXT),
        Property(name="body", data_type=DataType.TEXT),
        Property(name="wordCount", data_type=DataType.INT),
        Property(name="isPublished", data_type=DataType.BOOL),
        Property(name="publishedAt", data_type=DataType.DATE),
        Property(name="rating", data_type=DataType.NUMBER),
    ],
)
```

```typescript
await client.collections.create({
  name: 'Article',
  properties: [
    { name: 'title', dataType: dataType.TEXT },
    { name: 'body', dataType: dataType.TEXT },
    { name: 'wordCount', dataType: dataType.INT },
    { name: 'isPublished', dataType: dataType.BOOL },
    { name: 'publishedAt', dataType: dataType.DATE },
    { name: 'rating', dataType: dataType.NUMBER },
  ],
});
```

### With Vectorizer and Generative Model

```python
from weaviate.classes.config import Configure, Property, DataType

client.collections.create(
    "Article",
    vector_config=Configure.Vectors.text2vec_openai(),
    generative_config=Configure.Generative.openai(),
    properties=[
        Property(name="title", data_type=DataType.TEXT),
        Property(name="body", data_type=DataType.TEXT),
    ],
)
```

### With Named Vectors

```python
from weaviate.classes.config import Configure, Property, DataType

client.collections.create(
    "WineReview",
    vector_config=[
        Configure.NamedVectors.text2vec_openai(
            name="title_vector",
            source_properties=["title"],
        ),
        Configure.NamedVectors.text2vec_openai(
            name="review_vector",
            source_properties=["review_body"],
        ),
    ],
    properties=[
        Property(name="title", data_type=DataType.TEXT),
        Property(name="review_body", data_type=DataType.TEXT),
        Property(name="country", data_type=DataType.TEXT),
    ],
)
```

### With Nested Objects

```python
from weaviate.classes.config import Property, DataType

client.collections.create(
    "Event",
    properties=[
        Property(name="title", data_type=DataType.TEXT),
        Property(
            name="location",
            data_type=DataType.OBJECT,
            nested_properties=[
                Property(name="city", data_type=DataType.TEXT),
                Property(name="country", data_type=DataType.TEXT),
                Property(name="lat", data_type=DataType.NUMBER),
                Property(name="lon", data_type=DataType.NUMBER),
            ],
        ),
    ],
)
```

## Property Data Types

| Type | Python | Description |
|------|--------|-------------|
| `TEXT` | `DataType.TEXT` | String, tokenized for search |
| `TEXT_ARRAY` | `DataType.TEXT_ARRAY` | Array of strings |
| `INT` | `DataType.INT` | Integer |
| `INT_ARRAY` | `DataType.INT_ARRAY` | Array of integers |
| `NUMBER` | `DataType.NUMBER` | Float / decimal |
| `NUMBER_ARRAY` | `DataType.NUMBER_ARRAY` | Array of floats |
| `BOOL` | `DataType.BOOL` | Boolean |
| `BOOL_ARRAY` | `DataType.BOOL_ARRAY` | Array of booleans |
| `DATE` | `DataType.DATE` | RFC 3339 datetime |
| `DATE_ARRAY` | `DataType.DATE_ARRAY` | Array of dates |
| `UUID` | `DataType.UUID` | UUID string |
| `UUID_ARRAY` | `DataType.UUID_ARRAY` | Array of UUIDs |
| `OBJECT` | `DataType.OBJECT` | Nested object |
| `OBJECT_ARRAY` | `DataType.OBJECT_ARRAY` | Array of nested objects |
| `BLOB` | `DataType.BLOB` | Base64-encoded binary |
| `GEO_COORDINATES` | `DataType.GEO_COORDINATES` | Lat/lon pair |
| `PHONE_NUMBER` | `DataType.PHONE_NUMBER` | Phone with country code |

## Reading Collections

### Check Existence

```python
exists = client.collections.exists("Article")
```

### Get Collection Config

```python
articles = client.collections.use("Article")
config = articles.config.get()
print(config.name)
print(config.properties)
print(config.vector_config)
```

### List All Collections

```python
response = client.collections.list_all(simple=False)
for name, config in response.items():
    print(f"{name}: {len(config.properties)} properties")
```

## Updating Collections

Mutable settings include description, inverted index params, and vector index params. Property types cannot be changed after creation.

```python
from weaviate.classes.config import Reconfigure, VectorFilterStrategy

articles = client.collections.use("Article")
articles.config.update(
    description="News and blog articles",
    inverted_index_config=Reconfigure.inverted_index(bm25_k1=1.5),
    vector_config=Reconfigure.Vectors.update(
        name="default",
        vector_index_config=Reconfigure.VectorIndex.hnsw(
            filter_strategy=VectorFilterStrategy.ACORN
        ),
    ),
)
```

## Deleting Collections

```python
# Delete single collection (deletes ALL objects in it)
client.collections.delete("Article")

# Delete multiple
client.collections.delete(["Article", "Category"])

# Delete all collections
client.collections.delete_all()
```

## Adding Properties

```python
articles = client.collections.use("Article")
articles.config.add_property(
    Property(name="onHomepage", data_type=DataType.BOOL)
)
```

Properties added after data import do not automatically index existing objects. New objects get the property indexed; existing objects return null for the new property until updated.

## Naming Conventions

- **Collection names**: Must start with uppercase letter (GraphQL requirement). Example: `Article`, `WineReview`
- **Property names**: Must start with lowercase letter. Example: `title`, `reviewBody`
- Weaviate auto-converts uppercase property names to lowercase
- Only alphanumeric characters and underscores allowed

## Common Pitfalls

1. **Auto-schema in production**: Without explicit property definitions, Weaviate infers types from the first object. A string "123" becomes TEXT, not INT. Always define schemas in production.

2. **Immutable property types**: Once a property is created with a data type, it cannot be changed. You must create a new collection to change types.

3. **Adding properties post-import**: New properties don't backfill existing objects. Query with `is_null` filter to find objects missing the new property.

4. **Collection name casing**: `article` is auto-converted to `Article`. Use PascalCase explicitly to avoid confusion.

5. **Nested object depth**: Nested objects support arbitrary depth but add query complexity. Prefer flat schemas when possible.

## Related Topics

- Vector Configuration → `02-vector-config.md`
- Data Operations → `03-data-operations.md`
- Multi-Tenancy → `10-multi-tenancy.md`
