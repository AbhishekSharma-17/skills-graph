# Inngest — Middleware

> Source: [inngest.com/docs/features/middleware](https://www.inngest.com/docs/features/middleware)

## Table of Contents

- [Overview](#overview)
- [Creating Middleware](#creating-middleware)
- [Lifecycle Hooks](#lifecycle-hooks)
- [Client-Level Middleware](#client-level-middleware)
- [Function-Level Middleware](#function-level-middleware)
- [Built-In Middleware](#built-in-middleware)
- [Common Patterns](#common-patterns)
- [Python Middleware](#python-middleware)

---

## Overview

Middleware lets you run code at specific points during the Inngest function lifecycle. Use cases:

- **Observability** — Add tracing, logging, and metrics
- **Dependency injection** — Share client instances across functions
- **Encryption** — Encrypt/decrypt event data and step outputs
- **Error tracking** — Report errors to Sentry, Datadog, etc.
- **Authentication** — Validate context before function execution

## Creating Middleware

### TypeScript middleware

```typescript
import { InngestMiddleware } from "inngest";

const loggingMiddleware = new InngestMiddleware({
  name: "Logging Middleware",
  init() {
    return {
      onFunctionRun({ fn, ctx }) {
        const startTime = Date.now();
        console.log(`[${fn.id}] Started`, { runId: ctx.runId });

        return {
          afterExecution() {
            const duration = Date.now() - startTime;
            console.log(`[${fn.id}] Completed in ${duration}ms`);
          },
          onError({ error }) {
            console.error(`[${fn.id}] Failed:`, error.message);
          },
        };
      },
    };
  },
});
```

### Middleware structure

```typescript
new InngestMiddleware({
  name: string;          // Identifier for debugging
  init(options?) {       // Called once when middleware is registered
    return {
      onFunctionRun({ fn, ctx }) {   // Called for each function execution
        // Setup logic here
        return {
          transformInput({ ctx }) {},       // Before function handler
          beforeMemoization() {},           // Before step memoization
          afterMemoization() {},            // After step memoization
          beforeExecution() {},             // Before step execution
          afterExecution() {},              // After step execution
          transformOutput({ result }) {},   // Transform function output
          onError({ error }) {},            // On any error
        };
      },
      onSendEvent() {    // Called when events are sent
        return {
          transformInput({ payloads }) {},  // Transform outgoing events
          transformOutput({ result }) {},   // After events sent
        };
      },
    };
  },
});
```

## Lifecycle Hooks

### Function execution hooks

| Hook | When | Use For |
|------|------|---------|
| `onFunctionRun` | Function invoked | Setup, context creation |
| `transformInput` | Before handler called | Modify context, inject deps |
| `beforeMemoization` | Before checking step cache | Tracing setup |
| `afterMemoization` | After step cache check | Log memoization results |
| `beforeExecution` | Before step code runs | Start span/timer |
| `afterExecution` | After step code completes | End span/timer, log result |
| `transformOutput` | Before returning result | Transform/encrypt output |
| `onError` | On any error | Error reporting |

### Event sending hooks

| Hook | When | Use For |
|------|------|---------|
| `onSendEvent` | Event send initiated | Setup |
| `transformInput` | Before sending | Encrypt/modify events |
| `transformOutput` | After sending | Log confirmation |

## Client-Level Middleware

Register middleware on the Inngest client to apply to all functions:

```typescript
import { Inngest } from "inngest";

const inngest = new Inngest({
  id: "my-app",
  middleware: [loggingMiddleware, sentryMiddleware, encryptionMiddleware],
});
```

### Execution order

Client middleware executes in **descending** registration order:
```
Registered: [A, B, C]
Execution:  C → B → A (last registered runs first)
```

## Function-Level Middleware

Apply middleware to specific functions only:

```typescript
const sensitiveFunction = inngest.createFunction(
  {
    id: "process-pii",
    middleware: [encryptionMiddleware], // Only this function
    triggers: { event: "pii/process" },
  },
  async ({ event, step }) => { /* ... */ }
);
```

Function middleware executes after client middleware, also in descending order.

## Built-In Middleware

### Encryption middleware

Encrypt event data and step outputs:

```typescript
import { encryptionMiddleware } from "@inngest/middleware-encryption";

const inngest = new Inngest({
  id: "my-app",
  middleware: [
    encryptionMiddleware({
      key: process.env.INNGEST_ENCRYPTION_KEY!,
    }),
  ],
});
```

Features:
- Encrypts event data before sending to Inngest
- Decrypts event data when function receives it
- Encrypts step outputs before storage
- Decrypts step outputs during memoization

### Sentry middleware

```typescript
import { sentryMiddleware } from "@inngest/middleware-sentry";
import * as Sentry from "@sentry/node";

const inngest = new Inngest({
  id: "my-app",
  middleware: [sentryMiddleware(Sentry)],
});
```

### Validation middleware

Validate event payloads on send:

```typescript
import { validationMiddleware } from "@inngest/middleware-validation";

const inngest = new Inngest({
  id: "my-app",
  middleware: [validationMiddleware()],
});
```

## Common Patterns

### Dependency injection

```typescript
const dbMiddleware = new InngestMiddleware({
  name: "Database Middleware",
  init() {
    // Create shared connection pool once
    const pool = createPool(process.env.DATABASE_URL);

    return {
      onFunctionRun() {
        return {
          transformInput({ ctx }) {
            // Inject database client into context
            return {
              ctx: { ...ctx, db: pool },
            };
          },
        };
      },
    };
  },
});

// Usage in functions
async ({ event, step, db }) => {
  const user = await step.run("get-user", () =>
    db.query("SELECT * FROM users WHERE id = $1", [event.data.userId])
  );
};
```

### OpenTelemetry tracing

```typescript
import { trace, SpanStatusCode } from "@opentelemetry/api";

const tracingMiddleware = new InngestMiddleware({
  name: "OpenTelemetry Tracing",
  init() {
    const tracer = trace.getTracer("inngest");

    return {
      onFunctionRun({ fn, ctx }) {
        const span = tracer.startSpan(`inngest.${fn.id}`, {
          attributes: {
            "inngest.function_id": fn.id,
            "inngest.run_id": ctx.runId,
            "inngest.event_name": ctx.event.name,
          },
        });

        return {
          afterExecution() {
            span.setStatus({ code: SpanStatusCode.OK });
            span.end();
          },
          onError({ error }) {
            span.setStatus({
              code: SpanStatusCode.ERROR,
              message: error.message,
            });
            span.recordException(error);
            span.end();
          },
        };
      },
    };
  },
});
```

### Request timing

```typescript
const timingMiddleware = new InngestMiddleware({
  name: "Timing Middleware",
  init() {
    return {
      onFunctionRun({ fn }) {
        const start = performance.now();

        return {
          afterExecution() {
            const duration = performance.now() - start;
            metrics.histogram("inngest.function.duration", duration, {
              function: fn.id,
            });
          },
        };
      },
    };
  },
});
```

## Python Middleware

```python
import inngest

class LoggingMiddleware(inngest.Middleware):
    def __init__(self) -> None:
        super().__init__()

    async def before_execution(self) -> None:
        print(f"Function starting: {self.fn_id}")

    async def after_execution(self) -> None:
        print(f"Function completed: {self.fn_id}")

    async def on_error(self, error: Exception) -> None:
        print(f"Function failed: {self.fn_id} - {error}")


inngest_client = inngest.Inngest(
    app_id="my-app",
    middleware=[LoggingMiddleware],
)
```
