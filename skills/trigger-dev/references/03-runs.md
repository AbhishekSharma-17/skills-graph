# Runs

> Source: https://trigger.dev/docs — v4.4.3

## Contents

- [Run Lifecycle](#run-lifecycle)
- [Run States](#run-states)
- [Metadata](#metadata)
- [Tags](#tags)
- [Runs API](#runs-api)
- [Cancellation](#cancellation)
- [Replaying and Rescheduling](#replaying-and-rescheduling)

## Run Lifecycle

A **run** is a single execution of a task. When you trigger a task, a run is created and placed into a queue.

```
trigger() → Queued → Executing → Completed
                 ↓         ↓
              Delayed    Waiting (subtask/wait)
                 ↓         ↓
              Queued    Executing
                         ↓
                    Completed / Failed / Canceled
```

Each run has:
- A unique **run ID** (e.g., `run_xxxx`)
- A **payload** (the input data)
- One or more **attempts** (retries create new attempts)
- **Status**, **metadata**, and **tags**

## Run States

### Initial States

| State | Description |
|-------|-------------|
| `PENDING_VERSION` | Task awaiting a new deployment version |
| `DELAYED` | Run is waiting for its delay period to elapse |
| `QUEUED` | Ready for execution, waiting in queue |
| `DEQUEUED` | Being sent to a worker |

### Execution States

| State | Description |
|-------|-------------|
| `EXECUTING` | Currently running on a worker |
| `WAITING` | Paused — waiting for subtask, batch, or `wait.*` call |

### Terminal States

| State | Description |
|-------|-------------|
| `COMPLETED` | Successfully finished |
| `CANCELED` | Manually stopped |
| `FAILED` | Task code error after all retries exhausted |
| `TIMED_OUT` | Exceeded `maxDuration` |
| `CRASHED` | Worker process died (usually out of memory) |
| `SYSTEM_FAILURE` | Unrecoverable system error |
| `EXPIRED` | TTL elapsed before execution started |

### Status Helpers

```typescript
const run = await runs.retrieve(runId);

if (run.isCompleted) { /* success */ }
if (run.isFailed) { /* all retries exhausted */ }
if (run.isCanceled) { /* manually canceled */ }
if (run.isExecuting) { /* still running */ }
if (run.isQueued) { /* waiting in queue */ }
if (run.isWaiting) { /* paused at waitpoint */ }
if (run.isSuccess) { /* same as isCompleted */ }
```

## Metadata

Attach arbitrary metadata to runs for tracking and filtering:

### Setting Metadata at Trigger Time

```typescript
await myTask.trigger(payload, {
  metadata: {
    source: "webhook",
    customerId: "cust_123",
    priority: "high",
  },
});
```

### Updating Metadata from Inside a Task

```typescript
import { metadata } from "@trigger.dev/sdk/v3";

export const myTask = task({
  id: "my-task",
  run: async (payload) => {
    // Set metadata (merges with existing)
    await metadata.set("progress", { step: 1, total: 5 });
    await metadata.set("currentItem", "processing invoice #42");

    // Append to a list
    await metadata.append("processedIds", "item_1");
    await metadata.append("processedIds", "item_2");

    // Increment a counter
    await metadata.increment("itemsProcessed", 1);

    // Remove a key
    await metadata.remove("tempData");

    // Read current metadata
    const current = await metadata.get();
  },
});
```

Metadata updates are visible in real-time on the dashboard and via the Realtime API.

## Tags

Tags are string labels for filtering and grouping runs:

```typescript
// Set tags at trigger time
await myTask.trigger(payload, {
  tags: ["user:alice", "team:engineering", "env:staging"],
});
```

**Tag rules:**
- Max 5 tags per run
- Max 128 characters per tag
- Lowercase, alphanumeric, hyphens, colons, underscores
- Convention: `key:value` format (e.g., `user:123`)

### Filtering by Tags

```typescript
// List runs with specific tags
const page = await runs.list({
  tag: ["user:alice"],
  limit: 20,
});
```

### Subscribing by Tags (Realtime)

```typescript
// Subscribe to all runs with a tag
for await (const run of runs.subscribeToRunsWithTag("user:alice")) {
  console.log(`Run ${run.id}: ${run.status}`);
}
```

## Runs API

### List Runs

```typescript
import { runs } from "@trigger.dev/sdk/v3";

const page = await runs.list({
  limit: 20,
  status: ["QUEUED", "EXECUTING"],
  taskIdentifier: ["process-order"],
  tag: ["priority:high"],
  from: new Date("2026-03-01"),
  to: new Date("2026-03-25"),
});

for (const run of page.data) {
  console.log(`${run.id}: ${run.status}`);
}

// Pagination
if (page.hasNextPage) {
  const nextPage = await runs.list({ cursor: page.nextCursor });
}
```

### Retrieve a Run

```typescript
import type { myTask } from "../trigger/my-task";

const run = await runs.retrieve<typeof myTask>(runId);
console.log(run.id);        // run_xxxx
console.log(run.status);    // "COMPLETED"
console.log(run.output);    // Type-safe output
console.log(run.createdAt); // Date
console.log(run.startedAt); // Date
console.log(run.finishedAt);// Date
```

### Subscribe to a Run (Realtime)

```typescript
for await (const run of runs.subscribeToRun<typeof myTask>(runId)) {
  console.log(`Status: ${run.status}`);
  if (run.isCompleted) {
    console.log("Output:", run.output);
    break;
  }
}
```

### Poll for Completion

```typescript
// Simple polling (less efficient than subscribe)
const completedRun = await runs.poll<typeof myTask>(runId, {
  pollIntervalMs: 1000,
});
```

## Cancellation

```typescript
// Cancel a single run
await runs.cancel(runId);

// Cancel stops execution, prevents retries, and cancels child runs
```

**Cancellation behavior:**
- Currently executing runs are interrupted
- Queued runs are removed from queue
- Child runs triggered with `triggerAndWait` are also canceled
- Canceled runs cannot be restarted (use replay instead)

### Bulk Cancellation

```typescript
// Cancel all queued runs for a task
const page = await runs.list({
  taskIdentifier: ["my-task"],
  status: ["QUEUED"],
});

for (const run of page.data) {
  await runs.cancel(run.id);
}
```

## Replaying and Rescheduling

### Replay — Re-run with Same Payload

```typescript
// Create a new run with the same payload, using the latest task version
const newRun = await runs.replay(runId);
console.log(`New run: ${newRun.id}`);
```

Replay creates a **new run** — it does not modify the original. The new run uses the **current deployed version** of the task.

### Reschedule — Change Delayed Run Timing

```typescript
// Change when a delayed run executes (only works for DELAYED runs)
await runs.reschedule(runId, {
  delay: "2h", // New delay from now
});

// Or set a specific time
await runs.reschedule(runId, {
  delay: new Date("2026-04-01T09:00:00Z"),
});
```

Rescheduling only works for runs in the `DELAYED` state.

## Related Topics

- Triggering tasks → `02-triggering-tasks.md`
- Realtime subscriptions → `08-realtime-streaming.md`
- Error handling → `06-error-handling-retries.md`
