# Chroma — Metadata Filtering

> Source: [docs.trychroma.com/docs/querying-collections/metadata-filtering](https://docs.trychroma.com/docs/querying-collections/metadata-filtering)

## Table of Contents

- [Overview](#overview)
- [Where Clauses](#where-clauses)
- [Comparison Operators](#comparison-operators)
- [Inclusion Operators](#inclusion-operators)
- [Array Operators](#array-operators)
- [Logical Operators](#logical-operators)
- [Where Document Clauses](#where-document-clauses)
- [Combining Where and Where Document](#combining-where-and-where-document)
- [Complex Filter Examples](#complex-filter-examples)
- [Common Pitfalls](#common-pitfalls)

## Overview

Chroma supports metadata-based filtering on `query()`, `get()`, and `delete()` operations using `where` and `where_document` clauses. Filters are applied before similarity ranking, narrowing the search space.

## Where Clauses

The `where` parameter filters by metadata fields attached to records.

### Direct Equality (Shorthand)

```python
# These are equivalent:
collection.query(query_texts=["search"], where={"source": "docs"})
collection.query(query_texts=["search"], where={"source": {"$eq": "docs"}})
```

### With Operators

```python
collection.query(
    query_texts=["search"],
    where={"page": {"$gt": 10}},
)
```

## Comparison Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `$eq` | Equal to (default) | `{"field": {"$eq": "value"}}` |
| `$ne` | Not equal to | `{"field": {"$ne": "value"}}` |
| `$gt` | Greater than | `{"field": {"$gt": 10}}` |
| `$gte` | Greater than or equal | `{"field": {"$gte": 10}}` |
| `$lt` | Less than | `{"field": {"$lt": 100}}` |
| `$lte` | Less than or equal | `{"field": {"$lte": 100}}` |

```python
# Numeric comparison
results = collection.query(
    query_texts=["search"],
    where={"score": {"$gte": 0.8}},
)

# String comparison
results = collection.query(
    query_texts=["search"],
    where={"category": {"$ne": "draft"}},
)
```

## Inclusion Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `$in` | Value is in the provided list | `{"field": {"$in": ["a", "b"]}}` |
| `$nin` | Value is NOT in the list (or key absent) | `{"field": {"$nin": ["x", "y"]}}` |

```python
# Match any of multiple categories
results = collection.query(
    query_texts=["search"],
    where={"source": {"$in": ["docs", "readme", "tutorial"]}},
)

# Exclude specific sources
results = collection.query(
    query_texts=["search"],
    where={"source": {"$nin": ["draft", "archived"]}},
)
```

## Array Operators

For metadata fields that contain arrays (e.g., tags).

| Operator | Description | Example |
|----------|-------------|---------|
| `$contains` | Array includes the value | `{"tags": {"$contains": "python"}}` |
| `$not_contains` | Array does not include the value | `{"tags": {"$not_contains": "deprecated"}}` |

```python
# Find records tagged with "python"
results = collection.query(
    query_texts=["search"],
    where={"tags": {"$contains": "python"}},
)

# Exclude deprecated items
results = collection.query(
    query_texts=["search"],
    where={"tags": {"$not_contains": "deprecated"}},
)
```

**Note:** Array metadata was added in Chroma 1.5.0. Arrays must be uniform type (all strings, all ints, etc.) and non-empty.

## Logical Operators

Combine multiple conditions with `$and` (all must match) or `$or` (any must match).

### $and — All Conditions Must Match

```python
results = collection.query(
    query_texts=["search"],
    where={
        "$and": [
            {"source": {"$eq": "docs"}},
            {"page": {"$gte": 10}},
            {"reviewed": True},
        ]
    },
)
```

### $or — Any Condition Must Match

```python
results = collection.query(
    query_texts=["search"],
    where={
        "$or": [
            {"source": "readme"},
            {"source": "tutorial"},
        ]
    },
)
```

### Nested Logical Operators

```python
results = collection.query(
    query_texts=["search"],
    where={
        "$and": [
            {"page": {"$gte": 5}},
            {
                "$or": [
                    {"source": "docs"},
                    {"source": "api_reference"},
                ]
            },
        ]
    },
)
```

## Where Document Clauses

The `where_document` parameter filters by the text content of documents.

| Operator | Description | Example |
|----------|-------------|---------|
| `$contains` | Document contains exact text | `{"$contains": "vector"}` |
| `$not_contains` | Document does not contain text | `{"$not_contains": "deprecated"}` |
| `$regex` | Document matches regex pattern | `{"$regex": "\\bvector\\b"}` |
| `$not_regex` | Document does not match regex | `{"$not_regex": "TODO"}` |

```python
# Full-text search
results = collection.query(
    query_texts=["search"],
    where_document={"$contains": "installation guide"},
)

# Regex pattern matching
results = collection.get(
    where_document={"$regex": "^[A-Z].*\\.$"},
)

# Exclude documents containing specific text
results = collection.query(
    query_texts=["search"],
    where_document={"$not_contains": "DEPRECATED"},
)
```

### Logical Operators with Where Document

```python
results = collection.query(
    query_texts=["search"],
    where_document={
        "$and": [
            {"$contains": "python"},
            {"$not_contains": "deprecated"},
        ]
    },
)
```

**Important:** Full-text search with `$contains` is **case-sensitive**.

## Combining Where and Where Document

Apply both metadata and document content filters simultaneously.

```python
results = collection.query(
    query_texts=["machine learning tutorial"],
    n_results=10,
    where={
        "$and": [
            {"source": {"$in": ["docs", "tutorials"]}},
            {"page": {"$gte": 1}},
        ]
    },
    where_document={"$contains": "neural network"},
)
```

Execution order:
1. `where` narrows by metadata
2. `where_document` narrows by document content
3. Similarity ranking applies to remaining records

## Complex Filter Examples

### Multi-Field Filter with Range

```python
results = collection.query(
    query_texts=["deployment"],
    where={
        "$and": [
            {"category": {"$in": ["devops", "infrastructure"]}},
            {"year": {"$gte": 2024}},
            {"score": {"$gt": 0.7}},
        ]
    },
    n_results=20,
)
```

### Tag-Based Discovery

```python
results = collection.query(
    query_texts=["getting started"],
    where={
        "$and": [
            {"tags": {"$contains": "beginner"}},
            {"tags": {"$not_contains": "advanced"}},
        ]
    },
)
```

### Exclude Drafts with Text Filter

```python
results = collection.query(
    query_texts=["API reference"],
    where={"status": {"$ne": "draft"}},
    where_document={"$not_contains": "TODO"},
)
```

## Common Pitfalls

1. **$contains on metadata vs documents** — In `where`, `$contains` checks if an array field contains a scalar value. In `where_document`, it checks if the document text contains a substring. Different semantics.

2. **Case-sensitive text search** — `where_document` with `$contains` is case-sensitive. `"Python"` will not match `"python"`.

3. **Filters reduce result count** — If filters are too restrictive, you may get fewer results than `n_results`. Chroma returns what matches, not padded results.

4. **No null/None filtering** — You cannot filter for records where a metadata key is absent. Use sentinel values instead.

5. **Regex performance** — Complex regex patterns in `where_document` can be slow on large collections. Prefer `$contains` for simple substring matching.
