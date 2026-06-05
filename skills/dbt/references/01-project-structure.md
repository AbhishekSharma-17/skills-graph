# dbt — Project Structure & Configuration

> Source: https://docs.getdbt.com/reference/dbt_project.yml · https://docs.getdbt.com/docs/core/connect-data-platform/profiles.yml

## Table of Contents
- [dbt_project.yml](#dbt_projectyml)
- [profiles.yml](#profilesyml)
- [Directory Layout](#directory-layout)
- [Best Practice Layers](#best-practice-layers)
- [Naming Conventions](#naming-conventions)
- [YAML Configuration Files](#yaml-configuration-files)
- [Environment Variables](#environment-variables)

## dbt_project.yml

The central configuration file for every dbt project. Lives at the project root.

```yaml
name: jaffle_shop
config-version: 2
version: 1.0.0
profile: jaffle_shop

# Directory paths
model-paths: [models]
seed-paths: [seeds]
test-paths: [tests]
analysis-paths: [analyses]
macro-paths: [macros]
snapshot-paths: [snapshots]
docs-paths: [docs]
packages-install-path: dbt_packages
clean-targets: [target, dbt_packages]

# dbt version constraint
require-dbt-version: [">=1.8.0", "<2.0.0"]

# Query comment appended to all SQL
query-comment: "jaffle_shop"

# Project variables
vars:
  payment_methods: ["bank_transfer", "credit_card", "gift_card"]

# Lifecycle hooks
on-run-start:
  - "{{ log('Starting dbt run', info=true) }}"
on-run-end:
  - "{{ log('dbt run complete', info=true) }}"

# Resource-level configs (+ prefix required here)
models:
  jaffle_shop:
    +materialized: view
    staging:
      +materialized: view
      +schema: staging
    marts:
      +materialized: table
      +schema: analytics

seeds:
  jaffle_shop:
    +schema: seeds

snapshots:
  jaffle_shop:
    +schema: snapshots
```

### Key fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Project identifier (letters, digits, underscores) |
| `config-version` | Yes | Always `2` |
| `version` | No | Semantic version for the project |
| `profile` | Yes* | Maps to profiles.yml (*not needed in dbt Cloud) |
| `model-paths` | No | Where models live (default: `[models]`) |
| `require-dbt-version` | Recommended | Prevents running with incompatible dbt versions |
| `vars` | No | Project-scoped variables accessible via `var()` |

### The `+` prefix

In `dbt_project.yml`, resource configs use a `+` prefix to distinguish from directory names:

```yaml
models:
  jaffle_shop:          # project name — no +
    staging:            # folder name — no +
      +materialized: view    # config — uses +
      +schema: staging       # config — uses +
```

The `+` is only used in `dbt_project.yml`. In YAML property files and `config()` blocks, omit it.

## profiles.yml

Stores database connection credentials. Lives at `~/.dbt/profiles.yml` (recommended) or project root.

```yaml
jaffle_shop:                    # Must match dbt_project.yml profile
  target: dev                   # Default target
  outputs:
    dev:
      type: postgres
      host: localhost
      user: "{{ env_var('DBT_USER') }}"
      password: "{{ env_var('DBT_PASSWORD') }}"
      port: 5432
      dbname: jaffle_shop
      schema: dbt_dev
      threads: 4

    prod:
      type: postgres
      host: prod-db.example.com
      user: "{{ env_var('DBT_PROD_USER') }}"
      password: "{{ env_var('DBT_PROD_PASSWORD') }}"
      port: 5432
      dbname: jaffle_shop
      schema: analytics
      threads: 8
```

### Adapter-specific examples

**Snowflake:**
```yaml
my_profile:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: abc12345.us-east-1
      user: "{{ env_var('SNOWFLAKE_USER') }}"
      password: "{{ env_var('SNOWFLAKE_PASSWORD') }}"
      database: analytics
      warehouse: transforming
      schema: dbt_dev
      threads: 4
      role: transformer
```

**BigQuery:**
```yaml
my_profile:
  target: dev
  outputs:
    dev:
      type: bigquery
      method: oauth
      project: my-gcp-project
      dataset: dbt_dev
      threads: 4
      location: US
```

**Databricks:**
```yaml
my_profile:
  target: dev
  outputs:
    dev:
      type: databricks
      host: "{{ env_var('DBT_DATABRICKS_HOST') }}"
      http_path: /sql/1.0/warehouses/abc123
      token: "{{ env_var('DBT_DATABRICKS_TOKEN') }}"
      catalog: main
      schema: dbt_dev
      threads: 4
```

### Key configuration

| Field | Description |
|-------|-------------|
| `target` | Default environment (typically `dev`) |
| `type` | Adapter: postgres, snowflake, bigquery, databricks, redshift |
| `schema` | Default schema for dbt objects. Convention: `dbt_<username>` for dev |
| `threads` | Parallel execution paths (default: 4) |

### Switching targets

```bash
dbt run --target prod
dbt test --target staging
```

## Directory Layout

### Standard project structure

```
jaffle_shop/
├── dbt_project.yml
├── packages.yml              # Package dependencies
├── package-lock.yml          # Locked versions (auto-generated)
├── .env                      # Environment variables (gitignored)
├── models/
│   ├── staging/              # Layer 1: Source cleanup
│   │   ├── jaffle_shop/
│   │   │   ├── _jaffle_shop__sources.yml
│   │   │   ├── _jaffle_shop__models.yml
│   │   │   ├── stg_jaffle_shop__customers.sql
│   │   │   └── stg_jaffle_shop__orders.sql
│   │   └── stripe/
│   │       ├── _stripe__sources.yml
│   │       ├── _stripe__models.yml
│   │       └── stg_stripe__payments.sql
│   ├── intermediate/         # Layer 2: Business logic prep
│   │   └── finance/
│   │       ├── _int_finance__models.yml
│   │       └── int_payments_pivoted_to_orders.sql
│   └── marts/                # Layer 3: Business entities
│       ├── finance/
│       │   ├── _finance__models.yml
│       │   ├── orders.sql
│       │   └── payments.sql
│       └── marketing/
│           ├── _marketing__models.yml
│           └── customers.sql
├── tests/                    # Singular data tests
│   └── assert_positive_total_amount.sql
├── seeds/                    # CSV lookup tables
│   ├── employees.csv
│   └── properties.yml
├── macros/                   # Reusable SQL/Jinja
│   ├── cents_to_dollars.sql
│   └── properties.yml
├── snapshots/                # SCD Type 2 history
│   └── orders_snapshot.yml
├── analyses/                 # Ad-hoc analytical SQL
└── docs/                     # Additional documentation
```

## Best Practice Layers

### Layer 1: Staging (`stg_`)

Atomic building blocks from source data. One staging model per source table.

```sql
-- models/staging/jaffle_shop/stg_jaffle_shop__orders.sql
with source as (
    select * from {{ source('jaffle_shop', 'orders') }}
),

renamed as (
    select
        id as order_id,
        user_id as customer_id,
        order_date,
        status,
        _etl_loaded_at
    from source
)

select * from renamed
```

**Rules:**
- Materialized as `view` (lightweight, always fresh)
- Rename columns to consistent conventions
- Cast data types explicitly
- No joins — one source table per staging model
- No business logic

### Layer 2: Intermediate (`int_`)

Purpose-built transformations that prepare staging models for joining.

```sql
-- models/intermediate/finance/int_payments_pivoted_to_orders.sql
select
    order_id,
    {% for method in var('payment_methods') %}
    sum(case when payment_method = '{{ method }}' then amount else 0 end) as {{ method }}_amount
    {% if not loop.last %},{% endif %}
    {% endfor %}
from {{ ref('stg_stripe__payments') }}
group by 1
```

**Rules:**
- Materialized as `ephemeral` or `view`
- Specific, descriptive names
- Often not exposed to end users

### Layer 3: Marts

Business-conformed entities — the final output for consumers.

```sql
-- models/marts/finance/orders.sql
with orders as (
    select * from {{ ref('stg_jaffle_shop__orders') }}
),
payments as (
    select * from {{ ref('int_payments_pivoted_to_orders') }}
)

select
    orders.order_id,
    orders.customer_id,
    orders.order_date,
    orders.status,
    payments.credit_card_amount,
    payments.bank_transfer_amount,
    payments.gift_card_amount,
    coalesce(payments.credit_card_amount, 0)
        + coalesce(payments.bank_transfer_amount, 0)
        + coalesce(payments.gift_card_amount, 0) as total_amount
from orders
left join payments using (order_id)
```

**Rules:**
- Materialized as `table` (fast queries for BI tools)
- Organized by business department (finance, marketing, etc.)
- Clean entity names (no prefixes)
- Wide, denormalized tables

## Naming Conventions

| Layer | Pattern | Example |
|-------|---------|---------|
| Staging | `stg_[source]__[entity]` | `stg_jaffle_shop__customers` |
| Base | `base_[source]__[entity]` | `base_jaffle_shop__deleted_users` |
| Intermediate | `int_[description]` | `int_payments_pivoted_to_orders` |
| Marts | `[entity]` | `customers`, `orders` |
| Snapshots | `[entity]_snapshot` | `orders_snapshot` |
| Seeds | `[descriptive_name]` | `country_codes`, `employee_ids` |

### File naming for YAML

```
_[source]__sources.yml     # Source declarations
_[source]__models.yml      # Model properties
_[area]__models.yml        # For non-staging areas
```

The leading underscore groups YAML files at the top of directory listings.

## YAML Configuration Files

Model properties and documentation live in YAML files alongside the SQL:

```yaml
# models/staging/jaffle_shop/_jaffle_shop__models.yml
models:
  - name: stg_jaffle_shop__customers
    description: Cleaned customer data from the Jaffle Shop app database
    columns:
      - name: customer_id
        description: Primary key
        data_tests:
          - unique
          - not_null
      - name: first_name
        description: Customer's first name
```

## Environment Variables

### .env file (dbt Core 1.12+, Fusion CLI)

```bash
# .env (gitignored)
DBT_USER=dev_user
DBT_PASSWORD=secret123
SNOWFLAKE_ACCOUNT=abc12345
```

### Usage in profiles.yml

```yaml
outputs:
  dev:
    user: "{{ env_var('DBT_USER') }}"
    password: "{{ env_var('DBT_PASSWORD') }}"
```

### Usage in dbt_project.yml

```yaml
vars:
  schema_prefix: "{{ env_var('DBT_SCHEMA_PREFIX', 'dev') }}"
```

The second argument to `env_var()` provides a default value.
