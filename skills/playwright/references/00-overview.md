# Playwright — Overview & Setup

> Source: [playwright.dev/docs/intro](https://playwright.dev/docs/intro) | Version: 1.59

## What Is Playwright

Playwright is a browser automation and end-to-end testing framework by Microsoft. It enables testing across Chromium, Firefox, and WebKit with a single API. Unlike Selenium or Cypress, Playwright runs out-of-process and supports all modern rendering engines.

### Key Differentiators

- **Multi-browser** — Chromium (Chrome, Edge), Firefox, WebKit (Safari) from a single API
- **Multi-language** — TypeScript, JavaScript, Python, .NET, Java
- **Auto-waiting** — waits for elements to be actionable before interactions
- **Web-first assertions** — assertions automatically retry until conditions are met
- **Isolation** — each test gets a fresh browser context (cookies, storage, sessions isolated)
- **Parallelism** — tests run in parallel across multiple workers by default
- **Tracing** — post-mortem debugging with trace viewer, screenshots, and videos
- **Codegen** — record user interactions and generate test code automatically

### When to Use Playwright

| Use Case | Fit |
|----------|-----|
| E2E testing of web apps | Primary use case |
| Cross-browser verification | Excellent — all 3 engines |
| API testing alongside UI | Built-in APIRequestContext |
| Visual regression testing | Built-in screenshot comparison |
| Component testing | Experimental but functional |
| Mobile web testing | Via device emulation |
| PDF/download testing | Supported |
| Web scraping/automation | Supported (use `playwright` core) |

## Installation

### New Project (Recommended)

```bash
# Interactive setup — creates config, example tests, GitHub Action
npm init playwright@latest
```

This prompts for:
- Language (TypeScript or JavaScript)
- Test directory name
- Whether to add a GitHub Actions workflow
- Whether to install browsers

### Existing Project

```bash
# Install the test runner
npm install -D @playwright/test

# Install browser binaries
npx playwright install

# Install only specific browsers
npx playwright install chromium
npx playwright install firefox webkit
```

### Python

```bash
pip install playwright
playwright install
```

## Project Structure

After initialization, a typical project looks like:

```
project/
├── playwright.config.ts     # Configuration file
├── package.json
├── tests/
│   └── example.spec.ts      # Test files (*.spec.ts or *.test.ts)
├── tests-examples/
│   └── demo-todo-app.spec.ts
├── .github/
│   └── workflows/
│       └── playwright.yml   # CI workflow
└── test-results/            # Generated on test run
```

## First Test

```typescript
import { test, expect } from '@playwright/test';

test('homepage has title', async ({ page }) => {
  await page.goto('https://playwright.dev/');

  // Expect title to contain "Playwright"
  await expect(page).toHaveTitle(/Playwright/);
});

test('get started link navigates to intro', async ({ page }) => {
  await page.goto('https://playwright.dev/');

  // Click the "Get started" link
  await page.getByRole('link', { name: 'Get started' }).click();

  // Expect the URL to contain "intro"
  await expect(page).toHaveURL(/.*intro/);
});
```

## Configuration Basics

The `playwright.config.ts` file controls test execution:

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',

  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

### Key Configuration Options

| Option | Purpose | Default |
|--------|---------|---------|
| `testDir` | Where tests live | `./tests` |
| `fullyParallel` | Parallelize tests within files | `false` |
| `retries` | Retry failed tests N times | `0` |
| `workers` | Number of parallel workers | 50% of CPU cores |
| `timeout` | Per-test timeout (ms) | `30000` |
| `reporter` | Output format | `'list'` |
| `use.baseURL` | Base URL for `page.goto('/')` | — |
| `use.trace` | When to record traces | `'off'` |
| `use.screenshot` | When to capture screenshots | `'off'` |
| `use.video` | When to record video | `'off'` |

## Running Tests

```bash
# Run all tests
npx playwright test

# Run specific file
npx playwright test tests/login.spec.ts

# Run tests matching a regex
npx playwright test -g "login"

# Run in headed mode (see the browser)
npx playwright test --headed

# Run on specific browser
npx playwright test --project=chromium

# Run with UI mode (interactive)
npx playwright test --ui

# Debug mode
npx playwright test --debug

# Generate HTML report
npx playwright show-report
```

## Browser Downloads and Management

```bash
# Install all browsers
npx playwright install

# Install specific browser
npx playwright install chromium

# Install system dependencies (Linux)
npx playwright install-deps

# Show installed browsers
npx playwright install --dry-run
```

### Browser Versions (v1.59)

- Chromium 147.0.7727.15
- Firefox 148.0.2
- WebKit 26.4

## Common Pitfalls

1. **Forgetting `await`** — all Playwright methods are async; missing `await` causes flaky tests
2. **Using `page.waitForTimeout()`** — anti-pattern; use locators and assertions that auto-wait
3. **Hardcoded selectors** — use semantic locators (getByRole, getByLabel) instead of CSS/XPath
4. **Not isolating tests** — each test should be independent; don't rely on test execution order
5. **Ignoring `webServer`** — configure it in `playwright.config.ts` to auto-start your dev server

## Related

- Locators — `references/01-locators.md`
- Configuration — `references/11-configuration-cli.md`
- CI/CD — `references/12-ci-cd.md`
