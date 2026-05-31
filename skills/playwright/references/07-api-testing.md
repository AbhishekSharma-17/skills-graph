# Playwright — API Testing

> Source: [playwright.dev/docs/api-testing](https://playwright.dev/docs/api-testing) | Version: 1.59

## Overview

Playwright includes `APIRequestContext` for sending HTTP requests directly — no browser needed. Use it for:

- Testing REST/GraphQL APIs independently
- Setting up test data before UI tests (seed database via API)
- Validating server-side effects after UI actions
- Hybrid tests that combine API calls with browser interactions

## Setup

### Using the `request` Fixture

```typescript
import { test, expect } from '@playwright/test';

test('GET users returns 200', async ({ request }) => {
  const response = await request.get('/api/users');
  expect(response.ok()).toBeTruthy();
  expect(response.status()).toBe(200);

  const users = await response.json();
  expect(users.length).toBeGreaterThan(0);
});
```

### Configure baseURL

```typescript
// playwright.config.ts
export default defineConfig({
  use: {
    baseURL: 'http://localhost:3000',
  },
});
```

### Standalone API Context

For tests that don't need a browser at all:

```typescript
import { test, expect, request } from '@playwright/test';

let apiContext;

test.beforeAll(async () => {
  apiContext = await request.newContext({
    baseURL: 'https://api.example.com',
    extraHTTPHeaders: {
      Authorization: `Bearer ${process.env.API_TOKEN}`,
      Accept: 'application/json',
    },
  });
});

test.afterAll(async () => {
  await apiContext.dispose();
});

test('create user', async () => {
  const response = await apiContext.post('/users', {
    data: {
      name: 'Test User',
      email: 'test@example.com',
    },
  });
  expect(response.ok()).toBeTruthy();
});
```

## HTTP Methods

### GET

```typescript
const response = await request.get('/api/users');
const response = await request.get('/api/users', {
  params: { page: 1, limit: 10 },
});
```

### POST

```typescript
// JSON body
const response = await request.post('/api/users', {
  data: {
    name: 'Alice',
    email: 'alice@example.com',
  },
});

// Form data
const response = await request.post('/api/login', {
  form: {
    username: 'admin',
    password: 'secret',
  },
});

// Multipart form (file upload)
const response = await request.post('/api/upload', {
  multipart: {
    file: {
      name: 'document.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('pdf content'),
    },
    description: 'Test upload',
  },
});
```

### PUT / PATCH / DELETE

```typescript
await request.put('/api/users/1', {
  data: { name: 'Updated Name' },
});

await request.patch('/api/users/1', {
  data: { status: 'active' },
});

await request.delete('/api/users/1');
```

### HEAD / OPTIONS

```typescript
const response = await request.head('/api/health');
expect(response.status()).toBe(200);
```

## Response Handling

```typescript
const response = await request.get('/api/users');

// Status
response.status();       // 200
response.statusText();   // "OK"
response.ok();           // true (status 200-299)

// Headers
response.headers();                    // All headers
response.headers()['content-type'];   // Specific header

// Body
await response.json();    // Parse as JSON
await response.text();    // Raw text
await response.body();    // Buffer
```

## Hybrid Tests: API + Browser

### Setup Data via API, Verify via Browser

```typescript
test('create item via API and verify in UI', async ({ page, request }) => {
  // Create via API
  const response = await request.post('/api/items', {
    data: { name: 'Test Item', price: 29.99 },
  });
  expect(response.ok()).toBeTruthy();
  const item = await response.json();

  // Verify in browser
  await page.goto(`/items/${item.id}`);
  await expect(page.getByRole('heading')).toHaveText('Test Item');
  await expect(page.getByTestId('price')).toHaveText('$29.99');
});
```

### Authenticate via API, Browse as User

```typescript
test('admin dashboard after API login', async ({ page, request }) => {
  // Login via API
  const loginResponse = await request.post('/api/auth/login', {
    data: { email: 'admin@example.com', password: 'admin123' },
  });
  expect(loginResponse.ok()).toBeTruthy();

  // Cookies are shared between request and page in the same context
  await page.goto('/admin/dashboard');
  await expect(page.getByRole('heading')).toHaveText('Admin Dashboard');
});
```

### Verify Side Effects via API

```typescript
test('delete button removes item', async ({ page, request }) => {
  // Setup via API
  await request.post('/api/items', {
    data: { name: 'To Delete' },
  });

  // Delete via UI
  await page.goto('/items');
  await page.getByRole('row')
    .filter({ hasText: 'To Delete' })
    .getByRole('button', { name: 'Delete' })
    .click();
  await page.getByRole('button', { name: 'Confirm' }).click();

  // Verify via API
  const response = await request.get('/api/items');
  const items = await response.json();
  expect(items.find((i: any) => i.name === 'To Delete')).toBeUndefined();
});
```

## Custom Request Headers

```typescript
// Per-request headers
const response = await request.get('/api/data', {
  headers: {
    'X-Custom-Header': 'value',
    Authorization: 'Bearer my-token',
  },
});

// Default headers for all requests in config
export default defineConfig({
  use: {
    extraHTTPHeaders: {
      Accept: 'application/json',
      Authorization: `Bearer ${process.env.API_TOKEN}`,
    },
  },
});
```

## Common Pitfalls

1. **Forgetting `await` on response body methods** — `response.json()` is async
2. **Not disposing standalone contexts** — always `dispose()` contexts created with `request.newContext()`
3. **Cookie isolation** — `request` fixture shares cookies with `page` in the same test; standalone contexts have separate cookies
4. **Not checking `response.ok()`** — a 404 won't throw; check status explicitly
5. **Hardcoding URLs** — use `baseURL` in config so tests work across environments

## Related

- Network Mocking — `references/06-network-mocking.md`
- Authentication — `references/08-authentication.md`
- Configuration — `references/11-configuration-cli.md`
