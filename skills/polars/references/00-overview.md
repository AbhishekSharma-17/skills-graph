# Polars — Overview & Setup

> Source: [docs.pola.rs](https://docs.pola.rs/) | Version: 1.39.3

## What is Polars?

Polars is a blazingly fast DataFrame library for Python (and Rust, Node.js, R) built from the ground up in Rust. It uses Apache Arrow columnar format for memory layout and provides both eager and lazy execution modes with automatic query optimization.

**Key differentiators:**
- **5-20x faster than Pandas** for most operations
- **Zero required dependencies** — fast import (~70ms vs Pandas ~520ms)
- **Lazy evaluation** with automatic query optimization (predicate pushdown, projection pushdown)
- **Out-of-core processing** — stream datasets larger than RAM
- **True multithreading** — uses all CPU cores (no Python GIL limitations for Rust operations)
- **GPU support** via NVIDIA RAPIDS integration
- **Apache Arrow native** — zero-copy interop with Arrow ecosystem

## When to Use Polars

| Use Case | Polars | Pandas |
|----------|--------|--------|
| Large datasets (>1GB) | Excellent | Struggles |
| Complex aggregations | Much faster | Slower |
| ETL pipelines | Lazy API optimizes | Manual optimization |
| Memory-constrained | Streaming mode | Out of memory |
| Multi-core utilization | Automatic | Single-threaded |
| Small datasets (<100MB) | Fast | Also fine |
| Ecosystem compatibility | Growing | Mature |

## Installation

```bash
# Basic installation
pip install polars

# With all optional dependencies
pip install 'polars[all]'

# Common extras
pip install 'polars[numpy,pandas,pyarrow]'  # Interop
pip install 'polars[connectorx]'            # Database connectors
pip install 'polars[fsspec]'                # Cloud storage (S3, GCS, Azure)
pip install 'polars[gpu]'                   # GPU acceleration (NVIDIA)
pip install 'polars[xlsx2csv,openpyxl]'     # Excel support
```

Requires Python >= 3.10.

## Quickstart

```python
import polars as pl
import datetime as dt

# Create a DataFrame
df = pl.DataFrame({
    "name": ["Alice", "Bob", "Charlie", "Diana"],
    "age": [30, 25, 35, 28],
    "city": ["NYC", "LA", "NYC", "LA"],
    "salary": [85000, 72000, 95000, 68000],
    "start_date": [
        dt.date(2020, 1, 15),
        dt.date(2021, 6, 1),
        dt.date(2019, 3, 10),
        dt.date(2022, 9, 20),
    ],
})

print(df)
# shape: (4, 5)
# ┌─────────┬─────┬──────┬────────┬────────────┐
# │ name    ┆ age ┆ city ┆ salary ┆ start_date │
# │ ---     ┆ --- ┆ ---  ┆ ---    ┆ ---        │
# │ str     ┆ i64 ┆ str  ┆ i64    ┆ date       │
# ╞═════════╪═════╪══════╪════════╪════════════╡
# │ Alice   ┆ 30  ┆ NYC  ┆ 85000  ┆ 2020-01-15 │
# │ Bob     ┆ 25  ┆ LA   ┆ 72000  ┆ 2021-06-01 │
# │ Charlie ┆ 35  ┆ NYC  ┆ 95000  ┆ 2019-03-10 │
# │ Diana   ┆ 28  ┆ LA   ┆ 68000  ┆ 2022-09-20 │
# └─────────┴─────┴──────┴────────┴────────────┘
```

## Core Concepts at a Glance

### Expressions — The Building Blocks

Everything in Polars is an **expression**. Expressions describe transformations on columns:

```python
# Expressions are composable
expr = pl.col("salary") / 1000  # Reference column, do math
expr = pl.col("name").str.to_uppercase()  # String operations
expr = pl.col("age").mean()  # Aggregation
```

### Contexts — Where Expressions Run

Expressions execute within **contexts** that determine behavior:

```python
# select: pick/transform columns
df.select(pl.col("name"), pl.col("salary") * 1.1)

# with_columns: add new columns, keep existing
df.with_columns((pl.col("salary") * 1.1).alias("new_salary"))

# filter: subset rows
df.filter(pl.col("age") > 28)

# group_by + agg: aggregate by groups
df.group_by("city").agg(pl.col("salary").mean())
```

### Lazy vs Eager

```python
# Eager: executes immediately (like Pandas)
result = df.filter(pl.col("age") > 28).select("name", "salary")

# Lazy: builds query plan, optimizes, then executes
result = (
    df.lazy()
    .filter(pl.col("age") > 28)
    .select("name", "salary")
    .collect()  # Triggers execution
)

# Best practice: scan files lazily
result = (
    pl.scan_parquet("data/*.parquet")
    .filter(pl.col("age") > 28)
    .select("name", "salary")
    .collect()
)
```

## Architecture

```
┌──────────────────────────────────────────┐
│           Python API (polars)            │
├──────────────────────────────────────────┤
│         PyO3 Bindings (Rust ↔ Python)    │
├──────────────────────────────────────────┤
│        Query Optimizer (Lazy Engine)     │
│  • Predicate pushdown                   │
│  • Projection pushdown                  │
│  • Slice pushdown                       │
│  • Common subplan elimination           │
├──────────────────────────────────────────┤
│       Execution Engine (Rust)            │
│  • Multi-threaded via Rayon             │
│  • SIMD vectorized operations           │
│  • Streaming for out-of-core            │
├──────────────────────────────────────────┤
│       Apache Arrow Memory Layout         │
│  • Columnar, cache-friendly             │
│  • Zero-copy interop                    │
└──────────────────────────────────────────┘
```

## Common Patterns

### Reading Data
```python
df = pl.read_csv("data.csv")
df = pl.read_parquet("data.parquet")
df = pl.read_json("data.json")

# Lazy scanning (preferred for large files)
lf = pl.scan_csv("data.csv")
lf = pl.scan_parquet("data/*.parquet")  # Glob patterns supported
```

### Writing Data
```python
df.write_csv("output.csv")
df.write_parquet("output.parquet")
df.write_json("output.json")
```

### Method Chaining
```python
result = (
    pl.scan_parquet("sales/*.parquet")
    .filter(pl.col("date") >= dt.date(2024, 1, 1))
    .with_columns(
        (pl.col("quantity") * pl.col("price")).alias("revenue")
    )
    .group_by("product")
    .agg(
        pl.col("revenue").sum().alias("total_revenue"),
        pl.col("quantity").sum().alias("total_quantity"),
    )
    .sort("total_revenue", descending=True)
    .head(10)
    .collect()
)
```

## Related Topics

- **DataFrames & Series** → `01-dataframes-series.md`
- **Expressions** → `02-expressions.md`
- **Lazy API** → `04-lazy-api.md`
- **Performance & Migration** → `12-performance.md`
