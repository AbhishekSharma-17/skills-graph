# Weaviate — Filters

> Source: [docs.weaviate.io](https://docs.weaviate.io/weaviate/search/filters) | Version: v1.37

## Table of Contents
- [Overview](#overview)
- [Basic Filter Operators](#basic-filter-operators)
- [Text Filtering](#text-filtering)
- [Combining Filters](#combining-filters)
- [Nested Filters](#nested-filters)
- [Array Filters](#array-filters)
- [Metadata Filters](#metadata-filters)
- [Cross-Reference Filters](#cross-reference-filters)
- [Null State Filtering](#null-state-filtering)
- [Geo Filtering](#geo-filtering)
- [Using with Search Types](#using-with-search-types)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

Filters narrow search results by property values. They work with all search types (vector, keyword, hybrid) and with fetch/aggregate queries. Filters are applied post-search on the server side for efficiency.

```python
from weaviate.classes.query import Filter
```

## Basic Filter Operators

| Operator | Method | Works With |
|----------|--------|------------|
| Equal | `.equal(value)` | All types |
| Not equal | `.not_equal(value)` | All types |
| Greater than | `.greater_than(value)` | Number, int, date |
| Greater or equal | `.greater_or_equal(value)` | Number, int, date |
| Less than | `.less_than(value)` | Number, int, date |
| Less or equal | `.less_or_equal(value)` | Number, int, date |
| Like (pattern) | `.like(pattern)` | Text |
| Contains any | `.contains_any(values)` | Arrays |
| Contains all | `.contains_all(values)` | Arrays |
| Contains none | `.contains_none(values)` | Arrays |
| Is null | `.is_none(True/False)` | All types |

### Examples

```python
# Exact match
Filter.by_property("category").equal("technology")

# Numeric comparison
Filter.by_property("price").less_than(100)
Filter.by_property("rating").greater_or_equal(4.5)

# Date comparison
from datetime import datetime
Filter.by_property("publishedAt").greater_than(datetime(2026, 1, 1))
```

## Text Filtering

### Like Pattern Matching

Use `*` for zero or more characters, `?` for exactly one character:

```python
# Starts with "AI"
Filter.by_property("title").like("AI*")

# Contains "learn"
Filter.by_property("title").like("*learn*")

# Exact pattern: "data" followed by any single char
Filter.by_property("code").like("data?")
```

### Case Sensitivity

`like` matching is case-insensitive by default with `WORD` tokenization.

## Combining Filters

### AND (All conditions must match)

```python
# Using & operator
filters = (
    Filter.by_property("category").equal("technology")
    & Filter.by_property("rating").greater_than(4.0)
)

# Using all_of
filters = Filter.all_of([
    Filter.by_property("category").equal("technology"),
    Filter.by_property("rating").greater_than(4.0),
    Filter.by_property("isPublished").equal(True),
])
```

### OR (Any condition must match)

```python
# Using | operator
filters = (
    Filter.by_property("category").equal("technology")
    | Filter.by_property("category").equal("science")
)

# Using any_of
filters = Filter.any_of([
    Filter.by_property("category").equal("technology"),
    Filter.by_property("category").equal("science"),
    Filter.by_property("category").equal("engineering"),
])
```

### NOT (Negate a condition)

```python
filters = Filter.not_(
    Filter.by_property("category").equal("spam")
)
```

## Nested Filters

Combine AND, OR, and NOT for complex logic:

```python
# (category = "tech" AND rating > 4) OR (category = "science" AND rating > 3)
filters = (
    (Filter.by_property("category").equal("technology")
     & Filter.by_property("rating").greater_than(4.0))
    |
    (Filter.by_property("category").equal("science")
     & Filter.by_property("rating").greater_than(3.0))
)

response = articles.query.near_text(
    query="AI breakthroughs",
    filters=filters,
    limit=10,
)
```

## Array Filters

For properties with array types (TEXT_ARRAY, INT_ARRAY, etc.):

```python
# Object has ANY of these tags
Filter.by_property("tags").contains_any(["python", "machine-learning"])

# Object has ALL of these tags
Filter.by_property("tags").contains_all(["python", "machine-learning"])

# Object has NONE of these tags
Filter.by_property("tags").contains_none(["spam", "deprecated"])
```

## Metadata Filters

Filter by object metadata instead of properties:

### By Object ID

```python
Filter.by_id().equal("12345678-e64f-5d94-90db-c8cfa3fc1234")
```

### By Creation Time

```python
from datetime import datetime

Filter.by_creation_time().greater_than(datetime(2026, 1, 1))
```

### By Update Time

```python
Filter.by_update_time().greater_than(datetime(2026, 6, 1))
```

### By Property Length

```python
# Text properties with more than 100 characters
Filter.by_property("body", length=True).greater_than(100)

# Array properties with more than 5 elements
Filter.by_property("tags", length=True).greater_than(5)
```

## Cross-Reference Filters

Filter objects based on properties of referenced objects:

```python
# Articles whose referenced Category has title containing "Sport"
filters = Filter.by_ref(link_on="hasCategory").by_property("title").like("*Sport*")

response = articles.query.fetch_objects(
    filters=filters,
    limit=10,
)
```

### Multi-Hop References

```python
# Articles -> Category -> ParentCategory
filters = (
    Filter.by_ref(link_on="hasCategory")
    .by_ref(link_on="hasParent")
    .by_property("name").equal("STEM")
)
```

Cross-reference filters can be slower than property filters at scale. Prefer denormalized properties when performance matters.

## Null State Filtering

Find objects with or without values for a property. Requires `index_null_state=True` on the property.

```python
from weaviate.classes.config import Property, DataType

# Enable null state indexing at collection creation
Property(
    name="reviewScore",
    data_type=DataType.NUMBER,
    index_null_state=True,
)

# Find objects missing reviewScore
Filter.by_property("reviewScore").is_none(True)

# Find objects that have reviewScore
Filter.by_property("reviewScore").is_none(False)
```

## Geo Filtering

Filter by geographic distance:

```python
Filter.by_property("location").within_geo_range(
    coordinate=GeoCoordinate(latitude=52.39, longitude=4.84),
    distance=10000,  # Meters
)
```

Limited to the nearest 800 results from the source location.

## Using with Search Types

Filters work identically with all search types:

```python
# With vector search
articles.query.near_text(query="AI", filters=filters, limit=5)

# With BM25 keyword search
articles.query.bm25(query="AI", filters=filters, limit=5)

# With hybrid search
articles.query.hybrid(query="AI", filters=filters, limit=5)

# With fetch (no search, just filter)
articles.query.fetch_objects(filters=filters, limit=5)

# With aggregation
articles.aggregate.over_all(filters=filters, total_count=True)
```

## Common Pitfalls

1. **Null state not indexed**: By default, `is_none` filter doesn't work. You must set `index_null_state=True` on the property at collection creation time.

2. **Like pattern performance**: `like("*term*")` (leading wildcard) is slower than `like("term*")` (prefix match). Prefer prefix matches when possible.

3. **Cross-reference filter cost**: Filters traversing references are significantly slower at scale. Denormalize frequently filtered properties.

4. **Date format**: Date filters expect `datetime` objects in Python or RFC 3339 strings. Passing a plain string like "2026-01-01" may silently fail.

5. **Filter on non-indexed property**: If a property's inverted index is disabled, filters on it won't work. Check collection config.

## Related Topics

- Similarity Search → `04-similarity-search.md`
- Keyword Search → `05-keyword-search.md`
- Hybrid Search → `06-hybrid-search.md`
