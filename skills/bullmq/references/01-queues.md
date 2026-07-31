# BullMQ — Queues

> Source: [docs.bullmq.io/guide/queues](https://docs.bullmq.io/guide/queues)

## Overview

A Queue is a list of jobs waiting to be processed by workers. Queues can handle small message-like jobs for message brokering or larger, long-running tasks. When instantiating a Queue, BullMQ performs an upsert on a Redis meta-key — if the queue previously existed, it resumes from that state.

## Creating a Queue

```typescript
import { Queue } from 'bullmq';

// Minimal — connects to localhost:6379
const queue = new Queue('my-queue');

// With connection options
const queue = new Queue('my-queue', {
  connection: {
    host: 'redis.example.com',
    port: 6379,
    password: 'secret',
  },
});

// With a prefix (namespace isolation)
const queue = new Queue('my-queue', {
  prefix: 'myapp',
  connection: { host: 'localhost', port: 6379 },
});
```

## Adding Jobs

### Single Job

```typescript
// queue.add(jobName, data, options?)
await queue.add('send-email', {
  to: 'user@example.com',
  subject: 'Hello',
});

// With options
await queue.add('process-image', { url: 'https://...' }, {
  delay: 5000,           // delay 5 seconds
  priority: 1,           // high priority
  attempts: 3,           // retry up to 3 times
  removeOnComplete: true, // auto-cleanup
  removeOnFail: 1000,    // keep last 1000 failed
});
```

### Adding Jobs in Bulk

Bulk operations are atomic — all jobs are added or none are:

```typescript
await queue.addBulk([
  { name: 'send-email', data: { to: 'a@example.com' } },
  { name: 'send-email', data: { to: 'b@example.com' } },
  { name: 'send-email', data: { to: 'c@example.com' }, opts: { priority: 1 } },
]);
```

## Job Options Reference

```typescript
interface JobsOptions {
  // Scheduling
  delay?: number;           // ms to wait before processing
  priority?: number;        // 1 (highest) to 2097151 (lowest), 0 = no priority

  // Retries
  attempts?: number;        // max retry count (default: 0 = no retries)
  backoff?: {
    type: 'fixed' | 'exponential';
    delay: number;          // base delay in ms
    jitter?: number;        // 0-1 randomization factor
  };

  // Lifecycle
  removeOnComplete?: boolean | number | { age?: number; count?: number };
  removeOnFail?: boolean | number | { age?: number; count?: number };
  timestamp?: number;       // job creation timestamp override

  // Identity
  jobId?: string;           // custom ID (must not contain ":")

  // LIFO
  lifo?: boolean;           // process last-in first (default: false / FIFO)

  // Deduplication
  deduplication?: {
    id: string;
    ttl?: number;           // ms, throttle mode
    extend?: boolean;       // debounce: reset TTL
    replace?: boolean;      // debounce: replace data
    keepLastIfActive?: boolean;
  };

  // Repeat (deprecated in v6, use Job Schedulers)
  repeat?: { pattern?: string; every?: number; limit?: number };

  // Parent reference (for flows)
  parent?: { id: string; queue: string };
}
```

## Queue Management Methods

### Pausing and Resuming

```typescript
// Pause — workers stop picking up new jobs
await queue.pause();

// Resume
await queue.resume();
```

### Cleaning Jobs

```typescript
// Remove completed jobs older than 1 hour (grace period in ms)
await queue.clean(3600000, 100, 'completed');

// Remove all failed jobs
await queue.clean(0, 0, 'failed');

// Obliterate — remove ALL data for this queue
await queue.obliterate({ force: true });
```

### Draining

```typescript
// Remove all waiting jobs (delayed remains untouched)
await queue.drain();

// Also remove delayed jobs
await queue.drain(true);
```

### Job Counts and Getters

```typescript
// Get counts by state
const counts = await queue.getJobCounts('wait', 'active', 'completed', 'failed', 'delayed');
// { wait: 5, active: 2, completed: 100, failed: 3, delayed: 1 }

// Get jobs by state
const waitingJobs = await queue.getJobs(['wait'], 0, 10); // first 10
const failedJobs = await queue.getJobs(['failed']);

// Specific getters
const waiting = await queue.getWaiting(0, 10);
const active = await queue.getActive();
const delayed = await queue.getDelayed();
const completed = await queue.getCompleted(0, 50);
const failed = await queue.getFailed();
```

### Removing a Specific Job

```typescript
await queue.remove('job-id-123');
```

## Global Concurrency

Limit total active jobs across all workers for a queue:

```typescript
// Only 5 jobs active at any time, regardless of worker count
await queue.setGlobalConcurrency(5);
```

## Auto-Removal

Configure automatic job cleanup to prevent Redis memory growth:

```typescript
const queue = new Queue('tasks', {
  defaultJobOptions: {
    // Keep last 1000 completed jobs
    removeOnComplete: { count: 1000 },
    // Keep failed jobs for 24 hours
    removeOnFail: { age: 24 * 3600 },
  },
});
```

**Options for `removeOnComplete` / `removeOnFail`:**
- `true` — remove immediately
- `number` — keep this many recent jobs
- `{ count: number }` — keep N most recent
- `{ age: number }` — keep for N seconds
- `{ age: number, count: number }` — whichever triggers first

## Queue Events

```typescript
queue.on('waiting', (job) => {
  console.log(`Job ${job.id} is waiting`);
});

queue.on('error', (err) => {
  console.error('Queue error:', err);
});
```

## Event Stream Trimming

The event stream auto-trims to ~10,000 events by default. Manual control:

```typescript
// Trim to last 100 events
await queue.trimEvents(100);
```

## Closing a Queue

```typescript
await queue.close();
```

## Common Pitfalls

1. **Don't use ioredis `keyPrefix`** — use BullMQ's `prefix` option instead; ioredis keyPrefix conflicts with internal key management
2. **Redis `maxmemory-policy` must be `noeviction`** — arbitrary eviction breaks queue state
3. **Job IDs cannot contain colons (`:`)** — used as internal separators
4. **Queue instances are lightweight** — they only manage job storage, not processing

## Related Topics

- [Workers](./02-workers.md) — Processing queued jobs
- [Jobs](./03-jobs.md) — Job types and lifecycle
- [Rate Limiting](./08-rate-limiting-dedup.md) — Throttling job processing
