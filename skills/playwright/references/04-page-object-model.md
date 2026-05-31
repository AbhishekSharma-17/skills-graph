# Playwright — Page Object Model

> Source: [playwright.dev/docs/pom](https://playwright.dev/docs/pom) | Version: 1.59

## Overview

The Page Object Model (POM) encapsulates page interactions into reusable classes. Each page or significant component of your application gets a class that contains its locators and actions. When the UI changes, you update one class instead of every test file.

### Benefits

- **Single source of truth** for locators — selector changes require one update
- **Readable tests** — tests read like user stories, not DOM queries
- **Reusable actions** — login, navigate, fill forms defined once
- **Reduced duplication** — common flows shared across test files

## Basic Page Object

```typescript
// pages/login-page.ts
import { type Page, type Locator } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.getByLabel('Email');
    this.passwordInput = page.getByLabel('Password');
    this.submitButton = page.getByRole('button', { name: 'Sign in' });
    this.errorMessage = page.getByRole('alert');
  }

  async goto() {
    await this.page.goto('/login');
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }
}
```

### Using in Tests

```typescript
// tests/login.spec.ts
import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/login-page';

test('successful login redirects to dashboard', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.goto();
  await loginPage.login('user@example.com', 'password123');

  await expect(page).toHaveURL(/.*dashboard/);
});

test('shows error for invalid credentials', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.goto();
  await loginPage.login('wrong@example.com', 'bad');

  await expect(loginPage.errorMessage).toContainText('Invalid credentials');
});
```

## Page Object with Navigation

```typescript
// pages/dashboard-page.ts
import { type Page, type Locator } from '@playwright/test';

export class DashboardPage {
  readonly page: Page;
  readonly heading: Locator;
  readonly profileLink: Locator;
  readonly logoutButton: Locator;
  readonly projectList: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.getByRole('heading', { name: 'Dashboard' });
    this.profileLink = page.getByRole('link', { name: 'Profile' });
    this.logoutButton = page.getByRole('button', { name: 'Log out' });
    this.projectList = page.getByRole('list', { name: 'Projects' });
  }

  async goto() {
    await this.page.goto('/dashboard');
  }

  async getProjectCount() {
    return await this.projectList.getByRole('listitem').count();
  }

  async openProject(name: string) {
    await this.projectList
      .getByRole('listitem')
      .filter({ hasText: name })
      .getByRole('link')
      .click();
  }

  async logout() {
    await this.logoutButton.click();
  }
}
```

## Component Page Objects

For reusable UI components (modals, navbars, sidebars):

```typescript
// components/navbar.ts
import { type Page, type Locator } from '@playwright/test';

export class Navbar {
  readonly container: Locator;
  readonly searchInput: Locator;
  readonly notificationBell: Locator;
  readonly userMenu: Locator;

  constructor(page: Page) {
    this.container = page.getByRole('navigation');
    this.searchInput = this.container.getByRole('searchbox');
    this.notificationBell = this.container.getByRole('button', { name: 'Notifications' });
    this.userMenu = this.container.getByRole('button', { name: /user menu/i });
  }

  async search(query: string) {
    await this.searchInput.fill(query);
    await this.searchInput.press('Enter');
  }

  async openNotifications() {
    await this.notificationBell.click();
  }
}
```

### Composing Page Objects

```typescript
// pages/app-page.ts
import { type Page } from '@playwright/test';
import { Navbar } from '../components/navbar';

export class AppPage {
  readonly page: Page;
  readonly navbar: Navbar;

  constructor(page: Page) {
    this.page = page;
    this.navbar = new Navbar(page);
  }
}
```

## Using Fixtures for Page Objects

Instead of creating page objects in every test, use fixtures:

```typescript
// fixtures.ts
import { test as base } from '@playwright/test';
import { LoginPage } from './pages/login-page';
import { DashboardPage } from './pages/dashboard-page';

type MyFixtures = {
  loginPage: LoginPage;
  dashboardPage: DashboardPage;
};

export const test = base.extend<MyFixtures>({
  loginPage: async ({ page }, use) => {
    await use(new LoginPage(page));
  },
  dashboardPage: async ({ page }, use) => {
    await use(new DashboardPage(page));
  },
});

export { expect } from '@playwright/test';
```

```typescript
// tests/dashboard.spec.ts
import { test, expect } from '../fixtures';

test('dashboard shows projects', async ({ dashboardPage }) => {
  await dashboardPage.goto();
  const count = await dashboardPage.getProjectCount();
  expect(count).toBeGreaterThan(0);
});
```

## Project Structure

```
tests/
├── fixtures.ts           # Extended test with page object fixtures
├── pages/
│   ├── login-page.ts
│   ├── dashboard-page.ts
│   └── settings-page.ts
├── components/
│   ├── navbar.ts
│   ├── modal.ts
│   └── data-table.ts
├── auth/
│   └── login.spec.ts
├── dashboard/
│   └── projects.spec.ts
└── settings/
    └── profile.spec.ts
```

## Design Guidelines

1. **Page objects expose actions, not elements** — tests call `loginPage.login(email, pass)`, not `loginPage.emailInput.fill(email)`
2. **Don't put assertions in page objects** — assertions belong in tests so failures point to the test, not the helper
3. **Keep page objects focused** — one class per page or major component, not one giant class for the whole app
4. **Use composition over inheritance** — compose page objects from component objects rather than extending base classes
5. **Locators in constructor, actions as methods** — define all locators upfront; expose user-level actions as async methods

## Common Pitfalls

1. **Too many page objects** — don't create a page object for a page with only 1-2 interactions
2. **Assertions inside page objects** — makes failures harder to trace; keep assertions in test files
3. **Exposing raw locators** — prefer action methods (`login()`) over leaking locators (`emailInput`)
4. **Not updating when UI changes** — the whole point is centralizing selectors; stale page objects defeat the purpose
5. **Over-abstracting** — a simple test with 3 lines doesn't need a page object wrapper

## Related

- Fixtures — `references/05-fixtures.md`
- Locators — `references/01-locators.md`
