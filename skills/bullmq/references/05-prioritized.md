# BullMQ — Prioritized Jobs

> Source: [docs.bullmq.io/guide/jobs/prioritized](https://docs.bullmq.io/guide/jobs/prioritized)

## Overview

BullMQ supports job prioritization where lower numbers indicate higher priority. When multiple jobs exist in a queue, prioritized jobs are processed in priority order rather than FIFO. Jobs sharing the same priority value follow FIFO ordering among themselves.

## Priority Value Range

- **Range:** 1 to 2,097,151 (2^21 - 1)
- **0** means no priority assigned
- **Lower number = higher priority** (Unix convention)
- Jobs without a priority (0) are processed **before** prioritized jobs

```
No priority (0) > Priority 1 > Priority 2 > ... > Priority 2097151
  (highest)                                          (lowest)
```

## Adding Prioritized Jobs

```typescript
import { Queue } from 'bullmq';

const queue = new Queue('tasks');

// High priority
await queue.add('critical-alert', { level: 'error' }, { priority: 1 });

// Medium priority
await queue.add('user-notification', { msg: 'hello' }, { priority: 10 });

// Low priority
await queue.add('analytics-sync', { batch: 42 }, { priority: 100 });

// No priority (processed before ALL prioritized jobs)
await queue.add('health-check', {});
```

### Processing Order Example

```typescript
await queue.add('job-A', {}, { priority: 10 });
await queue.add('job-B', {}, { priority: 5 });
await queue.add('job-C', {}, { priority: 7 });
await queue.add('job-D', {});  // no priority

// Processing order: job-D (0), job-B (5), job-C (7), job-A (10)
```

## Same-Priority FIFO

Jobs with identical priority values are processed in insertion order:

```typescript
await queue.add('task-1', {}, { priority: 5 });
await queue.add('task-2', {}, { priority: 5 });
await queue.add('task-3', {}, { priority: 5 });

// Processing order: task-1, task-2, task-3 (FIFO within priority 5)
```

## Changing Priority at Runtime

Modify a job's priority after it has been added:

```typescript
const job = await queue.add('task', { data: 'value' }, { priority: 16 });

// Upgrade to highest priority
await job.changePriority({ priority: 1 });

// Switch to LIFO ordering (no priority)
await job.changePriority({ lifo: true });
```

**Constraint:** Only jobs in `wait` or `prioritized` state can have their priority changed.

## Querying Prioritized Jobs

```typescript
// Get all prioritized jobs
const prioritizedJobs = await queue.getJobs(['prioritized']);
const prioritizedJobs = await queue.getPrioritized();

// Get counts per priority level
const counts = await queue.getCountsPerPriority([0, 1, 5, 10]);
// { '0': 3, '1': 1, '5': 12, '10': 7 }

// Get total count of prioritized jobs
const count = await queue.getJobCountByTypes('prioritized');
```

## Priority with Bulk Operations

```typescript
await queue.addBulk([
  { name: 'urgent', data: { id: 1 }, opts: { priority: 1 } },
  { name: 'normal', data: { id: 2 }, opts: { priority: 10 } },
  { name: 'low',    data: { id: 3 }, opts: { priority: 100 } },
]);
```

## Priority with Delayed Jobs

Priority and delay can be combined. When a delayed job's timer expires, it moves to the prioritized set at its specified priority level:

```typescript
await queue.add('deferred-critical', data, {
  delay: 60000,     // wait 1 minute
  priority: 1,      // then process with highest priority
});
```

## Priority with Flows

Child jobs in a flow can have individual priorities:

```typescript
import { FlowProducer } from 'bullmq';

const flow = new FlowProducer();

await flow.add({
  name: 'parent',
  queueName: 'main',
  children: [
    { name: 'critical-child', queueName: 'tasks', opts: { priority: 1 } },
    { name: 'normal-child', queueName: 'tasks', opts: { priority: 10 } },
  ],
});
```

## Performance Considerations

Adding prioritized jobs has O(log n) complexity relative to the number of prioritized jobs in the queue, compared to O(1) for regular FIFO/LIFO jobs. In practice this is fast, but be aware of the difference at very high volumes (millions of prioritized jobs).

## Priority Patterns

### Tiered Priority System

```typescript
const Priority = {
  CRITICAL: 1,
  HIGH: 10,
  NORMAL: 50,
  LOW: 100,
  BACKGROUND: 1000,
} as const;

await queue.add('alert', data, { priority: Priority.CRITICAL });
await queue.add('email', data, { priority: Priority.NORMAL });
await queue.add('cleanup', data, { priority: Priority.BACKGROUND });
```

### Dynamic Priority Based on Data

```typescript
function getPriority(order: Order): number {
  if (order.type === 'express') return 1;
  if (order.total > 1000) return 10;
  if (order.isVip) return 20;
  return 50;
}

await queue.add('process-order', order, {
  priority: getPriority(order),
});
```

## Common Pitfalls

1. **Priority 0 beats all priorities** — unprioritized jobs process first, which can be counterintuitive
2. **O(log n) insertion** — at extreme scale, consider whether you truly need fine-grained priorities or if a few tiers suffice
3. **Priority starvation** — low-priority jobs may never run if high-priority jobs arrive continuously; monitor queue depths per priority level

## Related Topics

- [Queues](./01-queues.md) — Adding jobs with options
- [Jobs](./03-jobs.md) — Job types and lifecycle
- [Delayed & Scheduled](./04-delayed-scheduled.md) — Time-based scheduling
