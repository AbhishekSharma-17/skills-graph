---
name: dlt
description: "data load tool (dlt) — open-source Python library for declarative data loading from APIs, databases, and files into warehouses, lakes, and local engines. MANDATORY TRIGGERS: dlt, data load tool, dlthub, dlt pipeline, dlt resource, dlt source, dlt.sources.incremental, rest_api_source. Also trigger when the user wants to build Python data pipelines, extract from REST APIs declaratively, load data into DuckDB/BigQuery/Snowflake/Postgres, implement incremental loading, manage schema evolution, or normalize nested JSON into tables. When in doubt about whether to use this skill for data loading or ELT tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["data-engineering", "etl", "python", "data-loading", "pipelines"]
---

# dlt (data load tool)

> Source: dlt v1.29.1 — https://dlthub.com/docs

## Reference Files

| File | Read When |
|------|-----------|
| [00-overview.md](references/00-overview.md) | Need to understand what dlt is, installation, or quickstart |
| [01-pipeline.md](references/01-pipeline.md) | Creating/configuring pipelines, running loads, or checking load results |
| [02-resources.md](references/02-resources.md) | Defining data-yielding resources, transformers, or table dispatch |
| [03-sources.md](references/03-sources.md) | Combining resources into sources, source configuration, or resource selection |
| [04-incremental-loading.md](references/04-incremental-loading.md) | Implementing cursor-based incremental, merge strategies, or backfills |
| [05-schema-contracts.md](references/05-schema-contracts.md) | Controlling schema evolution, enforcing data quality, or Pydantic integration |
| [06-credentials-config.md](references/06-credentials-config.md) | Setting up secrets.toml, environment variables, or credential injection |
| [07-rest-api-source.md](references/07-rest-api-source.md) | Using the declarative REST API source with auth, pagination, and endpoints |
| [08-destinations.md](references/08-destinations.md) | Configuring destinations (DuckDB, BigQuery, Snowflake, Postgres, etc.) |
| [09-performance.md](references/09-performance.md) | Tuning parallelism, buffer sizes, file rotation, or worker counts |
| [10-transformations.md](references/10-transformations.md) | Transforming data with add_map, add_filter, transformers, or processing steps |
| [11-deployment.md](references/11-deployment.md) | Deploying pipelines to GitHub Actions, Airflow, cloud functions, or dltHub |
| [12-testing-debugging.md](references/12-testing-debugging.md) | Testing pipelines, inspecting load_info, debugging, or validating schemas |

## Installation

```bash
pip install dlt                # Core library
pip install "dlt[duckdb]"      # With DuckDB destination
pip install "dlt[bigquery]"    # With BigQuery destination
pip install "dlt[snowflake]"   # With Snowflake destination
pip install "dlt[postgres]"    # With PostgreSQL destination
```

## Quick Reference

- Docs: https://dlthub.com/docs
- GitHub: https://github.com/dlt-hub/dlt
- PyPI: https://pypi.org/project/dlt/
- Community: https://dlthub.com/community
