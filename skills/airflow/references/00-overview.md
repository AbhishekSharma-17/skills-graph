# Apache Airflow Overview

> Source: [airflow.apache.org/docs](https://airflow.apache.org/docs/apache-airflow/stable/) · v3.3.0

## What Is Airflow?

Apache Airflow is an open-source platform for developing, scheduling, and monitoring batch-oriented workflows. Workflows are defined as Python code (DAGs — Directed Acyclic Graphs), making them versionable, testable, and collaborative.

Airflow is **not** a streaming solution or data processing framework. It orchestrates when and where work runs, not how data is transformed. Use Airflow to coordinate Spark jobs, dbt models, API calls, and ML training — not to process data row-by-row.

## When to Use Airflow

| Good Fit | Poor Fit |
|----------|----------|
| ETL/ELT pipelines | Real-time event streaming |
| ML training/inference scheduling | Sub-second latency requirements |
| Data warehouse loading | Infinitely running processes |
| Report generation | Simple cron jobs (use cron directly) |
| Cross-system orchestration | Data transformation logic (use Spark/dbt) |
| Backfill historical data | CI/CD pipelines (use GitHub Actions) |

## Architecture

Airflow 3.x uses a service-oriented architecture with these core components:

### Scheduler
Monitors all DAGs and triggers task instances when dependencies are met. Submits tasks to the configured executor.

### API Server
Serves the REST API and the web UI (React-based in Airflow 3.x). Runs on port 8080 by default.

### DAG Processor
Parses DAG files from the `dags/` folder and builds the internal DAG representation. Runs independently from the scheduler in Airflow 3.x.

### Executor
Determines how tasks run: locally, on Celery workers, in Kubernetes pods, or on AWS ECS/Batch. Multiple executors can run simultaneously.

### Worker
Executes the actual task logic. In CeleryExecutor, workers pull from a Redis/RabbitMQ queue. In KubernetesExecutor, each task runs in its own pod.

### Triggerer
Handles deferrable operators — tasks that release their worker slot while waiting for an external condition, then resume when the condition is met.

### Metadata Database
PostgreSQL (production) or SQLite (development only) stores DAG definitions, task states, XComs, connections, variables, and audit logs.

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  DAG Files   │───▶│ DAG Processor│───▶│   Metadata   │
│  (Python)    │    │              │    │   Database   │
└──────────────┘    └──────────────┘    └──────┬───────┘
                                               │
                    ┌──────────────┐    ┌───────▼──────┐
                    │  API Server  │◀──▶│  Scheduler   │
                    │  (UI + REST) │    │              │
                    └──────────────┘    └───────┬──────┘
                                               │
                    ┌──────────────┐    ┌───────▼──────┐
                    │  Triggerer   │    │   Executor   │
                    │ (Deferrable) │    │              │
                    └──────────────┘    └───────┬──────┘
                                               │
                                       ┌───────▼──────┐
                                       │   Workers    │
                                       └──────────────┘
```

## Airflow 3.x Key Changes

Airflow 3.0 introduced the most significant changes since the 2.0 release:

### New SDK Namespace
DAG authors now import from `airflow.sdk`:

```python
from airflow.sdk import DAG, dag, task, asset, chain, cross_downstream
```

### Task Execution API
Tasks can execute remotely via a new Task Execution Interface, enabling polyglot task development (Java, Go, R) alongside Python.

### DAG Versioning
DAGs are versioned on deployment. Historical runs preserve their exact DAG version — no more execution drift from retroactive changes.

### Asset-Driven Scheduling
The `@asset` decorator treats data outputs as first-class orchestration objects. DAGs trigger based on data availability, not just time.

### Scheduler-Managed Backfills
Backfills run through the main scheduler with unified execution, UI/API/CLI triggering, and cancellable runs.

### Modernized UI
React + FastAPI backend with dark mode, improved grid/graph views, and an asset lineage panel.

## Installation

### pip (standalone)

```bash
pip install "apache-airflow==3.3.0" \
  --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-3.3.0/constraints-3.12.txt"
```

### Docker Compose (development)

```bash
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/3.3.0/docker-compose.yaml'
mkdir -p ./dags ./logs ./plugins ./config
echo -e "AIRFLOW_UID=$(id -u)" > .env
docker compose up airflow-init
docker compose up
```

Access the UI at `http://localhost:8080` (user: `airflow`, password: `airflow`).

### Kubernetes (production)

```bash
helm repo add apache-airflow https://airflow.apache.org
helm install airflow apache-airflow/airflow --namespace airflow --create-namespace
```

## Minimal DAG Example

```python
from airflow.sdk import dag, task
import pendulum

@dag(
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    schedule="@daily",
    catchup=False,
    tags=["example"],
)
def my_first_dag():

    @task()
    def extract():
        return {"data": [1, 2, 3]}

    @task()
    def transform(raw: dict):
        return {"total": sum(raw["data"])}

    @task()
    def load(result: dict):
        print(f"Loaded total: {result['total']}")

    raw = extract()
    result = transform(raw)
    load(result)

my_first_dag()
```

## CLI Quick Reference

```bash
# DAG operations
airflow dags list                        # List all DAGs
airflow dags trigger my_dag              # Trigger a DAG run
airflow dags test my_dag 2024-01-01      # Test a DAG locally
airflow dags pause my_dag                # Pause a DAG
airflow dags unpause my_dag              # Unpause a DAG

# Task operations
airflow tasks list my_dag                # List tasks in a DAG
airflow tasks test my_dag my_task 2024-01-01  # Test a single task
airflow tasks run my_dag my_task 2024-01-01   # Run a single task

# Database
airflow db migrate                       # Apply migrations
airflow db check                         # Verify DB connectivity
airflow db clean                         # Prune old metadata

# Users (if using built-in auth)
airflow users create --username admin --role Admin --email admin@example.com

# Info
airflow info                             # System info
airflow version                          # Print version
airflow config list                      # Show configuration
```

## Provider Packages

Airflow's integration ecosystem ships as separate provider packages:

```bash
pip install apache-airflow-providers-google      # GCP (BigQuery, GCS, Dataflow)
pip install apache-airflow-providers-amazon      # AWS (S3, Redshift, EMR, ECS)
pip install apache-airflow-providers-microsoft-azure  # Azure (Blob, Synapse)
pip install apache-airflow-providers-postgres     # PostgreSQL
pip install apache-airflow-providers-snowflake    # Snowflake
pip install apache-airflow-providers-databricks   # Databricks
pip install apache-airflow-providers-dbt-cloud    # dbt Cloud
pip install apache-airflow-providers-slack        # Slack notifications
pip install apache-airflow-providers-http         # HTTP operators
pip install apache-airflow-providers-docker       # Docker operators
pip install apache-airflow-providers-celery       # CeleryExecutor
pip install apache-airflow-providers-cncf-kubernetes  # KubernetesExecutor
```

## Key Configuration

Configuration lives in `airflow.cfg` or environment variables (`AIRFLOW__SECTION__KEY`):

```ini
[core]
dags_folder = /opt/airflow/dags
executor = CeleryExecutor
max_active_runs_per_dag = 16
max_active_tasks_per_dag = 16

[scheduler]
min_file_process_interval = 30
parsing_processes = 2

[database]
sql_alchemy_conn = postgresql+psycopg2://airflow:airflow@postgres/airflow

[celery]
broker_url = redis://redis:6379/0
result_backend = db+postgresql://airflow:airflow@postgres/airflow
```

Environment variable override:
```bash
export AIRFLOW__CORE__EXECUTOR=KubernetesExecutor
export AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://user:pass@host/db
```

## Related Topics

- [DAGs](01-dags.md) — DAG declaration, dependencies, control flow
- [TaskFlow API](02-taskflow-api.md) — Modern decorator-based DAG authoring
- [Deployment](11-deployment.md) — Production setup with Docker and Kubernetes
