# Temporal — Child Workflows & Continue-As-New

> Source: [docs.temporal.io/develop/python/child-workflows](https://docs.temporal.io/develop/python/child-workflows) | [docs.temporal.io/develop/python/continue-as-new](https://docs.temporal.io/develop/python/continue-as-new)

## When to Use Child Workflows

Use child workflows when you need to:
- Decompose a large workflow into independent units
- Enforce different retry policies per sub-workflow
- Allow sub-workflows to outlive the parent (abandon policy)
- Partition work across different task queues
- Create a clear ownership boundary for different teams

Avoid child workflows for simple sequential operations — just call activities directly.

## Starting Child Workflows (Python)

### Execute and Wait

```python
from temporalio import workflow

@workflow.defn
class ParentWorkflow:
    @workflow.run
    async def run(self, order_id: str) -> str:
        # Start child and wait for result
        result = await workflow.execute_child_workflow(
            PaymentWorkflow.run,
            PaymentInput(order_id=order_id, amount=99.99),
            id=f"payment-{order_id}",
        )
        return f"Payment completed: {result}"
```

### Start Without Waiting

```python
@workflow.defn
class ParentWorkflow:
    @workflow.run
    async def run(self, order_id: str) -> str:
        # Start child and get handle
        handle = await workflow.start_child_workflow(
            ShippingWorkflow.run,
            ShippingInput(order_id=order_id),
            id=f"shipping-{order_id}",
        )

        # Do other work while child runs
        await workflow.execute_activity(
            update_status, "shipping_started",
            start_to_close_timeout=timedelta(seconds=10),
        )

        # Wait for child result
        result = await handle
        return result
```

### Child Workflow Options

```python
result = await workflow.execute_child_workflow(
    ChildWorkflow.run,
    input_data,
    id="child-workflow-id",
    task_queue="child-queue",                    # Different task queue
    execution_timeout=timedelta(hours=24),       # Max total duration
    run_timeout=timedelta(hours=1),              # Max single run
    retry_policy=RetryPolicy(maximum_attempts=3),
    parent_close_policy=ParentClosePolicy.ABANDON,
    cancellation_type=workflow.ChildWorkflowCancellationType.WAIT_CANCELLATION_COMPLETED,
    memo={"context": "child-context"},
)
```

## Parent Close Policy

Controls what happens to child workflows when the parent closes:

```python
from temporalio.workflow import ParentClosePolicy

# TERMINATE (default) — child is terminated when parent closes
parent_close_policy=ParentClosePolicy.TERMINATE

# ABANDON — child continues running independently
parent_close_policy=ParentClosePolicy.ABANDON

# REQUEST_CANCEL — child receives cancellation request
parent_close_policy=ParentClosePolicy.REQUEST_CANCEL
```

### When to Use Each

| Policy | Use When |
|--------|----------|
| `TERMINATE` | Child results only matter within parent context |
| `ABANDON` | Child represents independent work (e.g., cleanup, notification) |
| `REQUEST_CANCEL` | Child should attempt graceful shutdown |

## Parallel Child Workflows

```python
import asyncio

@workflow.defn
class FanOutWorkflow:
    @workflow.run
    async def run(self, regions: list[str]) -> dict[str, str]:
        # Start all children in parallel
        tasks = {
            region: workflow.execute_child_workflow(
                RegionProcessingWorkflow.run,
                RegionInput(region=region),
                id=f"region-{region}",
            )
            for region in regions
        }

        results = {}
        for region, task in tasks.items():
            results[region] = await task

        return results
```

## Signaling Child Workflows

### From Parent

```python
@workflow.defn
class ParentWorkflow:
    @workflow.run
    async def run(self) -> None:
        handle = await workflow.start_child_workflow(
            ChildWorkflow.run,
            id="child-1",
        )
        # Send signal to child
        await handle.signal(ChildWorkflow.update_config, new_config)
```

### Between Unrelated Workflows

```python
@workflow.defn
class WorkflowA:
    @workflow.run
    async def run(self) -> None:
        # Signal a workflow by its ID (not a child)
        ext_handle = workflow.get_external_workflow_handle_for(
            WorkflowB.run,
            "workflow-b-id",
        )
        await ext_handle.signal(WorkflowB.notify, "data from A")
```

## Continue-As-New

For workflows that run indefinitely (polling, processing queues), use Continue-As-New to avoid unbounded Event History growth:

```python
@workflow.defn
class PollingWorkflow:
    @workflow.run
    async def run(self, state: PollingState) -> None:
        # Process a batch
        for i in range(100):
            item = await workflow.execute_activity(
                poll_queue,
                start_to_close_timeout=timedelta(seconds=10),
            )
            if item:
                await workflow.execute_activity(
                    process_item,
                    item,
                    start_to_close_timeout=timedelta(seconds=30),
                )

        # Continue with fresh history, carrying forward state
        workflow.continue_as_new(
            PollingState(
                items_processed=state.items_processed + 100,
                last_run=workflow.now(),
            )
        )
```

### When to Use Continue-As-New

- Workflows that run indefinitely (polling, subscriptions)
- Event History approaching size limits (50K events is a good threshold)
- Workflows with accumulated state that should be compacted

### Continue-As-New with Different Workflow

```python
# Continue as a different workflow type
workflow.continue_as_new(
    new_state,
    workflow=UpgradedPollingWorkflow.run,
    task_queue="new-queue",
)
```

## TypeScript Patterns

### Child Workflows

```typescript
import { executeChild, startChild } from '@temporalio/workflow';

export async function parentWorkflow(orderId: string): Promise<string> {
  // Execute and wait
  const result = await executeChild('paymentWorkflow', {
    args: [{ orderId, amount: 99.99 }],
    workflowId: `payment-${orderId}`,
  });

  // Start without waiting
  const handle = await startChild('shippingWorkflow', {
    args: [{ orderId }],
    workflowId: `shipping-${orderId}`,
    parentClosePolicy: ParentClosePolicy.ABANDON,
  });

  return await handle.result();
}
```

### Continue-As-New

```typescript
import { continueAsNew } from '@temporalio/workflow';

export async function pollingWorkflow(state: PollingState): Promise<void> {
  for (let i = 0; i < 100; i++) {
    await processItem();
  }
  await continueAsNew<typeof pollingWorkflow>({
    ...state,
    itemsProcessed: state.itemsProcessed + 100,
  });
}
```

## Common Pitfalls

1. **Unbounded Event History**: Workflows processing unbounded items without Continue-As-New will eventually hit history limits (50K events default). Always use Continue-As-New for infinite loops.

2. **Parent Close Policy mismatch**: Forgetting to set `ABANDON` for children that should outlive the parent leads to premature termination.

3. **Too many child workflows**: Each child adds events to the parent's history. For thousands of items, consider batching into fewer children or using activities instead.

4. **Missing await**: Starting a child without awaiting its result (or the handle) causes the parent to complete before the `ChildWorkflowExecutionStarted` event is recorded.
