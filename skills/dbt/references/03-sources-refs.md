# dbt — Sources, Refs & Lineage

> Source: https://docs.getdbt.com/docs/build/sources

## Table of Contents
- [The ref Function](#the-ref-function)
- [The source Function](#the-source-function)
- [Declaring Sources](#declaring-sources)
- [Source Properties](#source-properties)
- [Source Freshness](#source-freshness)
- [Non-Standard Names](#non-standard-names)
- [Source Selection](#source-selection)
- [DAG and Lineage](#dag-and-lineage)

## The ref Function

`ref()` is dbt's most important function. It creates dependencies between models and builds the DAG.

```sql
-- models/marts/orders.sql
select
    o.order_id,
    o.customer_id,
    p.amount
from {{ ref('stg_jaffle_shop__orders') }} o
left join {{ ref('stg_stripe__payments') }} p using (order_id)
```

**Compiled output:**
```sql
select
    o.order_id,
    o.customer_id,
    p.amount
from analytics.staging.stg_jaffle_shop__orders o
left join analytics.staging.stg_stripe__payments p using (order_id)
```

**What ref() does:**
- Resolves to the correct schema and table name for the current environment
- Creates a dependency edge in the DAG (execution order)
- Enables environment-agnostic SQL (dev vs prod schemas resolve automatically)
- Supports cross-project references (dbt Mesh)

### Cross-project ref

```sql
-- Reference a model from another dbt project
select * from {{ ref('other_project', 'public_model') }}
```

### ref with version

```sql
-- Reference a specific version of a model
select * from {{ ref('customers', v=2) }}
```

## The source Function

`source()` references raw tables loaded by external EL tools. Creates lineage from raw data into your dbt DAG.

```sql
-- models/staging/stg_jaffle_shop__orders.sql
select
    id as order_id,
    user_id as customer_id,
    order_date,
    status
from {{ source('jaffle_shop', 'orders') }}
```

**Compiled output:**
```sql
select
    id as order_id,
    user_id as customer_id,
    order_date,
    status
from raw.jaffle_shop.orders
```

## Declaring Sources

Sources are defined in YAML files, typically alongside staging models:

```yaml
# models/staging/jaffle_shop/_jaffle_shop__sources.yml
sources:
  - name: jaffle_shop
    database: raw
    schema: jaffle_shop
    description: Replica of the Postgres database used by the Jaffle Shop app
    tables:
      - name: orders
        description: One record per order. Includes cancelled and deleted orders.
        columns:
          - name: id
            description: Primary key of the orders table
            data_tests:
              - unique
              - not_null
          - name: status
            description: "Order status: placed, shipped, completed, returned"
            data_tests:
              - accepted_values:
                  values: ['placed', 'shipped', 'completed', 'returned']
      - name: customers
        description: One record per customer
        columns:
          - name: id
            data_tests:
              - unique
              - not_null
```

**Defaults:**
- `schema` defaults to `name` if not specified
- `database` defaults to the target database

### Multiple sources

```yaml
sources:
  - name: jaffle_shop
    database: raw
    tables:
      - name: orders
      - name: customers

  - name: stripe
    database: raw
    schema: stripe_data
    tables:
      - name: payments
```

## Source Properties

```yaml
sources:
  - name: jaffle_shop
    database: raw
    schema: jaffle_shop
    description: App database replica
    loader: fivetran
    tags: [jaffle_shop, daily]

    # Quoting rules
    quoting:
      database: true
      schema: true
      identifier: true

    # Default freshness for all tables
    config:
      freshness:
        warn_after: {count: 12, period: hour}
        error_after: {count: 24, period: hour}
      loaded_at_field: _etl_loaded_at

    tables:
      - name: orders
        identifier: api_orders        # Actual table name if different
        description: Raw order data
        config:
          freshness:                   # Override at table level
            warn_after: {count: 6, period: hour}
            error_after: {count: 12, period: hour}
        columns:
          - name: id
            data_tests:
              - unique
              - not_null

      - name: product_skus
        config:
          freshness: null              # Disable freshness check
```

## Source Freshness

Source freshness checks validate that EL pipelines are running on time.

### Configuration

```yaml
sources:
  - name: jaffle_shop
    config:
      freshness:
        warn_after: {count: 12, period: hour}
        error_after: {count: 24, period: hour}
      loaded_at_field: _etl_loaded_at
    tables:
      - name: orders
      - name: customers
```

### Running freshness checks

```bash
# Check all sources
dbt source freshness

# Check specific source
dbt source freshness --select source:jaffle_shop

# Check specific table
dbt source freshness --select source:jaffle_shop.orders
```

### Generated SQL

```sql
select
    max(_etl_loaded_at) as max_loaded_at,
    convert_timezone('UTC', current_timestamp()) as calculated_at
from raw.jaffle_shop.orders
```

### Freshness with filter (performance optimization)

```yaml
sources:
  - name: jaffle_shop
    config:
      freshness:
        warn_after: {count: 12, period: hour}
        error_after: {count: 24, period: hour}
      loaded_at_field: _etl_loaded_at
      filter: _etl_loaded_at >= date_sub(current_date(), interval 1 day)
    tables:
      - name: orders
```

### Build only fresh sources

```bash
# Check freshness first
dbt source freshness

# Build models downstream of fresh sources only
dbt build --select source_status:fresher+
```

## Non-Standard Names

When source table names don't match dbt naming conventions:

```yaml
sources:
  - name: jaffle_shop
    database: raw
    schema: postgres_backend_public_schema    # Actual schema name
    tables:
      - name: orders
        identifier: api_orders               # Actual table name
```

```sql
select * from {{ source('jaffle_shop', 'orders') }}
-- Compiles to: select * from raw.postgres_backend_public_schema.api_orders
```

### Quoting for case-sensitive identifiers

```yaml
sources:
  - name: jaffle_shop
    quoting:
      database: true
      schema: true
      identifier: true
    tables:
      - name: Order_Items    # Preserves case
```

## Source Selection

```bash
# Run tests on all sources
dbt test --select "source:*"

# Run tests on one source
dbt test --select source:jaffle_shop

# Run tests on a specific table
dbt test --select source:jaffle_shop.orders

# Run models downstream of a source
dbt run --select source:jaffle_shop+

# Run models downstream of a specific table
dbt run --select source:jaffle_shop.orders+
```

## DAG and Lineage

dbt builds a Directed Acyclic Graph from `ref()` and `source()` calls:

```
Sources (raw tables)
    ↓ source()
Staging Models (stg_)
    ↓ ref()
Intermediate Models (int_)
    ↓ ref()
Mart Models
    ↓
BI Tools / Dashboards (exposures)
```

### Viewing the DAG

```bash
# Generate documentation with DAG visualization
dbt docs generate
dbt docs serve

# List model dependencies
dbt ls --select +customers    # Upstream of customers
dbt ls --select customers+    # Downstream of customers
dbt ls --select +customers+   # Both directions
```

### Exposures (documenting downstream consumers)

```yaml
# models/exposures.yml
exposures:
  - name: weekly_revenue_dashboard
    description: Revenue dashboard in Looker
    type: dashboard
    owner:
      name: Finance Team
      email: finance@jaffle.shop
    depends_on:
      - ref('orders')
      - ref('customers')
    url: https://looker.jaffle.shop/dashboards/42
```

This enables lineage visibility from raw sources all the way to dashboards.
