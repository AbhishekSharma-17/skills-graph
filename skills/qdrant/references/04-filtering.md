# Qdrant — Filtering

> Source: [qdrant.tech/documentation/concepts/filtering](https://qdrant.tech/documentation/concepts/filtering/) | v1.17.1

## Table of Contents

- [Overview](#overview)
- [Boolean Clauses](#boolean-clauses)
- [Match Conditions](#match-conditions)
- [Range Conditions](#range-conditions)
- [Geo Conditions](#geo-conditions)
- [Special Conditions](#special-conditions)
- [Nested Filtering](#nested-filtering)
- [Common Pitfalls](#common-pitfalls)

## Overview

Qdrant supports rich payload filtering that can be applied to search, scroll, count, and delete operations. Filters use boolean clauses (`must`, `should`, `must_not`) to combine field conditions.

**Important:** For best performance, create payload indexes on fields you filter by. Without indexes, filtering falls back to full scan.

## Boolean Clauses

```python
from qdrant_client import models

# AND — all conditions must match
filter = models.Filter(
    must=[
        models.FieldCondition(key="city", match=models.MatchValue(value="Berlin")),
        models.FieldCondition(key="price", range=models.Range(gte=100, lte=500)),
    ]
)

# OR — at least one condition must match
filter = models.Filter(
    should=[
        models.FieldCondition(key="color", match=models.MatchValue(value="red")),
        models.FieldCondition(key="color", match=models.MatchValue(value="blue")),
    ]
)

# NOT — none of the conditions can match
filter = models.Filter(
    must_not=[
        models.FieldCondition(key="status", match=models.MatchValue(value="archived")),
    ]
)

# min_should — at least N conditions must match (threshold OR)
filter = models.Filter(
    should=[
        models.FieldCondition(key="tag", match=models.MatchValue(value="python")),
        models.FieldCondition(key="tag", match=models.MatchValue(value="rust")),
        models.FieldCondition(key="tag", match=models.MatchValue(value="go")),
    ],
    min_should=models.MinShould(
        conditions=[],  # references the should array above
        min_count=2,     # at least 2 of the 3 must match
    ),
)

# Nested filters (combine must + should)
filter = models.Filter(
    must=[
        models.FieldCondition(key="active", match=models.MatchValue(value=True)),
        models.Filter(  # nested OR inside AND
            should=[
                models.FieldCondition(key="tier", match=models.MatchValue(value="premium")),
                models.FieldCondition(key="tier", match=models.MatchValue(value="enterprise")),
            ]
        ),
    ]
)
```

**REST equivalent:**
```json
{
    "filter": {
        "must": [
            {"key": "city", "match": {"value": "Berlin"}},
            {"key": "price", "range": {"gte": 100, "lte": 500}}
        ],
        "must_not": [
            {"key": "status", "match": {"value": "archived"}}
        ]
    }
}
```

## Match Conditions

### Exact Match (keyword, integer, boolean)

```python
# String match
models.FieldCondition(key="city", match=models.MatchValue(value="Berlin"))

# Integer match
models.FieldCondition(key="count", match=models.MatchValue(value=42))

# Boolean match
models.FieldCondition(key="active", match=models.MatchValue(value=True))
```

### Match Any (IN operator, v1.1.0+)

```python
models.FieldCondition(
    key="color",
    match=models.MatchAny(any=["red", "blue", "green"]),
)
```

### Match Except (NOT IN, v1.2.0+)

```python
# Note: Python keyword escaping required
models.FieldCondition(
    key="color",
    match=models.MatchExcept(**{"except": ["black", "white"]}),
)
```

### Full-Text Match (tokenized, requires text index)

```python
# Matches if description contains BOTH "good" AND "cheap" tokens
models.FieldCondition(
    key="description",
    match=models.MatchText(text="good cheap"),
)
```

### Full-Text Any (v1.16.0+)

```python
# Matches if description contains ANY of the tokens
models.FieldCondition(
    key="description",
    match=models.MatchTextAny(text_any="good cheap fast"),
)
```

### Phrase Match (exact phrase, v1.15.0+)

Requires `phrase_matching: true` on the text index.

```python
models.FieldCondition(
    key="description",
    match=models.MatchPhrase(phrase="brown fox"),
)
```

### UUID Match (v1.11.0+)

```python
models.FieldCondition(
    key="doc_id",
    match=models.MatchValue(value="f47ac10b-58cc-4372-a567-0e02b2c3d479"),
)
```

## Range Conditions

### Numeric Range

```python
# Operators: gt, gte, lt, lte
models.FieldCondition(
    key="price",
    range=models.Range(gte=100.0, lte=500.0),
)
```

### Datetime Range (v1.8.0+)

```python
# RFC 3339 format
models.FieldCondition(
    key="created_at",
    range=models.DatetimeRange(
        gt="2024-01-01T00:00:00Z",
        lte="2024-12-31T23:59:59Z",
    ),
)
```

## Geo Conditions

### Bounding Box

```python
models.FieldCondition(
    key="location",
    geo_bounding_box=models.GeoBoundingBox(
        top_left=models.GeoPoint(lon=-0.1278, lat=51.5074),
        bottom_right=models.GeoPoint(lon=0.0, lat=51.45),
    ),
)
```

### Radius (meters)

```python
models.FieldCondition(
    key="location",
    geo_radius=models.GeoRadius(
        center=models.GeoPoint(lon=13.4050, lat=52.5200),
        radius=5000.0,  # 5km
    ),
)
```

### Polygon (v1.2.0+)

```python
models.FieldCondition(
    key="location",
    geo_polygon=models.GeoPolygon(
        exterior=models.GeoLineString(points=[
            models.GeoPoint(lon=-0.2, lat=51.6),
            models.GeoPoint(lon=0.1, lat=51.6),
            models.GeoPoint(lon=0.1, lat=51.4),
            models.GeoPoint(lon=-0.2, lat=51.4),
            models.GeoPoint(lon=-0.2, lat=51.6),  # close the ring
        ]),
        interiors=[],  # optional holes
    ),
)
```

**Payload format for geo points:**
```json
{"location": {"lat": 52.5200, "lon": 13.4050}}
```

## Special Conditions

### Has ID (filter by point IDs)

```python
models.HasIdCondition(has_id=[1, 3, 5, 7])
```

### Is Empty (missing, null, or empty array)

```python
models.IsEmptyCondition(
    is_empty=models.PayloadField(key="description"),
)
```

### Is Null (explicitly null)

```python
models.IsNullCondition(
    is_null=models.PayloadField(key="deleted_at"),
)
```

### Values Count (array length)

```python
# Points where "tags" array has more than 2 elements
models.FieldCondition(
    key="tags",
    values_count=models.ValuesCount(gt=2),
)
```

### Has Vector (v1.13.0+)

Filter by whether a specific named vector exists:

```python
models.HasVectorCondition(has_vector="image")
```

## Nested Filtering

### Dot Notation (v1.1.0+)

Access nested JSON fields:

```python
# payload: {"address": {"city": "Berlin", "zip": "10115"}}
models.FieldCondition(
    key="address.city",
    match=models.MatchValue(value="Berlin"),
)
```

### Array Element Access

```python
# payload: {"cities": [{"name": "Berlin", "pop": 3.7}, {"name": "Munich", "pop": 1.5}]}
models.FieldCondition(
    key="cities[].pop",
    range=models.Range(gte=2.0),
)
```

### Nested Object Filter (v1.2.0+)

Filter arrays of objects where conditions must match on the **same** element:

```python
# Find points where someone likes meat
models.NestedCondition(
    nested=models.Nested(
        key="diet",
        filter=models.Filter(
            must=[
                models.FieldCondition(key="food", match=models.MatchValue(value="meat")),
                models.FieldCondition(key="likes", match=models.MatchValue(value=True)),
            ]
        ),
    )
)
```

Without `NestedCondition`, the conditions could match different array elements. `NestedCondition` ensures both conditions apply to the same object in the array.

## Common Pitfalls

1. **MatchExcept syntax** — Python reserves `except` keyword. Use `**{"except": [...]}`.
2. **Missing payload index** — Without an index, filtering scans all payloads linearly. Always create indexes for filter fields.
3. **Nested vs dot notation** — Use `NestedCondition` when multiple conditions must match the same array element. Dot notation with `[]` applies conditions independently across elements.
4. **Full-text requires index** — `MatchText` only works with a `text` type payload index. Without it, you get no results.
5. **Geo point format** — Must be `{"lat": ..., "lon": ...}` in the payload. Other formats won't match.
6. **Null handling** — `IsEmpty` matches null, missing, AND empty arrays. `IsNull` matches only explicit null values.

## Related Topics

- Search & Query API → `references/03-search-query.md`
- Indexing → `references/05-indexing.md`
- Hybrid search → `references/07-hybrid-search.md`
