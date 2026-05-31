# Playwright — Assertions

> Source: [playwright.dev/docs/test-assertions](https://playwright.dev/docs/test-assertions) | Version: 1.59

## Table of Contents

- [Web-First Assertions](#web-first-assertions)
- [Page Assertions](#page-assertions)
- [Locator Assertions](#locator-assertions)
- [Generic Assertions](#generic-assertions)
- [Soft Assertions](#soft-assertions)
- [Polling Assertions](#polling-assertions)
- [Snapshot Assertions](#snapshot-assertions)
- [Custom Matchers](#custom-matchers)
- [Common Pitfalls](#common-pitfalls)

## Web-First Assertions

Playwright assertions automatically retry until the expected condition is met or the timeout expires. This makes tests resilient to timing issues.

```typescript
// This retries until the element becomes visible (up to 5s default)
await expect(page.getByText('Success')).toBeVisible();

// NOT web-first — evaluates once, may be flaky
const text = await page.textContent('.result');
expect(text).toBe('Success'); // regular Jest-style assert, no retry
```

### Assertion Timeout

```typescript
// Per-assertion timeout
await expect(page.getByText('Loaded')).toBeVisible({ timeout: 10000 });

// Global assertion timeout in config
export default defineConfig({
  expect: {
    timeout: 10000,
  },
});
```

## Page Assertions

```typescript
// Title
await expect(page).toHaveTitle('Dashboard');
await expect(page).toHaveTitle(/Dashboard/);

// URL
await expect(page).toHaveURL('https://example.com/dashboard');
await expect(page).toHaveURL(/\/dashboard$/);

// Screenshot (visual comparison)
await expect(page).toHaveScreenshot('homepage.png');
```

## Locator Assertions

### Visibility and State

```typescript
await expect(page.getByRole('button')).toBeVisible();
await expect(page.getByRole('button')).toBeHidden();
await expect(page.getByRole('button')).toBeEnabled();
await expect(page.getByRole('button')).toBeDisabled();
await expect(page.getByLabel('Terms')).toBeChecked();
await expect(page.getByRole('textbox')).toBeEditable();
await expect(page.getByRole('textbox')).toBeFocused();
await expect(page.locator('.item')).toBeAttached();
```

### Text Content

```typescript
// Contains text (substring match)
await expect(page.getByTestId('status')).toContainText('success');

// Exact text
await expect(page.getByTestId('status')).toHaveText('Upload successful');

// Regex
await expect(page.getByTestId('count')).toHaveText(/\d+ items/);

// Array of texts (for multiple elements)
await expect(page.getByRole('listitem')).toHaveText([
  'First item',
  'Second item',
  'Third item',
]);
```

### Attributes and Properties

```typescript
// Attribute
await expect(page.getByRole('link')).toHaveAttribute('href', '/about');
await expect(page.locator('img')).toHaveAttribute('alt', /logo/i);

// CSS class
await expect(page.locator('.alert')).toHaveClass(/alert-success/);
await expect(page.locator('.btn')).toHaveClass('btn btn-primary');

// CSS property
await expect(page.locator('.box')).toHaveCSS('color', 'rgb(255, 0, 0)');

// ID
await expect(page.locator('.main')).toHaveId('main-content');

// Count
await expect(page.getByRole('listitem')).toHaveCount(5);
```

### Input Values

```typescript
// Input/textarea value
await expect(page.getByLabel('Email')).toHaveValue('user@test.com');
await expect(page.getByLabel('Email')).toHaveValue(/.*@test\.com/);

// Multiple values (multi-select)
await expect(page.getByLabel('Colors')).toHaveValues([/red/, /green/]);
```

### Negation

Every assertion supports `.not`:

```typescript
await expect(page.getByRole('button')).not.toBeDisabled();
await expect(page.getByText('Error')).not.toBeVisible();
await expect(page.getByRole('listitem')).not.toHaveCount(0);
```

## Generic Assertions

Non-retrying assertions for plain values:

```typescript
const value = await page.getByLabel('Email').inputValue();
expect(value).toBe('test@example.com');
expect(value).toContain('@');
expect(value).toMatch(/\S+@\S+/);

const count = await page.getByRole('listitem').count();
expect(count).toBeGreaterThan(0);
expect(count).toBeLessThanOrEqual(10);

// Truthiness
expect(await page.getByRole('button').isVisible()).toBeTruthy();

// Objects
const data = { name: 'test', value: 42 };
expect(data).toEqual({ name: 'test', value: 42 });
expect(data).toMatchObject({ name: 'test' });
```

## Soft Assertions

Soft assertions don't stop the test on failure — all failures are collected and reported together:

```typescript
await expect.soft(page.getByTestId('status')).toHaveText('Active');
await expect.soft(page.getByTestId('name')).toHaveText('John');
await expect.soft(page.getByTestId('role')).toHaveText('Admin');

// Test continues even if assertions above fail
// All failures reported at the end
```

Check if any soft assertions failed:

```typescript
await expect.soft(page.getByTestId('status')).toHaveText('Active');

if (test.info().errors.length) {
  // Some soft assertions failed — skip remaining actions
  return;
}
```

## Polling Assertions

For custom async conditions that Playwright doesn't have built-in assertions for:

```typescript
// Poll until condition is met
await expect.poll(async () => {
  const response = await page.request.get('/api/status');
  return response.json();
}, {
  message: 'API should return ready status',
  timeout: 30000,
  intervals: [1000, 2000, 5000],
}).toEqual({ status: 'ready' });
```

## Snapshot Assertions

### Screenshot Comparison

```typescript
// Full page
await expect(page).toHaveScreenshot('full-page.png');

// Element only
await expect(page.getByTestId('chart')).toHaveScreenshot('chart.png');

// With options
await expect(page).toHaveScreenshot('dashboard.png', {
  maxDiffPixels: 100,
  maxDiffPixelRatio: 0.01,
  threshold: 0.2,
  animations: 'disabled',
  mask: [page.getByTestId('timestamp')],
});
```

### Text Snapshots

```typescript
const text = await page.getByTestId('output').textContent();
expect(text).toMatchSnapshot('output.txt');
```

## Custom Matchers

Extend `expect` with project-specific assertions:

```typescript
// playwright.config.ts or a setup file
import { expect, Locator } from '@playwright/test';

expect.extend({
  async toHaveAriaLabel(locator: Locator, expected: string) {
    const actual = await locator.getAttribute('aria-label');
    const pass = actual === expected;
    return {
      pass,
      message: () => `Expected aria-label "${expected}", got "${actual}"`,
      name: 'toHaveAriaLabel',
      expected,
      actual,
    };
  },
});

// Usage
await expect(page.getByRole('button')).toHaveAriaLabel('Close dialog');
```

## Common Pitfalls

1. **Using non-retrying assertions for DOM state** — always use `await expect(locator).toBeVisible()` over `expect(await locator.isVisible()).toBe(true)`
2. **Asserting text before page loads** — web-first assertions handle this, but ensure you await them
3. **Too-tight snapshot thresholds** — set reasonable `maxDiffPixels` for visual comparisons, especially with anti-aliasing
4. **Forgetting `await` on assertions** — assertions are async; forgetting `await` means they never execute
5. **Not using soft assertions for multi-field validation** — when checking many fields on a form, soft assertions give a complete picture

## Related

- Visual Testing — `references/09-visual-testing.md`
- Locators — `references/01-locators.md`
- Actions — `references/02-actions.md`
