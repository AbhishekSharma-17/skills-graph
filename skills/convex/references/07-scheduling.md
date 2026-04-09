# Scheduling

> Source: [docs.convex.dev/scheduling](https://docs.convex.dev/scheduling/scheduled-functions) | convex v1.34.x

## Overview

Convex scheduling lets you run functions at a future time without external infrastructure. Scheduled functions are stored in the database and execute reliably even across deployments.

## Scheduling from Mutations

Scheduling in mutations is **atomic** — if the mutation fails, the scheduled function is rolled back.

### runAfter (Delay)

```typescript
import { mutation, internalMutation } from "./_generated/server";
import { internal } from "./_generated/api";
import { v } from "convex/values";

export const sendMessage = mutation({
  args: { body: v.string(), author: v.string() },
  handler: async (ctx, args) => {
    const id = await ctx.db.insert("messages", {
      body: args.body,
      author: args.author,
    });

    // Delete after 5 seconds
    await ctx.scheduler.runAfter(
      5000,  // milliseconds
      internal.messages.deleteMessage,
      { messageId: id },
    );

    return id;
  },
});

export const deleteMessage = internalMutation({
  args: { messageId: v.id("messages") },
  handler: async (ctx, args) => {
    await ctx.db.delete(args.messageId);
  },
});
```

### runAt (Specific Time)

```typescript
export const scheduleReminder = mutation({
  args: { text: v.string(), remindAt: v.number() },
  handler: async (ctx, args) => {
    const id = await ctx.db.insert("reminders", {
      text: args.text,
      remindAt: args.remindAt,
    });

    await ctx.scheduler.runAt(
      args.remindAt,  // timestamp in milliseconds since epoch
      internal.reminders.sendReminder,
      { reminderId: id },
    );

    return id;
  },
});
```

## Scheduling from Actions

In actions, scheduling is **not atomic** — the scheduled function may execute even if the action later fails.

```typescript
export const processOrder = action({
  args: { orderId: v.id("orders") },
  handler: async (ctx, args) => {
    // Call external API
    const result = await chargePayment(args.orderId);

    // Schedule follow-up (runs regardless of what happens after)
    await ctx.scheduler.runAfter(
      0,  // Run immediately
      internal.orders.markPaid,
      { orderId: args.orderId, paymentId: result.id },
    );
  },
});
```

## Cron Jobs

Define recurring functions in `convex/crons.ts`:

```typescript
// convex/crons.ts
import { cronJobs } from "convex/server";
import { internal } from "./_generated/api";

const crons = cronJobs();

// Every hour
crons.interval(
  "cleanup expired sessions",
  { hours: 1 },
  internal.sessions.cleanupExpired,
);

// Cron expression (minute hour day-of-month month day-of-week)
crons.cron(
  "daily digest",
  "0 9 * * *",  // 9:00 AM UTC daily
  internal.notifications.sendDailyDigest,
);

// Every 5 minutes
crons.interval(
  "sync external data",
  { minutes: 5 },
  internal.sync.pullExternalData,
);

// With arguments
crons.interval(
  "weekly report",
  { hours: 168 },  // 7 days
  internal.reports.generateWeekly,
  { type: "summary" },  // Static args
);

export default crons;
```

### Cron Syntax

```
┌───────────── minute (0-59)
│ ┌───────────── hour (0-23)
│ │ ┌───────────── day of month (1-31)
│ │ │ ┌───────────── month (1-12)
│ │ │ │ ┌───────────── day of week (0-6, Sunday=0)
│ │ │ │ │
* * * * *
```

Examples:
- `"0 * * * *"` — Every hour at :00
- `"*/5 * * * *"` — Every 5 minutes
- `"0 9 * * 1-5"` — Weekdays at 9am UTC
- `"0 0 1 * *"` — First of every month at midnight

## Cancelling Scheduled Functions

```typescript
export const cancelScheduled = mutation({
  args: { scheduledId: v.id("_scheduled_functions") },
  handler: async (ctx, args) => {
    await ctx.scheduler.cancel(args.scheduledId);
  },
});
```

- If the function hasn't started, cancellation prevents execution
- If already running, the function completes but any functions it schedules won't run

## Tracking Scheduled Function Status

Query the `_scheduled_functions` system table:

```typescript
export const getScheduledStatus = query({
  args: { scheduledId: v.id("_scheduled_functions") },
  handler: async (ctx, args) => {
    return await ctx.db.system.get(args.scheduledId);
  },
});

export const listPending = query({
  handler: async (ctx) => {
    return await ctx.db.system
      .query("_scheduled_functions")
      .collect();
  },
});
```

### Scheduled Function Document

```typescript
{
  _id: Id<"_scheduled_functions">,
  _creationTime: number,
  name: string,           // Function path (e.g., "messages:deleteMessage")
  args: any[],            // Function arguments
  scheduledTime: number,  // When it should run (ms since epoch)
  completedTime?: number, // When it finished
  state: {
    kind: "Pending" | "InProgress" | "Success" | "Failed" | "Canceled",
    error?: string,  // Error message if Failed
  },
}
```

## Retry Behavior

- **Mutations:** Execute exactly once with automatic retries on internal errors
- **Actions:** Execute at most once — no automatic retries. Implement retry logic manually if needed:

```typescript
export const reliableAction = internalAction({
  args: { orderId: v.id("orders"), attempt: v.optional(v.number()) },
  handler: async (ctx, args) => {
    const attempt = args.attempt ?? 1;
    const maxAttempts = 3;

    try {
      await callExternalApi(args.orderId);
      await ctx.runMutation(internal.orders.markSuccess, {
        orderId: args.orderId,
      });
    } catch (error) {
      if (attempt < maxAttempts) {
        // Exponential backoff
        const delay = Math.pow(2, attempt) * 1000;
        await ctx.scheduler.runAfter(delay, internal.orders.reliableAction, {
          orderId: args.orderId,
          attempt: attempt + 1,
        });
      } else {
        await ctx.runMutation(internal.orders.markFailed, {
          orderId: args.orderId,
          error: String(error),
        });
      }
    }
  },
});
```

## Limits

| Constraint | Limit |
|-----------|-------|
| Functions scheduled per call | 1,000 |
| Total argument size per call | 8MB |
| Cron job minimum interval | 1 minute |

## Common Patterns

### Delayed Notification

```typescript
export const createInvite = mutation({
  args: { email: v.string(), teamId: v.id("teams") },
  handler: async (ctx, args) => {
    const id = await ctx.db.insert("invites", { ...args, status: "pending" });

    // Send notification immediately
    await ctx.scheduler.runAfter(0, internal.email.sendInvite, {
      inviteId: id,
    });

    // Auto-expire after 7 days
    await ctx.scheduler.runAfter(
      7 * 24 * 60 * 60 * 1000,
      internal.invites.expire,
      { inviteId: id },
    );

    return id;
  },
});
```

### Polling Pattern

```typescript
export const startPolling = internalAction({
  args: { jobId: v.string() },
  handler: async (ctx, args) => {
    const status = await fetch(`https://api.example.com/jobs/${args.jobId}`);
    const data = await status.json();

    if (data.status === "complete") {
      await ctx.runMutation(internal.jobs.markComplete, {
        jobId: args.jobId,
        result: data.result,
      });
    } else {
      // Poll again in 5 seconds
      await ctx.scheduler.runAfter(5000, internal.jobs.startPolling, {
        jobId: args.jobId,
      });
    }
  },
});
```

## Related References

- Actions (for side effects): `02-functions-actions-http.md`
- Internal functions: `01-functions-queries-mutations.md`
- Best practices: `11-best-practices.md`
