# Temporal — Nexus (Cross-Namespace Communication)

> Source: [docs.temporal.io/develop/python/nexus](https://docs.temporal.io/develop/python/nexus/quickstart) | GA for Python SDK

## What Is Temporal Nexus?

Nexus connects Temporal applications across namespace boundaries using three primitives:
- **Nexus Endpoint**: A named routing target within the Temporal Service
- **Nexus Service**: A contract defining available operations (like a gRPC service definition)
- **Nexus Operation**: An individual callable operation within a service

This enables teams to expose workflow capabilities as typed APIs without sharing code or task queues.

## Architecture

```
┌──────────────────┐                      ┌──────────────────┐
│  Namespace A     │                      │  Namespace B     │
│                  │     Nexus Endpoint    │                  │
│  CallerWorkflow  │─────────────────────>│  HandlerWorkflow │
│  (nexus_client)  │                      │  (service_handler)│
│                  │                      │                  │
│  Task Queue: tq-a│                      │  Task Queue: tq-b│
└──────────────────┘                      └──────────────────┘
```

## Defining a Nexus Service

A service contract defines typed operations:

```python
from dataclasses import dataclass
import nexusrpc

@dataclass
class GreetingInput:
    name: str
    language: str = "en"

@dataclass
class GreetingOutput:
    message: str
    translated: bool

@nexusrpc.service
class GreetingService:
    greet: nexusrpc.Operation[GreetingInput, GreetingOutput]
    translate: nexusrpc.Operation[GreetingInput, str]
```

The service is a pure contract — no implementation logic. Both caller and handler import this definition for type safety.

## Implementing Operation Handlers

### Workflow-Run Operations

The most common pattern — operations that start a workflow:

```python
from temporalio import nexus, workflow
import uuid

@workflow.defn
class GreetingWorkflow:
    @workflow.run
    async def run(self, input: GreetingInput) -> GreetingOutput:
        greeting = await workflow.execute_activity(
            generate_greeting,
            input,
            start_to_close_timeout=timedelta(seconds=10),
        )
        return GreetingOutput(message=greeting, translated=input.language != "en")

@nexus.handler.service_handler(service=GreetingService)
class GreetingServiceHandler:
    @nexus.workflow_run_operation
    async def greet(
        self, ctx: nexus.WorkflowRunOperationContext, input: GreetingInput
    ) -> nexus.WorkflowHandle[GreetingOutput]:
        return await ctx.start_workflow(
            GreetingWorkflow.run,
            input,
            id=f"greeting-{uuid.uuid4()}",
        )

    @nexus.workflow_run_operation
    async def translate(
        self, ctx: nexus.WorkflowRunOperationContext, input: GreetingInput
    ) -> nexus.WorkflowHandle[str]:
        return await ctx.start_workflow(
            TranslationWorkflow.run,
            input,
            id=f"translate-{uuid.uuid4()}",
        )
```

### Synchronous Operations

For lightweight operations that don't need a full workflow:

```python
@nexus.handler.service_handler(service=GreetingService)
class GreetingServiceHandler:
    @nexus.handler.sync_operation
    async def greet(
        self, ctx: nexus.handler.StartOperationContext, input: GreetingInput
    ) -> GreetingOutput:
        return GreetingOutput(
            message=f"Hello, {input.name}!",
            translated=False,
        )
```

## Registering Handlers with Workers

```python
from temporalio.worker import Worker

worker = Worker(
    client,
    task_queue="greeting-service-queue",
    workflows=[GreetingWorkflow, TranslationWorkflow],
    activities=[generate_greeting],
    nexus_service_handlers=[GreetingServiceHandler()],
)
await worker.run()
```

## Creating Nexus Endpoints

### Via Temporal CLI

```bash
temporal operator nexus endpoint create \
    --name greeting-endpoint \
    --target-namespace default \
    --target-task-queue greeting-service-queue
```

### Via Temporal Cloud UI

Navigate to Nexus > Endpoints > Create Endpoint, then configure the target namespace and task queue.

### Endpoint Attributes

| Attribute | Description |
|-----------|-------------|
| `name` | Unique endpoint identifier (used by callers) |
| `target-namespace` | Namespace where the handler worker runs |
| `target-task-queue` | Task queue the handler worker polls |

## Calling Nexus Operations from Workflows

### Create a Nexus Client

```python
NEXUS_ENDPOINT = "greeting-endpoint"

@workflow.defn
class CallerWorkflow:
    @workflow.run
    async def run(self, name: str) -> str:
        nexus_client = workflow.create_nexus_client(
            service=GreetingService,
            endpoint=NEXUS_ENDPOINT,
        )

        # Execute operation and wait for result
        result = await nexus_client.execute_operation(
            GreetingService.greet,
            GreetingInput(name=name, language="es"),
            schedule_to_close_timeout=timedelta(seconds=30),
        )

        return result.message
```

### Start Without Waiting

```python
@workflow.defn
class CallerWorkflow:
    @workflow.run
    async def run(self, name: str) -> str:
        nexus_client = workflow.create_nexus_client(
            service=GreetingService,
            endpoint=NEXUS_ENDPOINT,
        )

        # Start operation without waiting
        handle = await nexus_client.start_operation(
            GreetingService.translate,
            GreetingInput(name=name, language="zh"),
            schedule_to_close_timeout=timedelta(minutes=5),
        )

        # Do other work...

        # Get result later
        result = await handle.result()
        return result
```

## Cross-Namespace Use Cases

### Team A exposes a service, Team B consumes it

```
Team A (Payments Namespace)              Team B (Orders Namespace)
┌─────────────────────────┐              ┌─────────────────────────┐
│ PaymentServiceHandler   │              │ OrderWorkflow           │
│  - charge()             │<─── Nexus ───│  nexus_client.execute(  │
│  - refund()             │   Endpoint   │    PaymentService.charge│
│  - get_status()         │              │  )                      │
└─────────────────────────┘              └─────────────────────────┘
```

### Service Discovery Pattern

```python
# Shared contract (published as a package)
# payment_contracts/service.py
@nexusrpc.service
class PaymentService:
    charge: nexusrpc.Operation[ChargeInput, ChargeOutput]
    refund: nexusrpc.Operation[RefundInput, RefundOutput]
    get_status: nexusrpc.Operation[StatusInput, StatusOutput]
```

Both teams import the contract package, ensuring type safety across namespace boundaries.

## Configuration Options

### Operation Timeouts

```python
result = await nexus_client.execute_operation(
    GreetingService.greet,
    input,
    schedule_to_close_timeout=timedelta(seconds=30),  # Total time
)
```

### Nexus Client in Workflows

```python
nexus_client = workflow.create_nexus_client(
    service=GreetingService,
    endpoint="greeting-endpoint",
)
```

## Testing Nexus Services

```python
@pytest.mark.asyncio
async def test_nexus_greeting(workflow_env):
    caller_queue = "test-caller"
    handler_queue = "test-handler"

    # Create endpoint for testing
    # (In tests, often both caller and handler are in the same namespace)

    async with Worker(
        workflow_env.client,
        task_queue=handler_queue,
        workflows=[GreetingWorkflow],
        activities=[generate_greeting],
        nexus_service_handlers=[GreetingServiceHandler()],
    ), Worker(
        workflow_env.client,
        task_queue=caller_queue,
        workflows=[CallerWorkflow],
    ):
        result = await workflow_env.client.execute_workflow(
            CallerWorkflow.run,
            "World",
            id="test-caller-1",
            task_queue=caller_queue,
        )
        assert "Hello" in result
```

## When to Use Nexus vs Direct Calls

| Scenario | Use |
|----------|-----|
| Same team, same namespace | Direct child workflows or activities |
| Different teams, same namespace | Consider Nexus for contract enforcement |
| Different namespaces | Nexus (required for cross-namespace) |
| Different Temporal clusters | External API calls (Nexus is intra-cluster) |

## Common Pitfalls

1. **Endpoint name mismatch**: The `endpoint` parameter in `create_nexus_client` must exactly match the endpoint name created via CLI/UI.

2. **Missing task queue**: The endpoint's target task queue must match the task queue the handler worker polls.

3. **Circular dependencies**: Avoid Namespace A calling Namespace B which calls back to Namespace A — this can create deadlocks.

4. **Large payloads**: Nexus operations have the same 2 MB / 4 MB payload limits as regular activities.
