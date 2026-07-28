# DAGs (Directed Acyclic Graphs)

> Source: [airflow.apache.org/docs/…/dags](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html) · v3.3.0

## Table of Contents

- [What Is a DAG?](#what-is-a-dag)
- [Declaration Methods](#declaration-methods)
- [Task Dependencies](#task-dependencies)
- [Default Arguments](#default-arguments)
- [Control Flow](#control-flow)
- [Dynamic DAGs](#dynamic-dags)
- [Task Groups](#task-groups)
- [DAG Parameters](#dag-parameters)
- [DAG Loading & Discovery](#dag-loading--discovery)
- [Running DAGs](#running-dags)

## What Is a DAG?

A DAG encapsulates everything needed to execute a workflow: schedule, tasks, dependencies, callbacks, and operational parameters. It defines the *structure* of your pipeline — what runs and in what order — but contains no business logic itself.

## Declaration Methods

### Context Manager (recommended for classic style)

```python
from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator
import datetime

with DAG(
    dag_id="etl_pipeline",
    start_date=datetime.datetime(2024, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["etl", "production"],
) as dag:
    extract = BashOperator(task_id="extract", bash_command="echo extracting")
    transform = BashOperator(task_id="transform", bash_command="echo transforming")
    load = BashOperator(task_id="load", bash_command="echo loading")

    extract >> transform >> load
```

### Decorator (recommended for TaskFlow)

```python
from airflow.sdk import dag, task
import pendulum

@dag(
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    schedule="@daily",
    catchup=False,
)
def etl_pipeline():
    @task()
    def extract():
        return {"rows": 100}

    @task()
    def transform(data: dict):
        return {"processed": data["rows"] * 2}

    @task()
    def load(result: dict):
        print(f"Loaded {result['processed']} rows")

    load(transform(extract()))

etl_pipeline()
```

### Standard Constructor

```python
my_dag = DAG(dag_id="my_dag", start_date=datetime.datetime(2024, 1, 1), schedule="@daily")
task1 = BashOperator(task_id="task1", bash_command="echo hello", dag=my_dag)
```

## Task Dependencies

### Bitshift Operators

```python
# Linear chain
extract >> transform >> load

# Fan-out
extract >> [transform_a, transform_b]

# Fan-in
[transform_a, transform_b] >> load

# Upstream
load << transform
```

### Helper Functions

```python
from airflow.sdk import chain, cross_downstream

# Linear chain
chain(op1, op2, op3, op4)

# Pairwise chain (lists must be same length)
chain(op1, [op2, op3], [op4, op5], op6)
# op1 >> op2 >> op4 >> op6
# op1 >> op3 >> op5 >> op6

# Cross dependencies (every item in first list depends on every item in second)
cross_downstream([op1, op2], [op3, op4])
# op1 >> op3, op1 >> op4, op2 >> op3, op2 >> op4
```

## Default Arguments

Apply settings across all tasks in a DAG:

```python
default_args = {
    "owner": "data_team",
    "retries": 3,
    "retry_delay": datetime.timedelta(minutes=5),
    "email_on_failure": True,
    "email": ["alerts@company.com"],
    "execution_timeout": datetime.timedelta(hours=2),
}

with DAG(
    dag_id="production_pipeline",
    default_args=default_args,
    start_date=datetime.datetime(2024, 1, 1),
    schedule="@daily",
) as dag:
    # All tasks inherit retries=3, retry_delay, etc.
    task1 = BashOperator(task_id="task1", bash_command="echo hello")
    task2 = BashOperator(task_id="task2", bash_command="echo world", retries=1)  # overrides
```

## Control Flow

### Branching

```python
@task.branch(task_id="branch_task")
def decide_path(ti=None):
    value = int(ti.xcom_pull(task_ids="check_data"))
    if value >= 100:
        return "process_large"
    elif value >= 10:
        return "process_medium"
    else:
        return "process_small"
```

Only the returned task(s) execute; others are skipped. Return `None` to skip all downstream tasks.

### Latest Only

Prevents backfilled runs from executing downstream tasks:

```python
from airflow.providers.standard.operators.latest_only import LatestOnlyOperator

latest = LatestOnlyOperator(task_id="latest_only")
latest >> send_notification  # Only runs on the most recent DAG run
```

### Depends on Past

A task waits for its previous instance to succeed:

```python
task = BashOperator(
    task_id="sequential_task",
    bash_command="echo processing",
    depends_on_past=True,
)
```

### Trigger Rules

Control when a task runs based on upstream states:

| Rule | Fires When |
|------|------------|
| `all_success` (default) | All upstream tasks succeeded |
| `all_failed` | All upstream tasks failed |
| `all_done` | All upstream tasks completed (any state) |
| `all_skipped` | All upstream tasks skipped |
| `one_success` | At least one upstream succeeded |
| `one_failed` | At least one upstream failed |
| `one_done` | At least one upstream completed |
| `none_failed` | No upstream tasks failed (succeeded or skipped) |
| `none_skipped` | No upstream tasks skipped |
| `none_failed_min_one_success` | No failures and at least one success |
| `always` | No dependencies; runs unconditionally |

```python
from airflow.utils.trigger_rule import TriggerRule

cleanup = BashOperator(
    task_id="cleanup",
    bash_command="echo cleaning up",
    trigger_rule=TriggerRule.ALL_DONE,  # Always runs regardless of upstream state
)
```

**Important:** After a branch, downstream tasks with `all_success` trigger rule are skipped because non-selected branches are marked skipped. Use `none_failed_min_one_success` instead.

## Dynamic DAGs

Since DAGs are Python code, generate them dynamically:

```python
from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator
import yaml

with open("/opt/airflow/config/pipelines.yaml") as f:
    pipelines = yaml.safe_load(f)

for pipeline in pipelines:
    with DAG(
        dag_id=f"pipeline_{pipeline['name']}",
        schedule=pipeline.get("schedule", "@daily"),
        start_date=datetime.datetime(2024, 1, 1),
    ) as dag:
        for i, step in enumerate(pipeline["steps"]):
            task = BashOperator(
                task_id=f"step_{i}",
                bash_command=step["command"],
            )
            if i > 0:
                prev >> task
            prev = task

        globals()[f"pipeline_{pipeline['name']}"] = dag
```

Keep task topology stable across runs — dynamic task *counts* cause issues with task instance history.

## Task Groups

Organize related tasks visually without affecting execution:

```python
from airflow.sdk import task_group

@task_group(default_args={"retries": 3})
def data_quality_checks():
    @task()
    def check_nulls():
        return "no nulls"

    @task()
    def check_duplicates():
        return "no duplicates"

    @task()
    def check_schema():
        return "schema valid"

    check_nulls()
    check_duplicates()
    check_schema()

# Usage in DAG
extract() >> data_quality_checks() >> load()
```

### Edge Labels

Label dependency edges for clarity:

```python
from airflow.sdk import Label

branch_task >> Label("When valid") >> process_task
branch_task >> Label("When invalid") >> error_task
```

## DAG Parameters

Function parameters in `@dag` decorators become triggerable parameters:

```python
@dag(start_date=datetime.datetime(2024, 1, 1), schedule="@daily")
def parameterized_dag(
    source_table: str = "users",
    target_bucket: str = "s3://data-lake/raw/",
    run_quality_checks: bool = True,
):
    @task()
    def extract(table: str):
        return f"Extracted from {table}"

    extract(source_table)

parameterized_dag()
```

Parameters are accessible in Jinja templates via `{{ params.source_table }}`.

## DAG Loading & Discovery

Airflow scans `DAGS_FOLDER` for Python files containing DAG objects. Only top-level DAG objects are discovered:

```python
dag_1 = DAG("discovered")          # Found by parser

def my_function():
    dag_2 = DAG("not_discovered")   # NOT found — nested in function

my_function()
```

### .airflowignore

Exclude files/directories from parsing:

```
# .airflowignore (glob syntax)
**/test_*
**/archive/*
**/__pycache__/
```

### DAG Documentation

```python
dag.doc_md = """
### ETL Pipeline
Extracts data from source DB, transforms, and loads to warehouse.
Runs daily at midnight UTC.
"""

task.doc_md = "Extracts user records from PostgreSQL replica."
```

## Running DAGs

### Schedule Presets

| Preset | Cron Equivalent |
|--------|-----------------|
| `@once` | Run once then never |
| `@continuous` | Run as soon as previous finishes |
| `@hourly` | `0 * * * *` |
| `@daily` | `0 0 * * *` |
| `@weekly` | `0 0 * * 0` |
| `@monthly` | `0 0 1 * *` |
| `@yearly` | `0 0 1 1 *` |
| `None` | Manually triggered only |

### Manual Triggering

```bash
airflow dags trigger my_dag
airflow dags trigger my_dag --conf '{"key": "value"}'
```

### DAG Runs

Each execution creates a DAG Run with a `logical_date` representing the data interval. Multiple runs can execute concurrently:

```python
with DAG(
    dag_id="concurrent_dag",
    max_active_runs=3,          # Max concurrent DAG runs
    max_active_tasks=16,        # Max concurrent task instances
    schedule="@hourly",
    ...
):
    ...
```

## Related Topics

- [TaskFlow API](02-taskflow-api.md) — Modern decorator-based authoring
- [Scheduling](06-scheduling.md) — Cron, timetables, asset-driven scheduling
- [Best Practices](12-best-practices.md) — DAG writing anti-patterns
