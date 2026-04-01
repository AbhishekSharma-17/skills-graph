# Polars — Data Types

> Source: [docs.pola.rs](https://docs.pola.rs/user-guide/concepts/data-types-and-structures/)

## Table of Contents

- [Type System Overview](#type-system-overview)
- [Numeric Types](#numeric-types)
- [String & Binary](#string--binary)
- [Boolean](#boolean)
- [Temporal Types](#temporal-types)
- [Nested Types](#nested-types)
- [Categorical & Enum](#categorical--enum)
- [Type Casting](#type-casting)
- [Type Inference Rules](#type-inference-rules)

## Type System Overview

Polars uses Apache Arrow's type system. Every column is strictly typed — all elements share the same type.

| Category | Types |
|----------|-------|
| **Signed Integer** | `Int8`, `Int16`, `Int32`, `Int64`, `Int128` |
| **Unsigned Integer** | `UInt8`, `UInt16`, `UInt32`, `UInt64`, `UInt128` |
| **Float** | `Float32`, `Float64` |
| **Decimal** | `Decimal(precision, scale)` |
| **String** | `String` |
| **Binary** | `Binary` |
| **Boolean** | `Boolean` |
| **Temporal** | `Date`, `Time`, `Datetime`, `Duration` |
| **Nested** | `List`, `Array`, `Struct` |
| **Categorical** | `Categorical`, `Enum` |
| **Special** | `Null`, `Object` |

## Numeric Types

### Integers

```python
import polars as pl

# Signed integers: Int8 (-128 to 127), Int16, Int32, Int64, Int128
s = pl.Series("small", [1, 2, 3], dtype=pl.Int8)
s = pl.Series("big", [1, 2, 3], dtype=pl.Int64)      # Default for Python int

# Unsigned integers: UInt8 (0 to 255), UInt16, UInt32, UInt64, UInt128
s = pl.Series("positive", [1, 2, 3], dtype=pl.UInt32)
```

**Choosing the right integer type:**
- Default: `Int64` (inferred from Python int)
- IDs/counts: `UInt32` or `UInt64`
- Flags/small ranges: `Int8` or `UInt8` (saves memory)
- Large counts: `Int128` or `UInt128`

### Floats

```python
# Float32: single precision, less memory
# Float64: double precision (default for Python float)
s = pl.Series("precise", [1.1, 2.2], dtype=pl.Float64)
s = pl.Series("compact", [1.1, 2.2], dtype=pl.Float32)
```

**NaN handling:** `NaN` is a valid float value, not null. Use `fill_nan()` separately from `fill_null()`.

### Decimal

```python
# Fixed-point for financial calculations (no floating-point errors)
from decimal import Decimal as D

s = pl.Series("price", [D("19.99"), D("24.50")])
# dtype: Decimal(precision=4, scale=2)
```

## String & Binary

```python
# String: UTF-8 encoded
s = pl.Series("names", ["Alice", "Bob", "Charlie"])

# Binary: raw bytes
s = pl.Series("data", [b"\x00\x01", b"\x02\x03"], dtype=pl.Binary)
```

String operations use the `.str` namespace — see `09-string-operations.md`.

## Boolean

```python
# Bit-packed for memory efficiency
s = pl.Series("flags", [True, False, True, None])

# Boolean operations
s.sum()         # 2 (True = 1)
s.all()         # False
s.any()         # True
```

## Temporal Types

### Date

```python
import datetime as dt

# Date: calendar day (internally days since Unix epoch)
s = pl.Series("dates", [dt.date(2024, 1, 15), dt.date(2024, 6, 30)])
```

### Time

```python
# Time: time of day (internally nanoseconds since midnight)
s = pl.Series("times", [dt.time(9, 30), dt.time(17, 0)])
```

### Datetime

```python
# Datetime: date + time with configurable precision
s = pl.Series("timestamps", [
    dt.datetime(2024, 1, 15, 9, 30),
    dt.datetime(2024, 6, 30, 17, 0),
])

# With timezone
df = pl.DataFrame({
    "ts": pl.Series([dt.datetime(2024, 1, 1)]).cast(
        pl.Datetime("us", "America/New_York")
    )
})

# Time units: "ns" (nanoseconds), "us" (microseconds), "ms" (milliseconds)
```

### Duration

```python
# Duration: time delta (result of datetime subtraction)
s1 = pl.Series([dt.date(2024, 6, 1)])
s2 = pl.Series([dt.date(2024, 1, 1)])
duration = s1 - s2  # Duration type
```

Temporal operations use the `.dt` namespace — see `10-time-series.md`.

## Nested Types

### List

Variable-length sequence of a single type within each row:

```python
df = pl.DataFrame({
    "tags": [["python", "rust"], ["data"], ["ml", "ai", "deep"]],
    "scores": [[95, 87], [72], [88, 91, 76]],
})
# tags dtype: List(String)
# scores dtype: List(Int64)

# List operations via .list namespace
df.with_columns(
    pl.col("tags").list.len().alias("tag_count"),
    pl.col("scores").list.mean().alias("avg_score"),
    pl.col("tags").list.contains("python").alias("has_python"),
    pl.col("tags").list.get(0).alias("first_tag"),
    pl.col("scores").list.sort().alias("sorted_scores"),
)

# Explode list into rows
df.explode("tags")
# Each tag becomes its own row

# List eval — run expression on each list
df.with_columns(
    pl.col("scores").list.eval(pl.element() * 10).alias("scaled")
)
```

### Array

Fixed-size sequence (like NumPy arrays) — all rows have the same length:

```python
df = pl.DataFrame({
    "coords": [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
}, schema={"coords": pl.Array(pl.Float64, 3)})

# Array operations via .arr namespace
df.with_columns(
    pl.col("coords").arr.sum().alias("total"),
    pl.col("coords").arr.get(0).alias("x"),
)
```

### Struct

Named fields in a composite type:

```python
df = pl.DataFrame({
    "address": [
        {"street": "123 Main", "city": "NYC"},
        {"street": "456 Oak", "city": "LA"},
    ]
})
# address dtype: Struct({"street": String, "city": String})

# Access fields via .struct namespace
df.with_columns(
    pl.col("address").struct.field("city").alias("city"),
)

# Unnest struct into separate columns
df.unnest("address")
# Now has "street" and "city" as separate columns

# Create struct from columns
df.select(
    pl.struct("name", "age").alias("person")
)
```

## Categorical & Enum

### Categorical

Runtime-inferred categories — encoding determined from data:

```python
df = pl.DataFrame({
    "color": ["red", "blue", "red", "green", "blue"],
}).with_columns(
    pl.col("color").cast(pl.Categorical)
)

# Benefits: memory-efficient for repeating strings
# Stored as integer indices + string lookup table

# Physical representation (underlying integers)
df.with_columns(
    pl.col("color").to_physical().alias("color_id")
)
```

### Enum

Predetermined, ordered categories — defined upfront:

```python
size_type = pl.Enum(["S", "M", "L", "XL"])

df = pl.DataFrame({
    "size": ["M", "L", "S", "XL"],
}).with_columns(
    pl.col("size").cast(size_type)
)

# Enum advantages over Categorical:
# - Ordering is guaranteed (S < M < L < XL)
# - Invalid values are caught at cast time
# - Compatible across DataFrames (same categories)
```

## Type Casting

```python
# Numeric conversions
pl.col("float_col").cast(pl.Int64)          # Float → Int (truncates)
pl.col("int_col").cast(pl.Float64)          # Int → Float
pl.col("big_int").cast(pl.Int32)            # May overflow

# String conversions
pl.col("id").cast(pl.String)                # Any → String
pl.col("num_str").cast(pl.Int64)            # String → Int
pl.col("date_str").str.to_date("%Y-%m-%d")  # String → Date

# Strict vs lenient
pl.col("value").cast(pl.Int32, strict=True)   # Error on failure
pl.col("value").cast(pl.Int32, strict=False)  # Null on failure

# Boolean conversions
pl.col("flag").cast(pl.Boolean)    # 0/1 → False/True
pl.col("active").cast(pl.UInt8)    # True/False → 1/0
```

## Type Inference Rules

When creating DataFrames from Python data, Polars infers types:

| Python Type | Polars Type |
|-------------|------------|
| `int` | `Int64` |
| `float` | `Float64` |
| `str` | `String` |
| `bool` | `Boolean` |
| `datetime.date` | `Date` |
| `datetime.datetime` | `Datetime("us")` |
| `datetime.time` | `Time` |
| `datetime.timedelta` | `Duration("us")` |
| `list` | `List(...)` |
| `dict` | `Struct(...)` |
| `None` | `Null` |
| `Decimal` | `Decimal(p, s)` |

Override with `schema` or `schema_overrides` parameter.

## Related Topics

- **DataFrames & Series** → `01-dataframes-series.md`
- **Expressions (casting)** → `02-expressions.md`
- **Time Series** → `10-time-series.md`
