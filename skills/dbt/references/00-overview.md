# dbt — Overview

> Source: https://docs.getdbt.com/docs/introduction

## Table of Contents
- [What is dbt](#what-is-dbt)
- [Core Value Propositions](#core-value-propositions)
- [How dbt Works](#how-dbt-works)
- [The dbt Framework](#the-dbt-framework)
- [Core Concepts](#core-concepts)
- [Installation](#installation)
- [Project Initialization](#project-initialization)
- [dbt Engines](#dbt-engines)
- [Workflow Overview](#workflow-overview)
- [When to Use dbt](#when-to-use-dbt)
- [Community and Ecosystem](#community-and-ecosystem)

## What is dbt

dbt (data build tool) is the industry standard for data transformation in the ELT (Extract, Load, Transform) paradigm. It enables data analysts and engineers to transform data in the warehouse using SQL `select` statements, applying software engineering practices like version control, testing, CI/CD, and documentation.

dbt handles the **T** in ELT — it does NOT extract or load data. Raw data is loaded by EL tools (Fivetran, Airbyte, Stitch), then dbt transforms it into analytics-ready tables.

**Key stats:**
- 40K+ GitHub stars on dbt-core
- 27,000+ companies using dbt
- 100,000+ member community

## Core Value Propositions

**No boilerplate** — Write business logic as SQL `select` statements. dbt handles DDL/DML (CREATE TABLE AS, INSERT, MERGE), transactions, and schema changes.

**Modular and reusable** — Models reference each other with `ref()`. Changes propagate to all dependencies automatically.

**Fast builds** — Incremental models process only new/changed data. State-aware builds skip unchanged models.

**Tested and documented** — Write data quality tests inline. Auto-generate documentation from YAML descriptions.

**Software engineering workflows** — Git version control, pull request reviews, CI/CD pipelines, package management.

**State-aware orchestration** — Detect changes and build only what's needed using dbt state comparison.

## How dbt Works

```
Raw Data (loaded by EL tools)
    ↓
dbt Models (SQL select statements)
    ↓ dbt handles: CREATE TABLE AS, INSERT, MERGE
Transformed Tables/Views in Warehouse
    ↓
BI Tools, Dashboards, Applications
```

Each model is a single `.sql` file containing a final `select` statement. When you run `dbt run`, dbt:

1. Parses all models and builds a DAG (directed acyclic graph)
2. Determines execution order based on dependencies
3. Compiles Jinja + SQL into pure SQL
4. Executes SQL against your data warehouse
5. Creates tables/views as configured

## The dbt Framework

### Language
- **SQL** — Standard `select` statements (the primary interface)
- **Jinja** — Templating for dynamic SQL, control flow, macros
- **YAML** — Configuration, tests, documentation, properties
- **Python** — Python models for ML/complex transforms (since dbt 1.3)

### Engines

| Engine | Runtime | Status | Best For |
|--------|---------|--------|----------|
| dbt Core v1 | Python | Stable (1.11.x) | Self-hosted, open-source |
| dbt Core v2 | Rust | Alpha (2.0.0a1) | Next-gen OSS foundation |
| dbt Fusion | Rust | Platform | Enterprise, IDE features |

## Core Concepts

| Concept | What It Does |
|---------|-------------|
| **Models** | SQL `select` statements that define transformations |
| **Sources** | Declarations of raw data tables loaded by EL tools |
| **Tests** | Assertions about data quality (unique, not_null, etc.) |
| **Seeds** | CSV files loaded into the warehouse |
| **Snapshots** | SCD Type 2 history tracking for mutable data |
| **Macros** | Reusable Jinja code (like functions) |
| **Packages** | Shared dbt projects with models and macros |
| **Materializations** | How models persist (table, view, incremental, ephemeral) |
| **Metrics** | Business KPIs defined in the Semantic Layer |
| **Exposures** | Declarations of downstream consumers (dashboards, apps) |

## Installation

### dbt Core (open-source, self-hosted)

```bash
# Install dbt-core with your warehouse adapter
pip install dbt-core dbt-postgres       # PostgreSQL
pip install dbt-core dbt-snowflake      # Snowflake
pip install dbt-core dbt-bigquery       # Google BigQuery
pip install dbt-core dbt-databricks     # Databricks
pip install dbt-core dbt-redshift       # Amazon Redshift
pip install dbt-core dbt-duckdb         # DuckDB (local dev)

# Verify installation
dbt --version
```

### Using uv (recommended for Python projects)

```bash
uv pip install dbt-core dbt-postgres
```

### Supported adapters

dbt supports 30+ data platforms including Snowflake, BigQuery, Databricks, Redshift, PostgreSQL, DuckDB, Trino, Spark, ClickHouse, and more. Community-maintained adapters cover additional platforms.

## Project Initialization

```bash
# Create a new project
dbt init my_project

# Follow prompts:
# - Select your warehouse adapter
# - Configure connection in ~/.dbt/profiles.yml

# Navigate to project
cd my_project

# Verify connection
dbt debug

# Install packages
dbt deps

# Run all models
dbt run

# Run tests
dbt test

# Build everything (run + test + seed + snapshot)
dbt build
```

### Minimal project structure

```
my_project/
├── dbt_project.yml          # Project configuration
├── profiles.yml              # (or in ~/.dbt/)
├── models/
│   ├── staging/              # Raw data cleanup
│   │   └── stg_orders.sql
│   └── marts/                # Business logic
│       └── customers.sql
├── tests/                    # Singular data tests
├── seeds/                    # CSV lookup tables
├── macros/                   # Reusable SQL/Jinja
├── snapshots/                # SCD Type 2 history
└── packages.yml              # Package dependencies
```

## dbt Engines

### dbt Core v1 (Stable — 1.11.x)

The original Python-based engine. Open-source (Apache 2.0), self-hosted.

```bash
pip install dbt-core==1.11.11
dbt run
```

### dbt Core v2 (Alpha — 2.0.0a1)

Ground-up rewrite in Rust. Dramatically faster parsing and compilation. Ships as a single binary — no Python runtime needed.

```bash
pip install dbt-core==2.0.0a1
```

### dbt Fusion Engine (Platform)

Proprietary Rust-based engine with advanced features: native SQL comprehension, LSP support, instant feedback, cost optimization. Available via dbt Cloud platform and VS Code extension.

## Workflow Overview

### Development cycle

```bash
# 1. Write/edit a model
# models/marts/customers.sql

# 2. Compile to check SQL
dbt compile --select customers

# 3. Run the model
dbt run --select customers

# 4. Test the model
dbt test --select customers

# 5. Generate docs
dbt docs generate
dbt docs serve

# 6. Commit and push
git add . && git commit -m "Add customers model"
```

### Production deployment

```bash
# Full build (models + tests + seeds + snapshots)
dbt build

# Or step by step
dbt seed                    # Load CSV seeds
dbt snapshot                # Capture SCD history
dbt run                     # Run models
dbt test                    # Validate data

# State-aware (only changed models)
dbt build --select state:modified+
```

## When to Use dbt

**Use dbt when:**
- You have an ELT pipeline and need to transform data in the warehouse
- Multiple analysts/engineers work on the same data models
- You need version-controlled, tested, documented transformations
- Your transformation logic is primarily SQL-based
- You want reproducible, CI/CD-tested data pipelines

**Don't use dbt for:**
- Extract and Load (use Fivetran, Airbyte, Stitch)
- Real-time streaming transforms (use Kafka, Flink)
- Application-level queries (use your ORM)
- One-off ad-hoc queries (use your SQL editor directly)

## Community and Ecosystem

- **dbt Hub** — Package registry at [hub.getdbt.com](https://hub.getdbt.com)
- **dbt Community** — Forum at [discourse.getdbt.com](https://discourse.getdbt.com)
- **dbt Learn** — Free courses at [learn.getdbt.com](https://learn.getdbt.com)
- **dbt Certification** — Analytics Engineering Certification
- **Jaffle Shop** — Sample project for learning dbt
- **Popular packages**: dbt-utils, dbt-expectations, codegen, audit_helper
