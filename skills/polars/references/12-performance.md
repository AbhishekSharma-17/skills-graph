# Polars — Performance & Migration

> Source: [docs.pola.rs](https://docs.pola.rs/user-guide/)

## Table of Contents

- [Performance Principles](#performance-principles)
- [Expression Optimization](#expression-optimization)
- [Memory Management](#memory-management)
- [Threading](#threading)
- [Streaming Large Datasets](#streaming-large-datasets)
- [GPU Acceleration](#gpu-acceleration)
- [Anti-Patterns](#anti-patterns)
- [Pandas Migration Guide](#pandas-migration-guide)
- [Benchmarking Tips](#benchmarking-tips)

## Performance Principles

Polars is fast by default. Follow these priorities:

1. **Use native expressions** — Never use Python UDFs when a Polars expression exists
2. **Use the lazy API** — Enables automatic query optimization
3. **Use Parquet** — Columnar format with predicate and projection pushdown
4. **Let Polars parallelize** — Don't manually multiprocess
5. **Minimize data movement** — Filter early, project early

## Expression Optimization

### Do: Use Native Expressions

```python
# GOOD: Native expression (runs in Rust, parallel)
df.with_columns(pl.col("name").str.to_uppercase())

# BAD: Python UDF (single-threaded, slow)
df.with_columns(pl.col("name").map_elements(lambda x: x.upper()))
```

### Do: Combine Expressions

```python
# GOOD: Multiple expressions in one context (run in parallel)
df.with_columns(
    pl.col("a").sum().alias("sum_a"),
    pl.col("b").mean().alias("mean_b"),
    pl.col("c").std().alias("std_c"),
)

# BAD: Sequential operations (one at a time)
df = df.with_columns(pl.col("a").sum().alias("sum_a"))
df = df.with_columns(pl.col("b").mean().alias("mean_b"))
df = df.with_columns(pl.col("c").std().alias("std_c"))
```

### Do: Use Appropriate Types

```python
# GOOD: Use Categorical for repeated strings
df.with_columns(pl.col("category").cast(pl.Categorical))

# GOOD: Use smallest sufficient integer type
df.with_columns(pl.col("small_count").cast(pl.UInt8))  # 0-255

# GOOD: Float32 when Float64 precision isn't needed
df.with_columns(pl.col("score").cast(pl.Float32))
```

### Do: Filter Before Aggregating

```python
# GOOD: Filter first, then aggregate
(
    pl.scan_parquet("data.parquet")
    .filter(pl.col("year") == 2024)       # Reduce data first
    .group_by("category")
    .agg(pl.col("value").sum())
    .collect()
)

# BAD: Aggregate everything, then filter
(
    pl.scan_parquet("data.parquet")
    .group_by("category", "year")
    .agg(pl.col("value").sum())
    .filter(pl.col("year") == 2024)       # Too late
    .collect()
)
```

## Memory Management

### Estimated Size

```python
df.estimated_size()        # bytes
df.estimated_size("mb")    # megabytes
df.estimated_size("gb")    # gigabytes
```

### Rechunk

After many operations, data may be fragmented across multiple memory chunks:

```python
# Consolidate memory layout
df = df.rechunk()
```

### Column Type Optimization

```python
# Downcast numeric columns to save memory
import polars.selectors as cs

df = df.with_columns(
    cs.integer().shrink_dtype(),    # Auto-shrink to smallest int type
    cs.float().cast(pl.Float32),   # Reduce float precision if acceptable
)
```

### Drop Unused Columns Early

```python
# Projection pushdown handles this in lazy mode
lf = pl.scan_parquet("data.parquet").select("col1", "col2")  # Only reads 2 columns

# In eager mode, manually drop
df = df.drop("large_text_column", "unused_feature")
```

## Threading

Polars automatically uses all CPU cores. You rarely need to configure this.

### Thread Pool Configuration

```python
# Set before importing polars
import os
os.environ["POLARS_MAX_THREADS"] = "8"

# Or check current setting
import polars as pl
print(pl.thread_pool_size())
```

### Multiprocessing Considerations

**Don't use multiprocessing with Polars** — it's already parallel. If you must (for single-threaded third-party libraries):

```python
# MUST use spawn, NOT fork
from multiprocessing import get_context

with get_context("spawn").Pool() as pool:
    results = pool.map(process_with_external_lib, data_chunks)
```

**Why not fork?** Fork copies the parent process's mutex locks in an acquired state, causing deadlocks with Polars' internal thread pool.

## Streaming Large Datasets

For datasets larger than RAM:

```python
# Streaming execution
result = (
    pl.scan_csv("huge_file.csv")
    .filter(pl.col("valid"))
    .group_by("category")
    .agg(pl.col("amount").sum())
    .collect(streaming=True)
)

# Sink directly to file (never loads into memory)
(
    pl.scan_parquet("huge_input/*.parquet")
    .filter(pl.col("year") >= 2024)
    .sink_parquet("filtered_output.parquet")
)
```

### Chunked Processing (Manual)

When streaming isn't sufficient:

```python
# Process CSV in chunks
reader = pl.read_csv_batched("huge.csv", batch_size=100_000)
results = []
while True:
    batch = reader.next_batches(1)
    if batch is None:
        break
    result = batch[0].filter(pl.col("valid")).group_by("cat").agg(pl.col("val").sum())
    results.append(result)

final = pl.concat(results).group_by("cat").agg(pl.col("val").sum())
```

## GPU Acceleration

Requires `polars[gpu]` and NVIDIA GPU with CUDA:

```python
# Run query on GPU
result = (
    pl.scan_parquet("data.parquet")
    .filter(pl.col("value") > 100)
    .group_by("category")
    .agg(pl.col("value").sum())
    .collect(engine="gpu")
)
```

**When to use GPU:**
- Large in-memory datasets (millions of rows)
- Heavy aggregations and joins
- Compute-bound queries (not I/O-bound)

**When NOT to use GPU:**
- Small datasets (GPU overhead > benefit)
- I/O-bound workflows
- Operations GPU doesn't support yet

## Anti-Patterns

### 1. Row-by-Row Iteration

```python
# TERRIBLE: Python loop (1000x slower)
for i in range(len(df)):
    df[i, "result"] = df[i, "a"] + df[i, "b"]

# GOOD: Vectorized expression
df.with_columns((pl.col("a") + pl.col("b")).alias("result"))
```

### 2. Unnecessary .apply() / .map_elements()

```python
# BAD: Python lambda
df.with_columns(pl.col("x").map_elements(lambda x: x ** 2))

# GOOD: Native expression
df.with_columns((pl.col("x") ** 2).alias("x_squared"))
```

### 3. Repeated Collect

```python
# BAD: Collect after every step
df = lf.filter(...).collect()
df = df.lazy().with_columns(...).collect()
df = df.lazy().group_by(...).agg(...).collect()

# GOOD: Single collect at the end
result = (
    lf.filter(...)
    .with_columns(...)
    .group_by(...)
    .agg(...)
    .collect()
)
```

### 4. Using Pandas Interop in Hot Path

```python
# BAD: Convert back and forth
pandas_df = df.to_pandas()
result = pandas_df.groupby("cat")["val"].transform("mean")
df = df.with_columns(pl.from_pandas(result))

# GOOD: Stay in Polars
df.with_columns(pl.col("val").mean().over("cat"))
```

### 5. String Column for Categories

```python
# BAD: Repeated strings waste memory
# "electronics" stored 1M times

# GOOD: Use Categorical
df.with_columns(pl.col("category").cast(pl.Categorical))
```

## Pandas Migration Guide

### Common Translations

| Pandas | Polars |
|--------|--------|
| `df["col"]` | `df.select("col")` or `df["col"]` (returns Series) |
| `df[df["a"] > 5]` | `df.filter(pl.col("a") > 5)` |
| `df["new"] = expr` | `df.with_columns(expr.alias("new"))` |
| `df.apply(func)` | `df.with_columns(pl.col(...).map_elements(func))` |
| `df.groupby("a").agg({"b": "sum"})` | `df.group_by("a").agg(pl.col("b").sum())` |
| `df.merge(df2, on="key")` | `df.join(df2, on="key")` |
| `pd.concat([df1, df2])` | `pl.concat([df1, df2])` |
| `df.pivot_table(...)` | `df.pivot(...)` |
| `df.melt(...)` | `df.unpivot(...)` |
| `df.sort_values("a")` | `df.sort("a")` |
| `df.drop_duplicates()` | `df.unique()` |
| `df.isna()` | `df.select(pl.all().is_null())` |
| `df.fillna(0)` | `df.fill_null(0)` |
| `df.rename(columns={"a": "b"})` | `df.rename({"a": "b"})` |
| `df.dtypes` | `df.dtypes` or `df.schema` |
| `df.describe()` | `df.describe()` |

### Key Mindset Shifts

1. **Immutable DataFrames** — Operations return new DataFrames; no in-place modification
2. **Expressions over indexing** — Use `pl.col()` instead of `df["col"]` in operations
3. **Lazy by default** — Use `scan_*` and `.collect()` for pipelines
4. **No index** — Polars has no row index; use regular columns instead
5. **Parallel expressions** — Multiple expressions in `select`/`with_columns` run concurrently

## Benchmarking Tips

```python
import time

# Warm up (first query may include JIT compilation)
_ = lf.collect()

# Benchmark
start = time.perf_counter()
result = lf.collect()
elapsed = time.perf_counter() - start
print(f"Query took {elapsed:.3f}s")

# Compare plans
print(lf.explain())             # Logical plan
print(lf.explain(optimized=True))  # Optimized plan
```

## Related Topics

- **Lazy API** → `04-lazy-api.md`
- **I/O Operations** → `05-io-operations.md`
- **Overview** → `00-overview.md`
