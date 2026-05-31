# Playwright — Locators

> Source: [playwright.dev/docs/locators](https://playwright.dev/docs/locators) | Version: 1.59

## Table of Contents

- [Overview](#overview)
- [Recommended Locators](#recommended-locators)
- [Locator Methods](#locator-methods)
- [Chaining and Filtering](#chaining-and-filtering)
- [Locator Strictness](#locator-strictness)
- [Frames and Shadow DOM](#frames-and-shadow-dom)
- [Common Pitfalls](#common-pitfalls)

## Overview

Locators are Playwright's core mechanism for finding elements. Unlike raw selectors, locators are lazy (they don't query the DOM until needed) and auto-retry (they wait for elements to match before timing out).

### Locator vs Selector

| Aspect | Selector (string) | Locator (object) |
|--------|-------------------|-------------------|
| Evaluation | Once, at call time | Lazy, at interaction time |
| Auto-waiting | No | Yes — waits for attached, visible, stable, enabled |
| Retry | No | Yes — re-queries DOM on each retry |
| Strictness | Returns first match | Throws if multiple matches (by default) |

## Recommended Locators

Playwright prioritizes user-facing locators. Use them in this order:

### 1. `getByRole` (Best)

Finds elements by their ARIA role and accessible name. Most resilient to DOM changes.

```typescript
// Button with text "Submit"
page.getByRole('button', { name: 'Submit' });

// Heading level 1
page.getByRole('heading', { name: 'Welcome', level: 1 });

// Checkbox
page.getByRole('checkbox', { name: 'Accept terms' });

// Navigation link
page.getByRole('link', { name: 'Home' });

// Text input
page.getByRole('textbox', { name: 'Email' });

// Combobox / select
page.getByRole('combobox', { name: 'Country' });

// With exact match (default is substring)
page.getByRole('button', { name: 'Log in', exact: true });
```

Common ARIA roles: `button`, `checkbox`, `combobox`, `dialog`, `heading`, `img`, `link`, `list`, `listitem`, `menu`, `menuitem`, `navigation`, `radio`, `row`, `tab`, `tabpanel`, `textbox`.

### 2. `getByLabel`

Finds form controls by their associated `<label>`.

```typescript
page.getByLabel('Email');
page.getByLabel('Password');
page.getByLabel(/remember me/i);
```

### 3. `getByPlaceholder`

Finds inputs by placeholder text.

```typescript
page.getByPlaceholder('Search...');
page.getByPlaceholder('Enter your email');
```

### 4. `getByText`

Finds elements containing the given text.

```typescript
page.getByText('Welcome back');
page.getByText(/error/i);
page.getByText('Submit', { exact: true });
```

### 5. `getByAltText`

Finds images by alt text.

```typescript
page.getByAltText('Company logo');
page.getByAltText(/profile/i);
```

### 6. `getByTitle`

Finds elements by title attribute.

```typescript
page.getByTitle('Close dialog');
```

### 7. `getByTestId`

Finds elements by `data-testid` attribute. Use when semantic locators aren't available.

```typescript
page.getByTestId('login-form');
page.getByTestId('submit-button');
```

Configure the attribute name in config:

```typescript
// playwright.config.ts
export default defineConfig({
  use: {
    testIdAttribute: 'data-test-id', // default: 'data-testid'
  },
});
```

### 8. `page.locator()` (CSS/XPath — Last Resort)

```typescript
// CSS selector
page.locator('.submit-btn');
page.locator('#email-input');
page.locator('article >> .title');

// XPath
page.locator('xpath=//button[@type="submit"]');
```

## Locator Methods

### Creating Locators

```typescript
// From page
const btn = page.getByRole('button', { name: 'Save' });

// From another locator (scoped)
const form = page.locator('form.login');
const submit = form.getByRole('button', { name: 'Log in' });

// Nth element
page.getByRole('listitem').nth(2);       // 0-indexed
page.getByRole('listitem').first();
page.getByRole('listitem').last();
```

### Counting Elements

```typescript
const count = await page.getByRole('listitem').count();

// Assert count
await expect(page.getByRole('listitem')).toHaveCount(5);
```

### Getting All Elements

```typescript
const items = page.getByRole('listitem');
const texts = await items.allTextContents();
const innerTexts = await items.allInnerTexts();
```

## Chaining and Filtering

### Filter by Text

```typescript
page.getByRole('listitem')
  .filter({ hasText: 'Product A' });

page.getByRole('listitem')
  .filter({ hasNotText: 'Out of stock' });
```

### Filter by Child Locator

```typescript
page.getByRole('listitem')
  .filter({ has: page.getByRole('button', { name: 'Buy' }) });

page.getByRole('listitem')
  .filter({ hasNot: page.getByText('Sold out') });
```

### Chaining Locators

```typescript
// Scope: find a button inside a specific dialog
page.getByRole('dialog')
  .getByRole('button', { name: 'Confirm' });

// Multiple filters
page.getByRole('row')
  .filter({ hasText: 'John' })
  .filter({ has: page.getByRole('button', { name: 'Edit' }) })
  .getByRole('button', { name: 'Edit' });
```

### `or` and `and`

```typescript
// Match either locator
const saveOrSubmit = page.getByRole('button', { name: 'Save' })
  .or(page.getByRole('button', { name: 'Submit' }));

// Match both conditions
const visibleError = page.getByText('Error')
  .and(page.locator(':visible'));
```

## Locator Strictness

By default, actions throw if a locator matches multiple elements:

```typescript
// Throws if multiple buttons match "Delete"
await page.getByRole('button', { name: 'Delete' }).click();
```

To target a specific one:

```typescript
// Use nth()
await page.getByRole('button', { name: 'Delete' }).nth(0).click();

// Use filter to narrow down
await page.getByRole('row')
  .filter({ hasText: 'Project Alpha' })
  .getByRole('button', { name: 'Delete' })
  .click();
```

## Frames and Shadow DOM

### Frames

```typescript
// By name or URL
const frame = page.frameLocator('iframe[name="editor"]');
await frame.getByRole('button', { name: 'Bold' }).click();

// Nested frames
page.frameLocator('#outer').frameLocator('#inner').getByText('Hello');
```

### Shadow DOM

Locators automatically pierce shadow DOM by default:

```typescript
// This works even if the button is inside a shadow root
await page.getByRole('button', { name: 'Menu' }).click();
```

## Common Pitfalls

1. **Using CSS selectors first** — always prefer `getByRole`, `getByLabel`, `getByText` for resilience
2. **Forgetting `exact: true`** — `getByText('Log')` matches "Log in", "Log out", "Blog"; use exact when needed
3. **Not scoping locators** — if multiple matching elements exist, chain from a parent or use `filter`
4. **Using `page.$()`** — this is the Puppeteer-style API; use `page.locator()` for auto-waiting
5. **XPath for dynamic content** — XPath is brittle; use semantic locators and filters instead

## Related

- Actions — `references/02-actions.md`
- Assertions — `references/03-assertions.md`
- Page Object Model — `references/04-page-object-model.md`
