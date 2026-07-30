# dlt Performance Tuning

> Source: https://dlthub.com/docs/reference/performance | dlt v1.29.1

## Table of Contents
- [Overview](#overview)
- [Extract Phase Optimization](#extract-phase-optimization)
- [Memory and Buffer Management](#memory-and-buffer-management)
- [File Rotation](#file-rotation)
- [Extract Parallelism](#extract-parallelism)
- [Normalize Parallelism](#normalize-parallelism)
- [Load Parallelism](#load-parallelism)
- [Complete Parallel Pipeline](#complete-parallel-pipeline)
- [Multiple Pipelines](#multiple-pipelines)
- [JSON Performance](#json-performance)
- [Storage Configuration](#storage-configuration)
- [Pitfalls](#pitfalls)

## Overview

dlt parallelism operates at three levels:
- **Extract**: thread pool for sync resources, async event loop for async resources
- **Normalize**: process pool for concurrent file processing
- **Load**: thread pool for parallel file uploads

## Extract Phase Optimization

### Yield pages instead of individual rows
Each yielded chunk goes through the extract pipeline once. Batching yields significant savings:

```python
from itertools import islice

@dlt.resource
def database_cursor_chunked():
    rows = get_rows(10000)
    while item_slice := list(islice(rows, 1000)):
        yield item_slice
```

### Extraction mode: FIFO vs Round Robin

```toml
# config.toml
[extract]
next_item_mode = "round_robin"  # Default: one item per resource sequentially

[sources.my_pipeline.extract]
next_item_mode = "fifo"  # Extracts each resource fully before moving to next
```

Use `fifo` for debugging complex sources with many connected resources.

## Memory and Buffer Management

### In-memory buffer configuration

Default buffer: 5,000 items. Increase for throughput on capable machines:

```toml
# All buffers (extract and normalize)
[data_writer]
buffer_max_items = 100

# Extract buffers only
[sources.data_writer]
buffer_max_items = 100

# Source-specific
[sources.zendesk_support.data_writer]
buffer_max_items = 100

# Normalize stage only
[normalize.data_writer]
buffer_max_items = 100
```

### Compression control

```toml
[normalize.data_writer]
disable_compression = true
```

### Resource usage monitoring
Install `psutil` and enable progress logging:
```toml
progress = "log"
```

Or via environment:
```bash
PROGRESS=log python pipeline_script.py
```

## File Rotation

Critical for parallel processing. Default: no rotation (single file per resource).

```toml
# By item count
[data_writer]
file_max_items = 100000

# By file size (bytes)
[data_writer]
file_max_bytes = 1000000

# Source-specific
[sources.data_writer]
file_max_items = 100000
file_max_bytes = 1000000

# Normalize stage
[normalize.data_writer]
file_max_items = 100000
file_max_bytes = 1000000
```

File rotation creates multiple smaller files that can be processed in parallel during normalize and load phases.

## Extract Parallelism

### Sync resources with thread pool
```python
@dlt.resource(parallelized=True)
def list_users(n_users):
    for i in range(1, 1 + n_users):
        yield i

@dlt.transformer(parallelized=True)
def get_user_details(user_id):
    return {"entity": "user", "id": user_id}

@dlt.source
def api_data():
    return [
        list_users(24) | get_user_details,
        list_products(32) | get_product_details,
    ]
```

### Async resources (no flag needed)
```python
@dlt.resource
async def a_list_items(start, limit):
    index = start
    while index < start + limit:
        await asyncio.sleep(0.1)
        yield index
        index += 1

@dlt.transformer
async def a_get_details(item_id):
    await asyncio.sleep(0.1)
    return {"row": item_id}
```

### Worker configuration

```toml
# Global
[extract]
workers = 1

# Source-specific
[sources.zendesk_support.extract]
workers = 2

# Resource-specific
[sources.zendesk_support.tickets.extract]
workers = 4

# Async parallelism limit (default: 20)
[extract]
max_parallel_items = 10
```

## Normalize Parallelism

Uses process pool for concurrent file processing. Requires file rotation to be effective:

```toml
[normalize.data_writer]
file_max_bytes = 1000000

[normalize]
workers = 3
start_method = "spawn"  # Critical on Linux when using threads
```

The default spawn method on Linux is `fork`. If you use threads (or libraries that use threads), switch to `spawn` to avoid deadlocks.

## Load Parallelism

Thread pool–based (I/O-bound). Default: 20 threads:

```toml
[normalize.data_writer]
file_max_bytes = 1000000

[load]
workers = 50
```

## Complete Parallel Pipeline

```toml
# config.toml
[sources.my_pipeline.data_writer]
file_max_items = 100000

[normalize]
workers = 3

[normalize.data_writer]
file_max_items = 100000

[load]
workers = 11
```

```python
import dlt
from itertools import islice
from dlt.common import pendulum

@dlt.resource(name="table")
def read_table(limit):
    rows = iter(range(limit))
    while item_slice := list(islice(rows, 1000)):
        now = pendulum.now().isoformat()
        yield [
            {"row": _id, "description": f"row {_id}", "timestamp": now}
            for _id in item_slice
        ]

pipeline = dlt.pipeline("parallel_load", destination="duckdb", dev_mode=True)
pipeline.extract(read_table(1000000), loader_file_format="jsonl")
print(pipeline.normalize())
print(pipeline.load())
```

## Multiple Pipelines

Run multiple pipelines concurrently in separate threads:

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
import dlt
from dlt.common.runtime import signals

def _run_pipeline(pipeline, gen_):
    return pipeline.run(gen_())

pipeline_1 = dlt.pipeline("pipeline_1", destination="duckdb", dev_mode=True)
pipeline_2 = dlt.pipeline("pipeline_2", destination="duckdb", dev_mode=True)

async def _run_async():
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as executor:
        results = await asyncio.gather(
            loop.run_in_executor(executor, _run_pipeline, pipeline_1, resource_a),
            loop.run_in_executor(executor, _run_pipeline, pipeline_2, resource_b),
        )
    print("pipeline_1", results[0])
    print("pipeline_2", results[1])

with signals.intercepted_signals():
    asyncio.run(_run_async())

pipeline_1.activate()
pipeline_2.activate()
```

## JSON Performance

dlt uses `orjson` by default for JSON parsing. Custom encoder for unsupported types:

```python
from dlt.common import json

def my_custom_encoder(obj):
    if isinstance(obj, AnyUrl):
        return obj.unicode_string()
    raise TypeError(repr(obj) + " is not JSON serializable")

json.set_custom_encoder(my_custom_encoder)
```

## Storage Configuration

### Custom data directory
```python
import os
os.environ["DLT_DATA_DIR"] = "/path/to/mounted/bucket/dlt_pipeline_data"
```

### Cloud function FUSE mount (Terraform)
```hcl
volume_mounts {
  mount_path = "/usr/src/ingestion/pipeline_storage"
  name       = "pipeline_bucket"
}
volumes {
  name = "pipeline_bucket"
  gcs {
    bucket        = google_storage_bucket.dlt_pipeline_data_bucket.name
    read_only     = false
    mount_options = ["rename-dir-limit=100000"]
  }
}
```

## Pitfalls

1. **Never run pipelines with identical names in the same directory simultaneously** — they share state and will corrupt each other

2. **Process spawn method on Linux** — if using threads, set `start_method = "spawn"` in normalize config to avoid fork-related deadlocks

3. **File rotation is required for parallelism** — without `file_max_items` or `file_max_bytes`, normalize and load can't parallelize

4. **Staging dataset conflicts** — when multiple pipelines write to the same dataset with staging, assign unique `staging_dataset_name_layout` per pipeline or disable automatic cleanup

5. **Memory pressure** — reduce `buffer_max_items` on constrained environments; install `psutil` and enable `progress="log"` to monitor
