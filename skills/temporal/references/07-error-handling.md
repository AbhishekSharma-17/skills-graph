# Temporal — Error Handling, Retries & Timeouts

> Source: [docs.temporal.io/develop/python/failure-detection](https://docs.temporal.io/develop/python/failure-detection) | [docs.temporal.io/develop/python/cancellation](https://docs.temporal.io/develop/python/cancellation)

## Table of Contents

- [Error Categories](#error-categories)
- [Exception Types](#exception-types)
- [Retry Policies](#retry-policies)
- [Timeout Types](#timeout-types)
- [Activity Error Handling](#activity-error-handling)
- [Workflow Error Handling](#workflow-error-handling)
- [Cancellation](#cancellation)
- [Saga Pattern](#saga-pattern)
- [TypeScript Error Handling](#typescript-error-handling)

## Error Categories

Temporal distinguishes three failure types:

| Category | Example | Handling |
|----------|---------|----------|
| **Transient** | Network hiccup, service restart | Immediate retry (automatic) |
| **Intermittent** | Rate limit, resource contention | Exponential backoff (automatic) |
| **Permanent** | Invalid input, business rule violation | No retry — fix data or code |

Two failure modes in workflows:

- **Workflow Task failure** (bugs): Any unhandled exception except `ApplicationError` causes a Workflow Task failure. This retries indefinitely, allowing you to fix the bug and redeploy without losing state.
- **Workflow Execution failure** (business logic): Raising `ApplicationError` deliberately fails the entire execution. No automatic retries.

## Exception Types

```python
from temporalio.exceptions import (
    ApplicationError,      # Business logic failure (you raise this)
    ActivityError,         # Wraps activity exceptions caught in workflows
    ChildWorkflowError,    # Child workflow execution failed
    CancelledError,        # Cancellation (from asyncio)
    TimeoutError,          # Activity or workflow exceeded timeout
    TerminatedError,       # Workflow forcefully terminated
    WorkflowAlreadyStartedError,  # Duplicate workflow ID
)
```

### ApplicationError

The primary exception you should raise manually:

```python
from temporalio.exceptions import ApplicationError

# In an activity — permanent failure, no retry
raise ApplicationError(
    "Customer lives outside service area",
    type="OutsideServiceArea",
    non_retryable=True,
)

# In an activity — categorized failure, retryable
raise ApplicationError(
    "Payment gateway timeout",
    type="PaymentTimeout",
)

# In a workflow — deliberately fail the execution
raise ApplicationError(
    "Order cannot be fulfilled",
    type="UnfulfillableOrder",
    non_retryable=True,
)
```

## Retry Policies

### Default Behavior

Activities have **unlimited retry attempts** with exponential backoff by default.

### Custom Retry Policy

```python
from temporalio.common import RetryPolicy
from datetime import timedelta

retry_policy = RetryPolicy(
    initial_interval=timedelta(seconds=1),    # Delay before first retry
    backoff_coefficient=2.0,                  # Multiplier for subsequent delays
    maximum_interval=timedelta(minutes=5),    # Cap on retry delay
    maximum_attempts=10,                      # Max retry count (0 = unlimited)
    non_retryable_error_types=[               # Error types that bypass retries
        "InvalidCardFormat",
        "InsufficientFunds",
    ],
)

await workflow.execute_activity(
    charge_payment,
    payment_input,
    start_to_close_timeout=timedelta(seconds=30),
    retry_policy=retry_policy,
)
```

### Non-Retryable Errors

**Method 1 — Activity-side marking** (when the activity knows failure is permanent):

```python
@activity.defn
async def validate_card(card_number: str) -> bool:
    if not luhn_check(card_number):
        raise ApplicationError(
            "Invalid credit card format",
            type="InvalidCardFormat",
            non_retryable=True,
        )
    return True
```

**Method 2 — Workflow-side specification** (when callers decide recoverability):

```python
retry_policy = RetryPolicy(
    non_retryable_error_types=["InvalidCardFormat", "InsufficientFunds"]
)
```

## Timeout Types

### Activity Timeouts

```python
await workflow.execute_activity(
    process_order,
    order_input,
    # Time from scheduling to completion (most commonly used)
    start_to_close_timeout=timedelta(seconds=30),

    # Time from scheduling to worker pickup (detects stuck queues)
    schedule_to_close_timeout=timedelta(minutes=5),

    # Time from worker pickup to completion
    # start_to_close_timeout is preferred over this

    # Heartbeat interval — must heartbeat within this period
    heartbeat_timeout=timedelta(seconds=10),
)
```

| Timeout | Measures | Use When |
|---------|----------|----------|
| `start_to_close_timeout` | Single attempt duration | Always set this one |
| `schedule_to_close_timeout` | Total including retries | Cap total retry time |
| `heartbeat_timeout` | Between heartbeats | Long-running activities |

### Workflow Timeouts

```python
handle = await client.start_workflow(
    OrderWorkflow.run,
    input,
    id="order-123",
    task_queue="orders",
    execution_timeout=timedelta(hours=24),  # Max total (all runs)
    run_timeout=timedelta(hours=1),         # Max single run
    task_timeout=timedelta(seconds=10),     # Max workflow task
)
```

## Activity Error Handling

### Catching Activity Errors in Workflows

```python
from temporalio.exceptions import ActivityError, ApplicationError

@workflow.defn
class OrderWorkflow:
    @workflow.run
    async def run(self, input: OrderInput) -> str:
        try:
            result = await workflow.execute_activity(
                charge_payment,
                input,
                start_to_close_timeout=timedelta(seconds=30),
            )
        except ActivityError as e:
            # e.cause contains the original exception
            if isinstance(e.cause, ApplicationError):
                if e.cause.type == "InsufficientFunds":
                    return "Payment failed: insufficient funds"
            raise ApplicationError(
                f"Payment failed: {e.cause}",
                type="PaymentError",
            )
        return result
```

### Idempotency in Activities

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

## Workflow Error Handling

### Bug vs Business Logic Failure

```python
@workflow.defn
class ProcessingWorkflow:
    @workflow.run
    async def run(self, input: ProcessInput) -> str:
        # Bug — raises non-ApplicationError, retries indefinitely
        # (fix the bug and redeploy, state is preserved)
        result = some_function_with_bug()  # TypeError, etc.

        # Business logic failure — raises ApplicationError, fails execution
        if not input.is_valid:
            raise ApplicationError(
                "Invalid input provided",
                type="ValidationError",
                non_retryable=True,
            )
```

## Cancellation

### Cancelling a Workflow

```python
await client.get_workflow_handle("wf-123").cancel()
```

### Handling Cancellation in Workflows

```python
@workflow.defn
class OrderWorkflow:
    @workflow.run
    async def run(self, input: OrderInput) -> str:
        try:
            await workflow.execute_activity(
                process_order, input,
                start_to_close_timeout=timedelta(minutes=5),
            )
            return "completed"
        except asyncio.CancelledError:
            # Cleanup on cancellation
            await workflow.execute_activity(
                rollback_order, input,
                start_to_close_timeout=timedelta(seconds=30),
            )
            raise  # Re-raise to mark workflow as cancelled
```

### Cancelling Activities

Activities must heartbeat to be cancellable:

```python
@activity.defn
async def long_running_task(input: TaskInput) -> str:
    try:
        while not done:
            do_work()
            activity.heartbeat("progress")
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        cleanup()
        raise
```

### Termination (Forceful Stop)

```python
await client.get_workflow_handle("wf-123").terminate(reason="Manual cleanup")
```

Termination gives no opportunity for cleanup. Use as a last resort.

## Saga Pattern

Implement compensating actions for multi-step transactions:

```python
@workflow.defn
class TransferWorkflow:
    @workflow.run
    async def run(self, input: TransferInput) -> str:
        compensations: list[tuple] = []

        try:
            # Step 1: Reserve funds
            compensations.append((release_reservation, input))
            await workflow.execute_activity(
                reserve_funds, input,
                start_to_close_timeout=timedelta(seconds=10),
            )

            # Step 2: Debit source account
            compensations.append((credit_source, input))
            await workflow.execute_activity(
                debit_source, input,
                start_to_close_timeout=timedelta(seconds=10),
            )

            # Step 3: Credit target account
            await workflow.execute_activity(
                credit_target, input,
                start_to_close_timeout=timedelta(seconds=10),
            )

            return "transfer_complete"

        except ActivityError:
            # Compensate in reverse order
            for comp_activity, comp_input in reversed(compensations):
                try:
                    await workflow.execute_activity(
                        comp_activity, comp_input,
                        start_to_close_timeout=timedelta(seconds=10),
                    )
                except ActivityError as comp_err:
                    workflow.logger.error(f"Compensation failed: {comp_err.cause}")

            raise ApplicationError(
                "Transfer failed, compensations executed",
                type="TransferFailed",
            )
```

## TypeScript Error Handling

```typescript
import { ApplicationFailure, ActivityFailure } from '@temporalio/common';
import { proxyActivities } from '@temporalio/workflow';

const { chargePayment } = proxyActivities<typeof activities>({
  startToCloseTimeout: '30 seconds',
  retry: {
    maximumAttempts: 5,
    nonRetryableErrorTypes: ['InvalidCardFormat'],
  },
});

export async function orderWorkflow(input: OrderInput): Promise<string> {
  try {
    return await chargePayment(input);
  } catch (err) {
    if (err instanceof ActivityFailure && err.cause instanceof ApplicationFailure) {
      if (err.cause.type === 'InsufficientFunds') {
        return 'Payment failed: insufficient funds';
      }
    }
    throw ApplicationFailure.nonRetryable('Payment processing failed');
  }
}
```

### Throwing Non-Retryable Errors (TypeScript)

```typescript
// In an activity
throw ApplicationFailure.nonRetryable('Invalid input', 'ValidationError');

// Retryable (default)
throw ApplicationFailure.retryable('Temporary failure', 'TransientError');
```
