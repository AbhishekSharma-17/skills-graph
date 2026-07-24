# Storybook — Interaction Testing

> Source: https://storybook.js.org/docs/writing-tests/interaction-testing | v10.5.3

## Table of Contents

- [Overview](#overview)
- [Function Spying](#function-spying)
- [Mount Function](#mount-function)
- [Lifecycle Hooks](#lifecycle-hooks)
- [Mocking Modules](#mocking-modules)
- [Running Tests](#running-tests)
- [CI Integration](#ci-integration)
- [Test Coverage](#test-coverage)

## Overview

Interaction tests in Storybook are built into stories via play functions. They combine the authenticity of real browser rendering with the speed of unit tests. The Vitest addon converts stories into Vitest tests that run in browser mode.

Key advantages over standalone Vitest/Jest:

- Components render in a real browser, not jsdom
- Visual debugging through the Interactions panel
- Tests share the same setup as development stories
- No separate test file maintenance

## Function Spying

Use `fn()` from `storybook/test` to create spy functions that log to the Actions panel and can be asserted:

```typescript
import type { Meta, StoryObj } from '@storybook/react';
import { fn, expect } from 'storybook/test';
import { LoginForm } from './LoginForm';

const meta = {
  component: LoginForm,
  args: {
    onSubmit: fn(),
    onCancel: fn(),
  },
} satisfies Meta<typeof LoginForm>;

export default meta;
type Story = StoryObj<typeof meta>;

export const SubmitForm: Story = {
  play: async ({ args, canvas, userEvent }) => {
    await userEvent.type(canvas.getByLabelText('Email'), 'test@test.com');
    await userEvent.type(canvas.getByLabelText('Password'), 'secret');
    await userEvent.click(canvas.getByRole('button', { name: 'Log in' }));

    // Assert the callback was called with expected args
    await expect(args.onSubmit).toHaveBeenCalledWith({
      email: 'test@test.com',
      password: 'secret',
    });
    await expect(args.onCancel).not.toHaveBeenCalled();
  },
};
```

### Spy Assertion Methods

| Method | Checks |
|--------|--------|
| `toHaveBeenCalled()` | Function was invoked at least once |
| `toHaveBeenCalledTimes(n)` | Function was invoked exactly n times |
| `toHaveBeenCalledWith(arg1, arg2)` | Function called with specific arguments |
| `toHaveBeenLastCalledWith(arg)` | Last invocation had these arguments |
| `not.toHaveBeenCalled()` | Function was never invoked |

### spyOn for Non-Arg Functions

```typescript
import { spyOn } from 'storybook/test';

const preview: Preview = {
  async beforeEach() {
    spyOn(console, 'log').mockName('console.log');
  },
};
```

## Mount Function

The `mount` function controls when and how a component renders. Use it for pre-render setup:

### Mocking Before Render

```typescript
import MockDate from 'mockdate';

export const ChristmasTheme: Story = {
  async play({ mount }) {
    MockDate.set('2024-12-25');
    await mount();
    // Component renders with Christmas date
  },
};
```

### Rendering with Custom Props

```typescript
export const WithData: Story = {
  play: async ({ mount, args, userEvent }) => {
    const note = await db.note.create({
      data: { title: 'Test Note', body: 'Content' },
    });

    const canvas = await mount(
      <Page {...args} params={{ id: String(note.id) }} />
    );

    await userEvent.click(await canvas.findByRole('menuitem', { name: 'Edit' }));
  },
};
```

## Lifecycle Hooks

### beforeEach

Runs before each story renders. Return a cleanup function for teardown:

```typescript
const meta = {
  component: Dashboard,
  async beforeEach() {
    MockDate.set('2024-06-15');

    // Cleanup runs after the story unmounts
    return () => {
      MockDate.reset();
    };
  },
} satisfies Meta<typeof Dashboard>;
```

### Global beforeEach

```typescript
// .storybook/preview.ts
const preview: Preview = {
  async beforeEach() {
    // Reset all mocks between stories
    MockDate.reset();
  },
};
```

### beforeAll

One-time setup before any story runs:

```typescript
// .storybook/preview.ts
const preview: Preview = {
  async beforeAll() {
    await initializeTestDatabase();
  },
};
```

### afterEach

Post-test assertions or logging:

```typescript
const meta = {
  component: App,
  async afterEach(context) {
    console.log(`Tested: ${context.name}`);
  },
} satisfies Meta<typeof App>;
```

**Important**: Reset state in `beforeEach` cleanup functions, not `afterEach`. Cleanup functions are more reliable because they're tied to the story's lifecycle.

## Mocking Modules

Storybook can auto-mock imported modules for testing:

### Module Mocking in Stories

```typescript
import { expect } from 'storybook/test';
import { saveNote } from '../app/actions';

export const SaveFlow: Story = {
  play: async ({ canvas, userEvent }) => {
    await userEvent.click(
      canvas.getByRole('menuitem', { name: /save/i })
    );
    await expect(saveNote).toHaveBeenCalled();
  },
};
```

### Actions as Spies

```typescript
import { fn } from 'storybook/test';

const meta = {
  component: Form,
  args: {
    onSubmit: fn(),
    onChange: fn(),
  },
} satisfies Meta<typeof Form>;
```

Functions created with `fn()` automatically:
- Log calls to the Actions panel
- Act as Vitest spies for assertions
- Reset between stories

## Running Tests

### In Storybook UI

1. Open the testing widget in the sidebar
2. Click "Run component tests"
3. View results in the Interactions panel

### Via CLI

```bash
# Run all story tests via Vitest
npx vitest --project=storybook

# Watch mode
npx vitest --project=storybook --watch

# Specific story file
npx vitest --project=storybook Button.stories
```

### Package.json Script

```json
{
  "scripts": {
    "test-storybook": "vitest --project=storybook"
  }
}
```

### Watch Mode

Enable via the eye icon in the testing widget sidebar. Monitors code and test files, re-running only affected tests automatically.

## CI Integration

### Package.json Script

```json
{
  "scripts": {
    "test-storybook": "vitest --project=storybook"
  }
}
```

### GitHub Actions

Storybook tests use Playwright for browser rendering. Use a Playwright container image for CI:

```yaml
name: Storybook Tests
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    container:
      image: mcr.microsoft.com/playwright:v1.58.2-noble
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npm run test-storybook
```

## Test Coverage

### Enabling Coverage

Coverage is available through the testing widget. Check the "Coverage" checkbox and run tests. The coverage report shows:

- Overall line/branch coverage percentages
- Per-component coverage details
- Covered and uncovered code branches

### CLI Coverage

```bash
# Run all tests with coverage
npx vitest --coverage
```

### Coverage Configuration

Coverage is disabled by default due to performance impact. Enable it per-run rather than always-on for faster development feedback.

## Story Reusability

Stories can be imported into other test environments:

### In Playwright E2E Tests

```typescript
import { test, expect } from '@playwright/test';

test('button interaction', async ({ page }) => {
  await page.goto('http://localhost:6006/?path=/story/button--primary');
  // ...
});
```

### In Standalone Vitest

```typescript
import { composeStories } from '@storybook/react';
import * as stories from './Button.stories';

const { Primary, Secondary } = composeStories(stories);

test('renders primary button', () => {
  render(<Primary />);
  expect(screen.getByRole('button')).toHaveTextContent('Button');
});
```

## Common Pitfalls

1. **Not awaiting interactions** — Every `userEvent` and `expect` must be `await`ed
2. **Mixing `fn()` with `action()`** — `fn()` is spy-capable; `action()` is logging-only
3. **State leaking** — Clean up in `beforeEach` return function, not `afterEach`
4. **Container issues in CI** — Use Playwright container images for browser rendering
5. **Play function errors silently** — Check the Interactions panel for details

## Related Topics

- [Play Functions](05-play-functions.md) — Canvas queries and user events
- [Visual & A11y Testing](07-visual-a11y-testing.md) — Visual regression and accessibility
- [Sharing & Publishing](11-sharing-publishing.md) — CI/CD integration
