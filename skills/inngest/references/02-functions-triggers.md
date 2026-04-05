# Inngest — Functions & Triggers

> Source: [inngest.com/docs/reference/functions/create](https://www.inngest.com/docs/reference/functions/create)

## Table of Contents

- [createFunction API](#createfunction-api)
- [Function Configuration](#function-configuration)
- [Event Triggers](#event-triggers)
- [Cron Triggers](#cron-triggers)
- [Multiple Triggers](#multiple-triggers)
- [Type-Safe Events](#type-safe-events)
- [Handler Arguments](#handler-arguments)
- [Sending Events](#sending-events)
- [Event Payload Format](#event-payload-format)
- [Webhook Triggers](#webhook-triggers)

---

## createFunction API

```typescript
inngest.createFunction(config, handler): InngestFunction
```

### Basic example

```typescript
import { inngest } from "./client";

export const myFunction = inngest.createFunction(
  {
    id: "process-payment",
    triggers: { event: "payment/created" },
  },
  async ({ event, step }) => {
    // Function logic
    return { success: true };
  }
);
```

## Function Configuration

The first argument to `createFunction` is the configuration object:

```typescript
{
  // Required
  id: string;              // Unique, stable identifier
  triggers: Trigger | Trigger[];  // What invokes this function

  // Optional display
  name?: string;           // Human-readable name for dashboard

  // Optional retry behavior
  retries?: number;        // 0-20, default: 4

  // Optional flow control (see 06-flow-control.md)
  concurrency?: number | ConcurrencyConfig[];
  throttle?: ThrottleConfig;
  debounce?: DebounceConfig;
  rateLimit?: RateLimitConfig;
  priority?: PriorityConfig;

  // Optional batching (see 07-event-batching.md)
  batchEvents?: BatchConfig;

  // Optional cancellation (see 08-cancellation.md)
  cancelOn?: CancelConfig[];

  // Optional failure handler
  onFailure?: FailureHandler;
}
```

### Configuration options reference

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `id` | `string` | required | Unique function identifier (do not change after deploy) |
| `name` | `string` | — | Display name in dashboard |
| `triggers` | `Trigger \| Trigger[]` | required | Event names, cron expressions, or typed triggers |
| `retries` | `number` | `4` | Retry attempts per step (0-20) |
| `concurrency` | `number \| object[]` | — | Limit concurrent step executions |
| `throttle` | `object` | — | Rate-limit function starts over time |
| `debounce` | `object` | — | Delay execution with sliding window |
| `rateLimit` | `object` | — | Skip events beyond frequency limit |
| `batchEvents` | `object` | — | Process multiple events per run |
| `cancelOn` | `object[]` | — | Cancel running functions on events |
| `onFailure` | `function` | — | Handler called after all retries exhausted |

## Event Triggers

### Simple event trigger

```typescript
inngest.createFunction(
  {
    id: "on-user-created",
    triggers: { event: "user/created" },
  },
  async ({ event, step }) => {
    // event.name === "user/created"
    // event.data contains the payload
  }
);
```

### Event trigger with filter expression

```typescript
inngest.createFunction(
  {
    id: "on-premium-signup",
    triggers: {
      event: "user/created",
      if: "event.data.plan == 'premium'",
    },
  },
  async ({ event, step }) => {
    // Only fires for premium users
  }
);
```

### Typed event trigger (with Zod)

```typescript
import { eventType } from "inngest";
import { z } from "zod";

const userCreated = eventType("user/created", {
  schema: z.object({
    userId: z.string(),
    email: z.string().email(),
    plan: z.enum(["free", "pro", "enterprise"]),
  }),
});

inngest.createFunction(
  {
    id: "on-user-created",
    triggers: [userCreated],
  },
  async ({ event, step }) => {
    // event.data is fully typed: { userId: string, email: string, plan: "free" | "pro" | "enterprise" }
  }
);
```

## Cron Triggers

### Basic cron

```typescript
inngest.createFunction(
  {
    id: "daily-cleanup",
    triggers: { cron: "0 2 * * *" }, // Every day at 2 AM UTC
  },
  async ({ step }) => {
    await step.run("cleanup-expired", async () => {
      return await db.sessions.deleteExpired();
    });
  }
);
```

### Cron with helper

```typescript
import { cron } from "inngest";

inngest.createFunction(
  {
    id: "weekly-report",
    triggers: [cron("0 9 * * 1")], // Mondays at 9 AM
  },
  async ({ step }) => {
    await step.run("generate-report", () => generateWeeklyReport());
  }
);
```

### Common cron expressions

| Expression | Schedule |
|-----------|----------|
| `* * * * *` | Every minute |
| `*/5 * * * *` | Every 5 minutes |
| `0 * * * *` | Every hour |
| `0 0 * * *` | Daily at midnight |
| `0 9 * * 1-5` | Weekdays at 9 AM |
| `0 0 1 * *` | First of each month |
| `0 */6 * * *` | Every 6 hours |

## Multiple Triggers

A single function can respond to multiple events or combine event and cron triggers:

```typescript
inngest.createFunction(
  {
    id: "sync-user-data",
    triggers: [
      { event: "user/updated" },
      { event: "user/profile.changed" },
      { cron: "0 */4 * * *" }, // Also run every 4 hours
    ],
  },
  async ({ event, step }) => {
    // event.name tells you which trigger fired
    if (event.name === "inngest/scheduled.timer") {
      // Cron trigger
    } else {
      // Event trigger (user/updated or user/profile.changed)
    }
  }
);
```

## Type-Safe Events

### Define event types globally

```typescript
// src/inngest/client.ts
import { Inngest, EventSchemas } from "inngest";

type Events = {
  "user/created": {
    data: { userId: string; email: string; plan: string };
  };
  "user/updated": {
    data: { userId: string; changes: Record<string, unknown> };
  };
  "order/placed": {
    data: { orderId: string; total: number; items: string[] };
  };
};

export const inngest = new Inngest({
  id: "my-app",
  schemas: new EventSchemas().fromRecord<Events>(),
});
```

Now all functions and `inngest.send()` calls are fully typed:

```typescript
// Type error: 'nonexistent/event' not in Events
inngest.createFunction(
  { id: "bad", triggers: { event: "nonexistent/event" } },
  async () => {}
);

// Type error: missing 'email' in data
await inngest.send({
  name: "user/created",
  data: { userId: "123" }, // TS error: Property 'email' is missing
});
```

## Handler Arguments

The handler function receives a single object with these properties:

```typescript
async ({
  event,    // The triggering event payload
  events,   // Array of events (when using batchEvents)
  step,     // Step methods: run, sleep, sleepUntil, waitForEvent, invoke, sendEvent
  runId,    // Unique identifier for this function run
  logger,   // Structured logger (info, warn, error, debug)
  attempt,  // Zero-indexed retry attempt number
}) => {
  // ...
}
```

### event structure

```typescript
{
  name: "user/created",        // Event name
  data: { userId: "123" },     // Your payload
  user: {},                    // Optional user context
  ts: 1712345678000,           // Timestamp (ms since epoch)
  id: "evt_01abc...",          // Unique event ID
}
```

### logger

```typescript
async ({ logger, step }) => {
  logger.info("Function started", { runId });
  logger.warn("Slow response", { latency: 5000 });
  logger.error("Payment failed", { error: err.message });
  logger.debug("Step data", { data });
};
```

## Sending Events

### Single event

```typescript
await inngest.send({
  name: "user/signup.completed",
  data: { userId: "usr_123", email: "user@example.com" },
});
```

### Multiple events (batch)

```typescript
await inngest.send([
  { name: "order/item.shipped", data: { orderId: "ord_1", itemId: "item_a" } },
  { name: "order/item.shipped", data: { orderId: "ord_1", itemId: "item_b" } },
  { name: "order/item.shipped", data: { orderId: "ord_1", itemId: "item_c" } },
]);
```

### From within a step

```typescript
await step.sendEvent("notify-downstream", {
  name: "processing/complete",
  data: { resultUrl: "https://..." },
});
```

## Event Payload Format

```typescript
interface InngestEvent {
  name: string;                    // Required: event name (e.g., "user/created")
  data: Record<string, unknown>;   // Required: event payload
  user?: Record<string, unknown>;  // Optional: user context
  ts?: number;                     // Optional: timestamp (ms), defaults to now
  id?: string;                     // Optional: idempotency key
  v?: string;                      // Optional: schema version
}
```

### Event naming conventions

```
<domain>/<noun>.<verb>

Examples:
  user/signup.completed
  order/payment.failed
  email/delivery.bounced
  file/upload.started
  ai/generation.completed
```

## Webhook Triggers

Inngest can receive events from external webhook sources:

### Built-in webhook URL

Each Inngest app has a webhook endpoint. External services send POST requests to:

```
https://inn.gs/e/<event-key>
```

### Webhook event format

```bash
curl -X POST https://inn.gs/e/your-event-key \
  -H "Content-Type: application/json" \
  -d '{
    "name": "webhook/stripe.charge.succeeded",
    "data": {
      "chargeId": "ch_123",
      "amount": 5000
    }
  }'
```

### Transform webhooks

For third-party webhooks that don't match Inngest's format, use webhook transforms in the Inngest dashboard to map incoming payloads to the expected event structure.
