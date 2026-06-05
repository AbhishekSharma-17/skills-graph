# dbt — Hooks & Operations

> Source: https://docs.getdbt.com/docs/build/hooks-operations

## Table of Contents
- [Overview](#overview)
- [Pre-hooks and Post-hooks](#pre-hooks-and-post-hooks)
- [on-run-start and on-run-end](#on-run-start-and-on-run-end)
- [Operations and run-operation](#operations-and-run-operation)
- [Grants](#grants)
- [Common Use Cases](#common-use-cases)
- [Transaction Behavior](#transaction-behavior)

## Overview

Hooks are SQL statements that execute at specific points in the dbt lifecycle. Operations are macros invoked manually via `dbt run-operation`.

| Hook Type | When It Runs | Scope |
|-----------|-------------|-------|
| `pre-hook` | Before a model/seed/snapshot builds | Per-resource |
| `post-hook` | After a model/seed/snapshot builds | Per-resource |
| `on-run-start` | Before the entire dbt run | Global |
| `on-run-end` | After the entire dbt run | Global |

## Pre-hooks and Post-hooks

### In-model config

```sql
{{ config(
    materialized='table',
    pre_hook="ALTER SESSION SET TIMEZONE = 'UTC'",
    post_hook="GRANT SELECT ON {{ this }} TO ROLE analyst"
) }}

select * from {{ ref('stg_orders') }}
```

### Multiple hooks

```sql
{{ config(
    post_hook=[
        "GRANT SELECT ON {{ this }} TO ROLE analyst",
        "GRANT SELECT ON {{ this }} TO ROLE reporter",
        "ALTER TABLE {{ this }} SET COMMENT = 'Updated by dbt'"
    ]
) }}
```

### In YAML properties

```yaml
models:
  - name: customers
    config:
      post_hook:
        - "GRANT SELECT ON {{ this }} TO ROLE analyst"
```

### In dbt_project.yml (apply to all models in a folder)

```yaml
models:
  jaffle_shop:
    marts:
      +post-hook:
        - "GRANT SELECT ON {{ this }} TO ROLE analyst"
```

### Using a macro in a hook

```sql
-- macros/grant_select.sql
{% macro grant_to_role(role) %}
    GRANT SELECT ON {{ this }} TO ROLE {{ role }}
{% endmacro %}
```

```sql
{{ config(
    post_hook="{{ grant_to_role('analyst') }}"
) }}
```

## on-run-start and on-run-end

Global hooks that run at the beginning and end of `dbt build`, `dbt run`, `dbt test`, `dbt seed`, `dbt snapshot`, `dbt compile`, and `dbt docs generate`.

```yaml
# dbt_project.yml
on-run-start:
  - "{{ log('Starting dbt run at ' ~ modules.datetime.datetime.now(), info=true) }}"
  - "CREATE SCHEMA IF NOT EXISTS {{ target.schema }}_staging"

on-run-end:
  - "{{ log('dbt run complete', info=true) }}"
  - "GRANT USAGE ON SCHEMA {{ target.schema }} TO ROLE analyst"
```

### Available context in on-run-end

```yaml
on-run-end:
  # Access run results
  - "{{ log('Models run: ' ~ results|length, info=true) }}"
```

### Creating schemas on run start

```yaml
on-run-start:
  - "CREATE SCHEMA IF NOT EXISTS {{ target.schema }}"
  - "CREATE SCHEMA IF NOT EXISTS {{ target.schema }}_staging"
  - "CREATE SCHEMA IF NOT EXISTS {{ target.schema }}_snapshots"
```

## Operations and run-operation

Operations are macros invoked manually via the CLI — they don't run as part of `dbt run`.

### Defining an operation

```sql
-- macros/operations/grant_select.sql
{% macro grant_select(role) %}
    {% set sql %}
        GRANT USAGE ON SCHEMA {{ target.schema }} TO ROLE {{ role }};
        GRANT SELECT ON ALL TABLES IN SCHEMA {{ target.schema }} TO ROLE {{ role }};
        GRANT SELECT ON ALL VIEWS IN SCHEMA {{ target.schema }} TO ROLE {{ role }};
    {% endset %}

    {% do run_query(sql) %}
    {% do log("Privileges granted to " ~ role, info=True) %}
{% endmacro %}
```

### Running an operation

```bash
dbt run-operation grant_select --args '{role: reporter}'
```

### Key difference from hooks

Operations must explicitly execute queries using `run_query()` or statement blocks. In hooks, the SQL is executed automatically.

### Operation with return value

```sql
-- macros/operations/get_row_count.sql
{% macro get_row_count(model_name) %}
    {% set query %}
        SELECT COUNT(*) as cnt FROM {{ ref(model_name) }}
    {% endset %}

    {% set results = run_query(query) %}
    {% if execute %}
        {% set count = results.columns[0].values()[0] %}
        {{ log(model_name ~ " has " ~ count ~ " rows", info=True) }}
    {% endif %}
{% endmacro %}
```

```bash
dbt run-operation get_row_count --args '{model_name: customers}'
```

## Grants

dbt has a built-in `grants` config for managing database permissions — use this instead of post-hooks when possible.

```yaml
# dbt_project.yml
models:
  jaffle_shop:
    +grants:
      select: ['analyst', 'reporter']

# Or per-model in YAML
models:
  - name: customers
    config:
      grants:
        select: ['analyst', 'reporter']
```

```sql
-- Or in-model config
{{ config(
    grants={'select': ['analyst', 'reporter']}
) }}
```

### Grants behavior

- On `table` and `incremental`: Grants are applied after build
- On `view`: Grants are applied after view creation
- Grants are **revoked** for roles not in the config (clean slate)

## Common Use Cases

### Warehouse management (Snowflake)

```yaml
# Resume/suspend warehouse
on-run-start:
  - "ALTER WAREHOUSE transforming RESUME IF SUSPENDED"
on-run-end:
  - "ALTER WAREHOUSE transforming SUSPEND"
```

### Table maintenance (Redshift)

```sql
{{ config(
    post_hook=[
        "VACUUM {{ this }}",
        "ANALYZE {{ this }}"
    ]
) }}
```

### Row access policies (Snowflake)

```sql
{{ config(
    post_hook="ALTER TABLE {{ this }} ADD ROW ACCESS POLICY my_policy ON (region)"
) }}
```

### Creating UDFs

```yaml
on-run-start:
  - >
    CREATE OR REPLACE FUNCTION clean_email(email VARCHAR)
    RETURNS VARCHAR
    AS 'LOWER(TRIM(email))'
```

### Audit logging

```sql
-- macros/audit_log.sql
{% macro log_model_run() %}
    INSERT INTO audit.model_runs (model_name, run_at, target, status)
    VALUES ('{{ this.name }}', CURRENT_TIMESTAMP(), '{{ target.name }}', 'success')
{% endmacro %}
```

```yaml
models:
  jaffle_shop:
    +post-hook:
      - "{{ log_model_run() }}"
```

### Database cloning (Snowflake)

```bash
dbt run-operation clone_database --args '{source_db: production, target_db: staging}'
```

```sql
{% macro clone_database(source_db, target_db) %}
    {% set sql %}
        CREATE OR REPLACE DATABASE {{ target_db }} CLONE {{ source_db }};
    {% endset %}
    {% do run_query(sql) %}
    {{ log("Cloned " ~ source_db ~ " to " ~ target_db, info=True) }}
{% endmacro %}
```

## Transaction Behavior

- `pre-hook` and `post-hook` run inside the same transaction as the model (for transactional databases)
- `on-run-start` and `on-run-end` run outside model transactions
- To run a hook outside the transaction:

```yaml
models:
  - name: my_model
    config:
      post_hook:
        - sql: "VACUUM {{ this }}"
          transaction: false
```
