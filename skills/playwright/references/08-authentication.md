# Playwright — Authentication

> Source: [playwright.dev/docs/auth](https://playwright.dev/docs/auth) | Version: 1.59

## Overview

Playwright's authentication strategy is based on **storage state** — saving cookies, localStorage, and sessionStorage to a JSON file, then reusing it across tests. This avoids logging in before every test, dramatically reducing execution time.

## Storage State Approach

### Step 1: Create Auth Setup Project

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  projects: [
    // Auth setup — runs first
    {
      name: 'setup',
      testMatch: /.*\.setup\.ts/,
    },
    // Tests — depend on setup
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'playwright/.auth/user.json',
      },
      dependencies: ['setup'],
    },
    {
      name: 'firefox',
      use: {
        ...devices['Desktop Firefox'],
        storageState: 'playwright/.auth/user.json',
      },
      dependencies: ['setup'],
    },
  ],
});
```

### Step 2: Write the Setup Script

```typescript
// tests/auth.setup.ts
import { test as setup, expect } from '@playwright/test';

const authFile = 'playwright/.auth/user.json';

setup('authenticate', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill('user@example.com');
  await page.getByLabel('Password').fill('password123');
  await page.getByRole('button', { name: 'Sign in' }).click();

  // Wait for authentication to complete
  await page.waitForURL('/dashboard');

  // Save storage state
  await page.context().storageState({ path: authFile });
});
```

### Step 3: Add to .gitignore

```
# .gitignore
playwright/.auth/
```

### How It Works

1. The `setup` project runs first, performs login, and saves cookies/storage to `user.json`
2. Each browser project depends on `setup` and loads the saved `storageState`
3. Tests start already authenticated — no login UI interaction needed

## API-Based Authentication

Faster than UI login — use the API to authenticate:

```typescript
// tests/auth.setup.ts
import { test as setup } from '@playwright/test';

const authFile = 'playwright/.auth/user.json';

setup('authenticate via API', async ({ request, context }) => {
  // Login via API
  await request.post('/api/auth/login', {
    data: {
      email: 'user@example.com',
      password: 'password123',
    },
  });

  // Save storage state (cookies from API response are stored)
  await context.storageState({ path: authFile });
});
```

## Multiple Roles

Test different user types (admin, regular user, etc.):

```typescript
// playwright.config.ts
export default defineConfig({
  projects: [
    { name: 'setup', testMatch: /.*\.setup\.ts/ },

    {
      name: 'admin tests',
      use: {
        storageState: 'playwright/.auth/admin.json',
      },
      dependencies: ['setup'],
    },
    {
      name: 'user tests',
      use: {
        storageState: 'playwright/.auth/user.json',
      },
      dependencies: ['setup'],
    },
  ],
});
```

```typescript
// tests/auth.setup.ts
import { test as setup } from '@playwright/test';

setup('authenticate as admin', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill('admin@example.com');
  await page.getByLabel('Password').fill('adminpass');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.waitForURL('/admin');
  await page.context().storageState({ path: 'playwright/.auth/admin.json' });
});

setup('authenticate as user', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill('user@example.com');
  await page.getByLabel('Password').fill('userpass');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.waitForURL('/dashboard');
  await page.context().storageState({ path: 'playwright/.auth/user.json' });
});
```

## Per-Test Authentication Override

For tests that need a different auth state:

```typescript
import { test } from '@playwright/test';

// This test uses no authentication
test.use({ storageState: { cookies: [], origins: [] } });

test('login page shows form', async ({ page }) => {
  await page.goto('/login');
  await expect(page.getByLabel('Email')).toBeVisible();
});
```

## Multi-Context: Testing Multi-User Scenarios

```typescript
test('admin can see user profile', async ({ browser }) => {
  // Create admin context
  const adminContext = await browser.newContext({
    storageState: 'playwright/.auth/admin.json',
  });
  const adminPage = await adminContext.newPage();

  // Create user context
  const userContext = await browser.newContext({
    storageState: 'playwright/.auth/user.json',
  });
  const userPage = await userContext.newPage();

  // Admin views user's profile
  await userPage.goto('/profile');
  const userId = await userPage.getByTestId('user-id').textContent();

  await adminPage.goto(`/admin/users/${userId}`);
  await expect(adminPage.getByRole('heading')).toHaveText(/User Profile/);

  await adminContext.close();
  await userContext.close();
});
```

## Session Refresh / Token Rotation

For apps with short-lived tokens:

```typescript
// fixtures.ts
import { test as base, expect } from '@playwright/test';

export const test = base.extend({
  page: async ({ page, request }, use) => {
    // Refresh token before each test if needed
    const response = await request.post('/api/auth/refresh');
    if (!response.ok()) {
      // Re-login if refresh fails
      await page.goto('/login');
      await page.getByLabel('Email').fill(process.env.TEST_USER!);
      await page.getByLabel('Password').fill(process.env.TEST_PASS!);
      await page.getByRole('button', { name: 'Sign in' }).click();
      await page.waitForURL('/dashboard');
    }
    await use(page);
  },
});
```

## Common Pitfalls

1. **Stale storage state** — if your app changes cookie names or auth flow, delete `playwright/.auth/` and re-run setup
2. **Not adding `.auth/` to `.gitignore`** — storage state files contain session tokens
3. **Using UI login in every test** — use storage state reuse; UI login adds seconds per test
4. **Shared accounts in parallel** — if tests mutate user data, each worker needs its own account (use `workerIndex`)
5. **Expired tokens in CI** — if setup runs once but tests take hours, tokens may expire; add a refresh mechanism

## Related

- Fixtures — `references/05-fixtures.md`
- API Testing — `references/07-api-testing.md`
- Configuration — `references/11-configuration-cli.md`
