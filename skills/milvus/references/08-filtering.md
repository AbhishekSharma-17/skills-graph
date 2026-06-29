# Milvus — Filtering & Boolean Expressions

> Source: [milvus.io/docs/boolean.md](https://milvus.io/docs/boolean.md) | Version: 3.0-beta

## Overview

Milvus uses predicate expressions to filter entities during search and query operations. Filters evaluate to TRUE or FALSE per entity, narrowing the result set before or during ANN search. Filters work on scalar fields (numbers, strings, booleans) and composite fields (JSON, arrays).

## Comparison Operators

```python
# Equality
filter = "status == 'active'"
filter = "version != 2"

# Numeric comparison
filter = "price > 100"
filter = "score >= 0.8"
filter = "count < 50"
filter = "rating <= 4.5"

# Range (ternary)
filter = "500 <= price < 1000"
filter = "0.5 < score <= 1.0"
```

## Logical Operators

```python
# AND
filter = "category == 'tech' and score > 0.8"
filter = "category == 'tech' && score > 0.8"  # alternative syntax

# OR
filter = "category == 'tech' or category == 'science'"
filter = "category == 'tech' || category == 'science'"

# NOT
filter = "not (category == 'spam')"

# Complex combinations
filter = "(category == 'tech' or category == 'ai') and score > 0.7 and not archived"
```

## Membership (IN)

```python
# Check if value is in a set
filter = "category in ['tech', 'science', 'engineering']"
filter = "id in [1, 2, 3, 4, 5]"

# NOT IN
filter = "category not in ['spam', 'test']"
```

## Pattern Matching (LIKE)

```python
# Prefix match
filter = "title like 'Introduction%'"

# Suffix match
filter = "email like '%@example.com'"

# Contains
filter = "description like '%machine learning%'"

# Single character wildcard
filter = "code like 'A_B'"  # matches 'A1B', 'AXB', etc.
```

## Arithmetic Operators

```python
# Basic arithmetic in expressions
filter = "price * quantity > 1000"
filter = "score_a + score_b >= 1.5"
filter = "total - discount > 0"
filter = "value % 2 == 0"       # modulo
filter = "distance ** 2 < 100"  # power
```

## NULL Handling

```python
# Check for NULL values
filter = "description is null"
filter = "description is not null"
```

## JSON Field Filtering

### Access JSON Keys

```python
# Top-level key
filter = 'metadata["source"] == "arxiv"'
filter = 'metadata["confidence"] > 0.9'

# Nested keys
filter = 'metadata["author"]["name"] == "Alice"'
filter = 'metadata["stats"]["views"] > 1000'
```

### JSON Contains

```python
# Check if JSON array contains a value
filter = 'json_contains(metadata["tags"], "ml")'

# Check if JSON array contains ALL values
filter = 'json_contains_all(metadata["tags"], ["ml", "ai"])'

# Check if JSON array contains ANY of the values
filter = 'json_contains_any(metadata["tags"], ["ml", "nlp", "cv"])'
```

## Array Field Filtering

### Array Contains

```python
# Single element
filter = "array_contains(tags, 'machine-learning')"

# All elements present
filter = "array_contains_all(tags, ['python', 'ml'])"

# Any element present
filter = "array_contains_any(tags, ['python', 'javascript', 'rust'])"
```

### Array Length

```python
filter = "array_length(tags) > 3"
filter = "array_length(tags) == 0"
```

### Array Element Access

```python
# Access by index
filter = "scores[0] > 0.9"
filter = "tags[0] == 'primary'"
```

## Operator Precedence

From highest to lowest:

| Priority | Operator | Description |
|----------|----------|-------------|
| 1 | `+`, `-` (unary) | Sign |
| 2 | `not` | Logical negation |
| 3 | `**` | Power |
| 4 | `*`, `/`, `%` | Multiplication, division, modulo |
| 5 | `+`, `-` | Addition, subtraction |
| 6 | `<`, `<=`, `>`, `>=` | Relational |
| 7 | `==`, `!=` | Equality |
| 8 | `like` | Pattern matching |
| 9 | `json_contains`, `array_contains`, etc. | Container operations |
| 10 | `and`, `&&` | Logical AND |
| 11 | `or`, `\|\|` | Logical OR |

Use parentheses to override precedence when needed.

## Using Filters in Search

```python
results = client.search(
    collection_name="products",
    data=[query_vector],
    filter="category == 'electronics' and price < 500 and rating >= 4.0",
    limit=10,
    output_fields=["name", "price", "rating"],
)
```

## Using Filters in Query

```python
results = client.query(
    collection_name="products",
    filter="category in ['electronics', 'gadgets'] and array_contains(tags, 'sale')",
    output_fields=["name", "price", "tags"],
    limit=50,
)
```

## Using Filters in Delete

```python
client.delete(
    collection_name="products",
    filter="status == 'expired' or price == 0",
)
```

## Filter Performance

### Index Your Filter Fields

Scalar indexes dramatically speed up filtering:

```python
index_params.add_index(field_name="category", index_type="Trie")       # VARCHAR
index_params.add_index(field_name="price", index_type="STL_SORT")      # numeric
index_params.add_index(field_name="status", index_type="INVERTED")     # general
```

### Pre-Filtering vs. Post-Filtering

| Strategy | Behavior | When Used |
|----------|----------|-----------|
| **Pre-filtering** | Filter first, then ANN search | Small result set after filtering |
| **Post-filtering** | ANN search first, then filter | Large result set, few filtered out |

Milvus automatically chooses the optimal strategy based on filter selectivity.

## Complex Filter Examples

### E-Commerce Product Search

```python
filter = (
    "category in ['electronics', 'computers'] "
    "and price >= 100 and price <= 2000 "
    "and rating >= 4.0 "
    "and in_stock == true "
    "and not array_contains(tags, 'refurbished')"
)
```

### Document Search with Metadata

```python
filter = (
    'metadata["source"] in ["arxiv", "pubmed"] '
    'and metadata["year"] >= 2023 '
    'and metadata["citations"] > 10 '
    'and text like "%transformer%"'
)
```

### Multi-Tenant Filter

```python
filter = f"tenant_id == '{user_tenant_id}' and status == 'active'"
```

## Common Pitfalls

- **String values need quotes** — `category == tech` fails; use `category == 'tech'`
- **JSON keys need brackets and quotes** — `metadata.source` fails; use `metadata["source"]`
- **No regex support** — only `LIKE` with `%` and `_` wildcards
- **Filter on un-indexed fields is slow** — always add scalar indexes for frequently filtered fields
- **Boolean fields** — use `field == true` not `field is true`
- **Empty string vs NULL** — `field == ''` and `field is null` are different checks
