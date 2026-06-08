# Temporal — Client

> Source: [docs.temporal.io/develop/python/client](https://docs.temporal.io/develop/python/client/temporal-client) | [docs.temporal.io/develop/typescript](https://docs.temporal.io/develop/typescript)

## Table of Contents

- [Connecting to Temporal](#connecting-to-temporal)
- [Starting Workflows](#starting-workflows)
- [Getting Workflow Handles](#getting-workflow-handles)
- [Workflow Results](#workflow-results)
- [Listing Workflows](#listing-workflows)
- [Cancelling and Terminating](#cancelling-and-terminating)
- [Describing Workflows](#describing-workflows)
- [TypeScript Client](#typescript-client)

## Connecting to Temporal

### Python — Local Development

```python
from temporalio.client import Client

client = await Client.connect("localhost:7233")
```

### Python — Temporal Cloud

```python
from temporalio.client import Client, TLSConfig
from pathlib import Path

client = await Client.connect(
    "your-namespace.a1b2c.tmprl.cloud:7233",
    namespace="your-namespace.a1b2c",
    tls=TLSConfig(
        client_cert=Path("client.pem").read_bytes(),
        client_private_key=Path("client.key").read_bytes(),
    ),
)
```

### Python — With API Key

```python
client = await Client.connect(
    "your-namespace.a1b2c.tmprl.cloud:7233",
    namespace="your-namespace.a1b2c",
    api_key="your-api-key",
    tls=True,
)
```

### Client Options

```python
client = await Client.connect(
    "localhost:7233",
    namespace="production",          # Namespace (default: "default")
    data_converter=MyConverter(),    # Custom serialization
    interceptors=[LoggingInterceptor()],
    identity="my-service-v2",        # Client identity for debugging
)
```

## Starting Workflows

### execute_workflow — Start and Wait for Result

```python
result = await client.execute_workflow(
    OrderWorkflow.run,
    OrderInput(order_id="123", items=["item-a"]),
    id="order-123",
    task_queue="orders",
)
print(f"Order result: {result}")
```

### start_workflow — Start and Get Handle

```python
handle = await client.start_workflow(
    OrderWorkflow.run,
    OrderInput(order_id="123", items=["item-a"]),
    id="order-123",
    task_queue="orders",
)
print(f"Started workflow: {handle.id}")

# Later, get the result
result = await handle.result()
```

### Start Options

```python
handle = await client.start_workflow(
    OrderWorkflow.run,
    OrderInput(order_id="123"),
    id="order-123",
    task_queue="orders",
    execution_timeout=timedelta(hours=24),     # Max total duration
    run_timeout=timedelta(hours=1),            # Max single run
    task_timeout=timedelta(seconds=10),        # Max workflow task
    id_reuse_policy=common.WorkflowIDReusePolicy.REJECT_DUPLICATE,
    retry_policy=RetryPolicy(maximum_attempts=3),
    cron_schedule="0 */6 * * *",               # Deprecated; use Schedules
    memo={"team": "platform"},                 # Unindexed metadata
    search_attributes=TypedSearchAttributes([
        SearchAttributePair(customer_key, "cust-456"),
    ]),
    start_delay=timedelta(minutes=5),          # Delay before first task
)
```

### Workflow ID Strategies

Workflow IDs should be business-meaningful and unique:

```python
# Order processing — use order ID
id=f"order-{order_id}"

# User onboarding — use user ID
id=f"onboarding-{user_id}"

# Scheduled report — use date
id=f"daily-report-{date.today()}"

# Singleton pattern — fixed ID
id="inventory-sync"
```

### ID Conflict Policies

```python
from temporalio import common

# Reject if a workflow with this ID exists (default)
id_reuse_policy=common.WorkflowIDReusePolicy.REJECT_DUPLICATE

# Allow reuse if previous completed/failed/terminated
id_reuse_policy=common.WorkflowIDReusePolicy.ALLOW_DUPLICATE

# Allow reuse if previous failed/terminated (not completed)
id_reuse_policy=common.WorkflowIDReusePolicy.ALLOW_DUPLICATE_FAILED_ONLY

# Terminate existing and start new
id_conflict_policy=common.WorkflowIDConflictPolicy.TERMINATE_EXISTING
```

## Getting Workflow Handles

### By Workflow ID

```python
handle = client.get_workflow_handle("order-123")
result = await handle.result()
```

### Type-Safe Handle

```python
handle = client.get_workflow_handle_for(
    OrderWorkflow.run,
    "order-123",
)
# Now handle.signal(), handle.query() etc. are type-checked
```

## Workflow Results

```python
# Wait for result (blocks until workflow completes)
result = await handle.result()

# Check if workflow is still running
desc = await handle.describe()
print(desc.status)  # WorkflowExecutionStatus.RUNNING, COMPLETED, FAILED, etc.
```

## Listing Workflows

### List All Workflows

```python
async for workflow in client.list_workflows():
    print(f"ID: {workflow.id}, Status: {workflow.status}")
```

### Filter with Queries

```python
# By workflow type
async for wf in client.list_workflows('WorkflowType="OrderWorkflow"'):
    print(wf.id)

# By status
async for wf in client.list_workflows('ExecutionStatus="Running"'):
    print(wf.id)

# By custom search attributes
async for wf in client.list_workflows('CustomerId="cust-456"'):
    print(wf.id)

# Complex queries
async for wf in client.list_workflows(
    'WorkflowType="OrderWorkflow" AND ExecutionStatus="Running" AND StartTime > "2026-01-01"'
):
    print(wf.id)
```

### Count Workflows

```python
count = await client.count_workflows('ExecutionStatus="Running"')
print(f"Running workflows: {count}")
```

## Cancelling and Terminating

### Cancel (Graceful)

```python
handle = client.get_workflow_handle("order-123")
await handle.cancel()
```

Cancellation raises `CancelledError` in the workflow, giving it a chance to run cleanup logic.

### Terminate (Forceful)

```python
await handle.terminate(reason="Manual cleanup")
```

Termination immediately stops the workflow with no cleanup opportunity. Use as a last resort.

## Describing Workflows

```python
desc = await handle.describe()

desc.id                    # Workflow ID
desc.run_id                # Current run ID
desc.workflow_type         # Workflow type name
desc.status                # Execution status enum
desc.task_queue            # Task queue name
desc.start_time            # Start timestamp
desc.close_time            # Close timestamp (if completed)
desc.execution_time        # Execution start time
desc.history_length        # Number of events in history
desc.memo                  # Memo dict
desc.search_attributes     # Search attributes
desc.parent_id             # Parent workflow ID (if child)
desc.parent_run_id         # Parent run ID (if child)
```

## TypeScript Client

### Connect and Start Workflow

```typescript
import { Client, Connection } from '@temporalio/client';

const connection = await Connection.connect({ address: 'localhost:7233' });
const client = new Client({ connection });

// Start and wait
const result = await client.workflow.execute('orderWorkflow', {
  args: [{ orderId: '123', items: ['item-a'] }],
  taskQueue: 'orders',
  workflowId: 'order-123',
});

// Start and get handle
const handle = await client.workflow.start('orderWorkflow', {
  args: [{ orderId: '123' }],
  taskQueue: 'orders',
  workflowId: 'order-123',
});
const result = await handle.result();
```

### Get Handle and Interact

```typescript
const handle = client.workflow.getHandle('order-123');

// Query
const items = await handle.query('getItems');

// Signal
await handle.signal('addItem', 'new-item');

// Cancel
await handle.cancel();

// Terminate
await handle.terminate('manual cleanup');

// Describe
const desc = await handle.describe();
console.log(desc.status.name);
```
