# Weaviate — Reranking & Aggregation

> Source: [docs.weaviate.io](https://docs.weaviate.io/weaviate/search) | Version: v1.37

## Table of Contents
- [Reranking Overview](#reranking-overview)
- [Reranker Configuration](#reranker-configuration)
- [Reranking with Search Types](#reranking-with-search-types)
- [Aggregation Overview](#aggregation-overview)
- [Count Aggregation](#count-aggregation)
- [Numeric Aggregation](#numeric-aggregation)
- [Text Aggregation](#text-aggregation)
- [GroupBy Aggregation](#groupby-aggregation)
- [Search-Based Aggregation](#search-based-aggregation)
- [Filtered Aggregation](#filtered-aggregation)
- [Common Pitfalls](#common-pitfalls)

---

## Reranking Overview

Reranking re-scores search results using a more expensive (but more accurate) model after the initial retrieval. This two-stage pipeline improves precision:

```
Query → Fast Search (retrieve 100) → Reranker (re-score top 100) → Return top 10
```

Reranking works with all search types (vector, keyword, hybrid) and uses cross-encoder models that consider both the query and the full document text.

## Reranker Configuration

### At Collection Creation

```python
from weaviate.classes.config import Configure

client.collections.create(
    "Article",
    vector_config=Configure.Vectors.text2vec_openai(),
    reranker_config=Configure.Reranker.cohere(),
    properties=[...],
)
```

### Available Rerankers

```python
Configure.Reranker.cohere(model="rerank-english-v3.0")
Configure.Reranker.voyageai(model="rerank-2")
Configure.Reranker.jinaai(model="jina-reranker-v2-base-multilingual")
Configure.Reranker.nvidia()
Configure.Reranker.transformers()  # Self-hosted
```

## Reranking with Search Types

### Rerank Vector Search Results

```python
from weaviate.classes.query import Rerank, MetadataQuery

articles = client.collections.use("Article")
response = articles.query.near_text(
    query="machine learning trends",
    limit=20,  # Retrieve more candidates
    rerank=Rerank(
        prop="body",           # Property to rerank on
        query="latest ML trends 2026",  # Reranking query
    ),
    return_metadata=MetadataQuery(score=True),
)

for obj in response.objects:
    print(f"{obj.properties['title']} — rerank score: {obj.metadata.score:.4f}")
```

### Rerank Keyword Search

```python
response = articles.query.bm25(
    query="deep learning",
    limit=20,
    rerank=Rerank(
        prop="body",
        query="state of the art deep learning architectures",
    ),
    return_metadata=MetadataQuery(score=True),
)
```

### Rerank Hybrid Search

```python
response = articles.query.hybrid(
    query="AI research papers",
    alpha=0.75,
    limit=20,
    rerank=Rerank(
        prop="body",
        query="peer-reviewed AI research",
    ),
    return_metadata=MetadataQuery(score=True),
)
```

### TypeScript

```typescript
const result = await articles.query.nearText('machine learning trends', {
  limit: 20,
  rerank: {
    property: 'body',
    query: 'latest ML trends 2026',
  },
  returnMetadata: ['score'],
});
```

### Reranking Parameters

| Parameter | Description |
|-----------|-------------|
| `prop` | Object property to use for reranking comparison |
| `query` | Text to compare against (can differ from search query) |

The reranking query can be different from the search query, letting you retrieve broadly and then re-score for a specific intent.

## Aggregation Overview

Aggregation queries compute statistics over objects in a collection. They don't return individual objects — they return calculated values.

```python
from weaviate.classes.aggregate import Metrics
```

## Count Aggregation

Count total objects in a collection:

```python
articles = client.collections.use("Article")
response = articles.aggregate.over_all(total_count=True)
print(f"Total articles: {response.total_count}")
```

```typescript
const articles = client.collections.use('Article');
const result = await articles.aggregate.overAll();
console.log(`Total: ${result.totalCount}`);
```

## Numeric Aggregation

Compute sum, min, max, mean, median, mode on numeric properties:

```python
from weaviate.classes.aggregate import Metrics

response = articles.aggregate.over_all(
    return_metrics=Metrics("wordCount").integer(
        sum_=True,
        maximum=True,
        minimum=True,
        mean=True,
        median=True,
        mode=True,
        count=True,
    ),
)

stats = response.properties["wordCount"]
print(f"Sum: {stats.sum_}")
print(f"Max: {stats.maximum}")
print(f"Min: {stats.minimum}")
print(f"Mean: {stats.mean}")
```

### Float/Number Properties

```python
response = articles.aggregate.over_all(
    return_metrics=Metrics("rating").number(
        sum_=True,
        maximum=True,
        minimum=True,
        mean=True,
    ),
)
```

## Text Aggregation

Count top occurring values for text properties:

```python
response = articles.aggregate.over_all(
    return_metrics=Metrics("category").text(
        top_occurrences_count=True,
        top_occurrences_value=True,
        min_occurrences=3,  # Only values appearing 3+ times
    ),
)

for occurrence in response.properties["category"].top_occurrences:
    print(f"{occurrence.value}: {occurrence.count}")
```

## GroupBy Aggregation

Group results by a property and compute per-group metrics:

```python
from weaviate.classes.aggregate import GroupByAggregate

response = articles.aggregate.over_all(
    group_by=GroupByAggregate(prop="category"),
)

for group in response.groups:
    print(f"{group.grouped_by.value}: {group.total_count} articles")
```

### GroupBy with Metrics

```python
response = articles.aggregate.over_all(
    group_by=GroupByAggregate(prop="category"),
    return_metrics=Metrics("wordCount").integer(
        mean=True, maximum=True
    ),
)

for group in response.groups:
    stats = group.properties["wordCount"]
    print(f"{group.grouped_by.value}: avg={stats.mean:.0f}, max={stats.maximum}")
```

## Search-Based Aggregation

Aggregate over search results instead of the entire collection.

### Near Text Aggregation

```python
response = articles.aggregate.near_text(
    query="artificial intelligence",
    object_limit=50,  # Aggregate top 50 results
    return_metrics=Metrics("wordCount").integer(sum_=True, mean=True),
)
```

### With Distance Threshold

```python
response = articles.aggregate.near_text(
    query="artificial intelligence",
    distance=0.25,
    return_metrics=Metrics("wordCount").integer(sum_=True),
)
```

### Hybrid Aggregation

```python
response = articles.aggregate.hybrid(
    query="AI trends",
    object_limit=50,
    return_metrics=Metrics("rating").number(mean=True),
)
```

## Filtered Aggregation

Apply filters to narrow the aggregation scope:

```python
from weaviate.classes.query import Filter

response = articles.aggregate.over_all(
    filters=Filter.by_property("category").equal("technology"),
    total_count=True,
    return_metrics=Metrics("wordCount").integer(mean=True),
)
print(f"Tech articles: {response.total_count}")
```

## Common Pitfalls

1. **Rerank without reranker module**: Reranking fails if no reranker is configured on the collection. Configure it at creation time.

2. **Rerank limit too small**: Retrieve more candidates than you need (e.g., `limit=50`) then let reranking select the best. A small limit means the reranker has fewer candidates to work with.

3. **Aggregation on large collections**: `over_all` without filters scans every object. For large collections, add filters or use search-based aggregation with `object_limit`.

4. **GroupBy limitations**: `group_by` only works with `near<Media>` search operators and is limited to one property level.

5. **Missing property index**: Aggregation on non-indexed properties returns empty results. Ensure the inverted index is enabled.

## Related Topics

- Similarity Search → `04-similarity-search.md`
- Hybrid Search → `06-hybrid-search.md`
- Filters → `07-filters.md`
- Model Providers → `11-model-providers.md`
