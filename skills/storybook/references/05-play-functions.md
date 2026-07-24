# Storybook — Play Functions

> Source: https://storybook.js.org/docs/writing-stories/play-function | v10.5.3

## Table of Contents

- [Overview](#overview)
- [Basic Play Function](#basic-play-function)
- [Canvas Queries](#canvas-queries)
- [User Event Simulation](#user-event-simulation)
- [Screen Queries](#screen-queries)
- [Composing Play Functions](#composing-play-functions)
- [Assertions](#assertions)
- [Step Function](#step-function)
- [Debugging](#debugging)

## Overview

Play functions are small code snippets that execute after a story renders. They simulate user interactions — clicking, typing, selecting — and can assert on results. Play functions serve dual purposes: setting up a specific component state for development and running as interaction tests.

```typescript
import type { Meta, StoryObj } from '@storybook/react';
import { expect } from 'storybook/test';
import { LoginForm } from './LoginForm';

const meta = { component: LoginForm } satisfies Meta<typeof LoginForm>;
export default meta;
type Story = StoryObj<typeof meta>;

export const FilledForm: Story = {
  play: async ({ canvas, userEvent }) => {
    await userEvent.type(
      canvas.getByLabelText('Email'),
      'user@example.com'
    );
    await userEvent.type(
      canvas.getByLabelText('Password'),
      'secret123'
    );
    await userEvent.click(canvas.getByRole('button', { name: 'Log in' }));
    await expect(canvas.getByText('Welcome back!')).toBeInTheDocument();
  },
};
```

## Basic Play Function

Play functions are async functions that receive a context object:

```typescript
export const Clicked: Story = {
  play: async ({ canvas, userEvent }) => {
    const button = canvas.getByRole('button');
    await userEvent.click(button);
  },
};
```

### Context Properties

| Property | Description |
|----------|-------------|
| `canvas` | Scoped Testing Library queries (from component root) |
| `userEvent` | User interaction simulation |
| `args` | Current story arguments |
| `step` | Group interactions with labels |
| `mount` | Render component (for pre-render setup) |
| `context` | Full story context (for composing play functions) |

## Canvas Queries

The `canvas` object provides Testing Library queries scoped to the story's root element:

### Query Types

| Type | Returns | Throws |
|------|---------|--------|
| `getBy...` | Element | Error if not found |
| `queryBy...` | Element or null | Never |
| `findBy...` | Promise\<Element\> | Error if not found (async) |
| `getAllBy...` | Element[] | Error if none found |
| `queryAllBy...` | Element[] | Never (empty array) |
| `findAllBy...` | Promise\<Element[]\> | Error if none found (async) |

### Query Subjects (Priority Order)

Use the most accessible query first:

1. **`ByRole`** — Accessible role (`button`, `heading`, `textbox`)
2. **`ByLabelText`** — Associated `<label>` text
3. **`ByPlaceholderText`** — Placeholder value
4. **`ByText`** — Visible text content
5. **`ByDisplayValue`** — Input/textarea/select current value
6. **`ByAltText`** — `alt` attribute
7. **`ByTitle`** — `title` attribute
8. **`ByTestId`** — `data-testid` attribute (last resort)

### Query Examples

```typescript
play: async ({ canvas, userEvent }) => {
  // By role (preferred)
  const submitBtn = canvas.getByRole('button', { name: 'Submit' });
  const emailInput = canvas.getByRole('textbox', { name: /email/i });
  const heading = canvas.getByRole('heading', { level: 2 });

  // By label
  const password = canvas.getByLabelText('Password');

  // By text
  const message = canvas.getByText('Success!');
  const partial = canvas.getByText(/success/i);

  // By test ID (last resort)
  const widget = canvas.getByTestId('custom-widget');

  // Async (waits for element to appear)
  const result = await canvas.findByText('Loading complete');
}
```

## User Event Simulation

All `userEvent` methods must be awaited:

| Method | Description |
|--------|-------------|
| `click(element)` | Single click |
| `dblClick(element)` | Double click |
| `hover(element)` | Mouse enter |
| `unhover(element)` | Mouse leave |
| `tab()` | Tab key navigation |
| `type(element, 'text')` | Type text into input |
| `keyboard('{Shift}')` | Press keyboard key |
| `selectOptions(element, ['opt1'])` | Select dropdown option(s) |
| `deselectOptions(element, 'opt1')` | Deselect option |
| `clear(element)` | Clear input value |

### Typing with Options

```typescript
play: async ({ canvas, userEvent }) => {
  // Type with delay between keystrokes
  await userEvent.type(
    canvas.getByLabelText('Email'),
    'user@example.com',
    { delay: 100 }
  );

  // Clear then type
  const input = canvas.getByLabelText('Search');
  await userEvent.clear(input);
  await userEvent.type(input, 'new query');
}
```

### Keyboard Events

```typescript
play: async ({ userEvent }) => {
  await userEvent.keyboard('{Enter}');
  await userEvent.keyboard('{Escape}');
  await userEvent.keyboard('{Tab}');
  await userEvent.keyboard('{Shift>}{Tab}{/Shift}');  // Shift+Tab
}
```

### Select Options

```typescript
play: async ({ canvas, userEvent }) => {
  const select = canvas.getByRole('combobox', { name: 'Country' });
  await userEvent.selectOptions(select, ['US']);

  // Multi-select
  const multiSelect = canvas.getByRole('listbox');
  await userEvent.selectOptions(multiSelect, ['Option A', 'Option C']);
}
```

## Screen Queries

For elements rendered outside the story root (modals, dialogs, portals), use `screen`:

```typescript
import { screen } from 'storybook/test';

export const DialogOpen: Story = {
  play: async ({ canvas, userEvent }) => {
    // Click button inside story root
    await userEvent.click(
      canvas.getByRole('button', { name: 'Open dialog' })
    );

    // Query dialog rendered in a portal (outside story root)
    const dialog = screen.getByRole('dialog');
    await expect(dialog).toBeVisible();

    // Interact with dialog content
    await userEvent.click(
      screen.getByRole('button', { name: 'Confirm' })
    );
  },
};
```

`canvas` queries from the component root. `screen` queries from `document`.

## Composing Play Functions

Chain play functions from other stories to build workflows:

```typescript
export const EmptyForm: Story = {
  play: async ({ canvas }) => {
    await expect(canvas.getByLabelText('Email')).toHaveValue('');
  },
};

export const FilledForm: Story = {
  play: async ({ canvas, userEvent }) => {
    await userEvent.type(canvas.getByLabelText('Email'), 'test@test.com');
    await userEvent.type(canvas.getByLabelText('Password'), 'pass123');
  },
};

export const SubmittedForm: Story = {
  play: async ({ context, canvas, userEvent }) => {
    // Run previous story's play function
    await FilledForm.play(context);

    // Continue with additional interactions
    await userEvent.click(canvas.getByRole('button', { name: 'Submit' }));
    await expect(canvas.getByText('Form submitted')).toBeInTheDocument();
  },
};
```

## Assertions

Use `expect` from `storybook/test` for assertions:

```typescript
import { expect } from 'storybook/test';

play: async ({ canvas }) => {
  // Element presence
  await expect(canvas.getByText('Hello')).toBeInTheDocument();

  // Visibility
  await expect(canvas.getByRole('alert')).toBeVisible();

  // Attributes
  await expect(canvas.getByRole('button')).toBeDisabled();
  await expect(canvas.getByRole('link')).toHaveAttribute('href', '/home');

  // Values
  await expect(canvas.getByLabelText('Name')).toHaveValue('John');

  // CSS classes
  await expect(canvas.getByRole('button')).toHaveClass('btn-primary');

  // Text content
  await expect(canvas.getByRole('heading')).toHaveTextContent('Welcome');
}
```

All `expect` calls must be awaited.

## Step Function

Group interactions with descriptive labels for better debugging:

```typescript
export const CompleteCheckout: Story = {
  play: async ({ canvas, step, userEvent }) => {
    await step('Fill shipping address', async () => {
      await userEvent.type(canvas.getByLabelText('Street'), '123 Main St');
      await userEvent.type(canvas.getByLabelText('City'), 'Portland');
      await userEvent.selectOptions(canvas.getByLabelText('State'), ['OR']);
    });

    await step('Enter payment details', async () => {
      await userEvent.type(canvas.getByLabelText('Card'), '4242424242424242');
      await userEvent.type(canvas.getByLabelText('Expiry'), '12/25');
    });

    await step('Submit order', async () => {
      await userEvent.click(canvas.getByRole('button', { name: 'Place Order' }));
      await expect(canvas.getByText('Order confirmed')).toBeInTheDocument();
    });
  },
};
```

Steps appear as collapsible groups in the Interactions panel.

## Debugging

### Interactions Panel

The Interactions panel shows play function execution step-by-step:

- **Pause/resume** — Stop execution at any point
- **Step through** — Execute one interaction at a time
- **Rewind** — Go back to a previous step
- **Failure highlighting** — See exactly where an assertion failed

### Shareable Debugging

Each interaction test has a URL that can be shared — other developers can reproduce the exact failure without setting up the environment.

### Console Debugging

```typescript
play: async ({ canvas, userEvent }) => {
  const button = canvas.getByRole('button');
  console.log('Button found:', button.textContent);
  await userEvent.click(button);
}
```

## Common Pitfalls

1. **Not awaiting interactions** — Every `userEvent` and `expect` call must be awaited
2. **Using `screen` when `canvas` works** — Prefer `canvas` for scoped queries
3. **Fragile queries** — Prefer `ByRole` over `ByTestId`
4. **State leaking between stories** — Use `beforeEach` cleanup, not story-level state

## Related Topics

- [Interaction Testing](06-interaction-testing.md) — Full testing with spies and lifecycle
- [Writing Stories](02-writing-stories.md) — Story format basics
- [Args & Controls](03-args-controls.md) — Setting up component state
