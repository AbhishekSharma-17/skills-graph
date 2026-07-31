# BullMQ — Delayed & Scheduled Jobs

> Source: [docs.bullmq.io/guide/jobs/delayed](https://docs.bullmq.io/guide/jobs/delayed) · [docs.bullmq.io/guide/job-schedulers](https://docs.bullmq.io/guide/job-schedulers)

## Table of Contents

- [Delayed Jobs](#delayed-jobs)
- [Job Schedulers (v6)](#job-schedulers-v6)
- [Cron Patterns](#cron-patterns)
- [Repeat Strategies](#repeat-strategies)
- [Managing Schedulers](#managing-schedulers)
- [Migration from Repeatable Jobs](#migration-from-repeatable-jobs)

## Delayed Jobs

Delayed jobs sit in a special "delayed" set and transition to the waiting state when the delay period expires.

### Basic Delay

```typescript
import { Queue } from 'bullmq';

const queue = new Queue('notifications');

// Delay processing by 5 seconds
await queue.add('reminder', { userId: 123 }, { delay: 5000 });
```

### Schedule for a Specific Time

```typescript
const sendAt = new Date('2026-12-25T09:00:00Z');
const delayMs = sendAt.getTime() - Date.now();

await queue.add('holiday-greeting', { message: 'Happy Holidays!' }, {
  delay: delayMs,
});
```

### Modifying Delay After Creation

```typescript
const job = await queue.add('task', data, { delay: 2000 });

// Reschedule to 10 seconds from now
await job.changeDelay(10000);
```

Only jobs currently in the `delayed` state can have their delay modified.

### Promoting a Delayed Job

Move a delayed job to the waiting state immediately:

```typescript
const job = await queue.getJob('delayed-job-id');
await job.promote();
```

### Important Notes

- Delay timing is not exact — depends on worker availability and queue load
- Delay is specified in milliseconds
- Workers process delayed jobs as soon as they transition to the wait state

## Job Schedulers (v6)

Job Schedulers replace repeatable jobs (deprecated in v5.16.0, removed in v6). A Job Scheduler acts as a factory that automatically creates jobs based on repeat settings.

### Why Job Schedulers?

- **Upsert semantics** — no accidental duplicates in production
- **Cleaner management** — update or remove by scheduler ID
- **Robust** — new jobs only created when the last one begins processing

### Creating a Job Scheduler

```typescript
import { Queue } from 'bullmq';

const queue = new Queue('reports');

// Run every 60 seconds
const firstJob = await queue.upsertJobScheduler('hourly-report', {
  every: 60000,
});

// Run on a cron schedule
const firstJob = await queue.upsertJobScheduler('daily-cleanup', {
  pattern: '0 0 3 * * *',  // 3:00 AM daily
  tz: 'America/New_York',  // timezone
});
```

### Job Templates

Define default job name, data, and options for all produced jobs:

```typescript
await queue.upsertJobScheduler(
  'sync-data',
  { pattern: '*/15 * * * *' },  // every 15 minutes
  {
    name: 'data-sync',
    data: { source: 'api', target: 'db' },
    opts: {
      attempts: 3,
      backoff: { type: 'exponential', delay: 1000 },
      removeOnComplete: { count: 100 },
      removeOnFail: { count: 500 },
    },
  }
);
```

### Updating a Scheduler

`upsertJobScheduler` updates existing schedulers with the same ID:

```typescript
// Change from every 15 minutes to every 30 minutes
await queue.upsertJobScheduler(
  'sync-data',
  { every: 1800000 },
  { name: 'data-sync', data: { source: 'api', target: 'db' } }
);
```

## Cron Patterns

BullMQ supports standard Unix cron with optional seconds field:

```
┌────────────── second (0-59, optional)
│ ┌──────────── minute (0-59)
│ │ ┌────────── hour (0-23)
│ │ │ ┌──────── day of month (1-31)
│ │ │ │ ┌────── month (1-12)
│ │ │ │ │ ┌──── day of week (0-7, 0 and 7 = Sunday)
│ │ │ │ │ │
* * * * * *
```

### Examples

```typescript
// Every minute
{ pattern: '* * * * *' }

// Every 5 minutes
{ pattern: '*/5 * * * *' }

// At 3:00 AM daily
{ pattern: '0 3 * * *' }

// Monday through Friday at 9 AM
{ pattern: '0 9 * * 1-5' }

// First day of every month at midnight
{ pattern: '0 0 1 * *' }

// Every 30 seconds (6-field format)
{ pattern: '*/30 * * * * *' }

// With timezone
{ pattern: '0 9 * * *', tz: 'Europe/London' }
```

## Repeat Strategies

### Fixed Interval

```typescript
await queue.upsertJobScheduler('heartbeat', {
  every: 5000,          // every 5 seconds
  immediately: true,    // also run one immediately
});
```

### Custom Repeat Strategy

Define a custom strategy for non-standard patterns (e.g., RRULE):

```typescript
const queue = new Queue('custom', {
  settings: {
    repeatStrategy: (millis: number, opts: RepeatOptions) => {
      // Return the next execution timestamp in ms
      // Return undefined to stop repeating
      return millis + opts.every;
    },
  },
});
```

The strategy must also be set on the Worker:

```typescript
const worker = new Worker('custom', processor, {
  settings: {
    repeatStrategy: (millis, opts) => millis + opts.every,
  },
});
```

## Managing Schedulers

### List All Schedulers

```typescript
const schedulers = await queue.getJobSchedulers(0, 10); // offset, count
// Returns array of { key, name, id, endDate, tz, pattern, every, next }
```

### Remove a Scheduler

```typescript
await queue.removeJobScheduler('sync-data');
```

### Get Scheduler Count

```typescript
const count = await queue.getJobSchedulersCount();
```

## Migration from Repeatable Jobs

In v6, repeatable jobs (`repeat` option on `queue.add()`) are removed. Replace with Job Schedulers:

**Before (v5):**
```typescript
await queue.add('task', data, {
  repeat: { pattern: '*/5 * * * *' },
});

// Remove
const repeatableJobs = await queue.getRepeatableJobs();
await queue.removeRepeatableByKey(repeatableJobs[0].key);
```

**After (v6):**
```typescript
await queue.upsertJobScheduler('task-every-5m', {
  pattern: '*/5 * * * *',
}, {
  name: 'task',
  data,
});

// Remove
await queue.removeJobScheduler('task-every-5m');
```

## Common Pitfalls

1. **Job Scheduler rate** — new jobs are only created when the last produced job begins processing; under heavy load, actual frequency may be lower than specified
2. **Timezone handling** — always specify `tz` for cron patterns to avoid UTC surprises
3. **Custom job IDs unavailable** — Job Scheduler-produced jobs get auto-generated IDs
4. **One delayed job at a time** — each scheduler maintains exactly one pending delayed job

## Related Topics

- [Queues](./01-queues.md) — Adding and managing jobs
- [Prioritized Jobs](./05-prioritized.md) — Priority-based ordering
- [Rate Limiting](./08-rate-limiting-dedup.md) — Throttling processing
