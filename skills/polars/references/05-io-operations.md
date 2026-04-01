# Polars — I/O Operations

> Source: [docs.pola.rs](https://docs.pola.rs/user-guide/io/)

## Table of Contents

- [Overview](#overview)
- [CSV](#csv)
- [Parquet](#parquet)
- [JSON / NDJSON](#json--ndjson)
- [Excel](#excel)
- [IPC / Arrow / Feather](#ipc--arrow--feather)
- [Databases](#databases)
- [Cloud Storage](#cloud-storage)
- [Multiple Files](#multiple-files)
- [Hive Partitioning](#hive-partitioning)
- [Common Patterns](#common-patterns)

## Overview

Polars I/O functions come in two flavors:

| Function | Returns | Mode | Use When |
|----------|---------|------|----------|
| `pl.read_*()` | DataFrame | Eager | Small files, interactive work |
| `pl.scan_*()` | LazyFrame | Lazy | Large files, pipelines, optimization needed |

**Always prefer `scan_*` for production pipelines** — it enables query optimization and streaming.

## CSV

### Reading

```python
import polars as pl

# Basic read
df = pl.read_csv("data.csv")

# With options
df = pl.read_csv(
    "data.csv",
    separator=",",            # Default
    has_header=True,          # Default
    skip_rows=0,              # Skip N rows at start
    n_rows=1000,              # Only read first 1000 rows
    columns=["name", "age"],  # Only read specific columns
    dtypes={"age": pl.Int32}, # Force column types (deprecated: use schema_overrides)
    schema_overrides={"age": pl.Int32},
    null_values=["NA", ""],   # Treat as null
    try_parse_dates=True,     # Auto-detect date columns
    encoding="utf8",          # Default
    infer_schema_length=1000, # Rows to scan for type inference
    ignore_errors=True,       # Skip malformed rows
)
```

### Lazy Scanning

```python
lf = pl.scan_csv("data.csv")
lf = pl.scan_csv(
    "data.csv",
    try_parse_dates=True,
    n_rows=None,               # Read all
    schema_overrides={"id": pl.UInt32},
)
```

### Writing

```python
df.write_csv("output.csv")
df.write_csv(
    "output.csv",
    separator=",",
    include_header=True,
    date_format="%Y-%m-%d",
    datetime_format="%Y-%m-%d %H:%M:%S",
    null_value="",
)
```

## Parquet

The **preferred format** for Polars — columnar, compressed, fast, with embedded schema.

### Reading

```python
df = pl.read_parquet("data.parquet")
df = pl.read_parquet(
    "data.parquet",
    columns=["name", "revenue"],   # Only read specific columns
    n_rows=1000,                   # Limit rows
    use_pyarrow=False,             # Use Polars native reader (default)
)
```

### Lazy Scanning

```python
lf = pl.scan_parquet("data.parquet")
lf = pl.scan_parquet(
    "data/*.parquet",              # Glob patterns
    hive_partitioning=True,        # Read Hive-partitioned data
    rechunk=True,                  # Rechunk for contiguous memory
)
```

### Writing

```python
df.write_parquet("output.parquet")
df.write_parquet(
    "output.parquet",
    compression="zstd",       # Options: "lz4", "zstd", "snappy", "gzip", "uncompressed"
    compression_level=3,      # For zstd: 1-22
    statistics=True,          # Write column statistics (enables predicate pushdown)
    row_group_size=512 * 1024,
    use_pyarrow=False,
)

# Sink from lazy (streaming write)
lf.sink_parquet("output.parquet")
```

## JSON / NDJSON

### JSON (Array of Objects)

```python
# Read JSON array
df = pl.read_json("data.json")

# Write JSON
df.write_json("output.json")
df.write_json("output.json", row_oriented=True)
```

### NDJSON (Newline-Delimited JSON)

```python
# Read NDJSON (one JSON object per line)
df = pl.read_ndjson("data.ndjson")

# Lazy scan
lf = pl.scan_ndjson("data.ndjson")

# Write NDJSON
df.write_ndjson("output.ndjson")
```

## Excel

Requires `openpyxl` or `xlsx2csv` extra.

```python
# Read Excel
df = pl.read_excel(
    "data.xlsx",
    sheet_name="Sheet1",       # Or sheet index: sheet_id=0
    read_options={"skip_rows": 1},
)

# Write Excel
df.write_excel(
    "output.xlsx",
    worksheet="Results",
)
```

## IPC / Arrow / Feather

Zero-copy-compatible format (fastest I/O):

```python
# Read IPC (Arrow/Feather)
df = pl.read_ipc("data.arrow")
lf = pl.scan_ipc("data.arrow")

# Write IPC
df.write_ipc("output.arrow")

# Sink from lazy
lf.sink_ipc("output.arrow")
```

## Databases

Requires `connectorx` or `adbc` extra.

```python
# Read from database via connection string
df = pl.read_database_uri(
    query="SELECT * FROM users WHERE active = true",
    uri="postgresql://user:pass@localhost:5432/mydb",
)

# Using connection object (ADBC)
import adbc_driver_postgresql.dbapi as pg_dbapi

with pg_dbapi.connect("postgresql://localhost/mydb") as conn:
    df = pl.read_database(
        query="SELECT * FROM orders",
        connection=conn,
    )

# Write to database
df.write_database(
    table_name="results",
    connection="postgresql://user:pass@localhost:5432/mydb",
    if_table_exists="replace",   # "append", "replace", "fail"
)
```

**Supported databases via ConnectorX:** PostgreSQL, MySQL, SQLite, SQL Server, Oracle, BigQuery, Redshift, Clickhouse.

## Cloud Storage

Requires `fsspec` extra and provider-specific package.

```python
# AWS S3
lf = pl.scan_parquet(
    "s3://my-bucket/data/*.parquet",
    storage_options={
        "aws_access_key_id": "...",
        "aws_secret_access_key": "...",
        "aws_region": "us-east-1",
    },
)

# Google Cloud Storage
lf = pl.scan_parquet("gs://my-bucket/data.parquet")

# Azure Blob Storage
lf = pl.scan_parquet(
    "az://container/data.parquet",
    storage_options={"account_name": "...", "account_key": "..."},
)

# Write to cloud
df.write_parquet("s3://my-bucket/output.parquet")
```

**Environment variables:** Set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION` for credential-free S3 access.

## Multiple Files

```python
# Glob patterns
lf = pl.scan_parquet("data/year=*/month=*/*.parquet")
lf = pl.scan_csv("logs/*.csv")

# List of files
lf = pl.scan_parquet(["file1.parquet", "file2.parquet", "file3.parquet"])

# Concatenate multiple CSVs
import glob
files = glob.glob("data/*.csv")
df = pl.concat([pl.read_csv(f) for f in files])

# Better: lazy concat
lf = pl.concat([pl.scan_csv(f) for f in files])
```

## Hive Partitioning

Read directory-partitioned data where folders encode column values:

```
data/
  year=2023/
    month=01/
      part-0001.parquet
    month=02/
      part-0001.parquet
  year=2024/
    ...
```

```python
lf = pl.scan_parquet(
    "data/**/*.parquet",
    hive_partitioning=True,
)
# "year" and "month" columns are automatically available

# Filter uses partition pruning (fast)
result = lf.filter(pl.col("year") == 2024).collect()
```

## Common Patterns

### Type-Safe CSV Pipeline

```python
schema_overrides = {
    "id": pl.UInt32,
    "amount": pl.Float64,
    "date": pl.Date,
    "category": pl.Categorical,
}

result = (
    pl.scan_csv("transactions.csv", schema_overrides=schema_overrides)
    .filter(pl.col("amount") > 0)
    .group_by("category")
    .agg(pl.col("amount").sum())
    .collect()
)
```

### CSV to Parquet Conversion

```python
(
    pl.scan_csv("raw_data.csv", try_parse_dates=True)
    .with_columns(pl.col("id").cast(pl.UInt32))
    .sink_parquet("processed.parquet", compression="zstd")
)
```

## Related Topics

- **Lazy API** → `04-lazy-api.md`
- **Performance & Migration** → `12-performance.md`
- **Data Types** → `03-data-types.md`
