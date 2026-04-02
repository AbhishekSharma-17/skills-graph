# Qdrant — Multitenancy

> Source: [qdrant.tech/documentation/guides/multiple-partitions](https://qdrant.tech/documentation/guides/multiple-partitions/) | v1.17.1

## Overview

Multitenancy in Qdrant isolates data for different users/organizations within a single collection. The recommended approach is **payload-based tenant isolation** with tenant-optimized indexes — NOT separate collections per tenant.

**Why single collection > separate collections:**
- Lower memory overhead (shared HNSW graph structure)
- Simpler management (one collection to monitor, backup, optimize)
- Faster tenant onboarding (just upsert with tenant_id)
- Better resource utilization across tenants

## Basic Multitenancy Setup

### 1. Create Collection

```python
from qdrant_client import QdrantClient, models

client = QdrantClient("localhost", port=6333)

client.create_collection(
    collection_name="multi_tenant",
    vectors_config=models.VectorParams(
        size=768,
        distance=models.Distance.COSINE,
    ),
)
```

### 2. Create Tenant Index

```python
client.create_payload_index(
    collection_name="multi_tenant",
    field_name="tenant_id",
    field_schema=models.KeywordIndexParams(
        type="keyword",
        is_tenant=True,  # critical: marks as tenant field
    ),
)
```

**`is_tenant=True`** tells Qdrant to restructure internal storage to colocate data by tenant. This dramatically improves filtered search performance for tenant-scoped queries.

### 3. Upsert Data with Tenant ID

```python
client.upsert(
    collection_name="multi_tenant",
    points=[
        models.PointStruct(
            id=1,
            vector=[0.05, 0.61, 0.76, 0.74] + [0.0] * 764,
            payload={
                "tenant_id": "tenant_abc",
                "title": "Document 1",
                "content": "...",
            },
        ),
        models.PointStruct(
            id=2,
            vector=[0.19, 0.81, 0.75, 0.11] + [0.0] * 764,
            payload={
                "tenant_id": "tenant_xyz",
                "title": "Document 2",
                "content": "...",
            },
        ),
    ],
)
```

### 4. Search with Tenant Filter

**Always include tenant_id in every query:**

```python
results = client.query_points(
    collection_name="multi_tenant",
    query=[0.2, 0.1, 0.9, 0.7] + [0.0] * 764,
    query_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="tenant_id",
                match=models.MatchValue(value="tenant_abc"),
            )
        ]
    ),
    limit=10,
)
```

## UUID Tenant Index (v1.11.0+)

For UUID-based tenant IDs, use the optimized `uuid` index type:

```python
client.create_payload_index(
    collection_name="multi_tenant",
    field_name="tenant_id",
    field_schema=models.UuidIndexParams(
        type="uuid",
        is_tenant=True,
    ),
)
```

## Tiered Multitenancy (v1.16.0+)

For collections with a mix of small and large tenants, tiered multitenancy provides two levels of data organization:

- **Small tenants** share shard segments (efficient for thousands of small tenants)
- **Large tenants** get dedicated shard segments (prevents noisy neighbor problems)

Qdrant automatically manages the tiering based on data volume per tenant.

**Enable by setting the tenant index on the payload field.** Tiered multitenancy activates automatically when tenant sizes vary significantly.

## Shard Key Multitenancy

For very large deployments, use shard keys to physically separate tenant data:

```python
# Create collection with custom sharding
client.create_collection(
    collection_name="sharded_tenant",
    vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE),
    sharding_method=models.ShardingMethod.CUSTOM,
)

# Create shard for a tenant
client.create_shard_key(
    collection_name="sharded_tenant",
    shard_key="tenant_abc",
)

# Upsert to specific shard
client.upsert(
    collection_name="sharded_tenant",
    points=[
        models.PointStruct(
            id=1,
            vector=[0.05, 0.61, 0.76] + [0.0] * 765,
            payload={"title": "Doc 1"},
        ),
    ],
    shard_key_selector="tenant_abc",
)

# Search within specific shard
results = client.query_points(
    collection_name="sharded_tenant",
    query=[0.2, 0.1, 0.9] + [0.0] * 765,
    shard_key="tenant_abc",
    limit=10,
)
```

**When to use shard keys vs payload filtering:**
| Approach | Tenants | Isolation | Overhead |
|----------|---------|-----------|----------|
| Payload filter + `is_tenant` | 1 - 100,000+ | Logical | Low |
| Custom shard keys | 1 - 1,000 | Physical | Higher |
| Separate collections | 1 - 100 | Complete | Highest |

## Complete Multi-Tenant RAG Pattern

```python
from qdrant_client import QdrantClient, models

client = QdrantClient("localhost", port=6333)

# Setup
client.create_collection(
    collection_name="rag_documents",
    vectors_config=models.VectorParams(
        size=768,
        distance=models.Distance.COSINE,
        on_disk=True,
    ),
    quantization_config=models.ScalarQuantization(
        scalar=models.ScalarQuantizationConfig(
            type=models.ScalarType.INT8,
            always_ram=True,
        ),
    ),
    on_disk_payload=True,
)

# Tenant index
client.create_payload_index(
    collection_name="rag_documents",
    field_name="tenant_id",
    field_schema=models.KeywordIndexParams(type="keyword", is_tenant=True),
)

# Additional indexes for common filters
client.create_payload_index(
    collection_name="rag_documents",
    field_name="doc_type",
    field_schema="keyword",
)

client.create_payload_index(
    collection_name="rag_documents",
    field_name="created_at",
    field_schema=models.DatetimeIndexParams(type="datetime", is_principal=True),
)


def ingest_document(tenant_id: str, doc_id: str, chunks: list[dict]):
    """Ingest document chunks for a tenant."""
    points = [
        models.PointStruct(
            id=f"{doc_id}_{i}",
            vector=chunk["embedding"],
            payload={
                "tenant_id": tenant_id,
                "doc_id": doc_id,
                "chunk_index": i,
                "text": chunk["text"],
                "doc_type": chunk.get("doc_type", "general"),
                "created_at": chunk.get("created_at"),
            },
        )
        for i, chunk in enumerate(chunks)
    ]
    client.upsert(collection_name="rag_documents", points=points)


def search_tenant_docs(
    tenant_id: str,
    query_vector: list[float],
    doc_type: str | None = None,
    limit: int = 10,
) -> list:
    """Search documents for a specific tenant."""
    must_conditions = [
        models.FieldCondition(
            key="tenant_id",
            match=models.MatchValue(value=tenant_id),
        )
    ]
    if doc_type:
        must_conditions.append(
            models.FieldCondition(
                key="doc_type",
                match=models.MatchValue(value=doc_type),
            )
        )

    results = client.query_points(
        collection_name="rag_documents",
        query=query_vector,
        query_filter=models.Filter(must=must_conditions),
        limit=limit,
        with_payload=["text", "doc_id", "chunk_index"],
    )
    return results.points


def delete_tenant_data(tenant_id: str):
    """Remove all data for a tenant."""
    client.delete(
        collection_name="rag_documents",
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="tenant_id",
                        match=models.MatchValue(value=tenant_id),
                    )
                ]
            )
        ),
    )
```

## Common Pitfalls

1. **Missing `is_tenant=True`** — Without this flag, tenant-filtered searches scan all data. This is the most common performance mistake.
2. **Forgetting tenant filter** — Always include `tenant_id` in every query. A missing filter leaks data across tenants.
3. **Too many collections** — Don't create one collection per tenant (> 100 tenants). Use payload-based isolation instead.
4. **Tenant data deletion** — Use filter-based deletion. There's no "drop tenant" command — you delete points by filter.
5. **Uneven tenant sizes** — Tiered multitenancy (v1.16+) handles this automatically. Ensure your Qdrant version supports it.

## Related Topics

- Indexing → `references/05-indexing.md`
- Filtering → `references/04-filtering.md`
- Deployment → `references/12-deployment.md`
