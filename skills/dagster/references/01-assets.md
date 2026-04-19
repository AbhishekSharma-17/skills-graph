# Dagster — Software-Defined Assets

> Source: [docs.dagster.io/concepts/assets](https://docs.dagster.io/concepts/assets/software-defined-assets)

## Table of Contents

- [The @asset Decorator](#the-asset-decorator)
- [Asset Dependencies](#asset-dependencies)
- [Asset Groups and Keys](#asset-groups-and-keys)
- [@multi_asset](#multi_asset)
- [AssetSpec](#assetspec)
- [MaterializeResult](#materializeresult)
- [@graph_asset](#graph_asset)
- [Asset Checks](#asset-checks)
- [AssetSelection](#assetselection)
- [define_asset_job](#define_asset_job)
- [The Definitions Object](#the-definitions-object)
- [Common Patterns](#common-patterns)

---

## The @asset Decorator

```python
import dagster as dg

@dg.asset(
    name="my_asset",                        # defaults to function name
    key_prefix=["warehouse", "analytics"],  # namespacing
    group_name="etl",                       # UI grouping
    owners=["team:data-eng"],               # ownership metadata
    kinds={"python", "pandas"},             # asset type tags
    io_manager_key="snowflake_io",          # which I/O manager stores this
    partitions_def=None,                    # partition definition
    code_version="v2",                      # track code changes
    retry_policy=None,                      # op retry strategy
    automation_condition=None,              # declarative automation trigger
    backfill_policy=None,                   # single-run vs multi-run backfills
    check_specs=None,                       # inline check specifications
    tags={"priority": "high"},              # filtering/organization tags
    metadata={"team": "analytics"},         # static metadata
    deps=None,                              # non-loading dependencies
    output_required=True,                   # whether asset always materializes
)
def my_asset(context: dg.AssetExecutionContext) -> None:
    context.log.info(f"Run ID: {context.run.run_id}")
```

## Asset Dependencies

### Via function parameters (loads upstream data)

```python
@dg.asset
def raw_data() -> pd.DataFrame:
    return pd.read_csv("data.csv")

@dg.asset
def cleaned_data(raw_data: pd.DataFrame) -> pd.DataFrame:
    return raw_data.dropna()
```

### Via deps= (ordering only, no data loading)

```python
@dg.asset(deps=[raw_data])
def summary(context: dg.AssetExecutionContext) -> None:
    context.log.info("Raw data is ready, computing summary independently")
```

### Via AssetIn (detailed input config)

```python
@dg.asset(
    ins={
        "monthly_report": dg.AssetIn(key_prefix=["warehouse", "analytics"]),
    }
)
def quarterly_summary(monthly_report: pd.DataFrame) -> pd.DataFrame:
    return monthly_report.groupby("quarter").sum()
```

## Asset Groups and Keys

```python
# Simple key (defaults to function name)
@dg.asset
def users(): ...  # key: AssetKey(["users"])

# Prefixed key
@dg.asset(key_prefix=["warehouse", "analytics"])
def monthly_report(): ...  # key: AssetKey(["warehouse", "analytics", "monthly_report"])

# Grouped for UI organization
@dg.asset(group_name="ingestion")
def raw_events(): ...

@dg.asset(group_name="transform")
def cleaned_events(raw_events): ...
```

## @multi_asset

Produces multiple assets from a single computation:

```python
@dg.multi_asset(
    specs=[
        dg.AssetSpec("orders_cleaned", group_name="etl"),
        dg.AssetSpec("orders_summary", group_name="etl", deps=["orders_cleaned"]),
    ]
)
def process_orders():
    yield dg.MaterializeResult(
        asset_key="orders_cleaned",
        metadata={"num_rows": 1000},
    )
    yield dg.MaterializeResult(
        asset_key="orders_summary",
        metadata={"num_rows": 50},
    )
```

With subsetting (partial materialization):

```python
@dg.multi_asset(
    specs=[
        dg.AssetSpec("asset_a"),
        dg.AssetSpec("asset_b"),
    ],
    can_subset=True,
)
def my_multi_asset(context: dg.AssetExecutionContext):
    if dg.AssetKey("asset_a") in context.selected_asset_keys:
        yield dg.MaterializeResult(asset_key="asset_a")
    if dg.AssetKey("asset_b") in context.selected_asset_keys:
        yield dg.MaterializeResult(asset_key="asset_b")
```

## AssetSpec

Declarative asset definition (used in @multi_asset specs):

```python
dg.AssetSpec(
    key="my_asset",
    deps={"upstream_a", "upstream_b"},
    description="A processed dataset",
    metadata={"schema": "public"},
    group_name="analytics",
    owners=["team:data"],
    automation_condition=dg.AutomationCondition.eager(),
    tags={"pii": "true"},
    kinds={"sql", "snowflake"},
    partitions_def=dg.DailyPartitionsDefinition("2024-01-01"),
)
```

## MaterializeResult

Returned from assets to report metadata and check results:

```python
@dg.asset
def my_asset() -> dg.MaterializeResult:
    row_count = process_data()
    return dg.MaterializeResult(
        metadata={
            "row_count": row_count,
            "schema": dg.MetadataValue.md("| col | type |\n|---|---|\n| id | int |"),
        },
        data_version=dg.DataVersion("v2.1"),
        check_results=[
            dg.AssetCheckResult(check_name="no_nulls", passed=True),
        ],
    )
```

## @graph_asset

Uses a multi-op graph to produce a single asset (retries per step):

```python
@dg.op(retry_policy=dg.RetryPolicy(max_retries=5, delay=0.2, backoff=dg.Backoff.EXPONENTIAL))
def fetch_data() -> int:
    return 42

@dg.op
def transform_data(num: int) -> int:
    return num ** 2

@dg.graph_asset
def processed_data():
    return transform_data(fetch_data())
```

## Asset Checks

### Standalone check

```python
@dg.asset_check(asset=cleaned_data, blocking=True)
def no_null_ids(cleaned_data: pd.DataFrame) -> dg.AssetCheckResult:
    num_nulls = cleaned_data["id"].isna().sum()
    return dg.AssetCheckResult(
        passed=bool(num_nulls == 0),
        metadata={"null_count": int(num_nulls)},
    )
```

### Inline check via check_specs

```python
@dg.asset(check_specs=[dg.AssetCheckSpec(name="positive_values", asset="metrics")])
def metrics(context: dg.AssetExecutionContext):
    df = compute_metrics()
    yield dg.Output(value=df)
    yield dg.AssetCheckResult(
        passed=bool((df["value"] > 0).all()),
        check_name="positive_values",
    )
```

### Multi-asset check

```python
@dg.multi_asset_check(
    specs=[
        dg.AssetCheckSpec(name="orders_valid", asset="orders"),
        dg.AssetCheckSpec(name="items_valid", asset="items"),
    ]
)
def validate_tables():
    yield dg.AssetCheckResult(check_name="orders_valid", passed=True, asset_key="orders")
    yield dg.AssetCheckResult(check_name="items_valid", passed=True, asset_key="items")
```

## AssetSelection

Query and filter assets programmatically:

```python
dg.AssetSelection.all()                     # all assets
dg.AssetSelection.groups("sales")           # by group
dg.AssetSelection.key_prefixes("warehouse") # by prefix
dg.AssetSelection.assets(my_asset)          # specific asset(s)
selection.upstream()                         # upstream dependencies
selection.downstream()                       # downstream dependents
selection.without_checks()                   # exclude checks
dg.AssetSelection.checks_for_assets(orders) # checks for an asset
```

## define_asset_job

```python
daily_pipeline = dg.define_asset_job(
    name="daily_pipeline",
    selection=[raw_data, cleaned_data, report],
    tags={"team": "data-eng"},
    description="Daily ETL pipeline",
)
```

## The Definitions Object

```python
@dg.definitions
def defs():
    return dg.Definitions(
        assets=[raw_data, cleaned_data, report],
        asset_checks=[no_null_ids],
        jobs=[daily_pipeline],
        schedules=[daily_schedule],
        sensors=[file_sensor],
        resources={
            "io_manager": dg.FilesystemIOManager(),
            "db": DatabaseResource(url=dg.EnvVar("DB_URL")),
        },
    )
```

Merge multiple definitions:

```python
merged = dg.Definitions.merge(team_a_defs, team_b_defs)
```

## Common Patterns

**DO:** Use `deps=` for assets that don't load upstream data into memory. Use function parameters for assets that need upstream data loaded by I/O managers.

**DO:** Group related assets with `group_name` for UI organization.

**DO:** Use `code_version` to prevent redundant materializations when code hasn't changed.

**DO:** Use `kinds` to tag asset types (e.g., `{"python", "snowflake"}`) for UI filtering.

**DON'T:** Create deeply nested asset key hierarchies — keep to 2-3 levels max.

**DON'T:** Put heavy I/O directly in asset functions — use resources and I/O managers.

**DON'T:** Use `@multi_asset` when a simple `@asset` with `deps=` suffices — keep it simple.
