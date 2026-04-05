# Inngest — Flow Control

> Source: [inngest.com/docs/guides/flow-control](https://www.inngest.com/docs/guides/flow-control)

## Table of Contents

- [Overview](#overview)
- [Concurrency](#concurrency)
- [Throttle](#throttle)
- [Rate Limiting](#rate-limiting)
- [Debounce](#debounce)
- [Priority](#priority)
- [Combining Flow Controls](#combining-flow-controls)
- [Common Patterns](#common-patterns)

---

## Overview

Flow control mechanisms let you manage how and when functions execute:

| Mechanism | Purpose | Events Dropped? |
|-----------|---------|----------------|
| **Concurrency** | Limit parallel step executions | No (queued) |
| **Throttle** | Limit function starts over time | No (queued) |
| **Rate Limiting** | Skip events beyond frequency | Yes (dropped) |
| **Debounce** | Deduplicate events in time window | Yes (coalesced) |
| **Priority** | Reorder execution queue | No |

## Concurrency

Limits the number of steps executing simultaneously across function runs.

### Basic concurrency

```typescript
inngest.createFunction(
  {
    id: "process-import",
    concurrency: 10, // Max 10 steps running at once
    triggers: { event: "import/started" },
  },
  async ({ event, step }) => { /* ... */ }
);
```

### Keyed concurrency (per-tenant)

```typescript
inngest.createFunction(
  {
    id: "generate-report",
    concurrency: [{
      limit: 2,
      key: "event.data.accountId", // 2 concurrent per account
    }],
    triggers: { event: "report/requested" },
  },
  async ({ event, step }) => { /* ... */ }
);
```

### Scoped concurrency

```typescript
inngest.createFunction(
  {
    id: "ai-summarize",
    concurrency: [
      {
        scope: "account",        // Shared across all functions
        key: `"openai"`,         // Static key — all share one limit
        limit: 60,               // Max 60 concurrent OpenAI calls
      },
      {
        scope: "fn",             // Per-function
        key: "event.data.userId",
        limit: 1,                // 1 concurrent per user for this function
      },
    ],
    triggers: { event: "ai/summarize" },
  },
  async ({ event, step }) => { /* ... */ }
);
```

### Concurrency scope levels

| Scope | Behavior |
|-------|----------|
| `fn` (default) | Limit applies to this function only |
| `env` | Shared across all functions in the environment |
| `account` | Shared across all functions in the entire account |

### What counts against concurrency

| Operation | Counts? |
|-----------|---------|
| `step.run()` (active execution) | Yes |
| `step.sleep()` / `step.sleepUntil()` | No |
| `step.waitForEvent()` | No |
| `step.invoke()` (waiting for child) | No |
| Time between steps | No |

### Queue ordering

Queues are **FIFO** (first-in, first-out) within the same function. Ordering between different functions is not guaranteed. Up to 2 concurrency constraints per function.

## Throttle

Limits the rate of new function starts over a time period. Events exceeding the limit are queued, not dropped.

```typescript
inngest.createFunction(
  {
    id: "sync-crm",
    throttle: {
      limit: 10,         // Max 10 function starts
      period: "1m",      // Per 1-minute window
    },
    triggers: { event: "crm/sync.requested" },
  },
  async ({ event, step }) => { /* ... */ }
);
```

### Keyed throttle

```typescript
inngest.createFunction(
  {
    id: "send-email",
    throttle: {
      limit: 5,
      period: "1h",
      key: "event.data.userId", // 5 emails per user per hour
    },
    triggers: { event: "email/send" },
  },
  async ({ event, step }) => { /* ... */ }
);
```

### Throttle with burst

```typescript
inngest.createFunction(
  {
    id: "api-sync",
    throttle: {
      limit: 100,
      period: "1m",
      burst: 20, // Allow 20 extra in a burst
    },
    triggers: { event: "api/sync" },
  },
  async ({ event, step }) => { /* ... */ }
);
```

### Throttle configuration

| Option | Type | Description |
|--------|------|-------------|
| `limit` | `number` | Maximum function starts per period |
| `period` | `string` | Time window (e.g., `"1s"`, `"5m"`, `"1h"`) |
| `key` | `string` | CEL expression for per-value throttling |
| `burst` | `number` | Additional allowed starts beyond limit |

## Rate Limiting

Unlike throttle, rate limiting **drops** events that exceed the limit:

```typescript
inngest.createFunction(
  {
    id: "handle-webhook",
    rateLimit: {
      limit: 1,
      period: "1s",       // Max 1 per second
      key: "event.data.ip", // Per source IP
    },
    triggers: { event: "webhook/received" },
  },
  async ({ event, step }) => { /* ... */ }
);
```

### Rate limit configuration

| Option | Type | Description |
|--------|------|-------------|
| `limit` | `number` | Maximum functions per period |
| `period` | `string` | Time window (`"1s"` to `"60s"`) |
| `key` | `string` | CEL expression for per-value limiting |

### Throttle vs Rate Limiting

| | Throttle | Rate Limiting |
|---|---------|---------------|
| Excess events | Queued | Dropped |
| Use case | Respect API limits | Prevent abuse |
| Period range | Flexible | 1s - 60s |

## Debounce

Delays function execution by coalescing events within a sliding time window. Only the last event in the window triggers the function:

```typescript
inngest.createFunction(
  {
    id: "sync-search-index",
    debounce: {
      period: "5s",                     // Wait 5 seconds after last event
      key: "event.data.documentId",     // Per document
    },
    triggers: { event: "document/updated" },
  },
  async ({ event, step }) => {
    // Only fires once, with the LAST event's data
    await step.run("index-document", () =>
      searchIndex.update(event.data.documentId)
    );
  }
);
```

### How debounce works

```
Event 1 (t=0s)  → Timer starts (5s)
Event 2 (t=3s)  → Timer resets (5s from now)
Event 3 (t=6s)  → Timer resets (5s from now)
... no more events ...
Function fires (t=11s) with Event 3's data
```

### Debounce configuration

| Option | Type | Description |
|--------|------|-------------|
| `period` | `string` | Sliding window duration (`"1s"` to `"7d"`) |
| `key` | `string` | CEL expression for per-value debouncing |

## Priority

Dynamically reorder the execution queue based on event data:

```typescript
inngest.createFunction(
  {
    id: "process-task",
    priority: {
      run: "event.data.priority == 'critical' ? 100 : event.data.priority == 'high' ? 50 : 0",
    },
    triggers: { event: "task/created" },
  },
  async ({ event, step }) => { /* ... */ }
);
```

### Priority values

- Range: `-600` to `600`
- Higher values execute first
- Default: `0`
- Negative values push items later in the queue

### Priority expressions

```typescript
// Boolean priority
priority: {
  run: "event.data.isPremium ? 100 : 0"
}

// Tiered priority
priority: {
  run: "event.data.tier == 'enterprise' ? 200 : event.data.tier == 'pro' ? 100 : 0"
}
```

## Combining Flow Controls

You can combine multiple flow controls on a single function:

```typescript
inngest.createFunction(
  {
    id: "ai-generate",
    concurrency: [{
      scope: "account",
      key: `"openai"`,
      limit: 50,
    }],
    throttle: {
      limit: 100,
      period: "1m",
      key: "event.data.orgId",
    },
    priority: {
      run: "event.data.plan == 'enterprise' ? 100 : 0",
    },
    triggers: { event: "ai/generate" },
  },
  async ({ event, step }) => { /* ... */ }
);
```

### Incompatible combinations

| Feature | Cannot combine with |
|---------|-------------------|
| `batchEvents` | `rateLimit`, `cancelOn`, `priority`, idempotency |
| `debounce` | `batchEvents` (conceptually redundant) |

## Common Patterns

### API rate limit protection

```typescript
inngest.createFunction(
  {
    id: "call-stripe",
    concurrency: [{
      scope: "env",
      key: `"stripe-api"`,
      limit: 25,
    }],
    throttle: { limit: 100, period: "1s" },
    triggers: { event: "stripe/call" },
  },
  async ({ event, step }) => { /* ... */ }
);
```

### Per-user fair queuing

```typescript
inngest.createFunction(
  {
    id: "process-request",
    concurrency: [{
      key: "event.data.userId",
      limit: 3,
    }],
    priority: {
      run: "event.data.isPaying ? 50 : 0",
    },
    triggers: { event: "request/process" },
  },
  async ({ event, step }) => { /* ... */ }
);
```

### Prevent duplicate processing

```typescript
inngest.createFunction(
  {
    id: "import-file",
    debounce: {
      period: "10s",
      key: "event.data.fileId",
    },
    concurrency: [{
      key: "event.data.fileId",
      limit: 1,
    }],
    triggers: { event: "file/uploaded" },
  },
  async ({ event, step }) => { /* ... */ }
);
```
