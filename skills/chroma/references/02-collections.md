# Chroma — Collections

> Source: [docs.trychroma.com/docs/collections](https://docs.trychroma.com/docs/collections)

## Table of Contents

- [What Is a Collection](#what-is-a-collection)
- [Creating Collections](#creating-collections)
- [Retrieving Collections](#retrieving-collections)
- [Listing Collections](#listing-collections)
- [Modifying Collections](#modifying-collections)
- [Deleting Collections](#deleting-collections)
- [Collection Properties](#collection-properties)
- [Naming Rules](#naming-rules)
- [HNSW Configuration](#hnsw-configuration)
- [Distance Functions](#distance-functions)
- [Common Pitfalls](#common-pitfalls)

## What Is a Collection

A collection is a named group of embeddings, documents, and metadata. It is the primary organizational unit in Chroma — analogous to a table in relational databases or an index in Elasticsearch.

Each collection has:
- A unique name within its database
- An associated embedding function (default: `all-MiniLM-L6-v2`)
- An HNSW index configuration
- Optional metadata key-value pairs

## Creating Collections

### Basic Creation

```python
collection = client.create_collection(name="my_collection")
```

```typescript
const collection = await client.createCollection({
  name: "my_collection",
});
```

### With Embedding Function

```python
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

collection = client.create_collection(
    name="my_collection",
    embedding_function=OpenAIEmbeddingFunction(
        model_name="text-embedding-3-small"
    ),
)
```

### With HNSW Configuration

```python
collection = client.create_collection(
    name="my_collection",
    configuration={
        "hnsw": {
            "space": "cosine",
            "ef_construction": 200,
        }
    },
)
```

### With Metadata

```python
collection = client.create_collection(
    name="my_collection",
    metadata={"description": "Product documentation embeddings"},
)
```

## Retrieving Collections

### Get Existing

```python
collection = client.get_collection(name="my_collection")
```

```typescript
const collection = await client.getCollection({
  name: "my_collection",
});
```

### Get or Create

Creates the collection if it doesn't exist, returns it if it does.

```python
collection = client.get_or_create_collection(name="my_collection")
```

```typescript
const collection = await client.getOrCreateCollection({
  name: "my_collection",
});
```

## Listing Collections

```python
collections = client.list_collections()

# With pagination
collections = client.list_collections(limit=100, offset=0)
```

```typescript
const collections = await client.listCollections();
```

## Modifying Collections

Update name and/or metadata after creation.

```python
collection.modify(
    name="new_name",
    metadata={"description": "updated description"},
)
```

## Deleting Collections

```python
client.delete_collection(name="my_collection")
```

```typescript
await client.deleteCollection({ name: "my_collection" });
```

**Warning:** Deleting a collection is destructive and not reversible. All embeddings, documents, and metadata are permanently removed.

## Collection Properties

```python
collection.name          # Collection name
collection.metadata      # Collection metadata dict
collection.count()       # Number of records
collection.peek()        # First 10 records (for inspection)
```

## Naming Rules

Collection names must:
- Be **3–512 characters** long
- Start and end with a **lowercase letter or digit**
- May contain **dots (`.`), dashes (`-`), and underscores (`_`)**
- Must **not** contain consecutive dots (`..`)
- Must **not** be a valid IP address

Valid: `my-collection`, `docs_v2`, `project.embeddings`
Invalid: `ab` (too short), `My-Collection` (uppercase start), `192.168.1.1` (IP address)

## HNSW Configuration

HNSW (Hierarchical Navigable Small World) is the index algorithm for single-node deployments.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `space` | `str` | `"l2"` | Distance function: `l2`, `cosine`, `ip` |
| `ef_construction` | `int` | `100` | Build-time candidate list size. Higher = better quality, slower build |
| `ef_search` | `int` | `100` | Query-time candidate list. Modifiable after creation |
| `max_neighbors` | `int` | `16` | Max connections per node in the graph |
| `num_threads` | `int` | CPU cores | Threads for index operations |
| `batch_size` | `int` | `100` | Vectors processed per batch |
| `sync_threshold` | `int` | `1000` | Storage sync frequency |
| `resize_factor` | `float` | `1.2` | Index growth multiplier |

```python
collection = client.create_collection(
    name="high_recall",
    configuration={
        "hnsw": {
            "space": "cosine",
            "ef_construction": 200,
            "ef_search": 150,
            "max_neighbors": 32,
        }
    },
)
```

**Cloud note:** Chroma Cloud uses SPANN instead of HNSW. SPANN configuration is not user-customizable.

## Distance Functions

| Function | Parameter | Formula | Best For |
|----------|-----------|---------|----------|
| Squared L2 | `l2` (default) | `Σ(aᵢ - bᵢ)²` | Geometric proximity |
| Cosine | `cosine` | `1 - (a·b)/(‖a‖·‖b‖)` | Text embeddings (most common) |
| Inner Product | `ip` | `-a·b` | Recommendation systems |

**Tip:** For text embeddings from OpenAI, Cohere, or sentence-transformers, use `cosine`. It is the most common and recommended distance function for normalized embeddings.

## Common Pitfalls

1. **Default distance is L2, not cosine** — If your embeddings are normalized (most text embedding models), set `space: "cosine"` explicitly.

2. **Embedding function not persisted by default** — When using `get_collection()`, you must pass the same embedding function again. The collection stores the configuration but needs the function instance.

3. **get_or_create does not update config** — If the collection exists, `get_or_create_collection()` returns it as-is. It does not apply new configuration or metadata from the call.

4. **ef_search is the only tunable at query time** — All other HNSW parameters are fixed at creation. Plan `ef_construction` and `max_neighbors` carefully.
