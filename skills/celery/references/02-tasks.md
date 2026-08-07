# Tasks

> Source: [Celery Tasks Guide](https://docs.celeryq.dev/en/stable/userguide/tasks.html)

## Table of Contents

- [Defining Tasks](#defining-tasks)
- [Task Decorators](#task-decorators)
- [Bound Tasks](#bound-tasks)
- [Task Naming](#task-naming)
- [Task Options Reference](#task-options-reference)
- [Task Request Context](#task-request-context)
- [Pydantic Validation](#pydantic-validation)
- [Custom Task Classes](#custom-task-classes)
- [Task Lifecycle Handlers](#task-lifecycle-handlers)
- [Logging](#logging)
- [Best Practices](#best-practices)

## Defining Tasks

Tasks are the building blocks of Celery. Decorate any callable with `@app.task`:

```python
from myapp.celery import app

@app.task
def add(x, y):
    return x + y
```

With options:

```python
@app.task(serializer="json", rate_limit="10/m")
def send_email(to, subject, body):
    mail.send(to=to, subject=subject, body=body)
```

## Task Decorators

### @app.task — Tied to a Specific App

```python
from proj.celery import app

@app.task
def process_upload(file_id):
    ...
```

### @shared_task — App-Independent

Preferred for reusable libraries and Django apps:

```python
from celery import shared_task

@shared_task
def add(x, y):
    return x + y
```

### Multiple Decorators

Place `@app.task` last (outermost):

```python
@app.task
@my_decorator
def my_task():
    ...
```

## Bound Tasks

Setting `bind=True` passes the task instance as the first argument:

```python
@app.task(bind=True)
def send_notification(self, user_id):
    try:
        notify(user_id)
    except ConnectionError as exc:
        raise self.retry(exc=exc, countdown=60)
```

Use bound tasks when you need:
- `self.retry()` for retrying
- `self.request` for task metadata
- `self.update_state()` for progress tracking
- `self.app` for app access

## Task Naming

Celery auto-generates names from module + function: `myapp.tasks.add`.

### Explicit Names

```python
@app.task(name="sum-of-two-numbers")
def add(x, y):
    return x + y
```

### Best Practice — Module Namespacing

```python
@app.task(name="myapp.tasks.add")
def add(x, y):
    return x + y
```

### Custom Auto-Naming

```python
class MyCelery(Celery):
    def gen_task_name(self, name, module):
        if module.endswith(".tasks"):
            module = module[:-6]
        return super().gen_task_name(name, module)
```

## Task Options Reference

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `name` | str | auto | Task registration name |
| `bind` | bool | `False` | Pass task instance as first arg |
| `max_retries` | int/None | `3` | Max retry attempts (`None` = unlimited) |
| `default_retry_delay` | float | `180` | Seconds between retries |
| `rate_limit` | str | `None` | Rate limit (e.g., `"100/m"`, `"10/s"`) |
| `time_limit` | int | `None` | Hard time limit (seconds, kills task) |
| `soft_time_limit` | int | `None` | Soft time limit (raises exception) |
| `ignore_result` | bool | `False` | Don't store result |
| `store_errors_even_if_ignored` | bool | `False` | Store errors even if result ignored |
| `serializer` | str | app default | Serialization format |
| `compression` | str | `None` | Compression (gzip, bzip2) |
| `acks_late` | bool | `False` | Acknowledge after execution |
| `track_started` | bool | `False` | Report STARTED state |
| `throws` | tuple | `()` | Expected exceptions (not treated as failures) |
| `typing` | bool | `True` | Enable argument type checking |
| `autoretry_for` | tuple | `()` | Exception classes triggering auto-retry |
| `retry_backoff` | bool/int | `False` | Exponential backoff on retry |
| `retry_backoff_max` | int | `600` | Max backoff delay (seconds) |
| `retry_jitter` | bool | `True` | Randomize backoff delays |
| `dont_autoretry_for` | tuple | `()` | Exceptions excluded from auto-retry |
| `pydantic` | bool | `False` | Use Pydantic for arg validation |

## Task Request Context

Access via `self.request` in bound tasks:

```python
@app.task(bind=True)
def my_task(self, data):
    print(f"Task ID: {self.request.id}")
    print(f"Retries: {self.request.retries}")
    print(f"Worker: {self.request.hostname}")
```

| Attribute | Description |
|-----------|-------------|
| `id` | Unique task ID |
| `group` | Group ID (if member of a group) |
| `chord` | Chord ID (if part of a chord) |
| `args` / `kwargs` | Task arguments |
| `retries` | Current retry count (starts at 0) |
| `eta` | Original ETA |
| `expires` | Original expiry time |
| `hostname` | Worker node name |
| `delivery_info` | Exchange and routing key |
| `root_id` | First task in workflow |
| `parent_id` | Task that called this one |
| `is_eager` | `True` if executed locally |
| `timelimit` | Tuple of (soft, hard) time limits |
| `callbacks` | List of success callbacks |
| `errbacks` | List of error callbacks |
| `origin` | Hostname that sent the task |
| `called_directly` | `True` if not executed by worker |

## Pydantic Validation

Celery 5.6+ supports Pydantic models for task arguments:

```python
from pydantic import BaseModel

class OrderRequest(BaseModel):
    product_id: int
    quantity: int
    price: float

class OrderResult(BaseModel):
    order_id: str
    total: float

@app.task(pydantic=True)
def create_order(request: OrderRequest) -> OrderResult:
    assert isinstance(request, OrderRequest)
    total = request.quantity * request.price
    return OrderResult(order_id="ORD-123", total=total)

# Call with dict — Pydantic validates and converts
result = create_order.delay({"product_id": 1, "quantity": 3, "price": 29.99})
result.get()  # {"order_id": "ORD-123", "total": 89.97}
```

Pydantic options: `pydantic_strict`, `pydantic_context`, `pydantic_dump_kwargs`.

Union types and generic type arguments are not supported.

## Custom Task Classes

Tasks are registered as global instances (not instantiated per request):

```python
from celery import Task

class DatabaseTask(Task):
    _db = None

    @property
    def db(self):
        if self._db is None:
            self._db = Database.connect()
        return self._db

@app.task(base=DatabaseTask, bind=True)
def process_rows(self):
    for row in self.db.table.all():
        process(row)
```

Set a default task class for the entire app:

```python
app = Celery("tasks", task_cls="myapp.tasks:DatabaseTask")
```

## Task Lifecycle Handlers

```python
class MyTask(Task):

    def before_start(self, task_id, args, kwargs):
        """Runs before task body. Blocks execution."""

    def on_success(self, retval, task_id, args, kwargs):
        """After successful execution (result already persisted)."""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """After failure (FAILURE state already persisted)."""

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """When task will retry (RETRY state set)."""

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """Runs last on terminal states (not RETRY/REJECTED)."""
```

Execution order: `before_start` → `run()` → result persisted → `on_success`/`on_failure`/`on_retry` → `after_return`.

## Logging

Use the Celery task logger for automatic task name/ID inclusion:

```python
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

@app.task
def add(x, y):
    logger.info("Adding %s + %s", x, y)
    return x + y
```

## Hiding Sensitive Arguments

```python
# Hide args in logs and monitoring
add.apply_async(
    (2, 3),
    argsrepr="(<secret-x>, <secret-y>)",
)

# Hide specific kwargs
charge.s(account, card="1234 5678 1234 5678").set(
    kwargsrepr=repr({"card": "**** **** **** 5678"})
).delay()
```

## Best Practices

**Pass IDs, not objects** — avoid stale data and serialization issues:

```python
# Bad — object may be stale by the time worker processes it
@app.task
def process(article):
    article.save()

# Good — fetch fresh data in the task
@app.task
def process(article_id):
    article = Article.objects.get(id=article_id)
    article.save()
```

**Design for idempotency** — tasks may be executed more than once due to retries, at-least-once delivery, or worker crashes with `acks_late=True`.

**Ignore results when not needed** — reduces backend load:

```python
@app.task(ignore_result=True)
def send_email(to, body):
    mail.send(to, body)
```

**Use `throws` for expected exceptions** — prevents them from being logged as errors:

```python
@app.task(throws=(NotFoundError,))
def get_resource(resource_id):
    raise NotFoundError(resource_id)
```
