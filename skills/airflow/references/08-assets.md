# Assets (Data-Aware Scheduling)

> Source: [airflow.apache.org/docs/…/assets](https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/assets.html) · v3.3.0

## Table of Contents

- [Overview](#overview)
- [Defining Assets](#defining-assets)
- [The @asset Decorator](#the-asset-decorator)
- [Producing Asset Events](#producing-asset-events)
- [Consuming Assets](#consuming-assets)
- [Conditional Scheduling](#conditional-scheduling)
- [Asset Metadata](#asset-metadata)
- [AssetAlias](#assetalias)
- [Partitioned Assets](#partitioned-assets)
- [Access Control](#access-control)

## Overview

Assets represent logical data groupings (tables, files, models) identified by a URI. When a producer task updates an asset, downstream consumer DAGs trigger automatically. This enables data-driven scheduling — workflows react to data availability rather than time.

```python
from airflow.sdk import Asset

raw_events = Asset("s3://data-lake/raw/events.parquet")
clean_users = Asset(name="clean_users", uri="s3://warehouse/users/")
```

## Defining Assets

### Basic Asset

```python
from airflow.sdk import Asset

# URI-based
events = Asset("s3://data-lake/events/daily.parquet")

# Named with URI
users = Asset(name="user_data", uri="s3://data-lake/users/")

# With metadata
orders = Asset(
    "s3://data-lake/orders/",
    extra={"team": "commerce", "format": "parquet"},
)
```

### URI Rules

- Must conform to RFC 3986 characters (alphanumeric, `%`, `-`, `_`, `.`, `~`)
- Case-sensitive (including host portion)
- `airflow://` scheme is reserved
- Custom schemes are allowed: `Asset("x-my-system://foobarbaz")`
- Scheme-less paths work: `Asset("my_table")`

### Security Note

Asset URIs and `extra` values are stored in cleartext in the metadata database. Never store credentials in asset definitions.

## The @asset Decorator

Shorthand for creating an Asset, DAG, and task in one:

```python
from airflow.sdk import asset

@asset(uri="s3://data-lake/events.parquet", schedule="@hourly")
def raw_events():
    """Write events to S3."""
    import boto3
    s3 = boto3.client("s3")
    s3.put_object(Bucket="data-lake", Key="events.parquet", Body=data)
```

This creates:
- An `Asset` named `raw_events`
- A DAG named `raw_events` running `@hourly`
- A single task that produces the asset

### Multi-Asset Output

```python
from airflow.sdk import asset, Asset

output_a = Asset("s3://bucket/a.parquet")
output_b = Asset("s3://bucket/b.parquet")

@asset.multi(schedule="@daily", outlets=[output_a, output_b])
def split_pipeline():
    """Produces both output_a and output_b."""
    process_and_write()
```

## Producing Asset Events

### With Operators (outlets)

```python
from airflow.sdk import DAG, Asset, task

raw_data = Asset("s3://data-lake/raw/events.parquet")

@dag(schedule="@hourly")
def ingest():
    @task(outlets=[raw_data])
    def write_events():
        # Write data to S3
        return "wrote 1000 events"

    write_events()

ingest()
```

When a task with `outlets` succeeds, Airflow emits an asset event for each outlet, potentially triggering consumer DAGs.

### Attaching Event Metadata

```python
from airflow.sdk import Metadata, asset

@asset(uri="s3://data-lake/events.parquet", schedule="@hourly")
def raw_events(self):
    row_count = write_data()
    yield Metadata(self, {"row_count": row_count, "format": "parquet"})
```

Or via `outlet_events`:

```python
@task(outlets=[raw_data])
def write_events(context):
    count = process_and_write()
    context["outlet_events"][raw_data].extra = {"row_count": count}
```

Event metadata must be JSON-serializable.

## Consuming Assets

### Schedule on Asset Updates

```python
from airflow.sdk import dag, task, Asset

raw_events = Asset("s3://data-lake/raw/events.parquet")

@dag(schedule=[raw_events])  # Triggers when raw_events updates
def transform_events():
    @task()
    def clean():
        return "cleaned"

    clean()

transform_events()
```

### Read Event Metadata

```python
@asset(schedule=None)
def downstream(context, raw_events):
    events = context["inlet_events"][raw_events]
    last_event = events[-1]
    row_count = last_event.extra.get("row_count", 0)
    timestamp = last_event.timestamp
    print(f"Upstream produced {row_count} rows at {timestamp}")
```

## Conditional Scheduling

### AND — All Assets Must Update

```python
asset_a = Asset("s3://bucket/a")
asset_b = Asset("s3://bucket/b")

@dag(schedule=(asset_a & asset_b))
def needs_both():
    ...
```

### OR — Any Asset Triggers

```python
@dag(schedule=(asset_a | asset_b))
def needs_either():
    ...
```

### Mixed Conditions

```python
@dag(schedule=((asset_a & asset_b) | asset_c))
def complex_schedule():
    ...
```

## Asset Metadata

### Extra Field

```python
events = Asset(
    "s3://data-lake/events/",
    extra={"team": "analytics", "sla": "4h", "schema_version": 2},
)
```

`extra` does not affect asset identity — two assets with the same URI but different `extra` are the same asset. Multiple definitions with different `extra` may result in unpredictable stored metadata.

## AssetAlias

For assets discovered or created at runtime:

```python
from airflow.sdk import AssetAlias, Asset, task

@task(outlets=[AssetAlias("dynamic-outputs")])
def dynamic_producer(outlet_events):
    for table in discover_tables():
        asset = Asset(f"s3://warehouse/{table}")
        outlet_events[AssetAlias("dynamic-outputs")].add(asset, extra={"table": table})
```

### Via Metadata

```python
from airflow.sdk import Metadata, AssetAlias, Asset

@task(outlets=[AssetAlias("my-alias")])
def producer():
    asset = Asset(uri="s3://bucket/output", name="dynamic_output")
    yield Metadata(asset, extra={"rows": 100}, alias=AssetAlias("my-alias"))
```

### Consuming Aliased Events

```python
@task(inlets=[AssetAlias("my-alias")])
def consumer(inlet_events):
    events = inlet_events[AssetAlias("my-alias")]
    for event in events:
        print(f"Event: {event.extra}")
```

## Partitioned Assets

Partition assets for granular scheduling based on data slices (dates, regions).

### Time-Based Partitions

```python
from airflow.sdk import CronPartitionTimetable, asset

@asset(
    uri="s3://data-lake/hourly_stats.parquet",
    schedule=CronPartitionTimetable("0 * * * *", timezone="UTC"),
)
def hourly_stats():
    pass
```

### Runtime Partitions

```python
from airflow.sdk import PartitionedAtRuntime, asset

@asset(
    uri="s3://data-lake/regional_data.csv",
    schedule=PartitionedAtRuntime(),
)
def regional_data(self, outlet_events):
    for region in ["us", "eu", "apac"]:
        outlet_events[self].add_partitions(region)
```

### Consuming Partitioned Assets

```python
from airflow.sdk import (
    DAG, Asset, PartitionedAssetTimetable, StartOfHourMapper
)

with DAG(
    dag_id="aggregate_hourly",
    schedule=PartitionedAssetTimetable(
        assets=hourly_stats_asset,
        default_partition_mapper=StartOfHourMapper(),
    ),
    catchup=False,
):
    @task()
    def aggregate(dag_run=None):
        partition_key = dag_run.partition_key
        print(f"Aggregating partition: {partition_key}")
```

### Partition Mappers

| Mapper | Behavior |
|--------|----------|
| `IdentityMapper` | Pass keys unchanged |
| `StartOfHourMapper` | Normalize to hour boundary |
| `StartOfDayMapper` | Normalize to day boundary |
| `StartOfWeekMapper` | Normalize to week boundary |
| `ProductMapper` | Map composite keys segment-by-segment |
| `AllowedKeyMapper` | Validate against fixed key list |
| `FixedKeyMapper` | Collapse all keys to a single downstream key |

### Rollup Mappers (3.3.0+)

Compose upstream events into coarser periods:

```python
from airflow.sdk import RollupMapper, StartOfHourMapper, DayWindow

@dag(
    schedule=PartitionedAssetTimetable(
        assets=hourly_data,
        default_partition_mapper=RollupMapper(
            upstream_mapper=StartOfHourMapper(),
            window=DayWindow(),  # Hold until 24 hourly partitions arrive
        ),
    ),
)
def daily_summary():
    ...
```

### Fan-Out Mappers (3.3.0+)

Expand single upstream events to multiple downstream runs:

```python
from airflow.sdk import FanOutMapper, StartOfWeekMapper, WeekWindow

@dag(
    schedule=PartitionedAssetTimetable(
        assets=weekly_model,
        default_partition_mapper=FanOutMapper(
            upstream_mapper=StartOfWeekMapper(),
            window=WeekWindow(),
            max_downstream_keys=7,
        ),
    ),
)
def daily_inference():
    ...
```

### Wait Policies

| Policy | Behavior |
|--------|----------|
| `WaitForAll` (default) | Hold until all expected keys arrive |
| `MinimumCount(n)` | Fire once n keys have arrived |

## Access Control

Cross-team asset access control (3.3.0+, requires Multi-Team mode):

```python
from airflow.sdk import Asset, AssetAccessControl

shared_data = Asset(
    name="shared_metrics",
    uri="s3://warehouse/metrics.parquet",
    access_control=AssetAccessControl(
        producer_teams=["analytics", "data_eng"],
        consumer_teams=["ml", "reporting"],
        allow_global=False,  # Block teamless DAGs
    ),
)
```

## Related Topics

- [Scheduling](06-scheduling.md) — Cron and timetable-based scheduling
- [XComs & Variables](04-xcoms-and-variables.md) — Task communication
- [DAGs](01-dags.md) — DAG declaration and parameters
