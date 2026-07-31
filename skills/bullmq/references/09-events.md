# BullMQ — Events & Monitoring

> Source: [docs.bullmq.io/guide/events](https://docs.bullmq.io/guide/events)

## Overview

BullMQ uses an event-driven architecture where all core classes extend `EventEmitter`. There are two categories of events:

1. **Local events** — emitted by Worker/Queue instances for jobs they directly handle
2. **Global events** — emitted by `QueueEvents` via Redis streams, covering all workers across all processes

## Worker Events (Local)

Workers emit events only for jobs they process directly:

```typescript
import { Worker, Job } from 'bullmq';

const worker = new Worker('my-queue', processor);

// Job started processing
worker.on('active', (job: Job) => {
  console.log(`[${job.id}] Started processing ${job.name}`);
});

// Job completed successfully
worker.on('completed', (job: Job, returnvalue: any) => {
  console.log(`[${job.id}] Completed with:`, returnvalue);
});

// Job failed
worker.on('failed', (job: Job | undefined, error: Error) => {
  console.error(`[${job?.id}] Failed:`, error.message);
});

// Progress update
worker.on('progress', (job: Job, progress: number | object) => {
  console.log(`[${job.id}] Progress:`, progress);
});

// Queue has no more jobs to process
worker.on('drained', () => {
  console.log('Queue is empty, waiting for new jobs...');
});

// A job was stalled and needs reprocessing
worker.on('stalled', (jobId: string) => {
  console.warn(`Job ${jobId} stalled`);
});

// Worker encountered an error
worker.on('error', (error: Error) => {
  console.error('Worker error:', error);
});

// Worker is closing
worker.on('closing', (msg: string) => {
  console.log('Worker closing:', msg);
});

// Worker has closed
worker.on('closed', () => {
  console.log('Worker closed');
});
```

**Always attach an error handler** — unhandled error events crash the process.

## Queue Events (Local)

Queue instances emit limited events:

```typescript
import { Queue } from 'bullmq';

const queue = new Queue('my-queue');

// Job entered waiting state
queue.on('waiting', (job: Job) => {
  console.log(`Job ${job.id} is waiting`);
});

// Queue error
queue.on('error', (error: Error) => {
  console.error('Queue error:', error);
});
```

## QueueEvents (Global)

`QueueEvents` monitors all jobs across all workers using Redis streams. Events are globally distributed with delivery guarantees — they won't be lost during disconnections.

```typescript
import { QueueEvents } from 'bullmq';

const queueEvents = new QueueEvents('my-queue', {
  connection: { host: 'localhost', port: 6379 },
});

// Wait for connection
await queueEvents.waitUntilReady();
```

### Available Global Events

```typescript
// Job waiting for processing
queueEvents.on('waiting', ({ jobId }) => {
  console.log(`Job ${jobId} is waiting`);
});

// Job started processing
queueEvents.on('active', ({ jobId, prev }) => {
  console.log(`Job ${jobId} active (was: ${prev})`);
});

// Job completed
queueEvents.on('completed', ({ jobId, returnvalue }) => {
  console.log(`Job ${jobId} completed:`, returnvalue);
});

// Job failed
queueEvents.on('failed', ({ jobId, failedReason, prev }) => {
  console.error(`Job ${jobId} failed:`, failedReason);
});

// Job progress updated
queueEvents.on('progress', ({ jobId, data }) => {
  console.log(`Job ${jobId} progress:`, data);
});

// Job delayed
queueEvents.on('delayed', ({ jobId, delay }) => {
  console.log(`Job ${jobId} delayed for ${delay}ms`);
});

// Job stalled
queueEvents.on('stalled', ({ jobId }) => {
  console.warn(`Job ${jobId} stalled`);
});

// Job removed
queueEvents.on('removed', ({ jobId, prev }) => {
  console.log(`Job ${jobId} removed (was: ${prev})`);
});

// Job deduplicated
queueEvents.on('deduplicated', ({ jobId, deduplicationId }) => {
  console.log(`Deduplicated: ${deduplicationId}`);
});

// Job added
queueEvents.on('added', ({ jobId, name }) => {
  console.log(`Job ${jobId} (${name}) added`);
});
```

## Progress Tracking

Report progress from within a processor:

```typescript
const worker = new Worker('video-queue', async (job) => {
  const frames = job.data.totalFrames;

  for (let i = 0; i < frames; i++) {
    await encodeFrame(i);

    // Report as percentage
    await job.updateProgress(Math.round((i / frames) * 100));
  }

  return { frames };
});

// Monitor progress globally
const events = new QueueEvents('video-queue');
events.on('progress', ({ jobId, data }) => {
  console.log(`Job ${jobId}: ${data}%`);
});
```

Progress can be a number or an object:

```typescript
await job.updateProgress({
  step: 'encoding',
  percent: 45,
  framesProcessed: 1350,
});
```

## Event Stream Management

Events are stored in a Redis stream that auto-trims to ~10,000 events. Control manually:

```typescript
const queue = new Queue('my-queue');

// Trim to last 100 events
await queue.trimEvents(100);
```

## Waiting for Specific Events

Use `QueueEvents` to wait for a specific job to complete:

```typescript
const events = new QueueEvents('my-queue');

const job = await queue.add('task', data);

// Wait for this specific job to complete
const result = await job.waitUntilFinished(events, 30000); // 30s timeout
console.log('Job result:', result);
```

## Metrics and Prometheus

BullMQ can export metrics to Prometheus:

```typescript
import { Queue } from 'bullmq';

const queue = new Queue('my-queue', {
  metrics: {
    maxDataPoints: 60 * 24, // keep 24 hours of per-minute data
  },
});

// Retrieve metrics
const completedMetrics = await queue.getMetrics('completed');
// { meta: { count, prevCount }, data: [{ count, timestamp }] }

const failedMetrics = await queue.getMetrics('failed');
```

## Event-Driven Monitoring Dashboard

```typescript
import { Queue, QueueEvents, Worker } from 'bullmq';

const queue = new Queue('production');
const events = new QueueEvents('production');

// Track real-time stats
let stats = { active: 0, completed: 0, failed: 0, waiting: 0 };

events.on('active', () => { stats.active++; stats.waiting--; });
events.on('completed', () => { stats.active--; stats.completed++; });
events.on('failed', () => { stats.active--; stats.failed++; });
events.on('waiting', () => { stats.waiting++; });

// Periodic snapshot
setInterval(async () => {
  const counts = await queue.getJobCounts('wait', 'active', 'completed', 'failed', 'delayed');
  console.log('Queue stats:', counts);
}, 10000);
```

## Cleaning Up Event Listeners

```typescript
// Close QueueEvents when done
await queueEvents.close();

// Remove specific listener
const handler = ({ jobId }) => console.log(jobId);
queueEvents.on('completed', handler);
queueEvents.off('completed', handler);
```

## Common Pitfalls

1. **Always listen for `error` events** on workers and queues — unhandled errors crash the process
2. **Worker events are local only** — they only fire for jobs processed by that specific worker instance
3. **QueueEvents uses a separate Redis connection** — factor this into connection limits
4. **Event stream grows** — configure `trimEvents` or the `metrics.maxDataPoints` to bound memory usage
5. **`waitUntilFinished` requires QueueEvents** — pass the instance and set a reasonable timeout

## Related Topics

- [Workers](./02-workers.md) — Worker event handling
- [Telemetry](./11-telemetry.md) — OpenTelemetry integration
- [Production](./12-production-nestjs.md) — Monitoring in production
