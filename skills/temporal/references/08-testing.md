# Temporal — Testing

> Source: [docs.temporal.io/develop/python/testing-suite](https://docs.temporal.io/develop/python/testing-suite)

## Table of Contents

- [Testing Approaches](#testing-approaches)
- [Testing Activities](#testing-activities)
- [Testing Workflows](#testing-workflows)
- [Time-Skipping](#time-skipping)
- [Mocking Activities](#mocking-activities)
- [Replay Testing](#replay-testing)
- [Integration Testing](#integration-testing)
- [TypeScript Testing](#typescript-testing)
- [Best Practices](#best-practices)

## Testing Approaches

Temporal supports three testing levels:

| Level | What It Tests | Speed | Fidelity |
|-------|--------------|-------|----------|
| **Unit** | Individual functions, mocked dependencies | Fast | Low |
| **Integration** | Workflows with mocked activities, or activities with mocked contexts | Medium | Medium |
| **End-to-end** | Full stack with real Temporal server | Slow | High |

Temporal recommends writing the majority of tests as **integration tests**.

## Testing Activities

### Using ActivityEnvironment

Run activities in isolation without creating a Worker:

```python
import pytest
from temporalio.testing import ActivityEnvironment

@pytest.fixture
def activity_env():
    return ActivityEnvironment()

@pytest.mark.asyncio
async def test_greet_activity(activity_env):
    result = await activity_env.run(greet, "World")
    assert result == "Hello, World!"
```

### Testing Activity Heartbeats

Capture heartbeats using the `on_heartbeat` callback:

```python
@pytest.mark.asyncio
async def test_activity_heartbeats(activity_env):
    heartbeats = []
    activity_env.on_heartbeat = lambda *args: heartbeats.append(args[0])

    await activity_env.run(process_large_file, "test.csv")

    assert len(heartbeats) > 0
    assert heartbeats[-1] > 0  # Last heartbeat reports progress
```

### Testing Activity Info Access

```python
@pytest.mark.asyncio
async def test_activity_with_info(activity_env):
    activity_env.info.workflow_id = "test-workflow-123"
    activity_env.info.activity_id = "test-activity-1"
    activity_env.info.attempt = 1

    result = await activity_env.run(activity_using_info, "input")
    assert result is not None
```

### Testing Activities with External Dependencies

```python
@pytest.mark.asyncio
async def test_payment_activity(activity_env, mocker):
    mock_gateway = mocker.patch("myapp.activities.payment_gateway")
    mock_gateway.charge.return_value = PaymentResult(transaction_id="tx-123")

    result = await activity_env.run(
        process_payment,
        PaymentInput(order_id="order-1", amount=99.99, currency="USD"),
    )

    assert result == "tx-123"
    mock_gateway.charge.assert_called_once()
```

## Testing Workflows

### With Real Temporal Server (Time-Skipping)

```python
import pytest
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

@pytest.fixture
async def workflow_env():
    async with await WorkflowEnvironment.start_time_skipping() as env:
        yield env

@pytest.mark.asyncio
async def test_greeting_workflow(workflow_env):
    task_queue = "test-queue"

    async with Worker(
        workflow_env.client,
        task_queue=task_queue,
        workflows=[GreetingWorkflow],
        activities=[greet],
    ):
        result = await workflow_env.client.execute_workflow(
            GreetingWorkflow.run,
            "World",
            id="test-greeting-1",
            task_queue=task_queue,
        )
        assert result == "Hello, World!"
```

### Testing Signals and Queries

```python
@pytest.mark.asyncio
async def test_shopping_cart_workflow(workflow_env):
    task_queue = "test-cart"

    async with Worker(
        workflow_env.client,
        task_queue=task_queue,
        workflows=[ShoppingCartWorkflow],
        activities=[process_order],
    ):
        handle = await workflow_env.client.start_workflow(
            ShoppingCartWorkflow.run,
            id="test-cart-1",
            task_queue=task_queue,
        )

        # Send signals
        await handle.signal(ShoppingCartWorkflow.add_item, "item-a")
        await handle.signal(ShoppingCartWorkflow.add_item, "item-b")

        # Query state
        items = await handle.query(ShoppingCartWorkflow.get_items)
        assert items == ["item-a", "item-b"]

        # Signal checkout
        await handle.signal(ShoppingCartWorkflow.checkout)

        # Wait for completion
        result = await handle.result()
        assert result == ["item-a", "item-b"]
```

### Testing Updates

```python
@pytest.mark.asyncio
async def test_workflow_update(workflow_env):
    task_queue = "test-update"

    async with Worker(
        workflow_env.client,
        task_queue=task_queue,
        workflows=[GreetingWorkflow],
        activities=[fetch_translation],
    ):
        handle = await workflow_env.client.start_workflow(
            GreetingWorkflow.run,
            id="test-update-1",
            task_queue=task_queue,
        )

        # Execute update
        previous = await handle.execute_update(
            GreetingWorkflow.set_language,
            Language.SPANISH,
        )
        assert previous == Language.ENGLISH

        # Test validator rejection
        with pytest.raises(Exception):
            await handle.execute_update(
                GreetingWorkflow.set_language,
                Language.KLINGON,
            )
```

## Time-Skipping

### Automatic Time-Skipping

The test server automatically fast-forwards timers and sleeps:

```python
@pytest.mark.asyncio
async def test_reminder_workflow(workflow_env):
    task_queue = "test-reminder"

    async with Worker(
        workflow_env.client,
        task_queue=task_queue,
        workflows=[ReminderWorkflow],
        activities=[send_reminder],
    ):
        # This workflow has a 24-hour sleep, but completes instantly in tests
        result = await workflow_env.client.execute_workflow(
            ReminderWorkflow.run,
            id="test-reminder-1",
            task_queue=task_queue,
        )
        assert result == "reminder_sent"
```

### Manual Time-Skipping

Advance time explicitly:

```python
@pytest.mark.asyncio
async def test_timeout_behavior(workflow_env):
    task_queue = "test-timeout"

    async with Worker(
        workflow_env.client,
        task_queue=task_queue,
        workflows=[TimeoutWorkflow],
        activities=[long_task],
    ):
        handle = await workflow_env.client.start_workflow(
            TimeoutWorkflow.run,
            id="test-timeout-1",
            task_queue=task_queue,
        )

        # Manually advance time
        await workflow_env.sleep(3)

        result = await handle.result()
        assert result == "timed_out"
```

## Mocking Activities

Provide mock activity implementations with matching names:

```python
@activity.defn(name="process_payment")
async def mock_process_payment(input: PaymentInput) -> str:
    return "mock-transaction-123"

@activity.defn(name="send_notification")
async def mock_send_notification(input: NotificationInput) -> bool:
    return True

@pytest.mark.asyncio
async def test_order_workflow_with_mocks(workflow_env):
    task_queue = "test-order"

    async with Worker(
        workflow_env.client,
        task_queue=task_queue,
        workflows=[OrderWorkflow],
        activities=[mock_process_payment, mock_send_notification],
    ):
        result = await workflow_env.client.execute_workflow(
            OrderWorkflow.run,
            OrderInput(order_id="test-1"),
            id="test-order-1",
            task_queue=task_queue,
        )
        assert result == "order_completed"
```

## Replay Testing

Verify that workflow code changes don't break determinism against existing Event Histories:

```python
from temporalio.worker import Replayer, WorkflowHistory

@pytest.mark.asyncio
async def test_workflow_replay():
    replayer = Replayer(workflows=[OrderWorkflow])

    # Replay from JSON file
    with open("tests/histories/order-workflow.json") as f:
        history = WorkflowHistory.from_json("order-1", f.read())

    await replayer.replay_workflow(history)
```

### Replay Multiple Histories

```python
@pytest.mark.asyncio
async def test_replay_all_histories():
    replayer = Replayer(workflows=[OrderWorkflow, ShippingWorkflow])

    # Replay from live Temporal service
    async for workflow in client.list_workflows('TaskQueue="production"'):
        histories = client.list_workflows('TaskQueue="production"').map_histories()
        await replayer.replay_workflows(histories)
```

### Capturing Histories for Replay Tests

```bash
# Export workflow history via CLI
temporal workflow show --workflow-id order-123 --output json > tests/histories/order-workflow.json
```

Include replay testing in CI/CD to catch non-deterministic changes before deployment.

## Integration Testing

### Full End-to-End with Local Server

```python
@pytest.fixture(scope="session")
async def temporal_env():
    async with await WorkflowEnvironment.start_local() as env:
        yield env

@pytest.mark.asyncio
async def test_full_order_flow(temporal_env):
    task_queue = "integration-test"

    async with Worker(
        temporal_env.client,
        task_queue=task_queue,
        workflows=[OrderWorkflow],
        activities=[process_payment, update_inventory, send_notification],
    ):
        result = await temporal_env.client.execute_workflow(
            OrderWorkflow.run,
            OrderInput(order_id="int-test-1", items=["product-a"]),
            id="int-test-order-1",
            task_queue=task_queue,
        )
        assert result == "order_completed"
```

## TypeScript Testing

```typescript
import { TestWorkflowEnvironment } from '@temporalio/testing';
import { Worker } from '@temporalio/worker';

describe('OrderWorkflow', () => {
  let testEnv: TestWorkflowEnvironment;

  beforeAll(async () => {
    testEnv = await TestWorkflowEnvironment.createTimeSkipping();
  });

  afterAll(async () => {
    await testEnv?.teardown();
  });

  it('completes order successfully', async () => {
    const { client, nativeConnection } = testEnv;
    const taskQueue = 'test-order';

    const worker = await Worker.create({
      connection: nativeConnection,
      taskQueue,
      workflowsPath: require.resolve('./workflows'),
      activities: {
        processPayment: async () => 'tx-123',
        sendNotification: async () => true,
      },
    });

    const result = await worker.runUntil(
      client.workflow.execute('orderWorkflow', {
        args: [{ orderId: 'test-1' }],
        taskQueue,
        workflowId: 'test-order-1',
      })
    );

    expect(result).toBe('order_completed');
  });
});
```

## Best Practices

1. **Use time-skipping** for workflows with timers or sleeps — never use real delays in tests
2. **Mock at the activity boundary** — mock activity implementations, not internal workflow logic
3. **Run replay tests in CI** — catch non-deterministic changes before they break production
4. **Test signals/queries separately** — verify message handlers independently from main workflow logic
5. **Use unique task queues per test** to avoid interference between parallel tests
6. **Use unique workflow IDs per test** to prevent `WorkflowAlreadyStartedError`
