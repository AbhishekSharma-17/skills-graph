# Inngest — Steps & Workflows

> Source: [inngest.com/docs/features/inngest-functions/steps-workflows](https://www.inngest.com/docs/features/inngest-functions/steps-workflows)

## Table of Contents

- [Step Primitives Overview](#step-primitives-overview)
- [step.run](#steprun)
- [step.sleep](#stepsleep)
- [step.sleepUntil](#stepsleepuntil)
- [step.waitForEvent](#stepwaitforevent)
- [step.invoke](#stepinvoke)
- [step.sendEvent](#stepsendevent)
- [step.ai](#stepai)
- [Building Multi-Step Workflows](#building-multi-step-workflows)
- [Step ID Best Practices](#step-id-best-practices)

---

## Step Primitives Overview

Steps are the building blocks of Inngest workflows. Each step is:
- **Independently retriable** — Failures retry only the failed step
- **Memoized** — Completed steps are not re-executed
- **Checkpointed** — Results persist across function re-invocations

| Primitive | Purpose | Blocks Execution? |
|-----------|---------|-------------------|
| `step.run()` | Execute code with retry | Yes |
| `step.sleep()` | Pause for a duration | Yes (resumes after) |
| `step.sleepUntil()` | Pause until a timestamp | Yes (resumes after) |
| `step.waitForEvent()` | Wait for a matching event | Yes (until event or timeout) |
| `step.invoke()` | Call another Inngest function | Yes (until completion) |
| `step.sendEvent()` | Emit events | No (fire-and-forget) |
| `step.ai()` | Make an AI model call | Yes |

## step.run

Execute a block of code as a retriable, memoized step.

### Signature

```typescript
step.run(id: string, handler: () => T | Promise<T>): Promise<T>
```

### Parameters

| Param | Type | Description |
|-------|------|-------------|
| `id` | `string` | Unique step identifier (appears in logs/dashboard) |
| `handler` | `() => T \| Promise<T>` | Sync or async function to execute |

### Returns
Promise resolving to the handler's return value (JSON-serialized).

### Examples

```typescript
// Async handler
const user = await step.run("fetch-user", async () => {
  return await db.users.findById(event.data.userId);
});

// Synchronous handler
const total = await step.run("calculate-total", () => {
  return items.reduce((sum, item) => sum + item.price, 0);
});

// Handler that may fail (auto-retried)
const response = await step.run("call-api", async () => {
  const res = await fetch("https://api.example.com/data");
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
});
```

### Retry behavior
Each `step.run()` has its own retry counter. With `retries: 4` (default), each step gets up to 5 total attempts (1 initial + 4 retries). Retries use exponential backoff.

## step.sleep

Pause function execution for a specified duration. The function is suspended (no compute used) and resumed after the duration.

### Signature

```typescript
step.sleep(id: string, duration: string): Promise<void>
```

### Duration format

| Format | Example | Duration |
|--------|---------|----------|
| Seconds | `"30s"` | 30 seconds |
| Minutes | `"5m"` | 5 minutes |
| Hours | `"2h"` | 2 hours |
| Days | `"7d"` | 7 days |
| Combined | `"1h30m"` | 1 hour 30 minutes |

### Examples

```typescript
// Wait 5 minutes between steps
await step.run("send-notification", () => sendPush(userId));
await step.sleep("wait-before-followup", "5m");
await step.run("send-followup", () => sendFollowup(userId));

// Multi-day workflow
await step.run("start-trial", () => activateTrial(userId));
await step.sleep("trial-period", "14d");
await step.run("end-trial", () => convertOrExpire(userId));
```

### Important notes
- Sleep duration maximum: depends on your plan (up to 1 year)
- Function consumes zero compute during sleep
- Sleep is checkpointed — server restarts don't affect it

## step.sleepUntil

Pause execution until a specific timestamp.

### Signature

```typescript
step.sleepUntil(id: string, time: string | Date): Promise<void>
```

### Examples

```typescript
// Sleep until a specific ISO timestamp
await step.sleepUntil("wait-for-deadline", "2026-04-10T09:00:00Z");

// Sleep until a date from event data
await step.sleepUntil("wait-for-reminder", event.data.remindAt);

// Sleep until a computed time
const deadline = new Date(event.data.createdAt);
deadline.setHours(deadline.getHours() + 24);
await step.sleepUntil("24h-deadline", deadline);
```

## step.waitForEvent

Pause execution until a matching event is received or a timeout is reached.

### Signature

```typescript
step.waitForEvent(id: string, options: {
  event: string;
  match?: string;
  if?: string;
  timeout: string;
}): Promise<Event | null>
```

### Parameters

| Param | Type | Description |
|-------|------|-------------|
| `event` | `string` | Event name to wait for |
| `match` | `string` | Field path to match between trigger event and incoming event |
| `if` | `string` | CEL expression for conditional matching |
| `timeout` | `string` | Maximum wait duration (e.g., `"1h"`, `"7d"`) |

### Returns
- The matching event payload if received before timeout
- `null` if timeout is reached

### Examples

```typescript
// Wait for user to verify email (up to 24 hours)
const verification = await step.waitForEvent("wait-for-verification", {
  event: "user/email.verified",
  match: "data.userId",  // Match trigger's data.userId with incoming event's data.userId
  timeout: "24h",
});

if (verification) {
  await step.run("activate-account", () => activateUser(event.data.userId));
} else {
  await step.run("send-reminder", () => sendVerificationReminder(event.data.userId));
}

// Wait with conditional matching
const approval = await step.waitForEvent("wait-for-approval", {
  event: "order/approved",
  if: "async.data.orderId == event.data.orderId && event.data.approvedBy != async.data.requestedBy",
  timeout: "48h",
});
```

### Match vs If
- `match` — Simple field equality: `"data.userId"` matches `triggerEvent.data.userId === incomingEvent.data.userId`
- `if` — Complex CEL expression: `async` refers to the trigger event, `event` refers to the incoming event

## step.invoke

Invoke another Inngest function and wait for its result.

### Signature

```typescript
step.invoke(id: string, options: {
  function: InngestFunction;
  data?: Record<string, unknown>;
  timeout?: string;
}): Promise<unknown>
```

### Examples

```typescript
// Invoke another function and use its result
const summary = await step.invoke("generate-summary", {
  function: generateSummaryFn,
  data: { documentId: event.data.docId },
  timeout: "5m",
});

await step.run("save-summary", () => db.summaries.create(summary));
```

### Use cases
- **Composing workflows** — Break complex logic into reusable functions
- **Fan-out** — Invoke the same function with different inputs
- **Cross-app communication** — Invoke functions in other Inngest apps

### Important
- The invoked function must be registered in the same or connected Inngest app
- `step.invoke()` does NOT count against the invoking function's concurrency limit
- Timeout is optional; without it, waits indefinitely for completion

## step.sendEvent

Send one or more events from within a function. Unlike `step.run()`, this is fire-and-forget.

### Signature

```typescript
step.sendEvent(id: string, events: Event | Event[]): Promise<void>
```

### Examples

```typescript
// Send a single event
await step.sendEvent("notify-complete", {
  name: "processing/complete",
  data: { resultId: result.id },
});

// Send multiple events (fan-out)
await step.sendEvent("fan-out-tasks", users.map(user => ({
  name: "user/process-batch",
  data: { userId: user.id },
})));
```

## step.ai

Make an AI model call with built-in retry and cost tracking.

### Signature

```typescript
step.ai.infer(id: string, options: {
  model: string;
  body: {
    messages: Array<{ role: string; content: string }>;
    max_tokens?: number;
    temperature?: number;
  };
}): Promise<AIResponse>
```

### Example

```typescript
const response = await step.ai.infer("classify-ticket", {
  model: "openai/gpt-4o",
  body: {
    messages: [
      { role: "system", content: "Classify the support ticket priority." },
      { role: "user", content: event.data.ticketBody },
    ],
    max_tokens: 100,
  },
});

await step.run("update-ticket", () => {
  return db.tickets.update(event.data.ticketId, {
    priority: response.choices[0].message.content,
  });
});
```

## Building Multi-Step Workflows

### Sequential workflow

```typescript
const processOrder = inngest.createFunction(
  { id: "process-order", triggers: { event: "order/placed" } },
  async ({ event, step }) => {
    const order = await step.run("validate-order", () =>
      validateOrder(event.data.orderId)
    );

    const payment = await step.run("charge-payment", () =>
      stripe.charges.create({ amount: order.total, customer: order.customerId })
    );

    await step.run("update-inventory", () =>
      updateInventory(order.items)
    );

    await step.run("send-confirmation", () =>
      sendOrderConfirmation(order, payment)
    );

    await step.sleep("wait-for-delivery", "3d");

    await step.run("request-review", () =>
      sendReviewRequest(order.customerId, order.id)
    );

    return { orderId: order.id, status: "complete" };
  }
);
```

### Conditional workflow

```typescript
const handlePayment = inngest.createFunction(
  { id: "handle-payment", triggers: { event: "payment/received" } },
  async ({ event, step }) => {
    const amount = event.data.amount;

    if (amount > 10000) {
      const approval = await step.waitForEvent("wait-approval", {
        event: "payment/approved",
        match: "data.paymentId",
        timeout: "48h",
      });

      if (!approval) {
        await step.run("flag-for-review", () =>
          flagPayment(event.data.paymentId)
        );
        return { status: "pending-review" };
      }
    }

    await step.run("process-payment", () =>
      processPayment(event.data.paymentId)
    );
    return { status: "processed" };
  }
);
```

## Step ID Best Practices

```typescript
// DO: Descriptive, kebab-case
await step.run("fetch-user-profile", handler);
await step.run("send-welcome-email", handler);
await step.run("update-subscription-status", handler);

// DO: Deterministic dynamic IDs based on input
for (const item of order.items) {
  await step.run(`process-item-${item.id}`, () => processItem(item));
}

// DON'T: Non-deterministic IDs
await step.run(`step-${Date.now()}`, handler);      // Changes every run
await step.run(`step-${Math.random()}`, handler);    // Changes every run

// DON'T: Duplicate IDs in the same function
await step.run("fetch-data", fetchUsers);
await step.run("fetch-data", fetchOrders); // ERROR: duplicate step ID
```
