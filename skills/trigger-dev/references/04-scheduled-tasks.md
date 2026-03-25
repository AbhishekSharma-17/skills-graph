# Scheduled Tasks (Cron)

> Source: https://trigger.dev/docs/tasks/scheduled — v4.4.3

## Contents

- [Overview](#overview)
- [Declarative Schedules](#declarative-schedules)
- [Imperative Schedules](#imperative-schedules)
- [Cron Syntax](#cron-syntax)
- [Timezone Handling](#timezone-handling)
- [Schedule Payload](#schedule-payload)
- [Schedule Management API](#schedule-management-api)
- [Common Patterns](#common-patterns)

## Overview

Trigger.dev supports cron-based scheduled tasks using `schedules.task()`. Schedules can be:

- **Declarative** — Defined in code, synced on `dev`/`deploy`
- **Imperative** — Created dynamically via the SDK or dashboard

## Declarative Schedules

Define schedules directly in your task code. They sync automatically when you run `dev` or `deploy`:

```typescript
import { schedules } from "@trigger.dev/sdk/v3";

export const dailyCleanup = schedules.task({
  id: "daily-cleanup",
  // Simple cron (UTC by default)
  cron: "0 2 * * *", // 2:00 AM UTC daily
  run: async (payload) => {
    console.log(`Running cleanup at ${payload.timestamp}`);
    await deleteExpiredSessions();
    await archiveOldRecords();
    return { cleaned: true };
  },
});
```

### With Timezone

```typescript
export const tokyoMorningReport = schedules.task({
  id: "tokyo-morning-report",
  cron: {
    pattern: "0 9 * * 1-5", // 9:00 AM weekdays
    timezone: "Asia/Tokyo",
  },
  run: async (payload) => {
    console.log(`Timezone: ${payload.timezone}`); // "Asia/Tokyo"
    await generateMorningReport();
  },
});
```

### Environment-Specific Schedules

```typescript
export const prodOnlyTask = schedules.task({
  id: "prod-only-sync",
  cron: {
    pattern: "*/15 * * * *", // Every 15 minutes
    environments: ["PRODUCTION"], // Only in prod
  },
  run: async (payload) => {
    await syncExternalData();
  },
});
```

### Multiple Schedules on One Task

```typescript
export const multiSchedule = schedules.task({
  id: "multi-schedule",
  cron: [
    { pattern: "0 9 * * 1-5", timezone: "America/New_York" },  // Weekday 9am ET
    { pattern: "0 18 * * 5", timezone: "America/New_York" },   // Friday 6pm ET
  ],
  run: async (payload) => {
    console.log(`Schedule ID: ${payload.scheduleId}`);
  },
});
```

## Imperative Schedules

Create schedules dynamically — useful for per-user or per-tenant scheduling:

```typescript
import { schedules } from "@trigger.dev/sdk/v3";

// Create a schedule
const schedule = await schedules.create({
  task: "daily-report",
  cron: "0 8 * * *",
  timezone: "America/New_York",
  externalId: "user_123",                    // Link to your entity
  deduplicationKey: "user_123-daily-report", // Prevent duplicates
});

console.log(`Schedule ID: ${schedule.id}`);
```

### Per-User Scheduling Pattern

```typescript
// When a user signs up, create their personal schedule
async function onUserSignup(user: User) {
  await schedules.create({
    task: "user-daily-digest",
    cron: "0 8 * * *",
    timezone: user.timezone,
    externalId: user.id,
    deduplicationKey: `${user.id}-digest`,
  });
}

// The scheduled task receives the externalId
export const userDigest = schedules.task({
  id: "user-daily-digest",
  run: async (payload) => {
    const userId = payload.externalId; // "user_123"
    const user = await db.users.findById(userId);
    await sendDigestEmail(user);
  },
});
```

## Cron Syntax

Standard 5-field cron expression (seconds NOT supported):

```
┌───── minute (0-59)
│ ┌───── hour (0-23)
│ │ ┌───── day of month (1-31)
│ │ │ ┌───── month (1-12)
│ │ │ │ ┌───── day of week (0-7, 0 and 7 = Sunday)
│ │ │ │ │
* * * * *
```

### Common Patterns

| Pattern | Description |
|---------|-------------|
| `* * * * *` | Every minute |
| `*/5 * * * *` | Every 5 minutes |
| `*/15 * * * *` | Every 15 minutes |
| `0 * * * *` | Every hour |
| `0 */2 * * *` | Every 2 hours |
| `0 9 * * *` | Daily at 9:00 AM |
| `0 9 * * 1-5` | Weekdays at 9:00 AM |
| `0 0 * * 0` | Weekly on Sunday at midnight |
| `0 0 1 * *` | Monthly on the 1st at midnight |
| `0 0 1 1 *` | Yearly on January 1st |
| `30 9 * * 1` | Every Monday at 9:30 AM |
| `0 9,17 * * *` | Daily at 9:00 AM and 5:00 PM |

### Special Values

| Symbol | Meaning |
|--------|---------|
| `*` | Any value |
| `,` | List separator (`1,3,5`) |
| `-` | Range (`1-5`) |
| `/` | Step (`*/15` = every 15) |
| `L` | Last day of month/week |

## Timezone Handling

- Default timezone: **UTC**
- Supports all IANA timezone names (e.g., `America/New_York`, `Europe/London`)
- **Automatic DST adjustment** — Trigger.dev handles Daylight Saving Time transitions

```typescript
// List available timezones
const timezones = await schedules.timezones();
```

## Schedule Payload

The `run` function of a scheduled task receives a special payload:

```typescript
export const scheduled = schedules.task({
  id: "my-scheduled",
  cron: "0 9 * * *",
  run: async (payload) => {
    payload.timestamp;     // Date — when this run was scheduled
    payload.lastTimestamp;  // Date | undefined — previous execution time
    payload.timezone;       // string — IANA timezone (default: "UTC")
    payload.scheduleId;     // string — schedule identifier
    payload.externalId;     // string | undefined — your custom ID
    payload.upcoming;       // Date[] — next 5 scheduled times
  },
});
```

## Schedule Management API

```typescript
import { schedules } from "@trigger.dev/sdk/v3";

// Create
const schedule = await schedules.create({
  task: "my-task",
  cron: "0 9 * * *",
  timezone: "UTC",
  externalId: "user_123",
  deduplicationKey: "unique-key",
});

// Retrieve
const fetched = await schedules.retrieve(schedule.id);

// List all schedules
const list = await schedules.list();
for (const s of list.data) {
  console.log(`${s.id}: ${s.cron} (${s.active ? "active" : "inactive"})`);
}

// Update
await schedules.update(schedule.id, {
  cron: "0 10 * * *", // Change to 10 AM
});

// Deactivate / Activate
await schedules.deactivate(schedule.id);
await schedules.activate(schedule.id);

// Delete
await schedules.del(schedule.id);
```

## Common Patterns

### Daily Data Sync

```typescript
export const dataSync = schedules.task({
  id: "daily-data-sync",
  cron: {
    pattern: "0 3 * * *",
    timezone: "UTC",
  },
  retry: { maxAttempts: 3 },
  run: async (payload) => {
    const since = payload.lastTimestamp ?? new Date(Date.now() - 86400000);
    const records = await fetchUpdatedRecords(since);
    await syncToDataWarehouse(records);
    return { synced: records.length };
  },
});
```

### Execution Environment Rules

- **Dev:** Schedules trigger only when `npx trigger.dev dev` is running
- **Staging/Production:** Schedules trigger only if the task is in the current deployment
- Schedules are automatically deregistered when removed from code and redeployed

## Related Topics

- Writing tasks → `01-writing-tasks.md`
- Concurrency & queues → `05-concurrency-queues.md`
- Deployment → `10-deployment-cli.md`
