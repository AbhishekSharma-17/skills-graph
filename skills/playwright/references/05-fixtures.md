# Playwright — Fixtures & Hooks

> Source: [playwright.dev/docs/test-fixtures](https://playwright.dev/docs/test-fixtures) | Version: 1.59

## Table of Contents

- [Built-in Fixtures](#built-in-fixtures)
- [Custom Test Fixtures](#custom-test-fixtures)
- [Worker Fixtures](#worker-fixtures)
- [Automatic Fixtures](#automatic-fixtures)
- [Fixture Overrides](#fixture-overrides)
- [Test Hooks](#test-hooks)
- [Parameterized Tests](#parameterized-tests)
- [Common Pitfalls](#common-pitfalls)

## Built-in Fixtures

Playwright provides these fixtures out of the box:

| Fixture | Scope | Description |
|---------|-------|-------------|
| `page` | test | Isolated Page instance per test |
| `context` | test | Isolated BrowserContext per test |
| `browser` | worker | Shared Browser instance across tests in a worker |
| `browserName` | worker | `'chromium'`, `'firefox'`, or `'webkit'` |
| `request` | test | Isolated APIRequestContext per test |

```typescript
import { test, expect } from '@playwright/test';

test('uses built-in fixtures', async ({ page, context, browser, browserName }) => {
  console.log(`Running on ${browserName} version ${browser.version()}`);
  await page.goto('/');
  await expect(page).toHaveTitle(/Home/);
});
```

## Custom Test Fixtures

Extend the built-in `test` with your own fixtures:

```typescript
// fixtures.ts
import { test as base } from '@playwright/test';

type MyFixtures = {
  todoPage: TodoPage;
  defaultTodos: string[];
};

export const test = base.extend<MyFixtures>({
  // Fixture with setup and teardown
  todoPage: async ({ page }, use) => {
    // Setup: create page object
    const todoPage = new TodoPage(page);
    await todoPage.goto();

    // Provide fixture to test
    await use(todoPage);

    // Teardown: clean up (runs after test)
    await todoPage.removeAll();
  },

  // Simple value fixture
  defaultTodos: async ({}, use) => {
    await use(['Buy groceries', 'Clean house', 'Write tests']);
  },
});

export { expect } from '@playwright/test';
```

### Using Custom Fixtures

```typescript
import { test, expect } from './fixtures';

test('add a todo', async ({ todoPage, defaultTodos }) => {
  await todoPage.addTodo(defaultTodos[0]);
  await expect(todoPage.items).toHaveCount(1);
});
```

### Fixture Dependencies

Fixtures can depend on other fixtures:

```typescript
export const test = base.extend<{
  account: Account;
  loggedInPage: Page;
}>({
  account: async ({}, use) => {
    const account = await createTestAccount();
    await use(account);
    await deleteTestAccount(account);
  },

  loggedInPage: async ({ page, account }, use) => {
    await page.goto('/login');
    await page.getByLabel('Email').fill(account.email);
    await page.getByLabel('Password').fill(account.password);
    await page.getByRole('button', { name: 'Sign in' }).click();
    await use(page);
  },
});
```

## Worker Fixtures

Worker fixtures are shared across all tests in a single worker process. Use them for expensive, read-only resources:

```typescript
type WorkerFixtures = {
  dbConnection: DatabaseConnection;
  apiToken: string;
};

export const test = base.extend<{}, WorkerFixtures>({
  // Second generic parameter = worker fixtures
  dbConnection: [async ({}, use) => {
    const conn = await Database.connect();
    await use(conn);
    await conn.close();
  }, { scope: 'worker' }],

  apiToken: [async ({}, use) => {
    const token = await getServiceToken();
    await use(token);
  }, { scope: 'worker' }],
});
```

### Worker Index

Each worker gets a unique index for resource isolation:

```typescript
export const test = base.extend<{}, { dbName: string }>({
  dbName: [async ({}, use, workerInfo) => {
    const db = `test_db_${workerInfo.workerIndex}`;
    await createDatabase(db);
    await use(db);
    await dropDatabase(db);
  }, { scope: 'worker' }],
});
```

## Automatic Fixtures

Fixtures that run for every test without being explicitly requested:

```typescript
export const test = base.extend<{ autoSetup: void }>({
  autoSetup: [async ({ page }, use) => {
    // Runs before every test
    await page.addInitScript(() => {
      window.__TEST_MODE__ = true;
    });
    await use();
  }, { auto: true }],
});
```

## Fixture Overrides

Override built-in or custom fixtures in specific projects:

```typescript
// Override context to set locale
export const test = base.extend({
  context: async ({ browser }, use) => {
    const context = await browser.newContext({
      locale: 'fr-FR',
      timezoneId: 'Europe/Paris',
    });
    await use(context);
    await context.close();
  },
});
```

### Config-Level Overrides

```typescript
// playwright.config.ts
export default defineConfig({
  projects: [
    {
      name: 'admin',
      use: {
        storageState: 'auth/admin.json',
      },
    },
    {
      name: 'user',
      use: {
        storageState: 'auth/user.json',
      },
    },
  ],
});
```

## Test Hooks

### `test.beforeEach` / `test.afterEach`

```typescript
test.beforeEach(async ({ page }) => {
  await page.goto('/');
});

test.afterEach(async ({ page }, testInfo) => {
  if (testInfo.status !== 'passed') {
    await page.screenshot({ path: `failed-${testInfo.title}.png` });
  }
});
```

### `test.beforeAll` / `test.afterAll`

Run once per worker, before/after all tests in a file:

```typescript
test.beforeAll(async ({ browser }) => {
  // One-time setup per worker
});

test.afterAll(async () => {
  // Cleanup per worker
});
```

### Scoping with `describe`

```typescript
test.describe('checkout flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/cart');
  });

  test('shows cart items', async ({ page }) => {
    // ...
  });

  test('calculates total', async ({ page }) => {
    // ...
  });
});
```

## Parameterized Tests

### Using `test.describe` with a Loop

```typescript
const users = [
  { role: 'admin', canDelete: true },
  { role: 'editor', canDelete: false },
  { role: 'viewer', canDelete: false },
];

for (const { role, canDelete } of users) {
  test(`${role} ${canDelete ? 'can' : 'cannot'} delete items`, async ({ page }) => {
    await page.goto(`/login?role=${role}`);
    const deleteBtn = page.getByRole('button', { name: 'Delete' });
    if (canDelete) {
      await expect(deleteBtn).toBeEnabled();
    } else {
      await expect(deleteBtn).toBeDisabled();
    }
  });
}
```

### Using Fixture Options

```typescript
type TestOptions = {
  userRole: 'admin' | 'editor' | 'viewer';
};

export const test = base.extend<TestOptions>({
  userRole: ['viewer', { option: true }],
});

// In config
export default defineConfig({
  projects: [
    { name: 'admin', use: { userRole: 'admin' } },
    { name: 'viewer', use: { userRole: 'viewer' } },
  ],
});
```

## Common Pitfalls

1. **Sharing state between tests** — each test should be independent; use fixtures for setup, not shared variables
2. **Heavy worker fixtures** — worker fixtures share state; don't put mutable per-test data in them
3. **Forgetting teardown** — code after `await use()` runs as teardown; always clean up resources
4. **Overusing `beforeAll`** — prefer fixtures for setup; `beforeAll` doesn't integrate with the fixture lifecycle
5. **Not using `auto` fixtures** — for cross-cutting concerns (analytics mocking, error listeners), auto fixtures are cleaner than hooks

## Related

- Configuration — `references/11-configuration-cli.md`
- Authentication — `references/08-authentication.md`
- Page Object Model — `references/04-page-object-model.md`
