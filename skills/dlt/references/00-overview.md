# dlt (data load tool) — Overview

> Source: https://dlthub.com/docs/intro | dlt v1.29.1

## Table of Contents
- [What is dlt](#what-is-dlt)
- [When to Use dlt](#when-to-use-dlt)
- [Core Architecture](#core-architecture)
- [Installation](#installation)
- [Quickstart](#quickstart)
- [Key Concepts](#key-concepts)
- [Supported Data Formats](#supported-data-formats)
- [Supported Destinations](#supported-destinations)

## What is dlt

dlt (data load tool) is an open-source Python library that makes data loading easy. It extracts data from messy sources — REST APIs, databases, files, DataFrames — and loads them into well-structured, live datasets in warehouses, lakes, or local engines.

Key characteristics:
- **Python-first**: runs wherever Python runs — locally, in notebooks, on orchestrators
- **No backend required**: no external APIs, containers, or infrastructure needed
- **Automatic schema inference**: reads source data, infers schemas, creates destination tables
- **Schema evolution**: automatically adapts to source data changes (new columns, tables)
- **Incremental loading**: loads only new or changed records using cursor fields or merge strategies
- **LLM-native design**: typed, declarative primitives support prompt-to-pipeline workflows

## When to Use dlt

**Use dlt when you need to:**
- Extract data from REST APIs and load into a warehouse
- Build lightweight ELT pipelines without heavy orchestration infrastructure
- Normalize nested JSON into relational tables automatically
- Implement incremental loading with deduplication
- Create data pipelines that an LLM/coding agent can generate
- Load data locally into DuckDB for analysis or prototyping

**Consider alternatives when:**
- You need a full-featured orchestrator (use Airflow/Dagster + dlt as the loader)
- You need real-time streaming (dlt is batch-oriented)
- You need a GUI-based ETL tool (use Airbyte, Fivetran)

## Core Architecture

dlt processes data through three discrete phases:

### 1. Extract
```python
pipeline.extract(data)
```
- Pulls data from sources to local disk as load packages
- Supports schema hints for column types
- Handles parallelization and item limiting
- Supports data obfuscation and column removal

### 2. Normalize
```python
pipeline.normalize()
```
- Inspects and normalizes extracted data
- Computes schema from input data structure
- Unnests nested data into child tables
- Creates variant columns for type inconsistencies
- Applies schema contracts

### 3. Load
```python
pipeline.load()
```
- Executes schema migrations on destination
- Loads data in parallel chunks (load jobs)
- Supports safe reruns on connection failures
- Creates internal schema and metadata tables

All three phases run automatically via `pipeline.run()`:
```python
import dlt

pipeline = dlt.pipeline(pipeline_name="demo", destination="duckdb")
info = pipeline.run(
    [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
    table_name="users"
)
print(info)
```

## Installation

Requires Python 3.10–3.14 (3.14 experimental).

```bash
# Using pip
pip install -U dlt

# Using uv (recommended)
uv pip install -U dlt

# With destination extras
pip install "dlt[duckdb]"
pip install "dlt[bigquery]"
pip install "dlt[snowflake]"
pip install "dlt[postgres]"
pip install "dlt[redshift]"
pip install "dlt[clickhouse]"
pip install "dlt[databricks]"

# Using pixi
pixi add dlt

# Using conda
conda install -c conda-forge dlt
```

## Quickstart

### Minimal Pipeline
```python
import dlt

pipeline = dlt.pipeline(
    pipeline_name="quick_start",
    destination="duckdb",
    dataset_name="mydata"
)

data = [
    {"id": 1, "name": "Alice", "tags": ["admin", "user"]},
    {"id": 2, "name": "Bob", "tags": ["user"]},
]

info = pipeline.run(data, table_name="users")
print(info)
```

### REST API Source
```python
import dlt
from dlt.sources.rest_api import rest_api_source

source = rest_api_source({
    "client": {"base_url": "https://pokeapi.co/api/v2/"},
    "resource_defaults": {
        "endpoint": {"params": {"limit": 100}},
        "write_disposition": "replace",
    },
    "resources": ["pokemon", "berry", "location"],
})

pipeline = dlt.pipeline(
    pipeline_name="pokemon",
    destination="duckdb",
    dataset_name="pokemon_data"
)
info = pipeline.run(source)
print(info)
```

### SQL Database Source
```python
import dlt
from dlt.sources.sql_database import sql_database

source = sql_database(
    credentials="postgresql://user:pass@host/db",
    table_names=["users", "orders"]
)

pipeline = dlt.pipeline(
    pipeline_name="pg_mirror",
    destination="duckdb",
    dataset_name="pg_data"
)
info = pipeline.run(source)
```

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Pipeline** | Orchestrates extract → normalize → load; holds state and schema |
| **Source** | Function decorated with `@dlt.source` that yields one or more resources |
| **Resource** | Function decorated with `@dlt.resource` that yields data items |
| **Transformer** | Resource that receives data from another resource via pipe `\|` |
| **Schema** | Auto-inferred table/column definitions; evolves with data |
| **Schema Contract** | Rules governing how schema can change (evolve/freeze/discard) |
| **Write Disposition** | How data is written: append, replace, or merge |
| **Incremental** | Tracks cursor values between runs for delta loading |
| **Destination** | Target system (DuckDB, BigQuery, Snowflake, Postgres, etc.) |
| **Load Package** | Unit of work containing extracted/normalized data files |

## Supported Data Formats

dlt accepts these input types:
- Python dicts and lists
- Generators and iterators
- Pandas DataFrames
- Arrow tables and RecordBatches
- Polars DataFrames
- Pydantic models

Output file formats: JSONL, Parquet, CSV (destination-dependent).

## Supported Destinations

**Warehouses & Databases:**
BigQuery, Snowflake, Redshift, Databricks, ClickHouse, Postgres, MS SQL, Synapse, Athena, Fabric, DuckDB, MotherDuck, DuckLake

**Vector & Search:**
Qdrant, Weaviate, LanceDB

**Storage & Lakes:**
Filesystem (S3/GCS/Azure), Delta Lake, Iceberg

**Other:**
Dremio, Hugging Face, SQLAlchemy (generic SQL), Reverse ETL, Community destinations

Switch destinations by changing a single configuration string:
```python
pipeline = dlt.pipeline(destination="bigquery")  # or "snowflake", "postgres", etc.
```
