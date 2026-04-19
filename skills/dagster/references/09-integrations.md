# Dagster — Integrations

> Source: [docs.dagster.io/integrations](https://docs.dagster.io/integrations)

## Table of Contents

- [dbt](#dbt)
- [Snowflake](#snowflake)
- [BigQuery](#bigquery)
- [DuckDB](#duckdb)
- [Polars](#polars)
- [AWS S3](#aws-s3)
- [Google Cloud Storage](#google-cloud-storage)
- [Airbyte](#airbyte)
- [Fivetran](#fivetran)
- [Integration Packages](#integration-packages)

---

## dbt

```bash
pip install dagster-dbt
```

### @dbt_assets decorator

```python
from pathlib import Path
from dagster import AssetExecutionContext, Definitions
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

my_dbt_project = DbtProject(project_dir=Path("path/to/dbt_project"))
my_dbt_project.prepare_if_dev()

@dbt_assets(manifest=my_dbt_project.manifest_path)
def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()

defs = Definitions(
    assets=[my_dbt_assets],
    resources={"dbt": DbtCliResource(project_dir=my_dbt_project)},
)
```

### Custom asset keys via translator

```python
from dagster import AssetKey
from dagster_dbt import DagsterDbtTranslator

class CustomTranslator(DagsterDbtTranslator):
    def get_asset_key(self, dbt_resource_props):
        return super().get_asset_key(dbt_resource_props).with_prefix("snowflake")

@dbt_assets(
    manifest=my_dbt_project.manifest_path,
    dagster_dbt_translator=CustomTranslator(),
)
def prefixed_dbt_assets(context, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()
```

### Partitioned incremental models

```python
import json
from dagster import DailyPartitionsDefinition

@dbt_assets(
    manifest=my_dbt_project.manifest_path,
    partitions_def=DailyPartitionsDefinition(start_date="2023-01-01"),
)
def partitioned_dbt(context, dbt: DbtCliResource):
    start, end = context.partition_time_window
    dbt_vars = {"min_date": start.isoformat(), "max_date": end.isoformat()}
    yield from dbt.cli(
        ["build", "--vars", json.dumps(dbt_vars)], context=context
    ).stream()
```

### Schedule from dbt selection

```python
from dagster_dbt import build_schedule_from_dbt_selection

daily_schedule = build_schedule_from_dbt_selection(
    [my_dbt_assets],
    job_name="daily_dbt_models",
    cron_schedule="@daily",
    dbt_select="tag:daily",
)
```

## Snowflake

```bash
pip install dagster-snowflake dagster-snowflake-pandas
```

### SnowflakePandasIOManager

```python
from dagster_snowflake_pandas import SnowflakePandasIOManager
from dagster import Definitions, EnvVar
import pandas as pd

@dg.asset
def iris_dataset() -> pd.DataFrame:
    return pd.read_csv("https://example.com/iris.csv")

defs = Definitions(
    assets=[iris_dataset],
    resources={
        "io_manager": SnowflakePandasIOManager(
            account="abc1234.us-east-1",
            user=EnvVar("SNOWFLAKE_USER"),
            password=EnvVar("SNOWFLAKE_PASSWORD"),
            database="ANALYTICS",
            warehouse="COMPUTE_WH",
            schema="PUBLIC",
        )
    },
)
```

Also available: `SnowflakePySparkIOManager`, `SnowflakePolarsIOManager`.

## BigQuery

```bash
pip install dagster-gcp dagster-gcp-pandas
```

### BigQueryPandasIOManager

```python
from dagster_gcp_pandas import BigQueryPandasIOManager

defs = dg.Definitions(
    assets=[my_assets],
    resources={
        "io_manager": BigQueryPandasIOManager(
            project="my-gcp-project",
            location="us-east5",
            dataset="ANALYTICS",
            timeout=15.0,
        )
    },
)
```

### BigQueryResource (direct SQL)

```python
from dagster_gcp import BigQueryResource

@dg.asset
def bq_data(bigquery: BigQueryResource) -> None:
    with bigquery.get_client() as client:
        results = client.query("SELECT * FROM dataset.table").result()
```

## DuckDB

```bash
pip install dagster-duckdb-pandas
```

```python
from dagster_duckdb_pandas import DuckDBPandasIOManager

@dg.asset(key_prefix=["analytics"])
def my_table() -> pd.DataFrame:
    return pd.DataFrame({"col": [1, 2, 3]})

defs = dg.Definitions(
    assets=[my_table],
    resources={
        "io_manager": DuckDBPandasIOManager(
            database="warehouse.duckdb",
            schema="PUBLIC",
        )
    },
)
```

Also available: `DuckDBPolarsIOManager`, `DuckDBPySparkIOManager`.

## Polars

```bash
pip install dagster-polars
```

```python
import polars as pl
from dagster_polars import PolarsParquetIOManager

@dg.asset(io_manager_key="polars_io")
def upstream() -> pl.DataFrame:
    return pl.DataFrame({"foo": [1, 2, 3]})

@dg.asset(io_manager_key="polars_io")
def downstream(upstream: pl.LazyFrame) -> pl.LazyFrame:
    return upstream.filter(pl.col("foo") > 1)

defs = dg.Definitions(
    assets=[upstream, downstream],
    resources={"polars_io": PolarsParquetIOManager()},
)
```

Supports: Parquet, Delta Lake, BigQuery serialization. Filesystems: local, S3, GCS.

## AWS S3

```bash
pip install dagster-aws
```

### S3PickleIOManager

```python
from dagster_aws.s3 import S3PickleIOManager, S3Resource

defs = dg.Definitions(
    resources={
        "io_manager": S3PickleIOManager(
            s3_resource=S3Resource(region_name="us-west-1"),
            s3_bucket="my-dagster-bucket",
            s3_prefix="assets",
        ),
    },
)
```

### S3Resource (direct access)

```python
from dagster_aws.s3 import S3Resource

@dg.asset
def upload_to_s3(s3: S3Resource):
    client = s3.get_client()
    client.upload_file("local.csv", "my-bucket", "remote.csv")
```

## Google Cloud Storage

```bash
pip install dagster-gcp
```

```python
from dagster_gcp.gcs import GCSResource

@dg.asset
def gcs_upload(gcs: GCSResource):
    client = gcs.get_client()
    bucket = client.bucket("my-bucket")
    blob = bucket.blob("path/to/data.csv")
    blob.upload_from_string(csv_data)
```

Also provides `GCSPickleIOManager`.

## Airbyte

```bash
pip install dagster-airbyte
```

```python
from dagster_airbyte import AirbyteWorkspace, build_airbyte_assets_definitions

airbyte_workspace = AirbyteWorkspace(
    rest_api_base_url="http://localhost:8000/api/public/v1",
    workspace_id=dg.EnvVar("AIRBYTE_WORKSPACE_ID"),
    username="airbyte",
    password=dg.EnvVar("AIRBYTE_PASSWORD"),
)

airbyte_assets = build_airbyte_assets_definitions(workspace=airbyte_workspace)

defs = dg.Definitions(
    assets=airbyte_assets,
    resources={"airbyte": airbyte_workspace},
)
```

## Fivetran

```bash
pip install dagster-fivetran
```

```python
from dagster_fivetran import FivetranResource, load_assets_from_fivetran_instance

fivetran = FivetranResource(
    api_key="key",
    api_secret=dg.EnvVar("FIVETRAN_SECRET"),
)
fivetran_assets = load_assets_from_fivetran_instance(fivetran)
```

## Integration Packages

| Package | Integration |
|---------|------------|
| `dagster-dbt` | dbt Core/Cloud |
| `dagster-snowflake` | Snowflake |
| `dagster-gcp` | BigQuery, GCS, Dataproc |
| `dagster-duckdb` | DuckDB |
| `dagster-polars` | Polars DataFrames |
| `dagster-aws` | S3, Lambda, ECS, EMR |
| `dagster-airbyte` | Airbyte |
| `dagster-fivetran` | Fivetran |
| `dagster-openai` | OpenAI API |
| `dagster-databricks` | Databricks |
| `dagster-k8s` | Kubernetes |
| `dagster-docker` | Docker |
| `dagster-postgres` | PostgreSQL (metadata DB) |
| `dagster-pandas` | Pandas type validation |
| `dagster-pyspark` | PySpark |
| `dagster-celery-k8s` | Celery + K8s executor |
