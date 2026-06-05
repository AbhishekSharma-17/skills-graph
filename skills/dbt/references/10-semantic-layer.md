# dbt — Semantic Layer & Metrics

> Source: https://docs.getdbt.com/docs/build/metrics-overview

## Table of Contents
- [Overview](#overview)
- [Semantic Models](#semantic-models)
- [Entities](#entities)
- [Measures](#measures)
- [Dimensions](#dimensions)
- [Metrics](#metrics)
- [Metric Types](#metric-types)
- [Metric Filters](#metric-filters)
- [MetricFlow](#metricflow)
- [Querying the Semantic Layer](#querying-the-semantic-layer)

## Overview

The dbt Semantic Layer enables centralized metric definitions in your dbt project. Instead of every BI tool calculating "revenue" differently, you define it once in dbt and all tools query the same definition.

**Components:**
- **Semantic Models** — Define entities, measures, and dimensions on top of dbt models
- **Metrics** — Business KPIs calculated from semantic model measures
- **MetricFlow** — Query engine that translates metric queries into SQL

## Semantic Models

Semantic models are the foundation. They define the semantic structure of a dbt model — what entities exist, what can be measured, and what dimensions are available for grouping.

```yaml
# models/marts/semantic/sem_orders.yml
semantic_models:
  - name: orders
    defaults:
      agg_time_dimension: order_date
    description: Order data with payment information
    model: ref('fct_orders')

    entities:
      - name: order_id
        type: primary
      - name: customer_id
        type: foreign

    measures:
      - name: order_total
        description: Total order amount in dollars
        agg: sum
        expr: amount

      - name: order_count
        description: Number of orders
        agg: count
        expr: order_id

      - name: average_order_value
        description: Average amount per order
        agg: average
        expr: amount

      - name: large_orders
        description: Orders over $100
        agg: sum
        expr: amount
        filter: |
          {{ Dimension('order_id__amount') }} > 100

    dimensions:
      - name: order_date
        type: time
        type_params:
          time_granularity: day

      - name: status
        type: categorical

      - name: is_completed
        type: categorical
        expr: "case when status = 'completed' then true else false end"
```

## Entities

Entities represent business objects (customers, orders, products). They define how semantic models join together.

```yaml
entities:
  - name: order_id
    type: primary        # Primary key of this semantic model

  - name: customer_id
    type: foreign        # Foreign key to another semantic model

  - name: product_id
    type: foreign
```

**Entity types:**
| Type | Description |
|------|-------------|
| `primary` | Primary key — unique per row |
| `foreign` | Foreign key — links to another entity |
| `unique` | Unique but not the primary key |
| `natural` | Business key (may not be unique per row) |

## Measures

Measures are aggregatable quantities — the "numbers" in your metrics.

```yaml
measures:
  - name: revenue
    description: Total revenue in dollars
    agg: sum
    expr: amount

  - name: order_count
    agg: count
    expr: order_id

  - name: customer_count
    agg: count_distinct
    expr: customer_id

  - name: max_order_value
    agg: max
    expr: amount
```

**Aggregation functions:**
| `agg` | SQL Equivalent |
|-------|---------------|
| `sum` | `SUM(expr)` |
| `count` | `COUNT(expr)` |
| `count_distinct` | `COUNT(DISTINCT expr)` |
| `average` | `AVG(expr)` |
| `min` | `MIN(expr)` |
| `max` | `MAX(expr)` |
| `median` | `MEDIAN(expr)` |
| `percentile` | `PERCENTILE_CONT(expr)` |

### Non-additive dimensions

For measures that shouldn't be summed across certain dimensions (e.g., account balances):

```yaml
measures:
  - name: account_balance
    agg: sum
    expr: balance
    non_additive_dimension:
      name: date
      window_choice: latest
```

## Dimensions

Dimensions are attributes for filtering and grouping metrics.

### Categorical dimensions

```yaml
dimensions:
  - name: status
    type: categorical

  - name: country
    type: categorical

  - name: is_first_order
    type: categorical
    expr: "case when order_number = 1 then true else false end"
```

### Time dimensions

```yaml
dimensions:
  - name: order_date
    type: time
    type_params:
      time_granularity: day    # day, week, month, quarter, year

  - name: created_at
    type: time
    type_params:
      time_granularity: day
```

## Metrics

Metrics are business KPIs built on semantic model measures.

```yaml
# models/marts/semantic/metrics.yml
metrics:
  - name: revenue
    description: Total revenue from completed orders
    type: simple
    label: Revenue
    type_params:
      measure: revenue     # References a measure defined in a semantic model
    filter: |
      {{ Dimension('order_id__status') }} = 'completed'
```

## Metric Types

### Simple metrics

Direct aggregation on a single measure.

```yaml
metrics:
  - name: total_revenue
    type: simple
    label: Total Revenue
    type_params:
      measure: revenue

  - name: total_orders
    type: simple
    label: Total Orders
    type_params:
      measure: order_count
```

### Derived metrics

Calculations using other metrics.

```yaml
metrics:
  - name: average_revenue_per_order
    type: derived
    label: Average Revenue per Order
    type_params:
      expr: total_revenue / total_orders
      metrics:
        - name: total_revenue
        - name: total_orders
```

### Ratio metrics

Calculate a ratio between two metrics (numerator/denominator).

```yaml
metrics:
  - name: conversion_rate
    type: ratio
    label: Conversion Rate
    type_params:
      numerator: conversions
      denominator: visits
```

### Cumulative metrics

Running totals over time.

```yaml
metrics:
  - name: cumulative_revenue
    type: cumulative
    label: Cumulative Revenue
    type_params:
      measure: revenue
      window: 7       # 7-day rolling window
      # Or use grain_to_date: month  (month-to-date)
```

### Conversion metrics

Track base event to conversion event for an entity.

```yaml
metrics:
  - name: visit_to_purchase
    type: conversion
    label: Visit to Purchase Rate
    type_params:
      entity: customer_id
      calculation: conversion_rate
      base_measure: visits
      conversion_measure: purchases
      window: 7    # Days to convert
```

## Metric Filters

Filter metrics using Jinja template syntax:

```yaml
metrics:
  - name: us_revenue
    type: simple
    type_params:
      measure: revenue
    filter: |
      {{ Dimension('order_id__country') }} = 'US'

  - name: recent_revenue
    type: simple
    type_params:
      measure: revenue
    filter: |
      {{ TimeDimension('order_id__order_date', 'day') }} >= '2024-01-01'
```

### Filter functions

| Function | Purpose | Example |
|----------|---------|---------|
| `Dimension()` | Filter by dimension | `{{ Dimension('entity__dim') }}` |
| `TimeDimension()` | Filter by time dimension | `{{ TimeDimension('entity__date', 'month') }}` |
| `Entity()` | Filter by entity | `{{ Entity('customer_id') }}` |

## MetricFlow

MetricFlow is the query engine that powers the dbt Semantic Layer. It translates semantic layer queries into optimized SQL.

### CLI usage (dbt Cloud)

```bash
# Query a metric
mf query --metrics revenue --group-by order_date__month

# Multiple metrics
mf query --metrics revenue,order_count --group-by status

# With filters
mf query --metrics revenue --group-by country --where "country = 'US'"

# Time range
mf query --metrics revenue --group-by order_date__month \
  --start-time 2024-01-01 --end-time 2024-12-31
```

## Querying the Semantic Layer

### From BI tools

The dbt Semantic Layer integrates with BI tools that query metrics via API:
- Tableau
- Hex
- Mode
- Google Sheets
- Excel
- Custom integrations via JDBC/GraphQL

### From dbt

```sql
-- In a dbt model, reference a metric (dbt Cloud)
select * from {{ metrics.calculate(
    metric('revenue'),
    grain='month',
    dimensions=['country']
) }}
```

### Best practices

- Define one semantic model per fact/dimension table
- Keep measure names descriptive and consistent
- Use `filter` on metrics, not on measures (unless the filter defines the measure itself)
- Set `defaults.agg_time_dimension` on every semantic model
- Start with simple metrics, add derived/ratio as business needs grow
