# Dagster — Declarative Automation

> Source: [docs.dagster.io/guides/automate/declarative-automation](https://docs.dagster.io/guides/automate/declarative-automation)

## Table of Contents

- [Overview](#overview)
- [Built-in Conditions](#built-in-conditions)
- [Condition Operands](#condition-operands)
- [Operators](#operators)
- [Composite Conditions](#composite-conditions)
- [Custom Automation Conditions](#custom-automation-conditions)
- [Setup and Activation](#setup-and-activation)
- [Best Practices](#best-practices)

---

## Overview

Declarative Automation uses `AutomationCondition` objects to describe *when* assets should be materialized, replacing imperative schedule/sensor logic. You declare conditions on each asset, and Dagster's automation sensor evaluates them every ~30 seconds.

```python
import dagster as dg

@dg.asset(
    deps=["upstream"],
    automation_condition=dg.AutomationCondition.eager(),
)
def downstream_asset() -> None:
    ...
```

## Built-in Conditions

### AutomationCondition.on_cron(cron_schedule)

Materializes on a cron schedule after upstream dependencies have updated:

```python
@dg.asset(
    deps=["upstream"],
    automation_condition=dg.AutomationCondition.on_cron("@hourly"),
)
def hourly_asset() -> None: ...
```

Behavior:
- Triggers once per cron tick when all upstream assets updated since previous tick
- For time-partitioned assets, requests only the latest partition
- Will NOT fire if upstream does not update within the cron window

### AutomationCondition.eager()

Auto-updates whenever any upstream dependency changes:

```python
@dg.asset(
    deps=["upstream"],
    automation_condition=dg.AutomationCondition.eager(),
)
def eager_asset() -> None: ...
```

Behavior:
- Waits for all upstream partitions to be materialized
- Waits for in-progress upstream runs to complete before triggering
- For observed (external) assets, requires data version change
- For materialized assets, any new materialization counts

### AutomationCondition.on_missing()

Fills in missing asset partitions when upstream is available:

```python
@dg.asset(
    deps=[upstream],
    automation_condition=dg.AutomationCondition.on_missing(),
    partitions_def=dg.DailyPartitionsDefinition("2025-01-01"),
)
def backfill_asset() -> None: ...
```

Behavior:
- Requires all upstream partitions materialized before executing
- Only considers partitions added after condition was enabled
- For time-partitioned assets, requests only the latest partition

## Condition Operands

Primitive conditions that can be composed:

| Operand | Description |
|---------|-------------|
| `AutomationCondition.missing` | Asset has not been materialized |
| `AutomationCondition.in_progress` | Asset is part of an in-progress run |
| `AutomationCondition.execution_failed` | Asset failed in its latest run |
| `AutomationCondition.newly_updated` | Updated since previous evaluation |
| `AutomationCondition.newly_requested` | Requested on previous evaluation |
| `AutomationCondition.code_version_changed` | New code version detected |
| `AutomationCondition.cron_tick_passed` | New cron tick since previous evaluation |
| `AutomationCondition.in_latest_time_window` | Partition in latest time window |
| `AutomationCondition.will_be_requested` | Will be requested in this tick |
| `AutomationCondition.initial_evaluation` | First evaluation of this condition |

## Operators

Combine conditions using Python operators:

```python
# NOT
~dg.AutomationCondition.in_progress

# OR
dg.AutomationCondition.missing | dg.AutomationCondition.execution_failed

# AND
dg.AutomationCondition.missing & ~dg.AutomationCondition.in_progress

# Newly true (transition detection)
dg.AutomationCondition.missing.newly_true()

# Since (A occurred more recently than B)
dg.AutomationCondition.newly_updated.since(dg.AutomationCondition.newly_requested)

# Any deps match
dg.AutomationCondition.any_deps_match(dg.AutomationCondition.newly_updated)

# All deps match
dg.AutomationCondition.all_deps_match(dg.AutomationCondition.newly_updated)

# Any downstream conditions
dg.AutomationCondition.any_downstream_conditions()
```

## Composite Conditions

Pre-built combinations of primitives:

| Condition | Purpose |
|-----------|---------|
| `any_deps_updated` | Any dependency updated since last evaluation |
| `any_deps_missing` | Any dependency lacks materialization |
| `any_deps_in_progress` | Any dependency has in-progress runs |
| `all_deps_updated_since_cron` | All dependencies updated since cron tick |

## Custom Automation Conditions

For arbitrary Python logic, requires `use_user_code_server=True`:

```python
class IsCompanyHoliday(dg.AutomationCondition):
    def evaluate(self, context: dg.AutomationContext) -> dg.AutomationResult:
        if is_company_holiday(context.evaluation_time):
            true_subset = context.candidate_subset
        else:
            true_subset = context.get_empty_subset()
        return dg.AutomationResult(true_subset, context=context)

@dg.asset(
    automation_condition=dg.AutomationCondition.eager() & ~IsCompanyHoliday(),
)
def smart_asset() -> None: ...
```

Register the sensor with user code server:

```python
@dg.definitions
def defs():
    return dg.Definitions(
        sensors=[
            dg.AutomationConditionSensorDefinition(
                "automation_sensor",
                target=dg.AssetSelection.all(),
                use_user_code_server=True,
            )
        ],
        assets=[smart_asset],
    )
```

Limit: 500 assets/checks per sensor with custom conditions.

## Setup and Activation

1. Set `automation_condition` on assets
2. Enable the `default_automation_condition_sensor` in the Dagster UI (Automation tab → toggle on)
3. Or register a custom `AutomationConditionSensorDefinition` in Definitions

```python
# Using built-in sensor (no explicit registration needed)
@dg.asset(automation_condition=dg.AutomationCondition.eager())
def auto_asset(): ...

# Using custom sensor
sensor = dg.AutomationConditionSensorDefinition(
    "my_automation_sensor",
    target=dg.AssetSelection.all(),
    minimum_interval_seconds=30,
    use_user_code_server=False,  # True for custom conditions
)

defs = dg.Definitions(assets=[auto_asset], sensors=[sensor])
```

## Best Practices

- **Start with built-in conditions** (`on_cron`, `eager`, `on_missing`) before building custom ones.
- **`eager` on root assets** (no upstream) will never trigger — use `on_cron` or `on_missing` for root assets.
- **`on_cron` will not fire** if upstream assets didn't update in the cron window — this is intentional, not a bug.
- **Custom conditions require `use_user_code_server=True`** and are limited to 500 assets per sensor.
- **Prefer declarative automation over sensors** for new asset dependencies — it's more maintainable and composable.
- **`@multi_asset_sensor` is deprecated** — migrate to `AutomationCondition` for cross-asset triggers.
