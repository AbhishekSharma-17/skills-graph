# Temporal — Workers

> Source: [docs.temporal.io/develop/python/workers](https://docs.temporal.io/develop/python/workers/run-worker-process) | [docs.temporal.io/develop/typescript/workers](https://docs.temporal.io/develop/typescript/core-application)

## What Are Workers?

Workers are processes that execute workflow and activity code. They long-poll the Temporal Service for tasks from a specific Task Queue, execute the code, and report results back. Workers contain your application logic — the Temporal Service never runs your code directly.

## Python Worker Setup

### Basic Worker

```python
import asyncio
from temporalio.client import Client
from temporalio.worker import Worker

async def main():
    client = await Client.connect("localhost:7233")

    worker = Worker(
        client,
        task_queue="my-task-queue",
        workflows=[OrderWorkflow, ShippingWorkflow],
        activities=[process_payment, send_notification, update_inventory],
    )
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### Worker with Graceful Shutdown

```python
import asyncio
import signal
from temporalio.client import Client
from temporalio.worker import Worker

async def main():
    client = await Client.connect("localhost:7233")

    worker = Worker(
        client,
        task_queue="my-task-queue",
        workflows=[OrderWorkflow],
        activities=[process_payment],
    )

    loop = asyncio.get_event_loop()
    shutdown_event = asyncio.Event()

    def signal_handler():
        shutdown_event.set()

    loop.add_signal_handler(signal.SIGINT, signal_handler)
    loop.add_signal_handler(signal.SIGTERM, signal_handler)

    async with worker:
        await shutdown_event.wait()
        # Worker context manager handles graceful shutdown

asyncio.run(main())
```

### Worker with Thread Pool for Sync Activities

```python
import concurrent.futures
from temporalio.worker import Worker

worker = Worker(
    client,
    task_queue="compute-queue",
    workflows=[ComputeWorkflow],
    activities=[cpu_bound_activity],
    activity_executor=concurrent.futures.ThreadPoolExecutor(max_workers=10),
)
```

## TypeScript Worker Setup

```typescript
import { Worker } from '@temporalio/worker';
import * as activities from './activities';

async function run() {
  const worker = await Worker.create({
    workflowsPath: require.resolve('./workflows'),
    activities,
    taskQueue: 'my-task-queue',
  });
  await worker.run();
}

run().catch((err) => {
  console.error(err);
  process.exit(1);
});
```

### Worker with Custom Configuration

```typescript
const worker = await Worker.create({
  workflowsPath: require.resolve('./workflows'),
  activities,
  taskQueue: 'my-task-queue',
  maxConcurrentActivityTaskExecutions: 100,
  maxConcurrentWorkflowTaskExecutions: 100,
  maxCachedWorkflows: 1000,
  stickyQueueScheduleToStartTimeout: '10s',
});
```

## Task Queues

Task Queues are the routing mechanism between the Temporal Service and Workers.

### Key Rules

1. **All workers on the same Task Queue must register the same workflows and activities.** Mismatched registrations cause runtime errors.
2. Multiple workers can poll the same Task Queue for horizontal scaling
3. Different Task Queues can serve different purposes (e.g., high-priority vs low-priority)

### Task Queue Strategy Patterns

```python
# Separate queues by workload type
worker_api = Worker(client, task_queue="api-workflows", workflows=[...], activities=[...])
worker_compute = Worker(client, task_queue="compute-heavy", workflows=[...], activities=[...])
worker_email = Worker(client, task_queue="email-notifications", workflows=[...], activities=[...])
```

### Per-Activity Task Queues

Route specific activities to specialized workers:

```python
# In a workflow — send heavy activities to a different queue
result = await workflow.execute_activity(
    render_video,
    input,
    task_queue="gpu-workers",  # Override the workflow's task queue
    start_to_close_timeout=timedelta(minutes=30),
)
```

## Worker Configuration Options (Python)

| Parameter | Description | Default |
|-----------|-------------|---------|
| `task_queue` | Task Queue to poll | Required |
| `workflows` | Workflow classes to register | `[]` |
| `activities` | Activity functions to register | `[]` |
| `activity_executor` | Executor for sync activities | Thread pool |
| `max_concurrent_workflow_tasks` | Max parallel workflow tasks | 100 |
| `max_concurrent_activities` | Max parallel activities | 100 |
| `max_concurrent_local_activities` | Max parallel local activities | 100 |
| `max_cached_workflows` | Sticky cache size | 1000 |
| `workflow_runner` | Custom runner (e.g., sandbox config) | Sandboxed |
| `interceptors` | List of interceptor classes | `[]` |
| `build_id` | Worker build identifier (versioning) | Auto |
| `use_worker_versioning` | Enable worker versioning | `False` |
| `graceful_shutdown_timeout` | Time for in-progress tasks | `0s` |

## Worker Tuning

### Scaling Concurrent Executions

```python
worker = Worker(
    client,
    task_queue="high-throughput",
    workflows=[BatchWorkflow],
    activities=[process_item],
    max_concurrent_activities=200,         # More parallel activities
    max_concurrent_workflow_tasks=50,      # Fewer workflow tasks (less CPU)
    max_concurrent_local_activities=50,
)
```

### Multiple Workers in One Process

```python
async def main():
    client = await Client.connect("localhost:7233")

    workers = [
        Worker(client, task_queue="workflows", workflows=[OrderWorkflow]),
        Worker(client, task_queue="activities", activities=[process_payment]),
        Worker(client, task_queue="notifications", activities=[send_email]),
    ]

    # Run all workers concurrently
    await asyncio.gather(*[w.run() for w in workers])
```

## Connecting to Temporal Cloud

### Python

```python
from temporalio.client import Client, TLSConfig

client = await Client.connect(
    "your-namespace.a]b2c.tmprl.cloud:7233",
    namespace="your-namespace.a1b2c",
    tls=TLSConfig(
        client_cert=Path("client.pem").read_bytes(),
        client_private_key=Path("client.key").read_bytes(),
    ),
)
```

### TypeScript

```typescript
import { Client, Connection } from '@temporalio/client';
import fs from 'fs';

const connection = await Connection.connect({
  address: 'your-namespace.a1b2c.tmprl.cloud:7233',
  tls: {
    clientCertPair: {
      crt: fs.readFileSync('client.pem'),
      key: fs.readFileSync('client.key'),
    },
  },
});

const client = new Client({ connection, namespace: 'your-namespace.a1b2c' });
```

## Production Deployment Considerations

### Health Checks

Workers expose status through their running state:

```python
from aiohttp import web

worker = Worker(client, task_queue="my-queue", ...)

async def health_check(request):
    if worker.is_running:
        return web.Response(text="ok")
    return web.Response(status=503, text="worker not running")
```

### Worker Identity

```python
worker = Worker(
    client,
    task_queue="my-queue",
    workflows=[...],
    identity=f"worker-{hostname}-{pid}",  # Custom identity for debugging
)
```

### Resource Isolation

Deploy workflow-only and activity-only workers separately:

```python
# Worker 1: Only workflows (lightweight, no I/O)
workflow_worker = Worker(
    client,
    task_queue="orders",
    workflows=[OrderWorkflow, ShippingWorkflow],
)

# Worker 2: Only activities (can be scaled independently)
activity_worker = Worker(
    client,
    task_queue="orders",
    activities=[process_payment, update_inventory, send_notification],
)
```

This allows independent scaling — add more activity workers when I/O is the bottleneck, more workflow workers when orchestration load increases.
