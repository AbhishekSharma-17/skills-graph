# Playwright — Configuration & CLI

> Source: [playwright.dev/docs/test-configuration](https://playwright.dev/docs/test-configuration) | Version: 1.59

## Table of Contents

- [Configuration File](#configuration-file)
- [Projects](#projects)
- [Reporters](#reporters)
- [Retries and Timeouts](#retries-and-timeouts)
- [Parallelism and Sharding](#parallelism-and-sharding)
- [CLI Commands](#cli-commands)
- [Test Filtering](#test-filtering)
- [Common Pitfalls](#common-pitfalls)

## Configuration File

Playwright looks for `playwright.config.ts` (or `.js`) in the project root.

### Complete Configuration Example

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  // Test directory
  testDir: './tests',

  // File patterns
  testMatch: '**/*.spec.ts',
  testIgnore: '**/helpers/**',

  // Parallel execution
  fullyParallel: true,
  workers: process.env.CI ? 1 : '50%',

  // Retries
  retries: process.env.CI ? 2 : 0,

  // Fail CI on test.only
  forbidOnly: !!process.env.CI,

  // Timeouts
  timeout: 30000,
  expect: {
    timeout: 5000,
    toHaveScreenshot: {
      maxDiffPixels: 50,
    },
  },

  // Reporter
  reporter: process.env.CI
    ? [['html'], ['junit', { outputFile: 'results.xml' }]]
    : 'list',

  // Output
  outputDir: 'test-results',

  // Global setup/teardown
  globalSetup: './global-setup.ts',
  globalTeardown: './global-teardown.ts',

  // Shared settings for all projects
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 10000,
    navigationTimeout: 30000,
    locale: 'en-US',
    timezoneId: 'America/New_York',
    colorScheme: 'dark',
    geolocation: { longitude: -73.935, latitude: 40.730 },
    permissions: ['geolocation'],
  },

  // Browser projects
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
  ],

  // Dev server
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
```

## Projects

Projects let you run the same tests with different configurations:

### Multi-Browser

```typescript
projects: [
  { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
  { name: 'webkit', use: { ...devices['Desktop Safari'] } },
]
```

### Mobile Devices

```typescript
projects: [
  { name: 'Mobile Chrome', use: { ...devices['Pixel 5'] } },
  { name: 'Mobile Safari', use: { ...devices['iPhone 13'] } },
  { name: 'Tablet', use: { ...devices['iPad Pro 11'] } },
]
```

### Project Dependencies

```typescript
projects: [
  { name: 'setup', testMatch: /.*\.setup\.ts/ },
  {
    name: 'chromium',
    use: { ...devices['Desktop Chrome'], storageState: 'auth.json' },
    dependencies: ['setup'],
  },
]
```

### Teardown Projects

```typescript
projects: [
  {
    name: 'setup db',
    testMatch: /global\.setup\.ts/,
    teardown: 'cleanup db',
  },
  {
    name: 'cleanup db',
    testMatch: /global\.teardown\.ts/,
  },
  {
    name: 'tests',
    dependencies: ['setup db'],
  },
]
```

## Reporters

### Built-in Reporters

| Reporter | Description | Output |
|----------|-------------|--------|
| `'list'` | One line per test (default) | Terminal |
| `'dot'` | Minimal — one dot per test | Terminal |
| `'line'` | Single updating line | Terminal |
| `'html'` | Interactive HTML report | `playwright-report/` |
| `'json'` | Machine-readable JSON | File |
| `'junit'` | CI-friendly XML | File |
| `'github'` | GitHub Actions annotations | Terminal |
| `'blob'` | Binary format for merging shards | File |

### Configuration

```typescript
// Single reporter
reporter: 'html',

// Multiple reporters
reporter: [
  ['list'],
  ['html', { open: 'never' }],
  ['junit', { outputFile: 'results/junit.xml' }],
  ['json', { outputFile: 'results/report.json' }],
],
```

### HTML Report

```bash
# Open after test run
npx playwright show-report

# Auto-open on failure
reporter: [['html', { open: 'on-failure' }]],

# Custom output directory
reporter: [['html', { outputFolder: 'my-report' }]],
```

## Retries and Timeouts

### Retries

```typescript
// Config level
retries: 2,

// Per-project
projects: [
  { name: 'chromium', retries: 3 },
]

// CLI
// npx playwright test --retries=2
```

### Test Categorization with Retries

When retries are enabled, tests have three outcomes:
- **passed** — passed on first attempt
- **flaky** — failed first, passed on retry
- **failed** — failed all attempts

### Timeouts

```typescript
export default defineConfig({
  // Global test timeout
  timeout: 30000,

  // Assertion timeout
  expect: { timeout: 5000 },

  use: {
    // Per-action timeout (click, fill, etc.)
    actionTimeout: 10000,

    // Navigation timeout (goto, reload, etc.)
    navigationTimeout: 30000,
  },
});
```

Per-test override:

```typescript
test('slow operation', async ({ page }) => {
  test.setTimeout(120000);
  // ...
});

// Slow modifier (multiplies default timeout)
test('heavy page', async ({ page }) => {
  test.slow(); // 3x the default timeout
});
```

## Parallelism and Sharding

### Workers (Single Machine)

```typescript
// Number of parallel workers
workers: 4,

// Percentage of CPU cores
workers: '50%',

// Disable parallel (one test at a time)
workers: 1,
```

### Fully Parallel

```typescript
// All tests across all files run in parallel
fullyParallel: true,
```

### Serial Execution

```typescript
test.describe.serial('ordered tests', () => {
  test('step 1', async ({ page }) => { /* ... */ });
  test('step 2', async ({ page }) => { /* ... */ });
  test('step 3', async ({ page }) => { /* ... */ });
});
```

### Sharding (Multi-Machine)

Split tests across CI machines:

```bash
# Machine 1
npx playwright test --shard=1/3

# Machine 2
npx playwright test --shard=2/3

# Machine 3
npx playwright test --shard=3/3
```

### Merging Shard Reports

```bash
# Each shard produces a blob report
npx playwright test --shard=1/3 --reporter=blob

# Merge blob reports into HTML
npx playwright merge-reports --reporter=html ./blob-reports
```

## CLI Commands

```bash
# Core commands
npx playwright test                    # Run all tests
npx playwright test --headed           # Run with browser visible
npx playwright test --ui               # Interactive UI mode
npx playwright test --debug            # Debug mode with inspector
npx playwright show-report             # Open HTML report
npx playwright codegen                 # Record tests
npx playwright show-trace trace.zip    # Open trace viewer

# Browser management
npx playwright install                 # Install all browsers
npx playwright install chromium        # Install one browser
npx playwright install-deps            # Install OS dependencies

# Filtering
npx playwright test -g "login"         # Grep test titles
npx playwright test tests/auth/        # Run directory
npx playwright test login.spec.ts      # Run file
npx playwright test --project=chromium # Run project

# Sharding
npx playwright test --shard=1/3        # Run shard
npx playwright merge-reports ./blobs   # Merge shard reports

# Output control
npx playwright test --reporter=list    # Override reporter
npx playwright test --output=results   # Output directory
npx playwright test --update-snapshots # Update baselines
```

## Test Filtering

### By Title

```bash
npx playwright test -g "login"
npx playwright test --grep "checkout|payment"
npx playwright test --grep-invert "slow"
```

### By Tag

```typescript
test('fast @smoke', async ({ page }) => { /* ... */ });
test('detailed @regression', async ({ page }) => { /* ... */ });
```

```bash
npx playwright test --grep @smoke
npx playwright test --grep-invert @regression
```

### By File

```bash
npx playwright test tests/auth/
npx playwright test login.spec.ts checkout.spec.ts
npx playwright test tests/auth/login.spec.ts:25  # Specific line
```

### Skip and Focus

```typescript
test.skip('broken test', async () => { /* ... */ });
test.fixme('known issue', async () => { /* ... */ });
test.only('focus this', async () => { /* ... */ }); // Forbidden in CI with forbidOnly
test.fail('expected to fail', async () => { /* ... */ });
```

### Conditional Skip

```typescript
test('webkit only', async ({ page, browserName }) => {
  test.skip(browserName !== 'webkit', 'WebKit-specific test');
  // ...
});
```

## Common Pitfalls

1. **Not setting `forbidOnly` in CI** — `test.only` accidentally left in code passes CI without it
2. **Too many workers in CI** — CI machines often have limited resources; start with `workers: 1`
3. **Global setup without teardown** — always pair `globalSetup` with `globalTeardown`
4. **Ignoring flaky tests** — retries mask flaky tests; review and fix them, don't just increase retries
5. **Not using `webServer`** — manually starting the dev server is error-prone; let Playwright manage it

## Related

- CI/CD — `references/12-ci-cd.md`
- Fixtures — `references/05-fixtures.md`
- Tracing — `references/10-tracing-debugging.md`
