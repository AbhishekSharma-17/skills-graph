# Playwright — Actions & Interactions

> Source: [playwright.dev/docs/input](https://playwright.dev/docs/input) | Version: 1.59

## Table of Contents

- [Auto-Waiting](#auto-waiting)
- [Click Actions](#click-actions)
- [Text Input](#text-input)
- [Dropdowns and Checkboxes](#dropdowns-and-checkboxes)
- [File Upload](#file-upload)
- [Drag and Drop](#drag-and-drop)
- [Keyboard Actions](#keyboard-actions)
- [Mouse Actions](#mouse-actions)
- [Dialogs](#dialogs)
- [Downloads](#downloads)
- [Common Pitfalls](#common-pitfalls)

## Auto-Waiting

Before performing any action, Playwright automatically waits for the element to be:

1. **Attached** to the DOM
2. **Visible** (non-zero bounding box, no `visibility: hidden`)
3. **Stable** (not animating, no layout shifts)
4. **Enabled** (no `disabled` attribute)
5. **Receiving events** (not obscured by overlays)

This eliminates the need for manual `waitFor` calls in most scenarios.

```typescript
// Playwright auto-waits for the button to be ready
await page.getByRole('button', { name: 'Submit' }).click();
```

### Controlling Timeouts

```typescript
// Per-action timeout
await page.getByRole('button').click({ timeout: 5000 });

// Global action timeout in config
export default defineConfig({
  use: {
    actionTimeout: 10000,
  },
});
```

## Click Actions

```typescript
// Standard click
await page.getByRole('button', { name: 'Submit' }).click();

// Double click
await page.getByText('word').dblclick();

// Right click (context menu)
await page.getByText('item').click({ button: 'right' });

// Modifier + click
await page.getByText('link').click({ modifiers: ['Shift'] });
await page.getByText('file').click({ modifiers: ['Control'] }); // or 'Meta' on Mac

// Click at position (relative to element center)
await page.getByAltText('map').click({ position: { x: 100, y: 200 } });

// Force click (skip actionability checks)
await page.getByRole('button').click({ force: true });

// Click and don't wait for navigation
await page.getByRole('link').click({ noWaitAfter: true });
```

## Text Input

### fill — Replace All Text

```typescript
await page.getByLabel('Email').fill('user@example.com');
await page.getByLabel('Password').fill('secret123');
```

`fill` clears existing content first and triggers `input` and `change` events.

### pressSequentially — Type Character by Character

```typescript
// Simulates real keystrokes (useful for autocomplete, debounced inputs)
await page.getByLabel('Search').pressSequentially('playwright', { delay: 100 });
```

### Clear Input

```typescript
await page.getByLabel('Email').clear();
// or
await page.getByLabel('Email').fill('');
```

## Dropdowns and Checkboxes

### Select Options

```typescript
// By value
await page.getByLabel('Country').selectOption('us');

// By label text
await page.getByLabel('Country').selectOption({ label: 'United States' });

// By index
await page.getByLabel('Country').selectOption({ index: 2 });

// Multiple selections
await page.getByLabel('Colors').selectOption(['red', 'green', 'blue']);
```

### Checkboxes and Radio Buttons

```typescript
// Check
await page.getByLabel('Accept terms').check();

// Uncheck
await page.getByLabel('Subscribe').uncheck();

// Check state assertion
await expect(page.getByLabel('Accept terms')).toBeChecked();
await expect(page.getByLabel('Newsletter')).not.toBeChecked();

// Set to specific state
await page.getByLabel('Dark mode').setChecked(true);
```

## File Upload

```typescript
// Single file
await page.getByLabel('Upload').setInputFiles('path/to/file.pdf');

// Multiple files
await page.getByLabel('Upload').setInputFiles([
  'path/to/file1.png',
  'path/to/file2.jpg',
]);

// Clear file input
await page.getByLabel('Upload').setInputFiles([]);

// From buffer (no file on disk)
await page.getByLabel('Upload').setInputFiles({
  name: 'test.txt',
  mimeType: 'text/plain',
  buffer: Buffer.from('file content'),
});
```

### File Chooser Dialog

```typescript
const fileChooser = await page.waitForEvent('filechooser');
await page.getByRole('button', { name: 'Upload' }).click();
await fileChooser.setFiles('path/to/file.pdf');
```

## Drag and Drop

```typescript
// Built-in drag and drop
await page.getByText('Drag me').dragTo(page.getByText('Drop here'));

// Manual drag with mouse
await page.locator('#source').hover();
await page.mouse.down();
await page.locator('#target').hover();
await page.mouse.up();
```

## Keyboard Actions

```typescript
// Press a key
await page.keyboard.press('Enter');
await page.keyboard.press('Tab');
await page.keyboard.press('Escape');

// Key combinations
await page.keyboard.press('Control+A');
await page.keyboard.press('Meta+C');       // Cmd+C on Mac
await page.keyboard.press('Shift+Enter');

// Press on a specific element
await page.getByLabel('Search').press('Enter');

// Hold modifier
await page.keyboard.down('Shift');
await page.getByText('Item 1').click();
await page.getByText('Item 5').click();
await page.keyboard.up('Shift');
```

### Special Keys

`Backspace`, `Tab`, `Delete`, `Escape`, `Enter`, `ArrowDown`, `ArrowUp`, `ArrowLeft`, `ArrowRight`, `Home`, `End`, `PageUp`, `PageDown`, `F1`-`F12`.

## Mouse Actions

```typescript
// Move to coordinates
await page.mouse.move(200, 300);

// Click at coordinates
await page.mouse.click(200, 300);

// Wheel scroll
await page.mouse.wheel(0, 500);  // scroll down
await page.mouse.wheel(0, -500); // scroll up

// Hover
await page.getByText('Menu').hover();
```

## Dialogs

Playwright auto-dismisses dialogs. Register handlers to interact:

```typescript
// Accept alert/confirm
page.on('dialog', dialog => dialog.accept());

// Dismiss
page.on('dialog', dialog => dialog.dismiss());

// Accept with input (prompt dialogs)
page.on('dialog', dialog => dialog.accept('my input'));

// One-time handler (preferred pattern)
page.once('dialog', async dialog => {
  expect(dialog.message()).toBe('Are you sure?');
  await dialog.accept();
});
await page.getByRole('button', { name: 'Delete' }).click();
```

## Downloads

```typescript
// Wait for download
const download = await page.waitForEvent('download');
await page.getByRole('link', { name: 'Download PDF' }).click();
const path = await download.path();
const suggestedName = download.suggestedFilename();

// Save to specific path
await download.saveAs('/tmp/report.pdf');

// Get download as stream
const stream = await download.createReadStream();
```

## Common Pitfalls

1. **Using `page.type()` instead of `fill()`** — `type()` is deprecated; use `fill()` for setting values or `pressSequentially()` for keystroke simulation
2. **Adding manual waits** — trust auto-waiting; use assertions to wait for state changes
3. **Forgetting dialog handlers** — unhandled dialogs auto-dismiss; set up handlers before triggering them
4. **Force-clicking by default** — `{ force: true }` skips safety checks; fix the underlying issue instead
5. **Not using `{ noWaitAfter: true }` for navigations** — useful when a click triggers a download, not a navigation

## Related

- Locators — `references/01-locators.md`
- Assertions — `references/03-assertions.md`
- Keyboard reference — [playwright.dev/docs/api/class-keyboard](https://playwright.dev/docs/api/class-keyboard)
