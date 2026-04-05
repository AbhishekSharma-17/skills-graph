# Inngest — Error Handling & Retries

> Source: [inngest.com/docs/features/inngest-functions/error-handling](https://www.inngest.com/docs/features/inngest-functions/error-handling)

## Table of Contents

- [Retry Configuration](#retry-configuration)
- [Retry Behavior](#retry-behavior)
- [NonRetriableError](#nonretriableerror)
- [Step-Level Error Handling](#step-level-error-handling)
- [onFailure Handler](#onfailure-handler)
- [Error Patterns](#error-patterns)
- [Custom Backoff](#custom-backoff)
- [Python Error Handling](#python-error-handling)

---

## Retry Configuration

Retries are configured at the function level and apply per-step:

```typescript
inngest.createFunction(
  {
    id: "process-payment",
    retries: 4,  // Default: 4 retries (5 total attempts per step)
    triggers: { event: "payment/created" },
  },
  async ({ event, step }) => {
    // Each step gets up to 5 attempts independently
  }
);
```

### Retry limits

| Value | Total Attempts | Use Case |
|-------|---------------|----------|
| `0` | 1 (no retries) | Idempotency-critical operations |
| `1` | 2 | Quick retry for transient errors |
| `4` | 5 (default) | Most background jobs |
| `10` | 11 | Flaky external APIs |
| `20` | 21 (maximum) | Critical operations that must succeed |

## Retry Behavior

### Default backoff schedule

Inngest uses exponential backoff with jitter:

```
Attempt 1: Immediate
Attempt 2: ~10 seconds
Attempt 3: ~1 minute
Attempt 4: ~5 minutes
Attempt 5: ~15 minutes
```

The exact timing includes randomized jitter to prevent thundering herd problems.

### Per-step retry counters

Each step maintains its own retry counter. A function with 3 steps and `retries: 4` means each step can fail and retry up to 4 times independently:

```typescript
async ({ event, step }) => {
  // This step can retry up to 4 times
  await step.run("step-a", () => riskyOperation());

  // This step also has 4 retries (independent counter)
  await step.run("step-b", () => anotherRiskyOperation());

  // And this one too
  await step.run("step-c", () => yetAnotherOperation());
};
```

### What triggers a retry

- Any unhandled exception thrown inside `step.run()`
- Network errors during step execution
- Process crashes during execution (Inngest platform detects no response)

### What does NOT trigger a retry

- Returning a value (even `null` or `undefined`)
- Calling `NonRetriableError`
- Errors thrown outside of steps (they run on every invocation anyway)

## NonRetriableError

Use `NonRetriableError` to immediately fail a step without retrying:

```typescript
import { NonRetriableError } from "inngest";

await step.run("validate-input", () => {
  if (!event.data.email) {
    // Immediately fails — no retries
    throw new NonRetriableError("Missing required field: email");
  }

  if (!isValidEmail(event.data.email)) {
    // Also no retries — bad data won't fix itself
    throw new NonRetriableError("Invalid email format", {
      cause: new Error(`Got: ${event.data.email}`),
    });
  }

  return { valid: true };
});
```

### When to use NonRetriableError

- **Validation failures** — Bad input won't change on retry
- **Business rule violations** — Unauthorized actions, quota exceeded
- **Missing resources** — Referenced entity doesn't exist
- **Permanent API errors** — 400, 401, 403, 404 from external APIs

### When NOT to use NonRetriableError

- **Transient failures** — 500, 502, 503, timeout (let Inngest retry)
- **Rate limits** — 429 (retries with backoff will help)
- **Network issues** — Connection resets, DNS failures

## Step-Level Error Handling

### Try/catch within steps

```typescript
async ({ event, step }) => {
  const result = await step.run("call-api", async () => {
    try {
      return await externalApi.process(event.data);
    } catch (err) {
      if (err.status === 404) {
        // Handle known error case — return fallback
        return { status: "not-found", data: null };
      }
      // Re-throw unknown errors to trigger retry
      throw err;
    }
  });

  if (result.status === "not-found") {
    await step.run("handle-missing", () => notifyAdmin(event.data));
  }
};
```

### Try/catch around steps

```typescript
async ({ event, step }) => {
  try {
    await step.run("risky-operation", () => doSomethingRisky());
  } catch (err) {
    // This fires AFTER all retries are exhausted
    await step.run("handle-failure", () => {
      return recordFailure(event.data.id, err.message);
    });
  }
};
```

**Important:** The catch block fires only after all retry attempts for the step are exhausted. It does NOT catch individual retry failures.

## onFailure Handler

The `onFailure` handler is called when a function completely fails (all retries exhausted):

```typescript
const processOrder = inngest.createFunction(
  {
    id: "process-order",
    retries: 4,
    triggers: { event: "order/placed" },
    onFailure: async ({ event, error, step }) => {
      // This runs as a separate function with its own retries
      await step.run("notify-support", async () => {
        await slack.postMessage({
          channel: "#alerts",
          text: `Order processing failed: ${error.message}`,
        });
      });

      await step.run("refund-customer", async () => {
        await stripe.refunds.create({
          payment_intent: event.data.paymentIntentId,
        });
      });

      await step.run("update-order-status", async () => {
        await db.orders.update(event.data.orderId, { status: "failed" });
      });
    },
  },
  async ({ event, step }) => {
    // Main function logic
    await step.run("charge-payment", () =>
      stripe.charges.create({ amount: event.data.total })
    );
  }
);
```

### onFailure handler details

- Runs as a **separate function** with its own retries
- Receives `error` in addition to `event` and `step`
- Has access to all step primitives (run, sleep, etc.)
- The triggering event is `inngest/function.failed`
- Has access to the original function's event data

## Error Patterns

### Retry with fallback

```typescript
async ({ event, step }) => {
  let result;
  try {
    result = await step.run("primary-api", () =>
      primaryApi.fetch(event.data.query)
    );
  } catch {
    result = await step.run("fallback-api", () =>
      fallbackApi.fetch(event.data.query)
    );
  }
  return result;
};
```

### Graceful degradation

```typescript
async ({ event, step }) => {
  const essential = await step.run("essential-operation", () =>
    mustSucceed(event.data)
  );

  // Optional enrichment — catch and continue if it fails
  let enrichment = null;
  try {
    enrichment = await step.run("optional-enrichment", () =>
      enrichData(essential)
    );
  } catch {
    // Log but don't fail the function
  }

  return { ...essential, enrichment };
};
```

### Distinguish error types

```typescript
import { NonRetriableError } from "inngest";

await step.run("api-call", async () => {
  const res = await fetch("https://api.example.com/data");

  switch (res.status) {
    case 200:
      return res.json();
    case 400:
    case 401:
    case 403:
    case 404:
      // Client errors won't fix themselves
      throw new NonRetriableError(`API error: ${res.status}`);
    case 429:
      // Rate limited — throw to trigger retry with backoff
      throw new Error("Rate limited");
    default:
      // Server errors — throw to trigger retry
      throw new Error(`Server error: ${res.status}`);
  }
});
```

## Custom Backoff

While Inngest doesn't expose direct backoff configuration, you can implement custom retry logic:

```typescript
async ({ event, step, attempt }) => {
  await step.run("with-custom-backoff", async () => {
    try {
      return await callApi();
    } catch (err) {
      if (attempt >= 3) {
        throw new NonRetriableError("Max custom retries reached");
      }
      throw err; // Will use Inngest's built-in backoff
    }
  });
};
```

## Python Error Handling

```python
import inngest

@inngest_client.create_function(
    fn_id="process-data",
    trigger=inngest.TriggerEvent(event="data/process"),
    retries=4,
)
async def process_data(ctx: inngest.Context) -> str:
    try:
        result = await ctx.step.run("fetch-data", fetch_external_data)
    except Exception:
        result = await ctx.step.run("fetch-fallback", fetch_fallback_data)

    await ctx.step.run("save-result", lambda: save_to_db(result))
    return "done"


# Non-retriable errors in Python
@inngest_client.create_function(
    fn_id="validate-input",
    trigger=inngest.TriggerEvent(event="input/validate"),
)
async def validate_input(ctx: inngest.Context) -> str:
    data = ctx.event.data

    if "email" not in data:
        raise inngest.NonRetriableError("Missing email field")

    return "valid"
```
