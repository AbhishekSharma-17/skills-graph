# Upstash Workflow — Durable Serverless Functions

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Basic Setup — Next.js](#basic-setup--nextjs)
- [Serve Function](#serve-function)
- [Context Methods](#context-methods)
  - [context.run](#contextrunstepname-handler)
  - [context.sleep](#contextsleepstepname-seconds)
  - [context.sleepUntil](#contextsleepuntilstepname-unixtimestamp)
  - [context.call](#contextcallstepname-options)
  - [context.invoke](#contextinvokestepname-options)
  - [context.waitForEvent](#contextwaitforeventstepname-eventid-options)
  - [context.notify](#contextnotifyeventid-data)
- [Parallel Steps](#parallel-steps)
- [Error Handling](#error-handling)
- [Workflow Client](#workflow-client)
- [createWorkflow and serveMany](#createworkflow-and-servemany)
- [Flow Control](#flow-control)
- [Local Development](#local-development)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

Upstash Workflow provides durable serverless functions by breaking long-running processes into discrete steps, each executed as a separate HTTP request with automatic retries.

Key characteristics:

- **Step-based execution** — every step runs in its own HTTP invocation
- **Automatic retries** — failed steps retry individually; completed step state is preserved
- **Long delays** — sleep durations of days, weeks, or months
- **Built on QStash** — reliable step-to-step message delivery with at-least-once guarantees (failed messages go to DLQ)
- **Framework agnostic** — Next.js, Express, Hono, Cloudflare Workers, SvelteKit, Astro, SolidStart, H3

---

## Installation

**TypeScript / JavaScript:**

```bash
npm install @upstash/workflow
```

**Python:**

```bash
pip install upstash-workflow
```

---

## Environment Variables

| Variable                | Required | Description                                                    |
| ----------------------- | -------- | -------------------------------------------------------------- |
| `QSTASH_TOKEN`          | Yes      | Authentication token from the Upstash Console QStash dashboard |
| `UPSTASH_WORKFLOW_URL`  | No       | Override endpoint URL; used for local development              |

The `QSTASH_TOKEN` authenticates your workflow with QStash, which handles all inter-step message delivery. Obtain it from the Upstash Console under the QStash section.

---

## Basic Setup — Next.js

A minimal workflow that fetches a user, waits one day, then sends a follow-up email:

```typescript
import { serve } from "@upstash/workflow/nextjs";

export const { POST } = serve<{ email: string }>(async (context) => {
  const { email } = context.requestPayload;

  // Step 1: Fetch user from database
  const user = await context.run("fetch-user", async () => {
    return await db.users.findByEmail(email);
  });

  // Step 2: Wait 24 hours
  await context.sleep("wait-1-day", 60 * 60 * 24);

  // Step 3: Send follow-up email
  await context.run("send-followup", async () => {
    await sendEmail(user.email, "How's it going?");
  });
});
```

Each `context.run` call is a separate HTTP request. If the email send fails, only step 3 retries — the user fetch and sleep do not re-execute.

---

## Serve Function

The `serve` function is the entry point for creating a workflow endpoint. It wraps your handler and manages step execution, state persistence, and retry logic.

```typescript
import { serve } from "@upstash/workflow/nextjs";

const { POST } = serve(handler, options?);
```

**Framework-specific imports:** `@upstash/workflow/nextjs`, `@upstash/workflow/cloudflare-workers`, `@upstash/workflow/hono`, `@upstash/workflow/express`, `@upstash/workflow/h3`, `@upstash/workflow/solidstart`, `@upstash/workflow/sveltekit`, `@upstash/workflow/astro`.

**Options:**

| Option             | Type                                                   | Default | Description                                          |
| ------------------ | ------------------------------------------------------ | ------- | ---------------------------------------------------- |
| `retries`          | `number`                                               | `3`     | Number of retry attempts per step                    |
| `failureUrl`       | `string`                                               | —       | URL to POST to when the workflow permanently fails   |
| `failureFunction`  | `(context, failStatus, failResponse) => void`          | —       | Callback invoked on permanent failure                |
| `flowControl`      | `{ key, ratePerSecond, parallelism }`                  | —       | Rate limiting and concurrency control                |
| `env`              | `object`                                               | —       | Environment variables (required for Cloudflare Workers) |
| `baseUrl`          | `string`                                               | —       | Override the workflow endpoint URL                   |

```typescript
export const { POST } = serve(
  async (context) => {
    // workflow steps
  },
  {
    retries: 5,
    failureUrl: "https://your-app.com/api/workflow-failed",
    flowControl: {
      key: "onboarding",
      ratePerSecond: 10,
      parallelism: 5,
    },
  }
);
```

---

## Context Methods

The `context` object is the primary interface for defining workflow steps. Each method creates a discrete step in the workflow execution graph.

### context.run(stepName, handler)

Execute a step with automatic retry and state persistence. This is the fundamental building block of every workflow.

```typescript
const result = await context.run("step-name", async () => {
  // This code runs in its own HTTP request
  // The return value is serialized and stored
  return await fetchData();
});

// `result` is available in all subsequent steps
```

Key behaviors: each step runs as a separate HTTP request; return values are JSON-serialized and persisted by QStash; on retry only the failed step re-executes (completed steps return stored results); step names must be unique within a workflow.

### context.sleep(stepName, seconds)

Pause workflow execution for a specified duration. The sleep is handled by QStash, not your serverless function — your function is not running or consuming resources during the sleep.

```typescript
await context.sleep("wait-1-day", 60 * 60 * 24);      // 24 hours
await context.sleep("wait-1-week", 60 * 60 * 24 * 7);  // 1 week
```

Sleeps can span days, weeks, or months. QStash schedules the next step delivery after the duration elapses — your function consumes no resources during the wait.

### context.sleepUntil(stepName, unixTimestamp)

Pause workflow execution until a specific point in time, specified as a Unix timestamp in seconds.

```typescript
const trialEnd = user.trialStartedAt + 14 * 24 * 60 * 60; // 14 days from trial start
await context.sleepUntil("wait-for-trial-end", trialEnd);
```

### context.call(stepName, options)

Make an HTTP call without consuming your serverless function's execution time. The HTTP request is performed by QStash infrastructure, and the result is delivered back to your workflow as the next step.

```typescript
const { status, header, body } = await context.call<ResponseType>(
  "call-external-api",
  {
    url: "https://api.example.com/data",
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer token",
    },
    body: JSON.stringify({ key: "value" }),
    retries: 3,
  }
);
```

Critical for long-running HTTP requests (AI inference, file processing) that would exceed your serverless timeout. QStash supports call timeouts from 15 minutes up to 2 hours.

### context.invoke(stepName, options)

Start a sub-workflow (another workflow defined with `serve` or `createWorkflow`) and wait for its result. This enables composing complex workflows from smaller, reusable pieces.

```typescript
const paymentResult = await context.invoke("process-payment", {
  workflow: paymentWorkflow,
  body: { orderId, amount: order.total },
});
```

### context.waitForEvent(stepName, eventId, options?)

Pause workflow execution and wait for an external event notification. The workflow remains suspended (consuming no resources) until the event arrives or the timeout expires.

```typescript
const { eventData, timeout } = await context.waitForEvent(
  "wait-for-approval",
  "approval-event-123",
  { timeout: "7d" } // Wait up to 7 days
);

if (timeout) {
  await context.run("handle-timeout", async () => {
    await notifyAdmin("Approval timed out for request 123");
  });
} else {
  await context.run("process-approval", async () => {
    await processApproval(eventData);
  });
}
```

The `timeout` option accepts duration strings like `"7d"`, `"24h"`, `"30m"`. If the timeout elapses before an event arrives, `timeout` is `true` and `eventData` is `undefined`.

### context.notify(eventId, data)

Send an event to a waiting workflow from outside the workflow. Use the `Client` class to notify from API routes, webhooks, or other services.

```typescript
import { Client } from "@upstash/workflow";
const client = new Client({ token: process.env.QSTASH_TOKEN! });

await client.notify({
  eventId: "approval-event-123",
  eventData: { approved: true, approver: "admin@company.com" },
});
```

---

## Parallel Steps

Run multiple steps concurrently using `Promise.all`. Each step still executes as its own HTTP request, but QStash dispatches them in parallel rather than sequentially.

```typescript
const [userData, orderData, analyticsData] = await Promise.all([
  context.run("fetch-user", () => fetchUser(userId)),
  context.run("fetch-orders", () => fetchOrders(userId)),
  context.run("fetch-analytics", () => fetchAnalytics(userId)),
]);

// All three results are available here
await context.run("generate-report", async () => {
  return buildReport(userData, orderData, analyticsData);
});
```

Parallel steps are independent — if one fails and retries, the others are not affected.

---

## Error Handling

Configure retry behavior and failure callbacks at the workflow level.

```typescript
export const { POST } = serve(
  async (context) => {
    const data = await context.run("risky-step", async () => {
      const response = await fetch("https://unreliable-api.com/data");
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
      return response.json();
    });

    await context.run("process-data", async () => {
      await processData(data);
    });
  },
  {
    retries: 5,
    failureFunction: async (context, failStatus, failResponse) => {
      console.error(`Workflow failed with status ${failStatus}`);
      await notifyAdmin(`Workflow permanently failed: ${failResponse}`);
    },
  }
);
```

Retry and failure behavior: failed steps retry with exponential backoff up to `retries` times; exhausted retries move the message to the Dead Letter Queue (DLQ); the `failureFunction` fires on permanent failure. Alternatively, use `failureUrl` to POST failure details to a separate endpoint.

---

## Workflow Client

The `Client` class provides programmatic control over workflows from outside the workflow handler — trigger runs, cancel active workflows, query logs, and manage events.

```typescript
import { Client } from "@upstash/workflow";

const client = new Client({ token: process.env.QSTASH_TOKEN! });
```

**Trigger a workflow:**

```typescript
const { workflowRunId } = await client.trigger({
  url: "https://your-app.com/api/workflow",
  body: { userId: "123", action: "onboard" },
  headers: { "x-custom-header": "value" },
});
```

**Cancel workflows:**

```typescript
// Cancel by specific run IDs
await client.cancel({ ids: ["workflow-run-id-1", "workflow-run-id-2"] });

// Cancel all workflows matching a URL prefix
await client.cancel({
  urlStartingWith: "https://your-app.com/api/onboarding",
});
```

**Query logs and event waiters:**

```typescript
const failedLogs = await client.logs({ state: "FAILED" });
const activeLogs = await client.logs({ state: "ACTIVE" });
const waiters = await client.getWaiters({ eventId: "approval-event-123" });
```

---

## createWorkflow and serveMany

Define multiple workflows in a single file and serve them from one endpoint.

```typescript
import { createWorkflow, serveMany } from "@upstash/workflow/nextjs";

const emailWorkflow = createWorkflow<{ email: string }>(async (context) => {
  const { email } = context.requestPayload;
  await context.run("send-email", async () => { await sendEmail(email); });
});

const paymentWorkflow = createWorkflow<{ orderId: string; amount: number }>(async (context) => {
  const { orderId, amount } = context.requestPayload;
  await context.run("charge", async () => { return await stripe.charges.create({ amount, currency: "usd" }); });
});

export const { POST } = serveMany({
  "/api/email": emailWorkflow,
  "/api/payment": paymentWorkflow,
});
```

Each workflow gets its own path and can be triggered independently via the `Client`.

---

## Flow Control

Flow control limits the rate and concurrency of workflow executions sharing the same key. This prevents overwhelming downstream services or exceeding API rate limits.

```typescript
export const { POST } = serve(handler, {
  flowControl: {
    key: "my-workflow",        // Shared key for grouping
    ratePerSecond: 10,         // Max 10 new executions per second
    parallelism: 5,            // Max 5 concurrent workflow runs
  },
});
```

Multiple workflow endpoints can share the same `key` to enforce a global rate limit across all of them.

---

## Local Development

**Dev Server approach (recommended):** Start your app locally, then set `UPSTASH_WORKFLOW_URL=http://localhost:3000/api/workflow`. The dev server intercepts step completions and delivers them locally — no public URL, QStash token, or internet required.

**Tunnel approach (alternative):** Expose your local server via ngrok and set `baseUrl` in serve options:

```typescript
export const { POST } = serve(handler, {
  baseUrl: "https://your-tunnel-url.ngrok.io",
});
```

---

## Common Pitfalls

**Steps must be deterministic.** Do not use `Math.random()`, `Date.now()`, or `crypto.randomUUID()` inside `context.run`. The engine replays step definitions to reconstruct state — non-deterministic steps produce inconsistent results. Generate such values before passing them into the workflow payload.

**Step names must be unique.** Duplicate names across `context.run`, `context.sleep`, `context.call`, `context.waitForEvent` cause the engine to confuse step results.

**Return values must be JSON-serializable.** Functions, class instances, circular references, `Map`, `Set`, and `Date` objects will not survive serialization. Return plain objects, arrays, strings, numbers, and booleans.

**No side effects outside steps.** Code outside of `context.run()` executes on every HTTP request to your endpoint (once per step). Side effects like database writes, API calls, or sending emails must always be inside a `context.run` block to ensure they only execute once.

```typescript
// WRONG: This sends an email on every step replay
await sendEmail(user.email, "Welcome!");
await context.run("next-step", async () => { ... });

// CORRECT: Side effect inside a step
await context.run("send-welcome", async () => {
  await sendEmail(user.email, "Welcome!");
});
```

**Step handlers should be idempotent.** Retries may re-execute a step — use idempotency keys for charges, upserts for DB writes, and deduplication for messages.

**Workflow endpoint must be publicly accessible** in production. QStash delivers step results via HTTP POST. For local dev, use the workflow dev server or a tunnel.

**Single-step execution time limits still apply.** Each step runs in one serverless invocation (e.g., 10s on Vercel Hobby, 60s on Pro). For long HTTP requests, use `context.call` to offload to QStash.
