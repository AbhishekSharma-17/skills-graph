# dlt Resources

> Source: https://dlthub.com/docs/general-usage/resource | dlt v1.29.1

## Table of Contents
- [Resource Basics](#resource-basics)
- [Resource Parameters](#resource-parameters)
- [Schema Definition](#schema-definition)
- [Pydantic Model Integration](#pydantic-model-integration)
- [Dynamic Table Dispatch](#dynamic-table-dispatch)
- [Standalone Resources](#standalone-resources)
- [Async and Parallel Resources](#async-and-parallel-resources)
- [Transformers](#transformers)
- [Data Transformation Methods](#data-transformation-methods)
- [Resource Limiting](#resource-limiting)
- [Runtime Hints](#runtime-hints)
- [File Import](#file-import)

## Resource Basics

A resource is a function decorated with `@dlt.resource` that yields data items:

```python
@dlt.resource(name="users", write_disposition="replace")
def get_users():
    for i in range(10):
        yield {"id": i, "name": f"user_{i}"}
```

Resources can yield:
- Individual dicts
- Lists of dicts (batches — more efficient)
- Pandas DataFrames
- Arrow tables

## Resource Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | function name | Table name in destination |
| `table_name` | str/callable | same as `name` | Override table name; callable for dynamic dispatch |
| `write_disposition` | str | "append" | "append", "replace", or "merge" |
| `primary_key` | str/list | None | Column(s) for deduplication in merge mode |
| `merge_key` | str/list | None | Column(s) for merge matching |
| `columns` | dict/TypedDict/Pydantic | None | Explicit column type definitions |
| `max_table_nesting` | int | 1000 | Maximum depth for nested table creation |
| `file_format` | str | None | Override loader file format ("parquet", "jsonl") |
| `parallelized` | bool | False | Enable thread pool parallelism for sync generators |
| `schema_contract` | dict/str | None | Schema evolution rules |

```python
@dlt.resource(
    name="orders",
    write_disposition="merge",
    primary_key="order_id",
    columns={"amount": {"data_type": "decimal"}},
    file_format="parquet"
)
def get_orders():
    yield from fetch_orders()
```

## Schema Definition

### Explicit Column Types
```python
@dlt.resource(
    name="events",
    columns={
        "tags": {"data_type": "json"},
        "created_at": {"data_type": "timestamp"},
        "amount": {"data_type": "decimal", "precision": 10, "scale": 2}
    }
)
def get_events():
    yield from fetch_events()
```

### Nested Table Hints
```python
@dlt.resource(
    nested_hints={
        "purchases": dlt.mark.make_nested_hints(
            columns=[{"name": "price", "data_type": "decimal"}],
            schema_contract={"columns": "freeze"}
        )
    }
)
def customers():
    yield [{"id": 1, "purchases": [{"id": 1, "price": "1.50"}]}]
```

Deep nesting uses tuple paths: `("purchases", "coupons")`.

## Pydantic Model Integration

```python
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    email: str | None = None

@dlt.resource(columns=User)
def get_users():
    yield {"id": 1, "name": "Alice", "email": "alice@example.com"}
    yield {"id": 2, "name": "Bob"}
```

Pydantic fields marked `Optional` become nullable. `Union` types convert to the first non-None type.

## Dynamic Table Dispatch

Route data to multiple tables from a single resource:

### Via table_name callable
```python
@dlt.resource(table_name=lambda event: event["type"])
def repo_events():
    yield {"type": "push", "repo": "dlt"}
    yield {"type": "star", "repo": "dlt"}
```

### Via inline marking
```python
@dlt.resource
def repo_events():
    for item in get_events():
        yield dlt.mark.with_table_name(item, item["type"])
```

## Standalone Resources

Top-level functions that accept configuration via dependency injection:

```python
@dlt.resource
def fs_resource(bucket_url=dlt.config.value):
    """List files in bucket_url."""
    yield from list_bucket(bucket_url)

# Must call with arguments before use
pipeline.run(fs_resource("s3://my-bucket"))
```

Dynamic naming for standalone resources:
```python
@dlt.resource(name=lambda args: args["stream_name"])
def kinesis(stream_name: str):
    yield from read_stream(stream_name)
```

## Async and Parallel Resources

### Parallelized sync generators
```python
@dlt.resource(parallelized=True)
def get_users():
    for user_id in range(100):
        yield fetch_user(user_id)  # Each yield runs in thread pool
```

### Async generators
```python
@dlt.resource
async def get_users():
    async for user in async_fetch_users():
        yield user
```

### Parallel extraction of multiple resources
```python
pipeline.run([get_users(), get_orders()])
```

## Transformers

Chain resources to pass data between them:

```python
@dlt.resource(write_disposition="replace")
def users(limit=None):
    for user in fetch_users(limit):
        yield user

@dlt.transformer(data_from=users)
def user_details(user_item):
    for detail in fetch_details(user_item["user_id"]):
        yield detail

# Dependencies resolved automatically
pipeline.run(user_details)
```

### Pipe operator for dynamic binding
```python
pipeline.run(users(limit=100) | user_details)
```

### Async transformers
```python
@dlt.transformer
async def pokemon(id):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"https://pokeapi.co/api/v2/pokemon/{id}")
        return r.json()

result = list([1, 2, 3] | pokemon())
```

## Data Transformation Methods

Resources support chained transformations:

```python
for user in (
    users()
    .add_filter(lambda user: user["user_id"] != "me")
    .add_map(anonymize_user)
):
    print(user)
```

| Method | Description |
|--------|-------------|
| `add_map(fn)` | Transform each item |
| `add_filter(fn)` | Keep items where fn returns True |
| `add_yield_map(fn)` | Expand single items to multiple |
| `add_metrics(fn)` | Collect statistics without modifying data |

### Metrics collection
```python
def track_filtered(items, meta, metrics):
    users_list = items if isinstance(items, list) else [items]
    for user in users_list:
        if user["user_id"] == "me":
            metrics["filtered_me_users"] = metrics.get("filtered_me_users", 0) + 1

users().add_metrics(track_filtered)
```

### Custom resource metrics
```python
@dlt.resource
def get_pokemons():
    custom_metrics = dlt.current.resource_metrics()
    custom_metrics["page_count"] = 0
    for page in paginate("/pokemon"):
        custom_metrics["page_count"] += 1
        yield page
```

## Resource Limiting

```python
# Limit by item count
resource().add_limit(10)

# Limit by row count (after unnesting)
resource().add_limit(10, count_rows=True)

# Time-based limit (seconds)
resource().add_limit(max_time=10)

# Combined limits
resource().add_limit(max_items=10, max_time=10)
```

## Runtime Hints

Modify schema hints after resource creation:

```python
tables = sql_database()
tables.users.apply_hints(
    write_disposition="merge",
    primary_key="user_id",
    incremental=dlt.sources.incremental("updated_at")
)
pipeline.run(tables)
```

### Inline hints during extraction
```python
@dlt.resource
def sql_table(table_name):
    for idx, batch in enumerate(get_batches(table_name)):
        if idx == 0:
            yield dlt.mark.with_hints(
                batch,
                dlt.mark.make_hints(
                    columns=infer_columns(table_name),
                    primary_key=get_pk(table_name)
                )
            )
        else:
            yield batch
```

### Resource duplication and renaming
```python
@dlt.resource
def fs_resource(bucket_url):
    yield from list_files(bucket_url)

@dlt.transformer
def csv_reader(file_item):
    yield from read_csv(file_item)

reports = fs_resource("s3://my-bucket/reports") | csv_reader()
transactions = fs_resource("s3://my-bucket/txns") | csv_reader()

pipeline.run([
    reports.with_name("reports"),
    transactions.with_name("transactions")
])
```

## File Import

Import files directly into destinations:

```python
@dlt.transformer(columns=columns)
def orders(items):
    for item in items:
        dest_file = os.path.join(import_folder, item["file_name"])
        item.fsspec.download(item["file_url"], dest_file)
        yield dlt.mark.with_file_import(dest_file, "csv")

downloader = filesystem(bucket_url="s3://my_bucket/csv") | orders
pipeline.run(orders, destination="snowflake")
```
