# Dagster — Overview & Quickstart

> Source: [docs.dagster.io](https://docs.dagster.io) | Version: 1.13.x

## Table of Contents

- [What is Dagster?](#what-is-dagster)
- [Core Philosophy](#core-philosophy)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quickstart](#quickstart)
- [Key Terminology](#key-terminology)
- [When to Use Dagster](#when-to-use-dagster)
- [Dagster vs Alternatives](#dagster-vs-alternatives)

---

## What is Dagster?

Dagster is an asset-centric data orchestration platform for building, testing, and deploying data pipelines. Unlike task-centric orchestrators (Airflow), Dagster organizes pipelines around **software-defined assets** — declarative descriptions of the data artifacts your pipeline produces.

Key differentiators:
- **Asset-centric** — define *what* data exists, not just *how* to compute it
- **Type-safe** — Pydantic-based configuration and resource injection
- **Testable** — first-class testing support with direct function invocation
- **Observable** — built-in lineage, metadata tracking, and asset health monitoring
- **87+ integrations** — dbt, Snowflake, BigQuery, DuckDB, Airbyte, OpenAI, and more
- **Declarative automation** — describe *when* assets should update, not imperative schedules

## Core Philosophy

Dagster treats data assets as first-class citizens:

```
Traditional (task-centric):     Dagster (asset-centric):
  Task A → Task B → Task C       Asset: raw_data
  (what to DO)                    Asset: cleaned_data (depends on raw_data)
                                  Asset: report (depends on cleaned_data)
                                  (what data EXISTS)
```

Assets automatically create a dependency graph with lineage tracking. The UI shows which assets are fresh, stale, or missing.

## Architecture

```
[User / Schedule / Sensor]
         |
         v
[dagster-webserver]  ←→  [PostgreSQL]  ←→  [dagster-daemon]
  (UI + GraphQL API)       (metadata)       (schedules, sensors,
         |                                   run queuing)
         v
[Code Location Server(s)]  ← gRPC →  [Run Workers]
  (Definitions via gRPC)               (one per run)
```

Three long-running services:
1. **dagster-webserver** — serves UI, handles GraphQL, launches runs
2. **dagster-daemon** — manages schedules, sensors, run queue (singleton)
3. **Code Location Server** — exposes Definitions via gRPC (one per code location)

For development, `dg dev` starts everything in a single process.

## Installation

```bash
# Core packages
pip install dagster dagster-webserver
# or
uv add dagster dagster-webserver

# CLI for project scaffolding
pip install dagster-dg-cli
# or
uv add dagster-dg-cli

# Common integrations
pip install dagster-dbt dagster-snowflake-pandas dagster-duckdb-pandas
pip install dagster-aws dagster-gcp dagster-postgres dagster-docker dagster-k8s
```

**Python requirement:** ≥3.9, <3.15 (3.12-3.13 recommended)

## Quickstart

### Scaffold a new project

```bash
uvx create-dagster@latest project my-project
cd my-project
```

Generated structure:
```
my-project/
├── pyproject.toml
├── src/
│   └── my_project/
│       ├── __init__.py
│       ├── definitions.py
│       └── defs/
│           └── __init__.py
└── tests/
    └── __init__.py
```

### Define assets

```python
import dagster as dg
import pandas as pd

@dg.asset(group_name="ingestion")
def raw_sales() -> pd.DataFrame:
    return pd.read_csv("https://example.com/sales.csv")

@dg.asset(group_name="transform")
def cleaned_sales(raw_sales: pd.DataFrame) -> pd.DataFrame:
    return raw_sales.dropna().drop_duplicates()

@dg.asset(group_name="reporting")
def sales_summary(cleaned_sales: pd.DataFrame) -> pd.DataFrame:
    return cleaned_sales.groupby("region").agg({"revenue": "sum"}).reset_index()
```

### Wire definitions

```python
import dagster as dg

@dg.definitions
def defs():
    return dg.Definitions(
        assets=[raw_sales, cleaned_sales, sales_summary],
        resources={"io_manager": dg.FilesystemIOManager()},
    )
```

### Launch dev server

```bash
dg dev
# Opens UI at http://localhost:3000
```

### Materialize assets

In the UI, navigate to Assets → select all → Materialize. Or via Python:

```python
result = dg.materialize([raw_sales, cleaned_sales, sales_summary])
assert result.success
```

## Key Terminology

| Term | Description |
|------|-------------|
| **Asset** | A data artifact (table, file, ML model) defined by a Python function |
| **Materialization** | The act of computing and persisting an asset's value |
| **Resource** | An external system connection (database, API, cloud storage) |
| **I/O Manager** | Handles serialization/deserialization of asset values between steps |
| **Op** | A unit of computation (the building block inside assets) |
| **Job** | A set of ops or assets configured for execution |
| **Graph** | A DAG of ops wired together |
| **Schedule** | Cron-based trigger for materializing assets |
| **Sensor** | Event-driven trigger that reacts to external changes |
| **Partition** | A logical subdivision of an asset (e.g., by date or region) |
| **Code Location** | A deployed collection of Definitions (isolated Python process) |
| **Definitions** | The top-level container for all Dagster entities |
| **Dagster Cloud** | Managed deployment platform (serverless or hybrid) |

## When to Use Dagster

| Use Case | Dagster Fit |
|----------|-------------|
| ETL/ELT pipelines | Excellent — asset-centric model, dbt integration |
| ML training pipelines | Excellent — partitioned datasets, experiment tracking |
| Data quality monitoring | Excellent — asset checks, freshness policies |
| Event-driven ingestion | Good — sensors, Airbyte/Fivetran integration |
| Real-time streaming | Limited — designed for batch, not sub-second latency |
| Simple cron jobs | Overkill — use cron or a simpler scheduler |

## Dagster vs Alternatives

| Feature | Dagster | Airflow | Prefect |
|---------|---------|---------|---------|
| Core model | Asset-centric | Task-centric | Task-centric |
| Dependency tracking | Automatic lineage | Manual DAG wiring | Implicit |
| Testing | Direct invocation | Complex mocking | Direct invocation |
| Type safety | Pydantic config | Dict-based | Pydantic |
| UI | Asset catalog + lineage | Task-focused Gantt | Flow-focused dashboard |
| Local development | `dg dev` (instant) | Docker Compose | `prefect server start` |
| Partitioning | First-class (5+ types) | Manual | Basic |
| dbt integration | Native `@dbt_assets` | Operators | Blocks |
| Python version | 3.9–3.14 | 3.8–3.12 | 3.9–3.12 |
