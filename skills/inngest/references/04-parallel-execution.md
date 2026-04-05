# Inngest — Parallel Execution

> Source: [inngest.com/docs/guides/step-parallelism](https://www.inngest.com/docs/guides/step-parallelism)

## Table of Contents

- [Parallel Steps with Promise.all](#parallel-steps-with-promiseall)
- [How Parallel Execution Works](#how-parallel-execution-works)
- [TypeScript Patterns](#typescript-patterns)
- [Python Parallel Patterns](#python-parallel-patterns)
- [Chunked Processing](#chunked-processing)
- [Promise.race](#promiserace)
- [Limits and Constraints](#limits-and-constraints)
- [Common Patterns](#common-patterns)

---

## Parallel Steps with Promise.all

By default, steps execute sequentially. To run steps in parallel, use `Promise.all()`:

```typescript
async ({ event, step }) => {
  // Sequential: step-b waits for step-a to complete
  const a = await step.run("step-a", () => fetchUserProfile(userId));
  const b = await step.run("step-b", () => fetchOrderHistory(userId));

  // Parallel: both steps execute simultaneously
  const [profile, orders] = await Promise.all([
    step.run("fetch-profile", () => fetchUserProfile(userId)),
    step.run("fetch-orders", () => fetchOrderHistory(userId)),
  ]);
};
```

### Key: Don't await individual steps

```typescript
// WRONG: Awaiting each step makes them sequential
const a = await step.run("step-a", handlerA);
const b = await step.run("step-b", handlerB);

// RIGHT: Create promises without await, then collect
const promiseA = step.run("step-a", handlerA);
const promiseB = step.run("step-b", handlerB);
const [a, b] = await Promise.all([promiseA, promiseB]);
```

## How Parallel Execution Works

Under Inngest's durable execution model, parallel steps optimize HTTP requests:

### Sequential (3 HTTP requests)
```
Request 1: Execute step-a → persist result
Request 2: Memoize step-a, execute step-b → persist result
Request 3: Memoize step-a + step-b, execute step-c → persist result
```

### Parallel with Promise.all (1-2 HTTP requests)
```
Request 1: Execute step-a AND step-b AND step-c simultaneously → persist all results
(If any step fails, only the failed step retries)
```

With optimized parallelism (default in SDK v4+), Inngest detects that steps are wrapped in `Promise.all()` and executes them in a single HTTP request, significantly reducing latency.

## TypeScript Patterns

### Basic parallel execution

```typescript
const processDashboard = inngest.createFunction(
  { id: "process-dashboard", triggers: { event: "dashboard/refresh" } },
  async ({ event, step }) => {
    const [analytics, notifications, userPrefs] = await Promise.all([
      step.run("fetch-analytics", () => getAnalytics(event.data.userId)),
      step.run("fetch-notifications", () => getNotifications(event.data.userId)),
      step.run("fetch-preferences", () => getUserPrefs(event.data.userId)),
    ]);

    return { analytics, notifications, userPrefs };
  }
);
```

### Mixed sequential and parallel

```typescript
async ({ event, step }) => {
  // Step 1: Sequential - must complete first
  const user = await step.run("fetch-user", () =>
    getUser(event.data.userId)
  );

  // Steps 2-4: Parallel - all depend on user but not on each other
  const [subscription, usage, invoices] = await Promise.all([
    step.run("fetch-subscription", () => getSubscription(user.subscriptionId)),
    step.run("fetch-usage", () => getUsage(user.id)),
    step.run("fetch-invoices", () => getInvoices(user.billingId)),
  ]);

  // Step 5: Sequential - depends on parallel results
  await step.run("generate-report", () =>
    createReport(user, subscription, usage, invoices)
  );
};
```

### Dynamic parallel steps

```typescript
async ({ event, step }) => {
  const userIds = event.data.userIds; // ["usr_1", "usr_2", "usr_3"]

  const results = await Promise.all(
    userIds.map(userId =>
      step.run(`process-user-${userId}`, () => processUser(userId))
    )
  );

  return { processed: results.length };
};
```

## Python Parallel Patterns

Python uses `ctx.group.parallel()` instead of `Promise.all()`:

```python
@inngest_client.create_function(
    fn_id="process-batch",
    trigger=inngest.TriggerEvent(event="batch/process"),
)
async def process_batch(ctx: inngest.Context) -> dict:
    # Parallel execution in Python
    results = await ctx.group.parallel(
        lambda: ctx.step.run("fetch-users", fetch_users),
        lambda: ctx.step.run("fetch-orders", fetch_orders),
        lambda: ctx.step.run("fetch-analytics", fetch_analytics),
    )

    users, orders, analytics = results
    return {"users": len(users), "orders": len(orders)}
```

### Dynamic parallel in Python

```python
async def process_batch(ctx: inngest.Context) -> dict:
    user_ids = ctx.event.data["user_ids"]

    results = await ctx.group.parallel(
        *[
            lambda uid=uid: ctx.step.run(
                f"process-{uid}", lambda: process_user(uid)
            )
            for uid in user_ids
        ]
    )

    return {"processed": len(results)}
```

## Chunked Processing

For large datasets, split work into chunks and process each chunk in parallel:

```typescript
async ({ event, step }) => {
  // Step 1: Fetch all items
  const items = await step.run("fetch-items", () =>
    db.items.findMany({ where: { batchId: event.data.batchId } })
  );

  // Step 2: Chunk into groups of 10
  const chunks = [];
  for (let i = 0; i < items.length; i += 10) {
    chunks.push(items.slice(i, i + 10));
  }

  // Step 3: Process all chunks in parallel
  const results = await Promise.all(
    chunks.map((chunk, index) =>
      step.run(`process-chunk-${index}`, () =>
        Promise.all(chunk.map(item => processItem(item)))
      )
    )
  );

  // Step 4: Aggregate results
  const flatResults = results.flat();
  await step.run("save-results", () =>
    db.results.createMany({ data: flatResults })
  );

  return { total: flatResults.length };
};
```

### AI summarization with chunking

```typescript
async ({ event, step }) => {
  const document = await step.run("fetch-doc", () =>
    getDocument(event.data.docId)
  );

  const chunks = splitIntoChunks(document.text, 4000);

  // Summarize each chunk in parallel
  const summaries = await Promise.all(
    chunks.map((chunk, i) =>
      step.ai.infer(`summarize-chunk-${i}`, {
        model: "openai/gpt-4o",
        body: {
          messages: [
            { role: "system", content: "Summarize this section concisely." },
            { role: "user", content: chunk },
          ],
        },
      })
    )
  );

  // Final summary combining all chunks
  const finalSummary = await step.ai.infer("final-summary", {
    model: "openai/gpt-4o",
    body: {
      messages: [
        { role: "system", content: "Combine these summaries into one." },
        { role: "user", content: summaries.map(s =>
          s.choices[0].message.content).join("\n\n")
        },
      ],
    },
  });

  return { summary: finalSummary.choices[0].message.content };
};
```

## Promise.race

Use `Promise.race()` for first-to-complete semantics:

```typescript
async ({ event, step }) => {
  const fastest = await Promise.race([
    step.run("provider-a", () => fetchFromProviderA(query)),
    step.run("provider-b", () => fetchFromProviderB(query)),
  ]);

  return { result: fastest };
};
```

**Important:** With optimized parallelism (SDK v4+), all steps in a `Promise.race()` will execute and complete. The promise resolves with the first result, but all steps still run. This differs from regular JS `Promise.race()` where losing promises might be abandoned.

## Limits and Constraints

| Constraint | Limit |
|-----------|-------|
| Maximum steps per function | 1,000 |
| Combined step output size | 4 MB |
| Parallel steps per Promise.all | No hard limit (subject to 1,000 total) |
| Step execution timeout | Platform-dependent (serverless limits apply) |

## Common Patterns

### Fan-out / Fan-in

```typescript
async ({ event, step }) => {
  const users = await step.run("get-users", () => getActiveUsers());

  // Fan-out: process each user in parallel
  const results = await Promise.all(
    users.map(user =>
      step.run(`notify-${user.id}`, () => sendNotification(user))
    )
  );

  // Fan-in: aggregate results
  const stats = await step.run("compute-stats", () => ({
    sent: results.filter(r => r.success).length,
    failed: results.filter(r => !r.success).length,
  }));

  return stats;
};
```

### Parallel with shared dependency

```typescript
async ({ event, step }) => {
  // Fetch shared config first
  const config = await step.run("get-config", () => loadConfig());

  // Use config in parallel steps
  const [emails, sms] = await Promise.all([
    step.run("send-emails", () => sendEmails(config.emailProvider)),
    step.run("send-sms", () => sendSMS(config.smsProvider)),
  ]);
};
```
