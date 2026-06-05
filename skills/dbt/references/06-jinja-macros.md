# dbt — Jinja & Macros

> Source: https://docs.getdbt.com/docs/build/jinja-macros

## Table of Contents
- [Jinja in dbt](#jinja-in-dbt)
- [Jinja Syntax](#jinja-syntax)
- [Control Structures](#control-structures)
- [Variables](#variables)
- [Macros](#macros)
- [Built-in dbt Functions](#built-in-dbt-functions)
- [Whitespace Control](#whitespace-control)
- [Documenting Macros](#documenting-macros)
- [Best Practices](#best-practices)

## Jinja in dbt

Jinja is a templating language that turns dbt SQL files into a programming environment. It enables dynamic SQL generation, control flow, reusable code, and environment-aware queries.

Jinja is used in:
- Models (SQL files)
- Tests
- Macros
- Hooks
- Analyses
- Snapshot configurations

## Jinja Syntax

### Three delimiter types

**Expressions `{{ ... }}`** — Output values to the rendered SQL.
```sql
select * from {{ ref('customers') }}
-- Outputs: select * from analytics.customers
```

**Statements `{% ... %}`** — Control flow, do NOT output text.
```sql
{% set my_list = ['a', 'b', 'c'] %}
{% for item in my_list %}
    -- processing {{ item }}
{% endfor %}
```

**Comments `{# ... #}`** — Jinja comments (not rendered to SQL).
```sql
{# This comment won't appear in compiled SQL #}
select * from {{ ref('orders') }}
```

## Control Structures

### For loops

```sql
{% set payment_methods = ["bank_transfer", "credit_card", "gift_card"] %}

select
    order_id,
    {% for method in payment_methods %}
    sum(case when payment_method = '{{ method }}' then amount else 0 end)
        as {{ method }}_amount
    {% if not loop.last %},{% endif %}
    {% endfor %}
from {{ ref('stg_payments') }}
group by 1
```

**Compiled output:**
```sql
select
    order_id,
    sum(case when payment_method = 'bank_transfer' then amount else 0 end)
        as bank_transfer_amount,
    sum(case when payment_method = 'credit_card' then amount else 0 end)
        as credit_card_amount,
    sum(case when payment_method = 'gift_card' then amount else 0 end)
        as gift_card_amount
from analytics.stg_payments
group by 1
```

### Loop variables

| Variable | Description |
|----------|-------------|
| `loop.index` | Current iteration (1-indexed) |
| `loop.index0` | Current iteration (0-indexed) |
| `loop.first` | True on first iteration |
| `loop.last` | True on last iteration |
| `loop.length` | Total number of items |

### If/elif/else

```sql
select
    order_id,
    {% if target.name == 'prod' %}
        order_date
    {% else %}
        current_date as order_date   -- Use current date in dev
    {% endif %}
from {{ ref('stg_orders') }}
```

### Conditional model logic

```sql
{{ config(materialized='incremental') }}

select * from {{ ref('stg_events') }}

{% if is_incremental() %}
where event_time > (select max(event_time) from {{ this }})
{% endif %}
```

## Variables

### set — Local variables

```sql
{% set payment_methods = ["bank_transfer", "credit_card", "gift_card"] %}
{% set schema_name = "analytics" %}
{% set max_date_query %}
    select max(order_date) from {{ ref('orders') }}
{% endset %}
```

### var() — Project variables

Defined in `dbt_project.yml`:
```yaml
vars:
  payment_methods: ["bank_transfer", "credit_card", "gift_card"]
  start_date: "2020-01-01"
```

Used in models:
```sql
{% for method in var('payment_methods') %}
    ...
{% endfor %}

where order_date >= '{{ var("start_date") }}'
```

Override at runtime:
```bash
dbt run --vars '{"start_date": "2024-01-01"}'
```

### env_var() — Environment variables

```sql
{% if env_var('DBT_ENV') == 'production' %}
    select * from prod_schema.orders
{% else %}
    select * from {{ ref('stg_orders') }}
{% endif %}
```

With default value:
```sql
{{ env_var('MY_VAR', 'default_value') }}
```

## Macros

Reusable Jinja code blocks — like functions in programming languages.

### Defining a macro

```sql
-- macros/cents_to_dollars.sql
{% macro cents_to_dollars(column_name, scale=2) %}
    ({{ column_name }} / 100)::numeric(16, {{ scale }})
{% endmacro %}
```

### Using a macro

```sql
-- models/stg_payments.sql
select
    id as payment_id,
    {{ cents_to_dollars('amount') }} as amount_usd,
    {{ cents_to_dollars('tax', scale=4) }} as tax_usd
from {{ source('stripe', 'payments') }}
```

**Compiled:**
```sql
select
    id as payment_id,
    (amount / 100)::numeric(16, 2) as amount_usd,
    (tax / 100)::numeric(16, 4) as tax_usd
from raw.stripe.payments
```

### Macro with SQL execution

```sql
-- macros/get_payment_methods.sql
{% macro get_payment_methods() %}
    {% set query %}
        select distinct payment_method from {{ ref('stg_payments') }}
    {% endset %}

    {% set results = run_query(query) %}

    {% if execute %}
        {% set methods = results.columns[0].values() %}
        {{ return(methods) }}
    {% else %}
        {{ return([]) }}
    {% endif %}
{% endmacro %}
```

```sql
-- Usage in a model
{% set methods = get_payment_methods() %}
select
    order_id,
    {% for method in methods %}
    sum(case when payment_method = '{{ method }}' then amount end) as {{ method }}_amount
    {% if not loop.last %},{% endif %}
    {% endfor %}
from {{ ref('stg_payments') }}
group by 1
```

### Using package macros

```sql
-- After installing dbt-utils package
select
    {{ dbt_utils.generate_surrogate_key(['user_id', 'event_date']) }} as event_key,
    {{ dbt_utils.star(ref('stg_events'), except=['_loaded_at']) }}
from {{ ref('stg_events') }}
```

### Macro argument quoting

```sql
-- CORRECT: String arguments must be quoted
{{ cents_to_dollars('amount') }}

-- WRONG: Without quotes, Jinja looks for a variable named 'amount'
{{ cents_to_dollars(amount) }}
```

## Built-in dbt Functions

| Function | Purpose | Example |
|----------|---------|---------|
| `ref()` | Reference a model | `{{ ref('customers') }}` |
| `source()` | Reference a source table | `{{ source('jaffle_shop', 'orders') }}` |
| `config()` | Set model configuration | `{{ config(materialized='table') }}` |
| `var()` | Access project variables | `{{ var('start_date') }}` |
| `env_var()` | Access environment variables | `{{ env_var('DB_HOST') }}` |
| `target` | Current target info | `{{ target.name }}`, `{{ target.schema }}` |
| `this` | Current model's relation | `{{ this }}` (in incremental) |
| `log()` | Print to CLI output | `{{ log('message', info=true) }}` |
| `run_query()` | Execute SQL and get results | `{% set r = run_query(sql) %}` |
| `return()` | Return value from macro | `{{ return(value) }}` |
| `execute` | True during execution | `{% if execute %}` |
| `exceptions.raise_compiler_error()` | Raise an error | Abort compilation |

### target context

```sql
{% if target.name == 'prod' %}
    {{ config(materialized='table') }}
{% else %}
    {{ config(materialized='view') }}
{% endif %}

-- target.name, target.schema, target.database, target.type
```

## Whitespace Control

Remove unwanted whitespace with minus signs:

```sql
{%- set items = ['a', 'b', 'c'] -%}
{%- for item in items -%}
    {{ item }}
{%- endfor -%}
```

- `{%-` strips whitespace before
- `-%}` strips whitespace after
- Works on all delimiter types: `{{- ... -}}`, `{%- ... -%}`

## Documenting Macros

```yaml
# macros/properties.yml
macros:
  - name: cents_to_dollars
    description: Converts cent-denominated amounts to dollars
    arguments:
      - name: column_name
        type: column
        description: The column containing cent values
      - name: scale
        type: integer
        description: Decimal places (default 2)
```

## Best Practices

**Favor readability over DRY-ness.** Repeating SQL is fine if it's clearer than a macro. Don't make every pattern a macro.

**Set variables at the top of models:**
```sql
-- Good
{% set methods = ["bank_transfer", "credit_card"] %}
select
    {% for m in methods %} ... {% endfor %}
```

**Use package macros before writing your own.** Check [dbt-utils](https://hub.getdbt.com/dbt-labs/dbt_utils) first.

**Debug with compile:**
```bash
dbt compile --select my_model
# Check target/compiled/<project>/models/my_model.sql
```

**Use `log()` for debugging:**
```sql
{% set my_var = "test" %}
{{ log("my_var = " ~ my_var, info=true) }}
```

**Avoid deeply nested Jinja.** If the logic is complex, consider a Python model or pre-processing step.
