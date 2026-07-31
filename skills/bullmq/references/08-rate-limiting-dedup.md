# BullMQ — Rate Limiting & Deduplication

> Source: [docs.bullmq.io/guide/rate-limiting](https://docs.bullmq.io/guide/rate-limiting) · [docs.bullmq.io/guide/jobs/deduplication](https://docs.bullmq.io/guide/jobs/deduplication)

## Table of Contents

- [Rate Limiting](#rate-limiting)
- [Manual Rate Limiting](#manual-rate-limiting)
- [Deduplication](#deduplication)

---

## Rate Limiting

Rate limiting controls how many jobs are processed within a time window. The limiter applies **globally** across all workers for a queue — even with 10 workers, the total processing rate is capped.

### Basic Configuration

```typescript
import { Worker } from 'bullmq';

const worker = new Worker('api-calls', async (job) => {
  await callExternalApi(job.data);
}, {
  limiter: {
    max: 10,        // maximum 10 jobs
    duration: 1000, // per 1000 milliseconds
  },
});
```

### Rate Limiting Behavior

- Jobs that get rate-limited **stay in the waiting state** — they don't fail
- When the rate limit window expires, jobs resume processing automatically
- The limit is enforced atomically via Redis across all workers

### Inspecting Rate Limit Status

```typescript
const queue = new Queue('api-calls');

// Check if queue is currently rate limited
const ttl = await queue.getRateLimitTtl();
if (ttl > 0) {
  console.log(`Rate limited for ${ttl}ms more`);
}

// Clear rate limiting and reset counter
await queue.removeRateLimitKey();
```

## Manual Rate Limiting

For dynamic scenarios (e.g., external API returns 429 Too Many Requests), workers can programmatically trigger rate limiting:

```typescript
import { Worker } from 'bullmq';

const worker = new Worker('api-calls', async (job) => {
  try {
    const response = await fetch(job.data.url);

    if (response.status === 429) {
      const retryAfter = parseInt(response.headers.get('retry-after') || '60');
      await worker.rateLimit(retryAfter * 1000);
      throw Worker.RateLimitError();
    }

    return await response.json();
  } catch (err) {
    if (err instanceof Worker.RateLimitError) throw err;
    throw err;
  }
});
```

### Key Points for Manual Rate Limiting

1. Call `worker.rateLimit(durationMs)` to set the rate limit
2. Throw `Worker.RateLimitError()` to return the job to waiting
3. `RateLimitError` does **not** increment `attemptsMade`
4. All workers for the same queue respect the rate limit

---

## Deduplication

Deduplication prevents duplicate job execution using unique identifiers. When deduplication triggers, a `deduplicated` event is emitted.

### Simple Deduplication

Ignores duplicate jobs until the original reaches a terminal state (completed/failed):

```typescript
await queue.add('process-order', { orderId: 'ORD-123' }, {
  deduplication: { id: 'order-ORD-123' },
});

// This is ignored while the first job is still processing
await queue.add('process-order', { orderId: 'ORD-123' }, {
  deduplication: { id: 'order-ORD-123' },
});
```

### Throttle Deduplication

Time-based deduplication with TTL — duplicates within the TTL window are discarded:

```typescript
await queue.add('sync-user', { userId: 42 }, {
  deduplication: {
    id: 'sync-user-42',
    ttl: 5000,  // ignore duplicates for 5 seconds
  },
});

// Within 5 seconds: ignored
await queue.add('sync-user', { userId: 42 }, {
  deduplication: { id: 'sync-user-42', ttl: 5000 },
});

// After 5 seconds: processed normally
```

### Debounce Deduplication

Combines delayed execution with replacement — each new job replaces the previous and resets the TTL:

```typescript
await queue.add('save-draft', { content: 'v1' }, {
  deduplication: {
    id: 'draft-123',
    ttl: 3000,
    extend: true,    // reset TTL on each duplicate
    replace: true,   // replace job data with latest
  },
  delay: 3000,
});

// 1 second later — replaces the previous job's data and resets the 3s timer
await queue.add('save-draft', { content: 'v2' }, {
  deduplication: {
    id: 'draft-123',
    ttl: 3000,
    extend: true,
    replace: true,
  },
  delay: 3000,
});
// Only processes once with { content: 'v2' } after 3s of inactivity
```

### Keep Last If Active

Ensures one job is always queued after the current one finishes, using the latest data:

```typescript
await queue.add('deploy', { commit: 'abc123' }, {
  deduplication: {
    id: 'deploy-main',
    keepLastIfActive: true,
  },
});

// While deploy is running, new commits queue the latest one
await queue.add('deploy', { commit: 'def456' }, {
  deduplication: { id: 'deploy-main', keepLastIfActive: true },
});

await queue.add('deploy', { commit: 'ghi789' }, {
  deduplication: { id: 'deploy-main', keepLastIfActive: true },
});

// After current deploy finishes: processes { commit: 'ghi789' } only
```

**Guarantees:**
- Maximum one active job per deduplication ID
- At most two jobs total (one active + one queued)
- Queued job always has the most recent data

### Deduplication Events

```typescript
import { QueueEvents } from 'bullmq';

const events = new QueueEvents('my-queue');
events.on('deduplicated', ({ jobId, deduplicationId, deduplicatedJobId }) => {
  console.log(`Job ${deduplicatedJobId} was deduplicated (kept: ${jobId})`);
});
```

### Managing Deduplication Keys

```typescript
// Check if a deduplication key exists
const existingJobId = await queue.getDeduplicationJobId('order-ORD-123');

// Remove a deduplication key (allow new jobs with same ID)
await queue.removeDeduplicationKey('order-ORD-123');

// From within a job processor
await job.removeDeduplicationKey();
```

### Deduplication Use Cases

| Mode | Use Case |
|------|----------|
| Simple | Payment processing, order fulfillment — ensure single execution |
| Throttle | Webhook delivery, notification dispatch — rate-limit duplicates |
| Debounce | Auto-save, search indexing — only process the latest |
| Keep Last If Active | CI/CD deploys, cache invalidation — always run latest after current |

## Common Pitfalls

1. **Rate limit is global** — it applies across all workers, not per-worker
2. **Manual rate limiting requires `RateLimitError`** — just calling `rateLimit()` isn't enough; you must throw the error
3. **Deduplication keys persist** — manually deleting a job doesn't clear its dedup key; use `removeDeduplicationKey()`
4. **Dedup ID should be deterministic** — hash job data or use meaningful business identifiers

## Related Topics

- [Workers](./02-workers.md) — Worker configuration
- [Jobs](./03-jobs.md) — Job options and lifecycle
- [Retries & Backoff](./06-retries-backoff.md) — Failure recovery
