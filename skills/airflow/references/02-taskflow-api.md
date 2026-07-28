# TaskFlow API

> Source: [airflow.apache.org/docs/…/taskflow](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/taskflow.html) · v3.3.0

## Table of Contents

- [Overview](#overview)
- [The @task Decorator](#the-task-decorator)
- [The @dag Decorator](#the-dag-decorator)
- [Passing Data Between Tasks](#passing-data-between-tasks)
- [Multiple Outputs](#multiple-outputs)
- [Accessing Context](#accessing-context)
- [Specialized Decorators](#specialized-decorators)
- [Conditional Execution](#conditional-execution)
- [Task Groups](#task-groups)
- [Custom Object Serialization](#custom-object-serialization)
- [Logging](#logging)

## Overview

The TaskFlow API provides a Pythonic way to author DAGs using decorators instead of manually instantiating operators and managing XCom. Data flows between tasks by passing function return values as arguments — Airflow handles XCom serialization and dependency wiring automatically.

```python
from airflow.sdk import dag, task

@dag(schedule="@daily", start_date=pendulum.datetime(2024, 1, 1, tz="UTC"), catchup=False)
def etl():
    @task()
    def extract():
        return {"users": 1000, "orders": 5000}

    @task()
    def transform(raw: dict):
        return {"total_records": raw["users"] + raw["orders"]}

    @task()
    def load(summary: dict):
        print(f"Loading {summary['total_records']} records")

    raw = extract()
    summary = transform(raw)
    load(summary)

etl()
```

## The @task Decorator

Converts a Python function into an Airflow task. The function body executes at runtime on a worker, not during DAG parsing.

```python
from airflow.sdk import task

@task(
    task_id="custom_id",          # Override auto-generated ID (default: function name)
    retries=3,                     # Retry on failure
    retry_delay=timedelta(minutes=5),
    execution_timeout=timedelta(hours=1),
    pool="data_processing",        # Resource pool
    queue="heavy_tasks",           # Celery queue
    max_active_tis_per_dag=4,      # Concurrency limit
    do_xcom_push=True,             # Push return value to XCom (default)
    multiple_outputs=False,        # Expand dict return into multiple XCom keys
    trigger_rule="all_success",    # When to run relative to upstream
)
def my_task(input_data: dict) -> dict:
    return {"processed": True}
```

### Return Values and XCom

When a task function returns a value, it is automatically pushed to XCom with the key `return_value`. Invoking the decorated function returns an `XComArg` — a lazy reference, not the actual value:

```python
@task()
def get_count():
    return 42

result = get_count()        # XComArg, not 42
next_task(result)           # Airflow wires the dependency and passes 42 at runtime
```

## The @dag Decorator

Converts a function into a DAG factory. Function parameters become DAG parameters accessible during manual triggering:

```python
from airflow.sdk import dag, task
import pendulum

@dag(
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    schedule="@daily",
    catchup=False,
    default_args={"retries": 2},
    tags=["production", "etl"],
    description="Daily ETL pipeline for user data",
    max_active_runs=3,
)
def user_etl(
    source_schema: str = "public",
    batch_size: int = 10000,
):
    @task()
    def extract(schema: str, size: int):
        return f"Extracted from {schema} with batch {size}"

    extract(source_schema, batch_size)

user_etl()
```

## Passing Data Between Tasks

### Direct Argument Passing

The primary pattern — return from one task, pass as argument to the next:

```python
@task()
def extract():
    return [1, 2, 3, 4, 5]

@task()
def transform(data: list):
    return [x * 2 for x in data]

@task()
def load(data: list):
    print(f"Loading {len(data)} items")

raw = extract()
transformed = transform(raw)
load(transformed)
```

### XComArg Indexing

Access specific keys from a dict return:

```python
@task(multiple_outputs=True)
def get_config():
    return {"host": "db.example.com", "port": 5432, "database": "analytics"}

config = get_config()
connect(host=config["host"], port=config["port"])
```

## Multiple Outputs

When a task returns a dictionary, enable `multiple_outputs` to create separate XCom entries per key:

```python
@task(multiple_outputs=True)
def split_data():
    return {
        "users": [{"id": 1}, {"id": 2}],
        "orders": [{"id": 101}],
        "metadata": {"count": 3},
    }

result = split_data()
process_users(result["users"])
process_orders(result["orders"])
log_metadata(result["metadata"])
```

Alternatively, type-hint the return as `dict` and Airflow infers `multiple_outputs=True`:

```python
@task()
def split_data() -> dict[str, list]:
    return {"users": [...], "orders": [...]}
```

## Accessing Context

Tasks can receive Airflow execution context via typed keyword arguments:

```python
from airflow.sdk import TaskInstance
from airflow.sdk.types import DagRunProtocol

@task()
def context_aware(
    task_instance: TaskInstance,
    dag_run: DagRunProtocol,
    data_interval_start=None,
    data_interval_end=None,
):
    print(f"Run ID: {task_instance.run_id}")
    print(f"Logical date: {dag_run.logical_date}")
    print(f"Interval: {data_interval_start} to {data_interval_end}")
```

Or use `**kwargs` to receive all context variables:

```python
@task()
def with_context(**kwargs):
    ti = kwargs["task_instance"]
    ds = kwargs["ds"]  # YYYY-MM-DD string of logical_date
    print(f"Running for date: {ds}")
```

### Common Context Variables

| Variable | Type | Description |
|----------|------|-------------|
| `task_instance` / `ti` | TaskInstance | Current task instance |
| `dag_run` | DagRun | Current DAG run |
| `ds` | str | Logical date as `YYYY-MM-DD` |
| `ds_nodash` | str | Logical date as `YYYYMMDD` |
| `data_interval_start` | DateTime | Start of data interval |
| `data_interval_end` | DateTime | End of data interval |
| `logical_date` | DateTime | Logical date of the DAG run |
| `params` | dict | DAG parameters |
| `conf` | dict | Trigger configuration |

## Specialized Decorators

### @task.bash

Execute shell commands:

```python
@task.bash()
def run_etl_script():
    return "python /opt/etl/transform.py --date {{ ds }}"
```

### @task.python

Explicit Python task (equivalent to plain `@task`):

```python
@task.python()
def process():
    return "done"
```

### @task.branch

Conditional branching — return task ID(s) to execute:

```python
@task.branch()
def choose_path():
    if condition:
        return "path_a"
    return ["path_b", "path_c"]
```

### @task.short_circuit

Skip all downstream tasks if function returns falsy:

```python
@task.short_circuit()
def check_data_exists():
    return has_new_data()  # False skips everything downstream
```

### @task.virtualenv

Run in an isolated Python virtual environment:

```python
@task.virtualenv(
    python_version="3.11",
    requirements=["pandas==2.2.0", "numpy>=1.26"],
    system_site_packages=False,
)
def process_with_pandas():
    import pandas as pd
    df = pd.read_csv("/data/input.csv")
    return len(df)
```

### @task.external_python

Run in a pre-existing Python environment:

```python
@task.external_python(python="/opt/venvs/ml/bin/python")
def train_model():
    import tensorflow as tf
    model = tf.keras.models.load_model("/models/latest")
    return model.evaluate(test_data)
```

### @task.docker

Run in a Docker container:

```python
@task.docker(image="my-etl:latest", auto_remove="success")
def containerized_transform():
    import heavy_library
    return heavy_library.process()
```

### @task.kubernetes

Run in a Kubernetes pod:

```python
@task.kubernetes(
    image="my-ml:latest",
    namespace="airflow",
    node_selector={"gpu": "true"},
)
def gpu_training():
    import torch
    return train()
```

### @task.sensor

Create a sensor with a decorator:

```python
@task.sensor(poke_interval=60, timeout=3600, mode="reschedule")
def wait_for_file():
    from pathlib import Path
    return Path("/data/ready.flag").exists()
```

## Conditional Execution

### @skip_if / @run_if (Airflow 3.3+)

```python
from airflow.sdk import skip_if, run_if

@task()
@skip_if(lambda context: context["params"].get("skip_validation"))
def validate_data():
    return "validated"

@task()
@run_if(lambda context: context["dag_run"].conf.get("include_archive"))
def process_archive():
    return "archived"
```

## Task Groups

Group related tasks visually:

```python
from airflow.sdk import task_group

@task_group()
def quality_checks():
    @task()
    def check_nulls():
        return True

    @task()
    def check_types():
        return True

    check_nulls()
    check_types()

@dag(...)
def pipeline():
    data = extract()
    quality_checks()
    load(data)
```

### Nested Task Groups

```python
@task_group()
def outer_group():
    @task_group()
    def inner_group_a():
        task_a1()
        task_a2()

    @task_group()
    def inner_group_b():
        task_b1()

    inner_group_a() >> inner_group_b()
```

## Custom Object Serialization

Pass custom objects between tasks by implementing serialization:

```python
from dataclasses import dataclass
from typing import ClassVar

@dataclass
class ProcessingResult:
    __version__: ClassVar[int] = 1
    rows_processed: int
    errors: list[str]

    def serialize(self) -> dict:
        return {"rows_processed": self.rows_processed, "errors": self.errors}

    @staticmethod
    def deserialize(data: dict, version: int) -> "ProcessingResult":
        return ProcessingResult(
            rows_processed=data["rows_processed"],
            errors=data["errors"],
        )
```

Objects decorated with `@dataclass` or `@attr.define` get automatic serialization support.

## Logging

Use Python's standard logging in tasks:

```python
import logging

logger = logging.getLogger("airflow.task")

@task()
def process_data():
    logger.info("Starting data processing")
    logger.warning("Large dataset detected: %d rows", row_count)
    logger.error("Failed to process partition %s", partition_id)
    return result
```

Each log line appears in the task's log view in the Airflow UI.

## Related Topics

- [DAGs](01-dags.md) — DAG declaration patterns and control flow
- [XComs & Variables](04-xcoms-and-variables.md) — Manual XCom usage and variables
- [Dynamic Task Mapping](07-dynamic-task-mapping.md) — expand() with TaskFlow
