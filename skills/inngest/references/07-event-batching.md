# Inngest — Event Batching

> Source: [inngest.com/docs/guides/batching](https://www.inngest.com/docs/guides/batching)

## Table of Contents

- [What is Event Batching?](#what-is-event-batching)
- [Configuration](#configuration)
- [How Batching Works](#how-batching-works)
- [Keyed Batching](#keyed-batching)
- [Conditional Batching](#conditional-batching)
- [Accessing Batched Events](#accessing-batched-events)
- [Constraints and Limits](#constraints-and-limits)
- [Common Patterns](#common-patterns)

---

## What is Event Batching?

Event batching allows a function to process multiple events in a single execution. Instead of invoking the function once per event, Inngest collects events into a batch and invokes the function once with all collected events.

Use cases:
- **Bulk database writes** — Insert many rows in one query
- **API batching** — Combine multiple API calls into one batch request
- **Aggregation** — Compute statistics across multiple events
- **Cost reduction** — Fewer function invocations for high-throughput events

## Configuration

```typescript
inngest.createFunction(
  {
    id: "bulk-insert-logs",
    batchEvents: {
      maxSize: 100,     // Max events per batch
      timeout: "5s",    // Max wait time before executing
    },
    triggers: { event: "log/entry.created" },
  },
  async ({ events, step }) => {
    // events is an array of all batched events
    await step.run("bulk-insert", async () => {
      const rows = events.map(evt => ({
        message: evt.data.message,
        level: evt.data.level,
        timestamp: new Date(evt.ts),
      }));
      return await db.logs.insertMany(rows);
    });

    return { inserted: events.length };
  }
);
```

### Configuration options

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `maxSize` | `number` | Yes | Maximum events per batch (1-100) |
| `timeout` | `string` | Yes | Max wait before executing (e.g., `"5s"`, `"1m"`) |
| `key` | `string` | No | CEL expression to group events into separate batches |
| `if` | `string` | No | CEL expression for conditional batching |

## How Batching Works

```
Events:     E1    E2    E3    E4    E5
Time:       0s    1s    2s    3s    5s (timeout reached)
                                    |
                                    v
            Function invoked with [E1, E2, E3, E4, E5]
```

1. **First event arrives** — Inngest creates a new batch and starts the timeout timer
2. **Events accumulate** — Subsequent matching events are added to the batch
3. **Batch triggers** when EITHER condition is met:
   - `maxSize` events collected, OR
   - `timeout` duration elapsed since first event
4. **Function invoked** with all collected events as an array

### Example timeline

```
maxSize: 3, timeout: "10s"

Scenario A (size-triggered):
  t=0s: Event 1 → batch created, timer starts
  t=1s: Event 2 → added to batch
  t=2s: Event 3 → batch full (3/3) → EXECUTE immediately

Scenario B (timeout-triggered):
  t=0s:  Event 1 → batch created, timer starts
  t=5s:  Event 2 → added to batch
  t=10s: Timer expires → EXECUTE with 2 events
```

## Keyed Batching

Group events into separate batches based on a key:

```typescript
inngest.createFunction(
  {
    id: "record-api-calls",
    batchEvents: {
      maxSize: 100,
      timeout: "5s",
      key: "event.data.userId", // Separate batch per user
    },
    triggers: { event: "api/call.logged" },
  },
  async ({ events, step }) => {
    // All events in this batch have the same userId
    const userId = events[0].data.userId;

    await step.run("bulk-record", async () => {
      const records = events.map(evt => ({
        userId,
        endpoint: evt.data.endpoint,
        timestamp: new Date(evt.ts),
      }));
      return await db.apiLogs.insertMany(records);
    });
  }
);
```

### How keyed batching works

```
Events arriving:
  { userId: "A", endpoint: "/users" }
  { userId: "B", endpoint: "/orders" }
  { userId: "A", endpoint: "/products" }
  { userId: "A", endpoint: "/settings" }
  { userId: "B", endpoint: "/users" }

Creates two batches:
  Batch (userId=A): 3 events → function invoked
  Batch (userId=B): 2 events → function invoked
```

## Conditional Batching

Only batch events that match a condition:

```typescript
inngest.createFunction(
  {
    id: "process-free-tier",
    batchEvents: {
      maxSize: 50,
      timeout: "10s",
      key: "event.data.accountId",
      if: 'event.data.plan == "free"', // Only batch free tier events
    },
    triggers: { event: "request/process" },
  },
  async ({ events, step }) => {
    // Only free-tier events are batched
    // Premium events trigger individual function runs
  }
);
```

## Accessing Batched Events

When batching is enabled, use `events` (array) instead of `event` (single):

```typescript
async ({ events, step }) => {
  // events: InngestEvent[]
  console.log(`Processing batch of ${events.length} events`);

  // Access individual events
  for (const evt of events) {
    console.log(evt.name, evt.data, evt.ts);
  }

  // Map events to database records
  const records = events.map(evt => ({
    id: evt.data.id,
    payload: evt.data,
    receivedAt: new Date(evt.ts),
  }));

  await step.run("batch-insert", () => db.records.insertMany(records));
};
```

### event vs events

| Property | Without Batching | With Batching |
|----------|-----------------|---------------|
| `event` | Single event | First event in batch |
| `events` | `undefined` | Array of all events |

## Constraints and Limits

### Hard limits

| Constraint | Limit |
|-----------|-------|
| Maximum `maxSize` | 100 events |
| Maximum batch payload | 10 MiB |
| Minimum `timeout` | `"1s"` |
| Maximum `timeout` | `"60s"` |

### Incompatible features

Event batching **cannot** be combined with:

| Feature | Reason |
|---------|--------|
| `rateLimit` | Events are batched, not individually rate-limited |
| `cancelOn` | Cancellation targets individual runs, not batches |
| `priority` | Priority applies to individual events, not groups |
| Idempotency | Event dedup happens before batching |

### Concurrency interaction

When batching is enabled, the concurrency `key` option is **ignored**. The concurrency `limit` still applies to step execution count.

## Common Patterns

### Bulk database writes

```typescript
inngest.createFunction(
  {
    id: "bulk-write-metrics",
    batchEvents: { maxSize: 100, timeout: "5s" },
    triggers: { event: "metric/recorded" },
  },
  async ({ events, step }) => {
    await step.run("insert-metrics", async () => {
      const values = events.map(e => [
        e.data.name,
        e.data.value,
        new Date(e.ts),
      ]);
      return await db.query(
        "INSERT INTO metrics (name, value, recorded_at) VALUES ?",
        [values]
      );
    });
    return { inserted: events.length };
  }
);
```

### Third-party API batching

```typescript
inngest.createFunction(
  {
    id: "batch-segment-identify",
    batchEvents: { maxSize: 50, timeout: "10s" },
    triggers: { event: "user/profile.updated" },
  },
  async ({ events, step }) => {
    await step.run("segment-batch", async () => {
      const batch = events.map(e => ({
        userId: e.data.userId,
        traits: e.data.traits,
        timestamp: new Date(e.ts),
      }));
      return await analytics.batch(batch);
    });
  }
);
```

### Aggregation

```typescript
inngest.createFunction(
  {
    id: "aggregate-page-views",
    batchEvents: {
      maxSize: 100,
      timeout: "30s",
      key: "event.data.pageUrl",
    },
    triggers: { event: "page/viewed" },
  },
  async ({ events, step }) => {
    const pageUrl = events[0].data.pageUrl;
    const uniqueVisitors = new Set(events.map(e => e.data.visitorId)).size;

    await step.run("update-stats", async () => {
      return await db.pageStats.upsert({
        where: { url: pageUrl },
        update: {
          views: { increment: events.length },
          uniqueVisitors: { increment: uniqueVisitors },
        },
        create: {
          url: pageUrl,
          views: events.length,
          uniqueVisitors,
        },
      });
    });
  }
);
```
