# Weaviate — Data Operations (CRUD)

> Source: [docs.weaviate.io](https://docs.weaviate.io/weaviate/manage-data) | Version: v1.37

## Table of Contents
- [Insert Single Object](#insert-single-object)
- [Batch Import](#batch-import)
- [Insert with Custom Vectors](#insert-with-custom-vectors)
- [Deterministic IDs](#deterministic-ids)
- [Cross-References](#cross-references)
- [Read Objects](#read-objects)
- [Update Objects](#update-objects)
- [Delete Objects](#delete-objects)
- [Common Pitfalls](#common-pitfalls)

---

## Insert Single Object

### Python

```python
articles = client.collections.use("Article")
uuid = articles.data.insert({
    "title": "AI Revolution",
    "body": "Artificial intelligence is transforming...",
    "category": "technology",
})
print(uuid)  # Auto-generated UUID
```

### TypeScript

```typescript
const articles = client.collections.use('Article');
const uuid = await articles.data.insert({
  title: 'AI Revolution',
  body: 'Artificial intelligence is transforming...',
  category: 'technology',
});
console.log(uuid);
```

### With Custom UUID

```python
uuid = articles.data.insert(
    properties={"title": "Custom ID Article"},
    uuid="12345678-e64f-5d94-90db-c8cfa3fc1234"
)
```

## Batch Import

For bulk data loading, batch import is significantly faster than individual inserts. Weaviate handles vectorization, indexing, and error recovery.

### Dynamic Batching (Recommended)

```python
articles = client.collections.use("Article")

with articles.batch.dynamic() as batch:
    for item in data:
        batch.add_object(
            properties={
                "title": item["title"],
                "body": item["body"],
                "category": item["category"],
            },
        )

# Check for errors
if articles.batch.failed_objects:
    print(f"Failed: {len(articles.batch.failed_objects)}")
    for obj in articles.batch.failed_objects[:5]:
        print(f"  Error: {obj.message}")
```

### insert_many (Simpler API)

```python
import weaviate.classes as wvc

articles = client.collections.use("Article")

objects = [
    wvc.data.DataObject(
        properties={"title": "Article 1", "body": "Content 1"},
    ),
    wvc.data.DataObject(
        properties={"title": "Article 2", "body": "Content 2"},
    ),
]

response = articles.data.insert_many(objects)
print(f"Inserted: {len(response.all_responses)}")

# Check for errors
if response.has_errors:
    for idx, error in response.errors.items():
        print(f"  Object {idx}: {error.message}")
```

### Fixed-Size Batching

```python
with articles.batch.fixed_size(batch_size=100) as batch:
    for item in data:
        batch.add_object(properties=item)
```

### Rate-Limited Batching

```python
with articles.batch.rate_limit(requests_per_minute=600) as batch:
    for item in data:
        batch.add_object(properties=item)
```

### TypeScript Batch

```typescript
const articles = client.collections.use('Article');
let items = data.map(item => ({
  properties: { title: item.title, body: item.body },
}));
const response = await articles.data.insertMany(items);
```

## Insert with Custom Vectors

### Single Default Vector

```python
articles.data.insert(
    properties={"title": "Pre-vectorized article"},
    vector=[0.12345] * 1536,  # Your embedding
)
```

### Named Vectors

```python
reviews = client.collections.use("ProductReview")
reviews.data.insert(
    properties={
        "title": "Great product",
        "review_body": "Really enjoyed using this",
    },
    vector={
        "title_vector": [0.1] * 1536,
        "review_vector": [0.2] * 1536,
    },
)
```

### Batch with Vectors

```python
import weaviate.classes as wvc

objects = [
    wvc.data.DataObject(
        properties={"title": f"Article {i}"},
        vector=embeddings[i],
    )
    for i in range(len(data))
]
articles.data.insert_many(objects)
```

## Deterministic IDs

Generate consistent UUIDs from object content to prevent duplicates:

```python
from weaviate.util import generate_uuid5

data_object = {"title": "Unique Article", "body": "Content here"}
uuid = generate_uuid5(data_object)

articles.data.insert(
    properties=data_object,
    uuid=uuid,  # Same data always produces same UUID
)
```

Attempting to insert a duplicate UUID raises an error.

## Cross-References

Link objects across collections:

```python
# Create a reference from Article to Category
articles.data.insert(
    properties={"title": "AI News"},
    uuid=article_uuid,
    references={"hasCategory": category_uuid},
)

# Add reference to existing object
articles.data.reference_add(
    from_uuid=article_uuid,
    from_property="hasCategory",
    to=another_category_uuid,
)

# Replace all references
articles.data.reference_replace(
    from_uuid=article_uuid,
    from_property="hasCategory",
    to=new_category_uuid,
)

# Delete a reference
articles.data.reference_delete(
    from_uuid=article_uuid,
    from_property="hasCategory",
    to=category_uuid,
)
```

Cross-reference queries can be slower at scale. Prefer embedding related data directly when performance matters.

## Read Objects

### Fetch by ID

```python
articles = client.collections.use("Article")
obj = articles.query.fetch_object_by_id(uuid)
print(obj.properties["title"])
print(obj.uuid)
```

### Fetch with Vector

```python
obj = articles.query.fetch_object_by_id(
    uuid,
    include_vector=True,
)
print(obj.vector["default"])
```

### Fetch with Named Vectors

```python
obj = reviews.query.fetch_object_by_id(
    uuid,
    include_vector=["title_vector", "review_vector"],
)
```

### List Objects (Fetch Many)

```python
response = articles.query.fetch_objects(limit=10)
for obj in response.objects:
    print(obj.properties["title"])
```

### Cursor-Based Pagination

```python
cursor = None
while True:
    response = articles.query.fetch_objects(
        limit=100,
        after=cursor,
    )
    if not response.objects:
        break
    for obj in response.objects:
        print(obj.properties["title"])
    cursor = response.objects[-1].uuid
```

### Check Existence

```python
exists = articles.data.exists(uuid)
```

## Update Objects

### Replace All Properties

```python
articles.data.replace(
    uuid=article_uuid,
    properties={
        "title": "Updated Title",
        "body": "Completely new body",
        "category": "science",
    },
)
```

### Update Specific Properties (Merge)

```python
articles.data.update(
    uuid=article_uuid,
    properties={"title": "Just Update Title"},
)
```

### Update with New Vector

```python
articles.data.update(
    uuid=article_uuid,
    properties={"title": "Updated with new vector"},
    vector=[0.5] * 1536,
)
```

## Delete Objects

### Delete by ID

```python
articles.data.delete_by_id(uuid)
```

### Delete by Filter (Batch Delete)

```python
from weaviate.classes.query import Filter

articles.data.delete_many(
    where=Filter.by_property("category").equal("outdated"),
)
```

### Delete with Dry Run

```python
result = articles.data.delete_many(
    where=Filter.by_property("category").equal("outdated"),
    dry_run=True,
)
print(f"Would delete: {result.matches}")
```

## Common Pitfalls

1. **Not checking batch errors**: Batch imports silently collect errors. Always check `batch.failed_objects` or `response.errors` after a batch.

2. **Vectors in properties**: If you pass a vector inside the `properties` dict instead of the `vector` parameter, Weaviate stores it as a regular property, not an embedding.

3. **Replace vs Update**: `replace()` overwrites ALL properties (missing ones become null). `update()` merges only specified properties. Use `update()` for partial changes.

4. **Cursor pagination ordering**: `after` cursor pagination returns objects in UUID order, not insertion order. For ordered retrieval, use search with sorting.

5. **Batch size with vectorizers**: When using API-based vectorizers (OpenAI, Cohere), batch too aggressively and you'll hit rate limits. Use `rate_limit()` batching.

## Related Topics

- Collections & Schema → `01-collections.md`
- Vector Configuration → `02-vector-config.md`
- Filters → `07-filters.md`
