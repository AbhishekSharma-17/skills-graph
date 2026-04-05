# Inngest — Cancellation

> Source: [inngest.com/docs/features/inngest-functions/cancellation](https://www.inngest.com/docs/features/inngest-functions/cancellation)

## Table of Contents

- [Cancellation Overview](#cancellation-overview)
- [Event-Based Cancellation (cancelOn)](#event-based-cancellation-cancelon)
- [Matching Conditions](#matching-conditions)
- [Timeout-Based Cancellation](#timeout-based-cancellation)
- [API-Based Cancellation](#api-based-cancellation)
- [Dashboard Cancellation](#dashboard-cancellation)
- [Post-Cancellation Cleanup](#post-cancellation-cleanup)
- [Important Behaviors](#important-behaviors)
- [Common Patterns](#common-patterns)

---

## Cancellation Overview

Inngest provides three ways to cancel running function runs:

| Method | Trigger | Use Case |
|--------|---------|----------|
| `cancelOn` | Incoming event | User deleted, subscription cancelled |
| API | REST API call | Programmatic control |
| Dashboard | Manual UI action | Operations, debugging |

## Event-Based Cancellation (cancelOn)

Cancel a function run when a matching event is received:

```typescript
const scheduleReminder = inngest.createFunction(
  {
    id: "schedule-reminder",
    cancelOn: [{
      event: "reminder/cancelled",
      if: "event.data.reminderId == async.data.reminderId",
    }],
    triggers: { event: "reminder/created" },
  },
  async ({ event, step }) => {
    await step.sleepUntil("wait-for-time", event.data.remindAt);

    await step.run("send-reminder", async () => {
      await pushNotification.send(event.data.userId, event.data.message);
    });
  }
);
```

### cancelOn configuration

```typescript
cancelOn: [
  {
    event: string;    // Event name that triggers cancellation
    match?: string;   // Field path to match between events
    if?: string;      // CEL expression for conditional matching
    timeout?: string; // How long to listen for cancel events
  }
]
```

| Option | Type | Description |
|--------|------|-------------|
| `event` | `string` | Name of the cancellation event |
| `match` | `string` | Field path for simple equality matching |
| `if` | `string` | CEL expression for complex conditions |
| `timeout` | `string` | Duration to listen for cancellation (default: function lifetime) |

## Matching Conditions

### Simple field matching

```typescript
cancelOn: [{
  event: "user/deleted",
  match: "data.userId", // Cancel when incoming event's data.userId matches trigger's data.userId
}]
```

### CEL expression matching

```typescript
cancelOn: [{
  event: "subscription/cancelled",
  if: "event.data.subscriptionId == async.data.subscriptionId",
}]
```

In CEL expressions:
- `event` refers to the **incoming** (cancellation) event
- `async` refers to the **original** (trigger) event that started the function

### Multiple cancel conditions

```typescript
cancelOn: [
  { event: "user/deleted", match: "data.userId" },
  { event: "subscription/expired", match: "data.subscriptionId" },
  { event: "admin/force-cancel", if: "event.data.runId == async.runId" },
]
```

Any matching event cancels the run.

## Timeout-Based Cancellation

Limit how long the cancellation listener stays active:

```typescript
cancelOn: [{
  event: "task/deleted",
  match: "data.taskId",
  timeout: "24h", // Only listen for 24 hours
}]
```

After the timeout, the cancel listener is removed and the function continues uninterruptible.

## API-Based Cancellation

Cancel runs programmatically via the Inngest REST API:

```bash
# Cancel a specific run
curl -X POST https://api.inngest.com/v1/runs/{run_id}/cancel \
  -H "Authorization: Bearer ${INNGEST_SIGNING_KEY}"
```

```typescript
// Using the SDK (from server-side code)
// Note: Direct SDK cancellation API may vary by version
// Check current docs for the latest API surface
```

## Dashboard Cancellation

In the Inngest dashboard:
1. Navigate to **Functions** → select your function
2. Go to the **Runs** tab
3. Select individual runs or use bulk selection
4. Click **Cancel** to cancel selected runs

Bulk cancellation supports time-range filtering for cancelling all runs within a period.

## Post-Cancellation Cleanup

Use the system event `inngest/function.cancelled` to perform cleanup:

```typescript
const handleCancellation = inngest.createFunction(
  {
    id: "cleanup-cancelled-task",
    triggers: { event: "inngest/function.cancelled" },
  },
  async ({ event, step }) => {
    const functionId = event.data.function_id;
    const originalEvent = event.data.event;

    await step.run("cleanup", async () => {
      // Clean up resources, update database, etc.
      await db.tasks.update(originalEvent.data.taskId, {
        status: "cancelled",
        cancelledAt: new Date(),
      });
    });
  }
);
```

### inngest/function.cancelled event structure

```typescript
{
  name: "inngest/function.cancelled",
  data: {
    function_id: "schedule-reminder",   // The cancelled function ID
    run_id: "run_01abc...",             // The cancelled run ID
    event: { /* original trigger event */ },
  }
}
```

## Important Behaviors

### Active steps continue to completion

Cancelling a function does **not** stop a currently executing step:

```typescript
async ({ event, step }) => {
  // If cancellation happens during this step's execution,
  // the step COMPLETES before cancellation takes effect
  await step.run("long-running", async () => {
    await processLargeFile(event.data.fileUrl); // This will finish
  });

  // This step will NOT execute after cancellation
  await step.run("next-step", async () => {
    // Never reached if cancelled during long-running step
  });
};
```

### Cancellation timing

- Between steps: Immediate cancellation
- During step execution: Step completes, then function is cancelled
- During sleep/wait: Immediate cancellation

### Cancellation does not prevent new runs

Cancelling existing runs does not prevent new events from triggering new runs of the same function.

## Common Patterns

### Cancel on resource deletion

```typescript
const processUserData = inngest.createFunction(
  {
    id: "process-user-data",
    cancelOn: [{
      event: "user/deleted",
      match: "data.userId",
    }],
    triggers: { event: "user/data.process" },
  },
  async ({ event, step }) => {
    await step.run("step-1", () => processData(event.data.userId));
    await step.sleep("wait", "1h");
    await step.run("step-2", () => moreProcessing(event.data.userId));
  }
);
```

### Scheduled task with cancellation

```typescript
const scheduledEmail = inngest.createFunction(
  {
    id: "scheduled-email",
    cancelOn: [{
      event: "email/schedule.cancelled",
      if: "event.data.scheduleId == async.data.scheduleId",
    }],
    triggers: { event: "email/schedule.created" },
  },
  async ({ event, step }) => {
    await step.sleepUntil("wait-for-send-time", event.data.sendAt);

    await step.run("send-email", async () => {
      await emailService.send({
        to: event.data.recipient,
        subject: event.data.subject,
        body: event.data.body,
      });
    });
  }
);
```

### Subscription lifecycle

```typescript
const manageSubscription = inngest.createFunction(
  {
    id: "manage-subscription",
    cancelOn: [
      { event: "subscription/cancelled", match: "data.subscriptionId" },
      { event: "subscription/upgraded", match: "data.subscriptionId" },
    ],
    triggers: { event: "subscription/started" },
  },
  async ({ event, step }) => {
    // Send onboarding sequence
    await step.run("welcome-email", () => sendWelcome(event.data.userId));
    await step.sleep("wait-3d", "3d");
    await step.run("tips-email", () => sendTips(event.data.userId));
    await step.sleep("wait-7d", "7d");
    await step.run("checkin-email", () => sendCheckin(event.data.userId));
    // Cancels if user cancels or upgrades during this sequence
  }
);
```
