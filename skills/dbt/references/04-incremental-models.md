# dbt — Incremental Models

> Source: https://docs.getdbt.com/docs/build/incremental-models

## Table of Contents
- [What Are Incremental Models](#what-are-incremental-models)
- [Basic Pattern](#basic-pattern)
- [is_incremental Macro](#is_incremental-macro)
- [The this Variable](#the-this-variable)
- [unique_key](#unique_key)
- [Incremental Strategies](#incremental-strategies)
- [on_schema_change](#on_schema_change)
- [incremental_predicates](#incremental_predicates)
- [Full Refresh](#full-refresh)
- [Performance Tips](#performance-tips)
- [Common Patterns](#common-patterns)

## What Are Incremental Models

Incremental models process only new or changed rows on subsequent runs instead of rebuilding the entire table. This dramatically reduces runtime and compute costs for large datasets.

```sql
{{ config(materialized='incremental') }}

select * from {{ ref('stg_events') }}
{% if is_incremental() %}
where event_time > (select max(event_time) from {{ this }})
{% endif %}
```

**First run:** Creates the full table (like `materialized='table'`)
**Subsequent runs:** Inserts/updates only new rows matching the filter

## Basic Pattern

```sql
{{ config(
    materialized='incremental',
    unique_key='event_id'
) }}

select
    event_id,
    user_id,
    event_type,
    event_time,
    event_data
from {{ ref('stg_app_events') }}
{% if is_incremental() %}
    where event_time >= (select coalesce(max(event_time), '1900-01-01') from {{ this }})
{% endif %}
```

## is_incremental Macro

Returns `True` when ALL of these conditions are met:
1. The model already exists as a table in the database
2. The `--full-refresh` flag is NOT passed
3. The model is configured with `materialized='incremental'`

```sql
{% if is_incremental() %}
    -- This block runs only on incremental runs (not first build)
    where updated_at > (select max(updated_at) from {{ this }})
{% endif %}
```

The SQL must be valid whether `is_incremental()` evaluates to `True` or `False`. On the first run, the `{% if %}` block is skipped entirely.

## The this Variable

`{{ this }}` refers to the current model's existing table in the database. Only meaningful inside `{% if is_incremental() %}` blocks.

```sql
{% if is_incremental() %}
    where event_time >= (select max(event_time) from {{ this }})
{% endif %}
```

## unique_key

Controls upsert behavior — determines whether to update existing rows or only append.

### Without unique_key (append-only)

```sql
{{ config(
    materialized='incremental'
) }}
-- New rows are always inserted. Duplicates possible.
```

### With unique_key (upsert)

```sql
{{ config(
    materialized='incremental',
    unique_key='order_id'
) }}
-- Matching order_id: UPDATE existing row
-- New order_id: INSERT new row
```

### Composite unique_key

```sql
{{ config(
    materialized='incremental',
    unique_key=['user_id', 'session_number']
) }}
```

### Handling nulls in unique_key

Columns in `unique_key` must NOT contain nulls. Use coalesce:

```sql
{{ config(
    materialized='incremental',
    unique_key='surrogate_key'
) }}

select
    {{ dbt_utils.generate_surrogate_key(['user_id', 'event_type', 'event_date']) }} as surrogate_key,
    user_id,
    event_type,
    event_date,
    event_count
from {{ ref('stg_events') }}
{% if is_incremental() %}
where event_date >= (select max(event_date) from {{ this }})
{% endif %}
```

## Incremental Strategies

### append (simplest)

Inserts all new rows. No deduplication.

```sql
{{ config(
    materialized='incremental',
    incremental_strategy='append'
) }}
```

**Supported:** All adapters
**Use when:** Event logs, append-only data, no updates needed

### merge (default for most adapters)

Uses SQL `MERGE` statement. Updates matching rows, inserts new ones.

```sql
{{ config(
    materialized='incremental',
    incremental_strategy='merge',
    unique_key='order_id'
) }}
```

**Supported:** Snowflake, BigQuery, Databricks, Spark, Redshift
**Use when:** Rows can be updated (mutable data with a unique key)

### delete+insert

Deletes matching rows first, then inserts replacements. Useful when merge is slow.

```sql
{{ config(
    materialized='incremental',
    incremental_strategy='delete+insert',
    unique_key='order_id'
) }}
```

**Supported:** Postgres, Redshift, Snowflake
**Use when:** Large batch updates where merge performance is poor

### insert_overwrite

Replaces entire partitions. Does not use `unique_key`.

```sql
{{ config(
    materialized='incremental',
    incremental_strategy='insert_overwrite',
    partition_by={
        "field": "event_date",
        "data_type": "date",
        "granularity": "day"
    }
) }}
```

**Supported:** BigQuery, Spark, Databricks
**Use when:** Partition-based data (e.g., daily event tables)

### Adapter defaults

| Adapter | Default Strategy |
|---------|-----------------|
| Postgres | `append` |
| Redshift | `append` |
| Snowflake | `merge` |
| BigQuery | `merge` |
| Databricks | `merge` |
| Spark | `append` |

## on_schema_change

Controls behavior when the model's columns change between runs.

```sql
{{ config(
    materialized='incremental',
    unique_key='order_id',
    on_schema_change='sync_all_columns'
) }}
```

| Value | New Columns | Removed Columns | Type Changes |
|-------|-------------|-----------------|--------------|
| `ignore` (default) | Not added | Causes failure | Ignored |
| `fail` | Error raised | Error raised | Error raised |
| `append_new_columns` | Added | Not removed | Ignored |
| `sync_all_columns` | Added | Removed | Applied |

**Project-level default:**
```yaml
# dbt_project.yml
models:
  +on_schema_change: "sync_all_columns"
```

**Limitation:** Only tracks top-level columns, not nested/struct fields.

## incremental_predicates

Limits the scan of the existing table during merge operations. Critical performance optimization for large tables.

```sql
{{ config(
    materialized='incremental',
    unique_key='id',
    incremental_strategy='merge',
    cluster_by=['session_start'],
    incremental_predicates=[
        "DBT_INTERNAL_DEST.session_start > dateadd(day, -7, current_date)"
    ]
) }}
```

**Aliases:**
- `DBT_INTERNAL_DEST` — the existing/target table
- `DBT_INTERNAL_SOURCE` — temporary table with new records

**Generated merge:**
```sql
merge into existing_table DBT_INTERNAL_DEST
from temp_table DBT_INTERNAL_SOURCE
on DBT_INTERNAL_DEST.id = DBT_INTERNAL_SOURCE.id
   and DBT_INTERNAL_DEST.session_start > dateadd(day, -7, current_date)
when matched then update ...
when not matched then insert ...
```

## Full Refresh

Force a complete rebuild of an incremental model:

```bash
# Rebuild specific model and downstream
dbt run --full-refresh --select my_incremental_model+

# Rebuild all incremental models
dbt run --full-refresh
```

### Disable full_refresh for a model

```sql
{{ config(
    materialized='incremental',
    full_refresh=false
) }}
-- This model will NEVER be fully refreshed, even with --full-refresh flag
```

### When to use full_refresh

- After changing the model's SQL logic significantly
- After adding/removing columns with `on_schema_change='ignore'`
- When data quality issues require a clean rebuild
- After changing the `unique_key`

## Performance Tips

### Filter upstream CTEs early

```sql
{{ config(materialized='incremental', unique_key='id') }}

with events as (
    select * from {{ ref('stg_events') }}
    {% if is_incremental() %}
    where event_date >= dateadd(day, -3, current_date)
    {% endif %}
),
sessions as (
    select * from {{ ref('stg_sessions') }}
    {% if is_incremental() %}
    where session_start >= dateadd(day, -3, current_date)
    {% endif %}
)

select
    events.id,
    events.event_type,
    sessions.session_id,
    events.event_date
from events
left join sessions on events.session_id = sessions.session_id
```

### Use lookback windows

Instead of exact max timestamps, use a lookback window to catch late-arriving data:

```sql
{% if is_incremental() %}
where event_time >= dateadd(day, -3, (select max(event_time) from {{ this }}))
{% endif %}
```

### Cluster by filter columns

```sql
{{ config(
    materialized='incremental',
    unique_key='event_id',
    cluster_by=['event_date'],
    incremental_predicates=["DBT_INTERNAL_DEST.event_date > dateadd(day, -7, current_date)"]
) }}
```

## Common Patterns

### Daily aggregate

```sql
{{ config(
    materialized='incremental',
    unique_key='date_day'
) }}

select
    date_trunc('day', event_at) as date_day,
    count(distinct user_id) as daily_active_users,
    count(*) as total_events
from {{ ref('stg_events') }}
{% if is_incremental() %}
where date_day >= (select coalesce(max(date_day), '1900-01-01') from {{ this }})
{% endif %}
group by 1
```

### Late-arriving data with merge

```sql
{{ config(
    materialized='incremental',
    unique_key='event_id',
    incremental_strategy='merge'
) }}

select
    event_id,
    user_id,
    event_type,
    amount,
    updated_at
from {{ ref('stg_transactions') }}
{% if is_incremental() %}
where updated_at > (select dateadd(hour, -6, max(updated_at)) from {{ this }})
{% endif %}
```

### Python incremental model

```python
def model(dbt, session):
    dbt.config(materialized="incremental")
    df = dbt.ref("upstream_table")

    if dbt.is_incremental:
        max_ts = f"select max(updated_at) from {dbt.this}"
        df = df.filter(
            df.updated_at >= session.sql(max_ts).collect()[0][0]
        )

    return df
```
