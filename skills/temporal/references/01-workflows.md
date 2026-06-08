# Temporal — Workflows

> Source: [docs.temporal.io/develop/python/workflows](https://docs.temporal.io/develop/python/workflows/basics) | [docs.temporal.io/develop/typescript/workflows](https://docs.temporal.io/develop/typescript/workflows/basics)

## Table of Contents

- [Python Workflow Definition](#python-workflow-definition)
- [TypeScript Workflow Definition](#typescript-workflow-definition)
- [Deterministic Constraints](#deterministic-constraints)
- [Safe Alternatives for Non-Deterministic Operations](#safe-alternatives-for-non-deterministic-operations)
- [Workflow Parameters](#workflow-parameters)
- [Calling Activities from Workflows](#calling-activities-from-workflows)
- [Timers and Sleep](#timers-and-sleep)
- [Wait Conditions](#wait-conditions)
- [Sandbox Mode (Python)](#sandbox-mode-python)
- [Common Patterns](#common-patterns)

## Python Workflow Definition

Workflows are defined as classes using the `@workflow.defn` decorator with a `@workflow.run` entry point method:

```python
from dataclasses import dataclass
from datetime import timedelta
from temporalio import workflow

@dataclass
class OrderInput:
    order_id: str
    customer_id: str
    items: list[str]

@workflow.defn
class OrderWorkflow:
    @workflow.run
    async def run(self, input: OrderInput) -> str:
        result = await workflow.execute_activity(
            process_order,
            input,
            start_to_close_timeout=timedelta(seconds=30),
        )
        return result
```

Rules:
- The class must have exactly one `@workflow.run` method
- The `@workflow.run` method must be `async def`
- All parameters and return values must be serializable

### Custom Workflow Name

```python
@workflow.defn(name="OrderProcessing")
class OrderWorkflow:
    ...
```

Without `name=`, the unqualified class name becomes the workflow type.

## TypeScript Workflow Definition

In TypeScript, workflows are plain async functions (not classes):

```typescript
import { proxyActivities } from '@temporalio/workflow';
import type * as activities from './activities';

const { processOrder } = proxyActivities<typeof activities>({
  startToCloseTimeout: '30 seconds',
});

interface OrderInput {
  orderId: string;
  customerId: string;
  items: string[];
}

export async function orderWorkflow(input: OrderInput): Promise<string> {
  return await processOrder(input);
}
```

The function name becomes the workflow type. There is no mechanism to customize it — the exported function name is the identifier.

## Deterministic Constraints

Workflow code must be deterministic for replay. Prohibited patterns:

| Prohibited | Why |
|-----------|-----|
| Threading | Non-deterministic scheduling |
| `random.random()` | Different values on replay |
| `datetime.now()` | Time differs on replay |
| `uuid.uuid4()` | Different UUIDs on replay |
| Network I/O | Side effects must go in activities |
| File I/O | Side effects must go in activities |
| Global state mutation | Shared mutable state breaks isolation |
| External process calls | Non-deterministic |
| `print()` | Use `workflow.logger` instead |

## Safe Alternatives for Non-Deterministic Operations

### Python

```python
from temporalio import workflow

# Logging (replay-aware — suppressed during replay)
workflow.logger.info("Processing order %s", order_id)

# Random numbers (deterministic, seeded per workflow)
value = workflow.random().randint(1, 100)

# UUIDs (deterministic)
unique_id = workflow.uuid4()

# Current time (returns time of last workflow task completion)
now = workflow.now()
```

### TypeScript

```typescript
import { log, sleep } from '@temporalio/workflow';

// Logging (replay-aware)
log.info('Processing order', { orderId });

// Random (deterministic — Math.random() is replaced in sandbox)
const value = Math.random();

// UUID (deterministic — relies on deterministic Math.random())
import { v4 as uuid4 } from 'uuid';
const id = uuid4();

// Date.now() returns time of last workflow task completion
const now = Date.now();
```

## Workflow Parameters

Both SDKs strongly recommend using a single object parameter:

### Python — Dataclass Parameters

```python
from dataclasses import dataclass

@dataclass
class TransferInput:
    source_account: str
    target_account: str
    amount: float
    reference: str

@workflow.defn
class TransferWorkflow:
    @workflow.run
    async def run(self, input: TransferInput) -> str:
        ...
```

### TypeScript — Interface Parameters

```typescript
interface TransferInput {
  sourceAccount: string;
  targetAccount: string;
  amount: number;
  reference: string;
}

export async function transferWorkflow(input: TransferInput): Promise<string> {
  ...
}
```

Using a single object allows adding new fields without breaking the workflow signature, which is critical for versioning long-running workflows.

## Calling Activities from Workflows

### Python

```python
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

@workflow.defn
class OrderWorkflow:
    @workflow.run
    async def run(self, input: OrderInput) -> str:
        # Simple call
        result = await workflow.execute_activity(
            validate_order,
            input,
            start_to_close_timeout=timedelta(seconds=10),
        )

        # With custom retry policy
        result = await workflow.execute_activity(
            charge_payment,
            input,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                maximum_attempts=5,
                initial_interval=timedelta(seconds=1),
                backoff_coefficient=2.0,
            ),
        )

        # Start without waiting (get handle)
        handle = workflow.start_activity(
            send_notification,
            input,
            start_to_close_timeout=timedelta(seconds=10),
        )
        # ... do other work ...
        await handle  # await later

        return result
```

### TypeScript

```typescript
import { proxyActivities } from '@temporalio/workflow';
import type * as activities from './activities';

const { validateOrder, chargePayment, sendNotification } = proxyActivities<typeof activities>({
  startToCloseTimeout: '30 seconds',
  retry: {
    maximumAttempts: 5,
    initialInterval: '1s',
    backoffCoefficient: 2,
  },
});

export async function orderWorkflow(input: OrderInput): Promise<string> {
  await validateOrder(input);
  const result = await chargePayment(input);
  await sendNotification(input);
  return result;
}
```

## Timers and Sleep

### Python

```python
import asyncio
from temporalio import workflow

@workflow.defn
class ReminderWorkflow:
    @workflow.run
    async def run(self) -> None:
        # Durable sleep — survives crashes and restarts
        await asyncio.sleep(60 * 60 * 24)  # 24 hours
        await workflow.execute_activity(
            send_reminder,
            start_to_close_timeout=timedelta(seconds=10),
        )
```

### TypeScript

```typescript
import { sleep } from '@temporalio/workflow';

export async function reminderWorkflow(): Promise<void> {
  await sleep('24 hours');
  await sendReminder();
}
```

Temporal timers are durable — they survive process restarts. The timer state is stored in the Event History, not in memory.

## Wait Conditions

Block workflow execution until a condition becomes true:

### Python

```python
@workflow.defn
class ApprovalWorkflow:
    def __init__(self):
        self.approved = False

    @workflow.signal
    def approve(self) -> None:
        self.approved = True

    @workflow.run
    async def run(self) -> str:
        # Wait until approved or timeout
        try:
            await workflow.wait_condition(
                lambda: self.approved,
                timeout=timedelta(hours=24),
            )
            return "approved"
        except asyncio.TimeoutError:
            return "timed_out"
```

## Sandbox Mode (Python)

The Python SDK runs workflows in a sandbox that intercepts non-deterministic calls. For third-party libraries that don't need sandboxing:

```python
with workflow.unsafe.imports_passed_through():
    import pydantic
```

Or configure at the Worker level:

```python
from temporalio.worker import Worker
from temporalio.worker.workflow_sandbox import SandboxedWorkflowRunner, SandboxRestrictions

worker = Worker(
    client,
    task_queue="my-queue",
    workflows=[MyWorkflow],
    workflow_runner=SandboxedWorkflowRunner(
        restrictions=SandboxRestrictions.default.with_passthrough_modules("pydantic")
    ),
)
```

## Common Patterns

### Sequential Activity Execution

```python
@workflow.defn
class PipelineWorkflow:
    @workflow.run
    async def run(self, data: str) -> str:
        validated = await workflow.execute_activity(
            validate, data, start_to_close_timeout=timedelta(seconds=10))
        transformed = await workflow.execute_activity(
            transform, validated, start_to_close_timeout=timedelta(seconds=30))
        result = await workflow.execute_activity(
            load, transformed, start_to_close_timeout=timedelta(seconds=60))
        return result
```

### Parallel Activity Execution

```python
import asyncio

@workflow.defn
class FanOutWorkflow:
    @workflow.run
    async def run(self, items: list[str]) -> list[str]:
        tasks = [
            workflow.execute_activity(
                process_item, item, start_to_close_timeout=timedelta(seconds=30))
            for item in items
        ]
        results = await asyncio.gather(*tasks)
        return list(results)
```

### Stateful Workflow with Multiple Entry Points

```python
@workflow.defn
class ShoppingCartWorkflow:
    def __init__(self):
        self.items: list[str] = []
        self.checked_out = False

    @workflow.signal
    def add_item(self, item: str) -> None:
        self.items.append(item)

    @workflow.signal
    def remove_item(self, item: str) -> None:
        self.items.remove(item)

    @workflow.query
    def get_items(self) -> list[str]:
        return list(self.items)

    @workflow.signal
    def checkout(self) -> None:
        self.checked_out = True

    @workflow.run
    async def run(self) -> list[str]:
        await workflow.wait_condition(lambda: self.checked_out)
        await workflow.execute_activity(
            process_order, self.items,
            start_to_close_timeout=timedelta(seconds=30))
        return self.items
```
