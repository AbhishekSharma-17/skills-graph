# dlt Transformations

> Source: https://dlthub.com/docs/dlt-ecosystem/transformations | dlt v1.29.1

## Table of Contents
- [Overview](#overview)
- [ETL: Transform Before Loading](#etl-transform-before-loading)
- [add_map](#add_map)
- [add_filter](#add_filter)
- [add_yield_map](#add_yield_map)
- [Transformers](#transformers)
- [Processing Steps (REST API)](#processing-steps-rest-api)
- [ELT: Transform After Loading](#elt-transform-after-loading)
- [Dataset API](#dataset-api)
- [Nesting Control](#nesting-control)
- [Common Patterns](#common-patterns)

## Overview

dlt supports two transformation approaches:

- **ETL** (before loading): lightweight processing like adding columns, removing sensitive data, type casting — done in Python during extraction
- **ELT** (after loading): heavier transformations done in the destination using SQL, dbt, or compute engines

## ETL: Transform Before Loading

### Built-in transformation methods

Resources support chained transformation methods:

```python
for user in (
    users()
    .add_filter(lambda user: user["user_id"] != "me")
    .add_map(anonymize_user)
    .add_yield_map(expand_addresses)
):
    print(user)
```

Methods are applied in the order they're chained.

## add_map

Transform each item passing through the resource:

```python
def anonymize_user(user):
    user["email"] = hash_email(user["email"])
    user["name"] = "***"
    return user

pipeline.run(users().add_map(anonymize_user))
```

### Adding computed columns
```python
def add_timestamp(record):
    record["loaded_at"] = datetime.utcnow().isoformat()
    return record

pipeline.run(events().add_map(add_timestamp))
```

### Removing sensitive fields
```python
def remove_pii(record):
    record.pop("ssn", None)
    record.pop("phone", None)
    return record

pipeline.run(customers().add_map(remove_pii))
```

### Insertion order control
```python
resource().add_map(transform_fn, insert_at=1)
```

`insert_at=1` places the transform before incremental filtering, useful for setting default cursor values.

## add_filter

Keep only items where the function returns True:

```python
pipeline.run(
    events().add_filter(lambda e: e["type"] == "purchase")
)
```

### Multiple filters
```python
active_premium = (
    users()
    .add_filter(lambda u: u["is_active"])
    .add_filter(lambda u: u["plan"] == "premium")
)
pipeline.run(active_premium)
```

### Date-based filtering
```python
from datetime import datetime, timedelta

cutoff = (datetime.utcnow() - timedelta(days=30)).isoformat()
recent = events().add_filter(lambda e: e["created_at"] > cutoff)
pipeline.run(recent)
```

## add_yield_map

Expand a single item into multiple items:

```python
def expand_tags(record):
    for tag in record.get("tags", []):
        yield {
            "record_id": record["id"],
            "tag": tag
        }

pipeline.run(
    posts().add_yield_map(expand_tags),
    table_name="post_tags"
)
```

## Transformers

Chain resources where one feeds into another using the `@dlt.transformer` decorator:

```python
@dlt.resource(write_disposition="replace")
def users(limit=None):
    for user in fetch_users(limit):
        yield user

@dlt.transformer(data_from=users)
def user_details(user_item):
    for detail in fetch_user_detail(user_item["user_id"]):
        yield detail

# Static binding — dependencies auto-resolved
pipeline.run(user_details)
```

### Pipe operator for dynamic binding
```python
pipeline.run(users(limit=100) | user_details)
```

### Async transformers
```python
@dlt.transformer
async def enrich_user(user):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"https://api.example.com/enrich/{user['id']}")
        user["enrichment"] = r.json()
        return user
```

### Multi-step transformer chains
```python
pipeline.run(
    raw_events()
    | parse_event
    | enrich_event
    | validate_event
)
```

## Processing Steps (REST API)

The REST API source supports processing steps in resource configuration:

### Filter step
```python
"processing_steps": [
    {"filter": lambda x: x["status"] == "active"}
]
```

### Map step
```python
def normalize_title(record):
    record["title"] = record["title"].strip().lower()
    return record

"processing_steps": [
    {"map": normalize_title}
]
```

### Yield map step
```python
def flatten_reactions(post):
    for reaction in post["reactions"]:
        yield {"reaction": reaction, "post_id": post["id"]}

"processing_steps": [
    {"yield_map": flatten_reactions}
]
```

### Combined steps
```python
"processing_steps": [
    {"filter": lambda x: x["status"] == "active"},
    {"map": normalize_title},
    {"yield_map": flatten_reactions}
]
```

## ELT: Transform After Loading

### SQL transformations
Query loaded data using the pipeline's SQL client:

```python
with pipeline.sql_client() as client:
    client.execute_sql("""
        CREATE TABLE analytics.daily_revenue AS
        SELECT
            DATE(created_at) as date,
            SUM(amount) as revenue
        FROM raw.orders
        GROUP BY DATE(created_at)
    """)
```

### dbt integration
Run dbt models on data loaded by dlt:

```python
from dlt.helpers.dbt import create_runner

dbt = create_runner(
    venv=dlt.dbt.get_venv(pipeline),
    dataset_name=pipeline.dataset_name,
    working_dir="dbt_project/",
    package_additional_vars={"source_dataset": pipeline.dataset_name}
)

models = dbt.run_all()
for m in models:
    print(f"{m.model_name}: {m.status}")
```

## Dataset API

Read loaded data back for analysis:

```python
# Access the dataset
dataset = pipeline.dataset()

# Read a table
users_df = dataset["users"].df()  # As Pandas DataFrame
users_arrow = dataset["users"].arrow()  # As Arrow table

# Query with SQL
result = dataset.sql("SELECT * FROM users WHERE active = true")
for row in result:
    print(row)
```

## Nesting Control

Control how nested data structures are handled:

```python
# Source level
@dlt.source(max_table_nesting=1)
def my_source():
    return [resource_a(), resource_b()]

# Resource level
@dlt.resource(max_table_nesting=0)
def nested_data():
    yield {"id": 1, "nested": {"key": "value"}}

# Post-instantiation
source = my_source()
source.max_table_nesting = 0
```

| Level | Behavior |
|-------|----------|
| `0` | No child tables; nested data stored as JSON |
| `1` | One level of child tables |
| `1000` | Full nesting (default) |

## Common Patterns

### Anonymize before loading
```python
import hashlib

def anonymize(record):
    if "email" in record:
        record["email_hash"] = hashlib.sha256(
            record["email"].encode()
        ).hexdigest()
        del record["email"]
    return record

pipeline.run(users().add_map(anonymize))
```

### Add audit columns
```python
def add_audit(record):
    record["_loaded_at"] = pendulum.now("UTC").isoformat()
    record["_source"] = "hubspot_api"
    return record

pipeline.run(contacts().add_map(add_audit))
```

### Flatten nested structures before loading
```python
def flatten(record):
    if "address" in record:
        for key, val in record["address"].items():
            record[f"address_{key}"] = val
        del record["address"]
    return record

pipeline.run(customers().add_map(flatten))
```

### Sample data for development
```python
pipeline.run(
    large_dataset()
    .add_filter(lambda r: random.random() < 0.01)
    .add_limit(1000)
)
```
