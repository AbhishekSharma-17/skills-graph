# Grafana — Data Transformations

> Source: [grafana.com/docs/grafana/latest/panels-visualizations/query-transform-data/transform-data](https://grafana.com/docs/grafana/latest/panels-visualizations/query-transform-data/transform-data/) — Grafana 13.0

## Table of Contents

- [Core Transformations](#core-transformations) — Reduce, Merge, Join, Filter, Group By, Sort, Limit
- [Field Transformations](#add-field-from-calculation) — Calculate, Convert, Organize, Extract
- [Reshaping](#series-to-rows) — Series to Rows, Rows to Fields, Concatenate, Histogram
- [Transformation Chaining](#transformation-chaining) — Ordering, debugging, reordering
- [Common Patterns](#common-patterns) — Multi-source tables, Top-N, time comparisons
- [Common Pitfalls](#common-pitfalls)

## Overview

Transformations process query results before visualization. They can join data from multiple queries, filter rows, calculate new fields, rename columns, and reshape data. Transformations are chained — each processes the output of the previous one.

## When to Use Transformations

- Combine results from multiple data sources into a single table
- Calculate derived fields (percentages, rates, differences)
- Filter out irrelevant data
- Rename or reorder fields for display
- Convert field types (string to number, time format)
- Aggregate or group data for summary views

## Adding Transformations

1. Edit a panel → **Transform** tab
2. Click **Add transformation**
3. Select the transformation type
4. Configure options
5. Add more transformations to chain them

## Core Transformations

### Reduce

Collapse each time series into a single value:

```
Mode: Series to rows
Calculations: Last, Mean, Min, Max, Total, Count
```

Input:
```
Time       | CPU (server-1) | CPU (server-2)
10:00      | 45             | 62
10:01      | 48             | 58
10:02      | 52             | 65
```

Output (with Last, Max):
```
Field         | Last  | Max
CPU (server-1)| 52    | 52
CPU (server-2)| 65    | 65
```

### Merge

Combine multiple result sets into a single table by joining on common fields:

```
Query A → {time, cpu_usage}
Query B → {time, memory_usage}
Result  → {time, cpu_usage, memory_usage}
```

### Join by Field

Combine two queries using a shared field (like SQL JOIN):

```
Mode: Outer join (include all rows) / Inner join (matching rows only)
Field: time (or any shared field)
```

### Filter Data by Values

Include or exclude rows based on field values:

```
Filter type: Include | Exclude
Condition: Greater than, Less than, Equal, Regex, Is Null, Is Not Null
Match: Any condition | All conditions
```

Example: Only show rows where `status >= 500`:
```
Field: status
Condition: Greater than or equal
Value: 500
```

### Filter by Name

Show or hide specific fields (columns):

```
Select fields to include/exclude:
☑ time
☑ value
☐ __name__
☐ job
```

Use regex to match field names: `/^cpu_/` (all fields starting with `cpu_`).

### Organize Fields

Rename, reorder, and hide fields:

```
Original Name → Display Name    | Visible
time          → Timestamp       | ☑
value         → CPU Usage (%)   | ☑
instance      → Server          | ☑
__name__      → (hidden)        | ☐
job           → (hidden)        | ☐
```

### Group By

Aggregate rows with matching label values:

```
Group by: service, method
Calculate:
  - duration: Mean
  - requests: Sum
  - errors: Sum
```

Input:
```
service | method | duration | requests
api     | GET    | 120      | 500
api     | GET    | 130      | 480
api     | POST   | 200      | 100
```

Output:
```
service | method | duration (mean) | requests (sum)
api     | GET    | 125             | 980
api     | POST   | 200             | 100
```

### Sort By

Sort rows by one or more fields:

```
Field: value
Order: Descending
```

### Limit

Restrict the number of rows displayed:

```
Limit: 10   # Show top/bottom 10 rows (after sorting)
```

### Add Field from Calculation

Create new fields using math on existing fields:

```
Mode: Binary operation
Field 1: errors
Operator: /
Field 2: total_requests
Alias: error_rate
```

Or use **Reduce row** mode:
```
Mode: Reduce row
Calculation: Total
```

### Convert Field Type

Change field data types:

```
Field: timestamp
Target type: Time
Date format: YYYY-MM-DD HH:mm:ss
```

Supported conversions: Number → String, String → Number, String → Time, Time → String, Number → Boolean.

### Concatenate Fields

Merge all query result frames into a single frame:

```
Before: Query A returns frame 1, Query B returns frame 2
After: Single frame with all rows from both queries
```

### Series to Rows

Convert multiple series (wide format) into a long/tall format:

```
Before (wide):
Time  | cpu_server1 | cpu_server2
10:00 | 45          | 62

After (long):
Time  | Metric      | Value
10:00 | cpu_server1 | 45
10:00 | cpu_server2 | 62
```

### Rows to Fields

Convert rows into field headers (pivot):

```
Before:
Name    | Value
cpu     | 85
memory  | 72
disk    | 45

After:
cpu | memory | disk
85  | 72     | 45
```

### Extract Fields

Parse structured values from a string field:

```
Source: json_field
Format: JSON | Key=Value | Auto
```

### Create Heatmap

Convert time series data into heatmap buckets for heatmap visualization.

### Histogram

Calculate histogram buckets from raw values:

```
Bucket size: 10
Bucket offset: 0
Combine series: true/false
Fill missing: true/false
```

### Regression Analysis

Fit a line to time series data:

```
Type: Linear
```

Adds a trend line alongside the original data.

## Transformation Chaining

Transformations execute in order. Each receives the output of the previous:

```
1. Join by field (time)     → Combine Prometheus + PostgreSQL results
2. Add field from calc      → Calculate error_rate = errors / total
3. Filter by values         → Only rows where error_rate > 0.05
4. Sort by                  → Sort by error_rate descending
5. Limit                    → Top 10 results
6. Organize fields          → Rename, reorder, hide internal fields
```

### Reordering

Drag transformations up/down to change execution order. The order can significantly affect results.

### Debugging

Click the **Debug** icon on each transformation to see its input and output data frames.

## Transformation Expressions

For complex calculations, use the expression editor:

```
// Mathematical expressions
${errors} / ${total_requests} * 100

// Conditional
${status} >= 500 ? 1 : 0

// String concatenation (in organize fields)
${method} ${path}
```

## Common Patterns

### Multi-Source Dashboard Table

```
Query A: Prometheus → request rate by service
Query B: PostgreSQL → service metadata (owner, tier)

Transform 1: Reduce (A) → Last value per series
Transform 2: Join by field (service) → Merge A + B
Transform 3: Organize fields → Rename columns, set order
```

### Top-N With Percentage

```
Query: sum(rate(http_requests_total[5m])) by (path)

Transform 1: Reduce → Last value
Transform 2: Sort by value → Descending
Transform 3: Limit → 10
Transform 4: Add field from calc → percentage = value / total * 100
```

### Time Series Comparison

```
Query A: rate(http_requests_total[5m])                    # Current
Query B: rate(http_requests_total[5m] offset 1d)          # Yesterday

Transform 1: Join by field (time)
Transform 2: Add field from calc → change = A - B
Transform 3: Organize fields → Rename to meaningful names
```

## Common Pitfalls

- **Transform order matters** — Filtering before joining is different from joining before filtering
- **Missing join field** — Join by field requires an exact field name match; check field names in debug view
- **Wide vs long format** — Some visualizations (bar chart, pie) need long format; use "Series to rows" to convert
- **Performance** — Transformations run in the browser; for large datasets, use server-side aggregation (recording rules, SQL views)
- **Lost labels** — Some transformations (Reduce, Group by) may drop labels; check output in debug mode
- **Overusing transforms** — If a transform chain gets complex, consider using a recording rule or SQL view instead
