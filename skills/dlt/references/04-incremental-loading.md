# dlt Incremental Loading

> Source: https://dlthub.com/docs/general-usage/incremental-loading | dlt v1.29.1

## Table of Contents
- [Overview](#overview)
- [Write Dispositions](#write-dispositions)
- [Cursor-Based Incremental](#cursor-based-incremental)
- [Incremental Parameters](#incremental-parameters)
- [Backfills with end_value](#backfills-with-end_value)
- [Row Order Optimization](#row-order-optimization)
- [Missing Cursor Handling](#missing-cursor-handling)
- [Deduplication](#deduplication)
- [Merge Strategies](#merge-strategies)
- [External Scheduler Integration](#external-scheduler-integration)
- [Refresh Modes](#refresh-modes)
- [Common Patterns](#common-patterns)

## Overview

Incremental loading loads only new or changed data instead of reprocessing everything. dlt supports this through:
- **Cursor-based incremental**: track a timestamp/ID field between runs
- **Merge write disposition**: upsert or delete-insert based on keys
- **SCD2**: track historical changes with validity columns

## Write Dispositions

| Disposition | Behavior | Use Case |
|-------------|----------|----------|
| `replace` | Full reload — replaces entire table | Dimension tables, small datasets |
| `append` | Adds new data only | Event logs, append-only data |
| `merge` | Updates based on keys | Mutable records, user profiles |

## Cursor-Based Incremental

The `dlt.sources.incremental` class tracks a cursor field between pipeline runs:

```python
@dlt.resource(primary_key="id")
def repo_issues(
    updated_at=dlt.sources.incremental(
        "updated_at",
        initial_value="1970-01-01T00:00:00Z"
    )
):
    for page in get_issues(since=updated_at.start_value):
        yield page
        # updated_at.last_value updates in real-time
```

### How it works
1. First run: `start_value` equals `initial_value`
2. dlt tracks the maximum cursor value seen across all yielded items
3. Next run: `start_value` equals the previously tracked maximum
4. Items with cursor values below `start_value` are filtered out

### State attributes
- `start_value` — maximum cursor from previous run (or `initial_value` on first run); read-only, constant during execution
- `last_value` — real-time cursor updated with each yielded item; persisted after completion
- `start_out_of_range` — True when yielded cursor exceeds initial_value
- `end_out_of_range` — True when yielded cursor exceeds end_value

## Incremental Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cursor_path` | str | required | JSON path to cursor field (e.g., "updated_at", "item.ts") |
| `initial_value` | any | None | Starting value for first run |
| `last_value_func` | callable | `max` | Function to compute tracked value (max, min, or custom) |
| `end_value` | any | None | Upper bound for backfills (exclusive by default) |
| `row_order` | str | None | "asc" or "desc" — enables early exit optimization |
| `primary_key` | str/tuple | resource PK | Override for deduplication only |
| `range_start` | str | "closed" | "closed" (include lower bound) or "open" (exclude) |
| `range_end` | str | "open" | "open" (exclude upper bound) or "closed" (include) |
| `on_cursor_value_missing` | str | "raise" | "raise", "include", or "exclude" |
| `allow_external_schedulers` | bool | False | Enable Airflow interval integration |

## Backfills with end_value

Specify a time window for stateless backfills:

```python
@dlt.resource(primary_key="id")
def repo_issues(
    updated_at=dlt.sources.incremental(
        "updated_at",
        initial_value="2024-01-01T00:00:00Z",
        end_value="2024-02-01T00:00:00Z"
    )
):
    for page in get_issues(
        since=updated_at.start_value,
        until=updated_at.end_value
    ):
        yield page
```

### Partitioned backfills
```python
# Run multiple time windows in parallel
july = repo_issues(
    updated_at=dlt.sources.incremental(
        initial_value="2024-07-01T00:00:00Z",
        end_value="2024-08-01T00:00:00Z"
    )
)
august = repo_issues(
    updated_at=dlt.sources.incremental(
        initial_value="2024-08-01T00:00:00Z",
        end_value="2024-09-01T00:00:00Z"
    )
)
```

When `end_value` is set, state is not modified (stateless backfill).

## Row Order Optimization

When data is ordered by the cursor field, enable early exit:

```python
@dlt.resource(primary_key="id")
def events(
    created_at=dlt.sources.incremental(
        "created_at",
        initial_value="1970-01-01T00:00:00Z",
        row_order="desc"  # Newest first — stop when past start_value
    )
):
    for page in get_events():
        yield page
```

- `row_order="asc"` — stops when cursor exceeds `end_value`
- `row_order="desc"` — stops when cursor falls below `start_value`

Works with: `sql_database`, `filesystem`, `mongodb` sources.

## Missing Cursor Handling

```python
@dlt.resource
def some_data(
    updated_at=dlt.sources.incremental(
        "updated_at",
        on_cursor_value_missing="include"
    )
):
    yield [
        {"id": 1, "updated_at": 1},
        {"id": 2},                      # Missing cursor — included
        {"id": 3, "updated_at": None},   # None cursor — included
    ]
```

| Mode | Missing path | None value |
|------|-------------|------------|
| `raise` | Exception | Exception |
| `include` | Item passes through | Item passes through |
| `exclude` | Item filtered out | Item filtered out |

### Transform before incremental
```python
def set_default(record):
    if record.get("updated_at") is None:
        record["updated_at"] = record.get("created_at")
    return record

resource = some_data().add_map(set_default, insert_at=1)
```

The `insert_at=1` ensures the transform runs before incremental filtering.

## Deduplication

Default behavior: items with previously seen primary keys are skipped.

```python
# Use resource primary_key for dedup
@dlt.resource(primary_key="id")
def get_items(cursor=dlt.sources.incremental("updated_at")):
    yield items

# Override primary_key for dedup only
@dlt.resource(primary_key="id")
def get_items(
    cursor=dlt.sources.incremental("updated_at", primary_key="unique_id")
):
    yield items

# Disable deduplication
@dlt.resource(primary_key="id")
def get_items(
    cursor=dlt.sources.incremental("updated_at", primary_key=())
):
    yield items
```

Deduplication is disabled when:
- `range_start="open"` (no overlap with previous range)
- `end_value` is specified (stateless backfill)
- `primary_key=()` is explicitly empty

## Merge Strategies

### delete-insert (default)
```python
@dlt.resource(
    write_disposition="merge",
    primary_key="id"
)
def users():
    yield from fetch_users()
```

### upsert
```python
@dlt.resource(
    write_disposition={"disposition": "merge", "strategy": "upsert"},
    primary_key="id"
)
def users():
    yield from fetch_users()
```

### SCD2 (Slowly Changing Dimension Type 2)
```python
@dlt.resource(
    write_disposition={"disposition": "merge", "strategy": "scd2"},
    primary_key="id"
)
def users():
    yield from fetch_users()
# Creates _dlt_valid_from and _dlt_valid_to columns
```

## External Scheduler Integration

### Airflow integration
```python
@dlt.resource(primary_key="id")
def tickets(
    updated_at=dlt.sources.incremental[int](
        "updated_at",
        allow_external_schedulers=True
    )
):
    for page in get_tickets(start_time=updated_at.start_value):
        yield page
```

### Manual interval injection
```python
from dlt.common.configuration.container import Container
from dlt.extract.incremental.context import TimeIntervalContext
import pendulum

start = pendulum.datetime(2024, 1, 15, tz="UTC")
end = pendulum.datetime(2024, 1, 16, tz="UTC")

with Container().injectable_context(TimeIntervalContext(interval=(start, end))):
    pipeline.run(my_source)
```

### Environment variables
```bash
export DLT_INTERVAL_START="2024-01-15T00:00:00Z"
export DLT_INTERVAL_END="2024-01-16T00:00:00Z"
```

## Refresh Modes

Reset incremental state and destination data:

```python
# Truncate tables, reset cursors
pipeline.run(source(), refresh="drop_data")

# Drop and recreate tables, reset schema
pipeline.run(source(), refresh="drop_resources")

# Full reset
pipeline.run(source(), refresh="drop_sources")
```

## Common Patterns

### Split loading into time-bounded chunks
```python
pipeline = dlt.pipeline("chunked_load", destination="duckdb")
messages = sql_table(
    table="chat_message",
    incremental=dlt.sources.incremental(
        "created_at",
        row_order="asc",
        range_start="open"
    ),
)
while not pipeline.run(messages.add_limit(max_time=60)).is_empty:
    pass
```

### Custom last_value_func for multi-type tracking
```python
def by_event_type(event):
    last_value = None
    if len(event) == 1:
        item, = event
    else:
        item, last_value = event
    if last_value is None:
        last_value = {}
    else:
        last_value = dict(last_value)
    item_type = item["type"]
    last_value[item_type] = max(
        item["created_at"],
        last_value.get(item_type, "1970-01-01T00:00:00Z")
    )
    return last_value

@dlt.resource(primary_key="id", table_name=lambda i: i["type"])
def get_events(
    last_created_at=dlt.sources.incremental("$", last_value_func=by_event_type)
):
    yield events
```

### Configuration-based incremental
```python
@dlt.resource(table_name="records")
def load_records(id_after: dlt.sources.incremental = dlt.config.value):
    for i in range(150):
        yield {"id": i, "idAfter": i}
```

```toml
# config.toml
[my_pipeline.sources.id_after]
cursor_path = "idAfter"
initial_value = 10
```
