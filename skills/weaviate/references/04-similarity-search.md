# Weaviate — Similarity (Vector) Search

> Source: [docs.weaviate.io](https://docs.weaviate.io/weaviate/search/similarity) | Version: v1.37

## Table of Contents
- [Overview](#overview)
- [Near Text Search](#near-text-search)
- [Near Vector Search](#near-vector-search)
- [Near Object Search](#near-object-search)
- [Near Image Search](#near-image-search)
- [Distance Threshold](#distance-threshold)
- [Pagination](#pagination)
- [Named Vectors](#named-vectors)
- [GroupBy](#groupby)
- [MMR Diversity Search](#mmr-diversity-search)
- [Combining with Filters](#combining-with-filters)
- [Return Metadata](#return-metadata)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

Vector similarity search finds objects whose vector embeddings are closest to a query vector. Weaviate supports four search operators:

| Operator | Input | Use Case |
|----------|-------|----------|
| `near_text` | Text string | Most common — auto-vectorized by configured model |
| `near_vector` | Raw vector | Pre-computed embeddings from external models |
| `near_object` | Object UUID | "Find similar to this" |
| `near_image` | Base64 image | Image similarity (requires multimodal vectorizer) |

## Near Text Search

Converts text to a vector using the collection's configured vectorizer, then finds nearest neighbors.

### Python

```python
from weaviate.classes.query import MetadataQuery

articles = client.collections.use("Article")
response = articles.query.near_text(
    query="artificial intelligence breakthroughs",
    limit=5,
    return_metadata=MetadataQuery(distance=True),
)
for obj in response.objects:
    print(f"{obj.properties['title']} (distance: {obj.metadata.distance:.4f})")
```

### TypeScript

```typescript
const articles = client.collections.use('Article');
const result = await articles.query.nearText('artificial intelligence breakthroughs', {
  limit: 5,
  returnMetadata: ['distance'],
});
for (const obj of result.objects) {
  console.log(`${obj.properties.title} (distance: ${obj.metadata?.distance})`);
}
```

### Return Specific Properties

```python
response = articles.query.near_text(
    query="AI news",
    limit=5,
    return_properties=["title", "category"],
)
```

## Near Vector Search

Search with a pre-computed vector embedding.

```python
query_vector = embedding_model.encode("artificial intelligence")

response = articles.query.near_vector(
    near_vector=query_vector.tolist(),
    limit=5,
    return_metadata=MetadataQuery(distance=True),
)
```

```typescript
const result = await articles.query.nearVector(queryVector, {
  limit: 5,
  returnMetadata: ['distance'],
});
```

## Near Object Search

Find objects similar to an existing object by its UUID.

```python
response = articles.query.near_object(
    near_object="12345678-e64f-5d94-90db-c8cfa3fc1234",
    limit=5,
    return_metadata=MetadataQuery(distance=True),
)
```

```typescript
const result = await articles.query.nearObject('12345678-e64f-5d94-90db-c8cfa3fc1234', {
  limit: 5,
  returnMetadata: ['distance'],
});
```

## Near Image Search

Requires a collection configured with a multimodal vectorizer (e.g., `multi2vec-clip`).

```python
import base64

with open("photo.jpg", "rb") as f:
    image_b64 = base64.b64encode(f.read()).decode("utf-8")

response = collection.query.near_image(
    near_image=image_b64,
    limit=5,
    return_metadata=MetadataQuery(distance=True),
)
```

## Distance Threshold

Limit results to objects within a maximum distance from the query:

```python
response = articles.query.near_text(
    query="AI breakthroughs",
    distance=0.25,  # Only objects within this distance
)
```

Distance values depend on the distance metric:
- **Cosine**: 0 (identical) to 2 (opposite)
- **L2**: 0 to ∞
- **Dot**: -∞ to ∞

Use `certainty` as an alternative (normalized 0–1 scale, only for cosine):

```python
response = articles.query.near_text(
    query="AI breakthroughs",
    certainty=0.8,  # 0 = opposite, 1 = identical
)
```

## Pagination

### Limit + Offset

```python
response = articles.query.near_text(
    query="technology",
    limit=10,
    offset=20,  # Skip first 20 results
)
```

### Auto-Limit (Score Groups)

Returns results in score "groups" — objects with similar distances are grouped together:

```python
response = articles.query.near_text(
    query="technology",
    auto_limit=1,  # Return first score group only
)
```

## Named Vectors

When a collection has multiple named vectors, specify which to search:

```python
reviews = client.collections.use("ProductReview")
response = reviews.query.near_text(
    query="excellent battery life",
    target_vector="review_vector",
    limit=5,
)
```

```typescript
const result = await reviews.query.nearText('excellent battery life', {
  limit: 5,
  targetVector: 'review_vector',
});
```

## GroupBy

Organize results by a property value:

```python
from weaviate.classes.query import GroupBy

group_by = GroupBy(
    prop="category",
    objects_per_group=3,
    number_of_groups=5,
)

response = articles.query.near_text(
    query="technology",
    group_by=group_by,
)

for group_name, group in response.groups.items():
    print(f"\n{group_name} ({group.number_of_objects} objects)")
    for obj in group.objects:
        print(f"  - {obj.properties['title']}")
```

## MMR Diversity Search

Maximum Marginal Relevance balances relevance with diversity to avoid duplicate-heavy results.

```python
from weaviate.classes.query import Diversity

response = articles.query.near_text(
    query="machine learning",
    limit=20,
    selection=Diversity.MMR(
        limit=5,       # Final number of results
        balance=0.5,   # 0.0 = pure diversity, 1.0 = pure relevance
    ),
)
```

The `balance` parameter controls the trade-off:
- `1.0`: Pure relevance (equivalent to standard nearest-neighbor)
- `0.5`: Balanced relevance and diversity
- `0.0`: Maximize diversity (results may be less relevant)

## Combining with Filters

Apply property-based filters to narrow vector search results:

```python
from weaviate.classes.query import Filter

response = articles.query.near_text(
    query="AI breakthroughs",
    filters=Filter.by_property("category").equal("technology"),
    limit=5,
)

# Multiple filters
response = articles.query.near_text(
    query="AI breakthroughs",
    filters=(
        Filter.by_property("category").equal("technology")
        & Filter.by_property("wordCount").greater_than(500)
    ),
    limit=5,
)
```

See `07-filters.md` for the full filter reference.

## Return Metadata

```python
from weaviate.classes.query import MetadataQuery

response = articles.query.near_text(
    query="AI",
    limit=5,
    return_metadata=MetadataQuery(
        distance=True,       # Similarity distance
        certainty=True,      # Normalized similarity (cosine only)
        creation_time=True,  # Object creation timestamp
        last_update_time=True,
        is_consistent=True,  # Replication consistency
    ),
)

for obj in response.objects:
    print(obj.metadata.distance)
    print(obj.metadata.creation_time)
```

## Common Pitfalls

1. **No vectorizer configured**: `near_text` requires a text vectorizer. Without one, use `near_vector` with pre-computed embeddings.

2. **Missing target_vector**: Collections with named vectors require `target_vector` parameter. Omitting it causes an error.

3. **Distance vs certainty**: Distance ranges vary by metric. Certainty (0–1) only works with cosine. Don't compare distance values across different metrics.

4. **Large offset values**: `offset` pagination degrades with high values because Weaviate still computes all preceding results. Use cursor-based pagination for deep traversal.

5. **Mixing embedding models**: Querying with vectors from a different model than what produced the stored vectors yields meaningless results. Ensure consistency.

## Related Topics

- Hybrid Search → `06-hybrid-search.md`
- Keyword Search → `05-keyword-search.md`
- Filters → `07-filters.md`
- RAG → `08-rag.md`
