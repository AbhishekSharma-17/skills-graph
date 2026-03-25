# Writing Tasks

> Source: https://trigger.dev/docs — v4.4.3

## Contents

- [Task Definition](#task-definition)
- [Task Configuration Options](#task-configuration-options)
- [Lifecycle Hooks](#lifecycle-hooks)
- [Machine Configuration](#machine-configuration)
- [Task Payload and Output](#task-payload-and-output)
- [Logging](#logging)
- [Subtasks](#subtasks)
- [Common Patterns](#common-patterns)

## Task Definition

Tasks are the core building block of Trigger.dev. Each task is an exported function with a unique ID:

```typescript
import { task } from "@trigger.dev/sdk/v3";

export const myTask = task({
  id: "my-task",  // Unique identifier (used when triggering)
  run: async (payload: { userId: string }) => {
    // Your background logic here
    const user = await db.users.findById(payload.userId);
    await sendWelcomeEmail(user);
    return { success: true, email: user.email };
  },
});
```

**Rules:**
- Task `id` must be unique across your entire project
- Tasks must be exported from files in your `trigger/` directory (or configured `dirs`)
- The `run` function receives the payload and returns the output
- Both payload and output must be JSON-serializable

## Task Configuration Options

```typescript
export const processOrder = task({
  id: "process-order",

  // Maximum execution time (seconds)
  maxDuration: 600, // 10 minutes

  // Retry configuration (overrides global config)
  retry: {
    maxAttempts: 5,
    factor: 2,
    minTimeoutInMs: 1000,
    maxTimeoutInMs: 30000,
    randomize: true,
  },

  // Queue configuration
  queue: {
    concurrencyLimit: 10,
  },

  // Machine size
  machine: "medium-1x",

  run: async (payload, { ctx }) => {
    // ctx contains run metadata
    console.log(`Run ID: ${ctx.run.id}`);
    console.log(`Attempt: ${ctx.attempt.number}`);
    return { orderId: payload.orderId, status: "processed" };
  },
});
```

### All Configuration Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | `string` | Unique task identifier (required) |
| `run` | `function` | The task function (required) |
| `retry` | `object` | Retry configuration (overrides global) |
| `queue` | `object \| Queue` | Queue/concurrency settings |
| `machine` | `string` | Machine preset for compute resources |
| `maxDuration` | `number` | Max execution time in seconds |
| `init` | `function` | Runs before each attempt (for setup) |
| `onStart` | `function` | Runs when a run starts |
| `onSuccess` | `function` | Runs after successful completion |
| `onFailure` | `function` | Runs after all retries exhausted |
| `catchError` | `function` | Inspect/modify errors before retry decision |
| `middleware` | `function` | Wrap task execution with custom logic |
| `cleanup` | `function` | Runs after each attempt (success or failure) |

## Lifecycle Hooks

### init — Setup Before Each Attempt

```typescript
export const taskWithInit = task({
  id: "task-with-init",
  init: async (payload, { ctx }) => {
    // Runs before each attempt
    // Return value is passed to run() as second arg
    const db = await connectToDatabase();
    return { db };
  },
  run: async (payload, { ctx, init }) => {
    // init.db is the database connection from init()
    const result = await init.db.query("SELECT * FROM users");
    return result;
  },
});
```

### onStart, onSuccess, onFailure

```typescript
export const taskWithHooks = task({
  id: "task-with-hooks",
  onStart: async (payload, { ctx }) => {
    await notifySlack(`Task ${ctx.task.id} started (run: ${ctx.run.id})`);
  },
  onSuccess: async (payload, output, { ctx }) => {
    await notifySlack(`Task ${ctx.task.id} completed successfully`);
  },
  onFailure: async (payload, error, { ctx }) => {
    await notifySlack(`Task ${ctx.task.id} failed: ${error.message}`);
    await alertPagerDuty(ctx.task.id, error);
  },
  run: async (payload) => {
    return await processPayload(payload);
  },
});
```

### catchError — Dynamic Error Handling

```typescript
export const taskWithCatchError = task({
  id: "task-with-catch-error",
  catchError: async (payload, error, { ctx, retryAt, retryDelayInMs }) => {
    // Inspect the error and decide what to do
    if (error.message.includes("rate limit")) {
      // Retry after a custom delay
      return { retryAt: new Date(Date.now() + 60000) }; // 1 minute
    }
    if (error.message.includes("not found")) {
      // Don't retry — skip this run
      return { skipRetrying: true };
    }
    // Default: let normal retry logic handle it
    return;
  },
  run: async (payload) => {
    return await callExternalAPI(payload);
  },
});
```

## Machine Configuration

Choose compute resources per task:

| Preset | vCPU | Memory | Disk |
|--------|------|--------|------|
| `micro` | 0.25 | 0.25 GB | 10 GB |
| `small-1x` | 0.5 | 0.5 GB | 10 GB |
| `small-2x` | 1 | 1 GB | 10 GB |
| `medium-1x` | 1 | 2 GB | 10 GB |
| `medium-2x` | 2 | 4 GB | 10 GB |
| `large-1x` | 4 | 8 GB | 10 GB |
| `large-2x` | 8 | 16 GB | 10 GB |

```typescript
// Per-task machine
export const heavyTask = task({
  id: "heavy-computation",
  machine: "large-1x",
  run: async (payload) => {
    // Has 4 vCPU and 8GB RAM
    return await processLargeDataset(payload);
  },
});

// Global default in trigger.config.ts
export default defineConfig({
  project: "proj_xxxx",
  machine: "small-2x", // Default for all tasks
});
```

## Task Payload and Output

### Payload Size Limits

- **< 512 KB**: Stored directly in database
- **512 KB — 10 MB**: Auto-uploaded to S3, auto-downloaded on execution
- **> 10 MB**: Hard limit — upload externally and pass a URL

### Output Size Limits

- **Maximum**: 100 MB (auto-uploaded to S3 if large)

### Schema Validation with Zod

```typescript
import { task } from "@trigger.dev/sdk/v3";
import { z } from "zod";

const PayloadSchema = z.object({
  userId: z.string().uuid(),
  action: z.enum(["activate", "deactivate"]),
  metadata: z.record(z.string()).optional(),
});

export const validatedTask = task({
  id: "validated-task",
  run: async (payload: z.infer<typeof PayloadSchema>) => {
    const validated = PayloadSchema.parse(payload);
    return await processAction(validated);
  },
});
```

## Logging

Use the built-in `logger` for structured logging that appears in the dashboard:

```typescript
import { task, logger } from "@trigger.dev/sdk/v3";

export const loggingTask = task({
  id: "logging-example",
  run: async (payload) => {
    logger.debug("Starting task", { payload });
    logger.info("Processing user", { userId: payload.userId });
    logger.warn("Slow API response", { duration: 5000 });
    logger.error("Failed to send email", { error: "SMTP timeout" });

    // Log levels: debug, info, log, warn, error
    return { status: "done" };
  },
});
```

## Subtasks

Call other tasks from within a task:

```typescript
export const parentTask = task({
  id: "parent-task",
  run: async (payload) => {
    // Fire and forget (returns immediately)
    const handle = await childTask.trigger({ step: "first" });

    // Trigger and wait for result
    const result = await childTask.triggerAndWait({ step: "second" });
    if (result.ok) {
      console.log("Child output:", result.output);
    }

    // Batch trigger multiple children
    const batch = await childTask.batchTriggerAndWait(
      payload.items.map((item) => ({ payload: { item } }))
    );

    return { childResults: batch };
  },
});

export const childTask = task({
  id: "child-task",
  run: async (payload: { step: string }) => {
    return { processed: payload.step };
  },
});
```

**Important:** Subtasks do NOT inherit the parent's queue. They run on their own queue unless explicitly configured.

## Common Patterns

### AI Workflow with Multiple Steps

```typescript
export const aiWorkflow = task({
  id: "ai-workflow",
  machine: "medium-1x",
  maxDuration: 900, // 15 minutes
  run: async (payload: { prompt: string; userId: string }) => {
    // Step 1: Generate with LLM
    const draft = await openai.chat.completions.create({
      model: "gpt-4o",
      messages: [{ role: "user", content: payload.prompt }],
    });

    // Step 2: Store result
    await db.drafts.create({
      userId: payload.userId,
      content: draft.choices[0].message.content,
    });

    // Step 3: Notify user
    await notifyUser(payload.userId, "Your draft is ready!");

    return { draftId: draft.id };
  },
});
```

### Data Import with Progress

```typescript
export const importTask = task({
  id: "data-import",
  run: async (payload: { fileUrl: string }) => {
    const records = await downloadAndParse(payload.fileUrl);
    let processed = 0;

    for (const record of records) {
      await db.records.upsert(record);
      processed++;

      // Update metadata for realtime progress
      if (processed % 100 === 0) {
        await metadata.set("progress", {
          total: records.length,
          processed,
          percent: Math.round((processed / records.length) * 100),
        });
      }
    }

    return { totalProcessed: processed };
  },
});
```

## Related Topics

- Triggering tasks → `02-triggering-tasks.md`
- Concurrency & queues → `05-concurrency-queues.md`
- Error handling → `06-error-handling-retries.md`
- Configuration → `09-configuration.md`
