# Scheduling

> Source: [airflow.apache.org/docs/…/scheduling](https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/) · v3.3.0

## Table of Contents

- [Schedule Parameter](#schedule-parameter)
- [Cron Expressions](#cron-expressions)
- [Time Zones](#time-zones)
- [Data Intervals](#data-intervals)
- [Catchup and Backfill](#catchup-and-backfill)
- [Asset-Aware Scheduling](#asset-aware-scheduling)
- [Timetables](#timetables)
- [Event-Driven Scheduling](#event-driven-scheduling)

## Schedule Parameter

The `schedule` parameter controls when a DAG runs:

```python
from airflow.sdk import dag

@dag(schedule="@daily", ...)           # Preset
@dag(schedule="0 6 * * *", ...)        # Cron
@dag(schedule=timedelta(hours=2), ...) # Interval
@dag(schedule=None, ...)               # Manual only
@dag(schedule=[asset1, asset2], ...)   # Asset-driven
@dag(schedule=my_timetable, ...)       # Custom timetable
```

### Presets

| Preset | Cron | Interval |
|--------|------|----------|
| `@once` | — | Run once, never again |
| `@continuous` | — | Run immediately after previous completes |
| `@hourly` | `0 * * * *` | Every hour |
| `@daily` | `0 0 * * *` | Every day at midnight |
| `@weekly` | `0 0 * * 0` | Every Sunday at midnight |
| `@monthly` | `0 0 1 * *` | First day of every month |
| `@quarterly` | `0 0 1 */3 *` | First day of every quarter |
| `@yearly` | `0 0 1 1 *` | January 1st |
| `None` | — | Manually triggered only |

## Cron Expressions

```
┌────────── minute (0-59)
│ ┌──────── hour (0-23)
│ │ ┌────── day of month (1-31)
│ │ │ ┌──── month (1-12)
│ │ │ │ ┌── day of week (0-6, Sun=0)
│ │ │ │ │
* * * * *
```

| Expression | Meaning |
|------------|---------|
| `0 6 * * *` | Daily at 6:00 AM |
| `0 6 * * 1-5` | Weekdays at 6:00 AM |
| `*/15 * * * *` | Every 15 minutes |
| `0 0,12 * * *` | Midnight and noon |
| `0 9 1 * *` | 9:00 AM on the 1st of each month |
| `0 0 * * 0` | Every Sunday at midnight |
| `30 2 * * 1#1` | 2:30 AM on first Monday of month |

## Time Zones

Airflow stores all dates internally as UTC. Use `pendulum` for timezone-aware scheduling:

```python
import pendulum

@dag(
    start_date=pendulum.datetime(2024, 1, 1, tz="America/New_York"),
    schedule="0 9 * * 1-5",  # 9 AM ET on weekdays
)
def ny_business_hours():
    ...
```

The UI displays times in the user's configured timezone. DAG runs use the timezone from `start_date` for cron evaluation (handles DST transitions automatically).

## Data Intervals

Each DAG run processes a specific time window called the **data interval**:

```
Interval: [data_interval_start, data_interval_end)
```

For a daily DAG starting 2024-01-01:
- Run 1: interval `[2024-01-01 00:00, 2024-01-02 00:00)` → runs at `2024-01-02 00:00`
- Run 2: interval `[2024-01-02 00:00, 2024-01-03 00:00)` → runs at `2024-01-03 00:00`

Access in tasks:

```python
@task()
def process_interval(data_interval_start=None, data_interval_end=None):
    print(f"Processing data from {data_interval_start} to {data_interval_end}")
```

Or in templates:

```python
BashOperator(
    task_id="extract",
    bash_command=(
        "python extract.py "
        "--start '{{ data_interval_start }}' "
        "--end '{{ data_interval_end }}'"
    ),
)
```

## Catchup and Backfill

### Catchup

When a DAG has `start_date` in the past, `catchup=True` (default) creates runs for every missed interval:

```python
@dag(
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    schedule="@daily",
    catchup=True,   # Creates runs for all days since Jan 1
)
def backfill_dag():
    ...
```

Set `catchup=False` to skip past intervals and only run from the current time:

```python
@dag(
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    schedule="@daily",
    catchup=False,  # Only runs for current/future intervals
)
def no_backfill_dag():
    ...
```

### Backfill (CLI)

Manually backfill specific date ranges:

```bash
airflow dags backfill my_dag \
    --start-date 2024-03-01 \
    --end-date 2024-03-15 \
    --reset-dagruns  # Clear existing runs in range
```

In Airflow 3.x, backfills are scheduler-managed — they run through the main scheduler with unified execution, UI support, and are cancellable.

## Asset-Aware Scheduling

Schedule DAGs to run when upstream data is updated (see [Assets](08-assets.md) for full details):

```python
from airflow.sdk import Asset, dag, task

raw_data = Asset("s3://data-lake/raw/events.parquet")
user_data = Asset("s3://data-lake/raw/users.parquet")

# Producer DAG — emits asset events
@dag(schedule="@hourly")
def ingest():
    @task(outlets=[raw_data])
    def write_events():
        return "wrote events"

    write_events()

# Consumer DAG — triggered when assets update
@dag(schedule=[raw_data, user_data])  # Waits for BOTH assets
def transform():
    @task()
    def join_data():
        return "joined"

    join_data()

ingest()
transform()
```

### Conditional Asset Scheduling

```python
from airflow.sdk import Asset

asset_a = Asset("s3://bucket/a")
asset_b = Asset("s3://bucket/b")
asset_c = Asset("s3://bucket/c")

# AND — all must update
@dag(schedule=(asset_a & asset_b & asset_c))
def needs_all(): ...

# OR — any one triggers
@dag(schedule=(asset_a | asset_b))
def needs_any(): ...

# Mixed
@dag(schedule=((asset_a & asset_b) | asset_c))
def mixed_schedule(): ...
```

## Timetables

Custom scheduling logic beyond cron expressions:

### Built-in Timetables

```python
from airflow.timetables.trigger import CronTriggerTimetable
from airflow.timetables.simple import NullTimetable

# Trigger at specific times (no data interval)
@dag(schedule=CronTriggerTimetable("0 9 * * 1-5", timezone="UTC"))
def triggered_dag(): ...
```

### Custom Timetable

```python
from airflow.timetables.base import DagRunInfo, DataInterval, Timetable
from pendulum import DateTime, Duration

class BusinessDayTimetable(Timetable):
    def next_dagrun_info(
        self,
        *,
        last_automated_data_interval: DataInterval | None,
        restriction,
    ) -> DagRunInfo | None:
        if last_automated_data_interval is None:
            next_start = restriction.earliest
        else:
            next_start = last_automated_data_interval.end

        # Skip weekends
        while next_start.day_of_week in (5, 6):  # Saturday, Sunday
            next_start = next_start.add(days=1)

        next_end = next_start.add(days=1)
        while next_end.day_of_week in (5, 6):
            next_end = next_end.add(days=1)

        if restriction.latest is not None and next_start > restriction.latest:
            return None

        return DagRunInfo.interval(start=next_start, end=next_end)
```

Register via a plugin:

```python
from airflow.plugins_manager import AirflowPlugin

class BusinessDayPlugin(AirflowPlugin):
    name = "business_day_timetable"
    timetables = [BusinessDayTimetable]
```

## Event-Driven Scheduling

Airflow 3.x supports external event triggers:

### AWS SQS Trigger

```python
from airflow.providers.amazon.aws.triggers.sqs import SqsSensorTrigger

@dag(schedule=SqsSensorTrigger(sqs_queue="my-queue", aws_conn_id="my_aws"))
def event_driven(): ...
```

### HTTP Webhook

Trigger DAGs via the REST API:

```bash
curl -X POST "http://localhost:8080/api/v1/dags/my_dag/dagRuns" \
    -H "Content-Type: application/json" \
    -H "Authorization: Basic $(echo -n 'airflow:airflow' | base64)" \
    -d '{"conf": {"event": "new_data_arrived"}}'
```

### TriggerDagRunOperator

Cross-DAG triggering within Airflow:

```python
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator

trigger_downstream = TriggerDagRunOperator(
    task_id="trigger_transform",
    trigger_dag_id="transform_pipeline",
    conf={"source": "{{ ds }}"},
    wait_for_completion=True,
    poke_interval=60,
)
```

## Related Topics

- [Assets](08-assets.md) — Data-aware scheduling with @asset decorator
- [DAGs](01-dags.md) — DAG parameters including schedule
- [Best Practices](12-best-practices.md) — Scheduling anti-patterns
