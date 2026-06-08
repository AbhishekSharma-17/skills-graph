# Temporal — Schedules

> Source: [docs.temporal.io/develop/python/schedules](https://docs.temporal.io/develop/python/schedules)

## What Are Schedules?

Schedules create workflow executions on a recurring basis — intervals, calendars, or cron expressions. They replace the deprecated `cron_schedule` parameter and offer superior functionality including updates, pausing, backfill, and overlap policies.

## Creating a Schedule

```python
from temporalio.client import (
    Client,
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleSpec,
    ScheduleIntervalSpec,
    ScheduleState,
)
from datetime import timedelta

client = await Client.connect("localhost:7233")

await client.create_schedule(
    "daily-report-schedule",
    Schedule(
        action=ScheduleActionStartWorkflow(
            DailyReportWorkflow.run,
            ReportInput(report_type="daily"),
            id="daily-report",
            task_queue="reports",
        ),
        spec=ScheduleSpec(
            intervals=[ScheduleIntervalSpec(every=timedelta(hours=24))]
        ),
        state=ScheduleState(note="Daily analytics report"),
    ),
)
```

## Schedule Spec Options

### Intervals

```python
# Every 2 hours
spec=ScheduleSpec(
    intervals=[ScheduleIntervalSpec(every=timedelta(hours=2))]
)

# Every 30 minutes with offset
spec=ScheduleSpec(
    intervals=[ScheduleIntervalSpec(
        every=timedelta(minutes=30),
        offset=timedelta(minutes=5),  # Start at :05, :35
    )]
)
```

### Calendar Specs

```python
from temporalio.client import ScheduleCalendarSpec, ScheduleRange

# Every weekday at 9:00 AM
spec=ScheduleSpec(
    calendars=[ScheduleCalendarSpec(
        hour=[ScheduleRange(9)],
        day_of_week=[ScheduleRange(1, 5)],  # Mon-Fri
    )]
)

# First day of every month at midnight
spec=ScheduleSpec(
    calendars=[ScheduleCalendarSpec(
        hour=[ScheduleRange(0)],
        day_of_month=[ScheduleRange(1)],
    )]
)
```

### Cron Expressions

```python
# Every day at 3:30 AM
spec=ScheduleSpec(cron_expressions=["30 3 * * *"])

# Every Monday and Friday at noon
spec=ScheduleSpec(cron_expressions=["0 12 * * 1,5"])
```

### Multiple Specs (OR logic)

```python
spec=ScheduleSpec(
    intervals=[
        ScheduleIntervalSpec(every=timedelta(hours=6)),
    ],
    calendars=[
        ScheduleCalendarSpec(hour=[ScheduleRange(9)]),  # Also at 9 AM
    ],
)
```

## Overlap Policies

Control what happens when a new execution triggers while the previous one is still running:

```python
from temporalio.client import ScheduleOverlapPolicy

Schedule(
    action=...,
    spec=...,
    policy=SchedulePolicy(
        overlap=ScheduleOverlapPolicy.SKIP,  # Default
    ),
)
```

| Policy | Behavior |
|--------|----------|
| `SKIP` | Don't start new if previous is running (default) |
| `BUFFER_ONE` | Buffer one execution, start when previous completes |
| `BUFFER_ALL` | Buffer all, run sequentially |
| `CANCEL_OTHER` | Cancel running execution, start new |
| `TERMINATE_OTHER` | Terminate running execution, start new |
| `ALLOW_ALL` | Start new regardless (parallel runs) |

## Managing Schedules

### Get Schedule Handle

```python
handle = client.get_schedule_handle("daily-report-schedule")
```

### Describe

```python
desc = await handle.describe()
print(f"Schedule: {desc.id}")
print(f"Spec: {desc.schedule.spec}")
print(f"Recent actions: {desc.info.recent_actions}")
print(f"Next action times: {desc.info.next_action_times}")
```

### Pause / Unpause

```python
await handle.pause(note="Paused for maintenance")
await handle.unpause(note="Maintenance complete")
```

### Trigger Immediately

```python
await handle.trigger()
```

Execute a scheduled workflow right now, outside its normal schedule. Subject to overlap policies.

### Delete

```python
await handle.delete()
```

Removes the schedule without affecting previously spawned workflows.

### Update

Modify an existing schedule using a callback:

```python
from temporalio.client import ScheduleUpdate, ScheduleUpdateInput

async def update_schedule(input: ScheduleUpdateInput) -> ScheduleUpdate:
    schedule = input.description.schedule

    # Change the interval
    schedule.spec = ScheduleSpec(
        intervals=[ScheduleIntervalSpec(every=timedelta(hours=12))]
    )

    # Change the workflow arguments
    action = schedule.action
    if isinstance(action, ScheduleActionStartWorkflow):
        action.args = [ReportInput(report_type="detailed")]

    return ScheduleUpdate(schedule=schedule)

await handle.update(update_schedule)
```

### List All Schedules

```python
async for schedule in await client.list_schedules():
    print(f"Schedule: {schedule.id}")
    print(f"  Spec: {schedule.spec}")
    print(f"  Recent actions: {schedule.info.recent_actions}")
```

## Backfill

Execute actions for past time periods (recovering missed runs):

```python
from temporalio.client import ScheduleBackfill
from datetime import datetime, timedelta

now = datetime.utcnow()

await handle.backfill(
    ScheduleBackfill(
        start_at=now - timedelta(hours=24),
        end_at=now - timedelta(hours=12),
        overlap=ScheduleOverlapPolicy.ALLOW_ALL,
    ),
)
```

Multiple backfill ranges in one call:

```python
await handle.backfill(
    ScheduleBackfill(
        start_at=now - timedelta(days=3),
        end_at=now - timedelta(days=2),
        overlap=ScheduleOverlapPolicy.ALLOW_ALL,
    ),
    ScheduleBackfill(
        start_at=now - timedelta(days=1),
        end_at=now,
        overlap=ScheduleOverlapPolicy.ALLOW_ALL,
    ),
)
```

## Start Delay (One-Time Delayed Start)

For a single delayed execution (not recurring):

```python
result = await client.execute_workflow(
    OneTimeWorkflow.run,
    input_data,
    id="delayed-task-1",
    task_queue="tasks",
    start_delay=timedelta(hours=2),
)
```

## Deprecated: Cron Workflows

The `cron_schedule` parameter on `start_workflow` is deprecated. Use Schedules instead:

```python
# Deprecated — don't use
result = await client.execute_workflow(
    CronWorkflow.run,
    id="cron-wf",
    task_queue="tasks",
    cron_schedule="0 * * * *",
)

# Use this instead
await client.create_schedule(
    "hourly-schedule",
    Schedule(
        action=ScheduleActionStartWorkflow(
            CronWorkflow.run,
            id="scheduled-wf",
            task_queue="tasks",
        ),
        spec=ScheduleSpec(cron_expressions=["0 * * * *"]),
    ),
)
```

## Common Patterns

### Idempotent Schedule Creation

```python
try:
    await client.create_schedule("my-schedule", schedule)
except Exception:
    # Schedule already exists — update it instead
    handle = client.get_schedule_handle("my-schedule")
    await handle.update(lambda input: ScheduleUpdate(schedule=schedule))
```

### Timezone-Aware Schedules

```python
spec=ScheduleSpec(
    cron_expressions=["0 9 * * *"],
    jitter=timedelta(minutes=5),  # Random offset to prevent thundering herd
)
```
