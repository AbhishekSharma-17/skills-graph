# Dagster — Partitions & Backfills

> Source: [docs.dagster.io/concepts/partitions-schedules-sensors/partitioning-assets](https://docs.dagster.io/concepts/partitions-schedules-sensors/partitioning-assets)

## Table of Contents

- [Time-Based Partitions](#time-based-partitions)
- [StaticPartitionsDefinition](#staticpartitionsdefinition)
- [DynamicPartitionsDefinition](#dynamicpartitionsdefinition)
- [MultiPartitionsDefinition](#multipartitionsdefinition)
- [Custom Time Windows](#custom-time-windows)
- [Partitioned Asset Example](#partitioned-asset-example)
- [Partition Mappings](#partition-mappings)
- [Cross-Cadence Dependencies](#cross-cadence-dependencies)
- [BackfillPolicy](#backfillpolicy)
- [Scheduling Partitioned Assets](#scheduling-partitioned-assets)
- [Best Practices](#best-practices)

---

## Time-Based Partitions

### DailyPartitionsDefinition

```python
import dagster as dg

daily = dg.DailyPartitionsDefinition(
    start_date="2024-01-01",
    end_date=None,              # open-ended
    timezone="America/New_York",
    fmt="%Y-%m-%d",
    hour_offset=0,              # partition boundary hour
    end_offset=0,               # extend partition set
)
```

### HourlyPartitionsDefinition

```python
hourly = dg.HourlyPartitionsDefinition(
    start_date="2024-01-01-00:00",
    timezone="UTC",
    fmt="%Y-%m-%d-%H:%M",
)
```

### WeeklyPartitionsDefinition

```python
weekly = dg.WeeklyPartitionsDefinition(
    start_date="2024-01-01",
    day_offset=1,  # 0=Sunday, 1=Monday, ..., 6=Saturday
)
```

### MonthlyPartitionsDefinition

```python
monthly = dg.MonthlyPartitionsDefinition(
    start_date="2024-01-01",
    day_offset=1,  # day of month (1-31)
)
```

## StaticPartitionsDefinition

Fixed set of partition keys:

```python
region_partitions = dg.StaticPartitionsDefinition(["us", "eu", "jp", "au"])

@dg.asset(partitions_def=region_partitions)
def regional_data(context: dg.AssetExecutionContext) -> None:
    region = context.partition_key  # "us", "eu", etc.
    data = fetch_data_for_region(region)
```

## DynamicPartitionsDefinition

Partitions created at runtime via sensors:

```python
customer_partitions = dg.DynamicPartitionsDefinition(name="customers")

@dg.asset(partitions_def=customer_partitions)
def customer_report(context: dg.AssetExecutionContext) -> None:
    customer_id = context.partition_key
    generate_report(customer_id)

@dg.sensor(job=customer_job)
def new_customer_sensor(context: dg.SensorEvaluationContext):
    new_ids = fetch_new_customer_ids()
    return dg.SensorResult(
        run_requests=[dg.RunRequest(partition_key=c) for c in new_ids],
        dynamic_partitions_requests=[
            customer_partitions.build_add_request(new_ids),
        ],
    )
```

## MultiPartitionsDefinition

Two-dimensional partitioning:

```python
daily = dg.DailyPartitionsDefinition(start_date="2024-01-01")
regions = dg.StaticPartitionsDefinition(["us", "eu", "jp"])

two_d = dg.MultiPartitionsDefinition({"date": daily, "region": regions})

@dg.asset(partitions_def=two_d)
def daily_regional_data(context: dg.AssetExecutionContext) -> None:
    keys: dg.MultiPartitionKey = context.partition_key
    date = keys.keys_by_dimension["date"]     # "2024-01-15"
    region = keys.keys_by_dimension["region"] # "us"
```

Partition key format: `"2024-01-15|us"` (pipe-separated).

## Custom Time Windows

```python
from datetime import datetime

market_holidays = [
    datetime.strptime(d, "%Y-%m-%d")
    for d in ["2024-01-01", "2024-12-25"]
]

trading_days = dg.TimeWindowPartitionsDefinition(
    cron_schedule="0 0 * * 1-5",  # weekdays only
    start=datetime(2024, 1, 1),
    fmt="%Y-%m-%d",
    exclusions=market_holidays,
    timezone="America/New_York",
)
```

## Partitioned Asset Example

```python
import pandas as pd

daily = dg.DailyPartitionsDefinition(start_date="2024-01-01")

@dg.asset(partitions_def=daily, group_name="ingestion")
def daily_events(context: dg.AssetExecutionContext) -> pd.DataFrame:
    date = context.partition_key
    start, end = context.partition_time_window
    context.log.info(f"Processing {date}: {start} to {end}")
    return pd.DataFrame({"date": [date], "events": [100]})

@dg.asset(partitions_def=daily, group_name="transform")
def daily_summary(daily_events: pd.DataFrame) -> pd.DataFrame:
    return daily_events.groupby("date").sum()
```

## Partition Mappings

Control how partitions map between upstream and downstream:

```python
# Identity — same partitioning (default)
dg.IdentityPartitionMapping()

# Time window — map across cadences with offsets
dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=0)

# All — every downstream partition depends on ALL upstream partitions
dg.AllPartitionMapping()

# Last — all downstream partitions depend on the LAST upstream partition
dg.LastPartitionMapping()

# Static — explicit mapping between static partitions
dg.StaticPartitionMapping(
    downstream_partition_keys_by_upstream_partition_key={
        "us": ["north_america"],
        "ca": ["north_america"],
        "uk": ["europe"],
        "de": ["europe"],
    }
)

# Specific — map to specific upstream partitions
dg.SpecificPartitionsPartitionMapping(partition_keys=["2024-01-01", "2024-01-02"])
```

Usage in `AssetIn`:

```python
@dg.asset(
    partitions_def=daily,
    ins={"hourly_data": dg.AssetIn(partition_mapping=dg.TimeWindowPartitionMapping())},
)
def daily_aggregate(hourly_data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    return pd.concat(list(hourly_data.values()))
```

## Cross-Cadence Dependencies

```python
hourly = dg.HourlyPartitionsDefinition(start_date="2024-01-01-00:00")
daily = dg.DailyPartitionsDefinition(start_date="2024-01-01")

@dg.asset(partitions_def=hourly)
def hourly_events() -> pd.DataFrame:
    return pd.DataFrame({"count": [1]})

@dg.asset(partitions_def=daily)
def daily_summary(hourly_events: dict[str, pd.DataFrame]) -> pd.DataFrame:
    return pd.concat(list(hourly_events.values()))
```

When an asset with coarser partitioning depends on a finer one, the I/O manager loads all matching upstream partitions as a `dict[str, T]`.

## BackfillPolicy

Controls how backfills execute:

```python
# Default (no policy): N partitions = N separate runs

# Single-run — one run covers entire partition range
@dg.asset(
    partitions_def=daily,
    backfill_policy=dg.BackfillPolicy.single_run(),
)
def events(context: dg.AssetExecutionContext) -> None:
    start, end = context.partition_time_window
    process_range(start, end)

# Multi-run — batched execution
@dg.asset(
    partitions_def=daily,
    backfill_policy=dg.BackfillPolicy.multi_run(max_partitions_per_run=10),
)
def batched_events(context: dg.AssetExecutionContext) -> None:
    for key in context.partition_keys:
        process_partition(key)
```

For single-run backfills, use `context.partition_time_window` or `context.partition_key_range` instead of `context.partition_key`.

## Scheduling Partitioned Assets

```python
daily_job = dg.define_asset_job("daily_job", selection=[daily_events], partitions_def=daily)

# Auto-match partition cadence
schedule = dg.build_schedule_from_partitioned_job(daily_job)

# Manual multi-partition schedule
@dg.schedule(job=daily_regional_job, cron_schedule="0 1 * * *")
def daily_regional_schedule(context: dg.ScheduleEvaluationContext):
    from datetime import timedelta
    date = (context.scheduled_execution_time.date() - timedelta(days=1)).strftime("%Y-%m-%d")
    return [
        dg.RunRequest(
            run_key=f"{date}|{region}",
            partition_key=dg.MultiPartitionKey({"date": date, "region": region}),
        )
        for region in ["us", "eu", "jp"]
    ]
```

## Best Practices

- Limit each asset to **100,000 partitions or fewer** for acceptable UI performance.
- Use `DynamicPartitionsDefinition` when partition keys are not known at definition time.
- Use `MultiPartitionsDefinition` for two-dimensional partitioning (e.g., date × region).
- Use `BackfillPolicy.single_run()` for assets that can process a date range in one query (e.g., SQL `WHERE date BETWEEN`).
- Use `TimeWindowPartitionMapping` with offsets for dependencies that cross partition boundaries.
