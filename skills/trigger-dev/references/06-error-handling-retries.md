# Error Handling & Retries

> Source: https://trigger.dev/docs — v4.4.3

## Contents

- [Retry Configuration](#retry-configuration)
- [Global vs Task-Level Retries](#global-vs-task-level-retries)
- [Retry Strategies](#retry-strategies)
- [retry.onThrow — Block-Level Retries](#retryonthrow--block-level-retries)
- [retry.fetch — HTTP Retries](#retryfetch--http-retries)
- [catchError — Dynamic Error Handling](#catcherror--dynamic-error-handling)
- [Preventing Retries](#preventing-retries)
- [Common Patterns](#common-patterns)

## Retry Configuration

Configure retries with exponential backoff:

```typescript
export const myTask = task({
  id: "my-task",
  retry: {
    maxAttempts: 5,          // Total attempts (including first)
    factor: 2,               // Exponential backoff multiplier
    minTimeoutInMs: 1000,    // Min delay between retries (1s)
    maxTimeoutInMs: 60000,   // Max delay between retries (60s)
    randomize: true,         // Add jitter to prevent thundering herd
  },
  run: async (payload) => {
    // If this throws, it retries up to 5 times
    return await riskyOperation(payload);
  },
});
```

### Retry Timing Example

With `factor: 2`, `minTimeoutInMs: 1000`:

| Attempt | Delay |
|---------|-------|
| 1 | Immediate |
| 2 | ~1s |
| 3 | ~2s |
| 4 | ~4s |
| 5 | ~8s |

With `randomize: true`, each delay gets ±25% jitter.

## Global vs Task-Level Retries

### Global (trigger.config.ts)

```typescript
import { defineConfig } from "@trigger.dev/sdk/v3";

export default defineConfig({
  project: "proj_xxxx",
  retries: {
    enabledInDev: false,  // Disable retries in dev (recommended)
    default: {
      maxAttempts: 3,
      factor: 2,
      minTimeoutInMs: 1000,
      maxTimeoutInMs: 30000,
      randomize: true,
    },
  },
});
```

### Task-Level (Overrides Global)

```typescript
export const criticalTask = task({
  id: "critical-task",
  retry: {
    maxAttempts: 10,  // More retries for critical tasks
    factor: 1.8,
    minTimeoutInMs: 2000,
    maxTimeoutInMs: 120000,
  },
  run: async (payload) => { /* ... */ },
});
```

Task-level configuration always takes precedence over global defaults.

**Development note:** By default, retries are disabled in the `DEV` environment when you initialize a project with the CLI. Set `enabledInDev: true` to override.

## Retry Strategies

### Task-Level Retries (Default)

The entire `run` function is re-executed on each retry attempt. The `ctx.attempt.number` tells you which attempt you're on:

```typescript
export const taskWithAttemptAwareness = task({
  id: "attempt-aware",
  retry: { maxAttempts: 3 },
  run: async (payload, { ctx }) => {
    console.log(`Attempt ${ctx.attempt.number} of ${ctx.run.maxAttempts}`);

    if (ctx.attempt.number > 1) {
      // Use a fallback strategy on retries
      return await fallbackApproach(payload);
    }
    return await primaryApproach(payload);
  },
});
```

## retry.onThrow — Block-Level Retries

Retry a specific code block without retrying the entire task:

```typescript
import { task, retry } from "@trigger.dev/sdk/v3";

export const myTask = task({
  id: "my-task",
  run: async (payload) => {
    // Step 1 — no retry needed
    const data = prepareData(payload);

    // Step 2 — retry this specific block up to 3 times
    const result = await retry.onThrow(
      async () => {
        return await unreliableAPI.call(data);
      },
      {
        maxAttempts: 3,
        factor: 2,
        minTimeoutInMs: 500,
      }
    );

    // Step 3 — only runs if step 2 succeeded
    await saveResult(result);
    return result;
  },
});
```

**Use case:** When only part of your task is unreliable (e.g., an external API call), retry just that part without re-running the entire task.

## retry.fetch — HTTP Retries

Built-in fetch wrapper with retry logic based on status codes and headers:

```typescript
import { task, retry } from "@trigger.dev/sdk/v3";

export const apiTask = task({
  id: "api-task",
  run: async (payload) => {
    const response = await retry.fetch("https://api.example.com/data", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }, {
      retry: {
        // Retry on these status codes
        statusCodes: ["429", "500-599"],
        // Max retries
        maxAttempts: 5,
        // Respect Retry-After header
        byStatus: {
          "429": {
            strategy: "headers",
            headerName: "Retry-After",
          },
        },
      },
      timeout: {
        durationInMs: 30000,  // 30s per request
        retry: {
          maxAttempts: 2,
        },
      },
    });

    return await response.json();
  },
});
```

### retry.fetch Features

- Retry on specific HTTP status codes (ranges supported: `"500-599"`)
- Respect `Retry-After` headers for rate limiting
- Configurable timeouts with separate retry logic
- Supports all standard `fetch` options

## catchError — Dynamic Error Handling

Inspect errors and dynamically modify retry behavior:

```typescript
export const smartRetryTask = task({
  id: "smart-retry",
  retry: { maxAttempts: 5 },
  catchError: async (payload, error, { ctx, retryAt, retryDelayInMs }) => {
    // Log the error
    console.error(`Attempt ${ctx.attempt.number} failed:`, error.message);

    if (error.message.includes("rate limit")) {
      // Custom retry delay for rate limits
      return { retryAt: new Date(Date.now() + 60000) }; // Wait 1 minute
    }

    if (error.message.includes("not found")) {
      // Don't retry — this won't fix itself
      return { skipRetrying: true };
    }

    if (error.message.includes("invalid input")) {
      // Replace the error with a more descriptive one
      return { error: new Error(`Invalid input for ${payload.id}: ${error.message}`) };
    }

    // Default: use normal retry logic
    return;
  },
  run: async (payload) => {
    return await processPayload(payload);
  },
});
```

### catchError Return Options

| Return | Effect |
|--------|--------|
| `undefined` | Normal retry behavior |
| `{ skipRetrying: true }` | Stop retrying, fail the run |
| `{ retryAt: Date }` | Retry at a specific time |
| `{ retryDelayInMs: number }` | Custom delay in milliseconds |
| `{ error: Error }` | Replace the error (still retries) |

## Preventing Retries

### AbortTaskRunError

Throw this to immediately fail without retrying:

```typescript
import { task, AbortTaskRunError } from "@trigger.dev/sdk/v3";

export const validateTask = task({
  id: "validate-task",
  retry: { maxAttempts: 5 },
  run: async (payload) => {
    if (!payload.userId) {
      // This will NOT retry — fails immediately
      throw new AbortTaskRunError("userId is required");
    }

    // Normal errors WILL retry
    return await processUser(payload.userId);
  },
});
```

### Try/Catch

Handle errors gracefully within the task:

```typescript
export const resilientTask = task({
  id: "resilient-task",
  run: async (payload) => {
    try {
      return await primaryMethod(payload);
    } catch (error) {
      // Handled — no retry triggered
      console.warn("Primary method failed, using fallback");
      return await fallbackMethod(payload);
    }
  },
});
```

## Common Patterns

### OpenAI with Retries

```typescript
export const aiTask = task({
  id: "ai-generation",
  retry: {
    maxAttempts: 10,
    factor: 1.8,
    minTimeoutInMs: 1000,
    maxTimeoutInMs: 60000,
  },
  catchError: async (payload, error) => {
    if (error.message.includes("429")) {
      return { retryAt: new Date(Date.now() + 30000) };
    }
    if (error.message.includes("context_length_exceeded")) {
      return { skipRetrying: true };
    }
  },
  run: async (payload) => {
    const response = await openai.chat.completions.create({
      model: "gpt-4o",
      messages: payload.messages,
    });
    return response.choices[0].message;
  },
});
```

### Webhook with Idempotent Retries

```typescript
export const webhookHandler = task({
  id: "webhook-handler",
  retry: { maxAttempts: 3 },
  run: async (payload: { eventId: string; data: unknown }) => {
    // Check if already processed (idempotency)
    const existing = await db.events.findById(payload.eventId);
    if (existing) {
      return { status: "already_processed" };
    }

    await db.events.create({
      id: payload.eventId,
      data: payload.data,
      processedAt: new Date(),
    });

    return { status: "processed" };
  },
});
```

## Related Topics

- Writing tasks → `01-writing-tasks.md`
- Wait & human-in-the-loop → `07-wait-and-human-in-loop.md`
- Configuration → `09-configuration.md`
