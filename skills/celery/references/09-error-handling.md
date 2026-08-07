# Error Handling & Retries

> Source: [Celery Tasks — Retrying](https://docs.celeryq.dev/en/stable/userguide/tasks.html#retrying)

## Table of Contents

- [Manual Retries](#manual-retries)
- [Automatic Retries](#automatic-retries)
- [Exponential Backoff](#exponential-backoff)
- [Custom Retry Delays](#custom-retry-delays)
- [Error Callbacks](#error-callbacks)
- [Semipredicates](#semipredicates)
- [Task Acknowledgment Modes](#task-acknowledgment-modes)
- [Idempotency Patterns](#idempotency-patterns)
- [Dead Letter Queues](#dead-letter-queues)
- [Common Patterns](#common-patterns)

## Manual Retries

Use `self.retry()` in bound tasks to re-execute on recoverable errors:

```python
@app.task(bind=True, max_retries=3)
def send_email(self, to, subject, body):
    try:
        smtp.send(to=to, subject=subject, body=body)
    except SMTPConnectionError as exc:
        raise self.retry(exc=exc, countdown=60)
```

`self.retry()` raises `celery.exceptions.Retry` — code after it won't execute. Always use `raise self.retry(...)`.

### Retry Parameters

```python
self.retry(
    exc=exc,                # Original exception
    countdown=60,           # Seconds before retry
    max_retries=5,          # Override task's max_retries
    throw=True,             # Raise Retry exception (default True)
    eta=datetime,           # Absolute retry time
    args=None,              # Override positional args
    kwargs=None,            # Override keyword args
)
```

## Automatic Retries

Use `autoretry_for` to retry on specific exceptions without try/except:

```python
from requests.exceptions import RequestException

@app.task(
    autoretry_for=(RequestException, ConnectionError),
    max_retries=5,
    retry_kwargs={"countdown": 30},
)
def fetch_data(url):
    response = requests.get(url)
    return response.json()
```

### Excluding Exceptions

```python
@app.task(
    autoretry_for=(Exception,),
    dont_autoretry_for=(ValueError, TypeError),
    max_retries=3,
)
def process(data):
    validate(data)   # ValueError won't retry
    fetch(data)      # Other exceptions will retry
```

## Exponential Backoff

```python
@app.task(
    autoretry_for=(RequestException,),
    retry_backoff=True,       # Enable exponential backoff
    retry_backoff_max=600,    # Max delay: 600 seconds (10 min)
    retry_jitter=True,        # Add randomness (default True)
    max_retries=10,
)
def call_api(endpoint):
    return requests.get(endpoint).json()
```

### Backoff Progression

With `retry_backoff=True` (base=1):
- Retry 1: ~1s
- Retry 2: ~2s
- Retry 3: ~4s
- Retry 4: ~8s
- Retry 5: ~16s
- (capped at `retry_backoff_max`)

With `retry_backoff=2` (base=2):
- Retry 1: ~2s
- Retry 2: ~4s
- Retry 3: ~8s

### Jitter

When `retry_jitter=True` (default), a random component is added to prevent thundering herd when many tasks retry simultaneously.

## Custom Retry Delays

### Fixed Delay

```python
@app.task(bind=True, default_retry_delay=300)  # 5 minutes
def my_task(self):
    try:
        do_work()
    except Exception as exc:
        raise self.retry(exc=exc)
```

### Per-Retry Override

```python
@app.task(bind=True, max_retries=3)
def my_task(self):
    try:
        do_work()
    except Exception as exc:
        delays = [60, 300, 900]  # 1min, 5min, 15min
        delay = delays[min(self.request.retries, len(delays) - 1)]
        raise self.retry(exc=exc, countdown=delay)
```

### Class-Based Retry Configuration

```python
from celery import Task

class RetryTask(Task):
    autoretry_for = (Exception,)
    max_retries = 5
    retry_backoff = True
    retry_backoff_max = 700
    retry_jitter = False

@app.task(base=RetryTask)
def api_call(url):
    return requests.get(url).json()
```

## Error Callbacks

### link_error

```python
@app.task
def error_handler(request, exc, traceback):
    print(f"Task {request.id} failed: {exc!r}")
    # Log to Sentry, send alert, etc.

add.apply_async((2, 2), link_error=error_handler.s())
```

### In Chains

```python
workflow = (add.s(2, 2) | mul.s(8))
workflow.on_error(error_handler.s()).delay()
```

### In Chords

```python
chord(
    [add.s(i, i) for i in range(10)],
    tsum.s().on_error(on_chord_error.s()),
).delay()
```

## Semipredicates

Special exceptions for controlling task behavior:

### Ignore — Skip State Recording

```python
from celery.exceptions import Ignore

@app.task(bind=True)
def my_task(self):
    if already_processed(self.request.id):
        raise Ignore()
    process()
```

### Reject — Return Message to Broker

Only effective with `acks_late=True`:

```python
from celery.exceptions import Reject

@app.task(bind=True, acks_late=True)
def process_file(self, path):
    try:
        process(path)
    except MemoryError as exc:
        raise Reject(exc, requeue=False)  # Don't requeue
    except IOError as exc:
        raise Reject(exc, requeue=True)   # Requeue for another worker
```

### SoftTimeLimitExceeded

```python
from celery.exceptions import SoftTimeLimitExceeded

@app.task(bind=True, soft_time_limit=60)
def long_task(self, data):
    try:
        process(data)
    except SoftTimeLimitExceeded:
        cleanup()
        save_progress()
```

## Task Acknowledgment Modes

### acks_early (Default)

Task is acknowledged immediately when received. If worker crashes, task is lost.

```python
@app.task  # acks_late=False (default)
def fire_and_forget(data):
    process(data)
```

### acks_late

Task acknowledged after execution. If worker crashes, broker redelivers the task.

```python
@app.task(acks_late=True, reject_on_worker_lost=True)
def reliable_task(data):
    process(data)
```

Set `reject_on_worker_lost=True` to automatically requeue if the worker process dies unexpectedly.

## Idempotency Patterns

Tasks with `acks_late=True` or autoretry may execute multiple times. Design for idempotency:

### Unique Constraint Guard

```python
@app.task(bind=True, autoretry_for=(Exception,), max_retries=3)
def create_user(self, email, name):
    try:
        User.objects.create(email=email, name=name)
    except IntegrityError:
        pass  # Already created — idempotent
```

### Idempotency Key

```python
import hashlib

@app.task(bind=True)
def process_payment(self, order_id, amount):
    idempotency_key = f"payment:{order_id}"
    if cache.get(idempotency_key):
        return "Already processed"
    
    result = payment_gateway.charge(order_id, amount)
    cache.set(idempotency_key, True, timeout=86400)
    return result
```

### Optimistic Locking

```python
@app.task(bind=True, autoretry_for=(StaleDataError,), max_retries=5)
def update_balance(self, account_id, amount):
    account = Account.objects.select_for_update().get(id=account_id)
    account.balance += amount
    account.save()
```

## Dead Letter Queues

### RabbitMQ DLX

```python
from kombu import Queue, Exchange

dead_letter_exchange = Exchange("dlx", type="direct")

app.conf.task_queues = [
    Queue("default", queue_arguments={
        "x-dead-letter-exchange": "dlx",
        "x-dead-letter-routing-key": "dead",
    }),
    Queue("dead", dead_letter_exchange, routing_key="dead"),
]
```

Failed/rejected tasks route to the dead letter queue for inspection.

## Common Patterns

### Retry with Different Args

```python
@app.task(bind=True, max_retries=3)
def fetch_with_fallback(self, url):
    try:
        return requests.get(url).json()
    except RequestException as exc:
        fallback = url.replace("api.primary.com", "api.secondary.com")
        raise self.retry(exc=exc, args=(fallback,))
```

### Circuit Breaker

```python
@app.task(bind=True, max_retries=0)
def call_service(self, data):
    if cache.get("circuit:service:open"):
        raise Ignore()  # Circuit is open, skip

    try:
        result = service.call(data)
        cache.delete("circuit:service:failures")
        return result
    except ServiceError:
        failures = cache.incr("circuit:service:failures")
        if failures >= 5:
            cache.set("circuit:service:open", True, timeout=60)
        raise
```

### Max Retries Exhausted

```python
@app.task(bind=True, max_retries=3)
def my_task(self, data):
    try:
        process(data)
    except Exception as exc:
        if self.request.retries >= self.max_retries:
            alert_ops(f"Task {self.request.id} exhausted retries: {exc}")
        raise self.retry(exc=exc)
```
