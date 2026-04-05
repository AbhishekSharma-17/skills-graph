# Inngest — TypeScript Patterns

> Source: [inngest.com/docs](https://www.inngest.com/docs)

## Table of Contents

- [Type-Safe Event System](#type-safe-event-system)
- [Zod Schema Integration](#zod-schema-integration)
- [Function Organization](#function-organization)
- [Client Configuration Patterns](#client-configuration-patterns)
- [Advanced Workflow Patterns](#advanced-workflow-patterns)
- [AI Workflow Patterns](#ai-workflow-patterns)
- [Testing Patterns](#testing-patterns)
- [Project Structure](#project-structure)

---

## Type-Safe Event System

### Define events with EventSchemas

```typescript
// src/inngest/events.ts
import { EventSchemas } from "inngest";

export type Events = {
  "user/created": {
    data: {
      userId: string;
      email: string;
      plan: "free" | "pro" | "enterprise";
    };
  };
  "user/updated": {
    data: {
      userId: string;
      changes: Partial<{
        name: string;
        email: string;
        plan: string;
      }>;
    };
  };
  "order/placed": {
    data: {
      orderId: string;
      userId: string;
      items: Array<{ productId: string; quantity: number; price: number }>;
      total: number;
    };
  };
  "email/send": {
    data: {
      to: string;
      template: string;
      variables: Record<string, string>;
    };
  };
};

export const schemas = new EventSchemas().fromRecord<Events>();
```

### Create typed client

```typescript
// src/inngest/client.ts
import { Inngest } from "inngest";
import { schemas } from "./events";

export const inngest = new Inngest({
  id: "my-app",
  schemas,
});
```

### Benefits of typed events

```typescript
// Type-checked event names
await inngest.send({
  name: "user/created", // Autocomplete available
  data: {
    userId: "usr_123",
    email: "user@example.com",
    plan: "pro", // Must be "free" | "pro" | "enterprise"
  },
});

// Type error: 'premium' is not assignable to type '"free" | "pro" | "enterprise"'
await inngest.send({
  name: "user/created",
  data: { userId: "123", email: "a@b.com", plan: "premium" },
});

// Function handlers get typed events
inngest.createFunction(
  { id: "on-user", triggers: { event: "user/created" } },
  async ({ event }) => {
    event.data.userId; // string (typed!)
    event.data.plan;   // "free" | "pro" | "enterprise" (typed!)
  }
);
```

## Zod Schema Integration

### Using eventType helper

```typescript
import { eventType, cron } from "inngest";
import { z } from "zod";

// Define schemas with Zod
export const userCreated = eventType("user/created", {
  schema: z.object({
    userId: z.string().uuid(),
    email: z.string().email(),
    plan: z.enum(["free", "pro", "enterprise"]),
    metadata: z.record(z.string()).optional(),
  }),
});

export const orderPlaced = eventType("order/placed", {
  schema: z.object({
    orderId: z.string(),
    userId: z.string(),
    total: z.number().positive(),
    items: z.array(z.object({
      productId: z.string(),
      quantity: z.number().int().positive(),
      price: z.number().positive(),
    })),
  }),
});

// Use with createFunction
inngest.createFunction(
  {
    id: "process-order",
    triggers: [orderPlaced],
  },
  async ({ event }) => {
    // event.data is fully typed from Zod schema
    const total = event.data.total;
    const items = event.data.items;
  }
);
```

### Runtime validation with middleware

```typescript
import { validationMiddleware } from "@inngest/middleware-validation";

const inngest = new Inngest({
  id: "my-app",
  middleware: [validationMiddleware()],
});

// Events are validated at runtime against Zod schemas
// Invalid events throw before function execution
```

## Function Organization

### Barrel export pattern

```typescript
// src/inngest/functions/index.ts
export { sendWelcomeEmail } from "./user/send-welcome-email";
export { processOrder } from "./order/process-order";
export { dailyCleanup } from "./cron/daily-cleanup";
export { syncInventory } from "./inventory/sync-inventory";

// Re-export all as array for serve()
import { sendWelcomeEmail } from "./user/send-welcome-email";
import { processOrder } from "./order/process-order";
import { dailyCleanup } from "./cron/daily-cleanup";
import { syncInventory } from "./inventory/sync-inventory";

export const allFunctions = [
  sendWelcomeEmail,
  processOrder,
  dailyCleanup,
  syncInventory,
];
```

### Domain-grouped functions

```typescript
// src/inngest/functions/user/send-welcome-email.ts
import { inngest } from "../../client";

export const sendWelcomeEmail = inngest.createFunction(
  {
    id: "user-send-welcome-email",
    triggers: { event: "user/created" },
  },
  async ({ event, step }) => {
    // Implementation
  }
);
```

## Client Configuration Patterns

### Multi-environment setup

```typescript
const inngest = new Inngest({
  id: "my-app",
  // isDev is automatically inferred from INNGEST_DEV env var
  // Signing key from INNGEST_SIGNING_KEY
  // Event key from INNGEST_EVENT_KEY
});
```

### Custom logger

```typescript
import pino from "pino";

const logger = pino({ level: "debug" });

const inngest = new Inngest({
  id: "my-app",
  logger,
});
```

### Multiple Inngest clients

```typescript
// For microservices or multi-app architectures
const userService = new Inngest({ id: "user-service", schemas });
const orderService = new Inngest({ id: "order-service", schemas });

// Each has its own serve endpoint
// /api/inngest/users → serve({ client: userService, functions: [...] })
// /api/inngest/orders → serve({ client: orderService, functions: [...] })
```

## Advanced Workflow Patterns

### Saga pattern (distributed transaction)

```typescript
const processOrderSaga = inngest.createFunction(
  {
    id: "order-saga",
    retries: 0, // Handle failures manually via compensation
    triggers: { event: "order/placed" },
  },
  async ({ event, step }) => {
    // Forward steps
    const reservation = await step.run("reserve-inventory", () =>
      inventory.reserve(event.data.items)
    );

    let payment;
    try {
      payment = await step.run("charge-payment", () =>
        stripe.charges.create({ amount: event.data.total })
      );
    } catch {
      // Compensate: release inventory
      await step.run("compensate-inventory", () =>
        inventory.release(reservation.id)
      );
      throw new NonRetriableError("Payment failed, inventory released");
    }

    try {
      await step.run("confirm-order", () =>
        orders.confirm(event.data.orderId, payment.id)
      );
    } catch {
      // Compensate: refund payment + release inventory
      await step.run("compensate-payment", () =>
        stripe.refunds.create({ charge: payment.id })
      );
      await step.run("compensate-inventory-2", () =>
        inventory.release(reservation.id)
      );
      throw new NonRetriableError("Order confirmation failed, compensated");
    }

    return { status: "completed", orderId: event.data.orderId };
  }
);
```

### Human-in-the-loop

```typescript
const approvalWorkflow = inngest.createFunction(
  {
    id: "approval-workflow",
    triggers: { event: "expense/submitted" },
  },
  async ({ event, step }) => {
    // Notify approver
    await step.run("notify-approver", () =>
      slack.postMessage({
        channel: "#approvals",
        text: `Expense $${event.data.amount} from ${event.data.submitter}`,
      })
    );

    // Wait for approval (up to 7 days)
    const decision = await step.waitForEvent("wait-approval", {
      event: "expense/decision",
      match: "data.expenseId",
      timeout: "7d",
    });

    if (!decision) {
      await step.run("auto-escalate", () =>
        escalateToManager(event.data.expenseId)
      );
      return { status: "escalated" };
    }

    if (decision.data.approved) {
      await step.run("process-reimbursement", () =>
        reimburse(event.data)
      );
      return { status: "approved" };
    }

    await step.run("notify-rejection", () =>
      notifyRejection(event.data.submitter, decision.data.reason)
    );
    return { status: "rejected" };
  }
);
```

### Scheduled drip campaign

```typescript
const dripCampaign = inngest.createFunction(
  {
    id: "onboarding-drip",
    cancelOn: [{ event: "user/unsubscribed", match: "data.userId" }],
    triggers: { event: "user/created" },
  },
  async ({ event, step }) => {
    const emails = [
      { delay: "0s", template: "welcome" },
      { delay: "1d", template: "getting-started" },
      { delay: "3d", template: "tips-and-tricks" },
      { delay: "7d", template: "success-stories" },
      { delay: "14d", template: "upgrade-prompt" },
    ];

    for (const { delay, template } of emails) {
      if (delay !== "0s") {
        await step.sleep(`wait-${template}`, delay);
      }

      await step.run(`send-${template}`, () =>
        sendEmail(event.data.email, template)
      );
    }

    return { emailsSent: emails.length };
  }
);
```

## AI Workflow Patterns

### Multi-step AI pipeline

```typescript
const aiPipeline = inngest.createFunction(
  {
    id: "ai-content-pipeline",
    concurrency: [{ scope: "account", key: `"openai"`, limit: 20 }],
    triggers: { event: "content/generate" },
  },
  async ({ event, step }) => {
    const outline = await step.ai.infer("generate-outline", {
      model: "openai/gpt-4o",
      body: {
        messages: [
          { role: "system", content: "Create a content outline." },
          { role: "user", content: event.data.topic },
        ],
      },
    });

    const sections = await Promise.all(
      parseOutline(outline).map((section, i) =>
        step.ai.infer(`write-section-${i}`, {
          model: "openai/gpt-4o",
          body: {
            messages: [
              { role: "system", content: "Write this section in detail." },
              { role: "user", content: section },
            ],
          },
        })
      )
    );

    const article = await step.run("assemble", () =>
      assembleSections(sections.map(s => s.choices[0].message.content))
    );

    return { article };
  }
);
```

## Testing Patterns

### Unit testing with mocks

```typescript
import { describe, it, expect, vi } from "vitest";

describe("processOrder", () => {
  it("should process order successfully", async () => {
    const mockStep = {
      run: vi.fn()
        .mockResolvedValueOnce({ items: [{ id: "1", stock: 10 }] })
        .mockResolvedValueOnce({ chargeId: "ch_123" })
        .mockResolvedValueOnce({ orderId: "ord_1", status: "confirmed" }),
      sleep: vi.fn().mockResolvedValue(undefined),
    };

    const result = await processOrderHandler({
      event: {
        name: "order/placed",
        data: { orderId: "ord_1", total: 5000 },
      },
      step: mockStep,
    });

    expect(mockStep.run).toHaveBeenCalledTimes(3);
    expect(result).toEqual(expect.objectContaining({ status: "confirmed" }));
  });
});
```

## Project Structure

```
src/
├── inngest/
│   ├── client.ts              # Inngest client with schemas
│   ├── events.ts              # Event type definitions
│   └── functions/
│       ├── index.ts           # Barrel exports + allFunctions array
│       ├── user/
│       │   ├── send-welcome.ts
│       │   └── sync-profile.ts
│       ├── order/
│       │   ├── process-order.ts
│       │   └── send-receipt.ts
│       └── cron/
│           ├── daily-cleanup.ts
│           └── weekly-report.ts
├── app/
│   └── api/
│       └── inngest/
│           └── route.ts       # serve() endpoint
└── lib/
    ├── db.ts
    ├── email.ts
    └── stripe.ts
```
