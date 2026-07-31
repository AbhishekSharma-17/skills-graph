# BullMQ — Flows & Dependencies

> Source: [docs.bullmq.io/guide/flows](https://docs.bullmq.io/guide/flows)

## Table of Contents

- [FlowProducer Basics](#flowproducer-basics)
- [Creating Flows](#creating-flows)
- [Accessing Child Results](#accessing-child-results-in-parent)
- [Adding Flows in Bulk](#adding-flows-in-bulk)
- [Dependency Management](#dependency-management)
- [Fail Parent Behavior](#fail-parent-behavior)
- [Dynamic Flows](#dynamic-flows-process-step-pattern)

## Overview

BullMQ Flows enable parent-child job dependencies through the `FlowProducer` class. A parent job will not be processed until all its child jobs have completed successfully. This enables complex DAG-like workflows where jobs can span multiple queues.

## FlowProducer Basics

```typescript
import { FlowProducer } from 'bullmq';

const flowProducer = new FlowProducer({
  connection: { host: 'localhost', port: 6379 },
});
```

## Creating Flows

### Parallel Children (Fan-Out)

All children process in parallel; parent waits for all to complete:

```typescript
const flow = await flowProducer.add({
  name: 'renovate-interior',
  queueName: 'renovate',
  data: { budget: 10000 },
  children: [
    { name: 'paint', data: { place: 'ceiling' }, queueName: 'steps' },
    { name: 'paint', data: { place: 'walls' }, queueName: 'steps' },
    { name: 'fix',   data: { place: 'floor' },  queueName: 'steps' },
  ],
});
```

Execution: `paint(ceiling)`, `paint(walls)`, and `fix(floor)` run in parallel. When all three complete, `renovate-interior` becomes processable.

### Sequential Chain (Pipeline)

Nest children to create serial execution:

```typescript
const chain = await flowProducer.add({
  name: 'car',
  data: { step: 'engine' },
  queueName: 'assembly-line',
  children: [
    {
      name: 'car',
      data: { step: 'wheels' },
      queueName: 'assembly-line',
      children: [
        {
          name: 'car',
          data: { step: 'chassis' },
          queueName: 'assembly-line',
        },
      ],
    },
  ],
});
```

Execution order: `chassis` → `wheels` → `engine` (deepest-first).

### Mixed Parallel and Sequential

```typescript
await flowProducer.add({
  name: 'deploy',
  queueName: 'deploy',
  children: [
    {
      name: 'run-tests',
      queueName: 'ci',
      children: [
        { name: 'lint', queueName: 'ci', data: {} },
        { name: 'typecheck', queueName: 'ci', data: {} },
      ],
    },
    {
      name: 'build-assets',
      queueName: 'ci',
      data: {},
    },
  ],
});
// lint + typecheck run in parallel → run-tests
// build-assets runs in parallel with the test chain
// deploy runs after both run-tests and build-assets complete
```

## Accessing Child Results in Parent

Child workers return values that the parent worker can access:

```typescript
import { Worker } from 'bullmq';

// Child worker
const stepsWorker = new Worker('steps', async (job) => {
  if (job.name === 'paint') {
    await paintSurface(job.data.place);
    return 2500; // cost
  } else if (job.name === 'fix') {
    await fixSurface(job.data.place);
    return 1750; // cost
  }
});

// Parent worker — access child return values
const renovateWorker = new Worker('renovate', async (job) => {
  const childrenValues = await job.getChildrenValues();
  // { 'bull:steps:job-id-1': 2500, 'bull:steps:job-id-2': 2500, 'bull:steps:job-id-3': 1750 }

  const totalCost = Object.values(childrenValues).reduce(
    (sum, cost) => sum + cost, 0
  );

  await sendInvoice(totalCost);
  return { totalCost };
});
```

## Adding Flows in Bulk

Atomically add multiple independent flows:

```typescript
const flows = await flowProducer.addBulk([
  {
    name: 'order-1',
    queueName: 'orders',
    children: [
      { name: 'validate', queueName: 'steps', data: { orderId: 1 } },
      { name: 'charge',   queueName: 'steps', data: { orderId: 1 } },
    ],
  },
  {
    name: 'order-2',
    queueName: 'orders',
    children: [
      { name: 'validate', queueName: 'steps', data: { orderId: 2 } },
      { name: 'charge',   queueName: 'steps', data: { orderId: 2 } },
    ],
  },
]);
```

## Flow with Queue Options

Configure default job options per queue:

```typescript
const flow = await flowProducer.add(
  {
    name: 'parent',
    queueName: 'main',
    data: {},
    children: [
      { name: 'child-1', queueName: 'tasks', data: {} },
      { name: 'child-2', queueName: 'tasks', data: {} },
    ],
  },
  {
    queuesOptions: {
      main: {
        defaultJobOptions: { removeOnComplete: true },
      },
      tasks: {
        defaultJobOptions: { removeOnComplete: true, attempts: 3 },
      },
    },
  }
);
```

## Dependency Management

### Get Dependencies

```typescript
// All dependencies
const dependencies = await job.getDependencies();

// Paginated access by type
const { processed, nextProcessedCursor } = await job.getDependencies({
  processed: { count: 5, cursor: 0 },
});

const { unprocessed, nextUnprocessedCursor } = await job.getDependencies({
  unprocessed: { count: 5, cursor: 0 },
});

const { failed, nextFailedCursor } = await job.getDependencies({
  failed: { count: 5, cursor: 0 },
});
```

### Dependency Counts

```typescript
const counts = await job.getDependenciesCount();
// { processed: 2, unprocessed: 1, failed: 0, ignored: 0 }

// Specific counts
const { failed } = await job.getDependenciesCount({ failed: true });
```

### Check Parent

```typescript
const parentKey = job.parentKey;
// e.g., 'bull:renovate:parent-job-id'
```

## Fail Parent Behavior

If `failParentOnFailure` is set, when a child job fails, the parent is also moved to failed:

```typescript
await flowProducer.add({
  name: 'parent',
  queueName: 'main',
  children: [
    {
      name: 'critical-child',
      queueName: 'tasks',
      data: {},
      opts: { failParentOnFailure: true },
    },
    {
      name: 'optional-child',
      queueName: 'tasks',
      data: {},
      // No failParentOnFailure — parent survives this child's failure
    },
  ],
});
```

## Ignore Dependency

Mark a child as "ignorable" — parent won't wait for it:

```typescript
// Inside child processor
await job.moveToIgnored();
```

## Remove Dependency

Remove a child's dependency relationship:

```typescript
await childJob.removeDependency();
```

## Flow Tree Retrieval

Get the complete tree structure:

```typescript
const tree = await flowProducer.getFlow({
  id: parentJob.id,
  queueName: 'main',
});

// tree has: { job, children: [{ job, children: [...] }] }
```

## Removing Flow Jobs

- **Removing a parent** deletes all descendants
- **Removing a child** removes its dependency; if it's the last child, parent moves to processable
- **Locked (active) jobs** cannot be removed — an exception is thrown

```typescript
await parentJob.remove();  // removes parent + all children
```

## Dynamic Flows (Process Step Pattern)

Create child jobs during parent processing and wait for them:

```typescript
const worker = new Worker('main', async (job, token) => {
  // Add children dynamically
  const flow = new FlowProducer();
  await flow.add({
    name: 'dynamic-parent',
    queueName: 'main',
    data: {},
    children: [
      { name: 'step-1', queueName: 'tasks', data: { input: job.data } },
    ],
  });

  // Wait for children
  const shouldWait = await job.moveToWaitingChildren(token);
  if (shouldWait) {
    throw new WaitingChildrenError();
  }
});
```

## Common Pitfalls

1. **Job IDs in flows cannot contain colons (`:`)** — used as key separators
2. **Parent and child queues can be different** — each queue needs its own worker
3. **Parent enters `waiting-children` state** — it won't be picked up by workers until all children complete
4. **Flow depth** — deeply nested flows increase Redis operations; keep depth reasonable
5. **Atomicity** — `flowProducer.add()` is atomic; all jobs are created or none are

## Related Topics

- [Queues](./01-queues.md) — Queue management
- [Workers](./02-workers.md) — Processing jobs
- [Events](./09-events.md) — Monitoring flow progress
