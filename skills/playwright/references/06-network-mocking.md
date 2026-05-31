# Playwright — Network & Mocking

> Source: [playwright.dev/docs/network](https://playwright.dev/docs/network) | Version: 1.59

## Table of Contents

- [Intercepting Requests](#intercepting-requests)
- [Mocking API Responses](#mocking-api-responses)
- [Modifying Responses](#modifying-responses)
- [Aborting Requests](#aborting-requests)
- [Waiting for Network Events](#waiting-for-network-events)
- [HAR Replay](#har-replay)
- [WebSocket Mocking](#websocket-mocking)
- [Common Pitfalls](#common-pitfalls)

## Intercepting Requests

Use `page.route()` to intercept requests matching a URL pattern or predicate:

```typescript
// Intercept by URL glob
await page.route('**/api/users', async (route) => {
  console.log(route.request().url());
  await route.continue();
});

// Intercept by regex
await page.route(/\/api\/users\/\d+/, async (route) => {
  await route.continue();
});

// Intercept by predicate
await page.route(
  (url) => url.pathname.startsWith('/api/') && url.searchParams.has('debug'),
  async (route) => {
    await route.continue();
  }
);
```

### Request Object

```typescript
await page.route('**/api/**', async (route) => {
  const request = route.request();
  console.log(request.method());       // GET, POST, etc.
  console.log(request.url());          // Full URL
  console.log(request.headers());      // Request headers
  console.log(request.postData());     // POST body
  console.log(request.resourceType()); // document, xhr, fetch, etc.
  await route.continue();
});
```

## Mocking API Responses

### Static JSON Response

```typescript
await page.route('**/api/users', async (route) => {
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify([
      { id: 1, name: 'Alice', email: 'alice@example.com' },
      { id: 2, name: 'Bob', email: 'bob@example.com' },
    ]),
  });
});
```

### Mock Error Responses

```typescript
// 404
await page.route('**/api/users/999', async (route) => {
  await route.fulfill({
    status: 404,
    contentType: 'application/json',
    body: JSON.stringify({ error: 'User not found' }),
  });
});

// 500 server error
await page.route('**/api/data', async (route) => {
  await route.fulfill({
    status: 500,
    contentType: 'application/json',
    body: JSON.stringify({ error: 'Internal server error' }),
  });
});

// Network error (no response at all)
await page.route('**/api/data', async (route) => {
  await route.abort('connectionrefused');
});
```

### Mock Based on Method

```typescript
await page.route('**/api/users', async (route) => {
  if (route.request().method() === 'GET') {
    await route.fulfill({
      status: 200,
      body: JSON.stringify([{ id: 1, name: 'Alice' }]),
    });
  } else if (route.request().method() === 'POST') {
    const body = JSON.parse(route.request().postData() ?? '{}');
    await route.fulfill({
      status: 201,
      body: JSON.stringify({ id: 3, ...body }),
    });
  } else {
    await route.continue();
  }
});
```

### Respond with a File

```typescript
await page.route('**/api/config', async (route) => {
  await route.fulfill({ path: 'test-data/config.json' });
});
```

## Modifying Responses

Fetch the real response, then modify it:

```typescript
await page.route('**/api/users', async (route) => {
  // Fetch real response
  const response = await route.fetch();
  const json = await response.json();

  // Modify it
  json.push({ id: 99, name: 'Test User', email: 'test@example.com' });

  // Return modified response
  await route.fulfill({
    response,
    body: JSON.stringify(json),
  });
});
```

### Modify Headers

```typescript
await page.route('**/*', async (route) => {
  const headers = {
    ...route.request().headers(),
    'X-Test-Header': 'test-value',
  };
  await route.continue({ headers });
});
```

## Aborting Requests

Block specific requests (useful for testing without images, ads, or analytics):

```typescript
// Block images
await page.route('**/*.{png,jpg,jpeg,gif,svg}', (route) => route.abort());

// Block analytics
await page.route('**/analytics/**', (route) => route.abort());
await page.route('**/google-analytics.com/**', (route) => route.abort());

// Block with specific error
await page.route('**/api/slow', (route) => route.abort('timedout'));
```

Abort reasons: `'aborted'`, `'accessdenied'`, `'addressunreachable'`, `'blockedbyclient'`, `'blockedbyresponse'`, `'connectionaborted'`, `'connectionclosed'`, `'connectionfailed'`, `'connectionrefused'`, `'connectionreset'`, `'internetdisconnected'`, `'namenotresolved'`, `'timedout'`, `'failed'`.

## Waiting for Network Events

### Wait for a Specific Request

```typescript
const requestPromise = page.waitForRequest('**/api/users');
await page.getByRole('button', { name: 'Load users' }).click();
const request = await requestPromise;
console.log(request.url());
```

### Wait for a Specific Response

```typescript
const responsePromise = page.waitForResponse('**/api/users');
await page.getByRole('button', { name: 'Load users' }).click();
const response = await responsePromise;
const data = await response.json();
expect(data).toHaveLength(5);
```

### Wait for Response with Predicate

```typescript
const response = await page.waitForResponse(
  (resp) => resp.url().includes('/api/users') && resp.status() === 200
);
```

### Combine with Actions

```typescript
// Click and wait for response in parallel
const [response] = await Promise.all([
  page.waitForResponse('**/api/save'),
  page.getByRole('button', { name: 'Save' }).click(),
]);
expect(response.status()).toBe(200);
```

## HAR Replay

Record and replay HTTP archive files for deterministic tests:

### Record HAR

```typescript
// In test
const context = await browser.newContext({
  recordHar: { path: 'test-data/api.har' },
});
// ... run tests ...
await context.close(); // HAR saved on close
```

### Replay HAR

```typescript
await page.routeFromHAR('test-data/api.har', {
  url: '**/api/**',
  update: false,
});
```

### Update HAR (re-record if no match)

```typescript
await page.routeFromHAR('test-data/api.har', {
  url: '**/api/**',
  update: true, // Falls through to real server and records new entries
});
```

### CLI-Based HAR Recording

```bash
# Record HAR file from codegen
npx playwright codegen --save-har=test-data/api.har https://example.com
```

## WebSocket Mocking

```typescript
// Intercept WebSocket connections
page.on('websocket', (ws) => {
  console.log(`WebSocket opened: ${ws.url()}`);

  ws.on('framesent', (event) => {
    console.log(`Sent: ${event.payload}`);
  });

  ws.on('framereceived', (event) => {
    console.log(`Received: ${event.payload}`);
  });

  ws.on('close', () => {
    console.log('WebSocket closed');
  });
});
```

### Mock WebSocket with Route

```typescript
await page.routeWebSocket('wss://example.com/ws', (ws) => {
  ws.onMessage((message) => {
    if (message === 'ping') {
      ws.send('pong');
    }
  });
});
```

## Common Pitfalls

1. **Route order matters** — routes are matched in registration order; register specific routes before general ones
2. **Forgetting to `await route.fulfill/continue/abort`** — hanging routes cause tests to time out
3. **Mocking too broadly** — `page.route('**/*', ...)` intercepts everything including the page itself
4. **Not removing routes** — use `await page.unroute('**/api/**')` when done, or routes persist for the page's lifetime
5. **HAR file size** — HAR files can be large; commit only what you need and use `url` filter during replay

## Related

- API Testing — `references/07-api-testing.md`
- Authentication — `references/08-authentication.md`
