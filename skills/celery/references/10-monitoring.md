# Monitoring

> Source: [Celery Monitoring Guide](https://docs.celeryq.dev/en/stable/userguide/monitoring.html)

## Table of Contents

- [CLI Commands](#cli-commands)
- [Flower Web Monitor](#flower-web-monitor)
- [Celery Events](#celery-events)
- [Programmatic Inspection](#programmatic-inspection)
- [Event Types](#event-types)
- [Custom Event Listeners](#custom-event-listeners)
- [Queue Inspection](#queue-inspection)
- [Prometheus Integration](#prometheus-integration)

## CLI Commands

### Worker Status

```bash
# List active workers
celery -A proj status

# Active tasks (currently executing)
celery -A proj inspect active

# Registered task types
celery -A proj inspect registered

# Tasks with ETA/countdown
celery -A proj inspect scheduled

# Received but not yet started
celery -A proj inspect reserved

# Worker statistics
celery -A proj inspect stats

# Active queues per worker
celery -A proj inspect active_queues

# Revoked task IDs
celery -A proj inspect revoked

# Worker configuration
celery -A proj inspect conf
```

### Targeting Specific Workers

```bash
celery -A proj inspect active --destination worker1@host,worker2@host
celery -A proj inspect stats --timeout 5.0
```

### Queue Management

```bash
# Purge all messages (DESTRUCTIVE)
celery -A proj purge

# Enable task events
celery -A proj control enable_events

# Disable task events
celery -A proj control disable_events
```

## Flower Web Monitor

Real-time web UI for Celery cluster monitoring and administration.

### Installation

```bash
pip install flower
```

### Starting Flower

```bash
# Default (uses app's broker)
celery -A proj flower

# Custom port
celery -A proj flower --port=5555

# With explicit broker
celery --broker=redis://localhost:6379/0 flower

# With basic auth
celery -A proj flower --basic-auth=user:password

# Persistent mode (saves state)
celery -A proj flower --persistent=True --db=flower.db
```

Access at `http://localhost:5555`.

### Flower Features

- Real-time task progress and history
- Task details: arguments, result, traceback, timestamps
- Worker status: active/idle, pool size, processed count
- Remote worker control: shutdown, pool grow/shrink
- Queue lengths and consumer count
- Rate limit management
- Task revocation
- HTTP API for programmatic access
- OpenID authentication support

### Flower HTTP API

```bash
# List workers
curl http://localhost:5555/api/workers

# List tasks
curl http://localhost:5555/api/tasks

# Execute a task
curl -X POST http://localhost:5555/api/task/async-apply/tasks.add \
  -d '{"args": [1, 2]}'

# Revoke a task
curl -X POST http://localhost:5555/api/task/revoke/task-id-here
```

## Celery Events

Curses-based terminal monitor:

```bash
# Start the event monitor
celery -A proj events

# With custom camera
celery -A proj events -c myapp.DumpCam --frequency=2.0
```

### Snapshot Cameras

Create custom camera classes for periodic state capture:

```python
from celery.events.snapshot import Polaroid

class DumpCam(Polaroid):
    clear_after = True

    def on_shutter(self, state):
        if not state.event_count:
            return
        print(f"Workers: {state.workers}")
        print(f"Tasks: {state.tasks}")
        print(f"Total events: {state.event_count}")
```

## Programmatic Inspection

### Inspect Interface

```python
i = app.control.inspect()

# Target specific workers
i = app.control.inspect(destination=["worker1@host"])

# Currently executing
active = i.active()
# {"worker1@host": [{"id": "...", "name": "tasks.add", ...}]}

# Registered tasks
registered = i.registered()
# {"worker1@host": ["tasks.add", "tasks.mul", ...]}

# Scheduled (ETA tasks)
scheduled = i.scheduled()

# Reserved (prefetched)
reserved = i.reserved()

# Statistics
stats = i.stats()
# {"worker1@host": {"total": {"tasks.add": 100}, "pool": {...}}}
```

### Control Interface

```python
# Ping workers
app.control.ping(timeout=0.5)

# Rate limit a task
app.control.rate_limit("tasks.send_email", "100/m")

# Time limit
app.control.time_limit("tasks.process", soft=60, hard=120)

# Pool size
app.control.pool_grow(3)
app.control.pool_shrink(2)

# Queue management
app.control.add_consumer("new_queue", reply=True)
app.control.cancel_consumer("old_queue", reply=True)

# Shutdown workers
app.control.broadcast("shutdown")
app.control.broadcast("shutdown", destination=["worker1@host"])
```

## Event Types

### Task Events

| Event | When | Key Fields |
|-------|------|-----------|
| `task-sent` | Task published to broker | uuid, name, args, kwargs |
| `task-received` | Worker receives task | uuid, name, hostname |
| `task-started` | Execution begins | uuid, hostname, pid |
| `task-succeeded` | Completed successfully | uuid, result, runtime |
| `task-failed` | Exception raised | uuid, exception, traceback |
| `task-retried` | Scheduled for retry | uuid, exception |
| `task-revoked` | Task cancelled | uuid, terminated, signum |
| `task-rejected` | Invalid message | uuid |

### Worker Events

| Event | When | Key Fields |
|-------|------|-----------|
| `worker-online` | Connected to broker | hostname |
| `worker-heartbeat` | Periodic status | hostname, active, processed |
| `worker-offline` | Disconnected | hostname |

## Custom Event Listeners

### Real-Time Event Processing

```python
from celery import Celery

app = Celery("monitor", broker="redis://localhost:6379/0")

def my_monitor():
    state = app.events.State()

    def on_task_failed(event):
        state.event(event)
        task = state.tasks.get(event["uuid"])
        print(f"FAILED: {task.name}[{task.uuid}] {task.exception}")

    def on_task_succeeded(event):
        state.event(event)
        task = state.tasks.get(event["uuid"])
        print(f"SUCCESS: {task.name}[{task.uuid}] runtime={task.runtime:.2f}s")

    with app.connection() as conn:
        recv = app.events.Receiver(conn, handlers={
            "task-failed": on_task_failed,
            "task-succeeded": on_task_succeeded,
            "*": state.event,  # Catch-all to maintain state
        })
        recv.capture(limit=None, timeout=None, wakeup=True)

if __name__ == "__main__":
    my_monitor()
```

### Task Duration Alert

```python
def on_task_succeeded(event):
    state.event(event)
    task = state.tasks.get(event["uuid"])
    if task.runtime and task.runtime > 60:
        alert(f"Slow task: {task.name} took {task.runtime:.1f}s")
```

## Queue Inspection

### RabbitMQ

```bash
rabbitmqctl list_queues name messages messages_ready messages_unacknowledged
```

### Redis

```bash
# Queue length
redis-cli llen celery

# All Celery queues
redis-cli keys "celery*"
```

### Programmatic

```python
with app.connection_or_acquire() as conn:
    queue = app.amqp.queues["celery"]
    _, message_count, _ = queue(conn).queue_declare(passive=True)
    print(f"Messages in queue: {message_count}")
```

## Prometheus Integration

### Using celery-exporter

```bash
pip install celery-exporter
celery-exporter --broker-url=redis://localhost:6379/0
```

### Custom Metrics

```python
from prometheus_client import Counter, Histogram, start_http_server

task_counter = Counter("celery_tasks_total", "Total tasks", ["name", "state"])
task_duration = Histogram("celery_task_duration_seconds", "Task duration", ["name"])

def on_task_succeeded(event):
    state.event(event)
    task = state.tasks.get(event["uuid"])
    task_counter.labels(name=task.name, state="success").inc()
    if task.runtime:
        task_duration.labels(name=task.name).observe(task.runtime)

def on_task_failed(event):
    state.event(event)
    task = state.tasks.get(event["uuid"])
    task_counter.labels(name=task.name, state="failure").inc()

start_http_server(9090)
```
