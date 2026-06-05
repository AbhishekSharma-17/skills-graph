# dbt — Seeds & Snapshots

> Source: https://docs.getdbt.com/docs/build/seeds · https://docs.getdbt.com/docs/build/snapshots

## Table of Contents
- [Seeds](#seeds)
- [Creating Seeds](#creating-seeds)
- [Running Seeds](#running-seeds)
- [Seed Configuration](#seed-configuration)
- [Testing Seeds](#testing-seeds)
- [Snapshots](#snapshots)
- [Snapshot Strategies](#snapshot-strategies)
- [Snapshot Meta-Fields](#snapshot-meta-fields)
- [Advanced Snapshot Config](#advanced-snapshot-config)
- [Running Snapshots](#running-snapshots)
- [Using Snapshots in Models](#using-snapshots-in-models)

## Seeds

Seeds are CSV files in your dbt project that `dbt seed` loads into your data warehouse as tables. They are version-controlled and code-reviewable.

### Good use cases
- Country code mappings
- Test email addresses to exclude from analytics
- Static lookup tables
- Employee account IDs for filtering

### Bad use cases
- Large data exports (use EL tools instead)
- Sensitive data (PII, passwords)
- Frequently changing data (use sources instead)

## Creating Seeds

1. Add a CSV file to the `seeds/` directory:

```csv
# seeds/country_codes.csv
country_code,country_name
US,United States
CA,Canada
GB,United Kingdom
DE,Germany
FR,France
JP,Japan
```

2. Reference in models with `ref()`:

```sql
-- models/staging/stg_orders_with_country.sql
select
    orders.*,
    countries.country_name
from {{ ref('stg_orders') }} orders
left join {{ ref('country_codes') }} countries
    on orders.country_code = countries.country_code
```

## Running Seeds

```bash
# Load all seeds
dbt seed

# Load a specific seed
dbt seed --select country_codes

# Full refresh (drop and recreate — needed when columns change)
dbt seed --full-refresh

# Exclude a seed
dbt seed --exclude country_codes

# Run models downstream of a seed
dbt run --select country_codes+
```

**Default behavior:** `dbt seed` truncates and reinserts data. Use `--full-refresh` when column structure changes.

## Seed Configuration

### Column types

```yaml
# dbt_project.yml
seeds:
  jaffle_shop:
    country_codes:
      +column_types:
        country_code: varchar(2)
    zip_codes:
      +column_types:
        zipcode: varchar(5)    # Preserve leading zeros
```

### Schema and tags

```yaml
seeds:
  jaffle_shop:
    +schema: seeds
    +tags: ['static_data']
```

### Custom seed directory

```yaml
# dbt_project.yml
seed-paths: ["data"]    # Instead of default "seeds"
```

## Testing Seeds

```yaml
# seeds/properties.yml
seeds:
  - name: country_codes
    description: ISO 3166-1 alpha-2 country code mappings
    columns:
      - name: country_code
        description: Two-letter country code
        data_tests:
          - unique
          - not_null
      - name: country_name
        data_tests:
          - unique
          - not_null
```

---

## Snapshots

Snapshots record changes to mutable tables over time, implementing **Type-2 Slowly Changing Dimensions (SCD2)**. They let you "look back in time" at previous data states.

### The problem snapshots solve

Source tables overwrite data — you lose history:
```
id | status  | updated_at
1  | shipped | 2024-01-02     ← "pending" state is gone
```

With snapshots, history is preserved:
```
id | status  | updated_at | dbt_valid_from | dbt_valid_to
1  | pending | 2024-01-01 | 2024-01-01     | 2024-01-02
1  | shipped | 2024-01-02 | 2024-01-02     | NULL
```

### Defining snapshots (YAML — dbt 1.9+)

```yaml
# snapshots/orders_snapshot.yml
snapshots:
  - name: orders_snapshot
    relation: source('jaffle_shop', 'orders')
    config:
      schema: snapshots
      unique_key: order_id
      strategy: timestamp
      updated_at: updated_at
```

## Snapshot Strategies

### Timestamp strategy (recommended)

Uses an `updated_at` column to detect changes.

```yaml
snapshots:
  - name: orders_snapshot
    relation: source('jaffle_shop', 'orders')
    config:
      schema: snapshots
      unique_key: order_id
      strategy: timestamp
      updated_at: updated_at
```

**Advantages:**
- Only tracks one column for change detection
- Handles schema changes automatically (new/removed columns)
- Less error-prone as source evolves

### Check strategy

Compares specific columns to detect changes. Use when `updated_at` is unreliable.

```yaml
snapshots:
  - name: orders_snapshot
    relation: source('jaffle_shop', 'orders')
    config:
      schema: snapshots
      unique_key: order_id
      strategy: check
      check_cols:
        - status
        - is_cancelled
```

**Check all columns:**
```yaml
check_cols: 'all'    # Not recommended — fragile
```

## Snapshot Meta-Fields

dbt adds these columns automatically:

| Field | Description | Customizable |
|-------|-------------|-------------|
| `dbt_valid_from` | When snapshot row was first inserted | Yes |
| `dbt_valid_to` | When row became invalid (NULL = current) | Yes |
| `dbt_scd_id` | Unique key for each snapshot row | Yes |
| `dbt_updated_at` | Source `updated_at` when row was inserted | Yes |
| `dbt_is_deleted` | Tracks hard deletes (opt-in) | Yes |

### Customizing meta-field names

```yaml
snapshots:
  - name: orders_snapshot
    relation: source('jaffle_shop', 'orders')
    config:
      unique_key: order_id
      strategy: timestamp
      updated_at: updated_at
      snapshot_meta_column_names:
        dbt_valid_from: effective_date
        dbt_valid_to: expiration_date
        dbt_scd_id: dimension_id
        dbt_updated_at: modified_date
```

## Advanced Snapshot Config

### dbt_valid_to_current (dbt 1.9+)

Set a value instead of NULL for current records:

```yaml
snapshots:
  - name: orders_snapshot
    relation: source('jaffle_shop', 'orders')
    config:
      unique_key: order_id
      strategy: timestamp
      updated_at: updated_at
      dbt_valid_to_current: '9999-12-31'
```

**Benefit:** Simplifies queries — no need for `OR dbt_valid_to IS NULL`:
```sql
-- Without dbt_valid_to_current (complex)
where dbt_valid_from <= '2024-06-01'
  and (dbt_valid_to > '2024-06-01' or dbt_valid_to is null)

-- With dbt_valid_to_current (simple)
where dbt_valid_from <= '2024-06-01'
  and dbt_valid_to > '2024-06-01'
```

### Hard deletes

Track when source records are deleted:

```yaml
snapshots:
  - name: orders_snapshot
    relation: source('jaffle_shop', 'orders')
    config:
      unique_key: order_id
      strategy: timestamp
      updated_at: updated_at
      hard_deletes: 'new_record'
```

**Result:**
```
id | status  | dbt_valid_from | dbt_valid_to | dbt_is_deleted
1  | pending | 2024-01-01     | 2024-01-02   | False
1  | shipped | 2024-01-02     | 2024-01-20   | False
1  | deleted | 2024-01-20     | 2024-01-20   | True
```

### Snapshot from a model (not just source)

```yaml
snapshots:
  - name: customers_snapshot
    relation: ref('stg_customers')
    config:
      unique_key: customer_id
      strategy: timestamp
      updated_at: last_modified_at
```

## Running Snapshots

```bash
# Run all snapshots
dbt snapshot

# Run specific snapshot
dbt snapshot --select orders_snapshot

# Run as part of build
dbt build    # includes snapshots
```

**Frequency:** Run between hourly and daily depending on business needs. Snapshots are a batch-based approach to Change Data Capture (CDC).

### Schema changes

dbt will:
- Create new columns from the source query
- Expand string column sizes (varchar)
- NOT delete columns removed from the source
- NOT change column types (except varchar expansion)

## Using Snapshots in Models

Reference snapshots like any other model:

```sql
-- Get current customer data
select *
from {{ ref('customers_snapshot') }}
where dbt_valid_to is null

-- Get customer state at a specific date
select *
from {{ ref('customers_snapshot') }}
where '2024-06-01' between dbt_valid_from
    and coalesce(dbt_valid_to, '9999-12-31')

-- Track status changes over time
select
    order_id,
    status,
    dbt_valid_from as status_changed_at,
    dbt_valid_to as status_ended_at,
    datediff('hour', dbt_valid_from,
        coalesce(dbt_valid_to, current_timestamp())) as hours_in_status
from {{ ref('orders_snapshot') }}
order by order_id, dbt_valid_from
```

### Best practices

- Use the **timestamp strategy** for most cases
- Test `unique_key` uniqueness on the source
- Set `dbt_valid_to_current` for simpler queries
- Run snapshots before `dbt run` in your pipeline
- Keep snapshots in a dedicated schema
