# Workers

> Source: [Celery Workers Guide](https://docs.celeryq.dev/en/stable/userguide/workers.html)

## Table of Contents

- [Starting Workers](#starting-workers)
- [Concurrency Pools](#concurrency-pools)
- [Autoscaling](#autoscaling)
- [Time Limits](#time-limits)
- [Rate Limits](#rate-limits)
- [Resource Limits](#resource-limits)
- [Queue Management](#queue-management)
- [Shutdown Behavior](#shutdown-behavior)
- [Remote Control](#remote-control)
- [Inspecting Workers](#inspecting-workers)
- [Revoking Tasks](#revoking-tasks)
- [Process Signals](#process-signals)

## Starting Workers

```bash
# Basic start
celery -A proj worker --loglevel=INFO

# With concurrency
celery -A proj worker -c 4 --loglevel=INFO

# Named worker (required for multiple workers on one machine)
celery -A proj worker -n worker1@%h --loglevel=INFO

# With specific queues
celery -A proj worker -Q default,priority --loglevel=INFO

# With specific pool
celery -A proj worker --pool=gevent -c 100
```

### Hostname Variables

| Variable | Expands To |
|----------|-----------|
| `%h` | Full hostname (e.g., `worker1@myhost.local`) |
| `%n` | Hostname only (e.g., `myhost`) |
| `%d` | Domain only (e.g., `local`) |

### Multiple Workers

```bash
celery -A proj worker -n worker1@%h -Q default -c 4 &
celery -A proj worker -n worker2@%h -Q priority -c 2 &
celery -A proj worker -n worker3@%h -Q uploads -c 1 &
```

## Concurrency Pools

### Prefork (Default — Multiprocessing)

```bash
celery -A proj worker --pool=prefork -c 8
```

Best for CPU-bound tasks. Each task runs in a separate process. Defaults to CPU count.

### Eventlet (Green Threads)

```bash
pip install eventlet
celery -A proj worker --pool=eventlet -c 100
```

Best for I/O-bound tasks (HTTP calls, database queries). Supports hundreds of concurrent tasks with minimal overhead.

### Gevent (Coroutines)

```bash
pip install gevent
celery -A proj worker --pool=gevent -c 100
```

Similar to eventlet — high I/O concurrency. Some libraries have better gevent compatibility.

### Threads

```bash
celery -A proj worker --pool=threads -c 10
```

OS-level threads. Subject to the GIL — useful for I/O-bound tasks but not CPU-bound.

### Solo (Single Process)

```bash
celery -A proj worker --pool=solo
```

No concurrency — tasks execute sequentially. Useful for debugging.

## Autoscaling

Dynamically adjust the number of worker processes based on load:

```bash
# Min 3 processes, max 10
celery -A proj worker --autoscale=10,3
```

The autoscaler monitors task queue length and scales up when tasks queue, scales down when idle.

## Time Limits

### Hard Time Limit

Forcefully kills the task (SIGKILL to child process):

```bash
celery -A proj worker --time-limit=300
```

### Soft Time Limit

Raises `SoftTimeLimitExceeded` — allows cleanup:

```bash
celery -A proj worker --soft-time-limit=240 --time-limit=300
```

### Per-Task Time Limits

```python
@app.task(time_limit=120, soft_time_limit=100)
def long_task():
    pass
```

### Handling Soft Time Limits

```python
from celery.exceptions import SoftTimeLimitExceeded

@app.task(bind=True, soft_time_limit=60)
def process_file(self, file_id):
    try:
        do_processing(file_id)
    except SoftTimeLimitExceeded:
        save_partial_result(file_id)
        raise  # Let Celery mark it as failed
```

### Runtime Time Limit Changes

```python
app.control.time_limit(
    "tasks.crawl_the_web",
    soft=60,
    hard=120,
    reply=True,
)
```

## Rate Limits

```python
# On the task definition
@app.task(rate_limit="10/m")  # 10 per minute
def send_sms(phone, message):
    pass

# Formats: "100/s", "100/m", "100/h"
```

### Runtime Rate Limit Changes

```python
app.control.rate_limit("myapp.tasks.send_sms", "200/m")

# Target specific workers
app.control.rate_limit(
    "myapp.tasks.send_sms",
    "50/m",
    destination=["worker1@host"],
)
```

## Resource Limits

### Max Tasks Per Child

Recycle worker processes after N tasks (prevents memory leaks):

```bash
celery -A proj worker --max-tasks-per-child=1000
```

```python
app.conf.worker_max_tasks_per_child = 1000
```

### Max Memory Per Child

Recycle when a process exceeds memory threshold (in KB):

```bash
celery -A proj worker --max-memory-per-child=200000  # 200MB
```

```python
app.conf.worker_max_memory_per_child = 200_000  # KB
```

## Queue Management

### Start with Specific Queues

```bash
celery -A proj worker -Q feeds,priority
```

### Add Queues at Runtime

```python
app.control.add_consumer("new_queue", reply=True)

# Target specific workers
app.control.add_consumer(
    "new_queue",
    reply=True,
    destination=["worker1@host"],
)
```

### Remove Queues at Runtime

```python
app.control.cancel_consumer("old_queue", reply=True)
```

## Shutdown Behavior

### Warm Shutdown (SIGTERM)

Worker finishes currently executing tasks, then exits. Prefetched-but-unstarted tasks are requeued.

```bash
kill -TERM <worker_pid>
# or
celery -A proj control shutdown
```

### Cold Shutdown (SIGQUIT)

Immediately terminates — tasks in progress are lost:

```bash
kill -QUIT <worker_pid>
```

### Soft Shutdown (v5.5+)

Configurable grace period between warm and cold shutdown:

```python
app.conf.worker_soft_shutdown_timeout = 30  # seconds
```

### Keyboard Shortcuts

- First `Ctrl-C`: warm shutdown
- Second `Ctrl-C`: cold shutdown (immediate)

## Remote Control

### Ping Workers

```python
app.control.ping(timeout=0.5)
# [{'worker1@host': {'ok': 'pong'}}, ...]
```

### Broadcast Commands

```python
# Shutdown all workers
app.control.broadcast("shutdown")

# Shutdown specific workers
app.control.broadcast("shutdown", destination=["worker1@host"])
```

### Enable/Disable Events

```python
app.control.enable_events()
app.control.disable_events()
```

### Pool Management

```python
# Grow pool by 3 processes
app.control.pool_grow(3)

# Shrink pool by 2 processes
app.control.pool_shrink(2)
```

## Inspecting Workers

```python
i = app.control.inspect()

# Target specific workers
i = app.control.inspect(destination=["worker1@host"])

# Currently executing tasks
i.active()

# Registered task types
i.registered()

# Tasks with ETA/countdown waiting
i.scheduled()

# Received but not yet started
i.reserved()

# Worker statistics
i.stats()

# Revoked task IDs
i.revoked()

# Active queues
i.active_queues()

# Worker configuration
i.conf()
```

### CLI Equivalents

```bash
celery -A proj inspect active
celery -A proj inspect registered
celery -A proj inspect scheduled
celery -A proj inspect reserved
celery -A proj inspect stats
celery -A proj status  # List active workers
```

## Revoking Tasks

### By Task ID

```python
# Revoke (won't stop already-executing tasks)
app.control.revoke("task-id-here")

# Terminate running task
app.control.revoke("task-id-here", terminate=True)

# With specific signal
app.control.revoke("task-id-here", terminate=True, signal="SIGKILL")

# Bulk revoke
app.control.revoke(["id1", "id2", "id3"])
```

### Revoke by Stamped Headers (v5.3+)

```python
app.control.revoke_by_stamped_headers(
    {"stamp": "batch-2024-01"},
    terminate=True,
)
```

### Persistent Revokes

Revoke state is lost on worker restart. Use `--statedb` for persistence:

```bash
celery -A proj worker --statedb=/var/run/celery/worker.state
```

### Using AsyncResult

```python
result = add.delay(2, 2)
result.revoke()
result.revoke(terminate=True)
```

## Process Signals

| Signal | Action |
|--------|--------|
| `TERM` | Warm shutdown (finish current tasks) |
| `QUIT` | Cold shutdown (immediate) |
| `USR1` | Dump thread tracebacks to logs |
| `USR2` | Open remote debugger |
| `HUP` | Restart worker (daemon mode only) |

### File Path Variables

For log files, PID files, and state databases:

| Variable | Expands To |
|----------|-----------|
| `%p` | Full node name |
| `%h` | Hostname with domain |
| `%n` | Hostname only |
| `%d` | Domain only |
| `%i` | Pool process index (0 = main) |
| `%I` | Pool index with separator |
