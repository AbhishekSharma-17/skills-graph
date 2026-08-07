# Periodic Tasks

> Source: [Celery Periodic Tasks](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html)

## Table of Contents

- [Celery Beat Overview](#celery-beat-overview)
- [Configuration via beat_schedule](#configuration-via-beat_schedule)
- [Configuration via Decorators](#configuration-via-decorators)
- [Crontab Schedules](#crontab-schedules)
- [Solar Schedules](#solar-schedules)
- [Schedule Entry Fields](#schedule-entry-fields)
- [Starting Beat](#starting-beat)
- [Django-Celery-Beat](#django-celery-beat)
- [Time Zones](#time-zones)
- [Preventing Overlaps](#preventing-overlaps)
- [Common Pitfalls](#common-pitfalls)

## Celery Beat Overview

Celery Beat is a scheduler that kicks off tasks at regular intervals. It runs as a separate process (or embedded in a worker) and sends task messages to the broker at configured times.

Only one Beat instance should run at a time to prevent duplicate task execution.

## Configuration via beat_schedule

```python
app.conf.beat_schedule = {
    "add-every-30-seconds": {
        "task": "tasks.add",
        "schedule": 30.0,  # Every 30 seconds
        "args": (16, 16),
    },
    "daily-cleanup": {
        "task": "tasks.cleanup",
        "schedule": timedelta(hours=24),
        "kwargs": {"keep_days": 30},
    },
}
app.conf.timezone = "UTC"
```

## Configuration via Decorators

```python
from celery import Celery
from celery.schedules import crontab

app = Celery()

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Every 10 seconds
    sender.add_periodic_task(10.0, test.s("hello"), name="add every 10")

    # Every Monday at 7:30 AM
    sender.add_periodic_task(
        crontab(hour=7, minute=30, day_of_week=1),
        test.s("Happy Monday!"),
    )

@app.task
def test(arg):
    print(arg)
```

## Crontab Schedules

```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    "every-monday-morning": {
        "task": "tasks.report",
        "schedule": crontab(hour=7, minute=30, day_of_week=1),
    },
}
```

### Crontab Parameters

```python
crontab(
    minute="*",          # 0-59, */N, or comma-separated
    hour="*",            # 0-23
    day_of_week="*",     # 0-6 (0=Monday) or mon,tue,wed,...
    day_of_month="*",    # 1-31
    month_of_year="*",   # 1-12 or jan,feb,mar,...
)
```

### Common Patterns

```python
# Every minute
crontab()

# Every 15 minutes
crontab(minute="*/15")

# Daily at midnight
crontab(minute=0, hour=0)

# Every 3 hours
crontab(minute=0, hour="*/3")

# Monday through Friday at 8 AM
crontab(minute=0, hour=8, day_of_week="1-5")

# First day of every month
crontab(minute=0, hour=0, day_of_month=1)

# Every quarter (Jan, Apr, Jul, Oct) on the 1st
crontab(minute=0, hour=0, day_of_month=1, month_of_year="1,4,7,10")

# Weekdays at 9:30 AM and 4:30 PM
crontab(minute=30, hour="9,16", day_of_week="1-5")
```

## Solar Schedules

Execute tasks based on sunrise, sunset, and other solar events:

```python
from celery.schedules import solar

app.conf.beat_schedule = {
    "sunset-task": {
        "task": "tasks.close_blinds",
        "schedule": solar("sunset", -37.8175, 144.9672),  # Melbourne
    },
    "dawn-task": {
        "task": "tasks.turn_off_lights",
        "schedule": solar("dawn_civil", 40.7128, -74.0060),  # New York
    },
}
```

### Solar Events

| Event | Description |
|-------|-------------|
| `dawn_astronomical` | Sun 18° below horizon |
| `dawn_nautical` | Sun 12° below horizon |
| `dawn_civil` | Sun 6° below horizon |
| `sunrise` | Upper edge of sun on horizon |
| `solar_noon` | Sun at highest point |
| `sunset` | Upper edge of sun on horizon |
| `dusk_civil` | Sun 6° below horizon |
| `dusk_nautical` | Sun 12° below horizon |
| `dusk_astronomical` | Sun 18° below horizon |

Latitude: positive = North, negative = South. Longitude: positive = East, negative = West.

## Schedule Entry Fields

| Field | Type | Description |
|-------|------|-------------|
| `task` | str | Task name to execute |
| `schedule` | float/timedelta/crontab/solar | Execution frequency |
| `args` | tuple/list | Positional arguments |
| `kwargs` | dict | Keyword arguments |
| `options` | dict | `apply_async` options (queue, exchange, expires) |
| `relative` | bool | Round timedelta to nearest interval |

### Example with Options

```python
app.conf.beat_schedule = {
    "priority-task": {
        "task": "tasks.critical_check",
        "schedule": crontab(minute="*/5"),
        "options": {
            "queue": "priority",
            "expires": 240,  # Expire if not consumed in 4 minutes
        },
    },
}
```

## Starting Beat

### Standalone Process (Recommended for Production)

```bash
celery -A proj beat --loglevel=INFO
```

### Embedded in Worker (Development)

```bash
celery -A proj worker -B --loglevel=INFO
```

### Custom Schedule File Location

```bash
celery -A proj beat -s /var/run/celery/celerybeat-schedule
```

The default scheduler uses Python's `shelve` module to persist last-run times.

## Django-Celery-Beat

Database-backed scheduler with Django admin interface:

### Setup

```bash
pip install django-celery-beat
```

```python
# settings.py
INSTALLED_APPS = [
    ...
    "django_celery_beat",
]
```

```bash
python manage.py migrate
```

### Start Beat with Database Scheduler

```bash
celery -A proj beat --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Django Admin Models

- **PeriodicTask** — task name, schedule, arguments, enabled/disabled
- **IntervalSchedule** — every N seconds/minutes/hours/days
- **CrontabSchedule** — cron expressions
- **SolarSchedule** — solar events with coordinates
- **ClockedSchedule** — one-time execution at a specific datetime

### Programmatic Creation

```python
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json

schedule, _ = IntervalSchedule.objects.get_or_create(
    every=10,
    period=IntervalSchedule.SECONDS,
)

PeriodicTask.objects.create(
    interval=schedule,
    name="Check for new uploads",
    task="myapp.tasks.check_uploads",
    args=json.dumps([]),
    kwargs=json.dumps({}),
)
```

## Time Zones

```python
# Set timezone
app.conf.timezone = "Europe/London"

# Use UTC (default)
app.conf.enable_utc = True
```

The file-based scheduler auto-detects timezone changes and resets. Database-backed schedulers may need manual reset after timezone changes.

For Django, Celery respects `USE_TZ` and `TIME_ZONE` settings.

## Preventing Overlaps

Tasks may overlap if execution time exceeds the schedule interval. Implement locking:

```python
from celery import shared_task
from django.core.cache import cache

@shared_task(bind=True)
def exclusive_task(self):
    lock_id = f"lock-{self.name}"
    acquired = cache.add(lock_id, "locked", timeout=60 * 5)
    if not acquired:
        return "Already running"
    try:
        do_work()
    finally:
        cache.delete(lock_id)
```

### Using Redis Lock

```python
import redis

@app.task(bind=True)
def exclusive_task(self):
    r = redis.Redis()
    lock = r.lock(f"celery-lock:{self.name}", timeout=300)
    if lock.acquire(blocking=False):
        try:
            do_work()
        finally:
            lock.release()
```

## Common Pitfalls

**Running multiple Beat instances** — causes duplicate task execution. Only run one Beat process per schedule.

**Long-running tasks with short intervals** — tasks overlap. Use locking or increase the interval.

**Using countdown/ETA for far-future scheduling** — tasks sit in worker memory. Use Beat or django-celery-beat for scheduled tasks.

**Timezone confusion** — always set `timezone` explicitly. Mixing UTC and local times causes scheduling errors.
