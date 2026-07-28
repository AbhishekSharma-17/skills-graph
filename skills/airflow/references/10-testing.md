# Testing

> Source: [airflow.apache.org/docs/…/best-practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html) · v3.3.0

## Table of Contents

- [DAG Validation Tests](#dag-validation-tests)
- [Unit Testing Tasks](#unit-testing-tasks)
- [Testing DAG Structure](#testing-dag-structure)
- [Integration Testing](#integration-testing)
- [Mocking Connections and Variables](#mocking-connections-and-variables)
- [Testing with dag.test()](#testing-with-dagtest)
- [Staging Environments](#staging-environments)
- [CI/CD Integration](#cicd-integration)

## DAG Validation Tests

The simplest test: verify DAGs parse without errors.

### DAG Loader Test

```python
import pytest
from airflow.dag_processing.dagbag import DagBag

@pytest.fixture()
def dagbag():
    return DagBag(dag_folder="dags/", include_examples=False)

def test_no_import_errors(dagbag):
    assert dagbag.import_errors == {}, f"DAG import errors: {dagbag.import_errors}"

def test_dag_count(dagbag):
    assert len(dagbag.dags) > 0, "No DAGs found"
```

### Parse Time Test

```python
import time

def test_dag_parse_time():
    start = time.monotonic()
    dagbag = DagBag(dag_folder="dags/", include_examples=False)
    elapsed = time.monotonic() - start
    assert elapsed < 30, f"DAG parsing took {elapsed:.1f}s (>30s limit)"
    assert dagbag.import_errors == {}
```

### Individual DAG Validation

```python
def test_specific_dag(dagbag):
    dag = dagbag.get_dag("my_etl_pipeline")
    assert dag is not None
    assert dag.schedule == "@daily"
    assert dag.catchup is False
    assert len(dag.tasks) >= 3
    assert "extract" in dag.task_ids
    assert "transform" in dag.task_ids
    assert "load" in dag.task_ids
```

## Unit Testing Tasks

### Testing TaskFlow Functions

Extract business logic from tasks and test independently:

```python
# dags/etl.py
from airflow.sdk import dag, task

def _transform_records(records: list[dict]) -> list[dict]:
    """Pure function — testable without Airflow."""
    return [
        {**r, "name": r["name"].strip().title(), "active": r["status"] == "A"}
        for r in records
    ]

@dag(...)
def etl():
    @task()
    def transform(records):
        return _transform_records(records)
```

```python
# tests/test_etl.py
from dags.etl import _transform_records

def test_transform_records():
    input_data = [
        {"name": "  john doe ", "status": "A"},
        {"name": "JANE SMITH", "status": "I"},
    ]
    result = _transform_records(input_data)
    assert result[0]["name"] == "John Doe"
    assert result[0]["active"] is True
    assert result[1]["name"] == "Jane Smith"
    assert result[1]["active"] is False

def test_transform_empty():
    assert _transform_records([]) == []
```

### Testing Custom Operators

```python
import pendulum
from airflow.sdk import DAG, TaskInstanceState

def test_data_quality_operator():
    with DAG(
        dag_id="test_quality",
        schedule="@daily",
        start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    ) as test_dag:
        from my_operators import DataQualityOperator

        quality_check = DataQualityOperator(
            task_id="check",
            sql="SELECT COUNT(*) FROM test_table",
            conn_id="test_postgres",
            min_rows=1,
        )

    dagrun = test_dag.test()
    ti = dagrun.get_task_instance(task_id="check")
    assert ti.state == TaskInstanceState.SUCCESS
```

## Testing DAG Structure

Verify task dependencies match expected topology:

```python
def test_dag_structure(dagbag):
    dag = dagbag.get_dag("my_pipeline")

    expected = {
        "extract": ["transform_a", "transform_b"],
        "transform_a": ["join"],
        "transform_b": ["join"],
        "join": ["load"],
        "load": ["notify"],
        "notify": [],
    }

    assert set(dag.task_ids) == set(expected.keys())

    for task_id, expected_downstream in expected.items():
        task = dag.get_task(task_id)
        actual_downstream = sorted(task.downstream_task_ids)
        assert actual_downstream == sorted(expected_downstream), (
            f"Task {task_id}: expected downstream {expected_downstream}, "
            f"got {actual_downstream}"
        )
```

### Test Default Args

```python
def test_default_args(dagbag):
    dag = dagbag.get_dag("production_pipeline")
    for task in dag.tasks:
        assert task.retries >= 1, f"Task {task.task_id} has no retries"
        assert task.email_on_failure is True, f"Task {task.task_id} missing failure email"
```

## Integration Testing

### Self-Check Tasks

Add validation tasks within the DAG itself:

```python
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor

@dag(...)
def pipeline():
    @task(outlets=[output_asset])
    def write_to_s3():
        upload_data("s3://bucket/output/{{ ds }}/data.parquet")

    verify = S3KeySensor(
        task_id="verify_output",
        bucket_key="s3://bucket/output/{{ ds }}/data.parquet",
        bucket_name="bucket",
        poke_interval=0,
        timeout=0,
    )

    write_to_s3() >> verify
```

### Testing DAG Runs End-to-End

```python
def test_dag_end_to_end():
    from airflow.dag_processing.dagbag import DagBag

    dagbag = DagBag(dag_folder="dags/")
    dag = dagbag.get_dag("my_pipeline")

    dagrun = dag.test()

    for ti in dagrun.get_task_instances():
        assert ti.state == TaskInstanceState.SUCCESS, (
            f"Task {ti.task_id} failed with state {ti.state}"
        )
```

## Mocking Connections and Variables

### Mock Variables via Environment

```python
from unittest import mock
from airflow.sdk import Variable

def test_task_with_variable():
    with mock.patch.dict("os.environ", AIRFLOW_VAR_API_KEY="test-key-123"):
        assert Variable.get("api_key") == "test-key-123"
```

### Mock Connections via Environment

```python
from airflow.sdk import Connection

def test_task_with_connection():
    conn = Connection(
        conn_type="postgres",
        host="localhost",
        port=5432,
        login="test_user",
        password="test_pass",
        schema="test_db",
    )
    conn_uri = conn.get_uri()

    with mock.patch.dict("os.environ", AIRFLOW_CONN_TEST_DB=conn_uri):
        from airflow.providers.postgres.hooks.postgres import PostgresHook
        hook = PostgresHook("test_db")
        assert hook.get_connection("test_db").host == "localhost"
```

### Mock with JSON Connection

```python
import json

def test_aws_connection():
    conn_json = json.dumps({
        "conn_type": "aws",
        "extra": {
            "region_name": "us-east-1",
            "aws_access_key_id": "AKIATEST",
            "aws_secret_access_key": "test-secret",
        },
    })

    with mock.patch.dict("os.environ", AIRFLOW_CONN_MY_AWS=conn_json):
        # Task code that uses aws_conn_id="my_aws"
        result = my_task_function()
        assert result is not None
```

## Testing with dag.test()

Run a DAG locally with a simplified executor:

```python
# At the bottom of your DAG file
if __name__ == "__main__":
    dag.test()
```

```bash
python dags/my_dag.py
```

### With Configuration

```python
if __name__ == "__main__":
    dag.test(
        run_conf={"source": "test_table"},
        execution_date=pendulum.datetime(2024, 3, 15, tz="UTC"),
    )
```

### With Real Executor

```python
if __name__ == "__main__":
    dag.test(use_executor=True)
```

## Staging Environments

Parameterize DAGs to support multiple environments:

```python
import os

ENV = os.environ.get("AIRFLOW_ENV", "dev")

CONFIG = {
    "dev": {"bucket": "dev-data-lake", "db": "dev_warehouse", "schedule": None},
    "staging": {"bucket": "staging-data-lake", "db": "stg_warehouse", "schedule": "@daily"},
    "prod": {"bucket": "prod-data-lake", "db": "prod_warehouse", "schedule": "@daily"},
}

@dag(
    schedule=CONFIG[ENV]["schedule"],
    tags=[ENV],
    ...
)
def etl():
    @task()
    def extract():
        bucket = CONFIG[ENV]["bucket"]
        return f"Extracted from {bucket}"
```

### Cluster Policies

Skip DAGs per environment using tags:

```python
from airflow.exceptions import AirflowClusterPolicySkipDag

def dag_policy(dag):
    if "only_for_prod" in dag.tags and ENV != "prod":
        raise AirflowClusterPolicySkipDag(f"Skipping prod-only DAG {dag.dag_id}")
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Airflow DAG Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: airflow
          POSTGRES_PASSWORD: airflow
          POSTGRES_DB: airflow
        ports: ["5432:5432"]

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          pip install apache-airflow==3.3.0 pytest
          pip install -r requirements.txt

      - name: Initialize Airflow DB
        env:
          AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@localhost/airflow
        run: airflow db migrate

      - name: Run DAG validation tests
        env:
          AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@localhost/airflow
          AIRFLOW__CORE__DAGS_FOLDER: ${{ github.workspace }}/dags
        run: pytest tests/ -v

      - name: Lint DAGs with Ruff
        run: ruff check dags/ --select AIR3
```

### Ruff Airflow Rules

```bash
pip install "ruff>=0.15.17"
ruff check dags/ --select AIR3
```

Catches:
- `AIR301` — DAG missing explicit `schedule` argument
- `AIR303` — Operator moved to a different provider in 3.0
- Other Airflow-specific code quality issues

## Related Topics

- [Best Practices](12-best-practices.md) — Anti-patterns and performance
- [DAGs](01-dags.md) — DAG declaration and parameters
- [Connections & Hooks](05-connections-and-hooks.md) — Mocking connections
