# Calling Tasks

> Source: [Celery Calling Guide](https://docs.celeryq.dev/en/stable/userguide/calling.html)

## Table of Contents

- [Three Ways to Call](#three-ways-to-call)
- [delay() — Quick Shortcut](#delay--quick-shortcut)
- [apply_async() — Full Control](#apply_async--full-control)
- [Signatures](#signatures)
- [Partials](#partials)
- [Immutable Signatures](#immutable-signatures)
- [Callbacks and Error Callbacks](#callbacks-and-error-callbacks)
- [Timing: ETA and Countdown](#timing-eta-and-countdown)
- [Expiration](#expiration)
- [Retry Policy](#retry-policy)
- [Serialization and Compression](#serialization-and-compression)
- [Result Objects](#result-objects)
- [Common Pitfalls](#common-pitfalls)

## Three Ways to Call

```python
# 1. delay() — convenience shortcut
add.delay(2, 2)

# 2. apply_async() — full execution options
add.apply_async(args=(2, 2), countdown=10)

# 3. Direct call — runs in current process (no worker)
add(2, 2)  # returns 4 immediately
```

## delay() — Quick Shortcut

```python
task.delay(*args, **kwargs)

# Examples
add.delay(2, 2)
send_email.delay("user@example.com", subject="Hello", body="World")
```

`delay()` is a shorthand for `apply_async()` with no execution options. If you need to set queue, countdown, ETA, etc., use `apply_async()`.

## apply_async() — Full Control

```python
task.apply_async(
    args=None,          # Positional arguments (tuple/list)
    kwargs=None,        # Keyword arguments (dict)
    countdown=None,     # Seconds to wait before execution
    eta=None,           # Datetime for execution
    expires=None,       # Seconds or datetime until task expires
    retry=True,         # Retry on connection failure
    retry_policy=None,  # Dict of retry options
    queue=None,         # Target queue name
    exchange=None,      # Target exchange
    routing_key=None,   # Routing key
    priority=None,      # Priority (0–255, broker-dependent)
    serializer=None,    # Override serialization format
    compression=None,   # Override compression
    link=None,          # Success callback signature(s)
    link_error=None,    # Error callback signature(s)
    task_id=None,       # Custom task ID
    ignore_result=None, # Override ignore_result setting
)
```

### Examples

```python
# Delay execution by 60 seconds
add.apply_async((2, 2), countdown=60)

# Route to a specific queue
process_upload.apply_async((file_id,), queue="uploads")

# Set priority
urgent_task.apply_async(args=(data,), priority=9)

# Custom task ID
add.apply_async((2, 2), task_id="my-unique-id")
```

## Signatures

Signatures wrap a task call with its arguments into a serializable object:

```python
from celery import signature

# Three equivalent ways to create
sig = signature("tasks.add", args=(2, 2), countdown=10)
sig = add.signature((2, 2), countdown=10)
sig = add.s(2, 2)  # shortcut (no execution options)
```

### Inspecting Signatures

```python
sig = add.s(2, 2)
sig.args      # (2, 2)
sig.kwargs    # {}
sig.options   # {}
```

### Executing Signatures

```python
sig = add.s(2, 2)

sig.delay()                    # Send to worker
sig.apply_async(countdown=10)  # With options
sig()                          # Execute locally
```

### Setting Options on Signatures

```python
add.s(2, 2).set(countdown=1)
add.s(2, 2).set(queue="priority")
```

## Partials

Partial signatures have incomplete arguments — remaining args are supplied later:

```python
partial = add.s(2)       # Only first argument
partial.delay(8)         # Becomes add(8, 2) — args are PREPENDED
```

Kwargs merge with new values taking precedence:

```python
sig = add.s(2, 2)
sig.delay(debug=True)    # add(2, 2, debug=True)
```

### Cloning

```python
sig = add.s(2)
new_sig = sig.clone(args=(4,), kwargs={"debug": True})
```

## Immutable Signatures

Immutable signatures ignore any arguments passed from upstream tasks:

```python
# Full form
reset_buffers.signature(immutable=True)

# Shortcut
reset_buffers.si()
```

Use in workflows where a callback should NOT receive the parent's return value:

```python
# reset_buffers runs after add completes, but doesn't get add's result
add.apply_async((2, 2), link=reset_buffers.si())
```

## Callbacks and Error Callbacks

### Success Callbacks (link)

The parent's return value becomes the first argument of the callback:

```python
add.apply_async((2, 2), link=mul.s(16))
# add(2,2) → 4, then mul(4, 16) → 64
```

Multiple callbacks:

```python
add.apply_async((2, 2), link=[log_result.s(), notify.si()])
```

### Error Callbacks (link_error)

```python
@app.task
def error_handler(request, exc, traceback):
    print(f"Task {request.id} raised: {exc!r}")

add.apply_async((2, 2), link_error=error_handler.s())
```

### Fluent API

```python
add.s(2, 2).on_error(error_handler.s()).delay()
```

## Timing: ETA and Countdown

### Countdown — Relative Delay

```python
# Execute in 60 seconds
result = add.apply_async((2, 2), countdown=60)
```

### ETA — Absolute Time

```python
from datetime import datetime, timedelta

tomorrow = datetime.utcnow() + timedelta(days=1)
add.apply_async((2, 2), eta=tomorrow)
```

Tasks with ETA/countdown reside in worker memory until execution time. For distant future scheduling, use Celery Beat or a database-backed scheduler instead.

## Expiration

```python
# Expires in 60 seconds
add.apply_async((10, 10), expires=60)

# Expires at a specific time
from datetime import datetime, timedelta
add.apply_async((10, 10), expires=datetime.utcnow() + timedelta(hours=1))
```

Expired tasks receive REVOKED status.

## Retry Policy

Control connection retry behavior when sending tasks:

```python
add.apply_async((2, 2), retry=True, retry_policy={
    "max_retries": 3,
    "interval_start": 0,        # First retry immediately
    "interval_step": 0.2,       # Add 0.2s each retry
    "interval_max": 0.2,        # Max delay between retries
    "retry_errors": None,       # Tuple of exception classes
})
```

Disable retries entirely:

```python
add.apply_async((2, 2), retry=False)
```

## Serialization and Compression

```python
# Override serializer per call
add.apply_async((10, 10), serializer="json")
add.apply_async((10, 10), serializer="pickle")
add.apply_async((10, 10), serializer="msgpack")

# Override compression
add.apply_async((2, 2), compression="zlib")
add.apply_async((2, 2), compression="bzip2")
```

Priority: per-call > task attribute > global setting.

## Result Objects

`delay()` and `apply_async()` return an `AsyncResult`:

```python
result = add.delay(4, 4)

result.id            # Task UUID
result.status        # PENDING, STARTED, SUCCESS, FAILURE, RETRY, REVOKED
result.ready()       # True if task finished
result.successful()  # True if completed without error
result.failed()      # True if task raised an exception
result.result        # Return value (or exception if failed)
result.traceback     # Traceback string (if failed)

# Block until result is ready
value = result.get(timeout=10)

# Get without propagating exceptions
value = result.get(propagate=False)

# Forget stored result
result.forget()
```

### Checking State Without Blocking

```python
result = add.delay(4, 4)

if result.ready():
    print(result.result)
elif result.status == "STARTED":
    print("Still running...")
elif result.status == "RETRY":
    print("Retrying...")
```

## Common Pitfalls

**Never call .get() inside a task** — this causes deadlocks. Use chains instead:

```python
# Bad — can deadlock
@app.task
def bad_task():
    result = other_task.delay().get()

# Good — use a chain
from celery import chain
chain(other_task.s(), process_result.s())()
```

**Countdown is not a guarantee** — tasks with `countdown` sit in worker memory. If the worker restarts, they are lost (unless using `acks_late=True` with a persistent broker).

**Large arguments** — don't pass large data as task arguments. Store data externally (S3, database) and pass an ID/URL.
