# Temporal — Versioning & Safe Deployments

> Source: [docs.temporal.io/develop/python/versioning](https://docs.temporal.io/develop/python/versioning)

## Why Versioning Matters

Temporal workflows can run for days, months, or years. When you update workflow code, running executions must continue correctly — replaying against their existing Event History. Non-deterministic changes (reordering activities, adding/removing steps) break replay and cause `NonDeterminismError`.

## Two Versioning Strategies

| Strategy | How It Works | Best For |
|----------|-------------|----------|
| **Patching** | Conditional branches in code based on history markers | Incremental changes to existing workflows |
| **Worker Versioning** | Pin workflows to specific worker builds | Large-scale refactors, clean separation |

## Patching (Recommended for Most Cases)

A three-step process for safe code evolution:

### Step 1: Patch in New Code

Use `workflow.patched()` to branch between old and new logic:

```python
@workflow.defn
class OrderWorkflow:
    @workflow.run
    async def run(self, input: OrderInput) -> str:
        if workflow.patched("add-validation-step"):
            # New code path
            await workflow.execute_activity(
                validate_order,
                input,
                start_to_close_timeout=timedelta(seconds=10),
            )

        # Existing code continues
        result = await workflow.execute_activity(
            process_order,
            input,
            start_to_close_timeout=timedelta(seconds=30),
        )
        return result
```

`workflow.patched()` inserts a marker into the Event History. During replay:
- **New executions**: Take the patched (`True`) branch
- **Pre-patch executions**: Take the else (`False`) branch
- Replaying post-patch executions: Marker found, take `True` branch

### Step 2: Deprecate the Patch

After all pre-patch workflows have completed and left the retention period:

```python
@workflow.defn
class OrderWorkflow:
    @workflow.run
    async def run(self, input: OrderInput) -> str:
        workflow.deprecate_patch("add-validation-step")

        # Only new code path remains
        await workflow.execute_activity(
            validate_order,
            input,
            start_to_close_timeout=timedelta(seconds=10),
        )

        result = await workflow.execute_activity(
            process_order,
            input,
            start_to_close_timeout=timedelta(seconds=30),
        )
        return result
```

`deprecate_patch()` bridges the transition — it still recognizes the marker in history but no longer branches.

### Step 3: Remove the Patch

Once deprecate-era workflows have also left retention, remove the patch entirely:

```python
@workflow.defn
class OrderWorkflow:
    @workflow.run
    async def run(self, input: OrderInput) -> str:
        await workflow.execute_activity(
            validate_order,
            input,
            start_to_close_timeout=timedelta(seconds=10),
        )

        result = await workflow.execute_activity(
            process_order,
            input,
            start_to_close_timeout=timedelta(seconds=30),
        )
        return result
```

### Multiple Patches

```python
@workflow.defn
class OrderWorkflow:
    @workflow.run
    async def run(self, input: OrderInput) -> str:
        if workflow.patched("add-fraud-check"):
            await workflow.execute_activity(
                check_fraud, input,
                start_to_close_timeout=timedelta(seconds=10),
            )

        if workflow.patched("use-new-payment-provider"):
            result = await workflow.execute_activity(
                charge_stripe, input,
                start_to_close_timeout=timedelta(seconds=30),
            )
        else:
            result = await workflow.execute_activity(
                charge_legacy, input,
                start_to_close_timeout=timedelta(seconds=30),
            )

        return result
```

## Worker Versioning

Tags workers with build identifiers and programmatically rolls out new versions:

```python
from temporalio.worker import Worker

worker = Worker(
    client,
    task_queue="my-queue",
    workflows=[OrderWorkflow],
    activities=[process_order],
    build_id="v2.3.1",
    use_worker_versioning=True,
)
```

With Worker Versioning:
- Old workers with build `v2.3.0` continue running old workflows
- New workers with build `v2.3.1` handle new workflow starts
- No patching needed — each build runs its own code

### When to Use Worker Versioning

- Large-scale refactors where patching would be unwieldy
- Teams that prefer clean version separation over branching
- Workflows with many simultaneous in-flight executions

## Workflow Name Versioning (Alternative)

Create new workflow types for major version changes:

```python
@workflow.defn(name="OrderWorkflow")
class OrderWorkflowV1:
    @workflow.run
    async def run(self, input: OrderInput) -> str:
        # Original logic
        ...

@workflow.defn(name="OrderWorkflowV2")
class OrderWorkflowV2:
    @workflow.run
    async def run(self, input: OrderInputV2) -> str:
        # New logic with different structure
        ...

# Register both
worker = Worker(
    client,
    task_queue="orders",
    workflows=[OrderWorkflowV1, OrderWorkflowV2],
    activities=[...],
)
```

Trade-offs:
- Pros: Clean separation, no patching complexity
- Cons: Code duplication, caller must know which version to start

## Replay Testing for Version Safety

Always test patches with replay before deploying:

```python
from temporalio.worker import Replayer, WorkflowHistory

@pytest.mark.asyncio
async def test_patch_replay_safety():
    replayer = Replayer(workflows=[OrderWorkflow])

    # Replay against pre-patch histories
    with open("tests/histories/order-pre-patch.json") as f:
        history = WorkflowHistory.from_json("order-1", f.read())

    # This should NOT raise NonDeterminismError
    await replayer.replay_workflow(history)
```

### Capturing Histories

```bash
temporal workflow show \
    --workflow-id order-123 \
    --output json \
    > tests/histories/order-pre-patch.json
```

## Safe Deployment Checklist

1. **Identify the change type**: Is it deterministic (safe) or non-deterministic (needs patching)?
2. **Deterministic changes** (safe to deploy directly):
   - Changing activity implementation (not which activities are called)
   - Modifying activity timeout values
   - Adding new signal/query/update handlers
   - Changing non-workflow code
3. **Non-deterministic changes** (need patching):
   - Adding/removing/reordering activity calls
   - Changing sleep durations
   - Adding/removing child workflows
   - Changing workflow logic branches
4. **Patch the change** using the three-step process
5. **Run replay tests** against production histories
6. **Deploy** with monitoring for `NonDeterminismError`
7. **Deprecate patches** after all old executions complete
8. **Clean up** by removing deprecated patches

## TypeScript Versioning

```typescript
import { patched, deprecatePatch } from '@temporalio/workflow';

export async function orderWorkflow(input: OrderInput): Promise<string> {
  if (patched('add-validation')) {
    await validateOrder(input);
  }

  const result = await processOrder(input);
  return result;
}

// After all pre-patch workflows complete:
export async function orderWorkflow(input: OrderInput): Promise<string> {
  deprecatePatch('add-validation');
  await validateOrder(input);
  const result = await processOrder(input);
  return result;
}
```

## Common Pitfalls

1. **Skipping deprecation**: Jumping from patched to clean code breaks replay for workflows started during the patched period.

2. **Removing patches too early**: Always wait until all affected workflows have completed AND left the retention period.

3. **Forgetting replay tests**: Deploy patches without testing against production histories and risk `NonDeterminismError` in production.

4. **Changing non-deterministic operations without patches**: Reordering activities, changing sleep durations, or modifying conditional branches without `patched()` breaks all running workflows.
