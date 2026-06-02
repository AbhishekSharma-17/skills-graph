# Weaviate — Keyword (BM25) Search

> Source: [docs.weaviate.io](https://docs.weaviate.io/weaviate/search/bm25) | Version: v1.37

## Table of Contents
- [Overview](#overview)
- [Basic BM25 Query](#basic-bm25-query)
- [Search Operators](#search-operators)
- [Property Boosting](#property-boosting)
- [Tokenization](#tokenization)
- [Score Metadata](#score-metadata)
- [Filtering](#filtering)
- [Pagination and Grouping](#pagination-and-grouping)
- [Fuzzy Matching](#fuzzy-matching)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

BM25 (Best Match 25) is Weaviate's keyword search algorithm. Unlike vector search which finds semantically similar results, BM25 ranks objects based on exact term frequency and inverse document frequency — the same algorithm behind traditional search engines.

Use BM25 when:
- Users search for specific terms, product names, or codes
- Exact keyword matching matters more than semantic similarity
- You need explainable relevance scores based on term frequency

## Basic BM25 Query

### Python

```python
articles = client.collections.use("Article")
response = articles.query.bm25(
    query="machine learning frameworks",
    limit=5,
)
for obj in response.objects:
    print(obj.properties["title"])
```

### TypeScript

```typescript
const articles = client.collections.use('Article');
const result = await articles.query.bm25('machine learning frameworks', {
  limit: 5,
});
for (const obj of result.objects) {
  console.log(obj.properties.title);
}
```

## Search Operators

### OR Operator (Default)

Returns objects containing at least N of the query tokens. Default `minimum_match` is 1.

```python
from weaviate.classes.query import BM25Operator

response = articles.query.bm25(
    query="African desert wind patterns",
    operator=BM25Operator.or_(minimum_match=2),  # At least 2 tokens must match
    limit=5,
)
```

### AND Operator

Returns only objects containing ALL query tokens.

```python
response = articles.query.bm25(
    query="machine learning Python",
    operator=BM25Operator.and_(),
    limit=5,
)
```

## Property Boosting

Search specific properties and apply relative scoring weights:

### Search Selected Properties

```python
response = articles.query.bm25(
    query="neural network",
    query_properties=["title", "body"],  # Only search these properties
    limit=5,
)
```

### Boost Property Weights

Use `^weight` syntax to increase a property's scoring influence:

```python
response = articles.query.bm25(
    query="neural network",
    query_properties=["title^3", "body"],  # Title matches score 3x higher
    limit=5,
)
```

```typescript
const result = await articles.query.bm25('neural network', {
  queryProperties: ['title^3', 'body'],
  limit: 5,
});
```

## Tokenization

Controls how text is split into searchable tokens. Set per-property at collection creation.

| Mode | Behavior | Example: "New York City" |
|------|----------|--------------------------|
| `WORD` (default) | Lowercase, split on non-alphanumeric | `["new", "york", "city"]` |
| `LOWERCASE` | Lowercase, split on whitespace | `["new", "york", "city"]` |
| `WHITESPACE` | Preserve case, split on whitespace | `["New", "York", "City"]` |
| `FIELD` | No tokenization, entire value is one token | `["New York City"]` |
| `TRIGRAM` | 3-character sliding window | `["new", "ew ", "w y", " yo", "yor", ...]` |
| `GSE` | Chinese/Japanese segmentation | Language-specific tokens |
| `KAGOME_JA` | Japanese segmentation | Language-specific tokens |

### Setting Tokenization

```python
from weaviate.classes.config import Configure, Property, DataType, Tokenization

client.collections.create(
    "Product",
    vector_config=Configure.Vectors.text2vec_openai(),
    properties=[
        Property(
            name="name",
            data_type=DataType.TEXT,
            tokenization=Tokenization.LOWERCASE,
        ),
        Property(
            name="sku",
            data_type=DataType.TEXT,
            tokenization=Tokenization.FIELD,  # Match entire SKU
        ),
        Property(
            name="description",
            data_type=DataType.TEXT,
            tokenization=Tokenization.WORD,
        ),
    ],
)
```

### Accent Folding (v1.37 Preview)

Normalize accented characters to ASCII equivalents for broader matching.

### Stopwords (v1.37 Preview)

Customize stopword lists per-property to exclude common words from indexing.

## Score Metadata

Retrieve BM25F scores with results:

```python
from weaviate.classes.query import MetadataQuery

response = articles.query.bm25(
    query="machine learning",
    return_metadata=MetadataQuery(score=True),
    limit=5,
)
for obj in response.objects:
    print(f"{obj.properties['title']} — score: {obj.metadata.score:.4f}")
```

```typescript
const result = await articles.query.bm25('machine learning', {
  returnMetadata: ['score'],
  limit: 5,
});
for (const obj of result.objects) {
  console.log(`${obj.properties.title} — score: ${obj.metadata?.score}`);
}
```

## Filtering

Combine BM25 search with property filters:

```python
from weaviate.classes.query import Filter

response = articles.query.bm25(
    query="deep learning",
    filters=Filter.by_property("category").equal("research"),
    return_properties=["title", "category", "publishedAt"],
    limit=5,
)
```

```typescript
const result = await articles.query.bm25('deep learning', {
  filters: articles.filter.byProperty('category').equal('research'),
  returnProperties: ['title', 'category', 'publishedAt'],
  limit: 5,
});
```

## Pagination and Grouping

### Limit + Offset

```python
response = articles.query.bm25(
    query="technology",
    limit=10,
    offset=20,
)
```

### Auto-Limit by Score Groups

```python
response = articles.query.bm25(
    query="technology",
    auto_limit=1,  # Return first score group
)
```

### GroupBy

```python
from weaviate.classes.query import GroupBy

group_by = GroupBy(
    prop="category",
    objects_per_group=3,
    number_of_groups=5,
)
response = articles.query.bm25(
    query="technology",
    group_by=group_by,
)
```

## Fuzzy Matching

Enable typo tolerance using trigram tokenization. Trigrams create overlapping 3-character sequences that match similar strings.

```python
Property(
    name="title",
    data_type=DataType.TEXT,
    tokenization=Tokenization.TRIGRAM,
)
```

With trigram tokenization, "Morgn" matches "Morgan" because they share overlapping trigrams.

## Common Pitfalls

1. **BM25 on untokenized properties**: Properties with `FIELD` tokenization require exact full-value matches. Don't use BM25 queries expecting partial matching on FIELD-tokenized properties.

2. **Missing inverted index**: BM25 requires the inverted index. If disabled on a property, that property is invisible to keyword search.

3. **Property weight confusion**: `query_properties=["title^3"]` boosts title's BM25 score, not the number of results from title. A high-quality body match still outranks a weak title match.

4. **AND operator strictness**: `BM25Operator.and_()` requires ALL tokens present. Queries with many words return very few (or zero) results. Use OR with `minimum_match` for a middle ground.

5. **Tokenization mismatch**: If the collection uses LOWERCASE tokenization but you search for "NYC" expecting case-sensitive matching, it won't work. Check the tokenization mode.

## Related Topics

- Hybrid Search → `06-hybrid-search.md`
- Similarity Search → `04-similarity-search.md`
- Filters → `07-filters.md`
