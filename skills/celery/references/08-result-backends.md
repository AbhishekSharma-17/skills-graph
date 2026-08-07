# Result Backends

> Source: [Celery Configuration — Result Backends](https://docs.celeryq.dev/en/stable/userguide/configuration.html#task-result-backend-settings)

## Table of Contents

- [Overview](#overview)
- [Backend Comparison](#backend-comparison)
- [Redis Backend](#redis-backend)
- [SQLAlchemy Backend](#sqlalchemy-backend)
- [Django ORM Backend](#django-orm-backend)
- [RPC Backend](#rpc-backend)
- [Task States](#task-states)
- [Custom States](#custom-states)
- [AsyncResult API](#asyncresult-api)
- [GroupResult API](#groupresult-api)
- [Result Expiration](#result-expiration)
- [Configuration Reference](#configuration-reference)
- [Common Pitfalls](#common-pitfalls)

## Overview

Result backends store task return values, exception info, and state metadata. Without a backend configured, you cannot retrieve task results or check status.

```python
app = Celery("myapp", backend="redis://localhost:6379/1")
```

## Backend Comparison

| Backend | Speed | Persistence | Multi-consumer | Best For |
|---------|-------|-------------|----------------|----------|
| Redis | Fast | Optional (AOF/RDB) | Yes | Most use cases |
| SQLAlchemy | Moderate | Yes | Yes | Existing DB infrastructure |
| Django ORM | Moderate | Yes | Yes | Django projects |
| Memcached | Fast | No | Yes | Ephemeral results |
| RPC (AMQP) | Fast | No | No | Direct reply pattern |
| DynamoDB | Moderate | Yes | Yes | AWS-native |
| Elasticsearch | Moderate | Yes | Yes | Result analytics |
| Cassandra | Fast | Yes | Yes | High write throughput |
| GCS | Slow | Yes | Yes | Long-term archival |

## Redis Backend

```python
app.conf.result_backend = "redis://localhost:6379/1"

# With password
app.conf.result_backend = "redis://:password@host:6379/1"

# Redis Sentinel
app.conf.result_backend = "sentinel://sentinel1:26379;sentinel2:26379"
app.conf.result_backend_transport_options = {
    "master_name": "mymaster",
}

# Redis Cluster
app.conf.result_backend = "redis+cluster://host1:6379,host2:6379"
```

Redis is the most common choice — fast, supports result expiration, and can double as the broker.

## SQLAlchemy Backend

```python
# SQLite
app.conf.result_backend = "db+sqlite:///results.sqlite3"

# PostgreSQL
app.conf.result_backend = "db+postgresql://user:pass@host/dbname"

# MySQL
app.conf.result_backend = "db+mysql://user:pass@host/dbname"
```

Requires `pip install celery[sqlalchemy]`.

### Engine Options

```python
app.conf.database_engine_options = {
    "pool_size": 10,
    "max_overflow": 20,
    "pool_pre_ping": True,
}
```

## Django ORM Backend

```bash
pip install django-celery-results
```

```python
# settings.py
INSTALLED_APPS = [..., "django_celery_results"]
CELERY_RESULT_BACKEND = "django-db"
```

```bash
python manage.py migrate
```

Results are stored in the `TaskResult` model, viewable in Django admin.

### Cache Backend (Django)

```python
CELERY_RESULT_BACKEND = "django-cache"
CELERY_CACHE_BACKEND = "default"  # Uses Django CACHES setting
```

## RPC Backend

Direct reply via AMQP — results are sent as messages back to the caller:

```python
app.conf.result_backend = "rpc://"
```

Results can only be consumed once and only by the process that initiated the task. Not suitable for inspecting results from multiple consumers.

## Task States

### Built-in States

| State | Description | Terminal |
|-------|-------------|----------|
| `PENDING` | Task unknown or waiting (default) | No |
| `STARTED` | Execution begun (requires `track_started=True`) | No |
| `SUCCESS` | Completed successfully | Yes |
| `FAILURE` | Raised an exception | Yes |
| `RETRY` | Being retried | No |
| `REVOKED` | Task was cancelled | Yes |

### State Transitions

```
PENDING → STARTED → SUCCESS
                  → FAILURE
                  → RETRY → STARTED → ...
       → REVOKED
```

### Checking State

```python
result = add.delay(4, 4)

result.state     # "PENDING", "STARTED", "SUCCESS", etc.
result.status    # Alias for state
result.ready()   # True if terminal state
result.successful()
result.failed()
```

## Custom States

Track task progress with custom states:

```python
@app.task(bind=True)
def upload_files(self, filenames):
    total = len(filenames)
    for i, filename in enumerate(filenames):
        upload(filename)
        self.update_state(
            state="PROGRESS",
            meta={"current": i + 1, "total": total},
        )
    return {"uploaded": total}
```

### Reading Custom State

```python
result = upload_files.delay(["a.jpg", "b.jpg", "c.jpg"])

# Poll for progress
while not result.ready():
    if result.state == "PROGRESS":
        info = result.info
        print(f"{info['current']}/{info['total']}")
    time.sleep(1)

print(result.result)  # {"uploaded": 3}
```

## AsyncResult API

```python
from celery.result import AsyncResult

# From task call
result = add.delay(4, 4)

# From task ID
result = AsyncResult("task-uuid-here")
result = app.AsyncResult("task-uuid-here")

# Properties
result.id            # Task UUID
result.state         # Current state
result.result        # Return value or exception
result.traceback     # Traceback string (if failed)
result.date_done     # Completion datetime
result.children      # List of child task results

# Methods
result.get(timeout=10)              # Block until result
result.get(propagate=False)          # Don't re-raise exceptions
result.get(disable_sync_subtasks=False)  # Allow sync in task (dangerous)
result.ready()                       # True if terminal state
result.successful()                  # True if SUCCESS
result.failed()                      # True if FAILURE
result.forget()                      # Delete stored result
result.revoke()                      # Cancel the task
result.revoke(terminate=True)        # Kill running task
```

## GroupResult API

```python
from celery import group

gresult = group(add.s(i, i) for i in range(10))()

gresult.ready()              # True when all complete
gresult.successful()         # True if none failed
gresult.failed()             # True if any failed
gresult.completed_count()    # Number finished
gresult.join(timeout=10)     # Gather all results
gresult.get(timeout=10)      # Alias for join
gresult.revoke()             # Revoke all subtasks

# Iterate results
for result in gresult:
    print(result.get())

# Save/restore group results
gresult.save()
restored = gresult.restore(gresult.id)
```

## Result Expiration

```python
# Default: 24 hours (86400 seconds)
app.conf.result_expires = 86400

# 1 hour
app.conf.result_expires = 3600

# Using timedelta
from datetime import timedelta
app.conf.result_expires = timedelta(hours=6)

# Never expire (not recommended)
app.conf.result_expires = None
```

## Configuration Reference

| Setting | Default | Description |
|---------|---------|-------------|
| `result_backend` | `None` | Backend URL |
| `result_expires` | `86400` | Seconds before results expire |
| `result_serializer` | `"json"` | Result serialization format |
| `result_compression` | `None` | Compression scheme |
| `result_persistent` | `False` | Persist AMQP result messages |
| `result_extended` | `False` | Store extra metadata (name, args, kwargs) |
| `result_accept_content` | `None` | Allowed deserialization formats |

### Extended Results

```python
app.conf.result_extended = True
# Stores: task name, args, kwargs, worker, date started
```

## Common Pitfalls

**No backend configured** — `.get()` blocks indefinitely or raises. Always set `result_backend` if you need results.

**Using RPC backend with multiple consumers** — results can only be consumed once. Use Redis or a database for multi-consumer patterns.

**Forgetting to set result_expires** — results accumulate indefinitely. Set an appropriate TTL to prevent storage growth.

**Ignoring results you don't need** — use `@app.task(ignore_result=True)` to reduce backend load for fire-and-forget tasks.

**PENDING vs unknown** — `PENDING` is the default state for tasks that haven't been seen. It doesn't mean the task was received — it could be a nonexistent ID.
