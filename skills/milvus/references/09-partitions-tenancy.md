# Milvus — Partitions & Multi-Tenancy

> Source: [milvus.io/docs/manage-partitions.md](https://milvus.io/docs/manage-partitions.md), [milvus.io/docs/multi_tenancy.md](https://milvus.io/docs/multi_tenancy.md) | Version: 3.0-beta

## Table of Contents

- [Partitions Overview](#partitions-overview)
- [Partition Operations](#partition-operations)
- [Partition Key](#partition-key)
- [Multi-Tenancy Strategies](#multi-tenancy-strategies)
- [Strategy Comparison](#strategy-comparison)
- [Common Pitfalls](#common-pitfalls)

## Partitions Overview

A partition is a subset of a collection that shares the same schema but contains a slice of the data. Every collection has a default `_default` partition. Collections support up to **1,024 partitions**.

Partitions improve performance by restricting searches to relevant data subsets and enable data isolation for multi-tenancy.

## Partition Operations

### List Partitions

```python
from pymilvus import MilvusClient

client = MilvusClient(uri="http://localhost:19530", token="root:Milvus")

partitions = client.list_partitions(collection_name="articles")
# ['_default']
```

### Create a Partition

```python
client.create_partition(
    collection_name="articles",
    partition_name="tech_docs",
)

client.create_partition(
    collection_name="articles",
    partition_name="science_docs",
)
```

### Check Existence

```python
exists = client.has_partition(
    collection_name="articles",
    partition_name="tech_docs",
)
# True
```

### Load Partitions

```python
# Load specific partitions (not the entire collection)
client.load_partitions(
    collection_name="articles",
    partition_names=["tech_docs"],
)
```

### Release Partitions

```python
client.release_partitions(
    collection_name="articles",
    partition_names=["tech_docs"],
)
```

### Drop a Partition

```python
# Must release before dropping
client.release_partitions(
    collection_name="articles",
    partition_names=["science_docs"],
)
client.drop_partition(
    collection_name="articles",
    partition_name="science_docs",
)
```

## Partition-Scoped Operations

### Insert into Partition

```python
data = [
    {"id": 1, "vector": [...], "title": "AI Research"},
    {"id": 2, "vector": [...], "title": "Neural Networks"},
]

client.insert(
    collection_name="articles",
    partition_name="tech_docs",
    data=data,
)
```

### Search within Partitions

```python
results = client.search(
    collection_name="articles",
    partition_names=["tech_docs", "science_docs"],
    data=[query_vector],
    limit=10,
    output_fields=["title"],
)
```

### Delete from Partition

```python
client.delete(
    collection_name="articles",
    partition_name="tech_docs",
    ids=[1, 2],
)
```

## Partition Key

Partition keys automatically route entities to partitions based on a scalar field value. Milvus creates **16 physical partitions** internally and distributes data using a hash of the partition key.

### Define a Partition Key

```python
from pymilvus import MilvusClient, DataType

schema = client.create_schema()
schema.add_field("id", DataType.INT64, is_primary=True, auto_id=True)
schema.add_field("embedding", DataType.FLOAT_VECTOR, dim=768)
schema.add_field("tenant_id", DataType.VARCHAR, max_length=64, is_partition_key=True)
schema.add_field("text", DataType.VARCHAR, max_length=5000)

client.create_collection(
    collection_name="multi_tenant_docs",
    schema=schema,
    index_params=index_params,
)
```

### Insert with Partition Key

```python
data = [
    {"embedding": [...], "tenant_id": "tenant_a", "text": "Doc 1"},
    {"embedding": [...], "tenant_id": "tenant_b", "text": "Doc 2"},
    {"embedding": [...], "tenant_id": "tenant_a", "text": "Doc 3"},
]

client.insert(collection_name="multi_tenant_docs", data=data)
# Milvus auto-routes each entity to the correct partition
```

### Search with Partition Key Filter

```python
results = client.search(
    collection_name="multi_tenant_docs",
    data=[query_vector],
    filter="tenant_id == 'tenant_a'",  # automatically searches only relevant partitions
    limit=10,
    output_fields=["text", "tenant_id"],
)
```

## Multi-Tenancy Strategies

Milvus supports four isolation strategies, each with different trade-offs:

### Strategy 1: Database-Level Isolation

Each tenant gets a separate database.

```python
# Create database per tenant
from pymilvus import connections, db

connections.connect(host="localhost", port="19530")
db.create_database("tenant_acme")
db.create_database("tenant_globex")

# Use tenant's database
db.using_database("tenant_acme")
```

| Aspect | Detail |
|--------|--------|
| Max tenants | 64 (configurable via `maxDatabaseNum`) |
| Isolation | Strongest — complete data separation |
| RBAC | Yes |
| Schema flexibility | High — each tenant can have different schemas |
| Best for | Regulated environments, enterprise customers |

### Strategy 2: Collection-Level Isolation

Each tenant gets a separate collection within the same database.

```python
# One collection per tenant
client.create_collection(
    collection_name="tenant_acme_docs",
    schema=schema,
    index_params=index_params,
)

client.create_collection(
    collection_name="tenant_globex_docs",
    schema=schema,
    index_params=index_params,
)
```

| Aspect | Detail |
|--------|--------|
| Max tenants | 65,536 |
| Isolation | Strong — physical separation |
| RBAC | Yes |
| Cross-tenant queries | Not supported |
| Best for | Mid-scale SaaS with strong isolation needs |

### Strategy 3: Partition-Level Isolation

Each tenant maps to a manually-created partition.

```python
# Create partitions per tenant
client.create_partition("shared_docs", partition_name="tenant_acme")
client.create_partition("shared_docs", partition_name="tenant_globex")

# Insert
client.insert("shared_docs", partition_name="tenant_acme", data=acme_data)

# Search
results = client.search(
    collection_name="shared_docs",
    partition_names=["tenant_acme"],
    data=[query_vector],
    limit=10,
)
```

| Aspect | Detail |
|--------|--------|
| Max tenants | 1,024 per collection |
| Isolation | Physical partition separation |
| RBAC | Not available |
| Cross-tenant queries | Yes |
| Best for | Analytics with cross-tenant aggregation |

### Strategy 4: Partition Key-Level Isolation (Recommended)

Automatic partitioning based on a field value. Best for large-scale multi-tenancy.

```python
# Schema with partition key
schema.add_field("tenant_id", DataType.VARCHAR, max_length=64, is_partition_key=True)

# Insert — routing is automatic
client.insert("docs", data=[{"tenant_id": "acme", "embedding": [...], "text": "..."}])

# Search — Milvus scans only relevant partitions
results = client.search(
    collection_name="docs",
    data=[query_vector],
    filter="tenant_id == 'acme'",
    limit=10,
)
```

| Aspect | Detail |
|--------|--------|
| Max tenants | Millions |
| Isolation | Physical + Logical (hash-based routing) |
| RBAC | Not available |
| Cross-tenant queries | Yes |
| Manual setup | None — fully automatic |
| Best for | Large-scale SaaS, millions of tenants |

## Strategy Comparison

| Factor | Database | Collection | Partition | Partition Key |
|--------|----------|-----------|-----------|---------------|
| **Scale** | 64 | 65,536 | 1,024 | Millions |
| **Isolation** | Strongest | Strong | Physical | Physical + Logical |
| **Schema Flex** | High | Medium | Low | Low |
| **RBAC** | Yes | Yes | No | No |
| **Cross-Tenant** | No | No | Yes | Yes |
| **Ops Overhead** | High | Medium | High (manual) | Low (automatic) |

## Choosing a Strategy

- **< 64 tenants with compliance requirements** → Database-level
- **< 65K tenants with strong isolation** → Collection-level
- **< 1K tenants needing cross-tenant analytics** → Partition-level
- **Unlimited tenants, uniform schema** → Partition key (recommended default)

## Common Pitfalls

- **Exceeding 1,024 partitions** — partition creation fails; use partition keys for more tenants
- **Searching without loading partitions** — partitions must be loaded before search
- **Forgetting to filter by partition key** — without a filter, Milvus scans all partitions (slow)
- **Manual partitions for thousands of tenants** — use partition keys instead for automatic management
- **Dropping a partition without releasing it first** — causes an error
