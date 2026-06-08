# Temporal — Activities

> Source: [docs.temporal.io/develop/python/activities](https://docs.temporal.io/develop/python/activities/basics) | [docs.temporal.io/develop/typescript/activities](https://docs.temporal.io/develop/typescript/activities/basics)

## Table of Contents

- [What Are Activities?](#what-are-activities)
- [Python Activity Definition](#python-activity-definition)
- [TypeScript Activity Definition](#typescript-activity-definition)
- [Activity Execution Models (Python)](#activity-execution-models-python)
- [Parameters and Return Values](#parameters-and-return-values)
- [Heartbeating](#heartbeating)
- [Activity Info](#activity-info)
- [Idempotency](#idempotency)
- [Local Activities](#local-activities)
- [Standalone Activities](#standalone-activities)
- [Dependency Injection (TypeScript)](#dependency-injection-typescript)
- [Common Patterns](#common-patterns)

## What Are Activities?

Activities encapsulate non-deterministic operations — API calls, database queries, file I/O, and any side effects. Unlike workflows, activities:
- Can use any code (non-deterministic is fine)
- Are retried automatically on failure
- Execute with at-least-once semantics
- Can heartbeat to report progress and detect cancellation

## Python Activity Definition

```python
from temporalio import activity
from dataclasses import dataclass

@dataclass
class PaymentInput:
    order_id: str
    amount: float
    currency: str

@activity.defn
async def process_payment(input: PaymentInput) -> str:
    result = await payment_gateway.charge(
        order_id=input.order_id,
        amount=input.amount,
        currency=input.currency,
    )
    return result.transaction_id
```

### Custom Activity Name

```python
@activity.defn(name="process-payment")
async def process_payment(input: PaymentInput) -> str:
    ...
```

Without `name=`, the function name becomes the activity type.

## TypeScript Activity Definition

Activities are plain async functions exported from a module:

```typescript
// activities.ts
export async function processPayment(input: PaymentInput): Promise<string> {
  const result = await paymentGateway.charge({
    orderId: input.orderId,
    amount: input.amount,
    currency: input.currency,
  });
  return result.transactionId;
}
```

Activities cannot share a file with workflow code in TypeScript — they must be in separate modules.

## Activity Execution Models (Python)

The Python SDK supports three execution models:

### 1. Asynchronous (default)

```python
@activity.defn
async def fetch_data(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()
```

Runs on the asyncio event loop. Do not use blocking calls — use async-compatible libraries.

### 2. Synchronous Multithreaded

```python
@activity.defn
def cpu_intensive_task(data: bytes) -> bytes:
    return heavy_computation(data)
```

Register with a thread pool executor:

```python
import concurrent.futures

worker = Worker(
    client,
    task_queue="compute-queue",
    workflows=[MyWorkflow],
    activities=[cpu_intensive_task],
    activity_executor=concurrent.futures.ThreadPoolExecutor(max_workers=10),
)
```

### 3. Synchronous Multiprocess

```python
import concurrent.futures
import multiprocessing

worker = Worker(
    client,
    task_queue="compute-queue",
    workflows=[MyWorkflow],
    activities=[cpu_intensive_task],
    activity_executor=concurrent.futures.ProcessPoolExecutor(
        max_workers=4,
        mp_context=multiprocessing.get_context("spawn"),
    ),
)
```

Use for CPU-bound work that benefits from true parallelism.

## Parameters and Return Values

All parameters and return values must be serializable (JSON-serializable by default).

### Size Limits

- Individual argument: **2 MB** maximum
- Total gRPC message: **4 MB** maximum

### Best Practice — Single Object Parameter

```python
@dataclass
class EmailInput:
    recipient: str
    subject: str
    body: str
    attachments: list[str] | None = None

@activity.defn
async def send_email(input: EmailInput) -> bool:
    ...
```

Using a single object parameter allows adding fields without breaking the activity signature.

## Heartbeating

Long-running activities should heartbeat to:
1. Report progress to the Temporal Service
2. Detect cancellation requests
3. Enable activity restart from last heartbeat on retry

### Python

```python
@activity.defn
async def process_large_file(file_path: str) -> int:
    lines_processed = 0
    with open(file_path) as f:
        for i, line in enumerate(f):
            process_line(line)
            lines_processed += 1
            if i % 1000 == 0:
                activity.heartbeat(lines_processed)
    return lines_processed
```

### Heartbeat Timeout

Set from the workflow when calling the activity:

```python
await workflow.execute_activity(
    process_large_file,
    "/data/large.csv",
    start_to_close_timeout=timedelta(hours=1),
    heartbeat_timeout=timedelta(seconds=30),  # Must heartbeat every 30s
)
```

If no heartbeat is received within the timeout, the activity is considered failed and retried.

### Retrieving Last Heartbeat on Retry

```python
@activity.defn
async def resumable_upload(input: UploadInput) -> str:
    # Check if resuming from a previous attempt
    start_offset = activity.info().heartbeat_details[0] if activity.info().heartbeat_details else 0

    for chunk_offset in range(start_offset, input.total_size, CHUNK_SIZE):
        upload_chunk(input.file, chunk_offset, CHUNK_SIZE)
        activity.heartbeat(chunk_offset + CHUNK_SIZE)

    return "upload_complete"
```

## Activity Info

Access metadata about the current activity execution:

```python
@activity.defn
async def my_activity() -> None:
    info = activity.info()

    info.workflow_id          # Parent workflow ID
    info.workflow_run_id      # Parent workflow run ID
    info.activity_id          # Unique activity ID within workflow
    info.activity_type        # Activity type name
    info.task_queue           # Task queue name
    info.attempt              # Current attempt number (starts at 1)
    info.task_token           # Token for async completion
    info.heartbeat_details    # Last heartbeat details (for retries)
    info.scheduled_time       # When the activity was scheduled
    info.current_attempt_scheduled_time  # When current attempt was scheduled
    info.start_to_close_timeout         # Configured timeout
    info.is_local             # Whether this is a local activity
```

## Idempotency

Activities run with at-least-once semantics — crashes before acknowledgment trigger retries. Build idempotency keys from workflow context:

```python
@activity.defn
async def charge_customer(input: ChargeInput) -> str:
    info = activity.info()
    idempotency_key = f"{info.workflow_run_id}-{info.activity_id}"

    result = await payment_service.charge(
        amount=input.amount,
        customer_id=input.customer_id,
        idempotency_key=idempotency_key,
    )
    return result.transaction_id
```

## Local Activities

For very short operations (< 10 seconds, no retries needed), use local activities to avoid the overhead of scheduling through the Temporal Service:

```python
result = await workflow.execute_local_activity(
    quick_validation,
    input,
    start_to_close_timeout=timedelta(seconds=5),
)
```

Local activities run on the same worker and are not recorded as separate events in the history.

## Standalone Activities

Standalone Activities (Public Preview in 2026) allow activities to run independently without being tied to a specific workflow:

```python
from temporalio import activity

@activity.defn(standalone=True)
async def process_webhook(payload: dict) -> str:
    ...
```

These are useful for event-driven architectures where activities are triggered directly.

## Dependency Injection (TypeScript)

Create activity factories to share dependencies:

```typescript
// activities.ts
export const createActivities = (db: Database, emailService: EmailService) => ({
  async lookupUser(userId: string): Promise<User> {
    return await db.users.findById(userId);
  },
  async sendWelcomeEmail(user: User): Promise<void> {
    await emailService.send({
      to: user.email,
      template: 'welcome',
      data: { name: user.name },
    });
  },
});

export type Activities = ReturnType<typeof createActivities>;

// worker.ts
import { Worker } from '@temporalio/worker';
import { createActivities } from './activities';

const activities = createActivities(db, emailService);
const worker = await Worker.create({
  workflowsPath: require.resolve('./workflows'),
  activities,
  taskQueue: 'user-onboarding',
});
```

## Common Patterns

### Async Activity Completion

For activities that must wait for an external event (webhook, human approval):

```python
@activity.defn
async def wait_for_approval(input: ApprovalInput) -> None:
    # Store the task token for later completion
    token = activity.info().task_token
    await approval_service.request_approval(
        request_id=input.request_id,
        callback_token=token,
    )
    # Raise to indicate async completion
    activity.raise_complete_async()
```

Complete the activity later from an external service:

```python
client = await Client.connect("localhost:7233")
handle = client.get_async_activity_handle(task_token=callback_token)
await handle.complete("approved")
# or
await handle.fail(ApplicationError("rejected"))
```

### Activity with Structured Logging

```python
import logging

logger = logging.getLogger(__name__)

@activity.defn
async def process_order(input: OrderInput) -> str:
    info = activity.info()
    logger.info(
        "Processing order",
        extra={
            "order_id": input.order_id,
            "workflow_id": info.workflow_id,
            "attempt": info.attempt,
        },
    )
    ...
```
