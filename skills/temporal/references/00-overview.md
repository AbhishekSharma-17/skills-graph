# Temporal — Overview

> Source: [docs.temporal.io](https://docs.temporal.io) | Python SDK 1.28.0 | TypeScript SDK

## What Is Temporal?

Temporal is a durable execution platform that enables developers to build fault-tolerant, long-running applications. It separates business logic (workflows) from infrastructure concerns (retries, timeouts, state persistence), letting code run as if failures don't exist while the platform handles recovery transparently.

Key value proposition: write simple, linear code that survives process crashes, network failures, and infrastructure outages without manual checkpointing or state management.

## Core Concepts

### Durable Execution

The ability of a process to resume execution after suspending — whether due to an await, a crash, or a deployment. Temporal records every step in an **Event History**, enabling automatic replay to reconstruct state and continue from the exact point of interruption.

### Workflow Execution Lifecycle

1. Client initiates workflow → Temporal Service creates `WorkflowExecutionStarted` event
2. Service schedules Workflow Task → Worker picks up and executes code
3. Workflow calls Activity → Worker sends `ScheduleActivityTask` Command
4. Service queues Activity Task → Worker executes activity (with automatic retries)
5. Activity completes → Service creates new Workflow Task
6. Worker replays workflow using Event History, continues execution
7. Workflow completes → Client retrieves results

### Event History

Every workflow step is appended as an event to a persistent log. This log enables:
- Automatic state reconstruction after failures
- Full auditability of execution progress
- Replay-based recovery without manual checkpointing

### Deterministic Constraints

Workflow code must be **deterministic** — producing identical results given the same inputs — because replays depend on consistent execution paths. Non-deterministic operations (I/O, randomness, time) must occur in Activities, not Workflows.

### Task Queues

Workers poll Task Queues for assignments rather than receiving direct task dispatch. This decoupled architecture enables horizontal scaling and fault tolerance — tasks persist until workers become available.

### Namespaces

Logical isolation boundaries for workflows, providing multi-tenancy, separate retention policies, and security boundaries.

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│   Client     │────>│  Temporal Service │<────│   Worker    │
│  (SDK)       │     │  (Server/Cloud)   │     │  (Your Code)│
└─────────────┘     └──────────────────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    │ Event History│
                    │ (Persistence)│
                    └─────────────┘
```

- **Client**: Starts workflows, sends signals/queries, retrieves results
- **Temporal Service**: Manages state, task queues, event histories, timers
- **Worker**: Executes workflow and activity code, polls task queues

## Available SDKs

| Language | Package | Install |
|----------|---------|---------|
| Python | `temporalio` | `pip install temporalio` |
| TypeScript | `@temporalio/*` | `npm install @temporalio/client @temporalio/worker @temporalio/workflow @temporalio/activity` |
| Go | `go.temporal.io/sdk` | `go get go.temporal.io/sdk` |
| Java | `io.temporal:temporal-sdk` | Maven/Gradle |
| .NET | `Temporalio` | `dotnet add package Temporalio` |
| Ruby | `temporalio` | `gem install temporalio` |
| Rust | `temporalio-sdk` | Cargo |
| PHP | `temporal/sdk` | Composer |

## Installation — Python

```bash
pip install temporalio
```

Optional extras:

```bash
pip install temporalio[opentelemetry]  # Distributed tracing
pip install temporalio[pydantic]       # Pydantic data conversion
pip install temporalio[grpc]           # Custom gRPC options
```

## Installation — TypeScript

```bash
npm install @temporalio/client @temporalio/worker @temporalio/workflow @temporalio/activity
```

Scaffold a new project:

```bash
npx @temporalio/create my-app
```

## Running Temporal Locally

### Temporal CLI (Development Server)

```bash
# Install
brew install temporal
# or
curl -sSf https://temporal.download/cli.sh | sh

# Start development server
temporal server start-dev

# Access Web UI at http://localhost:8233
```

### Docker Compose

```bash
git clone https://github.com/temporalio/docker-compose.git
cd docker-compose
docker compose up
```

### Temporal Cloud

For production, use [Temporal Cloud](https://temporal.io/cloud) — a fully managed service with built-in security, scaling, and observability.

## Minimal Example — Python

```python
import asyncio
from datetime import timedelta
from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker

@activity.defn
async def greet(name: str) -> str:
    return f"Hello, {name}!"

@workflow.defn
class GreetingWorkflow:
    @workflow.run
    async def run(self, name: str) -> str:
        return await workflow.execute_activity(
            greet, name, start_to_close_timeout=timedelta(seconds=10)
        )

async def main():
    client = await Client.connect("localhost:7233")
    async with Worker(
        client,
        task_queue="greeting-queue",
        workflows=[GreetingWorkflow],
        activities=[greet],
    ):
        result = await client.execute_workflow(
            GreetingWorkflow.run,
            "World",
            id="greeting-1",
            task_queue="greeting-queue",
        )
        print(result)  # Hello, World!

asyncio.run(main())
```

## Minimal Example — TypeScript

```typescript
// activities.ts
export async function greet(name: string): Promise<string> {
  return `Hello, ${name}!`;
}

// workflows.ts
import { proxyActivities } from '@temporalio/workflow';
import type * as activities from './activities';

const { greet } = proxyActivities<typeof activities>({
  startToCloseTimeout: '10 seconds',
});

export async function greetingWorkflow(name: string): Promise<string> {
  return await greet(name);
}

// worker.ts
import { Worker } from '@temporalio/worker';
import * as activities from './activities';

const worker = await Worker.create({
  workflowsPath: require.resolve('./workflows'),
  activities,
  taskQueue: 'greeting-queue',
});
await worker.run();

// client.ts
import { Client } from '@temporalio/client';

const client = new Client();
const result = await client.workflow.execute('greetingWorkflow', {
  args: ['World'],
  taskQueue: 'greeting-queue',
  workflowId: 'greeting-1',
});
console.log(result); // Hello, World!
```

## When to Use Temporal

**Good fit:**
- Long-running business processes (order fulfillment, onboarding, provisioning)
- Multi-step transactions with compensation (saga pattern)
- Scheduled and recurring workflows
- AI agent orchestration requiring durable execution
- Microservice orchestration with complex retry logic
- Event-driven architectures needing reliable processing

**Consider alternatives when:**
- Simple request-response APIs (use standard web frameworks)
- Stateless data transformations (use serverless functions)
- Simple cron jobs without state (use system cron or cloud schedulers)
- Real-time streaming (use Kafka, Flink, or similar)

## Temporal vs Other Workflow Tools

| Feature | Temporal | Inngest | Trigger.dev |
|---------|----------|---------|-------------|
| Execution model | Durable replay | Event-driven steps | Serverless tasks |
| Language support | 8 SDKs | TypeScript/Python | TypeScript |
| Self-hosted | Yes | Yes | Yes |
| Long-running (days+) | Native | Limited | Limited |
| Saga pattern | Native | Manual | Manual |
| Workflow versioning | Built-in | N/A | N/A |
| Complexity | Higher | Lower | Lower |

## Key URLs

- Documentation: https://docs.temporal.io
- GitHub: https://github.com/temporalio/temporal
- Python SDK: https://github.com/temporalio/sdk-python
- TypeScript SDK: https://github.com/temporalio/sdk-typescript
- Samples (Python): https://github.com/temporalio/samples-python
- Samples (TypeScript): https://github.com/temporalio/samples-typescript
- Learning: https://learn.temporal.io
