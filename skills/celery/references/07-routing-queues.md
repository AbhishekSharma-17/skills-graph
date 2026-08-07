# Routing & Queues

> Source: [Celery Routing Guide](https://docs.celeryq.dev/en/stable/userguide/routing.html)

## Table of Contents

- [Automatic Routing](#automatic-routing)
- [task_routes Configuration](#task_routes-configuration)
- [Manual Queue Definition](#manual-queue-definition)
- [AMQP Exchanges](#amqp-exchanges)
- [Priority Queues](#priority-queues)
- [Broadcast Routing](#broadcast-routing)
- [Custom Router Functions](#custom-router-functions)
- [Route Resolution Order](#route-resolution-order)
- [Common Patterns](#common-patterns)

## Automatic Routing

By default, `task_create_missing_queues=True` — queues are created on-demand when referenced. This is the simplest approach:

```python
# Route a task to a specific queue
app.conf.task_routes = {
    "feeds.tasks.import_feed": {"queue": "feeds"},
}
```

Start a worker consuming from that queue:

```bash
celery -A proj worker -Q feeds
celery -A proj worker -Q feeds,celery  # Also consume default queue
```

## task_routes Configuration

### Dict Mapping

```python
app.conf.task_routes = {
    "myapp.tasks.send_email": {"queue": "email"},
    "myapp.tasks.process_payment": {"queue": "payments"},
    "myapp.tasks.generate_report": {"queue": "reports"},
}
```

### Glob Patterns

```python
app.conf.task_routes = ([
    ("feed.tasks.*", {"queue": "feeds"}),
    ("web.tasks.*", {"queue": "web"}),
    ("report.tasks.*", {"queue": "reports"}),
],)
```

### Regex Patterns

```python
import re

app.conf.task_routes = ([
    (re.compile(r"(video|image)\.tasks\..*"), {"queue": "media"}),
    (re.compile(r"email\.tasks\..*"), {"queue": "email"}),
],)
```

### Routing with Exchange and Routing Key

```python
app.conf.task_routes = {
    "feeds.tasks.import_feed": {
        "queue": "feed_tasks",
        "exchange": "feeds",
        "routing_key": "feed.import",
    },
}
```

## Manual Queue Definition

Define queues explicitly using the Kombu library:

```python
from kombu import Queue, Exchange

app.conf.task_default_queue = "default"
app.conf.task_default_exchange = "tasks"
app.conf.task_default_exchange_type = "direct"
app.conf.task_default_routing_key = "task.default"

app.conf.task_queues = (
    Queue("default", routing_key="task.#"),
    Queue("feed_tasks", routing_key="feed.#"),
    Queue("media_tasks", routing_key="media.#"),
)
```

### With Explicit Exchanges

```python
from kombu import Queue, Exchange

default_exchange = Exchange("default", type="direct")
media_exchange = Exchange("media", type="direct")

app.conf.task_queues = (
    Queue("default", default_exchange, routing_key="default"),
    Queue("videos", media_exchange, routing_key="media.video"),
    Queue("images", media_exchange, routing_key="media.image"),
)
```

### Multiple Bindings

```python
from kombu import Queue, Exchange, binding

media_exchange = Exchange("media", type="direct")

app.conf.task_queues = (
    Queue("media", [
        binding(media_exchange, routing_key="media.video"),
        binding(media_exchange, routing_key="media.image"),
    ]),
)
```

## AMQP Exchanges

### Direct Exchange (Default)

Exact routing key matching:

```python
Exchange("tasks", type="direct")
# Queue with routing_key="video" only gets messages with that exact key
```

### Topic Exchange

Pattern-based matching with wildcards:

```python
Exchange("tasks", type="topic")
# * matches one word, # matches zero or more
# "usa.*" matches "usa.news" but not "usa.breaking.news"
# "usa.#" matches "usa.news" and "usa.breaking.news"
```

### Fanout Exchange

Delivers to ALL bound queues (ignores routing key):

```python
Exchange("broadcast", type="fanout")
```

## Priority Queues

### RabbitMQ Native Priorities

```python
from kombu import Queue

app.conf.task_queues = [
    Queue("tasks", queue_arguments={"x-max-priority": 10}),
]
app.conf.task_queue_max_priority = 10
app.conf.task_default_priority = 5
```

Send with priority:

```python
urgent_task.apply_async(args=(data,), priority=9)
```

### Redis Priorities (Approximate)

```python
app.conf.broker_transport_options = {
    "queue_order_strategy": "priority",
    "priority_steps": list(range(10)),
    "sep": ":",
}
# Creates queues: celery, celery:1, celery:2, ..., celery:9
```

For responsive priorities, reduce prefetch:

```python
app.conf.worker_prefetch_multiplier = 1
```

## Broadcast Routing

Send task copies to ALL workers:

```python
from kombu.common import Broadcast

app.conf.task_queues = (Broadcast("broadcast_tasks"),)
app.conf.task_routes = {
    "tasks.reload_cache": {
        "queue": "broadcast_tasks",
        "exchange": "broadcast_tasks",
    },
}
```

### With Beat

```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    "reload-cache": {
        "task": "tasks.reload_cache",
        "schedule": crontab(minute=0, hour="*/3"),
        "options": {"exchange": "broadcast_tasks"},
    },
}
```

Set `ignore_result=True` on broadcast tasks since results aren't reliably collected.

## Custom Router Functions

```python
def route_task(name, args, kwargs, options, task=None, **kw):
    if name.startswith("myapp.tasks.urgent_"):
        return {"queue": "priority", "priority": 9}
    if name.startswith("myapp.tasks.bulk_"):
        return {"queue": "bulk", "routing_key": "bulk.process"}
    return None  # Fall through to next router

app.conf.task_routes = (route_task,)
```

### Class-Based Router

```python
class MyRouter:
    def route_for_task(self, task, args=None, kwargs=None):
        if task.startswith("feed."):
            return {"queue": "feeds"}
        elif task.startswith("media."):
            return {"queue": "media"}

app.conf.task_routes = (MyRouter(),)
```

Routers are evaluated sequentially — the first to return a value wins.

## Route Resolution Order

1. `apply_async()` arguments (`queue=`, `exchange=`, `routing_key=`)
2. Task class attributes
3. `task_routes` setting
4. `task_default_queue` fallback

### Per-Call Override

```python
import_feed.apply_async(
    args=("http://example.com/rss",),
    queue="feed_tasks",
    routing_key="feed.import",
)
```

## Common Patterns

### Separate Queues by Task Duration

```python
app.conf.task_routes = {
    "myapp.tasks.quick_*": {"queue": "fast"},
    "myapp.tasks.slow_*": {"queue": "slow"},
}
```

```bash
# Fast workers: more concurrency, short time limit
celery -A proj worker -Q fast -c 16 --time-limit=60

# Slow workers: less concurrency, long time limit
celery -A proj worker -Q slow -c 2 --time-limit=3600
```

### Separate Queues by Priority

```python
app.conf.task_routes = {
    "billing.tasks.*": {"queue": "critical"},
    "analytics.tasks.*": {"queue": "background"},
    "email.tasks.*": {"queue": "email"},
}
```

### Dedicated Workers for Specific Tasks

```python
app.conf.task_routes = {
    "myapp.tasks.process_video": {"queue": "video"},
    "myapp.tasks.generate_pdf": {"queue": "pdf"},
}
```

```bash
celery -A proj worker -Q video -c 2 --max-memory-per-child=500000
celery -A proj worker -Q pdf -c 4
```
