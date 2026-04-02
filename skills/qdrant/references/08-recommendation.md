# Qdrant — Recommendation & Discovery

> Source: [qdrant.tech/documentation/concepts/explore](https://qdrant.tech/documentation/concepts/explore/) | v1.17.1

## Overview

Qdrant's Recommendation and Discovery APIs let you search based on **examples** rather than raw vectors. Instead of providing a query vector, you provide positive and negative point examples, and Qdrant finds similar (or dissimilar) points.

**Use cases:**
- "More like this" recommendations
- Content-based filtering
- Exploratory search with positive/negative feedback
- Cross-collection recommendations

## Recommendation API

### Basic Recommendation

```python
from qdrant_client import QdrantClient, models

client = QdrantClient("localhost", port=6333)

results = client.query_points(
    collection_name="my_collection",
    query=models.RecommendQuery(
        recommend=models.RecommendInput(
            positive=[100, 231],   # point IDs to find similar to
            negative=[718],        # point IDs to avoid
        )
    ),
    limit=10,
)
```

### With Vectors Instead of IDs

```python
results = client.query_points(
    collection_name="my_collection",
    query=models.RecommendQuery(
        recommend=models.RecommendInput(
            positive=[
                100,                           # point ID
                [0.2, 0.3, 0.4, 0.5],        # raw vector
            ],
            negative=[
                [0.9, 0.1, 0.2, 0.3],        # raw vector
            ],
        )
    ),
    limit=10,
)
```

### Recommendation Strategies

| Strategy | Description | Performance |
|----------|-------------|-------------|
| `AVERAGE_VECTOR` | Combines examples into single query vector | Fast (single search) |
| `BEST_SCORE` | Scores each candidate against all examples | Slower (linear in examples) |
| `SUM_SCORES` | Sums scores from all positive, subtracts negative | Moderate |

```python
# Average Vector (default) — fast, single search
results = client.query_points(
    collection_name="my_collection",
    query=models.RecommendQuery(
        recommend=models.RecommendInput(
            positive=[100, 231],
            negative=[718],
            strategy=models.RecommendStrategy.AVERAGE_VECTOR,
        )
    ),
    limit=10,
)

# Best Score (v1.6+) — more accurate, slower
results = client.query_points(
    collection_name="my_collection",
    query=models.RecommendQuery(
        recommend=models.RecommendInput(
            positive=[100, 231, 500],
            negative=[718, 200],
            strategy=models.RecommendStrategy.BEST_SCORE,
        )
    ),
    limit=10,
)
```

**How strategies work:**
- `AVERAGE_VECTOR`: `query = avg(positive) + avg(positive) - avg(negative)`, then single ANN search
- `BEST_SCORE`: Each candidate scored against every example, best positive score - best negative score selected
- `SUM_SCORES`: `score = sum(positive_scores) - sum(negative_scores)`

### With Filters

```python
results = client.query_points(
    collection_name="my_collection",
    query=models.RecommendQuery(
        recommend=models.RecommendInput(
            positive=[100, 231],
            negative=[718],
            strategy=models.RecommendStrategy.BEST_SCORE,
        )
    ),
    query_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="category",
                match=models.MatchValue(value="electronics"),
            )
        ],
        must_not=[
            models.HasIdCondition(has_id=[100, 231, 718]),  # exclude input points
        ],
    ),
    limit=10,
)
```

### Named Vector Recommendation

```python
results = client.query_points(
    collection_name="multi_vec",
    query=models.RecommendQuery(
        recommend=models.RecommendInput(
            positive=[100, 231],
            negative=[718],
        )
    ),
    using="dense",  # which named vector to use
    limit=10,
)
```

## Cross-Collection Lookup

Use points from a different collection as recommendation input:

```python
results = client.query_points(
    collection_name="products",
    query=models.RecommendQuery(
        recommend=models.RecommendInput(
            positive=[42, 99],  # IDs from "user_history" collection
        )
    ),
    using="product_embedding",
    lookup_from=models.LookupLocation(
        collection="user_history",
        vector="item_embedding",
    ),
    limit=10,
)
```

**How it works:** Qdrant retrieves vectors from the `lookup_from` collection, then uses them to search in the target collection. The vector dimensions must match.

## Discovery API (v1.7+)

Discovery search lets you define a **target** vector and **context** pairs that partition the vector space, guiding search toward regions preferred by your context.

### Basic Discovery

```python
results = client.query_points(
    collection_name="my_collection",
    query=models.DiscoverQuery(
        discover=models.DiscoverInput(
            target=[0.2, 0.1, 0.9, 0.7],  # target vector or point ID
            context=[
                models.ContextPair(
                    positive=100,   # prefer this side
                    negative=718,   # avoid this side
                ),
                models.ContextPair(
                    positive=200,
                    negative=300,
                ),
            ],
        )
    ),
    limit=10,
)
```

**How it works:** Context pairs define hyperplanes in vector space. For each pair, points closer to the positive example get a score bonus. The target vector then searches within the favorable region.

### Context-Only Search

Search using only context pairs (no target vector):

```python
results = client.query_points(
    collection_name="my_collection",
    query=models.DiscoverQuery(
        discover=models.DiscoverInput(
            target=None,
            context=[
                models.ContextPair(positive=100, negative=718),
            ],
        )
    ),
    limit=10,
)
```

**Note:** Maximum score for context-only search is 0.0. All scores are negative, with less negative being better.

## Batch Recommendations

```python
results = client.query_batch_points(
    collection_name="my_collection",
    requests=[
        models.QueryRequest(
            query=models.RecommendQuery(
                recommend=models.RecommendInput(positive=[100]),
            ),
            limit=5,
        ),
        models.QueryRequest(
            query=models.RecommendQuery(
                recommend=models.RecommendInput(positive=[200, 300]),
            ),
            limit=5,
        ),
    ],
)
```

## REST API Examples

### Recommend

```http
POST /collections/my_collection/points/query
{
    "query": {
        "recommend": {
            "positive": [100, 231],
            "negative": [718],
            "strategy": "best_score"
        }
    },
    "limit": 10
}
```

### Discover

```http
POST /collections/my_collection/points/query
{
    "query": {
        "discover": {
            "target": [0.2, 0.1, 0.9, 0.7],
            "context": [
                {"positive": 100, "negative": 718}
            ]
        }
    },
    "limit": 10
}
```

## Common Pitfalls

1. **Exclude input points** — Add `must_not: HasIdCondition` to exclude the positive/negative example points from results.
2. **Strategy selection** — `AVERAGE_VECTOR` is fastest but works poorly with diverse positive examples. Use `BEST_SCORE` when positive examples span different clusters.
3. **Cross-collection dimensions** — The vector dimensions in `lookup_from` must match the target collection's vector dimensions.
4. **Context-only scores** — All scores are ≤ 0.0 in context-only discovery. Less negative = more aligned with context preferences.
5. **Performance with many examples** — `BEST_SCORE` performance is linear in the number of examples. Keep positive + negative lists small (< 20 total).

## Related Topics

- Search & Query API → `references/03-search-query.md`
- Hybrid search → `references/07-hybrid-search.md`
- Filtering → `references/04-filtering.md`
