# dbt — Tests

> Source: https://docs.getdbt.com/docs/build/tests

## Table of Contents
- [Overview](#overview)
- [Data Tests vs Unit Tests](#data-tests-vs-unit-tests)
- [Built-in Generic Tests](#built-in-generic-tests)
- [Singular Tests](#singular-tests)
- [Custom Generic Tests](#custom-generic-tests)
- [Test Configuration](#test-configuration)
- [Store Failures](#store-failures)
- [Running Tests](#running-tests)
- [Testing Patterns](#testing-patterns)
- [Debugging Failed Tests](#debugging-failed-tests)

## Overview

Tests are assertions about your data. When you run `dbt test`, dbt executes each test as a SQL query that returns failing rows. If zero rows are returned, the test passes.

```sql
-- A test is a query that finds "bad" records
-- Passing = 0 rows returned
-- Failing = 1+ rows returned
select * from orders where order_id is null
```

## Data Tests vs Unit Tests

| Feature | Data Tests | Unit Tests |
|---------|-----------|------------|
| **What they test** | Actual data in models/sources | SQL logic in isolation |
| **When they run** | After `dbt run` (on materialized data) | Before `dbt run` (on mock data) |
| **YAML key** | `data_tests:` | `unit_tests:` |
| **File location** | `tests/` directory or inline YAML | Under `model-paths` (e.g., `models/`) |

## Built-in Generic Tests

dbt ships four generic tests. Apply them in YAML property files:

### unique

Ensures all values in a column are distinct.

```yaml
models:
  - name: orders
    columns:
      - name: order_id
        data_tests:
          - unique
```

### not_null

Ensures no null values exist.

```yaml
columns:
  - name: order_id
    data_tests:
      - not_null
```

### accepted_values

Ensures column values are within an expected set.

```yaml
columns:
  - name: status
    data_tests:
      - accepted_values:
          values: ['placed', 'shipped', 'completed', 'returned']
```

### relationships

Ensures referential integrity (foreign key validation).

```yaml
columns:
  - name: customer_id
    data_tests:
      - relationships:
          to: ref('customers')
          field: customer_id
```

### Combined example

```yaml
models:
  - name: orders
    columns:
      - name: order_id
        description: Primary key
        data_tests:
          - unique
          - not_null
      - name: status
        data_tests:
          - accepted_values:
              values: ['placed', 'shipped', 'completed', 'returned']
      - name: customer_id
        data_tests:
          - not_null
          - relationships:
              to: ref('customers')
              field: customer_id
```

## Singular Tests

One-off test queries written as SQL files in the `tests/` directory.

```sql
-- tests/assert_total_payment_amount_is_positive.sql
select
    order_id,
    sum(amount) as total_amount
from {{ ref('fct_payments') }}
group by 1
having total_amount < 0
```

**Rules:**
- File name becomes the test name
- No semicolons at the end
- Return rows that FAIL the assertion
- Automatically discovered and run by `dbt test`

### Documenting singular tests

```yaml
# tests/schema.yml
data_tests:
  - name: assert_total_payment_amount_is_positive
    description: >
      Refunds have negative amounts, so the total per order
      should always be >= 0. Returns failing orders.
```

## Custom Generic Tests

Parameterized, reusable tests defined as Jinja macros in `tests/generic/` or `macros/`.

### Defining a custom test

```sql
-- tests/generic/test_is_positive.sql
{% test is_positive(model, column_name) %}
select *
from {{ model }}
where {{ column_name }} < 0
{% endtest %}
```

### Using a custom test

```yaml
models:
  - name: orders
    columns:
      - name: total_amount
        data_tests:
          - is_positive
```

### Custom test with arguments

```sql
-- tests/generic/test_accepted_range.sql
{% test accepted_range(model, column_name, min_value=0, max_value=1000) %}
select *
from {{ model }}
where {{ column_name }} < {{ min_value }}
   or {{ column_name }} > {{ max_value }}
{% endtest %}
```

```yaml
columns:
  - name: price
    data_tests:
      - accepted_range:
          min_value: 0
          max_value: 99999
```

### Popular test packages

- **dbt-utils** — `unique_combination_of_columns`, `expression_is_true`, `recency`, etc.
- **dbt-expectations** — Great Expectations-style tests (`expect_column_values_to_be_between`, etc.)

```yaml
# Using dbt-utils
models:
  - name: orders
    data_tests:
      - dbt_utils.unique_combination_of_columns:
          combination_of_columns:
            - country_code
            - order_id
      - dbt_utils.expression_is_true:
          expression: "total_amount >= 0"
```

## Test Configuration

### Severity

```yaml
data_tests:
  - unique:
      config:
        severity: warn    # warn instead of error
  - not_null:
      config:
        severity: error   # fail the run (default)
```

### Error and warning thresholds

```yaml
data_tests:
  - unique:
      config:
        error_if: ">10"     # Error only if >10 failures
        warn_if: ">5"       # Warn if >5 failures
```

### Tags

```yaml
data_tests:
  - unique:
      config:
        tags: ['daily', 'critical']
```

### Where clause (filter test scope)

```yaml
data_tests:
  - not_null:
      config:
        where: "status != 'deleted'"
```

## Store Failures

Save failing records to a table for debugging.

### Per-test

```yaml
data_tests:
  - unique:
      config:
        store_failures: true
        store_failures_as: table    # or 'ephemeral'
```

### Project-wide

```yaml
# dbt_project.yml
data_tests:
  +store_failures: true
```

Failure records are stored in the `dbt_test__audit` schema by default.

### Command-line override

```bash
dbt test --store-failures
```

## Running Tests

```bash
# Run all tests
dbt test

# Run only data tests (exclude unit tests)
dbt test --select "test_type:data"

# Run tests on a specific model
dbt test --select customers

# Run tests on all sources
dbt test --select "source:*"

# Run tests on a specific source
dbt test --select source:jaffle_shop

# Run tests on a specific source table
dbt test --select source:jaffle_shop.orders

# Run tests with a tag
dbt test --select "tag:critical"

# Run tests as part of build
dbt build    # runs models, tests, seeds, snapshots together
```

## Testing Patterns

### Primary key test (every model should have this)

```yaml
models:
  - name: customers
    columns:
      - name: customer_id
        data_tests:
          - unique
          - not_null
```

### Composite primary key

```yaml
models:
  - name: order_items
    data_tests:
      - dbt_utils.unique_combination_of_columns:
          combination_of_columns:
            - order_id
            - item_id
```

### Testing an expression

```yaml
models:
  - name: orders
    data_tests:
      - unique:
          column_name: "(country_code || '-' || order_id)"
```

### Source data validation

```yaml
sources:
  - name: jaffle_shop
    tables:
      - name: orders
        columns:
          - name: id
            data_tests:
              - unique
              - not_null
          - name: status
            data_tests:
              - accepted_values:
                  values: ['placed', 'shipped', 'completed', 'returned']
```

### Row count validation

```sql
-- tests/assert_orders_count_reasonable.sql
select 1
from (
    select count(*) as row_count
    from {{ ref('orders') }}
) t
where row_count < 100    -- Alert if fewer than 100 orders
```

## Debugging Failed Tests

### Find the compiled SQL

```bash
# Compiled test SQL is in:
# target/compiled/<project>/tests/
# target/compiled/<project>/models/  (for inline tests)
```

### Inspect failures

```bash
# Store failures for inspection
dbt test --store-failures --select failing_test_name

# Query the failure table
-- select * from dbt_test__audit.<test_name>
```

### Common causes of test failures

| Test | Failure Cause | Fix |
|------|--------------|-----|
| `unique` | Duplicate records | Add dedup logic or fix upstream |
| `not_null` | Missing data | Add `coalesce()` or filter nulls |
| `accepted_values` | New/unexpected values | Update the accepted list or fix source |
| `relationships` | Orphaned foreign keys | Add left join or fix data pipeline |

### Custom test directory

```yaml
# dbt_project.yml
test-paths: ["my_tests"]
```

Generic tests go in `my_tests/generic/`, singular tests anywhere else in the directory.
