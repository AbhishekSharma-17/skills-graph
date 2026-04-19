# Dagster — Schedules & Sensors

> Source: [docs.dagster.io/guides/automate/schedules](https://docs.dagster.io/guides/automate/schedules)

## Table of Contents

- [Schedules](#schedules)
- [Schedule with RunRequest](#schedule-with-runrequest)
- [Schedule with Skip Logic](#schedule-with-skip-logic)
- [Partitioned Schedules](#partitioned-schedules)
- [Sensors](#sensors)
- [File Watcher Sensor](#file-watcher-sensor)
- [SensorResult](#sensorresult)
- [@asset_sensor](#asset_sensor)
- [@multi_asset_sensor](#multi_asset_sensor)
- [@run_status_sensor](#run_status_sensor)
- [RunRequest](#runrequest)
- [Testing Schedules & Sensors](#testing-schedules--sensors)

---

## Schedules

### ScheduleDefinition (simple)

```python
import dagster as dg

daily_schedule = dg.ScheduleDefinition(
    name="daily_refresh",
    cron_schedule="0 0 * * *",
    target=[customer_data, sales_report],
    execution_timezone="America/New_York",
    default_status=dg.DefaultScheduleStatus.RUNNING,
)
```

### @schedule decorator (dynamic)

```python
@dg.schedule(
    cron_schedule="0 0 * * *",       # standard 5-field cron or @daily/@hourly
    target="*",                       # asset selection or job
    execution_timezone="US/Eastern",
    default_status=dg.DefaultScheduleStatus.STOPPED,
    description="Daily ETL schedule",
)
def configurable_schedule(context: dg.ScheduleEvaluationContext):
    date = context.scheduled_execution_time.strftime("%Y-%m-%d")
    return dg.RunRequest(
        run_key=date,
        tags={"date": date},
    )
```

Key parameters: `cron_schedule`, `target` (replaces `job`), `execution_timezone`, `default_status`, `should_execute`, `tags_fn`.

Cron shorthand: `@daily`, `@hourly`, `@monthly`, `@weekly`, `@yearly`

### ScheduleEvaluationContext

Properties: `scheduled_execution_time` (datetime), `instance` (DagsterInstance), `resources`.

## Schedule with RunRequest

```python
@dg.schedule(target="*", cron_schedule="0 6 * * *")
def morning_schedule(context: dg.ScheduleEvaluationContext):
    date = context.scheduled_execution_time.strftime("%Y-%m-%d")
    return dg.RunRequest(
        run_key=f"morning-{date}",
        tags={"scheduled_date": date},
    )
```

## Schedule with Skip Logic

```python
@dg.schedule(target="*", cron_schedule="0 0 * * *")
def weekday_schedule(context: dg.ScheduleEvaluationContext):
    if context.scheduled_execution_time.weekday() >= 5:
        return dg.SkipReason("Skipping weekends")
    return dg.RunRequest()
```

## Partitioned Schedules

Auto-match schedule to partition cadence:

```python
daily = dg.DailyPartitionsDefinition(start_date="2024-01-01")

@dg.asset(partitions_def=daily)
def daily_data(context: dg.AssetExecutionContext): ...

daily_job = dg.define_asset_job("daily_job", selection=[daily_data], partitions_def=daily)
schedule = dg.build_schedule_from_partitioned_job(daily_job)
```

---

## Sensors

### @sensor decorator

```python
@dg.sensor(
    job=my_job,
    minimum_interval_seconds=30,
    default_status=dg.DefaultSensorStatus.RUNNING,
    description="Watches for new files",
)
def my_sensor(context: dg.SensorEvaluationContext):
    if has_new_data():
        return dg.RunRequest(run_key="new-data")
    return dg.SkipReason("No new data")
```

Key parameters: `job`/`target`, `minimum_interval_seconds`, `default_status`, `description`.

### SensorEvaluationContext

Properties: `cursor` (persisted state), `instance`, `resources`, `is_first_tick_since_sensor_start`, `last_run_key`, `last_tick_completion_time`.

Methods: `update_cursor(value)` — persist state for next tick.

## File Watcher Sensor

```python
import os

@dg.sensor(job=process_job, minimum_interval_seconds=5)
def file_sensor(context: dg.SensorEvaluationContext):
    last_mtime = float(context.cursor) if context.cursor else 0
    max_mtime = last_mtime

    for filename in os.listdir("/data/incoming"):
        filepath = os.path.join("/data/incoming", filename)
        if os.path.isfile(filepath):
            fstats = os.stat(filepath)
            if fstats.st_mtime <= last_mtime:
                continue
            yield dg.RunRequest(run_key=f"{filename}:{fstats.st_mtime}")
            max_mtime = max(max_mtime, fstats.st_mtime)

    context.update_cursor(str(max_mtime))
```

## SensorResult

Structured return for sensors:

```python
@dg.sensor(job=my_job)
def structured_sensor(context: dg.SensorEvaluationContext):
    new_items = check_for_new_items()
    if not new_items:
        return dg.SensorResult(skip_reason="No new items")

    return dg.SensorResult(
        run_requests=[dg.RunRequest(run_key=item.id) for item in new_items],
        cursor=str(new_items[-1].id),
        dynamic_partitions_requests=[
            customer_partitions.build_add_request([i.customer_id for i in new_items]),
        ],
    )
```

## @asset_sensor

Triggers when a specific asset is materialized:

```python
@dg.asset_sensor(asset_key=dg.AssetKey("daily_sales"), job=report_job)
def sales_sensor(context: dg.SensorEvaluationContext, asset_event):
    materialization = asset_event.dagster_event.event_specific_data.materialization
    yield dg.RunRequest(run_key=context.cursor)
```

## @multi_asset_sensor

Monitors multiple assets (deprecated — prefer declarative automation):

```python
@dg.multi_asset_sensor(
    monitored_assets=[dg.AssetKey("asset_a"), dg.AssetKey("asset_b")],
    job=downstream_job,
)
def combined_sensor(context):
    records = context.latest_materialization_records_by_key()
    if all(records.values()):
        context.advance_all_cursors()
        return dg.RunRequest()
```

## @run_status_sensor

Reacts to run status changes (e.g., failures):

```python
@dg.run_status_sensor(
    run_status=dg.DagsterRunStatus.FAILURE,
    monitored_jobs=[my_job],
)
def failure_alert(context: dg.RunStatusSensorContext):
    context.log.info(f"Run {context.dagster_run.run_id} failed")
    send_slack_alert(context.dagster_run.run_id)

# Shorthand for failures
@dg.run_failure_sensor(monitored_jobs=[my_job])
def on_failure(context: dg.RunFailureSensorContext):
    events = context.get_step_failure_events()
    send_alert(events)
```

## RunRequest

```python
dg.RunRequest(
    run_key="unique-key",           # deduplication
    run_config=None,                # RunConfig or dict
    tags={"env": "prod"},           # run tags
    job_name=None,                  # required for multi-job sensors
    asset_selection=None,           # specific assets
    partition_key=None,             # target partition
    stale_assets_only=False,        # only stale assets
)
```

## Testing Schedules & Sensors

```python
def test_file_sensor():
    context = dg.build_sensor_context(cursor="0")
    result = file_sensor(context)
    assert isinstance(result, dg.RunRequest)

def test_schedule():
    from datetime import datetime
    context = dg.build_schedule_context(
        scheduled_execution_time=datetime(2024, 1, 15, 0, 0, 0)
    )
    result = configurable_schedule(context)
    assert isinstance(result, dg.RunRequest)
```
