# Polars — Filtering & Selection

> Source: [docs.pola.rs](https://docs.pola.rs/user-guide/expressions/)

## Table of Contents

- [Selecting Columns](#selecting-columns)
- [Filtering Rows](#filtering-rows)
- [Sorting](#sorting)
- [Slicing & Sampling](#slicing--sampling)
- [Unique & Deduplicate](#unique--deduplicate)
- [Dropping Columns & Nulls](#dropping-columns--nulls)
- [Combined Patterns](#combined-patterns)

## Selecting Columns

### select — Keep Only These Columns

```python
import polars as pl

# By name
df.select("name", "age")
df.select(pl.col("name"), pl.col("age"))

# With transformations
df.select(
    pl.col("name").str.to_uppercase().alias("NAME"),
    (pl.col("salary") / 1000).alias("salary_k"),
)

# By data type
df.select(pl.col(pl.Int64))
df.select(pl.col(pl.Float64, pl.Int64))

# By regex
df.select(pl.col("^score_.*$"))

# All columns
df.select(pl.all())

# Exclude specific
df.select(pl.all().exclude("internal_id", "debug_flag"))
```

### Column Selectors

```python
import polars.selectors as cs

# By type
df.select(cs.numeric())        # All numeric
df.select(cs.string())         # All string
df.select(cs.temporal())       # All date/time
df.select(cs.boolean())        # All boolean

# By name
df.select(cs.by_name("a", "b", "c"))
df.select(cs.starts_with("feature_"))
df.select(cs.ends_with("_id"))
df.select(cs.contains("score"))
df.select(cs.matches("^col_\\d+$"))

# Set operations
df.select(cs.numeric() - cs.by_name("id"))       # Numeric except "id"
df.select(cs.numeric() & cs.starts_with("feat")) # Numeric AND starts with "feat"
df.select(cs.numeric() | cs.boolean())            # Numeric OR boolean
```

### with_columns — Add Without Removing

```python
# Add new columns, keep all existing
df.with_columns(
    (pl.col("price") * pl.col("qty")).alias("total"),
    pl.lit("USD").alias("currency"),
)

# Overwrite existing column
df.with_columns(pl.col("name").str.to_uppercase())
```

## Filtering Rows

### Basic Filters

```python
# Single condition
df.filter(pl.col("age") > 30)
df.filter(pl.col("city") == "NYC")
df.filter(pl.col("name").str.contains("Ali"))

# Negation
df.filter(pl.col("status") != "inactive")
df.filter(~pl.col("is_deleted"))
```

### Multiple Conditions

```python
# AND — all conditions must be true
df.filter(
    (pl.col("age") > 25) & (pl.col("salary") > 80000)
)

# OR — any condition can be true
df.filter(
    (pl.col("city") == "NYC") | (pl.col("city") == "LA")
)

# Complex combinations
df.filter(
    ((pl.col("age") >= 25) & (pl.col("age") <= 40))
    & (pl.col("department").is_in(["Engineering", "Product"]))
    & ~(pl.col("on_leave"))
)
```

### Range and Membership

```python
# Between (inclusive)
df.filter(pl.col("score").is_between(70, 100))

# In list
df.filter(pl.col("status").is_in(["active", "pending"]))

# Not in list
df.filter(~pl.col("status").is_in(["cancelled", "deleted"]))
```

### Null-Aware Filters

```python
df.filter(pl.col("email").is_not_null())
df.filter(pl.col("deleted_at").is_null())
```

### String-Based Filters

```python
df.filter(pl.col("name").str.starts_with("A"))
df.filter(pl.col("email").str.ends_with("@gmail.com"))
df.filter(pl.col("bio").str.contains("engineer", literal=True))
df.filter(pl.col("code").str.contains(r"^[A-Z]{3}\d{4}$"))
```

### Date-Based Filters

```python
import datetime as dt

df.filter(pl.col("date") >= dt.date(2024, 1, 1))
df.filter(pl.col("date").dt.year() == 2024)
df.filter(pl.col("date").dt.month().is_in([1, 2, 3]))
df.filter(pl.col("created_at").dt.date() == dt.date.today())
```

## Sorting

```python
# Single column
df.sort("age")
df.sort("age", descending=True)

# Multiple columns
df.sort("department", "salary", descending=[False, True])

# With nulls positioning
df.sort("score", nulls_last=True)
df.sort("score", nulls_last=False)  # Nulls first (default)

# Sort by expression
df.sort(pl.col("name").str.len_chars())

# Top N (sort + head)
df.sort("revenue", descending=True).head(10)

# Bottom N
df.sort("revenue").head(10)
```

### sort_by in Expressions

```python
# Sort one column by another (within expressions)
df.select(
    pl.col("name").sort_by("age")
)

# Sort by multiple columns
df.select(
    pl.col("name").sort_by(["department", "salary"], descending=[False, True])
)
```

## Slicing & Sampling

```python
# Head / Tail
df.head(10)       # First 10 rows
df.tail(5)        # Last 5 rows

# Slice (offset, length)
df.slice(10, 20)  # 20 rows starting at index 10

# Python-style indexing
df[5:15]          # Rows 5 through 14

# Gather specific rows by index
df.gather([0, 5, 10, 15])

# Random sample
df.sample(n=100)                  # 100 random rows
df.sample(fraction=0.1)           # 10% of rows
df.sample(n=50, seed=42)          # Reproducible sampling
df.sample(n=10, with_replacement=True)
```

## Unique & Deduplicate

```python
# Unique rows (all columns)
df.unique()

# Unique by specific columns
df.unique(subset=["email"])
df.unique(subset=["first_name", "last_name"])

# Keep strategy
df.unique(subset=["email"], keep="first")  # First occurrence
df.unique(subset=["email"], keep="last")   # Last occurrence
df.unique(subset=["email"], keep="any")    # Any (fastest)
df.unique(subset=["email"], keep="none")   # Drop all duplicates

# Count unique values
df.select(pl.col("city").n_unique())

# Check if all unique
df.select(pl.col("id").is_unique())

# Find duplicates
df.filter(pl.col("email").is_duplicated())
```

## Dropping Columns & Nulls

```python
# Drop columns
df.drop("temp_col")
df.drop("col_a", "col_b", "col_c")

# Drop null rows
df.drop_nulls()                    # Any column has null
df.drop_nulls(subset=["email"])    # Specific columns
df.drop_nulls(subset=["name", "email"])
```

## Combined Patterns

### Top N per Group

```python
# Top 3 highest-paid per department
df.sort("salary", descending=True).group_by("department").head(3)
```

### Filter + Transform + Select

```python
result = (
    df
    .filter(pl.col("status") == "active")
    .with_columns(
        (pl.col("revenue") - pl.col("cost")).alias("profit"),
    )
    .filter(pl.col("profit") > 0)
    .select("name", "department", "profit")
    .sort("profit", descending=True)
)
```

### Conditional Column Selection

```python
# Select columns that have any null values
null_cols = [col for col in df.columns if df[col].null_count() > 0]
df.select(null_cols)
```

## Related Topics

- **Expressions** → `02-expressions.md`
- **Aggregation & GroupBy** → `07-aggregation-groupby.md`
- **String Operations** → `09-string-operations.md`
