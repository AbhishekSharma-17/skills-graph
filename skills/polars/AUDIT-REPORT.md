# Audit Report — Polars Skill

**Audit Date:** 2026-04-01
**Skill Version:** 1.0.0
**Source Version:** Polars v1.39.3

## Quality Assessment

| Category | Score (1-5) | Notes |
|----------|:-----------:|-------|
| **Architecture** | 5 | Clean router + 13 focused leaf nodes. No file exceeds 500 lines. Logical topic progression from basics to advanced. |
| **Content Quality** | 5 | All code examples are syntactically valid Python. Practical, real-world patterns included. Consistent formatting with tables, code blocks, and section headers. |
| **Completeness** | 4 | Covers core API surface comprehensively. Missing: expression plugins, SQL interface, Polars Cloud, visualization details. These are secondary topics. |
| **Maintainability** | 5 | VERSION.json tracks per-file source pages. check-updates.py automates staleness detection. Clear changelog format. |
| **Trigger Quality** | 5 | MANDATORY TRIGGERS cover primary identifiers (polars, pl.DataFrame, pl.col). Broader triggers catch data engineering and Pandas migration use cases. |

## Coverage Map

| Polars Feature | Reference File | Coverage |
|----------------|---------------|----------|
| Installation & Setup | 00-overview | Full |
| DataFrame/Series | 01-dataframes-series | Full |
| Expression System | 02-expressions | Full |
| Data Types | 03-data-types | Full |
| Lazy Evaluation | 04-lazy-api | Full |
| I/O (CSV, Parquet, etc.) | 05-io-operations | Full |
| Filtering/Selection | 06-filtering-selection | Full |
| Aggregation/GroupBy | 07-aggregation-groupby | Full |
| Joins/Concat | 08-joins-concat | Full |
| String Operations | 09-string-operations | Full |
| Time Series | 10-time-series | Full |
| Missing Data | 11-missing-data | Full |
| Performance/Migration | 12-performance | Full |
| SQL Interface | — | Not covered |
| Expression Plugins | — | Not covered |
| Polars Cloud | — | Not covered |
| Visualization | 00-overview (brief) | Partial |

## Recommendations for v1.1.0

1. Add SQL interface reference (Polars SQL context)
2. Add expression plugins guide
3. Add visualization integration details (Altair, hvPlot, Matplotlib)
4. Monitor for Polars v2.0 breaking changes
