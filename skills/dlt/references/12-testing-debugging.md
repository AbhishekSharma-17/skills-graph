# dlt Testing & Debugging

> Source: https://dlthub.com/docs | dlt v1.29.1

## Table of Contents
- [Testing Pipelines](#testing-pipelines)
- [Development Mode](#development-mode)
- [Inspecting Load Results](#inspecting-load-results)
- [Schema Inspection](#schema-inspection)
- [Querying Loaded Data](#querying-loaded-data)
- [Debugging Extract](#debugging-extract)
- [Debugging Normalize](#debugging-normalize)
- [Debugging Load](#debugging-load)
- [Pipeline State](#pipeline-state)
- [Common Issues](#common-issues)
- [Logging](#logging)

## Testing Pipelines

### Unit testing with DuckDB
```python
import pytest
import dlt

def test_my_pipeline():
    pipeline = dlt.pipeline(
        pipeline_name="test_pipeline",
        destination="duckdb",
        dataset_name="test_data",
        dev_mode=True  # Unique dataset per run
    )

    @dlt.resource
    def test_data():
        yield [{"id": 1, "name": "test"}]

    info = pipeline.run(test_data())

    assert not info.has_failed_jobs
    assert not info.is_empty

    with pipeline.sql_client() as client:
        result = client.execute_sql("SELECT COUNT(*) FROM test_data")
        assert result[0][0] == 1
```

### Testing resources in isolation
```python
def test_resource_output():
    @dlt.resource
    def users():
        yield [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]

    items = list(users())
    assert len(items) == 2
    assert items[0]["name"] == "Alice"
```

### Testing with schema contracts
```python
def test_schema_contract_freeze():
    pipeline = dlt.pipeline(
        pipeline_name="test_contract",
        destination="duckdb",
        dev_mode=True
    )

    @dlt.resource(columns={"id": {"data_type": "bigint"}})
    def strict_data():
        yield [{"id": 1}]

    # First run establishes schema
    pipeline.run(strict_data())

    # Second run with extra column should fail in freeze mode
    @dlt.resource(name="strict_data")
    def extra_column():
        yield [{"id": 2, "new_col": "surprise"}]

    from dlt.pipeline.exceptions import PipelineStepFailed
    with pytest.raises(PipelineStepFailed):
        pipeline.run(extra_column(), schema_contract="freeze")
```

### Testing incremental loading
```python
def test_incremental():
    pipeline = dlt.pipeline(
        pipeline_name="test_incr",
        destination="duckdb",
        dev_mode=True
    )

    @dlt.resource(primary_key="id")
    def events(
        updated_at=dlt.sources.incremental("updated_at", initial_value=0)
    ):
        yield [
            {"id": 1, "updated_at": 1, "data": "a"},
            {"id": 2, "updated_at": 2, "data": "b"},
        ]

    # First run loads both
    info = pipeline.run(events())
    with pipeline.sql_client() as c:
        assert c.execute_sql("SELECT COUNT(*) FROM events")[0][0] == 2

    # Second run with same data loads nothing (deduplicated)
    info = pipeline.run(events())
    with pipeline.sql_client() as c:
        assert c.execute_sql("SELECT COUNT(*) FROM events")[0][0] == 2
```

## Development Mode

Enable `dev_mode` to create unique datasets per run:

```python
pipeline = dlt.pipeline(
    pipeline_name="experiment",
    destination="duckdb",
    dev_mode=True  # Adds datetime suffix to dataset_name
)
```

This prevents interfering with existing data during development.

## Inspecting Load Results

### LoadInfo object
```python
info = pipeline.run(source())

# Human-readable summary
print(info)

# Check for empty loads
if info.is_empty:
    print("No data was loaded")

# Check for failures
if info.has_failed_jobs:
    for pkg in info.load_packages:
        for job in pkg.jobs.get("failed_jobs", []):
            print(f"Failed: {job.file_path}")
            print(f"Error: {job.failed_message}")

# Raise exception on any failure
info.raise_on_failed_jobs()

# Access metrics
print(info.metrics)
```

### Load package details
```python
for package in info.load_packages:
    print(f"Package: {package.load_id}")
    print(f"State: {package.state}")
    print(f"Schema: {package.schema_name}")
    for table_name, table in package.schema_update.items():
        print(f"  Table: {table_name}")
        for col_name, col in table.get("columns", {}).items():
            print(f"    Column: {col_name} ({col.get('data_type')})")
```

## Schema Inspection

### View current schema
```python
schema = pipeline.default_schema

# All tables
for table_name, table in schema.tables.items():
    print(f"\n{table_name}:")
    for col_name, col in table.get("columns", {}).items():
        print(f"  {col_name}: {col.get('data_type')} "
              f"{'PK' if col.get('primary_key') else ''} "
              f"{'NOT NULL' if not col.get('nullable', True) else ''}")
```

### Export schema
```python
# As YAML
print(pipeline.default_schema.to_pretty_yaml())

# As dict
schema_dict = pipeline.default_schema.to_dict()
```

### Schema versioning
```python
print(f"Schema version: {pipeline.default_schema.version}")
print(f"Schema hash: {pipeline.default_schema.version_hash}")
```

## Querying Loaded Data

### SQL client
```python
with pipeline.sql_client() as client:
    # Simple query
    rows = client.execute_sql("SELECT * FROM users LIMIT 10")
    for row in rows:
        print(row)

    # Parameterized query
    rows = client.execute_sql(
        "SELECT * FROM users WHERE id = %s", 42
    )
```

### Dataset API
```python
dataset = pipeline.dataset()

# As Pandas DataFrame
df = dataset["users"].df()
print(df.head())

# As Arrow table
arrow_table = dataset["users"].arrow()

# With SQL
result = dataset.sql("SELECT name, COUNT(*) FROM users GROUP BY name")
```

## Debugging Extract

### Run extract phase only
```python
pipeline.extract(source(), loader_file_format="jsonl")
# Inspect extracted files in pipeline working directory
```

### List resource items without loading
```python
@dlt.resource
def debug_resource():
    yield [{"id": 1}, {"id": 2}]

# Iterate without pipeline
for item in debug_resource():
    print(item)
```

### FIFO mode for debugging
```toml
# config.toml
[sources.my_pipeline.extract]
next_item_mode = "fifo"
```

Processes each resource completely before starting the next — easier to trace.

## Debugging Normalize

### Run normalize separately
```python
# After extract
normalize_info = pipeline.normalize()
print(normalize_info)
```

### Inspect normalized files
Check the pipeline working directory at `~/.dlt/pipelines/<name>/` for normalized load packages.

## Debugging Load

### Run load separately
```python
load_info = pipeline.load()
print(load_info)

# Check for failed jobs
if load_info.has_failed_jobs:
    for pkg in load_info.load_packages:
        for job in pkg.jobs.get("failed_jobs", []):
            print(f"Error: {job.failed_message}")
```

## Pipeline State

### Inspect pipeline state
```python
# Current state
state = pipeline.state

# Incremental cursor values
sources_state = state.get("sources", {})
for source_name, source_state in sources_state.items():
    resources = source_state.get("resources", {})
    for resource_name, resource_state in resources.items():
        incremental = resource_state.get("incremental", {})
        for cursor_name, cursor_state in incremental.items():
            print(f"{source_name}.{resource_name}.{cursor_name}: "
                  f"{cursor_state.get('last_value')}")
```

### Drop pipeline state
```python
pipeline.drop()  # Removes working directory entirely
```

## Common Issues

### "ConfigFieldMissingException"
Missing credentials. Check environment variables and secrets.toml:
```bash
export DESTINATION__POSTGRES__CREDENTIALS="postgresql://..."
```

### "PipelineStepFailed" during normalize
Usually a schema contract violation. Check the error's `__context__` for `DataValidationError`:
```python
try:
    pipeline.run(source())
except PipelineStepFailed as e:
    if e.step == "normalize":
        print(f"Schema error: {e.__context__}")
```

### Duplicate data after re-runs
Ensure you're using `primary_key` with merge write disposition, or enable deduplication via `dlt.sources.incremental`.

### Slow extraction
- Yield batches instead of individual items
- Enable `parallelized=True` on resources
- Use async resources for I/O-bound work

### Out of memory
- Reduce `buffer_max_items` in config.toml
- Enable file rotation with `file_max_items` or `file_max_bytes`
- Yield smaller batches

## Logging

### Configure log level
```toml
# config.toml
[runtime]
log_level = "DEBUG"  # DEBUG, INFO, WARNING, ERROR
```

### Via environment variable
```bash
export RUNTIME__LOG_LEVEL=DEBUG
```

### Progress-based logging
```python
pipeline = dlt.pipeline(progress="log")
```

### Structured logging with dlt.current
```python
@dlt.resource
def my_resource():
    logger = dlt.current.resource_state()
    # Access current pipeline context for debugging
    print(f"Pipeline: {dlt.current.pipeline().pipeline_name}")
    yield data
```
