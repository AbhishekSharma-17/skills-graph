# Signals & Hooks

> Source: [Celery Signals](https://docs.celeryq.dev/en/stable/userguide/signals.html)

## Table of Contents

- [Signal Basics](#signal-basics)
- [Task Signals](#task-signals)
- [Worker Signals](#worker-signals)
- [Beat Signals](#beat-signals)
- [App Signals](#app-signals)
- [Logging Signals](#logging-signals)
- [Practical Examples](#practical-examples)

## Signal Basics

Celery signals enable decoupled notifications when specific actions occur. Based on Django's dispatch implementation.

### Connecting to a Signal

```python
from celery.signals import task_success

@task_success.connect
def on_task_success(sender=None, result=None, **kwargs):
    print(f"Task {sender.name} succeeded with: {result}")
```

### Filtering by Sender

```python
from celery.signals import task_failure

@task_failure.connect(sender="myapp.tasks.send_email")
def on_email_failure(sender=None, task_id=None, exception=None, **kwargs):
    alert_ops(f"Email task {task_id} failed: {exception}")
```

### Best Practice

Always accept `**kwargs` for forward compatibility — future Celery versions may add new signal arguments.

## Task Signals

### before_task_publish

Fired in the sending process before the task message is published:

```python
from celery.signals import before_task_publish

@before_task_publish.connect
def before_publish(sender=None, headers=None, body=None, **kwargs):
    print(f"Sending task: {sender}")
    # Modify headers or body before sending
```

Arguments: `body`, `exchange`, `routing_key`, `headers`, `properties`, `declare`, `retry_policy`.

### after_task_publish

Fired after the broker receives the task message:

```python
from celery.signals import after_task_publish

@after_task_publish.connect
def after_publish(sender=None, headers=None, body=None, **kwargs):
    info = headers if "task" in headers else body
    print(f"Task sent: {info['id']}")
```

Arguments: `headers`, `body`, `exchange`, `routing_key`.

### task_prerun

Fired in the worker before task execution:

```python
from celery.signals import task_prerun

@task_prerun.connect
def on_task_prerun(sender=None, task_id=None, args=None, kwargs=None, **kw):
    print(f"Starting task {sender.name}[{task_id}]")
```

### task_postrun

Fired in the worker after task execution:

```python
from celery.signals import task_postrun

@task_postrun.connect
def on_task_postrun(sender=None, task_id=None, retval=None, state=None, **kw):
    print(f"Finished task {sender.name}[{task_id}] state={state}")
```

Arguments: `task_id`, `task`, `args`, `kwargs`, `retval`, `state`.

### task_success

```python
from celery.signals import task_success

@task_success.connect
def on_success(sender=None, result=None, **kwargs):
    print(f"Task {sender.name} returned: {result}")
```

### task_failure

```python
from celery.signals import task_failure

@task_failure.connect
def on_failure(sender=None, task_id=None, exception=None, traceback=None, **kw):
    print(f"Task {task_id} failed: {exception}")
    # Send to error tracking (Sentry, etc.)
```

Arguments: `task_id`, `exception`, `args`, `kwargs`, `traceback`, `einfo`.

### task_retry

```python
from celery.signals import task_retry

@task_retry.connect
def on_retry(sender=None, request=None, reason=None, **kwargs):
    print(f"Task {sender.name} retrying: {reason}")
```

### task_revoked

```python
from celery.signals import task_revoked

@task_revoked.connect
def on_revoked(sender=None, request=None, terminated=None, signum=None, **kw):
    print(f"Task {request.id} revoked (terminated={terminated})")
```

### task_received

Fired when the worker receives a task from the broker:

```python
from celery.signals import task_received

@task_received.connect
def on_received(sender=None, request=None, **kwargs):
    print(f"Received task: {request.name}[{request.id}]")
```

### task_unknown

Fired when a worker receives a task it hasn't registered:

```python
from celery.signals import task_unknown

@task_unknown.connect
def on_unknown(sender=None, name=None, id=None, message=None, **kwargs):
    print(f"Unknown task received: {name}[{id}]")
```

### task_rejected

Fired when a worker rejects an invalid message:

```python
from celery.signals import task_rejected

@task_rejected.connect
def on_rejected(sender=None, message=None, exc=None, **kwargs):
    print(f"Task rejected: {exc}")
```

## Worker Signals

### celeryd_init

First signal fired during worker startup. Good for worker-specific configuration:

```python
from celery.signals import celeryd_init

@celeryd_init.connect
def on_worker_init(sender=None, conf=None, **kwargs):
    print(f"Worker {sender} initializing")
```

### celeryd_after_setup

After worker initialization but before execution begins:

```python
from celery.signals import celeryd_after_setup

@celeryd_after_setup.connect
def after_setup(sender=None, instance=None, conf=None, **kwargs):
    # Register custom queues dynamically
    pass
```

### worker_init / worker_ready / worker_shutdown

```python
from celery.signals import worker_init, worker_ready, worker_shutdown

@worker_init.connect
def on_init(**kwargs):
    print("Worker process initializing")

@worker_ready.connect
def on_ready(**kwargs):
    print("Worker ready to accept tasks")

@worker_shutdown.connect
def on_shutdown(**kwargs):
    print("Worker shutting down")
```

### worker_process_init / worker_process_shutdown

Fired in prefork pool child processes:

```python
from celery.signals import worker_process_init, worker_process_shutdown

@worker_process_init.connect
def on_process_init(**kwargs):
    # Initialize per-process resources (DB connections, etc.)
    pass

@worker_process_shutdown.connect
def on_process_shutdown(**kwargs):
    # Clean up per-process resources
    pass
```

### heartbeat_sent

Fired when a heartbeat is dispatched:

```python
from celery.signals import heartbeat_sent

@heartbeat_sent.connect
def on_heartbeat(sender=None, **kwargs):
    pass  # Update health check
```

## Beat Signals

### beat_init

```python
from celery.signals import beat_init

@beat_init.connect
def on_beat_init(sender=None, **kwargs):
    print("Beat scheduler starting")
```

### beat_embedded_init

Fired when Beat starts embedded in a worker (`-B` flag):

```python
from celery.signals import beat_embedded_init

@beat_embedded_init.connect
def on_beat_embedded(sender=None, **kwargs):
    print("Embedded Beat scheduler starting")
```

## App Signals

### import_modules

Fired when configured modules need importing:

```python
from celery.signals import import_modules

@import_modules.connect
def on_import(**kwargs):
    pass
```

## Logging Signals

### setup_logging

Override Celery's default logging setup:

```python
from celery.signals import setup_logging

@setup_logging.connect
def on_setup_logging(**kwargs):
    import logging.config
    logging.config.dictConfig(MY_LOGGING_CONFIG)
```

Connecting to this signal disables Celery's default logging configuration.

### after_setup_logger / after_setup_task_logger

```python
from celery.signals import after_setup_logger

@after_setup_logger.connect
def on_after_logger_setup(logger=None, loglevel=None, **kwargs):
    # Add custom handlers
    handler = logging.handlers.SysLogHandler()
    logger.addHandler(handler)
```

## Practical Examples

### Sentry Error Tracking

```python
from celery.signals import task_failure
import sentry_sdk

@task_failure.connect
def on_task_failure(sender=None, task_id=None, exception=None,
                    traceback=None, args=None, kwargs=None, **kw):
    sentry_sdk.capture_exception(exception)
```

### Task Duration Logging

```python
import time
from celery.signals import task_prerun, task_postrun

_task_start_times = {}

@task_prerun.connect
def on_prerun(sender=None, task_id=None, **kwargs):
    _task_start_times[task_id] = time.time()

@task_postrun.connect
def on_postrun(sender=None, task_id=None, state=None, **kwargs):
    start = _task_start_times.pop(task_id, None)
    if start:
        duration = time.time() - start
        logger.info(f"Task {sender.name}[{task_id}] took {duration:.2f}s")
```

### Per-Process Database Connection

```python
from celery.signals import worker_process_init, worker_process_shutdown

@worker_process_init.connect
def init_db(**kwargs):
    from myapp.db import create_connection
    global db_conn
    db_conn = create_connection()

@worker_process_shutdown.connect
def close_db(**kwargs):
    global db_conn
    if db_conn:
        db_conn.close()
```

### Custom Logging Format

```python
from celery.signals import setup_logging
import logging

@setup_logging.connect
def configure_logging(**kwargs):
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        level=logging.INFO,
    )
```
