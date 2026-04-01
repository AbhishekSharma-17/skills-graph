---
name: polars
description: "High-performance DataFrame library written in Rust with Python bindings for blazingly fast data manipulation, lazy evaluation, and analytical queries. MANDATORY TRIGGERS: polars, pl.DataFrame, pl.LazyFrame, pl.col, pl.scan_csv, polars dataframe. Also trigger when user wants to process large datasets, replace pandas with faster alternative, do data engineering in Python, work with Parquet/CSV files at scale, or perform analytical queries on structured data. When in doubt about whether to use this skill for data processing tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["polars", "dataframe", "data-engineering", "python", "rust", "lazy-evaluation", "parquet", "analytics", "etl"]
---

# Polars — Skill Router

> Blazingly fast DataFrame library for Python — Rust-powered, lazy-first, with zero dependencies.

**Source:** [docs.pola.rs](https://docs.pola.rs/) v1.39.3 | **Package:** `polars` (PyPI) | **License:** MIT

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Setup** | `references/00-overview.md` | Getting started, installation, what Polars is, why use it, quickstart |
| **DataFrames & Series** | `references/01-dataframes-series.md` | Creating DataFrames/Series, inspection, schema, describe, head/tail |
| **Expressions** | `references/02-expressions.md` | pl.col, pl.lit, expression contexts, select/with_columns/filter, arithmetic |
| **Data Types** | `references/03-data-types.md` | Numeric, temporal, nested (List/Struct/Array), Categorical, Enum, casting |
| **Lazy API** | `references/04-lazy-api.md` | LazyFrame, scan_csv, scan_parquet, collect, explain, query optimization |
| **I/O Operations** | `references/05-io-operations.md` | CSV, Parquet, JSON, Excel, databases, cloud storage, Hive partitions |
| **Filtering & Selection** | `references/06-filtering-selection.md` | filter, select, with_columns, sort, slice, sample, unique, drop |
| **Aggregation & GroupBy** | `references/07-aggregation-groupby.md` | group_by, agg, window functions, over(), rolling, fold |
| **Joins & Concatenation** | `references/08-joins-concat.md` | Inner/left/outer/semi/anti joins, asof joins, concat, diagonal |
| **String Operations** | `references/09-string-operations.md` | str namespace, contains, replace, extract, split, regex, case conversion |
| **Time Series** | `references/10-time-series.md` | Temporal types, dt namespace, group_by_dynamic, rolling windows, parsing |
| **Missing Data** | `references/11-missing-data.md` | Null vs NaN, fill_null, interpolate, drop_nulls, null_count, strategies |
| **Performance & Migration** | `references/12-performance.md` | Threading, memory, streaming, GPU, Pandas migration, anti-patterns |

## Installation

```bash
pip install polars

# With optional dependencies
pip install 'polars[all]'        # Everything
pip install 'polars[numpy]'      # NumPy interop
pip install 'polars[pandas]'     # Pandas interop
pip install 'polars[pyarrow]'    # Arrow interop
pip install 'polars[fsspec]'     # Cloud storage
pip install 'polars[connectorx]' # Database support
pip install 'polars[xlsx2csv]'   # Excel support
pip install 'polars[gpu]'        # GPU acceleration
```

## Quick Reference

- [Polars User Guide](https://docs.pola.rs/)
- [API Reference](https://docs.pola.rs/api/python/stable/reference/)
- [GitHub Repository](https://github.com/pola-rs/polars) (38K+ stars)
- [Polars Cheat Sheet](https://docs.pola.rs/user-guide/misc/reference/)
