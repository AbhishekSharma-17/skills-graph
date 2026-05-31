# Playwright — Tracing & Debugging

> Source: [playwright.dev/docs/trace-viewer](https://playwright.dev/docs/trace-viewer) | Version: 1.59

## Table of Contents

- [Trace Viewer](#trace-viewer)
- [Recording Traces](#recording-traces)
- [Debug Mode](#debug-mode)
- [UI Mode](#ui-mode)
- [Codegen](#codegen)
- [Inspector](#inspector)
- [Console and Network Logs](#console-and-network-logs)
- [Common Pitfalls](#common-pitfalls)

## Trace Viewer

The Trace Viewer is a GUI tool for post-mortem debugging. It shows every action, screenshot, DOM snapshot, network request, and console log from a test run.

### What Traces Capture

- **Timeline** — chronological view of all actions
- **Screenshots** — before/after each action
- **DOM Snapshots** — inspectable DOM at each step
- **Network** — all HTTP requests and responses
- **Console** — browser console messages
- **Source** — test source code with execution pointer
- **Errors** — stack traces for failures

### Opening Traces

```bash
# Open trace file
npx playwright show-trace trace.zip

# Open from test results
npx playwright show-trace test-results/test-name/trace.zip

# View online (upload trace.zip)
# https://trace.playwright.dev
```

## Recording Traces

### In Configuration

```typescript
// playwright.config.ts
export default defineConfig({
  use: {
    // Record trace for each test
    trace: 'on',

    // Record only on first retry (recommended for CI)
    trace: 'on-first-retry',

    // Record only on failure
    trace: 'retain-on-failure',

    // Never record
    trace: 'off',
  },
});
```

### Per Test

```typescript
test('checkout flow', async ({ page, context }) => {
  // Start tracing
  await context.tracing.start({ screenshots: true, snapshots: true });

  await page.goto('/checkout');
  await page.getByRole('button', { name: 'Pay' }).click();

  // Stop and save trace
  await context.tracing.stop({ path: 'checkout-trace.zip' });
});
```

### Trace Options

```typescript
await context.tracing.start({
  screenshots: true,  // Capture screenshots on each action
  snapshots: true,     // Capture DOM snapshots
  sources: true,       // Include test source code
  title: 'Checkout Flow',
});
```

## Debug Mode

### Headed Debug

```bash
# Run all tests in debug mode
npx playwright test --debug

# Debug specific test
npx playwright test tests/login.spec.ts --debug

# Debug specific line
npx playwright test tests/login.spec.ts:15 --debug
```

Debug mode:
- Opens a browser window (headed)
- Opens the Playwright Inspector
- Pauses at each action
- Lets you step through, inspect locators, and resume

### CLI Debug (v1.59)

For AI agents and headless debugging:

```bash
npx playwright test --debug=cli
```

Prints an attach command and allows stepping through failures from the terminal.

### Debug in Code

```typescript
test('debug this test', async ({ page }) => {
  await page.goto('/');

  // Pause here — opens Inspector
  await page.pause();

  // Continue test after manual inspection
  await page.getByRole('button').click();
});
```

### Environment Variable

```bash
# Enable headed + inspector for all tests
PWDEBUG=1 npx playwright test
```

## UI Mode

Interactive test runner with live reload:

```bash
npx playwright test --ui
```

UI Mode features:
- **Watch mode** — re-runs tests on file changes
- **Time travel** — click any action to see the page state at that moment
- **Locator picker** — visually pick elements and get recommended locators
- **Filter** — filter by test name, status, or tag
- **Trace-like view** — action log, DOM snapshot, console, network

### UI Mode Configuration

```typescript
// playwright.config.ts
export default defineConfig({
  use: {
    // Trace is always 'on' in UI mode
    // These affect the UI mode experience:
    video: 'on',
    screenshot: 'on',
  },
});
```

## Codegen

Record browser interactions and generate test code:

```bash
# Open codegen with a URL
npx playwright codegen https://example.com

# With specific device
npx playwright codegen --device="iPhone 13" https://example.com

# With specific viewport
npx playwright codegen --viewport-size=1280,720 https://example.com

# Save to file
npx playwright codegen --output tests/recorded.spec.ts https://example.com

# With authentication state
npx playwright codegen --load-storage=auth.json https://example.com
```

### Codegen Features

- **Smart locators** — prioritizes `getByRole`, `getByLabel`, `getByText` over CSS
- **Assertion generation** — generates `toBeVisible()` assertions for interactions
- **Action recording** — records clicks, fills, selects, navigations
- **Multi-page** — handles new tabs and popups

### pickLocator (v1.59)

Programmatically launch the locator picker:

```typescript
// In debug mode, pick a locator interactively
const locator = await page.pickLocator();
```

## Inspector

The Playwright Inspector is a toolbar that appears in debug mode:

### Inspector Features

- **Step over** — execute one action at a time
- **Resume** — continue until the next breakpoint or `page.pause()`
- **Record** — start recording new actions
- **Locator** — type a locator and see what it matches (highlighted in the browser)
- **Actionability log** — see why an action is waiting (element not visible, not stable, etc.)

### Locator Exploration

```bash
# Open a browser with the locator exploration panel
npx playwright open https://example.com
```

## Console and Network Logs

### Capturing Console Messages

```typescript
// Listen for all console messages
page.on('console', (msg) => {
  console.log(`[${msg.type()}] ${msg.text()}`);
});

// Listen for errors only
page.on('console', (msg) => {
  if (msg.type() === 'error') {
    console.error(`Browser error: ${msg.text()}`);
  }
});

// Capture page errors (uncaught exceptions)
page.on('pageerror', (error) => {
  console.error(`Page error: ${error.message}`);
});
```

### Monitoring Network

```typescript
// Log all requests
page.on('request', (request) => {
  console.log(`>> ${request.method()} ${request.url()}`);
});

// Log all responses
page.on('response', (response) => {
  console.log(`<< ${response.status()} ${response.url()}`);
});

// Log failed requests
page.on('requestfailed', (request) => {
  console.log(`FAILED: ${request.url()} - ${request.failure()?.errorText}`);
});
```

### Videos

```typescript
// playwright.config.ts
export default defineConfig({
  use: {
    video: 'on-first-retry',    // Record video on retry
    video: 'retain-on-failure', // Keep video only for failures
    video: 'on',                // Always record
  },
});
```

Access video in test:

```typescript
test.afterEach(async ({}, testInfo) => {
  if (testInfo.status !== 'passed') {
    const video = testInfo.attachments.find(a => a.name === 'video');
    console.log('Video:', video?.path);
  }
});
```

## Common Pitfalls

1. **Traces on every test in CI** — use `'on-first-retry'` to save only when needed; traces are large files
2. **Not uploading trace artifacts** — always upload `test-results/` as artifacts in CI for debugging failures
3. **Overusing `page.pause()`** — remove debug pauses before committing; they'll hang CI
4. **Ignoring console errors** — browser errors can indicate real bugs; add a listener and fail on unexpected errors
5. **Not using UI mode locally** — it's the fastest way to develop and debug tests

## Related

- Configuration — `references/11-configuration-cli.md`
- CI/CD — `references/12-ci-cd.md`
- Visual Testing — `references/09-visual-testing.md`
