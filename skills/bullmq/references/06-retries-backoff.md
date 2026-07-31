# BullMQ — Retries & Backoff

> Source: [docs.bullmq.io/guide/retrying-failing-jobs](https://docs.bullmq.io/guide/retrying-failing-jobs)

## Table of Contents

- [Enabling Retries](#enabling-retries)
- [Built-in Backoff Strategies](#built-in-backoff-strategies)
- [Custom Backoff Strategies](#custom-backoff-strategies)
- [Stalled Jobs](#stalled-jobs)
- [Manual Retry](#manual-retry)
- [Special Errors](#special-errors-non-retryable)
- [Retry Patterns](#retry-patterns)

## Overview

When a job's processor function throws an error (or a job stalls beyond `maxStalledCount`), BullMQ marks it as failed. With retry configuration, failed jobs are automatically re-queued with configurable backoff delays. Retried jobs respect their priority when moved back to the waiting state.

## Enabling Retries

Set the `attempts` option to a value greater than 1:

```typescript
await queue.add('send-webhook', { url: 'https://api.example.com' }, {
  attempts: 5,  // retry up to 5 times (total of 5 attempts)
});
```

## Built-in Backoff Strategies

### Fixed Backoff

Retries after a constant delay:

```typescript
await queue.add('api-call', data, {
  attempts: 3,
  backoff: {
    type: 'fixed',
    delay: 5000,  // wait 5 seconds between each retry
  },
});
// Retry schedule: 5s, 5s, 5s
```

With jitter (random variation to avoid thundering herd):

```typescript
await queue.add('api-call', data, {
  attempts: 5,
  backoff: {
    type: 'fixed',
    delay: 3000,
    jitter: 0.5,  // 0 to 1 — adds random ±50% variation
  },
});
// Retry schedule: ~3s ± 1.5s each time
```

### Exponential Backoff

Delay increases exponentially: `2^(attempt-1) × delay` ms

```typescript
await queue.add('api-call', data, {
  attempts: 5,
  backoff: {
    type: 'exponential',
    delay: 1000,
  },
});
// Retry schedule: 1s, 2s, 4s, 8s, 16s
```

With jitter:

```typescript
await queue.add('api-call', data, {
  attempts: 7,
  backoff: {
    type: 'exponential',
    delay: 3000,
    jitter: 0.3,
  },
});
// Retry schedule: ~3s, ~6s, ~12s, ~24s, ~48s, ~96s, ~192s (±30%)
```

## Default Backoff for All Jobs

Set at the queue level to apply to every job:

```typescript
const queue = new Queue('webhooks', {
  defaultJobOptions: {
    attempts: 3,
    backoff: {
      type: 'exponential',
      delay: 2000,
    },
  },
});

// All jobs in this queue now retry 3 times with exponential backoff
await queue.add('notify', { event: 'user.created' });
```

## Custom Backoff Strategies

Define custom backoff logic in the worker settings:

```typescript
const worker = new Worker('my-queue', processor, {
  settings: {
    backoffStrategy: (attemptsMade: number, type: string, err: Error, job: Job) => {
      switch (type) {
        case 'linear':
          return attemptsMade * 1000;  // 1s, 2s, 3s, 4s...

        case 'rate-limited':
          // Parse retry-after from API response
          const retryAfter = parseInt(err.message.match(/retry-after: (\d+)/)?.[1] || '60');
          return retryAfter * 1000;

        case 'fibonacci': {
          const fib = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55];
          return (fib[attemptsMade - 1] || 60) * 1000;
        }

        default:
          return Math.min(attemptsMade * 1000, 30000);
      }
    },
  },
});
```

**Return values from `backoffStrategy`:**
- **Positive number** — delay in ms before next retry
- **0** — immediately move to end of waiting list
- **-1** — skip retry, move directly to failed state

### Using Custom Backoff

```typescript
await queue.add('api-call', data, {
  attempts: 5,
  backoff: {
    type: 'rate-limited',  // matches the switch case above
    delay: 1000,           // passed as base but custom logic may ignore it
  },
});
```

## Stalled Jobs

A job becomes "stalled" when its worker can't renew its Redis lock before the `stalledInterval` expires. This typically happens when:
- CPU-intensive work blocks the event loop
- Worker process crashes
- Long-running synchronous operations

### Stalled Job Configuration

```typescript
const worker = new Worker('my-queue', processor, {
  lockDuration: 60000,       // 60s — how long a lock is held
  stalledInterval: 30000,    // 30s — how often to check for stalls
  maxStalledCount: 2,        // allow 2 stall recoveries before permanent fail
});
```

### Stalled Job Flow

1. Worker acquires lock on job (duration: `lockDuration`)
2. Lock is auto-renewed at `lockDuration / 2` intervals
3. If renewal fails for `stalledInterval`, job is considered stalled
4. Stalled job moves back to `wait` (if `attemptsMade < maxStalledCount`)
5. After `maxStalledCount` stalls, job moves to `failed`

### Preventing Stalls

```typescript
// BAD: Blocking the event loop
const worker = new Worker('queue', async (job) => {
  heavySyncComputation(job.data);  // blocks lock renewal
});

// GOOD: Use sandboxed processor for CPU work
const worker = new Worker('queue', './processor.js');

// GOOD: Break work into async chunks
const worker = new Worker('queue', async (job) => {
  for (const chunk of splitWork(job.data)) {
    await processChunkAsync(chunk);  // yields to event loop
  }
});
```

## Manual Retry

Retry a specific failed job programmatically:

```typescript
const job = await queue.getJob('failed-job-id');
const state = await job.getState();

if (state === 'failed') {
  await job.retry('failed');  // moves back to wait
}
```

### Retry All Failed Jobs

```typescript
const failed = await queue.getFailed();
for (const job of failed) {
  await job.retry('failed');
}
```

## Accessing Retry Information

```typescript
const worker = new Worker('queue', async (job) => {
  console.log(`Attempt ${job.attemptsMade} of ${job.opts.attempts}`);

  if (job.attemptsMade > 0) {
    console.log('Previous failure:', job.failedReason);
    console.log('Stack traces:', job.stacktrace);
  }
});
```

## Special Errors (Non-Retryable)

Certain errors signal the worker to change job state without counting as an attempt:

```typescript
import { Worker, DelayedError, WaitingChildrenError } from 'bullmq';

const worker = new Worker('queue', async (job, token) => {
  // Move to delayed state without incrementing attemptsMade
  await job.moveToDelayed(Date.now() + 5000, token);
  throw new DelayedError();

  // Move to waiting-children state
  await job.moveToWaitingChildren(token);
  throw new WaitingChildrenError();

  // Trigger rate limiting
  await worker.rateLimit(60000);
  throw Worker.RateLimitError();
});
```

Use `maxStartedAttempts` to limit total processing starts when using special errors:

```typescript
await queue.add('task', data, {
  attempts: 3,                    // retry attempts for real failures
  // maxStartedAttempts: 100,     // limit total processing starts (including special errors)
});
```

## Retry Patterns

### Exponential with Maximum Cap

```typescript
const worker = new Worker('queue', processor, {
  settings: {
    backoffStrategy: (attemptsMade) => {
      const delay = Math.min(
        1000 * Math.pow(2, attemptsMade - 1),
        300000  // cap at 5 minutes
      );
      return delay;
    },
  },
});
```

### Circuit Breaker Pattern

```typescript
let consecutiveFailures = 0;
const CIRCUIT_THRESHOLD = 5;

const worker = new Worker('external-api', async (job) => {
  if (consecutiveFailures >= CIRCUIT_THRESHOLD) {
    await worker.rateLimit(60000);  // back off for 1 minute
    throw Worker.RateLimitError();
  }

  try {
    const result = await callExternalApi(job.data);
    consecutiveFailures = 0;
    return result;
  } catch (err) {
    consecutiveFailures++;
    throw err;
  }
});
```

## Common Pitfalls

1. **Exceptions must be Error objects** — throwing strings or plain objects won't be properly captured in `failedReason` and `stacktrace`
2. **Retries respect priority** — retried jobs compete with new jobs based on priority, not arrival order
3. **`maxStalledCount` is separate from `attempts`** — stalls and failures are independent counters
4. **Idempotent processors** — since jobs may run multiple times due to retries/stalls, processors should be idempotent

## Related Topics

- [Workers](./02-workers.md) — Stalled job handling
- [Jobs](./03-jobs.md) — Job state lifecycle
- [Events](./09-events.md) — Monitoring failures
