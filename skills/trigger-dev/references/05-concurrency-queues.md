# Concurrency & Queues

> Source: https://trigger.dev/docs/queue-concurrency — v4.4.3

## Contents

- [How Queues Work](#how-queues-work)
- [Environment Concurrency](#environment-concurrency)
- [Task-Level Concurrency](#task-level-concurrency)
- [Shared Queues](#shared-queues)
- [Per-Tenant Queuing](#per-tenant-queuing)
- [Queue Override at Trigger Time](#queue-override-at-trigger-time)
- [Queue Management API](#queue-management-api)
- [Checkpointing and Waitpoints](#checkpointing-and-waitpoints)
- [Common Patterns](#common-patterns)

## How Queues Work

When you trigger a task, the run is placed into a queue. By default, each task has its own queue. Queues are FIFO (first in, first out) and process runs based on concurrency limits.

**Key rule:** Only actively executing runs count towards concurrency. Runs that are delayed, waiting, or queued do NOT consume concurrency slots.

## Environment Concurrency

Each environment has two limits:

- **Base concurrency** — The standard limit (e.g., 10)
- **Burst concurrency** — Temporary overage, typically 2x base (e.g., 20)

```
Environment (base: 10, burst: 20)
├── Queue A: max 10 concurrent (capped at base)
├── Queue B: max 10 concurrent (capped at base)
└── Total across all queues: up to 20 (burst)
```

Individual queues are always capped at the base limit, not the burst. Burst capacity is shared across all queues in the environment.

## Task-Level Concurrency

Set concurrency limits directly on tasks:

```typescript
import { task } from "@trigger.dev/sdk/v3";

// Only one run at a time
export const sequentialTask = task({
  id: "sequential-task",
  queue: {
    concurrencyLimit: 1,
  },
  run: async (payload) => {
    await processSequentially(payload);
  },
});

// Up to 5 concurrent runs
export const parallelTask = task({
  id: "parallel-task",
  queue: {
    concurrencyLimit: 5,
  },
  run: async (payload) => {
    await processInParallel(payload);
  },
});
```

## Shared Queues

Define a queue and share it across multiple tasks:

```typescript
import { task, queue } from "@trigger.dev/sdk/v3";

// Define a shared queue
export const apiQueue = queue({
  name: "external-api",
  concurrencyLimit: 3, // Max 3 concurrent API calls total
});

// Both tasks share the same concurrency limit
export const fetchUsers = task({
  id: "fetch-users",
  queue: apiQueue,
  run: async (payload) => {
    return await callExternalAPI("/users");
  },
});

export const fetchOrders = task({
  id: "fetch-orders",
  queue: apiQueue,
  run: async (payload) => {
    return await callExternalAPI("/orders");
  },
});
```

**In v4:** Shared queues must be defined in your code before deployment. They cannot be created dynamically at trigger time.

## Per-Tenant Queuing

Use `concurrencyKey` to create isolated queue instances per user, team, or any entity:

```typescript
// Each user gets their own concurrency limit
await generateReport.trigger(
  { userId: "user_123", type: "monthly" },
  {
    queue: "reports",
    concurrencyKey: "user_123", // Separate queue for this user
  }
);

await generateReport.trigger(
  { userId: "user_456", type: "monthly" },
  {
    queue: "reports",
    concurrencyKey: "user_456", // Different queue, different user
  }
);
```

**Result:** `user_123` and `user_456` each have their own concurrency limit within the "reports" queue. One user's heavy usage doesn't block another.

### Free vs Paid Tier Pattern

```typescript
export const generatePR = task({
  id: "generate-pr",
  run: async (payload) => {
    // Task logic
  },
});

// Free users: 1 concurrent, shared per-user
await generatePR.trigger(data, {
  queue: { name: "free-users", concurrencyLimit: 1 },
  concurrencyKey: data.userId,
});

// Paid users: 5 concurrent, shared per-user
await generatePR.trigger(data, {
  queue: { name: "paid-users", concurrencyLimit: 5 },
  concurrencyKey: data.userId,
});
```

## Queue Override at Trigger Time

Override the default queue when triggering:

```typescript
// Use a specific named queue
await myTask.trigger(data, {
  queue: "priority-queue",
});

// Override with concurrency limit
await myTask.trigger(data, {
  queue: {
    name: "custom-queue",
    concurrencyLimit: 10,
  },
});
```

## Queue Management API

Programmatically manage queues:

```typescript
import { queues } from "@trigger.dev/sdk/v3";

// List all queues
const list = await queues.list({ page: 1, perPage: 20 });
for (const q of list.data) {
  console.log(`${q.name}: ${q.concurrencyLimit} limit`);
}

// Retrieve a specific queue
const q = await queues.retrieve("queue_xxxx");
// Or by type and name
const q2 = await queues.retrieve({ type: "task", name: "my-task" });

// Pause a queue (stops processing new runs)
await queues.pause("queue_xxxx");

// Resume a paused queue
await queues.resume("queue_xxxx");

// Override concurrency limit temporarily
await queues.overrideConcurrencyLimit("queue_xxxx", 20);

// Reset to original limit
await queues.resetConcurrencyLimit("queue_xxxx");
```

## Checkpointing and Waitpoints

When a task hits a waitpoint (`triggerAndWait`, `wait.for`, `wait.forToken`, etc.), it **checkpoints** and transitions to `WAITING` state:

- The run **releases its concurrency slot**
- The worker resources are freed
- Compute charges pause (on Trigger.dev Cloud)
- When the wait completes, the run re-enters the queue

**This prevents deadlocks:** A parent task waiting for child tasks doesn't consume a concurrency slot, allowing the children to execute even with a concurrency limit of 1.

```typescript
export const parentTask = task({
  id: "parent",
  queue: { concurrencyLimit: 1 },
  run: async (payload) => {
    // Checkpoints here — releases concurrency slot
    const result = await childTask.triggerAndWait({ data: "test" });
    // Resumes after child completes
    return result;
  },
});
```

## Common Patterns

### Rate-Limited API Integration

```typescript
const stripeQueue = queue({
  name: "stripe-api",
  concurrencyLimit: 5, // Respect Stripe's rate limits
});

export const createSubscription = task({
  id: "create-subscription",
  queue: stripeQueue,
  run: async (payload) => {
    return await stripe.subscriptions.create(payload);
  },
});

export const cancelSubscription = task({
  id: "cancel-subscription",
  queue: stripeQueue,
  run: async (payload) => {
    return await stripe.subscriptions.cancel(payload.subscriptionId);
  },
});
```

### Priority Queue Pattern

```typescript
// Trigger with priority (higher number = processed sooner)
await processOrder.trigger(
  { orderId: "order_123" },
  { priority: 10 } // High priority
);

await processOrder.trigger(
  { orderId: "order_456" },
  { priority: 1 } // Low priority
);
```

## Related Topics

- Writing tasks → `01-writing-tasks.md`
- Triggering tasks → `02-triggering-tasks.md`
- Error handling → `06-error-handling-retries.md`
