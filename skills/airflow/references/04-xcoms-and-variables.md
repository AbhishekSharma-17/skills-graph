# XComs & Variables

> Source: [airflow.apache.org/docs/…/xcoms](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/xcoms.html) · v3.3.0

## Table of Contents

- [XComs Overview](#xcoms-overview)
- [Pushing and Pulling](#pushing-and-pulling)
- [Multiple Outputs](#multiple-outputs)
- [Cross-DAG XComs](#cross-dag-xcoms)
- [Custom XCom Backends](#custom-xcom-backends)
- [Variables](#variables)
- [Params](#params)
- [Size and Performance](#size-and-performance)

## XComs Overview

XComs (cross-communications) enable task-to-task communication within a DAG. By default, tasks are isolated — XComs provide a controlled way to pass small amounts of data between them.

Each XCom entry is identified by:
- **key** — a string identifier (default: `return_value`)
- **task_id** — the producing task
- **dag_id** — the DAG
- **run_id** — the specific DAG run

XComs accept any serializable value, including objects decorated with `@dataclass` or `@attr.define`.

## Pushing and Pulling

### Explicit Push/Pull

```python
from airflow.sdk import task

@task()
def producer(ti=None):
    ti.xcom_push(key="row_count", value=42)
    ti.xcom_push(key="file_path", value="/data/output.csv")

@task()
def consumer(ti=None):
    count = ti.xcom_pull(task_ids="producer", key="row_count")
    path = ti.xcom_pull(task_ids="producer", key="file_path")
    print(f"Processing {count} rows from {path}")
```

### Automatic Push via Return Value

TaskFlow tasks automatically push their return value with key `return_value`:

```python
@task()
def extract():
    return {"users": 100, "orders": 500}  # Pushed as return_value

@task()
def transform(data: dict):  # Received automatically via XCom
    return data["users"] + data["orders"]
```

### Pull from Classic Operators

```python
@task()
def use_bash_output(ti=None):
    output = ti.xcom_pull(task_ids="bash_task")
    print(f"Bash output: {output}")
```

BashOperator pushes the last line of stdout to XCom by default (enable with `do_xcom_push=True`).

## Multiple Outputs

Return a dictionary with separate XCom keys:

```python
@task(multiple_outputs=True)
def split_config():
    return {
        "database_host": "db.example.com",
        "database_port": 5432,
        "api_endpoint": "https://api.example.com",
    }

config = split_config()

# Access individual keys
connect_db(host=config["database_host"], port=config["database_port"])
call_api(endpoint=config["api_endpoint"])
```

Each key becomes a separate XCom entry, so downstream tasks can depend on specific outputs without pulling the entire dictionary.

## Cross-DAG XComs

Pull XCom values from another DAG's task:

```python
@task()
def read_upstream(ti=None):
    trigger_run_id = ti.xcom_pull(
        task_ids="trigger_child",
        key="trigger_run_id",
    )

    child_result = ti.xcom_pull(
        task_ids="process_data",
        dag_id="child_pipeline",
        run_id=trigger_run_id,
    )
    return child_result
```

## Custom XCom Backends

The default backend stores XComs in the metadata database. For large data, implement a custom backend:

```python
from airflow.models.xcom import BaseXCom
import json

class S3XComBackend(BaseXCom):
    @staticmethod
    def serialize_value(value, key=None, task_id=None, dag_id=None, run_id=None, map_index=-1):
        import boto3
        s3 = boto3.client("s3")
        s3_key = f"xcom/{dag_id}/{run_id}/{task_id}/{key}.json"
        s3.put_object(
            Bucket="airflow-xcom",
            Key=s3_key,
            Body=json.dumps(value),
        )
        return s3_key  # Store only the reference in the DB

    @staticmethod
    def deserialize_value(result):
        import boto3
        s3 = boto3.client("s3")
        response = s3.get_object(Bucket="airflow-xcom", Key=result.value)
        return json.loads(response["Body"].read())
```

Configure in `airflow.cfg`:

```ini
[core]
xcom_backend = my_plugin.S3XComBackend
```

### Object Storage Backend

Airflow 3.x supports object storage natively for XCom:

```ini
[core]
xcom_backend = airflow.models.xcom.BaseXCom
xcom_objectstorage_path = s3://my-bucket/xcom/
xcom_objectstorage_threshold = 1048576  # 1MB — values above this go to object storage
```

## Variables

Variables are global key-value pairs for configuration. Unlike XComs (scoped to a task instance and run), Variables persist across DAG runs.

### Setting Variables

```bash
# CLI
airflow variables set my_api_key "sk-12345"
airflow variables set config '{"env": "prod", "region": "us-east-1"}' --json

# UI: Admin > Variables
```

```python
# In Python (task context only — never at module level)
from airflow.sdk import Variable

@task()
def use_variable():
    api_key = Variable.get("my_api_key")
    config = Variable.get("config", deserialize_json=True)
    default_val = Variable.get("optional_key", default_var="fallback")
    return config["region"]
```

### Variables in Templates (Preferred)

Jinja templates defer Variable resolution to execution time, avoiding database calls during parsing:

```python
BashOperator(
    task_id="run_job",
    bash_command="python job.py --key {{ var.value.api_key }} --env {{ var.json.config.env }}",
)
```

### Anti-Pattern: Top-Level Variable Access

```python
# BAD — triggers database call every time DAG file is parsed
api_key = Variable.get("api_key")  # Runs every 30 seconds!

# GOOD — deferred to execution time
@task()
def use_key():
    api_key = Variable.get("api_key")
```

## Params

Params are DAG-level parameters with JSON Schema validation, settable at trigger time:

```python
from airflow.sdk import DAG, Param

with DAG(
    dag_id="configurable_pipeline",
    params={
        "source": Param("s3://default-bucket/", type="string", description="Source data path"),
        "batch_size": Param(1000, type="integer", minimum=100, maximum=100000),
        "dry_run": Param(False, type="boolean"),
        "priority": Param("normal", enum=["low", "normal", "high"]),
    },
    ...
):
    @task()
    def extract(**kwargs):
        source = kwargs["params"]["source"]
        batch_size = kwargs["params"]["batch_size"]
        print(f"Extracting from {source} in batches of {batch_size}")
```

Access in templates:

```python
BashOperator(
    task_id="extract",
    bash_command="python extract.py --source {{ params.source }} --batch {{ params.batch_size }}",
)
```

### Params vs Variables

| Feature | Params | Variables |
|---------|--------|-----------|
| Scope | Single DAG | Global |
| Set at | Trigger time / DAG code | UI, CLI, or code |
| Validation | JSON Schema | None |
| Template access | `{{ params.key }}` | `{{ var.value.key }}` |
| Persistence | Per DAG run | Persistent across runs |

## Size and Performance

### XCom Size Limits

XComs are designed for small data — metadata, file paths, row counts, status flags. Never pass DataFrames, large lists, or binary blobs.

| Approach | Max Size | Use For |
|----------|----------|---------|
| Default XCom (database) | ~48KB practical | Metadata, paths, counts |
| Object storage backend | Configurable | Medium payloads |
| External storage (S3/GCS) | Unlimited | Large data — pass the path via XCom |

### Performance Tips

- Use `{{ var.value.x }}` templates instead of `Variable.get()` to avoid parsing-time DB calls
- Set `do_xcom_push=False` on tasks that don't need to share return values
- Use `multiple_outputs=True` so downstream tasks pull only what they need
- Clean up old XCom data with `airflow db clean`
- On retries, XComs from the failed attempt are cleared before the retry runs

### XCom Retention

```python
# Failed task clears XCom on retry
@task(do_xcom_push=True)
def unreliable_task():
    return compute()  # XCom cleared if this task retries
```

## Related Topics

- [TaskFlow API](02-taskflow-api.md) — Automatic XCom via return values
- [Connections & Hooks](05-connections-and-hooks.md) — Credential storage (not Variables)
- [Best Practices](12-best-practices.md) — Avoiding top-level Variable access
