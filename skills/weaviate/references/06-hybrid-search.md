# Weaviate — Hybrid Search

> Source: [docs.weaviate.io](https://docs.weaviate.io/weaviate/search/hybrid) | Version: v1.37

## Table of Contents
- [Overview](#overview)
- [Basic Hybrid Query](#basic-hybrid-query)
- [Alpha Parameter](#alpha-parameter)
- [Fusion Algorithms](#fusion-algorithms)
- [Query Properties and Weighting](#query-properties-and-weighting)
- [Search Operators](#search-operators)
- [Custom Search Vector](#custom-search-vector)
- [Named Vectors](#named-vectors)
- [Vector Distance Threshold](#vector-distance-threshold)
- [Score Metadata](#score-metadata)
- [Filtering and Pagination](#filtering-and-pagination)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

Hybrid search combines vector similarity and BM25 keyword scoring in a single query. It runs both searches in parallel, then fuses the result sets using a configurable algorithm and weighting.

This is Weaviate's most versatile search mode — it captures semantic meaning (via vectors) while still respecting exact keyword matches (via BM25).

```
Query: "best machine learning framework"
         │
    ┌────┴────┐
    │         │
  Vector    BM25
  Search    Search
    │         │
    └────┬────┘
         │
    Fusion Algorithm
    (Relative Score)
         │
    Combined Results
```

## Basic Hybrid Query

### Python

```python
articles = client.collections.use("Article")
response = articles.query.hybrid(
    query="machine learning frameworks",
    limit=5,
)
for obj in response.objects:
    print(obj.properties["title"])
```

### TypeScript

```typescript
const articles = client.collections.use('Article');
const result = await articles.query.hybrid('machine learning frameworks', {
  limit: 5,
});
for (const obj of result.objects) {
  console.log(obj.properties.title);
}
```

## Alpha Parameter

Controls the balance between vector and keyword search:

| Alpha | Behavior |
|-------|----------|
| `1.0` | Pure vector search |
| `0.75` | Favor vector, some keyword influence |
| `0.5` | Equal weight (default) |
| `0.25` | Favor keyword, some vector influence |
| `0.0` | Pure keyword (BM25) search |

```python
# Favor semantic similarity
response = articles.query.hybrid(
    query="AI innovations",
    alpha=0.75,
    limit=5,
)

# Favor exact keyword matching
response = articles.query.hybrid(
    query="GPT-4 benchmark",
    alpha=0.25,
    limit=5,
)
```

### When to Adjust Alpha

- **Technical terms, product names, codes** → lower alpha (favor keywords)
- **Conceptual queries, natural language** → higher alpha (favor vectors)
- **Mixed queries** → default 0.5

## Fusion Algorithms

### Relative Score Fusion (Default since v1.24)

Uses actual similarity/BM25 scores from both searches. Produces better rankings when result sets have varying score distributions.

```python
from weaviate.classes.query import HybridFusion

response = articles.query.hybrid(
    query="data science",
    fusion_type=HybridFusion.RELATIVE_SCORE,
    limit=5,
)
```

### Ranked Fusion

Uses rank positions instead of scores. Simpler but less precise.

```python
response = articles.query.hybrid(
    query="data science",
    fusion_type=HybridFusion.RANKED,
    limit=5,
)
```

Relative Score Fusion is preferred for most use cases. Only use Ranked Fusion if you need backward compatibility.

## Query Properties and Weighting

Restrict the keyword component to specific properties with optional boosting:

```python
response = articles.query.hybrid(
    query="deep learning",
    query_properties=["title^2", "body"],  # BM25 on title (2x boost) and body
    alpha=0.5,
    limit=5,
)
```

This only affects the BM25 component. The vector component always uses the full vectorized content.

## Search Operators

Control BM25 token matching within hybrid search:

### OR with Minimum Match

```python
from weaviate.classes.query import BM25Operator

response = articles.query.hybrid(
    query="Australian mammal cute",
    bm25_operator=BM25Operator.or_(minimum_match=2),
    limit=5,
)
```

### AND Operator

```python
response = articles.query.hybrid(
    query="Python deep learning",
    bm25_operator=BM25Operator.and_(),
    limit=5,
)
```

## Custom Search Vector

Supply an explicit vector for the vector component while using the query text for BM25:

```python
query_vector = embedding_model.encode("deep learning").tolist()

response = articles.query.hybrid(
    query="deep learning tutorial",  # Used for BM25
    vector=query_vector,              # Used for vector search
    alpha=0.5,
    limit=5,
)
```

This lets you use a different vectorization for the query than the one configured on the collection.

## Named Vectors

When a collection has multiple named vectors, specify which to use for the vector component:

```python
reviews = client.collections.use("ProductReview")
response = reviews.query.hybrid(
    query="excellent battery life",
    target_vector="review_vector",
    alpha=0.75,
    limit=5,
)
```

```typescript
const result = await reviews.query.hybrid('excellent battery life', {
  targetVector: 'review_vector',
  alpha: 0.75,
  limit: 5,
});
```

## Vector Distance Threshold

Limit the vector component to objects within a maximum distance:

```python
from weaviate.classes.query import HybridVector, Move

response = articles.query.hybrid(
    query="California wine",
    max_vector_distance=0.4,
    alpha=0.75,
    limit=5,
)
```

### Move Towards/Away (Concept Steering)

```python
response = articles.query.hybrid(
    query="wine",
    vector=HybridVector.near_text(
        query="French wine",
        move_away=Move(force=0.5, concepts=["cheap", "mass-produced"]),
        move_to=Move(force=0.3, concepts=["premium", "vintage"]),
    ),
    alpha=0.75,
    limit=5,
)
```

## Score Metadata

Retrieve combined scores and explanations:

```python
from weaviate.classes.query import MetadataQuery

response = articles.query.hybrid(
    query="machine learning",
    alpha=0.5,
    return_metadata=MetadataQuery(score=True, explain_score=True),
    limit=5,
)
for obj in response.objects:
    print(f"Score: {obj.metadata.score:.4f}")
    print(f"Explanation: {obj.metadata.explain_score}")
```

The `explain_score` field shows the individual vector and BM25 contributions.

## Filtering and Pagination

### Property Filters

```python
from weaviate.classes.query import Filter

response = articles.query.hybrid(
    query="AI research",
    filters=Filter.by_property("category").equal("technology"),
    alpha=0.75,
    limit=5,
)
```

### Pagination

```python
response = articles.query.hybrid(
    query="technology",
    limit=10,
    offset=20,
)
```

### GroupBy

```python
from weaviate.classes.query import GroupBy

response = articles.query.hybrid(
    query="technology",
    alpha=0.75,
    group_by=GroupBy(
        prop="category",
        objects_per_group=3,
        number_of_groups=5,
    ),
)
```

### Auto-Limit

Only works with Relative Score Fusion:

```python
response = articles.query.hybrid(
    query="technology",
    fusion_type=HybridFusion.RELATIVE_SCORE,
    auto_limit=1,
)
```

## Common Pitfalls

1. **Alpha = 0.5 is not always best**: For product search or technical docs, pure keyword (alpha=0) or keyword-heavy (alpha=0.25) often outperforms balanced hybrid. Experiment with your data.

2. **Ranked Fusion with auto_limit**: Auto-limit only works with Relative Score Fusion. Using it with Ranked Fusion silently ignores the setting.

3. **No vectorizer → hybrid breaks**: Hybrid search needs both a vectorizer (for the vector component) and an inverted index (for BM25). If either is missing, one component fails silently.

4. **Query properties affect BM25 only**: Setting `query_properties` restricts keyword search to those fields. The vector component still uses the full vectorized content. This can cause confusing rankings.

5. **High alpha with exact terms**: If users search for exact product IDs or codes, high alpha weights the (unhelpful) semantic similarity over the (critical) exact match. Lower alpha for such queries.

## Related Topics

- Similarity Search → `04-similarity-search.md`
- Keyword Search → `05-keyword-search.md`
- Filters → `07-filters.md`
- Reranking → `09-reranking-aggregation.md`
