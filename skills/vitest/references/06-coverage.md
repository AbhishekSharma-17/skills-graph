# Coverage

> Source: [vitest.dev/guide/coverage](https://vitest.dev/guide/coverage.html) | Version: 4.x

## Table of Contents

- [Coverage Providers](#coverage-providers)
- [Setup](#setup)
- [Configuration](#configuration)
- [Thresholds](#thresholds)
- [Reporters](#reporters)
- [Ignoring Code](#ignoring-code)
- [Custom Providers](#custom-providers)
- [CI Integration](#ci-integration)

---

## Coverage Providers

### V8 (Default)

Native code coverage via the V8 JavaScript engine. Fast, low memory, no pre-instrumentation.

- Works with: Node.js, Deno, Chromium-based browsers
- Since v3.2.0: uses AST-based remapping for accuracy matching Istanbul
- Best for: most projects, especially TypeScript/ESM

### Istanbul

Instrumented coverage via Babel. Battle-tested since 2012.

- Works with: any JavaScript runtime
- Requires pre-instrumentation step
- Higher memory and slower execution
- Best for: environments where V8 coverage is unavailable

## Setup

### Install Provider

```bash
# V8 (recommended)
npm install -D @vitest/coverage-v8

# Istanbul
npm install -D @vitest/coverage-istanbul
```

### Enable Coverage

```bash
# Via CLI
npx vitest run --coverage

# Via CLI with provider selection
npx vitest run --coverage.provider v8
```

```typescript
// Via config
export default defineConfig({
  test: {
    coverage: {
      enabled: true,
      provider: 'v8',
    },
  },
})
```

## Configuration

```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    coverage: {
      provider: 'v8',
      enabled: false,                // enable via CLI --coverage

      // File selection
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'node_modules',
        'test',
        '**/*.d.ts',
        '**/*.test.ts',
        '**/*.spec.ts',
        '**/types.ts',
      ],

      // Report configuration
      reporter: ['text', 'json', 'html', 'lcov'],
      reportsDirectory: './coverage',

      // Behavior
      all: true,                     // include uncovered files
      clean: true,                   // clean report dir before run
      skipFull: false,               // hide 100% covered files in text report

      // Watermarks (color thresholds in text report)
      watermarks: {
        statements: [50, 80],
        branches: [50, 80],
        functions: [50, 80],
        lines: [50, 80],
      },
    },
  },
})
```

### Include All Files

By default, coverage only includes files imported by tests. Set `all: true` to include uncovered files:

```typescript
coverage: {
  all: true,
  include: ['src/**/*.ts'],
}
```

## Thresholds

Enforce minimum coverage levels. Tests fail if coverage drops below thresholds:

```typescript
coverage: {
  thresholds: {
    lines: 80,
    branches: 80,
    functions: 80,
    statements: 80,
  },
}
```

### Per-File Thresholds

```typescript
coverage: {
  thresholds: {
    // Global defaults
    lines: 80,

    // Per-glob overrides
    'src/critical/**': {
      lines: 95,
      branches: 95,
    },
    'src/utils/**': {
      lines: 70,
    },
  },
}
```

### Auto-Update Thresholds

```typescript
coverage: {
  thresholds: {
    autoUpdate: true, // update thresholds in config when coverage improves
  },
}
```

## Reporters

### Built-in Reporters

| Reporter | Output | Use Case |
|----------|--------|----------|
| `text` | Terminal table | Local development |
| `text-summary` | Compact terminal summary | CI logs |
| `json` | JSON file | Programmatic processing |
| `json-summary` | Summary JSON | Dashboards |
| `html` | Interactive HTML report | Detailed review |
| `html-spa` | Single-page HTML | Standalone sharing |
| `lcov` | LCOV format | SonarQube, Codecov, Coveralls |
| `clover` | Clover XML | Jenkins |
| `cobertura` | Cobertura XML | Azure DevOps |

### Multiple Reporters

```typescript
coverage: {
  reporter: [
    'text',                          // terminal output
    ['json', { file: 'coverage.json' }],  // with options
    'html',
    'lcov',
  ],
}
```

### Output Files

```typescript
coverage: {
  reporter: ['json', 'lcov'],
  reportsDirectory: './coverage',
  // json → ./coverage/coverage-final.json
  // lcov → ./coverage/lcov.info
}
```

### Custom Reporters

```typescript
coverage: {
  reporter: [
    ['@vitest/custom-reporter', { someOption: true }],
    '/absolute/path/to/custom-reporter.cjs',
  ],
}
```

Custom reporters must extend Istanbul's `ReportBase` class.

### HTML Report with Vitest UI

```typescript
coverage: {
  reporter: ['html'],
}
```

Open the Vitest UI to view coverage inline:

```bash
npx vitest --ui --coverage
```

## Ignoring Code

### V8 Ignore Comments

```typescript
/* v8 ignore next */
const debug = process.env.DEBUG ? console.log : () => {}

/* v8 ignore start -- @preserve */
if (process.env.NODE_ENV === 'development') {
  enableDevTools()
}
/* v8 ignore stop */

/* v8 ignore if -- @preserve */
if (impossibleCondition) {
  handleEdgeCase()
}
```

### Istanbul Ignore Comments

```typescript
/* istanbul ignore next -- @preserve */
function unreachableHelper() {}

/* istanbul ignore if -- @preserve */
if (debugMode) {
  trace()
}

/* istanbul ignore else -- @preserve */
if (condition) {
  doWork()
} else {
  // ignored
}
```

### Supported Directives

| Directive | Description |
|-----------|-------------|
| `ignore next` | Ignore next line/statement |
| `ignore start` / `ignore stop` | Ignore block |
| `ignore if` | Ignore `if` branch |
| `ignore else` | Ignore `else` branch |
| `ignore file` | Ignore entire file |

**Note:** Add `-- @preserve` suffix to prevent TypeScript from stripping the comment.

## Custom Providers

```typescript
coverage: {
  provider: 'custom',
  customProviderModule: 'my-custom-coverage-provider',
}
```

The module must export a `CoverageProviderModule` implementing:
- `getProvider()` — returns a provider instance
- Provider implements `initialize()`, `resolveOptions()`, `clean()`, `onAfterSuiteRun()`, `reportCoverage()`, `generateCoverage()`

## CI Integration

### GitHub Actions

```yaml
- name: Run tests with coverage
  run: npx vitest run --coverage

- name: Upload coverage
  uses: codecov/codecov-action@v4
  with:
    file: ./coverage/lcov.info
```

### Enforce in CI

```typescript
coverage: {
  thresholds: {
    lines: 80,
    branches: 80,
    functions: 80,
    statements: 80,
  },
}
```

Tests will fail in CI if coverage drops below thresholds.

### Coverage for Changed Files Only

```bash
npx vitest run --coverage --changed HEAD~1
```

Or in config:

```typescript
coverage: {
  changed: true,
}
```

### AI Agent Optimization

Vitest auto-detects LLM environments and applies:
- `skipFull: true` — hide fully covered files
- `text-summary` reporter — compact output

---

**Related:** [08-cli-reporters.md](08-cli-reporters.md) for reporter details, [00-overview.md](00-overview.md) for setup
