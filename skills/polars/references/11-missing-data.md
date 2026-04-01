# Polars — Missing Data

> Source: [docs.pola.rs](https://docs.pola.rs/user-guide/expressions/missing-data/)

## Table of Contents

- [Null vs NaN](#null-vs-nan)
- [Detecting Missing Data](#detecting-missing-data)
- [Filling Missing Data](#filling-missing-data)
- [Dropping Missing Data](#dropping-missing-data)
- [Interpolation](#interpolation)
- [NaN Handling](#nan-handling)
- [Common Patterns](#common-patterns)

## Null vs NaN

Polars distinguishes between two types of "missing" values:

| | `null` | `NaN` |
|--|--------|-------|
| **Meaning** | Missing/absent data | Invalid floating-point result |
| **Types** | Any data type | Float32, Float64 only |
| **Detection** | `is_null()` | `is_nan()` |
| **Filling** | `fill_null()` | `fill_nan()` |
| **In aggregations** | Skipped by default | Propagated (poisonous) |
| **Python equivalent** | `None` | `float("nan")` |

```python
import polars as pl

df = pl.DataFrame({
    "a": [1.0, None, 3.0, float("nan"), 5.0],
})

# null_count does NOT count NaN
df.null_count()  # a: 1 (only None)

# mean skips null but NaN propagates
df.select(pl.col("a").mean())  # NaN (because NaN poisons)

# Best practice: convert NaN to null first
df.with_columns(pl.col("a").fill_nan(None))
```

**Rule of thumb:** Convert NaN to null early in your pipeline with `fill_nan(None)`, then handle all missing data uniformly with null-based functions.

## Detecting Missing Data

### null_count — Efficient Count

```python
# Count nulls per column (uses internal bitmap, very fast)
df.null_count()

# Per column in expression
df.select(pl.all().null_count())
```

### is_null / is_not_null

```python
# Boolean mask
df.with_columns(
    pl.col("email").is_null().alias("missing_email"),
    pl.col("email").is_not_null().alias("has_email"),
)

# Filter nulls
df.filter(pl.col("score").is_null())      # Rows with null score
df.filter(pl.col("score").is_not_null())  # Rows with non-null score
```

### Counting and Ratios

```python
# Null percentage per column
df.select(
    (pl.all().null_count() / pl.len() * 100).name.suffix("_null_pct")
)

# Columns with any nulls
null_cols = [
    col for col in df.columns
    if df.select(pl.col(col).null_count()).item() > 0
]
```

## Filling Missing Data

### fill_null — Literal Value

```python
# Fill with constant
df.with_columns(
    pl.col("score").fill_null(0),
    pl.col("name").fill_null("Unknown"),
    pl.col("active").fill_null(False),
)
```

### fill_null — Expression

```python
# Fill with computed value
df.with_columns(
    pl.col("score").fill_null(pl.col("score").mean()),
    pl.col("price").fill_null(pl.col("default_price")),
    pl.col("value").fill_null(2 * pl.col("base_value")),
)
```

### fill_null — Strategy

```python
# Forward fill (carry last known value forward)
df.with_columns(
    pl.col("value").fill_null(strategy="forward"),
)

# Backward fill (use next known value)
df.with_columns(
    pl.col("value").fill_null(strategy="backward"),
)

# Fill with min/max/mean/zero/one
df.with_columns(
    pl.col("value").fill_null(strategy="min"),
    pl.col("value").fill_null(strategy="max"),
    pl.col("value").fill_null(strategy="mean"),
    pl.col("value").fill_null(strategy="zero"),
    pl.col("value").fill_null(strategy="one"),
)

# Forward fill with limit
df.with_columns(
    pl.col("value").fill_null(strategy="forward", limit=3),
)
```

### fill_null — Group-Aware

```python
# Fill with group mean
df.with_columns(
    pl.col("score")
    .fill_null(pl.col("score").mean().over("department"))
)
```

## Dropping Missing Data

```python
# Drop rows with any null
df.drop_nulls()

# Drop rows with null in specific columns
df.drop_nulls(subset=["email"])
df.drop_nulls(subset=["name", "email"])
```

## Interpolation

Linear interpolation between known values:

```python
df = pl.DataFrame({
    "x": [1, 2, 3, 4, 5, 6, 7],
    "y": [1.0, None, None, 4.0, None, 6.0, 7.0],
})

df.with_columns(
    pl.col("y").interpolate().alias("y_interpolated"),
)
# y_interpolated: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
```

**Note:** Interpolation does NOT fill edge nulls (nulls at the start or end of a series).

## NaN Handling

### Detect NaN

```python
df.with_columns(
    pl.col("value").is_nan().alias("is_nan"),
    pl.col("value").is_not_nan().alias("is_not_nan"),
)

# Filter out NaN
df.filter(pl.col("value").is_not_nan())
```

### Replace NaN

```python
# NaN → null (recommended first step)
df.with_columns(pl.col("value").fill_nan(None))

# NaN → specific value
df.with_columns(pl.col("value").fill_nan(0.0))

# NaN → computed value
df.with_columns(pl.col("value").fill_nan(pl.col("value").mean()))
```

### Clean Both Null and NaN

```python
# Pipeline: normalize all missing to null, then fill
df.with_columns(
    pl.col("value")
    .fill_nan(None)           # NaN → null
    .fill_null(strategy="forward")  # null → forward fill
    .alias("cleaned"),
)
```

## Common Patterns

### Complete Missing Data Pipeline

```python
cleaned = (
    df
    # Step 1: Normalize NaN to null
    .with_columns(cs.float().fill_nan(None))
    # Step 2: Fill categorical with "Unknown"
    .with_columns(cs.string().fill_null("Unknown"))
    # Step 3: Fill numeric with column median
    .with_columns(
        cs.numeric().fill_null(cs.numeric().median())
    )
    # Step 4: Drop rows still missing critical columns
    .drop_nulls(subset=["id", "date"])
)
```

### Null-Safe Operations

```python
# Null-safe equality (treats null == null as True)
pl.col("a").eq_missing(pl.col("b"))

# Coalesce: first non-null value
pl.coalesce(pl.col("primary"), pl.col("secondary"), pl.lit("default"))
```

### Sentinel Value Detection

```python
# Convert sentinel values to proper nulls
df.with_columns(
    pl.when(pl.col("value") == -999)
    .then(None)
    .otherwise(pl.col("value"))
    .alias("value"),
)

# Or use replace
df.with_columns(
    pl.col("status").replace({"N/A": None, "": None}),
)
```

### Missing Data Report

```python
# Summary of missing data
missing_report = df.select(
    pl.all().null_count().name.suffix("_nulls"),
).unpivot(variable_name="column", value_name="null_count")

# With percentages
missing_report = pl.DataFrame({
    "column": df.columns,
    "null_count": [df[c].null_count() for c in df.columns],
    "null_pct": [df[c].null_count() / len(df) * 100 for c in df.columns],
}).filter(pl.col("null_count") > 0).sort("null_pct", descending=True)
```

## Related Topics

- **Data Types** → `03-data-types.md`
- **Expressions** → `02-expressions.md`
- **Filtering & Selection** → `06-filtering-selection.md`
