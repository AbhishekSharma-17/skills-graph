# Polars — DataFrames & Series

> Source: [docs.pola.rs](https://docs.pola.rs/user-guide/concepts/data-types-and-structures/)

## Table of Contents

- [Series](#series)
- [DataFrame Creation](#dataframe-creation)
- [DataFrame Inspection](#dataframe-inspection)
- [Column Operations](#column-operations)
- [Row Operations](#row-operations)
- [Schema Management](#schema-management)
- [Conversion & Interop](#conversion--interop)

## Series

A **Series** is a 1-dimensional, homogeneous data structure. All elements share the same data type.

```python
import polars as pl

# Create from list (type inferred)
s = pl.Series("heights", [1.75, 1.82, 1.65, 1.90])
# shape: (4,), dtype: f64

# Explicit dtype
s = pl.Series("ids", [1, 2, 3], dtype=pl.UInt32)

# From range
s = pl.Series("index", range(100))

# Named series
s = pl.Series(name="temps", values=[22.5, 18.3, 25.1])
```

### Series Operations

```python
s = pl.Series("values", [10, 20, 30, 40, 50])

# Basic stats
s.mean()       # 30.0
s.sum()        # 150
s.min()        # 10
s.max()        # 50
s.std()        # 15.81...
s.median()     # 30.0
s.len()        # 5

# Element-wise operations
s * 2          # [20, 40, 60, 80, 100]
s > 25         # [false, false, true, true, true]
s.is_between(15, 35)  # [false, true, true, false, false]

# Sorting
s.sort()                    # ascending
s.sort(descending=True)     # descending
s.arg_sort()                # indices that would sort

# Unique values
s.unique()
s.n_unique()       # count of unique values
s.value_counts()   # frequency table
```

## DataFrame Creation

### From Dictionaries

```python
df = pl.DataFrame({
    "name": ["Alice", "Bob", "Charlie"],
    "age": [30, 25, 35],
    "score": [9.5, 8.2, 7.8],
})
```

### From Lists of Rows

```python
df = pl.DataFrame(
    data=[
        ("Alice", 30, 9.5),
        ("Bob", 25, 8.2),
        ("Charlie", 35, 7.8),
    ],
    schema=["name", "age", "score"],
)
```

### With Explicit Schema

```python
df = pl.DataFrame(
    {
        "id": [1, 2, 3],
        "value": [10.5, 20.3, 30.1],
    },
    schema={
        "id": pl.UInt32,
        "value": pl.Float32,
    },
)
```

### Schema Overrides (Partial)

```python
df = pl.DataFrame(
    {"a": [1, 2, 3], "b": ["x", "y", "z"]},
    schema_overrides={"a": pl.Int16},  # Only override 'a'
)
```

### Empty DataFrame with Schema

```python
df = pl.DataFrame(
    schema={
        "id": pl.Int64,
        "name": pl.String,
        "created_at": pl.Datetime,
    }
)
```

## DataFrame Inspection

```python
df = pl.DataFrame({
    "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
    "age": [30, 25, 35, 28, 32],
    "salary": [85000, 72000, 95000, 68000, 91000],
})

# Shape and schema
df.shape        # (5, 3)
df.height       # 5 (row count)
df.width        # 3 (column count)
df.columns      # ["name", "age", "salary"]
df.dtypes       # [String, Int64, Int64]
df.schema       # Schema({"name": String, "age": Int64, "salary": Int64})

# Quick views
df.head(3)      # First 3 rows
df.tail(2)      # Last 2 rows
df.sample(2)    # Random 2 rows
df.glimpse()    # Transposed view (good for wide DataFrames)

# Statistics
df.describe()   # Summary statistics (count, null_count, mean, std, min, max, etc.)
df.null_count() # Null count per column

# Estimated memory
df.estimated_size()        # bytes
df.estimated_size("mb")    # megabytes
```

## Column Operations

### Selecting Columns

```python
# By name
df.select("name", "age")
df.select(pl.col("name", "age"))

# By dtype
df.select(pl.col(pl.Int64))          # All Int64 columns
df.select(cs.numeric())               # All numeric (with selectors)

# By pattern
df.select(pl.col("^salary.*$"))       # Regex pattern

# Excluding columns
df.select(pl.exclude("salary"))
```

### Column Selectors

```python
import polars.selectors as cs

df.select(cs.numeric())           # All numeric columns
df.select(cs.string())            # All string columns
df.select(cs.temporal())          # All date/time columns
df.select(cs.by_name("a", "b"))  # By name
df.select(cs.by_dtype(pl.Int64))  # By dtype
df.select(cs.numeric() - cs.by_name("id"))  # Set operations
```

### Renaming Columns

```python
# Rename specific columns
df.rename({"name": "full_name", "age": "years"})

# Rename all columns with a function
df.rename(lambda col: col.upper())
```

### Adding/Dropping Columns

```python
# Add columns
df.with_columns(
    (pl.col("salary") * 0.1).alias("bonus"),
    pl.lit("active").alias("status"),
)

# Drop columns
df.drop("salary")
df.drop("salary", "age")
```

## Row Operations

```python
# Get single row as tuple
df.row(0)              # First row
df.row(-1)             # Last row
df.row(0, named=True)  # As dict: {"name": "Alice", "age": 30, ...}

# Iterate rows (avoid for large data — use expressions instead)
for row in df.iter_rows(named=True):
    print(row["name"])

# Slice
df.slice(1, 3)    # 3 rows starting at index 1
df.head(5)        # First 5
df.tail(5)        # Last 5
df[2:5]           # Python slicing

# Filter (prefer expressions)
df.filter(pl.col("age") > 28)

# Unique rows
df.unique()                        # All columns
df.unique(subset=["city"])         # Unique by specific columns
df.unique(subset=["city"], keep="first")  # Keep first occurrence

# Sort
df.sort("age")
df.sort("age", descending=True)
df.sort("city", "age", descending=[False, True])  # Multi-column
```

## Schema Management

```python
# View schema
df.schema
# Schema({"name": String, "age": Int64, "salary": Int64})

# Cast column types
df.with_columns(
    pl.col("age").cast(pl.Float64),
    pl.col("salary").cast(pl.Int32),
)

# Cast in schema override during creation
df = pl.DataFrame(
    {"a": [1, 2], "b": [1.0, 2.0]},
    schema_overrides={"a": pl.UInt8, "b": pl.Float32},
)

# Rechunk for memory optimization
df = df.rechunk()
```

## Conversion & Interop

```python
# To/from Pandas
pandas_df = df.to_pandas()
df = pl.from_pandas(pandas_df)

# To/from Arrow
arrow_table = df.to_arrow()
df = pl.from_arrow(arrow_table)

# To/from NumPy
numpy_array = df.to_numpy()
df = pl.from_numpy(numpy_array, schema=["a", "b", "c"])

# To/from dicts
records = df.to_dicts()           # List of dicts
df = pl.from_dicts(records)

row_dict = df.to_dict()           # Dict of lists
series_dict = df.to_dict(as_series=True)  # Dict of Series

# To/from records (list of dicts)
records = df.to_dicts()
df = pl.from_dicts(records)
```

## Common Pitfalls

1. **Don't iterate rows** — Use expressions for vectorized operations instead of `for row in df.iter_rows()`
2. **Schema inference** — When creating from ambiguous data, explicitly specify `schema` or `schema_overrides`
3. **Column names must be unique** — Polars enforces unique column names within a DataFrame
4. **Immutability** — Polars DataFrames are immutable; operations return new DataFrames

## Related Topics

- **Expressions** → `02-expressions.md`
- **Data Types** → `03-data-types.md`
- **Filtering & Selection** → `06-filtering-selection.md`
