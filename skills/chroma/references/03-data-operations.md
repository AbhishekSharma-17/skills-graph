# Chroma — Data Operations

> Source: [docs.trychroma.com/docs/collections](https://docs.trychroma.com/docs/collections)

## Table of Contents

- [Adding Data](#adding-data)
- [Updating Data](#updating-data)
- [Upserting Data](#upserting-data)
- [Deleting Data](#deleting-data)
- [IDs](#ids)
- [Documents](#documents)
- [Embeddings](#embeddings)
- [Metadata](#metadata)
- [Common Pitfalls](#common-pitfalls)

## Adding Data

The `.add()` method inserts new records into a collection. Each record requires a unique ID.

### Documents with Auto-Embedding

Chroma generates embeddings automatically using the collection's embedding function.

```python
collection.add(
    ids=["doc1", "doc2", "doc3"],
    documents=[
        "Chroma is an open-source vector database",
        "It supports semantic search and filtering",
        "Embeddings are generated automatically",
    ],
    metadatas=[
        {"source": "readme", "chapter": 1},
        {"source": "docs", "chapter": 5},
        {"source": "tutorial", "chapter": 2},
    ],
)
```

```typescript
await collection.add({
  ids: ["doc1", "doc2", "doc3"],
  documents: [
    "Chroma is an open-source vector database",
    "It supports semantic search and filtering",
    "Embeddings are generated automatically",
  ],
  metadatas: [
    { source: "readme", chapter: 1 },
    { source: "docs", chapter: 5 },
    { source: "tutorial", chapter: 2 },
  ],
});
```

### Documents with Pre-Computed Embeddings

Supply both — Chroma stores the embeddings without re-processing.

```python
collection.add(
    ids=["doc1"],
    documents=["Some text to store"],
    embeddings=[[0.1, 0.2, 0.3, ...]],
    metadatas=[{"source": "manual"}],
)
```

### Embeddings Only (No Documents)

Store vectors with metadata when documents are managed externally (images, large files).

```python
collection.add(
    ids=["img1", "img2"],
    embeddings=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
    metadatas=[
        {"path": "/images/cat.jpg", "label": "cat"},
        {"path": "/images/dog.jpg", "label": "dog"},
    ],
)
```

### Rust (Requires Pre-Computed Embeddings)

```rust
collection
    .add(
        vec!["id1".to_string(), "id2".to_string()],
        vec![vec![0.1, 0.2, 0.3], vec![0.4, 0.5, 0.6]],
        Some(vec![
            Some("Document about pineapple".to_string()),
            Some("Document about oranges".to_string()),
        ]),
        None, // metadatas
        None, // uris
    )
    .await?;
```

**Key behavior:** If you add a record with an ID that already exists, it will be silently ignored (no error thrown). Use `upsert()` to overwrite existing records.

## Updating Data

The `.update()` method modifies existing records by ID. Only provided fields are changed.

```python
collection.update(
    ids=["doc1", "doc2"],
    documents=["Updated text for doc1", "Updated text for doc2"],
    metadatas=[
        {"source": "readme", "chapter": 2, "reviewed": True},
        {"source": "docs", "chapter": 6},
    ],
)
```

```typescript
await collection.update({
  ids: ["doc1", "doc2"],
  documents: ["Updated text for doc1", "Updated text for doc2"],
  metadatas: [
    { source: "readme", chapter: 2, reviewed: true },
    { source: "docs", chapter: 6 },
  ],
});
```

**Parameters:**

| Parameter | Required | Description |
|-----------|----------|-------------|
| `ids` | Yes | Record IDs to update |
| `documents` | No | New document text (triggers re-embedding if no embeddings provided) |
| `embeddings` | No | New embedding vectors |
| `metadatas` | No | New metadata (replaces entire metadata object per record) |

**Key behavior:** If an ID is not found in the collection, an error will be logged and that update is ignored.

## Upserting Data

The `.upsert()` method combines add and update: creates new records or updates existing ones based on ID presence.

```python
collection.upsert(
    ids=["doc1", "doc4"],
    documents=[
        "Updated existing doc1",
        "Brand new doc4",
    ],
    metadatas=[
        {"source": "readme", "version": 2},
        {"source": "changelog", "version": 1},
    ],
)
```

```typescript
await collection.upsert({
  ids: ["doc1", "doc4"],
  documents: [
    "Updated existing doc1",
    "Brand new doc4",
  ],
  metadatas: [
    { source: "readme", version: 2 },
    { source: "changelog", version: 1 },
  ],
});
```

**Use `upsert()` instead of `add()` when** you may be re-processing data and don't want to track which IDs already exist.

## Deleting Data

The `.delete()` method removes records by ID or by filter. This is destructive and irreversible.

### By IDs

```python
collection.delete(ids=["doc1", "doc2", "doc3"])
```

```typescript
await collection.delete({ ids: ["doc1", "doc2", "doc3"] });
```

### By Metadata Filter

```python
collection.delete(where={"chapter": "20"})
```

```typescript
await collection.delete({ where: { chapter: "20" } });
```

### Rust

```rust
collection
    .delete(
        Some(vec!["id1".to_string(), "id2".to_string()]),
        None, // where clause
    )
    .await?;
```

## IDs

- **Required** for every record
- Must be **unique strings** within the collection
- Chroma does not auto-generate IDs — you must provide them
- Common patterns: UUIDs, content hashes, sequential identifiers

```python
import uuid

ids = [str(uuid.uuid4()) for _ in range(len(documents))]
```

## Documents

- Raw text strings stored alongside embeddings
- Used for auto-embedding when no `embeddings` parameter is provided
- Returned in query results when `include=["documents"]`
- Optional — you can store embeddings without documents

## Embeddings

- Numeric vectors (list of floats)
- All embeddings in a collection must have the same dimensionality
- If both `documents` and `embeddings` are provided, the embeddings are stored as-is
- If only `documents` are provided, the collection's embedding function generates vectors

## Metadata

Metadata is a dictionary of key-value pairs attached to each record.

**Supported value types:**
- Strings
- Integers
- Floats
- Booleans
- Arrays of the above (uniform type, no empty arrays, no nested arrays)

```python
metadatas=[
    {
        "source": "website",           # string
        "page": 42,                    # integer
        "score": 0.95,                 # float
        "reviewed": True,              # boolean
        "tags": ["python", "ml"],      # string array
        "versions": [1, 2, 3],         # integer array
    }
]
```

**Invalid metadata:**
- Nested objects: `{"author": {"name": "Alice"}}` — not supported
- Mixed-type arrays: `["hello", 42]` — all elements must be same type
- Empty arrays: `[]` — not allowed
- `None` values — not supported

## Common Pitfalls

1. **add() silently ignores duplicates** — If an ID already exists, the record is not updated. Use `upsert()` when you want to overwrite.

2. **update() replaces entire metadata** — Updating metadata replaces the whole metadata dict, not individual keys. To preserve existing keys, read the record first, merge, then update.

3. **Embedding dimension mismatch** — All records in a collection must have the same embedding dimension. Mixing dimensions causes errors.

4. **IDs must be strings** — Passing integers as IDs will raise an error. Always convert: `ids=[str(i) for i in range(10)]`.

5. **Metadata None values** — Setting a metadata value to `None` will raise an error. To remove a key, update the record with metadata that omits that key.
