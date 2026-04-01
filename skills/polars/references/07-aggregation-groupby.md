# Polars — Aggregation & GroupBy

> Source: [docs.pola.rs](https://docs.pola.rs/user-guide/expressions/aggregation/)

## Table of Contents

- [Basic Aggregation](#basic-aggregation)
- [GroupBy](#groupby)
- [Aggregation Functions](#aggregation-functions)
- [Conditional Aggregation](#conditional-aggregation)
- [Window Functions](#window-functions)
- [Fold Operations](#fold-operations)
- [Common Patterns](#common-patterns)

## Basic Aggregation

Aggregate entire DataFrame without grouping:

```python
import polars as pl

df = pl.DataFrame({
    "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
    "dept": ["Eng", "Sales", "Eng", "Sales", "Eng"],
    "salary": [90000, 75000, 85000, 70000, 95000],
    "years": [5, 3, 7, 2, 10],
})

# Single aggregation
df.select(pl.col("salary").mean())

# Multiple aggregations
df.select(
    pl.col("salary").mean().alias("avg_salary"),
    pl.col("salary").median().alias("median_salary"),
    pl.col("salary").std().alias("std_salary"),
    pl.col("salary").min().alias("min_salary"),
    pl.col("salary").max().alias("max_salary"),
    pl.col("salary").sum().alias("total_salary"),
    pl.len().alias("count"),
)
```

## GroupBy

### Basic GroupBy

```python
# Group by single column
result = df.group_by("dept").agg(
    pl.col("salary").mean().alias("avg_salary"),
    pl.len().alias("headcount"),
)

# Group by multiple columns
result = df.group_by("dept", "level").agg(
    pl.col("salary").mean().alias("avg_salary"),
)
```

### Multiple Aggregations per Group

```python
result = df.group_by("dept").agg(
    # Count
    pl.len().alias("count"),

    # Numeric aggregations
    pl.col("salary").mean().alias("avg_salary"),
    pl.col("salary").sum().alias("total_salary"),
    pl.col("salary").max().alias("max_salary"),
    pl.col("salary").min().alias("min_salary"),

    # First/Last
    pl.col("name").first().alias("first_hire"),
    pl.col("name").last().alias("last_hire"),

    # Collect into list
    pl.col("name").alias("members"),  # List of names per group
)
```

### Sorting Within Groups

```python
result = df.group_by("dept").agg(
    # Sort names alphabetically within each group
    pl.col("name").sort().alias("sorted_names"),

    # Get highest paid per department
    pl.col("name").sort_by("salary", descending=True).first().alias("top_earner"),
)
```

### maintain_order

By default, group_by does not guarantee output order. Use `maintain_order=True` for deterministic order:

```python
result = df.group_by("dept", maintain_order=True).agg(
    pl.col("salary").mean()
)
```

## Aggregation Functions

| Function | Description |
|----------|-------------|
| `.count()` | Non-null count |
| `pl.len()` | Total rows (including nulls) |
| `.sum()` | Sum |
| `.mean()` | Arithmetic mean |
| `.median()` | Median |
| `.min()` | Minimum |
| `.max()` | Maximum |
| `.std()` | Standard deviation |
| `.var()` | Variance |
| `.first()` | First value |
| `.last()` | Last value |
| `.head(n)` | First n values (as list) |
| `.tail(n)` | Last n values (as list) |
| `.n_unique()` | Count of unique values |
| `.quantile(q)` | Quantile at q |
| `.arg_min()` | Index of minimum |
| `.arg_max()` | Index of maximum |
| `.implode()` | Collect all values into a list |

## Conditional Aggregation

### Filter Inside Aggregation

```python
result = df.group_by("dept").agg(
    # Count of high earners per department
    pl.col("salary").filter(pl.col("salary") > 80000).count().alias("high_earners"),

    # Average salary of senior employees
    pl.col("salary").filter(pl.col("years") >= 5).mean().alias("senior_avg"),

    # Sum only positive values
    pl.col("bonus").filter(pl.col("bonus") > 0).sum().alias("total_bonuses"),
)
```

### Boolean Sums

```python
result = df.group_by("dept").agg(
    # Count matching condition (True = 1)
    (pl.col("salary") > 80000).sum().alias("high_earner_count"),
    (pl.col("years") >= 5).sum().alias("senior_count"),
)
```

## Window Functions

Window functions compute aggregations **without collapsing rows** — each row keeps its original position.

### over() — Basic Window

```python
# Add department average salary to each row
df.with_columns(
    pl.col("salary").mean().over("dept").alias("dept_avg"),
)

# Rank within department
df.with_columns(
    pl.col("salary").rank("dense", descending=True).over("dept").alias("dept_rank"),
)

# Percentage of department total
df.with_columns(
    (pl.col("salary") / pl.col("salary").sum().over("dept") * 100)
    .round(1)
    .alias("pct_of_dept"),
)
```

### over() — Multiple Partition Columns

```python
df.with_columns(
    pl.col("salary").mean().over("dept", "level").alias("avg_by_dept_level"),
)
```

### Mapping Strategies

```python
# group_to_rows (default): maintains row order within groups
df.with_columns(
    pl.col("salary").rank("dense").over("dept", mapping_strategy="group_to_rows")
)

# explode: groups together, no position tracking (faster)
df.select(
    pl.col("name", "salary")
    .sort_by("salary", descending=True)
    .over("dept", mapping_strategy="explode")
)

# join: aggregates into lists, broadcasts to all group members
df.with_columns(
    pl.col("name").sort().over("dept", mapping_strategy="join").alias("all_dept_members")
)
```

### Window vs GroupBy

```python
# GroupBy: collapses rows (one row per group)
df.group_by("dept").agg(pl.col("salary").mean())
# Result: 2 rows (Eng, Sales)

# Window: preserves all rows
df.with_columns(pl.col("salary").mean().over("dept").alias("dept_avg"))
# Result: 5 rows (original data + new column)
```

## Fold Operations

Horizontal operations across columns:

```python
# Sum across columns (horizontal)
df.with_columns(
    pl.sum_horizontal("score_1", "score_2", "score_3").alias("total_score"),
)

# Mean across columns
df.with_columns(
    pl.mean_horizontal("q1", "q2", "q3", "q4").alias("quarterly_avg"),
)

# Min/Max across columns
df.with_columns(
    pl.min_horizontal("a", "b", "c").alias("row_min"),
    pl.max_horizontal("a", "b", "c").alias("row_max"),
)

# Custom fold
df.with_columns(
    pl.fold(
        acc=pl.lit(0),
        function=lambda acc, x: acc + x,
        exprs=pl.col("^score_.*$"),
    ).alias("total"),
)
```

## Common Patterns

### Top N per Group

```python
# Top 3 earners per department
result = (
    df.sort("salary", descending=True)
    .group_by("dept")
    .head(3)
)
```

### Running Totals

```python
df.with_columns(
    pl.col("revenue").cum_sum().alias("running_total"),
    pl.col("revenue").cum_sum().over("category").alias("category_running_total"),
)
```

### Percentage Change

```python
df.sort("date").with_columns(
    ((pl.col("price") - pl.col("price").shift(1)) / pl.col("price").shift(1) * 100)
    .alias("pct_change"),
)
```

### Pivot Table (Equivalent)

```python
result = (
    df.group_by("dept")
    .agg(
        pl.col("salary").filter(pl.col("level") == "junior").mean().alias("junior_avg"),
        pl.col("salary").filter(pl.col("level") == "senior").mean().alias("senior_avg"),
    )
)
```

## Related Topics

- **Expressions** → `02-expressions.md`
- **Time Series** → `10-time-series.md`
- **Filtering & Selection** → `06-filtering-selection.md`
