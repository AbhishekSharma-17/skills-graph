# Canvas Workflows

> Source: [Celery Canvas Guide](https://docs.celeryq.dev/en/stable/userguide/canvas.html)

## Table of Contents

- [Overview](#overview)
- [Chains](#chains)
- [Groups](#groups)
- [Chords](#chords)
- [Map and Starmap](#map-and-starmap)
- [Chunks](#chunks)
- [Complex Compositions](#complex-compositions)
- [Stamping API](#stamping-api)
- [Best Practices](#best-practices)

## Overview

Canvas primitives compose tasks into workflows. Each primitive is a signature that can be combined with others:

| Primitive | Purpose | Metaphor |
|-----------|---------|----------|
| `chain` | Sequential execution | Pipeline |
| `group` | Parallel execution | Fan-out |
| `chord` | Parallel + callback | MapReduce |
| `starmap` | Apply to each item (single message) | Map |
| `chunks` | Split iterable into batches | Batch |

## Chains

Execute tasks sequentially — each task's result feeds into the next:

```python
from celery import chain

# Explicit chain()
res = chain(add.s(4, 4), mul.s(8), mul.s(10))()
res.get()  # ((4+4) * 8) * 10 = 640

# Pipe operator (preferred)
res = (add.s(2, 2) | mul.s(8) | mul.s(10))()
res.get()  # (2+2) * 8 * 10 = 320
```

### Partial Chains

```python
pipeline = add.s(4) | mul.s(8)
res = pipeline(16)      # (16 + 4) * 8 = 160
res.get()
```

### Accessing Intermediate Results

```python
res = (add.s(4, 4) | mul.s(8) | mul.s(10))()
res.get()                  # 640 (final)
res.parent.get()           # 64  (second task)
res.parent.parent.get()    # 8   (first task)
```

### Error Handling in Chains

If any task fails, subsequent tasks are not executed. Attach error callbacks:

```python
(add.s(2, 2) | mul.s(8)).on_error(error_handler.s()).delay()
```

## Groups

Execute tasks in parallel and collect results:

```python
from celery import group

# Create and execute
res = group(add.s(i, i) for i in range(10))()
res.get(timeout=10)  # [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]
```

### GroupResult Methods

```python
res = group(add.s(i, i) for i in range(5))()

res.ready()            # True when all tasks are done
res.successful()       # True if none raised exceptions
res.failed()           # True if any raised an exception
res.completed_count()  # Number of completed tasks
res.join()             # Gather results as list
res.revoke()           # Revoke all subtasks
```

### Groups with Explicit Tasks

```python
g = group([
    process_image.s(img_id, "resize"),
    process_image.s(img_id, "thumbnail"),
    process_image.s(img_id, "watermark"),
])
res = g.apply_async()
```

## Chords

A chord = group (header) + callback (body). The callback executes after ALL header tasks complete:

```python
from celery import chord

# Sum all results: (0+0) + (1+1) + ... + (9+9) = 90
callback = tsum.s()
header = [add.s(i, i) for i in range(10)]
result = chord(header)(callback)
result.get()  # 90
```

### Shorthand — Pipe Group Into Callback

```python
res = (group(add.s(i, i) for i in range(10)) | tsum.s())()
res.get()  # 90
```

### Immutable Callbacks

When the callback doesn't need the header's results:

```python
chord(
    [import_contact.s(c) for c in contacts],
    notify_complete.si(import_id),  # .si() = immutable
).apply_async()
```

### Error Handling in Chords

If any header task fails, the callback gets a `ChordError`. Remaining header tasks still execute.

```python
@app.task
def on_chord_error(request, exc, traceback):
    print(f"Task {request.id} raised: {exc!r}")

chord(
    [add.s(i, i) for i in range(10)],
    tsum.s().on_error(on_chord_error.s()),
).delay()
```

### Chord Requirements

- Tasks in chords must NOT have `ignore_result=True`
- A result backend must be configured
- If overriding `after_return()`, call `super().after_return()`

## Map and Starmap

Apply a task to each element in a sequence as a single message (runs in one worker):

### Map

```python
# Sum each sublist
res = ~tsum.map([list(range(10)), list(range(100))])
# [45, 4950]
```

### Starmap

```python
# Unpack args for each call
res = ~add.starmap(zip(range(10), range(10)))
# [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]
```

Unlike groups, map/starmap execute sequentially in one worker process.

## Chunks

Split a large iterable into sized batches, each processed as a separate task:

```python
# 100 items split into 10 chunks of 10
res = add.chunks(zip(range(100), range(100)), 10)()
res.get()
# [[0, 2, 4, ...], [20, 22, 24, ...], ...]
```

### Convert to Group for Parallel Execution

```python
g = add.chunks(zip(range(100), range(100)), 10).group()
g.skew(start=1, stop=10)()  # Stagger execution with countdown offsets
```

## Complex Compositions

### Chain → Group (Fan-Out)

```python
workflow = (
    create_user.s()
    | group(import_contacts.s(), send_welcome_email.s())
)
workflow.delay(username="alice", email="alice@example.com")
```

### Group → Chain (Fan-In → Sequential)

```python
workflow = (
    group(fetch_url.s(url) for url in urls)
    | merge_results.s()
    | generate_report.s()
)
workflow.apply_async()
```

### Immutable Signatures in Workflows

Prevent parent results from being prepended:

```python
res = (
    add.s(4, 4)
    | group(add.si(i, i) for i in range(10))
)()
res.get()  # [0, 2, 4, ..., 18] — group ignores add's result
```

### Nested Chords

```python
workflow = chord(
    [
        chord([add.s(1, 1), add.s(2, 2)], tsum.s()),
        chord([add.s(3, 3), add.s(4, 4)], tsum.s()),
    ],
    tsum.s(),  # Sum of sub-chord sums
)
result = workflow.apply_async()
```

### Real-World Example — Image Processing Pipeline

```python
from celery import chain, group, chord

def process_batch(image_ids):
    workflow = chord(
        [
            chain(
                download_image.s(img_id),
                resize_image.s(width=800),
                apply_watermark.s(),
            )
            for img_id in image_ids
        ],
        upload_batch.s(destination="s3://processed/"),
    )
    return workflow.apply_async()
```

## Stamping API

Label canvas components with metadata for debugging and tracing (v5.3+):

```python
sig = add.si(2, 2)
g = group(sig, add.si(3, 3))
g.stamp(stamp="batch-2024-01")
res = g.apply_async()
```

### Custom Stamping Visitor

```python
from celery.canvas import StampingVisitor

class MonitoringVisitor(StampingVisitor):
    def on_signature(self, sig, **headers):
        return {"monitoring_id": generate_id()}

sig = add.s(2, 2)
sig.stamp(visitor=MonitoringVisitor())
```

## Best Practices

**Use chains instead of synchronous subtasks** — never call `.get()` inside a task:

```python
# Bad — deadlock risk
@app.task
def bad():
    result = fetch.delay(url).get()
    parse.delay(result).get()

# Good
workflow = fetch.s(url) | parse.s()
workflow.apply_async()
```

**Use .si() for fire-and-forget callbacks** — when the callback ignores the parent result.

**Use pickle for complex workflows** — JSON serialization can inflate messages with recursive references.

**Chords require result backends** — tasks cannot have `ignore_result=True` inside chords.

**Prefer chord over group + link** — `link` on groups doesn't synchronize properly; chord does.
