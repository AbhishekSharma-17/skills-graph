# Cloudflare Workers — Testing

> Source: [developers.cloudflare.com/workers/testing](https://developers.cloudflare.com/workers/testing/)

## Table of Contents

- [Testing Strategy](#testing-strategy)
- [Vitest Integration Setup](#vitest-integration-setup)
- [Writing Unit Tests](#writing-unit-tests)
- [Testing with Bindings](#testing-with-bindings)
- [Testing Durable Objects](#testing-durable-objects)
- [Testing Scheduled Handlers](#testing-scheduled-handlers)
- [Integration Tests](#integration-tests)
- [Mocking External APIs](#mocking-external-apis)
- [Test Configuration](#test-configuration)
- [Common Patterns](#common-patterns)

## Testing Strategy

Cloudflare recommends the **Workers Vitest integration** (`@cloudflare/vitest-pool-workers`) — tests run inside the actual `workerd` runtime, not Node.js. This gives you real Workers APIs, real bindings, and real behavior.

Test pyramid for Workers:
1. **Unit tests** — Test individual functions in `workerd` runtime
2. **Integration tests** — Test full request/response with real bindings
3. **E2E tests** — Test deployed Worker via HTTP (optional)

## Vitest Integration Setup

### Install Dependencies

```bash
npm install -D vitest @cloudflare/vitest-pool-workers
```

### vitest.config.ts

```typescript
import { defineWorkersConfig } from "@cloudflare/vitest-pool-workers/config";

export default defineWorkersConfig({
  test: {
    poolOptions: {
      workers: {
        wrangler: {
          configPath: "./wrangler.toml",  // Uses your existing config
        },
      },
    },
  },
});
```

### Alternative: Inline Worker Configuration

```typescript
import { defineWorkersConfig } from "@cloudflare/vitest-pool-workers/config";

export default defineWorkersConfig({
  test: {
    poolOptions: {
      workers: {
        main: "./src/index.ts",
        miniflare: {
          compatibilityDate: "2026-04-23",
          compatibilityFlags: ["nodejs_compat_v2"],
          kvNamespaces: ["MY_KV"],
          d1Databases: ["DB"],
          r2Buckets: ["MY_BUCKET"],
        },
      },
    },
  },
});
```

### Package.json Script

```json
{
  "scripts": {
    "test": "vitest",
    "test:run": "vitest run",
    "test:watch": "vitest --watch"
  }
}
```

## Writing Unit Tests

### Testing a Fetch Handler

```typescript
// test/index.spec.ts
import { env, createExecutionContext, waitOnExecutionContext } from "cloudflare:test";
import { describe, it, expect } from "vitest";
import worker from "../src/index";

describe("Worker", () => {
  it("responds with hello", async () => {
    const request = new Request("http://localhost/");
    const ctx = createExecutionContext();
    const response = await worker.fetch(request, env, ctx);
    await waitOnExecutionContext(ctx);

    expect(response.status).toBe(200);
    expect(await response.text()).toBe("Hello World!");
  });

  it("returns 404 for unknown routes", async () => {
    const request = new Request("http://localhost/unknown");
    const ctx = createExecutionContext();
    const response = await worker.fetch(request, env, ctx);
    await waitOnExecutionContext(ctx);

    expect(response.status).toBe(404);
  });

  it("handles POST with JSON body", async () => {
    const request = new Request("http://localhost/api/data", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: "Alice" }),
    });
    const ctx = createExecutionContext();
    const response = await worker.fetch(request, env, ctx);
    await waitOnExecutionContext(ctx);

    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty("name", "Alice");
  });
});
```

### Using SELF for Integration-Style Tests

```typescript
import { SELF } from "cloudflare:test";
import { describe, it, expect } from "vitest";

describe("Worker (integration)", () => {
  it("handles full request lifecycle", async () => {
    // SELF dispatches to your Worker's fetch handler directly
    const response = await SELF.fetch("http://localhost/api/health");
    expect(response.status).toBe(200);

    const body = await response.json<{ status: string }>();
    expect(body.status).toBe("ok");
  });
});
```

## Testing with Bindings

Each test file gets **isolated binding instances** — KV, D1, R2 data doesn't leak between test files.

### KV

```typescript
import { env } from "cloudflare:test";
import { describe, it, expect, beforeEach } from "vitest";

describe("KV operations", () => {
  beforeEach(async () => {
    // Each test file starts with empty KV
    await env.MY_KV.put("test-key", "test-value");
  });

  it("reads from KV", async () => {
    const value = await env.MY_KV.get("test-key");
    expect(value).toBe("test-value");
  });

  it("writes and reads JSON", async () => {
    await env.MY_KV.put("user", JSON.stringify({ name: "Alice" }));
    const user = await env.MY_KV.get("user", "json");
    expect(user).toEqual({ name: "Alice" });
  });
});
```

### D1

```typescript
import { env } from "cloudflare:test";
import { describe, it, expect, beforeAll } from "vitest";

describe("D1 operations", () => {
  beforeAll(async () => {
    await env.DB.exec(`
      CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL
      )
    `);
  });

  it("inserts and queries users", async () => {
    await env.DB.prepare("INSERT INTO users (name, email) VALUES (?, ?)")
      .bind("Alice", "alice@example.com")
      .run();

    const user = await env.DB.prepare("SELECT * FROM users WHERE email = ?")
      .bind("alice@example.com")
      .first();

    expect(user).toBeDefined();
    expect(user!.name).toBe("Alice");
  });

  it("handles batch operations", async () => {
    const results = await env.DB.batch([
      env.DB.prepare("INSERT INTO users (name, email) VALUES (?, ?)").bind("Bob", "bob@example.com"),
      env.DB.prepare("SELECT count(*) as total FROM users"),
    ]);

    expect(results[1].results[0]).toHaveProperty("total");
  });
});
```

### R2

```typescript
import { env } from "cloudflare:test";
import { describe, it, expect } from "vitest";

describe("R2 operations", () => {
  it("uploads and downloads objects", async () => {
    await env.MY_BUCKET.put("test.txt", "Hello R2!");

    const obj = await env.MY_BUCKET.get("test.txt");
    expect(obj).not.toBeNull();
    expect(await obj!.text()).toBe("Hello R2!");
  });

  it("lists objects with prefix", async () => {
    await env.MY_BUCKET.put("docs/a.txt", "A");
    await env.MY_BUCKET.put("docs/b.txt", "B");
    await env.MY_BUCKET.put("images/c.png", "C");

    const listed = await env.MY_BUCKET.list({ prefix: "docs/" });
    expect(listed.objects).toHaveLength(2);
  });
});
```

## Testing Durable Objects

```typescript
import { env, runInDurableObject } from "cloudflare:test";
import { describe, it, expect } from "vitest";

describe("Counter Durable Object", () => {
  it("increments counter", async () => {
    const id = env.COUNTER.idFromName("test");
    const stub = env.COUNTER.get(id);

    // Call RPC methods on the stub
    const count1 = await stub.increment();
    expect(count1).toBe(1);

    const count2 = await stub.increment();
    expect(count2).toBe(2);

    const current = await stub.getCount();
    expect(current).toBe(2);
  });

  it("maintains state across calls", async () => {
    const id = env.COUNTER.idFromName("persistent");
    const stub = env.COUNTER.get(id);

    await stub.increment();
    await stub.increment();

    // Same ID returns same DO instance
    const stub2 = env.COUNTER.get(id);
    const count = await stub2.getCount();
    expect(count).toBe(2);
  });
});
```

## Testing Scheduled Handlers

```typescript
import { env, createScheduledController, waitOnExecutionContext, createExecutionContext } from "cloudflare:test";
import { describe, it, expect } from "vitest";
import worker from "../src/index";

describe("Scheduled handler", () => {
  it("runs cleanup on schedule", async () => {
    const controller = createScheduledController({
      scheduledTime: new Date("2026-04-23T00:00:00Z"),
      cron: "0 0 * * *",
    });
    const ctx = createExecutionContext();

    await worker.scheduled(controller, env, ctx);
    await waitOnExecutionContext(ctx);

    // Verify side effects (e.g., old records deleted)
    const count = await env.DB.prepare("SELECT count(*) as c FROM expired_tokens").first("c");
    expect(count).toBe(0);
  });
});
```

## Integration Tests

Test full end-to-end with `SELF`:

```typescript
import { SELF, env } from "cloudflare:test";
import { describe, it, expect, beforeAll } from "vitest";

describe("API Integration", () => {
  beforeAll(async () => {
    await env.DB.exec(`
      CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE)
    `);
  });

  it("creates and retrieves a user", async () => {
    // Create
    const createRes = await SELF.fetch("http://localhost/api/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: "Alice", email: "alice@test.com" }),
    });
    expect(createRes.status).toBe(201);
    const created = await createRes.json<{ id: number }>();

    // Retrieve
    const getRes = await SELF.fetch(`http://localhost/api/users/${created.id}`);
    expect(getRes.status).toBe(200);
    const user = await getRes.json<{ name: string }>();
    expect(user.name).toBe("Alice");
  });
});
```

## Mocking External APIs

```typescript
import { fetchMock } from "cloudflare:test";
import { describe, it, expect, beforeEach, afterEach } from "vitest";

describe("External API calls", () => {
  beforeEach(() => {
    fetchMock.activate();
    fetchMock.disableNetConnect(); // Block real network calls
  });

  afterEach(() => {
    fetchMock.deactivate();
  });

  it("calls external API and processes response", async () => {
    fetchMock.get("https://api.example.com")
      .intercept({ path: "/data", method: "GET" })
      .reply(200, JSON.stringify({ result: "mocked" }));

    const response = await SELF.fetch("http://localhost/proxy");
    const data = await response.json();
    expect(data.result).toBe("mocked");
  });
});
```

## Test Configuration

### Isolated Storage Per Test File

By default, each test file gets isolated binding state. To share state:

```typescript
// vitest.config.ts
export default defineWorkersConfig({
  test: {
    poolOptions: {
      workers: {
        isolatedStorage: false,  // Share storage across test files
      },
    },
  },
});
```

### Remote Bindings (Test Against Production)

```typescript
export default defineWorkersConfig({
  test: {
    poolOptions: {
      workers: {
        wrangler: { configPath: "./wrangler.toml" },
        miniflare: {
          kvNamespaces: { MY_KV: { remote: true } },  // Use real KV namespace
        },
      },
    },
  },
});
```

## Common Patterns

### Test Helpers

```typescript
// test/helpers.ts
import { env, createExecutionContext, waitOnExecutionContext } from "cloudflare:test";
import worker from "../src/index";

export async function callWorker(path: string, init?: RequestInit) {
  const request = new Request(`http://localhost${path}`, init);
  const ctx = createExecutionContext();
  const response = await worker.fetch(request, env, ctx);
  await waitOnExecutionContext(ctx);
  return response;
}

export async function seedDB() {
  await env.DB.exec(`
    INSERT INTO users (name, email) VALUES ('Alice', 'alice@test.com');
    INSERT INTO users (name, email) VALUES ('Bob', 'bob@test.com');
  `);
}
```

## Common Pitfalls

- **Not Node.js** — Tests run in `workerd`, not Node.js. Node APIs like `fs` aren't available in tests.
- **Isolated by default** — KV/D1/R2 data is isolated per test file, not per test case. Use `beforeEach` to reset state.
- **Import from `cloudflare:test`** — Always import `env`, `SELF`, etc. from `cloudflare:test`, not from your Worker code.
- **waitOnExecutionContext** — Always call `await waitOnExecutionContext(ctx)` to ensure `ctx.waitUntil()` promises complete.
- **fetchMock** — Must activate/deactivate fetchMock around tests. Forgetting `deactivate()` breaks subsequent tests.
