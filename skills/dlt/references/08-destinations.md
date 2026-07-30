# dlt Destinations

> Source: https://dlthub.com/docs/dlt-ecosystem/destinations | dlt v1.29.1

## Table of Contents
- [Overview](#overview)
- [Destination Categories](#destination-categories)
- [Installation](#installation)
- [Common Configuration](#common-configuration)
- [DuckDB](#duckdb)
- [PostgreSQL](#postgresql)
- [BigQuery](#bigquery)
- [Snowflake](#snowflake)
- [Redshift](#redshift)
- [Filesystem](#filesystem)
- [Other Destinations](#other-destinations)
- [Staging](#staging)
- [Switching Destinations](#switching-destinations)

## Overview

dlt supports 26+ destinations. Switch between them by changing a single configuration value:

```python
pipeline = dlt.pipeline(destination="duckdb")   # Local development
pipeline = dlt.pipeline(destination="bigquery")  # Production
```

## Destination Categories

### Warehouses & Databases
BigQuery, Snowflake, Redshift, Databricks, ClickHouse, Postgres, MS SQL, Synapse, Athena, Fabric

### Local & Analytical
DuckDB, MotherDuck, DuckLake

### Storage & Lakes
Filesystem (S3/GCS/Azure), Delta Lake, Iceberg

### Vector & Search
Qdrant, Weaviate, LanceDB, Lance

### Generic & Custom
SQLAlchemy (any SQL database), Dremio, Hugging Face, Reverse ETL, Community destinations

## Installation

Install dlt with destination-specific extras:

```bash
pip install "dlt[duckdb]"
pip install "dlt[postgres]"
pip install "dlt[bigquery]"
pip install "dlt[snowflake]"
pip install "dlt[redshift]"
pip install "dlt[clickhouse]"
pip install "dlt[databricks]"
pip install "dlt[mssql]"
pip install "dlt[synapse]"
pip install "dlt[athena]"
pip install "dlt[filesystem]"
pip install "dlt[motherduck]"
pip install "dlt[qdrant]"
pip install "dlt[weaviate]"
pip install "dlt[lancedb]"
```

## Common Configuration

### Via secrets.toml
```toml
[destination.postgres.credentials]
user = "loader"
password = "secret"
host = "localhost"
port = 5432
database = "analytics"
```

### Via environment variables
```bash
export DESTINATION__POSTGRES__CREDENTIALS__USER="loader"
export DESTINATION__POSTGRES__CREDENTIALS__PASSWORD="secret"
```

### Via connection string
```toml
[destination.postgres]
credentials = "postgresql://loader:secret@localhost:5432/analytics"
```

## DuckDB

Local analytical database — ideal for development and prototyping:

```python
pipeline = dlt.pipeline(
    pipeline_name="demo",
    destination="duckdb",
    dataset_name="mydata"
)
```

Default creates a file at `{pipeline_name}.duckdb` in the working directory.

```python
# Custom file path
pipeline = dlt.pipeline(destination=dlt.destinations.duckdb("/path/to/my.duckdb"))

# In-memory database
pipeline = dlt.pipeline(destination=dlt.destinations.duckdb(":memory:"))
```

Query loaded data directly:
```python
with pipeline.sql_client() as client:
    result = client.execute_sql("SELECT * FROM mydata.users LIMIT 10")
    for row in result:
        print(row)
```

## PostgreSQL

```toml
# secrets.toml
[destination.postgres.credentials]
drivername = "postgresql"
username = "loader"
password = "secret"
host = "localhost"
port = 5432
database = "analytics"

# Or as connection string
[destination.postgres]
credentials = "postgresql://loader:secret@localhost:5432/analytics"
```

```python
pipeline = dlt.pipeline(destination="postgres", dataset_name="public_data")
```

## BigQuery

```toml
# secrets.toml
[destination.bigquery.credentials]
project_id = "my-gcp-project"
client_email = "loader@my-gcp-project.iam.gserviceaccount.com"
private_key = "-----BEGIN PRIVATE KEY-----\n..."
location = "US"
```

```python
pipeline = dlt.pipeline(destination="bigquery", dataset_name="analytics")
```

Or use Application Default Credentials:
```bash
gcloud auth application-default login
```

## Snowflake

```toml
# secrets.toml
[destination.snowflake.credentials]
database = "MY_DATABASE"
username = "MY_USER"
password = "MY_PASSWORD"
host = "account.snowflakecomputing.com"
warehouse = "MY_WAREHOUSE"
role = "MY_ROLE"
```

```python
pipeline = dlt.pipeline(destination="snowflake", dataset_name="analytics")
```

## Redshift

```toml
# secrets.toml
[destination.redshift.credentials]
database = "analytics"
username = "loader"
password = "secret"
host = "cluster.us-east-1.redshift.amazonaws.com"
port = 5439
```

## Filesystem

Load data as files to S3, GCS, Azure Blob, or local filesystem:

```toml
# secrets.toml
[destination.filesystem]
bucket_url = "s3://my-bucket/data"

[destination.filesystem.credentials]
aws_access_key_id = "AKIA..."
aws_secret_access_key = "secret"
```

```python
pipeline = dlt.pipeline(
    destination="filesystem",
    dataset_name="raw_data"
)
pipeline.run(data, table_name="events", loader_file_format="parquet")
```

Supported protocols: `s3://`, `gs://`, `az://`, `file://`, `memory://`

## Other Destinations

### ClickHouse
```python
pipeline = dlt.pipeline(destination="clickhouse")
```

### Databricks
```python
pipeline = dlt.pipeline(destination="databricks")
```

### MotherDuck (cloud DuckDB)
```python
pipeline = dlt.pipeline(destination="motherduck")
```

### SQLAlchemy (generic)
```python
pipeline = dlt.pipeline(
    destination=dlt.destinations.sqlalchemy("sqlite:///my.db")
)
```

### Vector databases
```python
pipeline = dlt.pipeline(destination="qdrant")
pipeline = dlt.pipeline(destination="weaviate")
pipeline = dlt.pipeline(destination="lancedb")
```

## Staging

Some destinations support staging through cloud storage for better performance:

```python
pipeline = dlt.pipeline(
    destination="bigquery",
    staging="filesystem"
)
```

```toml
# secrets.toml
[destination.filesystem]
bucket_url = "gs://my-staging-bucket"

[destination.filesystem.credentials]
project_id = "my-project"
client_email = "..."
private_key = "..."
```

Destinations supporting staging: BigQuery, Snowflake, Redshift, Databricks, Synapse, Athena.

## Switching Destinations

Switch from development (DuckDB) to production (BigQuery) by changing one value:

```python
import os

destination = os.getenv("DLT_DESTINATION", "duckdb")
pipeline = dlt.pipeline(
    pipeline_name="my_pipeline",
    destination=destination,
    dataset_name="analytics"
)
```

The same pipeline code, resources, and sources work across all destinations. Only credentials need updating per environment.
