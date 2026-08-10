# Gradio — Queuing & Performance

> Source: [gradio.app/guides/queuing](https://gradio.app/guides/queuing) · [gradio.app/guides/batch-functions](https://gradio.app/guides/batch-functions)

## Table of Contents

- [Overview](#overview)
- [Queue System](#queue-system)
- [Concurrency Control](#concurrency-control)
- [Batch Processing](#batch-processing)
- [Performance Optimization](#performance-optimization)
- [File Handling](#file-handling)
- [Caching](#caching)
- [Resource Cleanup](#resource-cleanup)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## Overview

Gradio's built-in queue system manages concurrent requests, prevents timeouts, and enables features like streaming and progress bars. It's enabled by default in modern versions.

## Queue System

### Basic Configuration

```python
with gr.Blocks() as demo:
    # Components and events...
    pass

demo.queue(
    max_size=100,          # Max requests in queue (None = unlimited)
    default_concurrency_limit=1,  # Default per-event concurrency
)
demo.launch()
```

### Queue Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_size` | `int \| None` | `None` | Max queue length; excess gets error |
| `default_concurrency_limit` | `int \| None` | `1` | Default concurrent executions per event |

### Per-Event Concurrency

```python
# This event allows 5 concurrent executions
btn.click(fn=fast_fn, inputs=inp, outputs=out, concurrency_limit=5)

# This event allows unlimited concurrent executions
btn.click(fn=read_only_fn, inputs=inp, outputs=out, concurrency_limit=None)

# This event allows only 1 (default)
btn.click(fn=gpu_fn, inputs=inp, outputs=out, concurrency_limit=1)
```

### Concurrency Groups

Share a concurrency pool across multiple events:

```python
# Both events share a pool of 2 concurrent slots
btn1.click(fn=fn1, concurrency_limit=2, concurrency_id="gpu_pool")
btn2.click(fn=fn2, concurrency_limit=2, concurrency_id="gpu_pool")
```

## Concurrency Control

### Trigger Modes

| Mode | Default For | Behavior |
|------|------------|----------|
| `"once"` | `.click()`, `.submit()` | No new submissions while pending |
| `"multiple"` | — | Unlimited concurrent submissions |
| `"always_last"` | `.change()`, `.key_up()` | Queues latest, replaces pending |

```python
# Fast search: always process the latest keystroke
inp.change(
    fn=search,
    inputs=inp,
    outputs=results,
    trigger_mode="always_last",
)

# File processing: allow multiple concurrent
upload.upload(
    fn=process_file,
    inputs=upload,
    outputs=result,
    trigger_mode="multiple",
    concurrency_limit=3,
)
```

### Disabling Queue for Specific Events

```python
# Skip queue for fast operations
btn.click(fn=quick_fn, inputs=inp, outputs=out, queue=False)
```

## Batch Processing

Process multiple requests simultaneously for GPU-bound workloads:

```python
def classify_batch(images):
    """Accepts a list of images, returns a list of labels."""
    predictions = model.predict_batch(images)
    return [pred.label for pred in predictions]

demo = gr.Interface(
    fn=classify_batch,
    inputs=gr.Image(),
    outputs=gr.Label(),
    batch=True,
    max_batch_size=8,
)
```

### Batch with Blocks

```python
with gr.Blocks() as demo:
    img = gr.Image()
    label = gr.Label()
    btn = gr.Button("Classify")

    btn.click(
        fn=classify_batch,
        inputs=img,
        outputs=label,
        batch=True,
        max_batch_size=8,
    )
```

### Batch Function Rules

1. Each input parameter receives a **list** of values (one per request)
2. All input lists have equal length (up to `max_batch_size`)
3. Must return a **tuple of lists**, one list per output
4. Batch is gathered from queued requests

```python
def batch_fn(texts: list[str], temperatures: list[float]) -> tuple[list[str], list[float]]:
    results = []
    scores = []
    for text, temp in zip(texts, temperatures):
        r, s = process(text, temp)
        results.append(r)
        scores.append(s)
    return results, scores
```

## Performance Optimization

### Model Loading

```python
# Load model once at startup (global scope)
model = load_model("my-model")

def predict(image):
    return model(image)

# NOT inside the function:
def predict_slow(image):
    model = load_model("my-model")  # Reloads every call!
    return model(image)
```

### GPU Memory Management

```python
import torch

def predict(image):
    with torch.no_grad():
        result = model(image)
    torch.cuda.empty_cache()
    return result
```

### Async Functions

```python
import asyncio

async def fetch_data(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()

# Gradio supports async functions natively
btn.click(fn=fetch_data, inputs=url_input, outputs=json_output)
```

### Workers

```python
demo.launch(
    max_threads=40,     # Max parallel threads (default)
    num_workers=4,      # Background workers for file I/O
)
```

## File Handling

### Upload Limits

```python
demo.launch(max_file_size="50mb")  # Limit upload size
```

### Temporary Files

Gradio stores uploaded files in a temp directory. Control cleanup:

```python
with gr.Blocks(delete_cache=(3600, 3600)) as demo:
    # Check every 3600s, delete files older than 3600s
    pass
```

### Allowed/Blocked Paths

```python
demo.launch(
    allowed_paths=["./data", "./models"],    # Accessible
    blocked_paths=["./secrets", "./.env"],    # Blocked (overrides allowed)
)
```

### File Response

```python
def process_and_download(data):
    output_path = "/tmp/result.csv"
    df.to_csv(output_path)
    return output_path  # gr.File output shows download link

btn.click(fn=process_and_download, inputs=data, outputs=gr.File())
```

## Caching

### Example Caching

```python
demo = gr.Interface(
    fn=predict,
    inputs="image",
    outputs="label",
    examples=["cat.jpg", "dog.jpg"],
    cache_examples="lazy",  # "eager" | "lazy" | True | False
)
```

| Mode | Behavior |
|------|----------|
| `"eager"` | Cache all examples at startup |
| `"lazy"` | Cache on first access |
| `True` | Same as `"eager"` |
| `False` | No caching |

### Application-Level Caching

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def expensive_computation(text):
    return model.predict(text)
```

## Resource Cleanup

### Session Cleanup

```python
with gr.Blocks() as demo:
    demo.unload(fn=cleanup_session)

def cleanup_session(request: gr.Request):
    session_id = request.session_hash
    release_gpu(session_id)
```

### Cache Cleanup

```python
with gr.Blocks(delete_cache=(300, 600)) as demo:
    # Check every 300s, delete caches older than 600s
    pass
```

### State Session Capacity

```python
demo.launch(state_session_capacity=10000)  # Max concurrent sessions
```

## Common Patterns

### Rate Limiting

```python
from collections import defaultdict
import time

request_counts = defaultdict(list)

def rate_limited_fn(text, request: gr.Request):
    ip = request.client.host
    now = time.time()
    request_counts[ip] = [t for t in request_counts[ip] if now - t < 60]

    if len(request_counts[ip]) >= 10:
        raise gr.Error("Rate limit exceeded (10/min)")

    request_counts[ip].append(now)
    return process(text)
```

### GPU Queue Pattern

```python
with gr.Blocks() as demo:
    prompt = gr.Textbox()
    image = gr.Image()
    btn = gr.Button("Generate")

    btn.click(
        fn=generate_image,
        inputs=prompt,
        outputs=image,
        concurrency_limit=1,      # One GPU job at a time
        concurrency_id="gpu",
        show_progress="full",
    )

demo.queue(max_size=20)  # Limit queue to prevent long waits
```

### Health Check Endpoint

```python
import gradio as gr
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

demo = gr.Blocks()
# ... build demo
app = gr.mount_gradio_app(app, demo, path="/")
```

## Common Pitfalls

1. **Queue size unlimited**: Without `max_size`, the queue grows unbounded — users wait forever. Set a reasonable limit.
2. **Concurrency too high**: Setting `concurrency_limit` too high on GPU tasks causes OOM errors — match to available GPU memory
3. **Blocking event loop**: CPU-heavy sync functions block other requests — use `max_threads` or run expensive work in a thread pool
4. **File cleanup**: Uploaded files persist in temp dirs — configure `delete_cache` to prevent disk exhaustion
5. **Batch size mismatch**: Batch functions must handle variable-length lists (1 to `max_batch_size`) — don't assume fixed batch size
6. **Progress in cached examples**: `gr.Progress()` won't display in cached example outputs — cache only final results
