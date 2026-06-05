# dbt — Models & Materializations

> Source: https://docs.getdbt.com/docs/build/models · https://docs.getdbt.com/docs/build/materializations

## Table of Contents
- [What Are Models](#what-are-models)
- [SQL Models](#sql-models)
- [Python Models](#python-models)
- [Materializations](#materializations)
- [Configuring Materializations](#configuring-materializations)
- [View](#view)
- [Table](#table)
- [Incremental](#incremental)
- [Ephemeral](#ephemeral)
- [Materialized View](#materialized-view)
- [Performance Comparison](#performance-comparison)
- [Model Configuration](#model-configuration)

## What Are Models

Models are the core building blocks of dbt. Each model is a single file containing a final `select` statement that defines a data transformation. When you run `dbt run`, dbt executes each model's SQL against your data warehouse and materializes the result.

## SQL Models

The primary way to write dbt models — a `.sql` file in the `models/` directory.

```sql
-- models/marts/customers.sql
with customers as (
    select * from {{ ref('stg_jaffle_shop__customers') }}
),
orders as (
    select
        customer_id,
        min(order_date) as first_order_date,
        max(order_date) as most_recent_order_date,
        count(order_id) as number_of_orders
    from {{ ref('stg_jaffle_shop__orders') }}
    group by 1
)

select
    customers.customer_id,
    customers.first_name,
    customers.last_name,
    orders.first_order_date,
    orders.most_recent_order_date,
    coalesce(orders.number_of_orders, 0) as number_of_orders
from customers
left join orders using (customer_id)
```

**Key rules:**
- Each file contains exactly one final `select` statement
- Use `{{ ref('model_name') }}` to reference other models (creates DAG dependency)
- Use `{{ source('source_name', 'table_name') }}` to reference raw tables
- No semicolons at the end
- Use CTEs (`with` clauses) for readability

## Python Models

Available since dbt 1.3 for complex transformations, ML, or when SQL is impractical. Supported on Snowflake, BigQuery, Databricks, and Spark.

```python
# models/ml/customer_segments.py
def model(dbt, session):
    dbt.config(materialized="table")

    customers = dbt.ref("customers")

    # Use pandas/Snowpark for complex logic
    df = customers.to_pandas()
    df["segment"] = df["number_of_orders"].apply(
        lambda x: "high" if x > 10 else "medium" if x > 3 else "low"
    )

    return session.create_dataframe(df)
```

**Limitations:**
- Only `table` and `incremental` materializations
- Platform-dependent (not all adapters support Python models)
- Slower than SQL models for simple transforms

## Materializations

Materializations define how dbt persists a model in the warehouse. Five built-in strategies:

## Configuring Materializations

### Method 1: In-model config block

```sql
{{ config(materialized='table') }}

select * from {{ ref('stg_orders') }}
```

### Method 2: dbt_project.yml (apply to folders)

```yaml
models:
  jaffle_shop:
    staging:
      +materialized: view
    marts:
      +materialized: table
```

### Method 3: YAML properties file

```yaml
models:
  - name: customers
    config:
      materialized: table
```

**Precedence:** In-model config > YAML properties > dbt_project.yml

## View

Creates a database view (`CREATE VIEW AS`). Default materialization.

```sql
{{ config(materialized='view') }}

select
    id as customer_id,
    first_name,
    last_name,
    email
from {{ source('jaffle_shop', 'customers') }}
```

**Pros:**
- No additional storage cost
- Always reflects latest source data
- Fast to build

**Cons:**
- Slow to query if stacked on other views or complex logic
- Query time increases with transformation complexity

**When to use:**
- Staging models (lightweight renaming, casting)
- Simple transformations with low query frequency
- Start here, upgrade to `table` when queries slow down

## Table

Rebuilds a full table on each run (`CREATE TABLE AS`).

```sql
{{ config(materialized='table') }}

select
    customer_id,
    first_name,
    last_name,
    count(order_id) as lifetime_orders,
    sum(amount) as lifetime_value
from {{ ref('stg_customers') }}
left join {{ ref('stg_orders') }} using (customer_id)
left join {{ ref('stg_payments') }} using (order_id)
group by 1, 2, 3
```

**Pros:**
- Fast to query (pre-computed results)
- Ideal for BI tools and dashboards

**Cons:**
- Full rebuild each run (slow for large datasets)
- Stale between runs

**When to use:**
- Mart models queried by BI tools
- Complex joins or aggregations
- Models referenced by many downstream models

## Incremental

Processes only new/changed rows on subsequent runs. Detailed in `04-incremental-models.md`.

```sql
{{ config(
    materialized='incremental',
    unique_key='order_id'
) }}

select * from {{ ref('stg_orders') }}
{% if is_incremental() %}
where updated_at > (select max(updated_at) from {{ this }})
{% endif %}
```

**When to use:**
- Large event tables (billions of rows)
- When full rebuilds take too long
- Append-heavy data (logs, events, transactions)

## Ephemeral

Not built in the database. Injected as a CTE into downstream models.

```sql
{{ config(materialized='ephemeral') }}

select
    id as payment_id,
    order_id,
    amount / 100.0 as amount_dollars,
    payment_method
from {{ source('stripe', 'payments') }}
```

When referenced, the SQL is inlined as `__dbt__cte__model_name`:

```sql
with __dbt__cte__stg_payments as (
    select
        id as payment_id,
        order_id,
        amount / 100.0 as amount_dollars,
        payment_method
    from raw.stripe.payments
)
select * from __dbt__cte__stg_payments
```

**Pros:**
- No database object created (keeps warehouse clean)
- Reusable logic without storage cost

**Cons:**
- Cannot query directly (no table/view exists)
- Harder to debug (SQL is embedded in downstream queries)
- Does not support model contracts
- Cannot be used with `ref()` in operations

**When to use:**
- Very lightweight, early-stage transformations
- Logic used in only 1-2 downstream models
- When you don't need to query the model directly

## Materialized View

Creates a database-managed materialized view. Combines table performance with view freshness.

```sql
{{ config(
    materialized='materialized_view'
) }}

select
    date_trunc('day', order_date) as order_day,
    count(*) as order_count,
    sum(amount) as total_amount
from {{ ref('stg_orders') }}
group by 1
```

**Pros:**
- Database handles incremental refresh automatically
- `dbt run` acts as code deployment (like views)
- No manual incremental logic needed

**Cons:**
- Not supported on all platforms
- Fewer configuration options than incremental models
- Snowflake uses Dynamic Tables instead

**When to use:**
- Simple aggregations where the database can manage refresh
- When incremental models feel like overkill

## Performance Comparison

| Materialization | Build Speed | Query Speed | Data Freshness | Storage |
|-----------------|-------------|-------------|----------------|---------|
| View | Fast | Depends | Real-time | None |
| Table | Slow | Fast | On rebuild | Full |
| Incremental | Fast* | Fast | Recent | Full |
| Ephemeral | N/A | Depends | Real-time | None |
| Materialized View | Slow | Fast | Auto-refresh | Full |

*After initial build

## Model Configuration

### Common config options

```sql
{{ config(
    materialized='table',
    schema='analytics',
    alias='dim_customers',
    tags=['daily', 'finance'],
    enabled=true,
    persist_docs={"relation": true, "columns": true},
    pre_hook="ALTER SESSION SET TIMEZONE = 'UTC'",
    post_hook="GRANT SELECT ON {{ this }} TO ROLE reporter",
    grants={"select": ["reporter", "analyst"]}
) }}
```

### Config in YAML

```yaml
models:
  - name: customers
    description: One row per customer with lifetime metrics
    config:
      materialized: table
      schema: analytics
      tags: [daily, finance]
      grants:
        select: [reporter, analyst]
    columns:
      - name: customer_id
        description: Primary key
        data_tests:
          - unique
          - not_null
```

### schema and alias

```sql
-- Creates: analytics.analytics.dim_customers (if custom schema macro not set)
{{ config(
    schema='analytics',
    alias='dim_customers'
) }}
```

By default, dbt concatenates the target schema with the custom schema. Override with a custom `generate_schema_name` macro for cleaner behavior.
