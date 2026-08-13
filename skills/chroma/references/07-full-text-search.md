# Chroma — Full-Text Search

> Source: [docs.trychroma.com/docs/querying-collections/full-text-search](https://docs.trychroma.com/docs/querying-collections/full-text-search)

## Table of Contents

- [Overview](#overview)
- [Text Search Operators](#text-search-operators)
- [Regex Search](#regex-search)
- [Combining Text Filters](#combining-text-filters)
- [Combining with Vector Search](#combining-with-vector-search)
- [Combining with Metadata Filters](#combining-with-metadata-filters)
- [Performance Considerations](#performance-considerations)
- [Common Pitfalls](#common-pitfalls)

## Overview

Chroma provides full-text search and regex matching through the `where_document` parameter, available on both `query()` and `get()` methods. These filters work on the raw document text stored alongside embeddings.

Full-text search in Chroma is **case-sensitive** and uses exact substring matching, not tokenized or stemmed search. For more advanced text search capabilities, use Chroma Cloud's Search API.

## Text Search Operators

### $contains — Exact Substring Match

```python
# Find documents containing "vector database"
results = collection.get(
    where_document={"$contains": "vector database"},
)

# Combined with query
results = collection.query(
    query_texts=["machine learning"],
    where_document={"$contains": "neural network"},
    n_results=10,
)
```

```typescript
const results = await collection.get({
  whereDocument: { $contains: "vector database" },
});
```

### $not_contains — Exclude Substring

```python
# Exclude documents containing "deprecated"
results = collection.get(
    where_document={"$not_contains": "deprecated"},
)
```

## Regex Search

### $regex — Pattern Match

```python
# Match email addresses
results = collection.get(
    where_document={
        "$regex": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    },
)

# Match documents starting with uppercase letter
results = collection.get(
    where_document={"$regex": r"^[A-Z]"},
)

# Match version numbers
results = collection.get(
    where_document={"$regex": r"v\d+\.\d+\.\d+"},
)
```

```typescript
const results = await collection.get({
  whereDocument: { $regex: "v\\d+\\.\\d+\\.\\d+" },
});
```

### $not_regex — Exclude Pattern

```python
# Exclude documents with TODO markers
results = collection.get(
    where_document={"$not_regex": r"TODO|FIXME|HACK"},
)
```

## Combining Text Filters

Use `$and` and `$or` to combine multiple document filters.

### All Conditions Must Match

```python
results = collection.query(
    query_texts=["deployment"],
    where_document={
        "$and": [
            {"$contains": "kubernetes"},
            {"$not_contains": "deprecated"},
        ]
    },
    n_results=10,
)
```

### Any Condition Must Match

```python
results = collection.get(
    where_document={
        "$or": [
            {"$contains": "python"},
            {"$contains": "typescript"},
        ]
    },
)
```

### Mixed Operators

```python
results = collection.query(
    query_texts=["API reference"],
    where_document={
        "$and": [
            {"$contains": "endpoint"},
            {"$regex": r"(GET|POST|PUT|DELETE)\s+/api/"},
        ]
    },
    n_results=20,
)
```

## Combining with Vector Search

When used with `query()`, document filters narrow the search space before similarity ranking:

```python
# Semantic search + text filter
results = collection.query(
    query_texts=["how to deploy"],
    n_results=5,
    where_document={"$contains": "docker"},
)
```

**Execution order:**
1. Filter documents by `where_document` criteria
2. Rank filtered results by embedding similarity
3. Return top `n_results`

## Combining with Metadata Filters

Both `where` and `where_document` can be used in the same query:

```python
results = collection.query(
    query_texts=["getting started guide"],
    n_results=10,
    where={"category": {"$in": ["tutorial", "quickstart"]}},
    where_document={
        "$and": [
            {"$contains": "install"},
            {"$not_contains": "Windows"},
        ]
    },
)
```

```typescript
const results = await collection.query({
  queryTexts: ["getting started guide"],
  nResults: 10,
  where: { category: { $in: ["tutorial", "quickstart"] } },
  whereDocument: {
    $and: [
      { $contains: "install" },
      { $not_contains: "Windows" },
    ],
  },
});
```

## Performance Considerations

- **$contains** scans document text linearly — fast for small collections, slower for millions of records
- **$regex** is significantly slower than `$contains` for simple substring matching
- Pre-filter with `where` (metadata) first to reduce the document scan space
- For production full-text search at scale, consider Chroma Cloud's Search API which uses optimized indexes

## Common Pitfalls

1. **Case-sensitive matching** — `$contains: "Python"` will NOT match `"python"`. Normalize case in your documents at insert time if case-insensitive search is needed.

2. **Not tokenized search** — `$contains: "vector database"` matches the exact phrase, not individual words. `"This is a vector and database"` would NOT match.

3. **Regex escaping** — Special regex characters (`.`, `*`, `+`, `?`, etc.) must be escaped. Use raw strings in Python: `r"v\d+\.\d+"`.

4. **Empty results from over-filtering** — Combining restrictive `where`, `where_document`, and vector similarity can return zero results. Start broad and narrow down.

5. **No stemming or fuzzy matching** — Chroma's built-in text search is exact. `"running"` will not match `"run"`. For fuzzy matching, use embedding-based similarity search instead.
