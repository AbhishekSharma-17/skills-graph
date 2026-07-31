# BullMQ — Overview & Getting Started

> Source: [docs.bullmq.io](https://docs.bullmq.io/) · Version: 6.0.x · License: MIT

## What is BullMQ?

BullMQ is a Node.js-based queue management system built on Redis. It provides a robust framework for handling asynchronous job processing across distributed systems, enabling developers to decouple task execution from request handling to improve scalability and reliability.

BullMQ is the successor to Bull, rewritten from scratch in TypeScript with a modern architecture and additional features like parent-child flows, job schedulers, and OpenTelemetry integration.

### When to Use BullMQ

- Background job processing (emails, image processing, report generation)
- Distributed task queues across multiple servers
- Rate-limited API calls and webhook delivery
- Scheduled/recurring jobs (cron-like)
- Complex multi-step workflows with parent-child dependencies
- Priority-based job processing
- Reliable message passing between microservices

### BullMQ vs Alternatives

| Feature | BullMQ | Trigger.dev | Inngest |
|---------|--------|-------------|---------|
| Hosting | Self-hosted (Redis) | Cloud / Self-hosted | Cloud / Self-hosted |
| Backend | Redis | PostgreSQL | Cloud |
| Languages | Node, Python, Rust, Elixir, PHP | TypeScript | TypeScript |
| Flows/DAGs | Built-in FlowProducer | Via SDK | Via step functions |
| Rate Limiting | Built-in | Via config | Built-in |
| Best For | High-throughput self-hosted queues | Serverless background jobs | Event-driven workflows |

## Core Architecture

BullMQ centers around four primary classes:

### Queue
Manages job storage and basic operations — adding jobs, pausing, cleaning, and data retrieval.

### Worker
Processes jobs from the queue. Workers are independent instances capable of consuming jobs, executing them, and marking them as completed or failed. Multiple workers can operate simultaneously across different processes and machines.

### QueueEvents
Monitors queue activity and job lifecycle events via Redis streams, providing real-time visibility with delivery guarantees.

### FlowProducer
Orchestrates complex job workflows with parent-child dependencies between multiple jobs.

## Job Lifecycle

Jobs progress through distinct states:

```
┌──────────┐    ┌──────────────┐    ┌────────┐    ┌───────────┐
│  Added    │───>│  wait /      │───>│ active │───>│ completed │
│          │    │  prioritized │    │        │    └───────────┘
└──────────┘    │  / delayed   │    │        │    ┌────────┐
                └──────────────┘    │        │───>│ failed │
                       ^            └────────┘    └────────┘
                       │                │              │
                       └────────────────┘              │
                        (retry if attempts remain)     │
                       ^                               │
                       └───────────────────────────────┘
                        (retry with backoff)
```

**States:**
- **wait** — Default initial state, job is in the queue waiting for a worker
- **prioritized** — Waiting but ordered by priority value
- **delayed** — Waiting for a delay/schedule to expire before moving to wait
- **active** — Currently being processed by a worker
- **completed** — Successfully processed
- **failed** — Processing threw an error (may be retried)
- **waiting-children** — Parent job waiting for all child jobs to complete (flows)

## Installation

```bash
# Node.js
npm install bullmq

# Bun
bun add bullmq

# Python
pip install bullmq

# Requires Redis 6.2+
# Docker quickstart:
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

## Quick Start

### Minimal Queue + Worker

```typescript
import { Queue, Worker } from 'bullmq';

// 1. Create a queue
const queue = new Queue('my-tasks');

// 2. Add a job
await queue.add('send-email', {
  to: 'user@example.com',
  subject: 'Welcome!',
  body: 'Thanks for signing up.',
});

// 3. Create a worker to process jobs
const worker = new Worker('my-tasks', async (job) => {
  console.log(`Processing ${job.name} with data:`, job.data);
  await sendEmail(job.data);
  return { sent: true };
});

// 4. Listen for completion
worker.on('completed', (job, result) => {
  console.log(`Job ${job.id} completed with result:`, result);
});

worker.on('failed', (job, err) => {
  console.error(`Job ${job?.id} failed:`, err.message);
});
```

### Python Quick Start

```python
from bullmq import Queue, Worker

queue = Queue("my-tasks")

async def process(job, token):
    print(f"Processing {job.name}: {job.data}")
    # Do work...
    return {"done": True}

worker = Worker("my-tasks", process)
```

## Redis Requirements

- **Minimum version:** Redis 6.2+
- **Memory policy:** Must set `maxmemory-policy=noeviction`
- **Persistence:** Enable AOF with ~1s write intervals for durability
- **Compatible backends:** Redis, Dragonfly, AWS MemoryDB, AWS ElastiCache, Upstash

```redis
# Required Redis config
CONFIG SET maxmemory-policy noeviction
```

## Key Design Principles

1. **At-least-once delivery** — Jobs are guaranteed to be processed at least once via lock-based claiming
2. **Distributed by design** — Multiple workers across multiple machines, no single point of failure
3. **Atomic operations** — All state transitions use Lua scripts for atomicity
4. **Horizontal scaling** — Add more workers to increase throughput
5. **Back-pressure** — Rate limiting and concurrency controls prevent overload

## Related Topics

- [Queues](./01-queues.md) — Creating and managing queues
- [Workers](./02-workers.md) — Processing jobs with concurrency
- [Flows](./07-flows.md) — Parent-child job dependencies
- [Production](./12-production-nestjs.md) — Going to production
