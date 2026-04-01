# Polars — Lazy API

> Source: [docs.pola.rs](https://docs.pola.rs/user-guide/lazy/)

## Table of Contents

- [Why Lazy?](#why-lazy)
- [Creating LazyFrames](#creating-lazyframes)
- [Building Queries](#building-queries)
- [Executing Queries](#executing-queries)
- [Query Optimization](#query-optimization)
- [Query Plans](#query-plans)
- [Streaming Mode](#streaming-mode)
- [GPU Support](#gpu-support)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## Why Lazy?

The lazy API defers all computation until you explicitly call `.collect()`. This enables:

1. **Automatic query optimization** — predicate pushdown, projection pushdown, slice pushdown
2. **Larger-than-RAM datasets** — streaming mode processes data in chunks
3. **Early schema validation** — catch type errors before processing data
4. **Efficient I/O** — only read columns and rows actually needed

**Rule of thumb:** Always use the lazy API for data pipelines. Use eager only for interactive exploration.

## Creating LazyFrames

### From Files (Preferred)

```python
import polars as pl

# Scan — creates LazyFrame without reading data
lf = pl.scan_csv("data.csv")
lf = pl.scan_parquet("data.parquet")
lf = pl.scan_parquet("data/*.parquet")     # Glob patterns
lf = pl.scan_ipc("data.arrow")
lf = pl.scan_ndjson("data.ndjson")

# With options
lf = pl.scan_csv(
    "data.csv",
    separator=",",
    has_header=True,
    try_parse_dates=True,
    n_rows=1000,                  # Limit rows read
    schema_overrides={"id": pl.UInt32},
)

lf = pl.scan_parquet(
    "s3://bucket/data/*.parquet",  # Cloud storage
    hive_partitioning=True,
    storage_options={"aws_region": "us-east-1"},
)
```

### From Existing DataFrame

```python
df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
lf = df.lazy()
```

## Building Queries

LazyFrames support the same expression API as DataFrames. Operations are recorded but not executed:

```python
lf = (
    pl.scan_parquet("sales/*.parquet")
    .filter(pl.col("date") >= "2024-01-01")
    .with_columns(
        (pl.col("price") * pl.col("quantity")).alias("revenue"),
        pl.col("category").str.to_uppercase().alias("category_upper"),
    )
    .group_by("category_upper")
    .agg(
        pl.col("revenue").sum().alias("total_revenue"),
        pl.col("revenue").mean().alias("avg_revenue"),
        pl.len().alias("order_count"),
    )
    .sort("total_revenue", descending=True)
    .head(20)
)
# Nothing has executed yet — lf is a query plan
```

## Executing Queries

### collect() — Full Materialization

```python
# Execute the query and return a DataFrame
df = lf.collect()

# With streaming for large datasets
df = lf.collect(streaming=True)
```

### fetch() — Partial Execution (for Testing)

```python
# Execute on first N rows (useful for testing queries)
sample_df = lf.fetch(n_rows=1000)
```

### sink_parquet() / sink_csv() — Write Without Loading

```python
# Process and write directly without loading into memory
lf.sink_parquet("output.parquet")
lf.sink_csv("output.csv")
lf.sink_ipc("output.arrow")
```

## Query Optimization

Polars automatically applies these optimizations:

### Predicate Pushdown

Filters are pushed to the data source level:

```python
# The filter is applied during scan, not after loading all data
lf = (
    pl.scan_parquet("data.parquet")
    .filter(pl.col("year") == 2024)       # Pushed to scan
    .select("name", "revenue")
)
# Parquet row groups where year != 2024 are skipped entirely
```

### Projection Pushdown

Only required columns are read:

```python
# Only "name" and "revenue" columns are read from disk
lf = (
    pl.scan_parquet("data.parquet")       # Has 50 columns
    .select("name", "revenue")             # Only 2 needed
)
```

### Slice Pushdown

Limits are pushed to scan:

```python
# Only reads first 10 rows
lf = pl.scan_csv("huge.csv").head(10)
```

### Common Subplan Elimination

Shared computations are cached:

```python
# If two branches of a query use the same scan, it's read once
lf1 = pl.scan_parquet("data.parquet")
joined = lf1.join(lf1.group_by("key").agg(pl.col("val").sum()), on="key")
```

## Query Plans

### Inspect the Plan

```python
# Logical plan (what you wrote)
print(lf.explain())

# Optimized plan (what will actually execute)
print(lf.explain(optimized=True))

# Show query plan as a graph (in Jupyter)
lf.show_graph()
```

### Reading Plans

```
SORT BY [col("total_revenue")]
  AGGREGATE
    [col("revenue").sum().alias("total_revenue")] BY [col("category")]
    Csv SCAN [sales.csv]
    PROJECT 3/8 COLUMNS        ← Projection pushdown: only 3 of 8 columns read
    SELECTION: col("date") >= "2024-01-01"  ← Predicate pushdown
```

Key terms:
- `PROJECT N/M COLUMNS` — projection pushdown reduced columns
- `SELECTION:` — predicate pushdown pushed filter to scan
- `CACHE` — common subplan elimination

## Streaming Mode

Process data in chunks without loading everything into memory:

```python
# Stream large dataset
result = (
    pl.scan_csv("huge_file.csv")
    .filter(pl.col("category") == "A")
    .group_by("region")
    .agg(pl.col("sales").sum())
    .collect(streaming=True)
)

# Sink directly to file (never loads full result)
(
    pl.scan_parquet("input/*.parquet")
    .filter(pl.col("valid"))
    .sink_parquet("output.parquet")
)
```

**Streaming limitations:**
- Not all operations support streaming (e.g., some complex joins)
- Performance may differ from non-streaming mode
- Check `.explain(streaming=True)` to verify streaming plan

## GPU Support

```python
# Requires polars[gpu] and NVIDIA GPU
result = (
    pl.scan_parquet("data.parquet")
    .filter(pl.col("value") > 100)
    .group_by("category")
    .agg(pl.col("value").sum())
    .collect(engine="gpu")    # Run on GPU
)
```

## Common Patterns

### ETL Pipeline

```python
def build_sales_report(input_path: str, output_path: str) -> None:
    (
        pl.scan_parquet(input_path)
        .filter(pl.col("status") == "completed")
        .with_columns(
            (pl.col("price") * pl.col("quantity")).alias("revenue"),
            pl.col("date").dt.month().alias("month"),
        )
        .group_by("month", "product_category")
        .agg(
            pl.col("revenue").sum().alias("total_revenue"),
            pl.col("revenue").mean().alias("avg_order_value"),
            pl.len().alias("order_count"),
        )
        .sort("month", "total_revenue", descending=[False, True])
        .sink_parquet(output_path)
    )
```

### Lazy Join

```python
orders = pl.scan_parquet("orders.parquet")
customers = pl.scan_parquet("customers.parquet")

result = (
    orders
    .join(customers, on="customer_id", how="left")
    .filter(pl.col("country") == "US")
    .select("order_id", "customer_name", "total")
    .collect()
)
```

## Common Pitfalls

1. **Forgetting .collect()** — LazyFrame operations return another LazyFrame, not data
2. **Mixing eager and lazy** — Don't call DataFrame methods on a LazyFrame
3. **Over-collecting** — Collect once at the end, not after each step
4. **Ignoring streaming** — For large data, always try `collect(streaming=True)`
5. **Not checking the plan** — Use `.explain()` to verify optimizations are applied

## Related Topics

- **Overview & Setup** → `00-overview.md`
- **I/O Operations** → `05-io-operations.md`
- **Performance & Migration** → `12-performance.md`
