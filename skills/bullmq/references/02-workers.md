# BullMQ — Workers

> Source: [docs.bullmq.io/guide/workers](https://docs.bullmq.io/guide/workers)

## Overview

Workers are the instances that process jobs from a queue. They consume jobs, execute a user-defined processor function, and mark jobs as completed or failed. Multiple workers can operate simultaneously across the same or different processes and machines, enabling horizontal scaling.

## Creating a Worker

```typescript
import { Worker, Job } from 'bullmq';

const worker = new Worker('my-queue', async (job: Job) => {
  // Process the job
  console.log(`Processing ${job.name} [${job.id}]`);
  console.log('Data:', job.data);

  // Return a value — accessible via job.returnvalue or completion events
  return { processed: true, timestamp: Date.now() };
});
```

### With Connection Options

```typescript
const worker = new Worker(
  'my-queue',
  async (job) => {
    await doWork(job.data);
  },
  {
    connection: {
      host: 'redis.example.com',
      port: 6379,
    },
    concurrency: 10,
  }
);
```

## Worker Options

```typescript
interface WorkerOptions {
  connection: ConnectionOptions;  // Redis connection
  concurrency?: number;           // parallel jobs per worker (default: 1)
  limiter?: {
    max: number;                  // max jobs per duration
    duration: number;             // ms window
  };
  lockDuration?: number;          // ms, job lock timeout (default: 30000)
  lockRenewTime?: number;         // ms, lock renewal interval (lockDuration / 2)
  stalledInterval?: number;       // ms, stall check interval (default: 30000)
  maxStalledCount?: number;       // max stall recoveries before fail (default: 1)
  prefix?: string;                // Redis key prefix
  settings?: {
    backoffStrategy?: Function;   // custom backoff
  };
  autorun?: boolean;              // start processing immediately (default: true)
  useWorkerThreads?: boolean;     // use worker threads for sandboxed processors
  removeOnComplete?: RemoveOptions;
  removeOnFail?: RemoveOptions;
  telemetry?: TelemetryClient;    // OpenTelemetry instance
}
```

## Concurrency

The concurrency factor determines how many jobs a single worker processes simultaneously:

```typescript
// Process up to 50 jobs in parallel
const worker = new Worker('my-queue', processor, { concurrency: 50 });

// Dynamically adjust at runtime
worker.concurrency = 5;
```

**Important:** Concurrency works well with async I/O operations (HTTP requests, database calls). For CPU-intensive work, use sandboxed processors instead — high concurrency with CPU-bound work will starve the event loop.

### Scaling with Multiple Workers

Deploy multiple worker instances (separate processes or machines) for true parallelism:

```typescript
// worker-1.ts (machine A)
const worker1 = new Worker('my-queue', processor, { concurrency: 20 });

// worker-2.ts (machine B)
const worker2 = new Worker('my-queue', processor, { concurrency: 20 });

// Both process from the same queue — 40 concurrent jobs total
```

## Worker Events

Workers emit events for jobs they process directly:

```typescript
worker.on('completed', (job: Job, returnvalue: any) => {
  console.log(`Job ${job.id} completed with:`, returnvalue);
});

worker.on('failed', (job: Job | undefined, error: Error) => {
  console.error(`Job ${job?.id} failed:`, error.message);
});

worker.on('progress', (job: Job, progress: number | object) => {
  console.log(`Job ${job.id} progress:`, progress);
});

worker.on('drained', () => {
  console.log('No more jobs to process');
});

worker.on('error', (error: Error) => {
  console.error('Worker error:', error);
});

worker.on('active', (job: Job) => {
  console.log(`Job ${job.id} started processing`);
});

worker.on('stalled', (jobId: string) => {
  console.warn(`Job ${jobId} has stalled`);
});
```

## Progress Reporting

Jobs can report progress during processing:

```typescript
const worker = new Worker('video-processing', async (job) => {
  const totalFrames = job.data.frames;

  for (let i = 0; i < totalFrames; i++) {
    await processFrame(i);
    // Report progress as number (0-100) or object
    await job.updateProgress(Math.floor((i / totalFrames) * 100));
  }

  return { processedFrames: totalFrames };
});
```

Monitor progress externally:

```typescript
import { QueueEvents } from 'bullmq';

const events = new QueueEvents('video-processing');
events.on('progress', ({ jobId, data }) => {
  console.log(`Job ${jobId}: ${data}% complete`);
});
```

## Sandboxed Processors

For CPU-intensive work, run processors in separate processes to prevent event loop blocking and stalled jobs.

### Create a Processor File

```typescript
// processors/heavy-task.ts
import { SandboxedJob } from 'bullmq';

module.exports = async (job: SandboxedJob) => {
  // CPU-intensive work runs in isolation
  const result = await computeHeavyTask(job.data);
  await job.updateProgress(100);
  return result;
};
```

### Use the Processor File

```typescript
import { Worker } from 'bullmq';
import path from 'path';

const processorFile = path.join(__dirname, 'processors/heavy-task.js');

const worker = new Worker('heavy-queue', processorFile, {
  concurrency: 4, // 4 separate processes
});
```

### Using URL (recommended for Windows)

```typescript
import { pathToFileURL } from 'url';

const processorUrl = pathToFileURL(path.join(__dirname, 'processors/heavy-task.js'));
const worker = new Worker('heavy-queue', processorUrl);
```

### Worker Threads (lighter alternative)

Since BullMQ v3.13.0, use Node.js Worker Threads instead of spawned processes — less resource-demanding but still isolated:

```typescript
const worker = new Worker('heavy-queue', processorFile, {
  useWorkerThreads: true,
  concurrency: 4,
});
```

## Stalled Jobs

A job becomes stalled when its worker cannot renew the lock before the `stalledInterval` expires. Common causes:
- CPU-intensive synchronous code blocking the event loop
- Long-running operations without yielding
- Worker process crash

```typescript
const worker = new Worker('my-queue', processor, {
  lockDuration: 60000,        // 60s lock (default: 30s)
  stalledInterval: 30000,     // check every 30s (default: 30s)
  maxStalledCount: 2,         // allow 2 stall recoveries before failing
});

worker.on('stalled', (jobId) => {
  console.warn(`Job ${jobId} stalled — will be reprocessed`);
});
```

**Prevention:** Ensure your processor returns control to the Node.js event loop regularly. Use async/await for I/O operations. For CPU-bound work, use sandboxed processors.

## Pausing and Resuming

```typescript
// Pause the worker (finishes current jobs, stops picking new ones)
await worker.pause();

// Resume processing
worker.resume();

// Pause the entire queue (affects all workers)
await queue.pause();
await queue.resume();
```

## Graceful Shutdown

```typescript
const worker = new Worker('my-queue', processor);

const gracefulShutdown = async (signal: string) => {
  console.log(`Received ${signal}, shutting down...`);
  await worker.close(); // waits for active jobs to finish
  process.exit(0);
};

process.on('SIGINT', () => gracefulShutdown('SIGINT'));
process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
```

## Cancelling Active Jobs

Workers receive a cancellation token to support cooperative cancellation:

```typescript
const worker = new Worker('my-queue', async (job, token) => {
  for (let i = 0; i < 100; i++) {
    // Check for cancellation periodically
    if (await job.isCancelled()) {
      throw new Error('Job was cancelled');
    }
    await doChunk(i);
  }
});
```

## Delayed Autorun

Start a worker without immediately processing:

```typescript
const worker = new Worker('my-queue', processor, { autorun: false });

// Start processing later
worker.run();
```

## Common Pitfalls

1. **Always attach an error handler** — unhandled worker errors crash the process
2. **ioredis `maxRetriesPerRequest` must be `null` for workers** — otherwise they fail during temporary Redis disconnections
3. **Don't block the event loop** — use sandboxed processors for CPU work
4. **Concurrency > 1 requires async processors** — synchronous code runs sequentially regardless of concurrency setting

## Related Topics

- [Queues](./01-queues.md) — Adding jobs to process
- [Jobs](./03-jobs.md) — Job types and data
- [Retries & Backoff](./06-retries-backoff.md) — Handling failures
- [Events](./09-events.md) — Monitoring job lifecycle
