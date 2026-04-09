# Functions: Actions & HTTP Endpoints

> Source: [docs.convex.dev/functions/actions](https://docs.convex.dev/functions/actions) | convex v1.34.x

## Table of Contents

- [Actions Overview](#actions-overview)
- [Action Context](#action-context)
- [Calling External APIs](#calling-external-apis)
- [Running Queries and Mutations from Actions](#running-queries-and-mutations-from-actions)
- [Runtime Selection](#runtime-selection)
- [HTTP Actions](#http-actions)
- [HTTP Routing](#http-routing)
- [CORS Handling](#cors-handling)
- [Webhook Patterns](#webhook-patterns)
- [Common Pitfalls](#common-pitfalls)

## Actions Overview

Actions handle side effects — external API calls, sending emails, processing payments. Unlike queries and mutations, actions are **not transactional** and **not automatically retried**.

```typescript
import { action } from "./_generated/server";
import { v } from "convex/values";

export const sendEmail = action({
  args: { to: v.string(), subject: v.string(), body: v.string() },
  handler: async (ctx, args) => {
    const response = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${process.env.RESEND_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        from: "app@example.com",
        to: args.to,
        subject: args.subject,
        html: args.body,
      }),
    });
    if (!response.ok) throw new Error("Failed to send email");
    return { sent: true };
  },
});
```

## Action Context

The `ctx` object in actions provides:

```typescript
ctx.runQuery(ref, args)     // Run a query
ctx.runMutation(ref, args)  // Run a mutation
ctx.runAction(ref, args)    // Run another action (use sparingly)
ctx.auth                    // Authentication info
ctx.storage                 // File storage
ctx.scheduler               // Schedule functions
ctx.vectorSearch(table, index, query)  // Vector similarity search
```

**Key difference from queries/mutations:** Actions cannot access `ctx.db` directly. All database operations go through `ctx.runQuery` and `ctx.runMutation`.

## Calling External APIs

Actions have full `fetch` support:

```typescript
export const createStripeCheckout = action({
  args: { priceId: v.string(), userId: v.id("users") },
  handler: async (ctx, args) => {
    const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

    const session = await stripe.checkout.sessions.create({
      mode: "payment",
      line_items: [{ price: args.priceId, quantity: 1 }],
      success_url: "https://example.com/success",
      cancel_url: "https://example.com/cancel",
    });

    // Store the session ID in the database
    await ctx.runMutation(internal.payments.storeSession, {
      userId: args.userId,
      sessionId: session.id,
      url: session.url,
    });

    return { url: session.url };
  },
});
```

## Running Queries and Mutations from Actions

```typescript
export const processOrder = action({
  args: { orderId: v.id("orders") },
  handler: async (ctx, args) => {
    // Read data via internal query
    const order = await ctx.runQuery(internal.orders.getOrder, {
      orderId: args.orderId,
    });
    if (!order) throw new Error("Order not found");

    // Call external payment API
    const paymentResult = await chargePayment(order.total);

    // Write result via internal mutation
    await ctx.runMutation(internal.orders.markPaid, {
      orderId: args.orderId,
      paymentId: paymentResult.id,
    });
  },
});
```

**Best practice:** Batch database calls into single internal functions. Each `runQuery`/`runMutation` is a separate transaction:

```typescript
// BAD: Two separate transactions
const user = await ctx.runQuery(internal.users.get, { userId });
const orders = await ctx.runQuery(internal.orders.getByUser, { userId });

// GOOD: Single transaction
const { user, orders } = await ctx.runQuery(internal.data.getUserWithOrders, {
  userId,
});
```

## Runtime Selection

Convex provides two runtimes:

### Convex Runtime (Default)

- Faster startup (no cold starts)
- Built-in `fetch` support
- Most npm packages work
- 64MB memory limit
- 10-minute timeout

### Node.js Runtime

Add `"use node"` at the top of the file:

```typescript
"use node";
import { action } from "./_generated/server";
import sharp from "sharp"; // Node.js-specific package

export const resizeImage = action({
  args: { storageId: v.id("_storage") },
  handler: async (ctx, args) => {
    const blob = await ctx.storage.get(args.storageId);
    const buffer = await blob!.arrayBuffer();
    const resized = await sharp(Buffer.from(buffer))
      .resize(800, 600)
      .toBuffer();
    return await ctx.storage.store(new Blob([resized]));
  },
});
```

- Required for packages needing Node.js APIs (sharp, puppeteer, etc.)
- 512MB memory limit
- Has cold start latency
- Cannot mix with non-Node functions in the same file

## HTTP Actions

HTTP actions expose endpoints at `https://<deployment>.convex.site`:

```typescript
// convex/http.ts
import { httpRouter } from "convex/server";
import { httpAction } from "./_generated/server";
import { internal } from "./_generated/api";

const http = httpRouter();

// POST endpoint
http.route({
  path: "/webhooks/stripe",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const body = await request.text();
    const signature = request.headers.get("stripe-signature")!;

    // Verify and process webhook
    await ctx.runMutation(internal.webhooks.processStripe, {
      body,
      signature,
    });

    return new Response("OK", { status: 200 });
  }),
});

// GET endpoint with query params
http.route({
  path: "/api/status",
  method: "GET",
  handler: httpAction(async (ctx, request) => {
    const url = new URL(request.url);
    const id = url.searchParams.get("id");

    const status = await ctx.runQuery(internal.orders.getStatus, {
      orderId: id,
    });

    return new Response(JSON.stringify(status), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  }),
});

// Path prefix (wildcard) routing
http.route({
  pathPrefix: "/api/users/",
  method: "GET",
  handler: httpAction(async (ctx, request) => {
    const url = new URL(request.url);
    const userId = url.pathname.replace("/api/users/", "");
    // ...
    return new Response(JSON.stringify({ userId }));
  }),
});

export default http;
```

## HTTP Routing

- **Exact paths:** `path: "/webhooks/stripe"` — matches exactly
- **Prefix paths:** `pathPrefix: "/api/"` — matches any path starting with prefix
- Exact paths take precedence over prefix paths
- Each path + method combination must have exactly one handler
- Supported methods: GET, POST, PUT, DELETE, PATCH, OPTIONS

## CORS Handling

```typescript
function corsHeaders(origin: string) {
  return {
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Max-Age": "86400",
    Vary: "origin",
  };
}

// Preflight handler
http.route({
  path: "/api/data",
  method: "OPTIONS",
  handler: httpAction(async (_, request) => {
    const origin = request.headers.get("Origin");
    if (!origin) return new Response(null, { status: 204 });
    return new Response(null, {
      status: 204,
      headers: new Headers(corsHeaders(origin)),
    });
  }),
});

// Actual handler with CORS headers
http.route({
  path: "/api/data",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const origin = request.headers.get("Origin") || "*";
    const data = await request.json();
    // ... process data
    return new Response(JSON.stringify({ ok: true }), {
      status: 200,
      headers: new Headers({
        "Content-Type": "application/json",
        ...corsHeaders(origin),
      }),
    });
  }),
});
```

## Webhook Patterns

### Stripe Webhook Verification

```typescript
"use node";
import Stripe from "stripe";
import { httpAction } from "./_generated/server";
import { internal } from "./_generated/api";

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

export const stripeWebhook = httpAction(async (ctx, request) => {
  const body = await request.text();
  const sig = request.headers.get("stripe-signature")!;

  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(
      body,
      sig,
      process.env.STRIPE_WEBHOOK_SECRET!,
    );
  } catch (err) {
    return new Response("Invalid signature", { status: 400 });
  }

  switch (event.type) {
    case "checkout.session.completed":
      await ctx.runMutation(internal.payments.fulfill, {
        sessionId: event.data.object.id,
      });
      break;
    case "invoice.payment_failed":
      await ctx.runMutation(internal.payments.handleFailure, {
        invoiceId: event.data.object.id,
      });
      break;
  }

  return new Response("OK", { status: 200 });
});
```

## Common Pitfalls

### 1. Dangling Promises

```typescript
// BAD: Promise not awaited — may not execute
export const bad = action({
  handler: async (ctx) => {
    ctx.runMutation(internal.tasks.update, { id }); // Missing await!
  },
});

// GOOD: Always await
export const good = action({
  handler: async (ctx) => {
    await ctx.runMutation(internal.tasks.update, { id });
  },
});
```

### 2. Calling Actions from Client (Anti-pattern)

```typescript
// ANTI-PATTERN: Direct action call from client
const result = useAction(api.payments.charge);

// BETTER: Mutation captures intent, schedules action
const startPayment = useMutation(api.payments.startPayment);
// Mutation writes to DB, then schedules the action internally
```

### 3. Excessive runQuery/runMutation Calls

```typescript
// BAD: Multiple separate transactions
const user = await ctx.runQuery(internal.users.get, { id: userId });
const prefs = await ctx.runQuery(internal.prefs.get, { userId });
const orders = await ctx.runQuery(internal.orders.list, { userId });

// GOOD: Single internal function, single transaction
const data = await ctx.runQuery(internal.users.getFullProfile, { userId });
```

### Limits

| Resource | Limit |
|----------|-------|
| Action timeout | 10 minutes |
| Memory (Convex runtime) | 64MB |
| Memory (Node.js runtime) | 512MB |
| Request/Response size (HTTP) | 20MB |
| Concurrent operations per action | 1,000 |

## Related References

- Queries and mutations: `01-functions-queries-mutations.md`
- Scheduling actions: `07-scheduling.md`
- Best practices: `11-best-practices.md`
