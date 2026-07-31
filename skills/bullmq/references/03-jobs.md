# BullMQ — Jobs

> Source: [docs.bullmq.io/guide/jobs](https://docs.bullmq.io/guide/jobs)

## Overview

Jobs represent units of work stored in a queue. Each job contains a name, user-defined data payload, and configurable options. BullMQ supports mixing different job types (FIFO, LIFO, delayed, prioritized) in the same queue.

## Job States

Every job progresses through a lifecycle of states:

| State | Description |
|-------|-------------|
| `wait` | Queued for processing (FIFO order by default) |
| `prioritized` | Queued but ordered by priority value |
| `delayed` | Waiting for delay/schedule to expire |
| `active` | Currently being processed by a worker |
| `completed` | Successfully processed |
| `failed` | Processing threw an error |
| `waiting-children` | Parent job waiting for children (flows) |

## FIFO (Default)

First-In, First-Out is the default processing order:

```typescript
await queue.add('task-1', { order: 1 });
await queue.add('task-2', { order: 2 });
await queue.add('task-3', { order: 3 });
// Processed in order: task-1, task-2, task-3
```

## LIFO

Last-In, First-Out — newest jobs are processed first:

```typescript
await queue.add('task', { urgent: true }, { lifo: true });
```

## Custom Job IDs

By default, BullMQ generates unique IDs. Provide custom IDs for idempotency:

```typescript
await queue.add('process-order', { orderId: 'ORD-123' }, {
  jobId: 'order-ORD-123',
});

// Adding a job with the same ID is a no-op (no duplicate)
await queue.add('process-order', { orderId: 'ORD-123' }, {
  jobId: 'order-ORD-123',
});
```

**Constraint:** Job IDs cannot contain colons (`:`) — used as internal separators.

## Job Data

Job data is any JSON-serializable object:

```typescript
await queue.add('import-csv', {
  filePath: '/uploads/data.csv',
  mappings: { name: 0, email: 1 },
  options: { skipHeader: true },
});
```

### Updating Job Data

Workers can update job data during processing (useful for step-based patterns):

```typescript
const worker = new Worker('my-queue', async (job) => {
  await job.updateData({
    ...job.data,
    processedAt: Date.now(),
    status: 'in-progress',
  });
});
```

## Job Properties

Access inside a processor:

```typescript
const worker = new Worker('my-queue', async (job) => {
  job.id;            // unique identifier
  job.name;          // job name
  job.data;          // user payload
  job.opts;          // job options
  job.attemptsMade;  // current attempt number
  job.timestamp;     // creation timestamp
  job.returnvalue;   // value from previous attempt (if retried)
  job.failedReason;  // error message from last failure
  job.stacktrace;    // error stacktraces from each attempt
  job.progress;      // last reported progress value
  job.parentKey;     // parent job reference (flows)
});
```

## Job Methods

```typescript
// Inside a processor
await job.updateProgress(50);           // report progress
await job.updateData({ step: 2 });      // update stored data
await job.log('Processing started');    // add a log entry
await job.moveToFailed(new Error('manual fail'), 'token');
await job.remove();                     // delete from queue

// Outside (from a Job instance)
const job = await queue.getJob('job-id');
const state = await job.getState();     // 'wait' | 'active' | 'completed' | ...
const logs = await job.getLogs(0, 10);  // get log entries
await job.retry('failed');              // move back to wait
await job.remove();
await job.promote();                    // move delayed job to wait immediately
await job.changeDelay(10000);           // reschedule delayed job
await job.changePriority({ priority: 1 });
```

## Removing Jobs

### Auto-Removal (Recommended)

Set at queue level or per-job to prevent Redis memory growth:

```typescript
// Queue-level defaults
const queue = new Queue('tasks', {
  defaultJobOptions: {
    removeOnComplete: { count: 500 },  // keep last 500
    removeOnFail: { age: 86400 },      // keep 24 hours
  },
});

// Per-job override
await queue.add('task', data, {
  removeOnComplete: true,   // remove immediately on completion
  removeOnFail: { count: 100, age: 3600 }, // keep 100 or 1 hour
});
```

### Manual Removal

```typescript
// By job ID
await queue.remove('job-id');

// By job instance
const job = await queue.getJob('job-id');
await job.remove();

// Bulk cleaning
await queue.clean(3600000, 100, 'completed'); // completed older than 1 hour
await queue.clean(0, 0, 'failed');            // all failed
```

## Retrieving Jobs

```typescript
// Get a specific job
const job = await queue.getJob('job-id');

// Get jobs by state
const waiting = await queue.getWaiting(0, 10);     // offset, limit
const active = await queue.getActive();
const delayed = await queue.getDelayed();
const completed = await queue.getCompleted(0, 50);
const failed = await queue.getFailed();
const prioritized = await queue.getJobs(['prioritized']);

// Count jobs by state
const counts = await queue.getJobCounts(
  'wait', 'active', 'completed', 'failed', 'delayed', 'prioritized'
);

// Count by priority
const priorityCounts = await queue.getCountsPerPriority([0, 1, 5, 10]);
```

## Job Logs

Jobs can store structured log entries:

```typescript
const worker = new Worker('my-queue', async (job) => {
  await job.log('Step 1: Downloading file');
  await downloadFile(job.data.url);

  await job.log('Step 2: Processing');
  const result = await processFile();

  await job.log(`Step 3: Complete — processed ${result.count} records`);
  return result;
});

// Retrieve logs later
const job = await queue.getJob('job-id');
const { logs, count } = await job.getLogs(0, 100);
```

## Common Pitfalls

1. **Job data must be JSON-serializable** — no functions, circular references, or class instances
2. **Don't store large payloads** — store references (URLs, IDs) instead of full data
3. **Custom job IDs are global to the queue** — duplicates are silently ignored
4. **Sensitive data** — avoid storing secrets in job data; encrypt if necessary

## Related Topics

- [Delayed & Scheduled](./04-delayed-scheduled.md) — Timing-based jobs
- [Prioritized](./05-prioritized.md) — Priority-ordered processing
- [Retries & Backoff](./06-retries-backoff.md) — Failure recovery
- [Flows](./07-flows.md) — Parent-child dependencies
