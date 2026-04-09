# Testing & Deployment

> Source: [docs.convex.dev/production](https://docs.convex.dev/production) | convex v1.34.x

## Table of Contents

- [Testing Overview](#testing-overview)
- [Unit Testing with convex-test](#unit-testing-with-convex-test)
- [Testing Queries and Mutations](#testing-queries-and-mutations)
- [Testing Actions](#testing-actions)
- [Testing HTTP Actions](#testing-http-actions)
- [CI/CD Setup](#cicd-setup)
- [Production Deployment](#production-deployment)
- [Environment Variables](#environment-variables)
- [Custom Domains](#custom-domains)
- [Monitoring and Logs](#monitoring-and-logs)
- [Limits and Quotas](#limits-and-quotas)

## Testing Overview

Convex provides `convex-test` for fast, local function testing with a mocked backend:

```bash
npm install --save-dev convex-test vitest
```

## Unit Testing with convex-test

```typescript
// convex/messages.test.ts
import { convexTest } from "convex-test";
import { expect, test } from "vitest";
import { api } from "./_generated/api";
import schema from "./schema";

test("send and list messages", async () => {
  const t = convexTest(schema);

  // Run a mutation
  await t.mutation(api.messages.send, {
    author: "Alice",
    body: "Hello!",
  });

  // Query and verify
  const messages = await t.query(api.messages.list);
  expect(messages).toHaveLength(1);
  expect(messages[0].body).toBe("Hello!");
  expect(messages[0].author).toBe("Alice");
});
```

### Test Context

```typescript
test("with authenticated user", async () => {
  const t = convexTest(schema);

  // Set auth identity for this test
  const asAlice = t.withIdentity({
    name: "Alice",
    email: "alice@example.com",
    tokenIdentifier: "test|alice",
  });

  await asAlice.mutation(api.posts.create, { title: "My Post" });
  const posts = await asAlice.query(api.posts.list);
  expect(posts).toHaveLength(1);
});
```

### Testing with Time

```typescript
test("scheduled function executes", async () => {
  const t = convexTest(schema);

  // Create a message that auto-deletes after 5 seconds
  await t.mutation(api.messages.sendExpiring, {
    body: "Temporary",
    author: "Alice",
  });

  // Verify message exists
  let messages = await t.query(api.messages.list);
  expect(messages).toHaveLength(1);

  // Fast-forward time to trigger scheduled function
  await t.finishInProgressScheduledFunctions();

  // Verify message was deleted
  messages = await t.query(api.messages.list);
  expect(messages).toHaveLength(0);
});
```

## Testing Queries and Mutations

```typescript
test("query returns empty initially", async () => {
  const t = convexTest(schema);
  const tasks = await t.query(api.tasks.list);
  expect(tasks).toEqual([]);
});

test("mutation inserts document", async () => {
  const t = convexTest(schema);

  const id = await t.mutation(api.tasks.create, {
    text: "Buy groceries",
    completed: false,
  });

  expect(id).toBeDefined();

  const tasks = await t.query(api.tasks.list);
  expect(tasks).toHaveLength(1);
  expect(tasks[0].text).toBe("Buy groceries");
});

test("mutation validates arguments", async () => {
  const t = convexTest(schema);

  await expect(
    t.mutation(api.tasks.create, {
      text: 123 as any,  // Wrong type
      completed: false,
    }),
  ).rejects.toThrow();
});
```

## Testing Actions

```typescript
test("action with mocked fetch", async () => {
  const t = convexTest(schema);

  // Mock the global fetch for external API calls
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () =>
    new Response(JSON.stringify({ status: "ok" }));

  try {
    const result = await t.action(api.external.checkStatus);
    expect(result).toEqual({ status: "ok" });
  } finally {
    globalThis.fetch = originalFetch;
  }
});
```

## Testing HTTP Actions

```typescript
test("http endpoint returns correct response", async () => {
  const t = convexTest(schema);

  const response = await t.fetch("/api/health", { method: "GET" });
  expect(response.status).toBe(200);

  const body = await response.json();
  expect(body.status).toBe("healthy");
});

test("webhook processes payload", async () => {
  const t = convexTest(schema);

  const response = await t.fetch("/webhooks/stripe", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ type: "payment_intent.succeeded" }),
  });

  expect(response.status).toBe(200);
});
```

## CI/CD Setup

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Test and Deploy
on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: npm ci
      - run: npx vitest run

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: npm ci
      - run: npx convex deploy
        env:
          CONVEX_DEPLOY_KEY: ${{ secrets.CONVEX_DEPLOY_KEY }}
```

### Getting a Deploy Key

```bash
npx convex deploy-key create
# Copy the key and add it as CONVEX_DEPLOY_KEY secret in GitHub
```

## Production Deployment

### Manual Deploy

```bash
npx convex deploy
```

This:
1. Validates your schema against existing data
2. Pushes all functions to production
3. Applies schema changes
4. Creates/updates indexes

### Deploy with Environment Variables

```bash
npx convex deploy --env-file .env.production
```

### Preview Deployments

```bash
# Create a preview deployment for a PR
npx convex deploy --preview pr-123
```

Preview deployments get their own database and URL — isolated from production.

## Environment Variables

```bash
# Set for development
npx convex env set API_KEY "sk-dev-123"

# Set for production
npx convex env set API_KEY "sk-prod-456" --prod

# List all env vars
npx convex env list

# Remove an env var
npx convex env unset API_KEY
```

Access in functions:

```typescript
const apiKey = process.env.API_KEY;
```

**Security:** Environment variables are encrypted at rest. Never hardcode secrets in function code.

## Custom Domains

Configure a custom domain for HTTP actions in the dashboard or via CLI:

```bash
# HTTP actions will be served at https://api.example.com
npx convex domain add api.example.com
```

Requires DNS CNAME configuration pointing to your Convex deployment.

## Monitoring and Logs

### Dashboard

The Convex dashboard provides:
- **Logs** — Real-time function execution logs
- **Data** — Browse and edit database documents
- **Functions** — View deployed functions and their stats
- **Schedules** — Monitor cron jobs and scheduled functions
- **Storage** — Manage uploaded files

### CLI Logs

```bash
# Stream logs in real-time
npx convex logs

# Filter by function
npx convex logs --function messages:send

# Show errors only
npx convex logs --success false
```

### Logging in Functions

```typescript
export const processOrder = mutation({
  handler: async (ctx, args) => {
    console.log("Processing order:", args.orderId);
    console.warn("Low inventory for item:", args.itemId);
    console.error("Payment failed:", error.message);
    // All logs appear in dashboard and CLI
  },
});
```

## Limits and Quotas

### Function Limits

| Resource | Query/Mutation | Action |
|----------|---------------|--------|
| Execution time | 1 second | 10 minutes |
| Memory | 64MB | 64MB (Convex) / 512MB (Node.js) |
| Database reads | 4,096 documents | Via runQuery |
| Database writes | 8,192 documents | Via runMutation |
| Argument size | 8MB | 8MB |
| Return value size | 8MB | 8MB |

### Database Limits

| Resource | Limit |
|----------|-------|
| Document size | 1MB |
| Indexes per table | 32 |
| Fields per index | 16 |
| Tables per deployment | No hard limit |
| Storage per deployment | Plan-dependent |

### HTTP Action Limits

| Resource | Limit |
|----------|-------|
| Request body | 20MB |
| Response body | 20MB |
| Execution time | 10 minutes |

### Rate Limits

| Resource | Free Plan | Pro Plan |
|----------|-----------|----------|
| Function calls | 500K/month | 2.5M/month |
| Database bandwidth | 1GB/month | 5GB/month |
| File storage | 1GB | 50GB |
| Action compute | 500K GB-ms | 2.5M GB-ms |

## Deployment Checklist

1. All public functions have argument validators
2. All public functions check authentication
3. Internal functions used for scheduled work
4. Environment variables set in production
5. Schema validated against production data
6. Indexes created for all production queries
7. ESLint rules enabled and passing
8. Tests passing in CI
9. Preview deployment tested
10. Deploy key configured in CI

## Related References

- Best practices: `11-best-practices.md`
- Functions: `01-functions-queries-mutations.md`
- Schemas: `03-database-schemas.md`
