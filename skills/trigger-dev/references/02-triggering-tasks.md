# Triggering Tasks

> Source: https://trigger.dev/docs — v4.4.3

## Contents

- [Triggering from Backend Code](#triggering-from-backend-code)
- [Triggering from Inside Tasks](#triggering-from-inside-tasks)
- [Batch Triggering](#batch-triggering)
- [Trigger Options](#trigger-options)
- [Payload Handling](#payload-handling)
- [Environment Setup](#environment-setup)

## Triggering from Backend Code

Use `tasks.trigger()` from your backend without importing the task directly:

```typescript
import { tasks } from "@trigger.dev/sdk/v3";
import type { emailSequence } from "../../trigger/email-sequence";

// Trigger a single task
const handle = await tasks.trigger<typeof emailSequence>(
  "email-sequence",
  { to: "user@example.com", name: "Alice" }
);

console.log(`Run ID: ${handle.id}`);
```

**Why use `tasks.trigger()` instead of `emailSequence.trigger()`?**
Backend code should not directly import task files (which may have server-only dependencies). Use the string ID with type annotation for type safety without import side effects.

### Batch from Backend

```typescript
import { tasks } from "@trigger.dev/sdk/v3";
import type { emailSequence } from "../../trigger/email-sequence";

const batchHandle = await tasks.batchTrigger<typeof emailSequence>(
  "email-sequence",
  users.map((u) => ({
    payload: { to: u.email, name: u.name },
  }))
);

console.log(`Batch ID: ${batchHandle.batchId}`);
console.log(`Runs: ${batchHandle.runs.length}`);
```

## Triggering from Inside Tasks

Inside a task, you can import and call other tasks directly:

### Fire and Forget

```typescript
// Trigger without waiting — returns immediately
const handle = await otherTask.trigger(payload);
// handle.id is the run ID
```

### Trigger and Wait

```typescript
// Block until the child task completes
const result = await otherTask.triggerAndWait(payload);

if (result.ok) {
  console.log("Output:", result.output);
} else {
  console.log("Error:", result.error);
}

// Or use .unwrap() to throw on failure
const output = await otherTask.triggerAndWait(payload).unwrap();
```

### Batch Trigger and Wait

```typescript
// Trigger multiple runs and wait for all to complete
const results = await otherTask.batchTriggerAndWait(
  items.map((item) => ({ payload: { item } }))
);

for (const result of results) {
  if (result.ok) {
    console.log("Success:", result.output);
  }
}
```

### Heterogeneous Batch (Different Tasks)

```typescript
import { batch } from "@trigger.dev/sdk/v3";

// Trigger different tasks in a single batch
const results = await batch.triggerByTaskAndWait([
  { task: processImage, payload: { url: "..." } },
  { task: generateThumbnail, payload: { url: "..." } },
  { task: extractMetadata, payload: { url: "..." } },
]);

// Results are type-safe per task
const [imageResult, thumbResult, metaResult] = results;
```

## Batch Triggering

### Standard Batch

```typescript
const batchHandle = await myTask.batchTrigger(
  items.map((item) => ({
    payload: { itemId: item.id },
    options: { delay: "5s" }, // Optional per-item options
  }))
);
```

**Limits:** Up to 1,000 items per batch call (SDK 4.3.1+).

### Streaming Batch (Large Datasets)

For batches larger than memory, use `AsyncIterable` or `ReadableStream`:

```typescript
// Generator for memory-efficient large batches
async function* generateItems() {
  for await (const userId of fetchAllUserIds()) {
    yield { payload: { userId } };
  }
}

const batchHandle = await myTask.batchTrigger(generateItems());
```

### Batch Error Handling

```typescript
import { BatchTriggerError } from "@trigger.dev/sdk/v3";

try {
  const handle = await myTask.batchTrigger(items);
} catch (error) {
  if (error instanceof BatchTriggerError) {
    if (error.isRateLimited) {
      // Wait and retry
      await new Promise((r) => setTimeout(r, error.retryAfterMs ?? 10000));
    }
  }
}
```

## Trigger Options

All trigger methods accept an options object:

### delay — Schedule for Later

```typescript
// Duration string
await myTask.trigger(data, { delay: "1h30m" });

// Specific timestamp
await myTask.trigger(data, { delay: new Date("2026-04-01T09:00:00Z") });

// Supported formats: "30s", "5m", "2h", "1d", "1h30m", etc.
```

Delayed runs show as "Delayed" in the dashboard and execute on the **deployed version at execution time**, not the version when triggered.

### ttl — Time to Live

```typescript
// Auto-expire if not started within 1 hour
await myTask.trigger(data, { ttl: "1h" });

// Numeric value in seconds
await myTask.trigger(data, { ttl: 3600 });
```

- Development default: 10 minutes
- Cloud maximum: 14 days
- Expired runs transition to "Expired" state

### idempotencyKey — Prevent Duplicates

```typescript
await myTask.trigger(data, {
  idempotencyKey: `order-${orderId}`,
});

// Same key within 30 days → returns previous run handle
// Does NOT re-execute the task
```

Default TTL: 30 days. Set custom TTL with `idempotencyKeyTTL: "1h"`.

### debounce — Consolidate Triggers

```typescript
// Only the last trigger within the delay window executes
await myTask.trigger(data, {
  debounce: {
    key: `user-${userId}`,
    delay: "5s",
    maxDelay: "5m", // Hard upper limit
  },
});
```

Modes:
- `"trailing"` (default) — Last payload wins
- `"leading"` — First payload wins, subsequent are absorbed

### concurrencyKey — Per-Entity Queuing

```typescript
await myTask.trigger(data, {
  concurrencyKey: data.userId, // Separate queue per user
});
```

### queue — Override Queue

```typescript
await myTask.trigger(data, {
  queue: {
    name: "priority-queue",
    concurrencyLimit: 20,
  },
});
```

### Other Options

```typescript
await myTask.trigger(data, {
  tags: ["user:123", "priority:high"],    // Filterable tags
  metadata: { source: "api", version: 2 }, // Arbitrary metadata
  maxAttempts: 3,                          // Override retry count
  maxDuration: 600,                        // Override timeout (seconds)
  machine: "large-1x",                     // Override machine size
  region: "eu-central-1",                  // Execution region
  priority: 1,                             // Queue priority (higher = sooner)
});
```

## Payload Handling

### Size Limits

| Size | Behavior |
|------|----------|
| < 512 KB | Stored in database |
| 512 KB — 10 MB | Auto-uploaded to S3, auto-downloaded on execution |
| > 10 MB | **Rejected** — upload externally, pass URL in payload |

### Output Limits

- Maximum output size: 100 MB
- Large outputs auto-uploaded to S3

### Best Practice for Large Data

```typescript
// Don't pass large data in payload
// ❌ Bad
await myTask.trigger({ csvData: hugeString });

// ✅ Good — upload first, pass URL
const url = await uploadToS3(hugeString);
await myTask.trigger({ csvUrl: url });
```

## Environment Setup

### Backend Authentication

Set `TRIGGER_SECRET_KEY` in your backend environment:

```bash
# Get from dashboard → Project → API Keys
TRIGGER_SECRET_KEY=tr_dev_xxxx   # Development
TRIGGER_SECRET_KEY=tr_prod_xxxx  # Production
```

### Preview Branches

For preview environments, also set:

```bash
TRIGGER_PREVIEW_BRANCH=feature/my-branch
```

### Programmatic Configuration

```typescript
import { configure } from "@trigger.dev/sdk/v3";

configure({
  secretKey: process.env.TRIGGER_SECRET_KEY,
  baseURL: "https://your-self-hosted.com", // Optional for self-hosted
});
```

## Related Topics

- Writing tasks → `01-writing-tasks.md`
- Runs lifecycle → `03-runs.md`
- Batch processing → `05-concurrency-queues.md`
