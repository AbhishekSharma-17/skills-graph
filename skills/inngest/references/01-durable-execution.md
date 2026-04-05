# Inngest — Durable Execution Model

> Source: [inngest.com/docs/learn/how-functions-are-executed](https://www.inngest.com/docs/learn/how-functions-are-executed)

## Table of Contents

- [What is Durable Execution?](#what-is-durable-execution)
- [Execution Lifecycle](#execution-lifecycle)
- [Memoization](#memoization)
- [State Persistence](#state-persistence)
- [HTTP-Based Invocation](#http-based-invocation)
- [Step Identity and Hashing](#step-identity-and-hashing)
- [Determinism Requirements](#determinism-requirements)
- [Execution Examples](#execution-examples)
- [Common Pitfalls](#common-pitfalls)

---

## What is Durable Execution?

Durable execution is a programming model where function state persists outside the execution context. This enables:

- **Fault tolerance** — Automatic retries on failure with state preserved
- **Sleep resumption** — Functions pause for hours/days and resume exactly where they left off
- **Infrastructure independence** — Functions can resume on different servers/containers
- **Step-level checkpointing** — Each step's result is persisted independently

Unlike traditional background jobs, durable execution means your function's progress is never lost, even if the server crashes mid-execution.

## Execution Lifecycle

### Initial Execution (First Step)

```
Event received
  → Function handler invoked via HTTP
  → Code runs until first step.run() encountered
  → Step executes, result captured
  → Result persisted with hashed step ID
  → Response sent back to Inngest
```

### Subsequent Executions (Steps 2+)

```
Inngest re-invokes function via HTTP
  → Function receives: event + all prior step states
  → Previously completed steps are SKIPPED (memoized)
  → SDK injects cached results instead of re-executing
  → Next unexecuted step runs
  → New result persisted
  → Response sent back
```

### Key insight: Each step is a separate HTTP request

```typescript
const fn = inngest.createFunction(
  { id: "three-step-example", triggers: { event: "test/run" } },
  async ({ event, step }) => {
    // HTTP Request 1: This step executes
    const a = await step.run("step-a", async () => {
      return fetchDataFromAPI();
    });

    // HTTP Request 2: step-a is memoized, step-b executes
    const b = await step.run("step-b", async () => {
      return processData(a);
    });

    // HTTP Request 3: step-a and step-b memoized, step-c executes
    const c = await step.run("step-c", async () => {
      return saveResults(b);
    });

    return { a, b, c };
  }
);
```

## Memoization

Memoization is the core mechanism that makes durable execution work. When a function re-executes:

1. The SDK receives all previously completed step states
2. When a completed step is encountered, the SDK returns the cached result
3. The function code continues with that cached value
4. Only the next unexecuted step actually runs

### What gets memoized

- Return values from `step.run()`
- Sleep completion status from `step.sleep()` / `step.sleepUntil()`
- Received events from `step.waitForEvent()`
- Results from `step.invoke()`

### Serialization

All step return values are serialized as JSON. This means:
- `Date` objects become ISO strings
- `ObjectId` instances become strings
- Class instances lose their methods
- Functions and symbols are dropped

```typescript
// BAD: Date will be serialized as string
const result = await step.run("get-date", () => new Date());
// result is "2026-04-05T..." (string), NOT a Date object

// GOOD: Parse it back if you need a Date
const timestamp = await step.run("get-timestamp", () => Date.now());
const date = new Date(timestamp); // Works correctly
```

## State Persistence

Step state is stored in Inngest's state store:

- **Encrypted at rest** — All step data is encrypted
- **Size limits** — Combined output from all steps must not exceed 4MB
- **Maximum steps** — A function can have up to 1,000 steps
- **Retention** — State is retained for the lifetime of the function run

### State store flow

```
step.run("my-step", handler)
  → handler() executes
  → Return value serialized to JSON
  → Stored: { stepId: hash("my-step"), data: <serialized> }
  → On next invocation: stepId found → return cached data
```

## HTTP-Based Invocation

Inngest invokes your functions via HTTP, not a persistent connection:

```
┌──────────┐         ┌───────────────┐
│ Inngest  │──POST──>│ Your API      │
│ Platform │         │ /api/inngest  │
│          │<─200────│               │
└──────────┘         └───────────────┘
```

Implications:
- **Serverless compatible** — No long-running processes needed
- **Platform agnostic** — Works anywhere that handles HTTP
- **Timeout aware** — Steps must complete within your platform's timeout
- **Streaming** — Enable streaming for longer-running steps on serverless

Each step execution is a separate HTTP request/response cycle. The function re-runs from the top each time, but memoization makes previously completed steps near-instant.

## Step Identity and Hashing

Steps are identified by their string ID, which is hashed for storage:

```typescript
// The string "fetch-user" becomes the step's unique identity
await step.run("fetch-user", async () => {
  return db.users.find(userId);
});
```

### Rules for step IDs

- **Must be unique** within a function (duplicate IDs cause errors)
- **Must be stable** across function versions (changing IDs breaks memoization)
- **Should be descriptive** — They appear in the dashboard and logs

```typescript
// BAD: Dynamic IDs that change between runs
await step.run(`step-${Date.now()}`, handler); // Never do this

// GOOD: Stable, descriptive IDs
await step.run("fetch-user-profile", handler);

// GOOD: Dynamic but deterministic (based on input data)
for (const userId of userIds) {
  await step.run(`process-user-${userId}`, () => processUser(userId));
}
```

## Determinism Requirements

Because functions re-execute from the top on each step, the code path must be deterministic:

### Code outside steps runs on EVERY invocation

```typescript
async ({ event, step }) => {
  // This runs on EVERY HTTP request (every step execution)
  console.log("Function invoked"); // Logged N times for N steps

  // This is a step — runs once, then memoized
  const data = await step.run("fetch", async () => {
    return await fetchData();
  });

  // This also runs on every invocation after step-1 completes
  const transformed = data.map(item => item.name);

  // Second step
  await step.run("save", async () => {
    return await saveData(transformed);
  });
};
```

### What must be inside steps

All non-deterministic operations must be wrapped in `step.run()`:

```typescript
// BAD: API call outside a step — runs on every re-execution
const data = await fetch("https://api.example.com/data");

// GOOD: API call inside a step — runs once, memoized
const data = await step.run("fetch-data", async () => {
  return await fetch("https://api.example.com/data").then(r => r.json());
});

// BAD: Random value outside a step — different each re-execution
const id = crypto.randomUUID();

// GOOD: Random value inside a step
const id = await step.run("generate-id", () => crypto.randomUUID());
```

### What can safely be outside steps

- Pure computations on memoized data
- Logging (idempotent side effects)
- Variable declarations using step results

## Execution Examples

### Sequential execution (3 HTTP requests)

```typescript
async ({ event, step }) => {
  const user = await step.run("get-user", () => getUser(event.data.id));
  const order = await step.run("create-order", () => createOrder(user));
  const receipt = await step.run("send-receipt", () => sendEmail(user, order));
  return { receipt };
};
```

### With sleep (4 HTTP requests + timer)

```typescript
async ({ event, step }) => {
  await step.run("charge-card", () => stripe.charges.create(/*...*/));
  await step.sleep("wait-for-delivery", "7d"); // Pauses for 7 days
  await step.run("request-review", () => sendReviewRequest(event.data.userId));
  return { status: "review-requested" };
};
```

### Error and retry flow

```
Attempt 1: step.run("api-call") → throws Error
  → Inngest receives error, schedules retry
Attempt 2 (after backoff): step.run("api-call") → throws Error
  → Inngest schedules another retry
Attempt 3: step.run("api-call") → returns data
  → Result persisted, function continues to next step
```

## Common Pitfalls

### 1. Side effects outside steps

```typescript
// WRONG: This email sends on EVERY re-execution
async ({ event, step }) => {
  await sendEmail(event.data.email, "Welcome!"); // Sends multiple times!
  await step.run("update-db", () => db.update(/*...*/));
};

// RIGHT: Wrap side effects in steps
async ({ event, step }) => {
  await step.run("send-email", () => sendEmail(event.data.email, "Welcome!"));
  await step.run("update-db", () => db.update(/*...*/));
};
```

### 2. Relying on non-serializable return values

```typescript
// WRONG: Map is not JSON-serializable
await step.run("build-map", () => new Map([["key", "value"]]));

// RIGHT: Use plain objects
await step.run("build-map", () => ({ key: "value" }));
```

### 3. Branching on non-deterministic values

```typescript
// WRONG: Math.random() changes each re-execution
if (Math.random() > 0.5) {
  await step.run("path-a", handler);
} else {
  await step.run("path-b", handler);
}

// RIGHT: Use a step to produce the random value
const coin = await step.run("flip-coin", () => Math.random() > 0.5);
if (coin) {
  await step.run("path-a", handler);
} else {
  await step.run("path-b", handler);
}
```

### 4. Exceeding state limits

- **4MB total** for all step outputs combined
- **1,000 steps** maximum per function
- For large data, store in external storage and return a reference:

```typescript
const fileRef = await step.run("process-file", async () => {
  const result = await processLargeFile(event.data.url);
  const key = await s3.upload(result); // Store externally
  return { bucket: "results", key }; // Return reference, not data
});
```
