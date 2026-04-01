# Polars — Expressions

> Source: [docs.pola.rs](https://docs.pola.rs/user-guide/expressions/)

## Table of Contents

- [What Are Expressions?](#what-are-expressions)
- [Column References](#column-references)
- [Literal Values](#literal-values)
- [Expression Contexts](#expression-contexts)
- [Arithmetic & Comparison](#arithmetic--comparison)
- [Boolean Logic](#boolean-logic)
- [Conditional Expressions](#conditional-expressions)
- [Expression Expansion](#expression-expansion)
- [Casting](#casting)
- [User-Defined Functions](#user-defined-functions)
- [Common Pitfalls](#common-pitfalls)

## What Are Expressions?

Expressions are the core building blocks of Polars. An expression describes a **computation on columns** that produces new columns. Expressions are:

- **Lazy** — they describe what to do, not when
- **Composable** — chain operations together
- **Parallel** — multiple expressions in a context execute concurrently
- **Optimizable** — the query optimizer can rewrite them

```python
import polars as pl

# These are all expressions:
pl.col("name")                          # Column reference
pl.col("price") * pl.col("quantity")    # Arithmetic
pl.col("score").mean()                  # Aggregation
pl.col("text").str.to_uppercase()       # String transform
pl.lit(42)                              # Literal value
pl.col("date").dt.year()                # Temporal extraction
```

## Column References

### pl.col() — Reference Columns

```python
# Single column
pl.col("name")

# Multiple columns
pl.col("name", "age", "salary")

# By data type
pl.col(pl.Int64)          # All Int64 columns
pl.col(pl.Float64)        # All Float64 columns
pl.col(pl.String)         # All String columns

# By regex pattern
pl.col("^score_.*$")     # Columns matching regex

# All columns
pl.all()                  # Every column
pl.col("*")               # Same as pl.all()

# Exclude columns
pl.all().exclude("id")
pl.all().exclude(pl.String)
```

### pl.first(), pl.last()

```python
pl.first()    # First column
pl.last()     # Last column
```

## Literal Values

```python
# Scalar literals
pl.lit(42)                    # Integer
pl.lit(3.14)                  # Float
pl.lit("hello")               # String
pl.lit(True)                  # Boolean
pl.lit(None)                  # Null

# Use in expressions
df.with_columns(
    pl.lit("active").alias("status"),
    (pl.col("price") + pl.lit(10)).alias("adjusted_price"),
)
```

## Expression Contexts

Expressions run inside **contexts** that determine their behavior:

### select — Choose and Transform Columns

```python
# Returns only the specified columns
result = df.select(
    pl.col("name"),
    pl.col("salary") / 1000,
    (pl.col("age") * 365).alias("age_days"),
)
```

### with_columns — Add/Modify Columns

```python
# Keeps all existing columns and adds/replaces
result = df.with_columns(
    (pl.col("salary") * 1.1).alias("raised_salary"),
    pl.col("name").str.to_uppercase().alias("upper_name"),
)

# Overwrite existing column (same name, no alias)
result = df.with_columns(
    pl.col("salary") * 1.1,  # Overwrites "salary"
)
```

### filter — Subset Rows

```python
# Boolean expression determines which rows to keep
result = df.filter(pl.col("age") > 30)

# Multiple conditions
result = df.filter(
    (pl.col("age") > 25) & (pl.col("salary") > 80000)
)
```

### group_by + agg — Aggregate by Groups

```python
result = df.group_by("department").agg(
    pl.col("salary").mean().alias("avg_salary"),
    pl.col("name").count().alias("headcount"),
    pl.col("age").max().alias("oldest"),
)
```

## Arithmetic & Comparison

### Arithmetic

```python
pl.col("a") + pl.col("b")      # Addition
pl.col("a") - pl.col("b")      # Subtraction
pl.col("a") * pl.col("b")      # Multiplication
pl.col("a") / pl.col("b")      # Division (float)
pl.col("a") // pl.col("b")     # Floor division
pl.col("a") % pl.col("b")      # Modulo
pl.col("a") ** 2                # Power

# Chained
(pl.col("price") * pl.col("qty") * (1 - pl.col("discount")))
```

### Comparison

```python
pl.col("age") > 30             # Greater than
pl.col("age") >= 30            # Greater or equal
pl.col("age") < 30             # Less than
pl.col("age") <= 30            # Less or equal
pl.col("age") == 30            # Equal
pl.col("age") != 30            # Not equal

# Range check
pl.col("age").is_between(25, 35)

# Membership check
pl.col("city").is_in(["NYC", "LA", "Chicago"])
```

## Boolean Logic

```python
# AND
(pl.col("age") > 25) & (pl.col("salary") > 80000)

# OR
(pl.col("city") == "NYC") | (pl.col("city") == "LA")

# NOT
~(pl.col("active"))
pl.col("active").not_()

# Combined
(
    (pl.col("age").is_between(25, 40))
    & (pl.col("salary") > 70000)
    & ~(pl.col("city") == "Remote")
)
```

**Important:** Always wrap individual conditions in parentheses due to Python operator precedence.

## Conditional Expressions

### when/then/otherwise

```python
# Simple if/else
df.with_columns(
    pl.when(pl.col("age") >= 30)
    .then(pl.lit("senior"))
    .otherwise(pl.lit("junior"))
    .alias("level")
)

# Chained conditions (if/elif/else)
df.with_columns(
    pl.when(pl.col("score") >= 90)
    .then(pl.lit("A"))
    .when(pl.col("score") >= 80)
    .then(pl.lit("B"))
    .when(pl.col("score") >= 70)
    .then(pl.lit("C"))
    .otherwise(pl.lit("F"))
    .alias("grade")
)

# With expressions in then/otherwise
df.with_columns(
    pl.when(pl.col("discount") > 0)
    .then(pl.col("price") * (1 - pl.col("discount")))
    .otherwise(pl.col("price"))
    .alias("final_price")
)
```

## Expression Expansion

When an expression refers to multiple columns, it **expands** into parallel operations:

```python
# Applies to ALL numeric columns
df.select(pl.col(pl.NUMERIC_DTYPES).mean())

# Apply same transform to multiple columns
df.with_columns(
    pl.col("col_a", "col_b", "col_c").fill_null(0)
)

# Using selectors
import polars.selectors as cs
df.select(cs.numeric().round(2))
```

## Casting

```python
# Cast to specific type
pl.col("price").cast(pl.Float32)
pl.col("count").cast(pl.UInt16)
pl.col("id").cast(pl.String)

# Strict vs non-strict
pl.col("value").cast(pl.Int32, strict=True)    # Raises on overflow
pl.col("value").cast(pl.Int32, strict=False)   # Returns null on failure

# String to numeric
pl.col("amount").str.replace("$", "").cast(pl.Float64)
```

## User-Defined Functions

Use only when Polars expressions can't express the logic — UDFs break parallelism.

### map_elements — Row-by-Row (Slow)

```python
df.with_columns(
    pl.col("name").map_elements(
        lambda x: x.split()[0],
        return_dtype=pl.String,
    ).alias("first_name")
)
```

### map_batches — Whole-Column (Faster)

```python
import numpy as np

df.with_columns(
    pl.col("values").map_batches(
        lambda s: pl.Series(np.log1p(s.to_numpy())),
        return_dtype=pl.Float64,
    ).alias("log_values")
)
```

**Prefer expressions over UDFs.** Example — instead of:
```python
# BAD: UDF for string operation
pl.col("name").map_elements(lambda x: x.upper())

# GOOD: Native expression
pl.col("name").str.to_uppercase()
```

## Common Pitfalls

1. **Missing parentheses in boolean logic** — `pl.col("a") > 5 & pl.col("b") < 10` is wrong. Use: `(pl.col("a") > 5) & (pl.col("b") < 10)`
2. **Forgetting .alias()** — Without alias, computed columns get auto-generated names
3. **Using Python functions instead of expressions** — Always check if a native expression exists before writing a UDF
4. **Confusing select and with_columns** — `select` drops other columns; `with_columns` keeps them

## Related Topics

- **DataFrames & Series** → `01-dataframes-series.md`
- **Filtering & Selection** → `06-filtering-selection.md`
- **Aggregation & GroupBy** → `07-aggregation-groupby.md`
