# Operators & Sensors

> Source: [airflow.apache.org/docs/…/operators](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/operators.html) · v3.3.0

## Table of Contents

- [What Are Operators?](#what-are-operators)
- [Built-in Operators](#built-in-operators)
- [Jinja Templating](#jinja-templating)
- [Custom Operators](#custom-operators)
- [Setup and Teardown Tasks](#setup-and-teardown-tasks)
- [Sensors](#sensors)
- [Deferrable Operators](#deferrable-operators)

## What Are Operators?

An Operator is a pre-built task template. Rather than writing a Python function for every task, use an operator with the right parameters. Each operator instance becomes a single task in your DAG.

Rules:
- Each operator instance corresponds to exactly one task
- Operators should be idempotent — running twice produces the same result
- Operators within a DAG can run on different workers and should not share state

## Built-in Operators

### BashOperator

Execute shell commands:

```python
from airflow.providers.standard.operators.bash import BashOperator

download = BashOperator(
    task_id="download_data",
    bash_command="curl -o /data/file.csv https://api.example.com/data?date={{ ds }}",
    env={"API_KEY": "{{ var.value.api_key }}"},
    cwd="/opt/airflow/scripts",
)
```

### PythonOperator

Call Python functions (prefer `@task` decorator in new code):

```python
from airflow.providers.standard.operators.python import PythonOperator

def process_data(ds, **kwargs):
    print(f"Processing data for {ds}")
    return {"status": "complete"}

process = PythonOperator(
    task_id="process",
    python_callable=process_data,
    op_kwargs={"extra_param": "value"},
)
```

### EmptyOperator

No-op task for DAG structure (join points, milestones):

```python
from airflow.providers.standard.operators.empty import EmptyOperator

start = EmptyOperator(task_id="start")
end = EmptyOperator(task_id="end", trigger_rule="none_failed")
```

### BranchPythonOperator

Conditional branching (prefer `@task.branch` decorator):

```python
from airflow.providers.standard.operators.python import BranchPythonOperator

def decide(ti):
    value = ti.xcom_pull(task_ids="check_count")
    return "process_large" if value > 1000 else "process_small"

branch = BranchPythonOperator(task_id="branch", python_callable=decide)
```

### SQLExecuteQueryOperator

Execute SQL on any supported database:

```python
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator

query = SQLExecuteQueryOperator(
    task_id="insert_data",
    conn_id="postgres_warehouse",
    sql="""
        INSERT INTO analytics.daily_summary (date, total)
        SELECT '{{ ds }}', COUNT(*)
        FROM events
        WHERE event_date = '{{ ds }}'
        ON CONFLICT (date) DO UPDATE SET total = EXCLUDED.total;
    """,
)
```

### Popular Provider Operators

```python
# Google Cloud
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator

# AWS
from airflow.providers.amazon.aws.operators.s3 import S3CreateObjectOperator
from airflow.providers.amazon.aws.operators.emr import EmrAddStepsOperator

# Slack
from airflow.providers.slack.operators.slack_webhook import SlackWebhookOperator

# Docker
from airflow.providers.docker.operators.docker import DockerOperator

# HTTP
from airflow.providers.http.operators.http import HttpOperator
```

## Jinja Templating

Operators support Jinja2 templating in fields marked as `template_fields`. Templates render just before task execution.

### Common Template Variables

| Variable | Example | Description |
|----------|---------|-------------|
| `{{ ds }}` | `2024-03-15` | Logical date (YYYY-MM-DD) |
| `{{ ds_nodash }}` | `20240315` | Logical date without dashes |
| `{{ data_interval_start }}` | DateTime | Start of data interval |
| `{{ data_interval_end }}` | DateTime | End of data interval |
| `{{ logical_date }}` | DateTime | Logical date of the run |
| `{{ ts }}` | ISO timestamp | Execution timestamp |
| `{{ dag.dag_id }}` | `my_dag` | DAG ID |
| `{{ task.task_id }}` | `my_task` | Task ID |
| `{{ var.value.my_var }}` | Value | Airflow Variable |
| `{{ var.json.my_var.key }}` | Value | JSON Variable field |
| `{{ conn.my_conn.host }}` | Hostname | Connection field |
| `{{ params.key }}` | Value | DAG parameter |

### Template Examples

```python
# Template in BashOperator
BashOperator(
    task_id="run_report",
    bash_command="python generate_report.py --date {{ ds }} --env {{ var.value.env }}",
)

# Template in SQL
SQLExecuteQueryOperator(
    task_id="load",
    sql="SELECT * FROM events WHERE dt = '{{ ds }}'",
    conn_id="{{ var.value.warehouse_conn }}",
)

# Template with filters
BashOperator(
    task_id="greet",
    bash_command="echo Hello {{ params.name | upper }}!",
)
```

### F-string Conflicts

When mixing Python f-strings with Jinja, escape braces:

```python
bash_command=f"echo Date: {{{{ ds }}}}"  # quadruple braces
```

### Native Python Objects

By default, templates render as strings. Enable native rendering to receive Python objects:

```python
with DAG(dag_id="native_dag", render_template_as_native_obj=True, ...):
    @task()
    def use_config():
        pass

    use_config.op_args=["{{ var.json.config }}"]  # Receives dict, not string
```

## Custom Operators

### Basic Custom Operator

```python
from airflow.models.baseoperator import BaseOperator

class DataQualityOperator(BaseOperator):
    template_fields = ("sql", "conn_id")

    def __init__(self, sql: str, conn_id: str, min_rows: int = 1, **kwargs):
        super().__init__(**kwargs)
        self.sql = sql
        self.conn_id = conn_id
        self.min_rows = min_rows

    def execute(self, context):
        from airflow.providers.common.sql.hooks.sql import DbApiHook
        hook = DbApiHook.get_hook(self.conn_id)
        records = hook.get_records(self.sql)
        if len(records) < self.min_rows:
            raise ValueError(f"Quality check failed: {len(records)} < {self.min_rows}")
        self.log.info("Quality check passed: %d rows", len(records))
        return len(records)
```

### Template Fields

Mark operator parameters as Jinja-templatable:

```python
class MyOperator(BaseOperator):
    template_fields = ("query", "bucket", "prefix")
    template_ext = (".sql",)  # Also render files with these extensions

    def __init__(self, query: str, bucket: str, prefix: str, **kwargs):
        super().__init__(**kwargs)
        self.query = query
        self.bucket = bucket
        self.prefix = prefix
```

Use `literal()` to prevent a string from being templated:

```python
from airflow.utils.template import literal

task = MyOperator(
    task_id="task",
    query=literal("{{ this is not a template }}"),
)
```

## Setup and Teardown Tasks

Manage resources that multiple tasks depend on:

```python
from airflow.sdk import dag, task

@dag(...)
def pipeline_with_resources():
    @task()
    def create_cluster():
        return "cluster-123"

    @task()
    def process_data():
        pass

    @task()
    def delete_cluster():
        pass

    cluster = create_cluster()
    process = process_data()
    cleanup = delete_cluster()

    cluster >> process >> cleanup

    # Mark setup/teardown relationship
    cluster.as_setup()
    cleanup.as_teardown(setups=cluster)
```

Teardown tasks always run (even if the work tasks fail), ensuring resources are cleaned up.

## Sensors

Sensors are specialized operators that wait for a condition to be met before proceeding.

### Operating Modes

| Mode | Behavior | Use When |
|------|----------|----------|
| `poke` (default) | Occupies worker slot continuously, checks at `poke_interval` | Short waits, frequent checks |
| `reschedule` | Releases worker slot between checks | Long waits, infrequent checks |

### Common Sensors

```python
from airflow.providers.standard.sensors.bash import BashSensor
from airflow.providers.standard.sensors.python import PythonSensor
from airflow.providers.standard.sensors.filesystem import FileSensor
from airflow.providers.standard.sensors.time_delta import TimeDeltaSensor
from airflow.providers.standard.sensors.external_task import ExternalTaskSensor

# Wait for a file
wait_file = FileSensor(
    task_id="wait_for_file",
    filepath="/data/incoming/{{ ds }}/data.csv",
    poke_interval=60,
    timeout=3600,
    mode="reschedule",
)

# Wait for bash command to return true
wait_api = BashSensor(
    task_id="wait_for_api",
    bash_command="curl -sf https://api.example.com/health",
    poke_interval=30,
    timeout=600,
)

# Wait for Python condition
wait_condition = PythonSensor(
    task_id="wait_for_condition",
    python_callable=lambda: check_data_ready(),
    poke_interval=120,
    timeout=7200,
    mode="reschedule",
)

# Wait for another DAG's task
wait_upstream = ExternalTaskSensor(
    task_id="wait_for_upstream",
    external_dag_id="upstream_dag",
    external_task_id="final_task",
    timeout=7200,
    mode="reschedule",
)

# Wait for time delta
wait_delay = TimeDeltaSensor(
    task_id="wait_30_min",
    delta=timedelta(minutes=30),
)
```

### Sensor Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `poke_interval` | 60 | Seconds between checks |
| `timeout` | 604800 (7 days) | Max seconds before sensor fails |
| `mode` | `"poke"` | `"poke"` or `"reschedule"` |
| `soft_fail` | `False` | `True` = SKIPPED instead of FAILED on timeout |
| `exponential_backoff` | `False` | Increase delay between checks exponentially |
| `max_wait` | None | Upper bound (seconds) for exponential backoff |

### Custom Sensors

```python
from airflow.sensors.base import BaseSensorOperator

class DataReadySensor(BaseSensorOperator):
    template_fields = ("partition",)

    def __init__(self, conn_id: str, partition: str, **kwargs):
        super().__init__(**kwargs)
        self.conn_id = conn_id
        self.partition = partition

    def poke(self, context) -> bool:
        hook = DbApiHook.get_hook(self.conn_id)
        count = hook.get_first(f"SELECT COUNT(*) FROM staging WHERE dt = '{self.partition}'")
        return count[0] > 0
```

## Deferrable Operators

Deferrable operators release their worker slot while waiting, using the Triggerer process to resume:

```python
from airflow.providers.standard.sensors.time_delta import TimeDeltaSensorAsync

wait = TimeDeltaSensorAsync(
    task_id="wait_30_min",
    delta=timedelta(minutes=30),
)
```

Deferrable operators are more resource-efficient than `mode="reschedule"` sensors because they don't consume scheduler database writes on each reschedule cycle.

### When to Use Each

| Approach | Worker Slot | Best For |
|----------|-------------|----------|
| `mode="poke"` | Held continuously | Short waits (<5 min) |
| `mode="reschedule"` | Released between pokes | Medium waits, limited workers |
| Deferrable operator | Released entirely | Long waits, many concurrent sensors |

## Related Topics

- [TaskFlow API](02-taskflow-api.md) — Decorator-based task authoring
- [Connections & Hooks](05-connections-and-hooks.md) — Configuring external system access
- [XComs & Variables](04-xcoms-and-variables.md) — Passing data between operators
