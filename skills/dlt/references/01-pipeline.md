# dlt Pipeline

> Source: https://dlthub.com/docs/general-usage/pipeline | dlt v1.29.1

## Table of Contents
- [Creating a Pipeline](#creating-a-pipeline)
- [Pipeline Parameters](#pipeline-parameters)
- [Running a Pipeline](#running-a-pipeline)
- [Write Dispositions](#write-dispositions)
- [Refresh Modes](#refresh-modes)
- [Pipeline Phases](#pipeline-phases)
- [Load Info and Traces](#load-info-and-traces)
- [Progress Monitoring](#progress-monitoring)
- [Working Directory](#working-directory)
- [Attaching to Existing Pipelines](#attaching-to-existing-pipelines)

## Creating a Pipeline

```python
import dlt

pipeline = dlt.pipeline(
    pipeline_name="my_pipeline",
    destination="duckdb",
    dataset_name="my_dataset"
)
```

## Pipeline Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `pipeline_name` | str | auto from filename | Identifies pipeline in traces and monitoring |
| `destination` | str | None | Target system ("duckdb", "bigquery", "snowflake", etc.) |
| `dataset_name` | str | `{pipeline_name}_dataset` | Logical schema grouping in destination |
| `pipelines_dir` | str | `~/.dlt/pipelines/` | Working directory for pipeline state |
| `dev_mode` | bool | False | Adds datetime suffix to dataset name for experiments |
| `full_refresh` | bool | False | Deprecated; use `dev_mode` |
| `progress` | str | None | Progress monitor ("log", "tqdm", "enlighten", "alive_progress") |

```python
pipeline = dlt.pipeline(
    pipeline_name="production_load",
    destination="bigquery",
    dataset_name="analytics",
    dev_mode=False,
    progress="log"
)
```

## Running a Pipeline

### pipeline.run()

The `run()` method executes all three phases (extract → normalize → load):

```python
info = pipeline.run(
    data,                              # Source, resource, generator, or iterable
    table_name="my_table",             # Table name (required if not inferrable)
    write_disposition="append",         # append | replace | merge
    primary_key="id",                  # For merge deduplication
    schema=my_schema,                  # Custom schema object
    loader_file_format="parquet",      # jsonl | parquet | csv
)
```

### Loading Different Data Types

```python
# List of dicts
pipeline.run([{"id": 1}, {"id": 2}], table_name="items")

# Generator function
def generate():
    for i in range(100):
        yield {"id": i, "value": f"item_{i}"}
pipeline.run(generate(), table_name="items")

# dlt resource
@dlt.resource
def my_data():
    yield {"id": 1}
pipeline.run(my_data())

# dlt source
@dlt.source
def my_source():
    return [resource_a(), resource_b()]
pipeline.run(my_source())

# Pandas DataFrame
import pandas as pd
df = pd.DataFrame({"id": [1, 2], "name": ["a", "b"]})
pipeline.run(df, table_name="from_pandas")
```

## Write Dispositions

### append (default)
Adds new data to the end of existing tables:
```python
pipeline.run(data, table_name="events", write_disposition="append")
```

### replace
Overwrites existing table contents:
```python
pipeline.run(data, table_name="dim_products", write_disposition="replace")
```

### merge
Updates records based on primary_key and/or merge_key:
```python
pipeline.run(
    data,
    table_name="users",
    write_disposition="merge",
    primary_key="user_id"
)
```

Merge strategies:
- **delete-insert** (default): deletes matching rows, inserts new ones
- **upsert**: updates existing rows, inserts new ones
- **scd2**: tracks historical changes with validity columns

## Refresh Modes

Reset pipeline state and destination data:

```python
# Truncate tables, reset incremental state
pipeline.run(source(), refresh="drop_data")

# Drop and recreate tables for specific resources, reset state
pipeline.run(source().with_resources("users"), refresh="drop_resources")

# Full reset — drop all source tables and state
pipeline.run(source(), refresh="drop_sources")
```

| Mode | Tables | Schema | State |
|------|--------|--------|-------|
| `drop_data` | Truncated | Preserved | Reset |
| `drop_resources` | Dropped + recreated | Reset for resource | Reset |
| `drop_sources` | Dropped + recreated | Fully reset | Reset |

## Pipeline Phases

Run phases independently for fine-grained control:

```python
# Extract only
pipeline.extract(data, table_name="items", loader_file_format="jsonl")

# Normalize extracted data
normalize_info = pipeline.normalize()
print(normalize_info)

# Load normalized data
load_info = pipeline.load()
print(load_info)
```

This is useful for:
- Debugging each phase separately
- Running normalize/load on pre-extracted data
- Implementing custom logic between phases

## Load Info and Traces

The `run()` method returns a `LoadInfo` object:

```python
info = pipeline.run(data, table_name="events")

# Check if load produced data
if info.is_empty:
    print("No data loaded")

# Print human-readable summary
print(info)

# Access metrics
print(info.metrics)

# Check for errors
if info.has_failed_jobs:
    for job in info.load_packages[0].jobs["failed_jobs"]:
        print(f"Failed: {job.file_path}, Error: {job.failed_message}")

# Raise on any failures
info.raise_on_failed_jobs()
```

## Progress Monitoring

```python
# Built-in progress bars
pipeline = dlt.pipeline(progress="tqdm")         # tqdm progress bar
pipeline = dlt.pipeline(progress="enlighten")    # enlighten progress bar
pipeline = dlt.pipeline(progress="alive_progress")

# Logging (recommended for production)
pipeline = dlt.pipeline(progress="log")

# Custom log interval
pipeline = dlt.pipeline(
    progress=dlt.progress.log(log_period=60, logger=my_logger.info)
)
```

## Working Directory

Pipeline state is stored at `~/.dlt/pipelines/<pipeline_name>/`:
- Extracted files and load packages
- Schemas (current and historical)
- Pipeline traces
- State (incremental cursors, resource state)

Override the default:
```python
pipeline = dlt.pipeline(
    pipeline_name="my_pipe",
    destination="duckdb",
    pipelines_dir="/custom/path/pipelines"
)
```

Or via environment variable:
```bash
export DLT_DATA_DIR="/path/to/dlt_data"
```

## Attaching to Existing Pipelines

Reconnect to a pipeline's working directory without overriding destination:

```python
pipeline = dlt.attach(pipeline_name="my_pipe")
# or with explicit directory
pipeline = dlt.attach(pipeline_name="my_pipe", pipelines_dir="/custom/path")
```

This is useful for inspecting state, schemas, or rerunning load on previously extracted data.
