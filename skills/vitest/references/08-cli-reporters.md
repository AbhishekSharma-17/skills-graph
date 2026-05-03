# CLI & Reporters

> Source: [vitest.dev/guide/cli](https://vitest.dev/guide/cli.html) | [vitest.dev/guide/reporters](https://vitest.dev/guide/reporters.html) | Version: 4.x

## Table of Contents

- [Core Commands](#core-commands)
- [Test Filtering](#test-filtering)
- [Watch Mode](#watch-mode)
- [Sharding](#sharding)
- [Built-in Reporters](#built-in-reporters)
- [Reporter Configuration](#reporter-configuration)
- [Custom Reporters](#custom-reporters)
- [Output Files](#output-files)
- [Common CLI Patterns](#common-cli-patterns)

---

## Core Commands

### vitest

Start Vitest. Enters watch mode in development, run mode in CI:

```bash
npx vitest
```

### vitest run

Single run without watch mode:

```bash
npx vitest run
```

### vitest watch / vitest dev

Explicit watch mode:

```bash
npx vitest watch
```

### vitest bench

Run benchmark files only:

```bash
npx vitest bench
```

### vitest related

Run tests covering specific source files (great for lint-staged):

```bash
npx vitest related src/utils/math.ts src/utils/string.ts
```

### vitest list

Print matching test names without running them:

```bash
npx vitest list
npx vitest list --json          # JSON output
npx vitest list --filesOnly     # file paths only
```

### vitest init

Scaffold project configuration:

```bash
npx vitest init browser
```

## Test Filtering

### By Name Pattern

```bash
npx vitest -t "should add"           # match test name
npx vitest -t "/user.*create/i"      # regex pattern
```

### By File Path

```bash
npx vitest src/utils/               # directory
npx vitest math.test.ts             # specific file
npx vitest "src/**/*.unit.test.ts"  # glob pattern
```

### By Tags

```typescript
// In test file
test('creates user', { tags: ['integration', 'db'] }, () => { /* ... */ })
```

```bash
npx vitest --tagsFilter integration          # tests with tag
npx vitest --tagsFilter "integration & db"   # AND
npx vitest --tagsFilter "integration | api"  # OR
npx vitest --tagsFilter "!slow"              # NOT
npx vitest --listTags                        # list all tags
```

### By Project

```bash
npx vitest --project unit
npx vitest --project unit --project api
```

### By Changed Files

```bash
npx vitest --changed              # uncommitted changes
npx vitest --changed HEAD~1      # since last commit
npx vitest --changed main        # since branch point
```

## Watch Mode

### Interactive Commands

In watch mode, press:

| Key | Action |
|-----|--------|
| `a` | Run all tests |
| `f` | Run only failed tests |
| `u` | Update snapshots |
| `p` | Filter by filename |
| `t` | Filter by test name |
| `q` | Quit |
| `h` | Show help |
| `Enter` | Re-run |

### Watch Trigger Patterns

Re-run tests when non-test files change:

```typescript
export default defineConfig({
  test: {
    watchTriggerPatterns: [
      ['src/**/*.ts', 'test/**/*.test.ts'],
    ],
  },
})
```

## Sharding

Split tests across multiple CI jobs:

```bash
# Job 1 of 3
npx vitest run --shard 1/3

# Job 2 of 3
npx vitest run --shard 2/3

# Job 3 of 3
npx vitest run --shard 3/3
```

### Merge Shard Reports

```bash
# Each shard outputs blob reports
npx vitest run --shard 1/3 --reporter blob
npx vitest run --shard 2/3 --reporter blob
npx vitest run --shard 3/3 --reporter blob

# Merge after all shards complete
npx vitest --merge-reports
```

## Built-in Reporters

| Reporter | Description |
|----------|-------------|
| `default` | Summary with pass/fail status. Auto-selected. |
| `verbose` | Individual test results with immediate errors |
| `tree` | Hierarchical suite/test display |
| `dot` | Minimal — one dot per test |
| `json` | Jest-compatible JSON output |
| `junit` | XML for CI systems (Jenkins, GitLab) |
| `html` | Interactive dashboard (requires `@vitest/ui`) |
| `tap` | Test Anything Protocol (nested) |
| `tap-flat` | TAP as flat list |
| `github-actions` | GitHub Actions annotations |
| `minimal` / `agent` | LLM-optimized output for AI assistants |
| `hanging-process` | Identifies processes blocking exit |
| `blob` | Mergeable binary for sharded runs |

## Reporter Configuration

### Via CLI

```bash
npx vitest --reporter verbose
npx vitest --reporter json --reporter default   # multiple
```

### Via Config

```typescript
export default defineConfig({
  test: {
    reporters: ['verbose'],
  },
})
```

### Reporter-Specific Options

```typescript
// Default/verbose: disable summary
reporters: [['default', { summary: false }]]

// JUnit: custom suite name
reporters: [['junit', {
  suiteName: 'My Project Tests',
  classnameTemplate: '{filename}',
}]]

// JSON: filter metadata
reporters: [['json', {
  filterMeta: (key) => key !== 'internal',
}]]

// GitHub Actions: job summary
reporters: [['github-actions', {
  jobSummary: { enabled: true },
  displayAnnotations: true,
}]]
```

## Custom Reporters

### From npm Package

```typescript
reporters: ['some-published-vitest-reporter']
```

### Local File

```typescript
reporters: ['./src/test/my-reporter.ts']
```

### Reporter Interface

```typescript
import type { Reporter } from 'vitest/reporters'

export default class MyReporter implements Reporter {
  onInit(ctx) { /* Vitest initialized */ }
  onTestFileStart(file) { /* file starts */ }
  onTestCaseResult(result) { /* individual test done */ }
  onTestFileEnd(file) { /* file complete */ }
  onFinished(files, errors) { /* all done */ }
}
```

## Output Files

Write reports to disk:

```typescript
export default defineConfig({
  test: {
    reporters: ['json', 'junit', 'verbose'],
    outputFile: {
      json: './reports/test-results.json',
      junit: './reports/junit.xml',
    },
  },
})
```

## Common CLI Patterns

### CI Pipeline

```bash
npx vitest run --reporter json --reporter github-actions --outputFile reports/results.json
```

### Pre-commit Hook (lint-staged)

```json
{
  "*.{ts,tsx}": "vitest related --run"
}
```

### Debug a Single Test

```bash
npx vitest run src/utils/math.test.ts -t "should add" --reporter verbose
```

### Performance Profiling

```bash
npx vitest run --logHeapUsage
npx vitest run --slowTestThreshold 100
```

### Clear Cache

```bash
npx vitest --clearCache
```

### Standalone Mode

Start Vitest without running tests (for IDE integration):

```bash
npx vitest --standalone
```

### Key Timeout Options

```bash
npx vitest --testTimeout 10000      # per-test timeout (default 5000)
npx vitest --hookTimeout 30000      # lifecycle hook timeout (default 10000)
npx vitest --teardownTimeout 10000  # teardown timeout (default 10000)
```

### Detect Async Leaks

```bash
npx vitest --detectAsyncLeaks
```

### Node.js Inspector

```bash
npx vitest --inspect                # attach debugger
npx vitest --inspectBrk             # break on first line
```

---

**Related:** [06-coverage.md](06-coverage.md) for coverage reporters, [00-overview.md](00-overview.md) for config
