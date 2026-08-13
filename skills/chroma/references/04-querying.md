# Chroma — Querying

> Source: [docs.trychroma.com/docs/querying-collections](https://docs.trychroma.com/docs/querying-collections)

## Table of Contents

- [Query Method](#query-method)
- [Get Method](#get-method)
- [Result Format](#result-format)
- [Include Parameter](#include-parameter)
- [Pagination](#pagination)
- [Peek and Count](#peek-and-count)
- [Combining Filters with Queries](#combining-filters-with-queries)
- [Common Pitfalls](#common-pitfalls)

## Query Method

The `.query()` method performs similarity search using embeddings. It returns the nearest neighbors ranked by distance.

### Query with Text (Auto-Embedded)

```python
results = collection.query(
    query_texts=["What is a vector database?"],
    n_results=5,
)
```

```typescript
const results = await collection.query({
  queryTexts: ["What is a vector database?"],
  nResults: 5,
});
```

### Query with Pre-Computed Embeddings

```python
results = collection.query(
    query_embeddings=[[0.1, 0.2, 0.3, ...]],
    n_results=10,
)
```

### Multiple Queries in One Call

```python
results = collection.query(
    query_texts=[
        "vector database features",
        "how to install chroma",
    ],
    n_results=3,
)
# results["documents"][0] — results for first query
# results["documents"][1] — results for second query
```

### Query with Filters

```python
results = collection.query(
    query_texts=["machine learning"],
    n_results=5,
    where={"source": "research_papers"},
    where_document={"$contains": "neural"},
)
```

### Query with ID Constraints

```python
results = collection.query(
    query_texts=["search term"],
    n_results=5,
    ids=["doc1", "doc2", "doc3"],  # Only search within these IDs
)
```

### Full Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query_texts` | `list[str]` | — | Text queries (auto-embedded) |
| `query_embeddings` | `list[list[float]]` | — | Pre-computed query vectors |
| `n_results` | `int` | `10` | Max results per query |
| `ids` | `list[str]` | — | Restrict search to these IDs |
| `where` | `dict` | — | Metadata filter |
| `where_document` | `dict` | — | Document content filter |
| `include` | `list[str]` | `["documents", "metadatas", "distances"]` | Fields to return |

**Note:** Provide either `query_texts` or `query_embeddings`, not both.

## Get Method

The `.get()` method retrieves records without similarity ranking. Use for direct lookups and filtered fetches.

### Get by IDs

```python
results = collection.get(ids=["doc1", "doc2"])
```

```typescript
const results = await collection.get({ ids: ["doc1", "doc2"] });
```

### Get with Filters

```python
results = collection.get(
    where={"source": "readme"},
    limit=50,
)
```

### Get with Pagination

```python
# Page 1
page1 = collection.get(limit=100, offset=0)
# Page 2
page2 = collection.get(limit=100, offset=100)
```

### Full Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ids` | `list[str]` | — | Specific record IDs |
| `where` | `dict` | — | Metadata filter |
| `where_document` | `dict` | — | Document content filter |
| `limit` | `int` | — | Max records to return |
| `offset` | `int` | — | Pagination offset |
| `include` | `list[str]` | `["documents", "metadatas"]` | Fields to return |

## Result Format

Results use a **column-major** structure — parallel arrays where index `i` across all arrays refers to the same record.

### Query Result Structure

```python
{
    "ids": [["doc2", "doc1"]],           # list of lists (one per query)
    "documents": [["text2", "text1"]],
    "metadatas": [[{"k": "v"}, {"k": "v"}]],
    "distances": [[0.12, 0.45]],
    "embeddings": None,                   # only if requested in include
}
```

Note the **nested lists** — the outer list has one entry per input query.

### Get Result Structure

```python
{
    "ids": ["doc1", "doc2"],              # flat list
    "documents": ["text1", "text2"],
    "metadatas": [{"k": "v"}, {"k": "v"}],
    "embeddings": None,
}
```

Get results are **flat lists** (no nesting by query).

## Include Parameter

Controls which fields are returned. Omitting fields saves bandwidth and processing time.

```python
# Only IDs and distances
results = collection.query(
    query_texts=["search"],
    n_results=10,
    include=["distances"],
)

# Include embeddings (large payload)
results = collection.query(
    query_texts=["search"],
    n_results=10,
    include=["documents", "metadatas", "distances", "embeddings"],
)

# Get with embeddings
results = collection.get(
    ids=["doc1"],
    include=["documents", "metadatas", "embeddings"],
)
```

**Available include values:**

| Value | query() default | get() default | Description |
|-------|----------------|---------------|-------------|
| `"documents"` | Yes | Yes | Document text |
| `"metadatas"` | Yes | Yes | Metadata dicts |
| `"distances"` | Yes | No | Similarity distances |
| `"embeddings"` | No | No | Embedding vectors |
| `"uris"` | No | No | URI references |

## Pagination

Use `limit` and `offset` with `.get()` for pagination:

```python
page_size = 100
all_records = []
offset = 0

while True:
    page = collection.get(limit=page_size, offset=offset)
    if not page["ids"]:
        break
    all_records.extend(page["ids"])
    offset += page_size
```

**Note:** `.query()` does not support `offset`. Use `n_results` to control how many results are returned per query.

## Peek and Count

```python
# Quick inspection — returns first 10 records
sample = collection.peek()

# Total record count
total = collection.count()
```

## Combining Filters with Queries

Filters narrow the search space before similarity ranking is applied.

```python
results = collection.query(
    query_texts=["deployment guide"],
    n_results=5,
    where={
        "$and": [
            {"source": {"$eq": "docs"}},
            {"page": {"$gte": 10}},
        ]
    },
    where_document={"$contains": "kubernetes"},
)
```

The execution order is:
1. Apply `where` (metadata filter)
2. Apply `where_document` (text filter)
3. Rank remaining records by similarity to query
4. Return top `n_results`

## Common Pitfalls

1. **Query results are nested lists** — `results["documents"]` is `list[list[str]]`, not `list[str]`. Access the first query's results with `results["documents"][0]`.

2. **n_results > collection size** — If `n_results` exceeds the number of records (after filtering), Chroma returns all available results without error.

3. **Distance interpretation varies** — Lower distances mean closer matches. For cosine space, distance 0.0 means identical; for L2, distance varies with embedding magnitude.

4. **Embeddings not included by default** — To get embedding vectors in results, explicitly pass `include=["embeddings"]`. They are omitted by default to save bandwidth.

5. **get() has no ranking** — Records from `.get()` are returned in insertion order, not by relevance. Use `.query()` for similarity-ranked results.
