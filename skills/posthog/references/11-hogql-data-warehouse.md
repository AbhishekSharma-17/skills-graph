# PostHog — HogQL & Data Warehouse

> Source: [posthog.com/docs/sql](https://posthog.com/docs/sql) | [posthog.com/docs/data-warehouse](https://posthog.com/docs/data-warehouse)

## Table of Contents

- [HogQL Overview](#hogql-overview)
- [SQL Editor](#sql-editor)
- [Core Tables](#core-tables)
- [Query Syntax](#query-syntax)
- [Property Access](#property-access)
- [Joins](#joins)
- [Aggregations & Functions](#aggregations--functions)
- [SQL Insights](#sql-insights)
- [Data Warehouse](#data-warehouse)
- [Querying External Sources](#querying-external-sources)
- [Views](#views)
- [Common Queries](#common-queries)
- [Common Pitfalls](#common-pitfalls)

## HogQL Overview

HogQL is PostHog's SQL interface, a translation layer over ClickHouse SQL. It provides direct access to all PostHog data — events, persons, groups, sessions — with familiar SQL syntax plus PostHog-specific helpers.

Key features:
- **Full SQL** — SELECT, JOIN, subqueries, CTEs, window functions
- **Property shorthand** — `properties.$browser` instead of complex JSON extraction
- **Auto-joins** — referencing `events.person.properties` auto-joins the persons table
- **Data warehouse access** — query external sources alongside PostHog data
- **SQL insights** — save queries as dashboard visualizations

## SQL Editor

Access via the SQL Editor tab in PostHog:

```sql
-- Basic query
SELECT
  event,
  count() as event_count,
  uniq(distinct_id) as unique_users
FROM events
WHERE timestamp > now() - interval 7 day
GROUP BY event
ORDER BY event_count DESC
LIMIT 20
```

### Editor Features

- **Autocomplete** — table names, column names, functions
- **Query history** — access previous queries
- **Save as insight** — add to dashboards
- **Export results** — CSV download
- **Explain** — view the query execution plan

## Core Tables

| Table | Description | Key Columns |
|-------|-------------|-------------|
| `events` | All captured events | `event`, `distinct_id`, `properties`, `timestamp` |
| `persons` | Person profiles | `id`, `properties`, `created_at` |
| `groups` | Group entities | `group_type_index`, `group_key`, `group_properties` |
| `sessions` | Session data | `session_id`, `distinct_id`, `duration`, `entry_url` |
| `cohort_people` | Cohort memberships | `cohort_id`, `person_id` |
| `session_replay_events` | Replay metadata | `session_id`, `distinct_id`, `first_url` |

### Events Table Columns

```sql
SELECT
  uuid,                    -- unique event ID
  event,                   -- event name
  distinct_id,             -- user identifier
  properties,              -- event properties (JSON)
  timestamp,               -- when event occurred
  created_at,              -- when event was ingested
  person_id,               -- linked person ID
  person_properties,       -- person properties at event time
  elements_chain           -- autocapture DOM element chain
FROM events
LIMIT 1
```

## Query Syntax

### SELECT

```sql
-- Standard columns
SELECT event, distinct_id, timestamp FROM events

-- Aliases
SELECT event AS event_name, count() AS total FROM events GROUP BY event_name

-- Expressions
SELECT
  event,
  dateDiff('minute', timestamp, now()) AS minutes_ago
FROM events
```

### WHERE

```sql
-- String comparison
WHERE event = 'purchase_completed'

-- Numeric comparison
WHERE properties.amount > 50

-- Date range
WHERE timestamp >= '2026-04-01' AND timestamp < '2026-05-01'

-- Relative dates
WHERE timestamp > now() - interval 30 day

-- NULL checks
WHERE properties.referrer IS NOT NULL

-- LIKE
WHERE properties.$current_url LIKE '%/pricing%'

-- IN
WHERE event IN ('signup_completed', 'purchase_completed', 'upgrade_completed')
```

### GROUP BY & ORDER BY

```sql
SELECT
  properties.$browser AS browser,
  count() AS events,
  uniq(distinct_id) AS users
FROM events
WHERE timestamp > now() - interval 7 day
GROUP BY browser
ORDER BY users DESC
LIMIT 10
```

### HAVING

```sql
SELECT
  distinct_id,
  count() AS event_count
FROM events
WHERE timestamp > now() - interval 30 day
GROUP BY distinct_id
HAVING event_count > 100
ORDER BY event_count DESC
```

## Property Access

HogQL provides shorthand for accessing JSON properties:

```sql
-- Event properties
properties.$browser                    -- 'Chrome'
properties.$os                         -- 'Mac OS X'
properties.amount                      -- 49.99
properties.$current_url                -- 'https://...'

-- Person properties (auto-joins persons table)
person.properties.email                -- 'jane@example.com'
person.properties.plan                 -- 'enterprise'

-- Nested properties
properties.metadata.source             -- nested JSON access

-- Type casting
toFloat(properties.amount)             -- cast string to float
toInt(properties.quantity)             -- cast to integer
```

### Property Type Handling

Properties are stored as strings in ClickHouse. Cast when needed:

```sql
SELECT
  avg(toFloat(properties.amount)) AS avg_amount,
  max(toInt(properties.quantity)) AS max_quantity
FROM events
WHERE event = 'purchase_completed'
```

## Joins

### Explicit Joins

```sql
-- Join events with persons
SELECT
  e.event,
  e.distinct_id,
  p.properties.email AS email
FROM events e
JOIN persons p ON e.person_id = p.id
WHERE e.event = 'purchase_completed'
```

### Auto-Joins

HogQL automatically joins when you reference related tables:

```sql
-- This auto-joins the persons table
SELECT
  event,
  distinct_id,
  person.properties.email    -- auto-join!
FROM events
WHERE event = 'purchase_completed'
```

### Join with External Data

```sql
-- Join PostHog events with synced Stripe data
SELECT
  e.distinct_id,
  e.timestamp,
  s.amount,
  s.currency
FROM events e
JOIN stripe_charges s ON e.distinct_id = s.customer_id
WHERE e.event = 'checkout_started'
```

## Aggregations & Functions

### Aggregate Functions

| Function | Description |
|----------|-------------|
| `count()` | Count of rows |
| `uniq(col)` | Approximate unique count |
| `uniqExact(col)` | Exact unique count (slower) |
| `sum(col)` | Sum |
| `avg(col)` | Average |
| `min(col)` / `max(col)` | Min/Max |
| `median(col)` | Median |
| `quantile(0.95)(col)` | Percentile |
| `groupArray(col)` | Collect into array |
| `argMax(a, b)` | Value of `a` at max `b` |

### Date/Time Functions

```sql
-- Date truncation
toStartOfDay(timestamp)
toStartOfWeek(timestamp)
toStartOfMonth(timestamp)

-- Date arithmetic
timestamp + interval 7 day
dateDiff('day', created_at, now())

-- Formatting
formatDateTime(timestamp, '%Y-%m-%d')

-- Current time
now()
today()
```

### String Functions

```sql
-- Matching
LIKE '%pattern%'
match(col, 'regex_pattern')

-- Extraction
extract(properties.$current_url, '/([^/]+)$')
splitByChar('/', properties.$pathname)

-- Transformation
lower(properties.email)
trim(properties.name)
```

### Window Functions

```sql
-- Row number
SELECT
  distinct_id,
  event,
  timestamp,
  row_number() OVER (PARTITION BY distinct_id ORDER BY timestamp) AS event_order
FROM events
WHERE timestamp > now() - interval 7 day
```

## SQL Insights

Save HogQL queries as visualizations on dashboards:

```sql
-- This becomes a line chart on a dashboard
SELECT
  toStartOfDay(timestamp) AS day,
  uniq(distinct_id) AS daily_active_users
FROM events
WHERE timestamp > now() - interval 30 day
GROUP BY day
ORDER BY day
```

### Visualization Types

After writing a query, choose how to display results:
- **Line chart** — time series data
- **Bar chart** — categorical comparisons
- **Number** — single aggregate value
- **Table** — raw data view

## Data Warehouse

The Data Warehouse lets you query external data sources directly from PostHog:

### Adding a Source

```
1. Data Warehouse → Sources → New Source
2. Select source type (Postgres, S3, Stripe, etc.)
3. Enter connection details
4. Select tables to sync
5. Configure sync schedule
```

### Querying Warehouse Tables

Once synced, tables appear in the SQL editor:

```sql
-- Query external Postgres table
SELECT * FROM postgres_users LIMIT 10

-- Join with PostHog events
SELECT
  e.event,
  e.distinct_id,
  u.name,
  u.plan
FROM events e
JOIN postgres_users u ON e.distinct_id = u.user_id
WHERE e.event = 'feature_used'
```

## Views

Create reusable SQL views:

```sql
-- Create a view
CREATE VIEW active_users AS
SELECT
  distinct_id,
  count() AS event_count,
  max(timestamp) AS last_active
FROM events
WHERE timestamp > now() - interval 30 day
GROUP BY distinct_id
HAVING event_count > 10
```

Views can be used in other queries:

```sql
SELECT * FROM active_users WHERE event_count > 100
```

## Common Queries

### Daily Active Users (DAU)

```sql
SELECT
  toStartOfDay(timestamp) AS day,
  uniq(distinct_id) AS dau
FROM events
WHERE timestamp > now() - interval 30 day
GROUP BY day
ORDER BY day
```

### Event Frequency Distribution

```sql
SELECT
  event_count,
  count() AS num_users
FROM (
  SELECT distinct_id, count() AS event_count
  FROM events
  WHERE timestamp > now() - interval 7 day
  GROUP BY distinct_id
)
GROUP BY event_count
ORDER BY event_count
```

### Revenue by Day

```sql
SELECT
  toStartOfDay(timestamp) AS day,
  sum(toFloat(properties.amount)) AS revenue,
  uniq(distinct_id) AS paying_users
FROM events
WHERE event = 'purchase_completed'
  AND timestamp > now() - interval 30 day
GROUP BY day
ORDER BY day
```

### User Journey (First N Events)

```sql
SELECT
  distinct_id,
  groupArray(event) AS event_sequence
FROM (
  SELECT distinct_id, event, timestamp,
    row_number() OVER (PARTITION BY distinct_id ORDER BY timestamp) AS rn
  FROM events
  WHERE timestamp > now() - interval 7 day
)
WHERE rn <= 10
GROUP BY distinct_id
LIMIT 100
```

### Feature Flag Evaluation Counts

```sql
SELECT
  properties.$feature_flag AS flag_name,
  properties.$feature_flag_response AS variant,
  count() AS evaluations,
  uniq(distinct_id) AS unique_users
FROM events
WHERE event = '$feature_flag_called'
  AND timestamp > now() - interval 7 day
GROUP BY flag_name, variant
ORDER BY evaluations DESC
```

## Common Pitfalls

1. **Not casting property types** — properties are strings; use `toFloat()`, `toInt()` for math
2. **Using `uniqExact` unnecessarily** — `uniq()` is much faster and accurate enough for most cases
3. **Missing date filters** — queries without date bounds scan all data; always filter by `timestamp`
4. **Joining large tables without filters** — apply WHERE clauses before JOINs for performance
5. **Forgetting ClickHouse quirks** — `count()` not `count(*)`, `uniq()` not `COUNT(DISTINCT)`
6. **Not using views for common queries** — create views for frequently used subqueries
