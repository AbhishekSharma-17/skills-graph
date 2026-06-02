# Weaviate — Multi-Tenancy

> Source: [docs.weaviate.io](https://docs.weaviate.io/weaviate/manage-collections/multi-tenancy) | Version: v1.37

## Table of Contents
- [Overview](#overview)
- [Enabling Multi-Tenancy](#enabling-multi-tenancy)
- [Auto-Tenant Creation](#auto-tenant-creation)
- [Managing Tenants](#managing-tenants)
- [Tenant Activity States](#tenant-activity-states)
- [CRUD with Tenants](#crud-with-tenants)
- [Search with Tenants](#search-with-tenants)
- [Cross-References](#cross-references)
- [Backup Considerations](#backup-considerations)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

Multi-tenancy provides complete data isolation within a single Weaviate collection. Each tenant gets its own shard, ensuring:

- **Data privacy**: Tenants cannot access each other's data
- **Performance isolation**: One tenant's load doesn't affect others
- **Cost efficiency**: Cold/offloaded tenants release resources
- **Scale**: Supports millions of tenants per collection

Use cases: SaaS applications, per-user data stores, per-customer RAG, multi-org platforms.

## Enabling Multi-Tenancy

Enable at collection creation (cannot be changed after):

```python
from weaviate.classes.config import Configure, Property, DataType

client.collections.create(
    "UserDocument",
    multi_tenancy_config=Configure.multi_tenancy(enabled=True),
    vector_config=Configure.Vectors.text2vec_openai(),
    properties=[
        Property(name="title", data_type=DataType.TEXT),
        Property(name="content", data_type=DataType.TEXT),
    ],
)
```

```typescript
await client.collections.create({
  name: 'UserDocument',
  multiTenancy: configure.multiTenancy({ enabled: true }),
  vectorizers: vectors.text2VecOpenAI(),
  properties: [
    { name: 'title', dataType: dataType.TEXT },
    { name: 'content', dataType: dataType.TEXT },
  ],
});
```

## Auto-Tenant Creation

Automatically create tenants when objects are inserted for non-existent tenants:

```python
client.collections.create(
    "UserDocument",
    multi_tenancy_config=Configure.multi_tenancy(
        enabled=True,
        auto_tenant_creation=True,
    ),
    properties=[...],
)
```

- Available since v1.25.0 for batch imports, v1.25.2+ for single inserts
- Tenant names are case-sensitive: "TenantA" and "tenanta" create separate tenants

## Managing Tenants

### Create Tenants

```python
from weaviate.classes.tenants import Tenant

collection = client.collections.use("UserDocument")
collection.tenants.create(
    tenants=[
        Tenant(name="tenant_alice"),
        Tenant(name="tenant_bob"),
        Tenant(name="tenant_charlie"),
    ]
)
```

Tenant names: alphanumeric, underscore, hyphen. Length: 4–64 characters.

### List All Tenants

```python
tenants = collection.tenants.get()
for name, tenant in tenants.items():
    print(f"{name}: {tenant.activity_status}")
```

### Get Specific Tenants

```python
# By name (single)
tenant = collection.tenants.get_by_name("tenant_alice")

# By names (multiple)
tenants = collection.tenants.get_by_names(["tenant_alice", "tenant_bob"])
```

### Delete Tenants

Permanently removes the tenant and ALL its data:

```python
collection.tenants.remove(["tenant_charlie"])
```

## Tenant Activity States

Control tenant resource usage with activity states:

| State | Data Location | Queryable | Resources |
|-------|--------------|-----------|-----------|
| `ACTIVE` | Memory + disk | Yes | Full |
| `INACTIVE` | Disk only | No | Minimal |
| `OFFLOADED` | Cloud storage (S3) | No | None |

### Change Tenant State

```python
from weaviate.classes.tenants import Tenant, TenantActivityStatus

# Deactivate (move to disk only)
collection.tenants.update(tenants=[
    Tenant(name="tenant_alice", activity_status=TenantActivityStatus.INACTIVE),
])

# Reactivate
collection.tenants.update(tenants=[
    Tenant(name="tenant_alice", activity_status=TenantActivityStatus.ACTIVE),
])

# Offload to cloud storage
collection.tenants.update(tenants=[
    Tenant(name="tenant_bob", activity_status=TenantActivityStatus.OFFLOADED),
])
```

### Auto-Tenant Activation

Automatically activate inactive tenants when accessed (v1.27+):

```python
Configure.multi_tenancy(
    enabled=True,
    auto_tenant_activation=True,
)
```

## CRUD with Tenants

All data operations require specifying the tenant:

### Insert Data

```python
tenant_collection = collection.with_tenant("tenant_alice")

uuid = tenant_collection.data.insert({
    "title": "Alice's Document",
    "content": "Private content for Alice...",
})
```

### Batch Import

```python
tenant_collection = collection.with_tenant("tenant_alice")

with tenant_collection.batch.dynamic() as batch:
    for doc in alice_documents:
        batch.add_object(properties=doc)
```

### Read Data

```python
tenant_collection = collection.with_tenant("tenant_alice")

# Fetch by ID
obj = tenant_collection.query.fetch_object_by_id(uuid)

# List objects
response = tenant_collection.query.fetch_objects(limit=10)
```

### Update Data

```python
tenant_collection = collection.with_tenant("tenant_alice")
tenant_collection.data.update(
    uuid=uuid,
    properties={"title": "Updated Title"},
)
```

### Delete Data

```python
tenant_collection = collection.with_tenant("tenant_alice")
tenant_collection.data.delete_by_id(uuid)
```

## Search with Tenants

All search types work per-tenant:

```python
tenant_collection = collection.with_tenant("tenant_alice")

# Vector search
response = tenant_collection.query.near_text(
    query="project updates",
    limit=5,
)

# Hybrid search
response = tenant_collection.query.hybrid(
    query="meeting notes",
    alpha=0.75,
    limit=5,
)

# BM25 search
response = tenant_collection.query.bm25(
    query="budget report",
    limit=5,
)

# RAG
response = tenant_collection.generate.near_text(
    query="project updates",
    limit=3,
    grouped_task="Summarize the key updates.",
)
```

## Cross-References

Multi-tenant objects can reference:
- Objects in the same tenant of the same collection
- Objects in non-multi-tenant collections

```python
tenant_collection = collection.with_tenant("tenant_alice")

# Add reference
tenant_collection.data.reference_add(
    from_uuid=document_uuid,
    from_property="hasCategory",
    to=category_uuid,  # Can reference non-tenant collection
)
```

Cross-tenant references (between different tenants) are not allowed.

## Backup Considerations

Only `ACTIVE` tenants are included in backups. `INACTIVE` and `OFFLOADED` tenants are excluded.

To ensure complete backup:

```python
# Activate all tenants before backup
tenants = collection.tenants.get()
inactive = [
    Tenant(name=name, activity_status=TenantActivityStatus.ACTIVE)
    for name, t in tenants.items()
    if t.activity_status != TenantActivityStatus.ACTIVE
]
if inactive:
    collection.tenants.update(tenants=inactive)

# Now perform backup...
```

## Common Pitfalls

1. **Forgetting `.with_tenant()`**: All operations on a multi-tenant collection require `.with_tenant()`. Without it, operations fail with a "tenant required" error.

2. **Case-sensitive tenant names**: "UserA" and "usera" are different tenants. Normalize names (e.g., lowercase) before creating tenants to avoid duplicates.

3. **Querying inactive tenants**: Querying an INACTIVE or OFFLOADED tenant returns an error. Check or auto-activate before querying.

4. **Backup excludes cold tenants**: INACTIVE and OFFLOADED tenants are not backed up. Activate all tenants before taking backups.

5. **Cannot disable multi-tenancy**: Once enabled on a collection, multi-tenancy cannot be disabled. Plan your schema accordingly.

6. **Cross-tenant references**: You cannot create references between objects in different tenants. Design your data model to keep related objects in the same tenant.

## Related Topics

- Collections & Schema → `01-collections.md`
- Data Operations → `03-data-operations.md`
- Filters → `07-filters.md`
