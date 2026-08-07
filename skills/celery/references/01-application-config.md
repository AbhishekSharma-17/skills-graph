# Application & Configuration

> Source: [Celery Application](https://docs.celeryq.dev/en/stable/userguide/application.html) · [Configuration](https://docs.celeryq.dev/en/stable/userguide/configuration.html)

## Table of Contents

- [Creating the Celery App](#creating-the-celery-app)
- [Configuration Methods](#configuration-methods)
- [Django Integration](#django-integration)
- [FastAPI Integration](#fastapi-integration)
- [Broker Settings](#broker-settings)
- [Result Backend Settings](#result-backend-settings)
- [Task Settings](#task-settings)
- [Worker Settings](#worker-settings)
- [Serialization Settings](#serialization-settings)
- [Security Settings](#security-settings)
- [Common Pitfalls](#common-pitfalls)

## Creating the Celery App

```python
from celery import Celery

# Minimal
app = Celery("myapp")

# With broker and backend
app = Celery(
    "myapp",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)

# With task module discovery
app = Celery("myapp", include=["myapp.tasks", "myapp.reports"])
```

The first argument is the app name — used for auto-generating task names and as a namespace prefix.

## Configuration Methods

### Direct Attribute Assignment

```python
app.conf.broker_url = "redis://localhost:6379/0"
app.conf.result_backend = "redis://localhost:6379/1"
app.conf.task_serializer = "json"
```

### Using update()

```python
app.conf.update(
    broker_url="redis://localhost:6379/0",
    result_backend="redis://localhost:6379/1",
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)
```

### From a Config Module

```python
# celeryconfig.py
broker_url = "redis://localhost:6379/0"
result_backend = "redis://localhost:6379/1"
task_serializer = "json"
timezone = "UTC"

# In your app
app.config_from_object("celeryconfig")
```

### From Environment Variables

```python
import os
app.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
```

## Django Integration

### Project Structure

```
myproject/
├── manage.py
├── myproject/
│   ├── __init__.py
│   ├── celery.py      # Celery app definition
│   ├── settings.py
│   └── urls.py
└── myapp/
    ├── __init__.py
    └── tasks.py        # Auto-discovered
```

### celery.py

```python
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")

app = Celery("myproject")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
```

### __init__.py

```python
from .celery import app as celery_app

__all__ = ("celery_app",)
```

### Django Settings (settings.py)

```python
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/1"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
```

The `namespace="CELERY"` means all settings must have a `CELERY_` prefix in Django settings.

### Django Task with shared_task

```python
# myapp/tasks.py
from celery import shared_task

@shared_task
def add(x, y):
    return x + y

@shared_task
def send_notification(user_id):
    from myapp.models import User
    user = User.objects.get(pk=user_id)
    user.send_notification()
```

Use `@shared_task` instead of `@app.task` for reusable Django apps — it works without a concrete app instance.

### Transaction Safety

```python
from django.db import transaction

@transaction.atomic
def create_order(request):
    order = Order.objects.create(...)
    # Task fires AFTER the transaction commits
    process_order.delay_on_commit(order.pk)
    return redirect("/orders/")
```

`delay_on_commit()` (Celery 5.4+) wraps the call in Django's `on_commit` hook, preventing race conditions where a task runs before the transaction is committed.

## FastAPI Integration

```python
# celery_app.py
from celery import Celery

celery = Celery(
    "worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)
celery.conf.update(task_track_started=True)

# tasks.py
from celery_app import celery

@celery.task
def process_data(data_id: int):
    # heavy processing
    return {"status": "done", "id": data_id}

# main.py
from fastapi import FastAPI, BackgroundTasks
from celery.result import AsyncResult
from tasks import process_data

app = FastAPI()

@app.post("/process/{data_id}")
async def start_processing(data_id: int):
    task = process_data.delay(data_id)
    return {"task_id": task.id}

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    result = AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None,
    }
```

## Broker Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `broker_url` | `"amqp://"` | Broker connection URL |
| `broker_connection_retry_on_startup` | `True` | Retry connection on startup |
| `broker_connection_max_retries` | `100` | Max reconnection attempts |
| `broker_pool_limit` | `10` | Max concurrent broker connections |
| `broker_heartbeat` | `120.0` | Heartbeat interval (AMQP only) |
| `broker_use_ssl` | `False` | Enable SSL/TLS |
| `broker_transport_options` | `{}` | Transport-specific options |

### Broker URL Formats

```python
# Redis
broker_url = "redis://localhost:6379/0"
broker_url = "redis://:password@hostname:6379/0"
broker_url = "redis+socket:///var/run/redis/redis.sock"

# RabbitMQ
broker_url = "amqp://guest:guest@localhost:5672//"
broker_url = "amqp://user:pass@host:5672/myvhost"

# Amazon SQS
broker_url = "sqs://ACCESS_KEY:SECRET_KEY@"
```

## Result Backend Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `result_backend` | `None` | Result storage backend |
| `result_expires` | `86400` (1 day) | Seconds before results are deleted |
| `result_serializer` | `"json"` | Serialization format for results |
| `result_compression` | `None` | Compression scheme |
| `result_persistent` | `False` | Persist RPC backend messages |

### Backend URL Formats

```python
# Redis
result_backend = "redis://localhost:6379/1"

# SQLAlchemy
result_backend = "db+sqlite:///results.sqlite3"
result_backend = "db+postgresql://user:pass@host/dbname"

# Django ORM (requires django-celery-results)
result_backend = "django-db"

# RPC (direct reply, no persistence)
result_backend = "rpc://"
```

## Task Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `task_serializer` | `"json"` | Default task serialization |
| `task_track_started` | `False` | Report STARTED state |
| `task_time_limit` | `None` | Hard time limit (seconds) |
| `task_soft_time_limit` | `None` | Soft time limit (seconds) |
| `task_acks_late` | `False` | Acknowledge after execution |
| `task_reject_on_worker_lost` | `False` | Requeue if worker crashes |
| `task_ignore_result` | `False` | Don't store results globally |
| `task_default_queue` | `"celery"` | Default queue name |
| `task_create_missing_queues` | `True` | Auto-create undefined queues |
| `task_routes` | `None` | Task-to-queue routing rules |
| `task_always_eager` | `False` | Execute tasks locally (testing) |
| `task_store_eager_result` | `False` | Store results in eager mode |
| `task_annotations` | `None` | Override task attributes via config |

## Worker Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `worker_concurrency` | CPU count | Concurrent worker processes |
| `worker_prefetch_multiplier` | `4` | Messages prefetched per process |
| `worker_max_tasks_per_child` | `None` | Tasks before process recycled |
| `worker_max_memory_per_child` | `None` | Memory limit (KB) before recycle |
| `worker_disable_rate_limits` | `False` | Ignore rate limits |
| `worker_send_task_events` | `False` | Enable monitoring events |
| `worker_state_db` | `None` | Persistent state file |

## Serialization Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `accept_content` | `["json"]` | Allowed deserialization formats |
| `task_serializer` | `"json"` | Task message serialization |
| `result_serializer` | `"json"` | Result serialization |
| `event_serializer` | `"json"` | Event serialization |

## Security Settings

To restrict deserialization to safe formats:

```python
app.conf.update(
    accept_content=["json"],
    task_serializer="json",
    result_serializer="json",
)
```

Pickle is powerful but allows arbitrary code execution — only enable it in trusted environments.

## Common Pitfalls

**Forgetting the backend** — without `result_backend`, calling `.get()` on results blocks forever or raises an error.

**Using pickle in untrusted environments** — pickle can execute arbitrary code. Use JSON unless you need to serialize complex Python objects.

**Setting task_always_eager=True in production** — this executes tasks synchronously and bypasses the entire distributed system. Only use for testing.

**Not setting timezone** — default is UTC. If your app uses a different timezone, set `timezone` explicitly or expect scheduling confusion.

**High prefetch multiplier with long tasks** — `worker_prefetch_multiplier=4` (default) means each worker process reserves 4 tasks. For long-running tasks, set this to `1` to avoid one worker hoarding tasks.
