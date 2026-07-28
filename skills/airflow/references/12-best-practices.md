# Best Practices

> Source: [airflow.apache.org/docs/…/best-practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html) · v3.3.0

## Table of Contents

- [Idempotency](#idempotency)
- [Top-Level Code](#top-level-code)
- [Task Communication](#task-communication)
- [Error Handling](#error-handling)
- [Performance](#performance)
- [Security](#security)
- [Anti-Patterns](#anti-patterns)
- [DAG Organization](#dag-organization)

## Idempotency

Tasks should produce identical results when re-run with the same inputs. This is the most important Airflow principle — tasks will be retried on failure and backfilled over historical dates.

### Use UPSERT, Not INSERT

```python
# BAD — duplicates on retry
@task()
def load(records):
    db.execute("INSERT INTO summary VALUES (%s, %s)", records)

# GOOD — idempotent
@task()
def load(records, ds=None):
    db.execute("""
        INSERT INTO summary (date, total)
        VALUES (%s, %s)
        ON CONFLICT (date) DO UPDATE SET total = EXCLUDED.total
    """, (ds, sum(records)))
```

### Use Data Intervals, Not datetime.now()

```python
# BAD — different results each execution
@task()
def extract():
    return db.query("SELECT * FROM events WHERE created_at > NOW() - INTERVAL '1 day'")

# GOOD — deterministic based on data interval
@task()
def extract(data_interval_start=None, data_interval_end=None):
    return db.query(
        "SELECT * FROM events WHERE created_at >= %s AND created_at < %s",
        (data_interval_start, data_interval_end),
    )
```

### Partition by Date

```python
# BAD — "latest" changes between executions
@task()
def write_output(data):
    write_to_s3(data, "s3://bucket/output/latest.parquet")

# GOOD — partition by execution date
@task()
def write_output(data, ds=None):
    write_to_s3(data, f"s3://bucket/output/dt={ds}/data.parquet")
```

## Top-Level Code

DAG files are parsed every `min_file_process_interval` seconds (default 30s). Expensive operations at the module level dramatically slow the scheduler.

### Avoid Expensive Imports at Top Level

```python
# BAD — pandas imported every 30 seconds
import pandas as pd

@task()
def process():
    df = pd.read_csv("data.csv")

# GOOD — import inside task function
@task()
def process():
    import pandas as pd
    df = pd.read_csv("data.csv")
```

### Never Call APIs or DB at Top Level

```python
# BAD — API call every 30 seconds during parsing
from airflow.sdk import Variable
config = Variable.get("config", deserialize_json=True)  # DB call!
api_data = requests.get("https://api.example.com/config").json()  # API call!

# GOOD — defer to execution time
@task()
def get_config():
    config = Variable.get("config", deserialize_json=True)
    return config

# ALSO GOOD — use Jinja templates
BashOperator(
    task_id="run",
    bash_command="echo {{ var.value.api_key }}",  # Resolved at execution, not parse time
)
```

### Variables in Templates

| Method | Runs During | Use |
|--------|-------------|-----|
| `Variable.get()` in task | Task execution | Always safe |
| `{{ var.value.key }}` | Task execution | Templates in operators |
| `{{ var.json.key.subkey }}` | Task execution | JSON variable fields |
| `Variable.get()` at module level | DAG parsing | **Never do this** |

## Task Communication

### Use XCom for Metadata Only

```python
# BAD — passing large data through XCom
@task()
def extract():
    df = pd.read_csv("large_file.csv")  # 500MB DataFrame
    return df.to_dict()  # Serialized into metadata DB!

# GOOD — pass the path, not the data
@task()
def extract(ds=None):
    df = pd.read_csv("large_file.csv")
    path = f"s3://bucket/staging/{ds}/data.parquet"
    df.to_parquet(path)
    return path  # Small string in XCom

@task()
def transform(path: str):
    df = pd.read_parquet(path)
    # ...
```

### Don't Store Files Locally

Tasks may run on different machines (Kubernetes pods, Celery workers):

```python
# BAD — file may not exist on the next worker
@task()
def write():
    with open("/tmp/data.csv", "w") as f:
        f.write(data)

@task()
def read():
    with open("/tmp/data.csv") as f:  # Different machine!
        return f.read()

# GOOD — use remote storage
@task()
def write():
    s3_hook.load_string(data, "s3://bucket/data.csv")

@task()
def read():
    return s3_hook.read_key("s3://bucket/data.csv")
```

### Never Hardcode Secrets

```python
# BAD
@task()
def call_api():
    requests.get("https://api.example.com", headers={"Authorization": "Bearer sk-12345"})

# GOOD — use Connections
@task()
def call_api():
    http_hook = HttpHook(http_conn_id="my_api")
    response = http_hook.run(endpoint="/data")
    return response.json()
```

## Error Handling

### Retries and Exponential Backoff

```python
@task(
    retries=3,
    retry_delay=timedelta(minutes=2),
    retry_exponential_backoff=True,
    max_retry_delay=timedelta(minutes=30),
)
def flaky_api_call():
    response = requests.get("https://unreliable-api.com/data")
    response.raise_for_status()
    return response.json()
```

### Callbacks

```python
def on_failure(context):
    task_id = context["task_instance"].task_id
    dag_id = context["dag"].dag_id
    send_slack_alert(f"Task {dag_id}.{task_id} failed!")

def on_success(context):
    log_metric("task_success", 1)

@dag(
    on_failure_callback=on_failure,
    ...
)
def pipeline():
    @task(on_success_callback=on_success)
    def process():
        return "done"
```

### SLA Monitoring

```python
@dag(
    sla_miss_callback=sla_alert,
    ...
)
def time_sensitive():
    @task(sla=timedelta(hours=2))  # Alert if task takes >2 hours
    def critical_transform():
        return process()
```

### Watcher Pattern

Ensure the DAG fails if any parallel branch fails:

```python
from airflow.utils.trigger_rule import TriggerRule
from airflow.exceptions import AirflowException

@task(trigger_rule=TriggerRule.ONE_FAILED, retries=0)
def watcher():
    raise AirflowException("Upstream task failed")

@dag(...)
def parallel_pipeline():
    t1 = branch_a()
    t2 = branch_b()
    cleanup = teardown_resources()

    [t1, t2] >> cleanup
    [t1, t2, cleanup] >> watcher()
```

## Performance

### DAG Parsing Speed

The single biggest performance lever. Optimize to keep parse time under 5 seconds:

```bash
# Measure parse time
time python dags/my_dag.py
```

- Move heavy imports inside task functions
- Avoid `Variable.get()` at module level
- Use `.airflowignore` to skip non-DAG files
- Split large DAG files (one DAG per file for large DAGs)

### Scheduler Tuning

```ini
[scheduler]
min_file_process_interval = 30    # Seconds between re-parsing a DAG file
parsing_processes = 4              # Parallel DAG parsing processes
scheduler_idle_sleep_time = 1      # Seconds scheduler waits when idle
max_dagruns_to_create_per_loop = 10

[core]
parallelism = 32                   # Max concurrent task instances
max_active_tasks_per_dag = 16      # Max concurrent tasks per DAG
max_active_runs_per_dag = 16       # Max concurrent DAG runs per DAG
```

### Reduce DAG Complexity

```python
# BAD — deeply nested tree creates scheduling overhead
for i in range(100):
    for j in range(10):
        task = create_task(i, j)

# GOOD — flatter structures are more efficient
@task_group()
def batch(items):
    for item in items:
        process(item)

batch(items[:50])
batch(items[50:])
```

### Database Maintenance

```bash
# Clean metadata older than 90 days
airflow db clean --clean-before-timestamp "$(date -d '90 days ago' +%Y-%m-%d)"
```

### Dependency Isolation

```python
# For tasks needing different Python packages
@task.virtualenv(requirements=["pandas==2.2.0", "numpy>=1.26"])
def process_with_pandas():
    import pandas as pd
    return pd.read_csv("data.csv").shape[0]

@task.external_python(python="/opt/venvs/ml/bin/python")
def train_model():
    import tensorflow as tf
    return tf.keras.models.load_model("/models/latest").evaluate(test)

@task.docker(image="my-spark:latest")
def spark_job():
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.getOrCreate()
    return spark.sql("SELECT COUNT(*) FROM events").collect()
```

## Security

### Fernet Key

Encrypt connection passwords:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

```ini
[core]
fernet_key = your-generated-fernet-key
```

### RBAC Roles

| Role | Permissions |
|------|-------------|
| Admin | Full access |
| Op | DAG runs, connections, variables |
| User | View DAGs, trigger runs |
| Viewer | Read-only access |
| Public | No access (default for unauthenticated) |

### Configuration Security

```ini
[webserver]
expose_config = False           # Hide config in UI
secret_key = your-secret-key    # For session signing

[api]
auth_backends = airflow.api.auth.backend.basic_auth
```

### Secrets Best Practices

1. Use a secrets backend (Vault, AWS SM, GCP SM) — not the database
2. Never store secrets in DAG code or Variables
3. Use Connections for all external credentials
4. Rotate Fernet keys periodically
5. Set `expose_config = False` in production

## Anti-Patterns

| Anti-Pattern | Impact | Fix |
|-------------|--------|-----|
| `Variable.get()` at top level | DB call every parse cycle | Use `{{ var.value.x }}` |
| Heavy imports at top level | Slow scheduler | Import inside tasks |
| `datetime.now()` in tasks | Non-deterministic results | Use `data_interval_start` |
| `INSERT` without conflict handling | Duplicates on retry | Use `UPSERT` |
| Local file storage | Lost on distributed exec | Use S3/GCS |
| Deleting tasks from DAGs | Lost logs and history | Create new DAG |
| Secrets in code/Variables | Security risk | Use Connections |
| Triggering immediately after deploy | DAG not yet parsed | Wait for parser |
| Multiple DAGs per file | Scaling issues | One DAG per file |
| Deeply nested task trees | Scheduler overhead | Flatten structures |
| Large XCom payloads | Database bloat | Pass paths, not data |
| `trigger_rule=all_success` after branches | Tasks skip unexpectedly | Use `none_failed_min_one_success` |

## DAG Organization

### Recommended Directory Structure

```
airflow-project/
├── dags/
│   ├── etl/
│   │   ├── __init__.py
│   │   ├── ingest.py          # One DAG per file
│   │   ├── transform.py
│   │   └── load.py
│   ├── ml/
│   │   ├── __init__.py
│   │   ├── training.py
│   │   └── inference.py
│   └── utils/
│       ├── __init__.py
│       ├── helpers.py         # Shared business logic
│       └── constants.py
├── plugins/
│   ├── operators/
│   │   └── custom_operator.py
│   └── hooks/
│       └── custom_hook.py
├── tests/
│   ├── test_dag_integrity.py
│   ├── test_etl.py
│   └── test_operators.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yaml
└── .airflowignore
```

### Naming Conventions

- DAG IDs: `domain_action` (e.g., `analytics_daily_etl`, `ml_model_training`)
- Task IDs: `verb_noun` (e.g., `extract_users`, `transform_orders`, `load_warehouse`)
- Connections: `system_environment` (e.g., `postgres_production`, `s3_analytics`)
- Variables: `UPPER_SNAKE_CASE` in UI, `lower_snake_case` in templates

### Documentation

```python
@dag(
    description="Daily ETL pipeline: extracts user events from PostgreSQL, "
                "transforms with deduplication, loads to Snowflake warehouse.",
    doc_md="""
    ## Daily User Events ETL

    **Owner:** data-eng team
    **SLA:** Complete by 06:00 UTC
    **Upstream:** PostgreSQL replica (events table)
    **Downstream:** Snowflake analytics.user_events

    ### Troubleshooting
    - If extract fails: check PostgreSQL replica lag
    - If load fails: verify Snowflake connection in Admin > Connections
    """,
    tags=["etl", "production", "daily"],
    ...
)
def daily_user_events():
    ...
```

## Related Topics

- [Testing](10-testing.md) — DAG validation and CI/CD
- [Deployment](11-deployment.md) — Production configuration
- [XComs & Variables](04-xcoms-and-variables.md) — Safe data passing
