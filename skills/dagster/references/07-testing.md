# Dagster — Testing

> Source: [docs.dagster.io/guides/test](https://docs.dagster.io/guides/test/unit-testing-assets-and-ops)

## Table of Contents

- [Testing Assets](#testing-assets)
- [Testing with Resources](#testing-with-resources)
- [Testing with Context](#testing-with-context)
- [Testing Multi-Assets](#testing-multi-assets)
- [Testing Ops](#testing-ops)
- [Testing Partitioned Assets](#testing-partitioned-assets)
- [Testing Schedules and Sensors](#testing-schedules-and-sensors)
- [Validating Definitions](#validating-definitions)
- [Integration Testing](#integration-testing)
- [Best Practices](#best-practices)

---

## Testing Assets

### Direct invocation (recommended)

Call asset functions directly, passing mock inputs as arguments:

```python
import dagster as dg

@dg.asset
def raw_data() -> list[dict]:
    return [{"id": 1, "value": 100}]

@dg.asset
def processed_data(raw_data: list[dict]) -> list[dict]:
    return [{"id": r["id"], "doubled": r["value"] * 2} for r in raw_data]

def test_raw_data():
    result = raw_data()
    assert len(result) == 1
    assert result[0]["id"] == 1

def test_processed_data():
    mock_input = [{"id": 1, "value": 50}]
    result = processed_data(mock_input)
    assert result[0]["doubled"] == 100
```

### Testing with config

```python
class FilepathConfig(dg.Config):
    path: str

@dg.asset
def loaded_file(config: FilepathConfig) -> str:
    with open(config.path) as f:
        return f.read()

def test_loaded_file(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello")
    result = loaded_file(FilepathConfig(path=str(test_file)))
    assert result == "hello"
```

## Testing with Resources

### Mock resource pattern

```python
from unittest import mock

class S3Resource(dg.ConfigurableResource):
    bucket: str
    def read(self, key: str) -> str: ...

@dg.asset
def s3_data(s3: S3Resource) -> str:
    return s3.read("data.csv")

def test_s3_data():
    mocked_s3 = mock.Mock(spec=S3Resource)
    mocked_s3.read.return_value = "col1,col2\n1,2"
    result = s3_data(mocked_s3)
    assert "col1" in result
```

### Environment substitution pattern

Use different resource instances for test vs production:

```python
class DatabaseResource(dg.ConfigurableResource):
    connection_url: str
    def query(self, sql: str): ...

def test_with_sandbox_db():
    test_defs = dg.Definitions(
        assets=[my_asset],
        resources={"db": DatabaseResource(connection_url="sqlite:///test.db")},
    )
    job = test_defs.get_implicit_global_asset_job_def()
    assert job.execute_in_process().success
```

## Testing with Context

Use `build_asset_context` when assets access `context`:

```python
@dg.asset(partitions_def=dg.DailyPartitionsDefinition("2024-01-01"))
def daily_asset(context: dg.AssetExecutionContext) -> str:
    return f"data for {context.partition_key}"

def test_daily_asset():
    context = dg.build_asset_context(partition_key="2024-01-15")
    result = daily_asset(context)
    assert result == "data for 2024-01-15"
```

## Testing Multi-Assets

Use a mock I/O manager to supply upstream data:

```python
import pandas as pd

class MockIOManager(dg.IOManager):
    def __init__(self, data: dict):
        self._data = data

    def load_input(self, context):
        return self._data[tuple(context.asset_key.path)]

    def handle_output(self, context, obj):
        pass

@dg.multi_asset(
    specs=[
        dg.AssetSpec("summary", deps=["raw_data"]),
        dg.AssetSpec("metrics", deps=["raw_data"]),
    ]
)
def compute_assets(raw_data: pd.DataFrame):
    yield dg.MaterializeResult(asset_key="summary", metadata={"rows": len(raw_data)})
    yield dg.MaterializeResult(asset_key="metrics", metadata={"cols": len(raw_data.columns)})

def test_compute_assets():
    test_df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    source = dg.SourceAsset(key="raw_data")

    defs = dg.Definitions(
        assets=[source, compute_assets],
        resources={"io_manager": MockIOManager({("raw_data",): test_df})},
    )
    job = defs.get_implicit_global_asset_job_def()
    result = job.execute_in_process(
        asset_selection=[dg.AssetKey("summary"), dg.AssetKey("metrics")]
    )
    assert result.success
```

## Testing Ops

```python
@dg.op
def add_one(x: int) -> int:
    return x + 1

def test_add_one():
    assert add_one(5) == 6

@dg.op
def logging_op(context: dg.OpExecutionContext, x: int) -> int:
    context.log.info(f"Processing {x}")
    return x + 1

def test_logging_op():
    context = dg.build_op_context()
    assert logging_op(context, 5) == 6
```

### Testing jobs

```python
@dg.job
def my_job():
    add_one(return_five())

def test_job():
    result = my_job.execute_in_process()
    assert result.success
    assert result.output_for_node("add_one") == 6
```

## Testing Partitioned Assets

```python
@dg.daily_partitioned_config(start_date="2024-01-01")
def my_config(start, _end):
    return {"ops": {"process": {"config": {"date": start.strftime("%Y-%m-%d")}}}}

def test_partitioned_config():
    from datetime import datetime
    config = my_config(datetime(2024, 1, 15), datetime(2024, 1, 16))
    assert config["ops"]["process"]["config"]["date"] == "2024-01-15"

def test_partitioned_job():
    result = my_job.execute_in_process(partition_key="2024-01-15")
    assert result.success
```

## Testing Schedules and Sensors

```python
def test_sensor():
    context = dg.build_sensor_context(cursor="0")
    result = my_sensor(context)
    assert isinstance(result, (dg.RunRequest, dg.SkipReason, dg.SensorResult))

def test_schedule():
    from datetime import datetime
    context = dg.build_schedule_context(
        scheduled_execution_time=datetime(2024, 1, 15)
    )
    result = my_schedule(context)
    assert isinstance(result, dg.RunRequest)
```

## Validating Definitions

Catch misconfigurations before deployment:

```python
def test_definitions_loadable():
    from my_project.definitions import defs
    defs.validate_loadable()
```

This checks: resource requirements satisfied, no conflicting keys, valid partition mappings, all references resolve.

## Integration Testing

### execute_in_process (full pipeline test)

```python
def test_full_pipeline():
    defs = dg.Definitions(
        assets=[raw_data, cleaned_data, report],
        resources={"io_manager": dg.InMemoryIOManager()},
    )
    job = defs.get_implicit_global_asset_job_def()
    result = job.execute_in_process()
    assert result.success
```

### materialize (asset-focused)

```python
def test_materialize():
    result = dg.materialize(
        [raw_data, cleaned_data],
        resources={"io_manager": dg.InMemoryIOManager()},
    )
    assert result.success
```

## Best Practices

- **Test individual assets, not entire jobs** — faster feedback, better isolation.
- **Direct invocation is preferred** over `execute_in_process` for unit tests.
- **Use `mock.Mock(spec=ResourceClass)`** to enforce the resource's interface in mocks.
- **`build_asset_context()` is only needed** when the asset uses `context` — skip it for data-only inputs.
- **Always call `validate_loadable()` in CI** to catch resource mismatches and duplicate keys.
- **Mock only external boundaries** (resources, I/O managers) — never mock internal functions.
- **Use `InMemoryIOManager`** for integration tests to avoid filesystem side effects.
