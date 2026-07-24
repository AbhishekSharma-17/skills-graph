# Storybook — Visual & Accessibility Testing

> Source: https://storybook.js.org/docs/writing-tests/visual-testing | https://storybook.js.org/docs/writing-tests/accessibility-testing | v10.5.3

## Table of Contents

- [Visual Testing](#visual-testing)
- [Chromatic Integration](#chromatic-integration)
- [Visual Test Workflow](#visual-test-workflow)
- [Accessibility Testing](#accessibility-testing)
- [A11y Addon Setup](#a11y-addon-setup)
- [A11y Configuration](#a11y-configuration)
- [WCAG Standards](#wcag-standards)
- [Rule Management](#rule-management)
- [Test Behavior Levels](#test-behavior-levels)
- [Progressive A11y Workflow](#progressive-a11y-workflow)
- [Snapshot Testing](#snapshot-testing)

## Visual Testing

Visual tests capture pixel-based snapshots of every story and compare them against baselines. They catch UI regressions that unit tests and interaction tests miss — layout shifts, color changes, font rendering issues, and broken responsive designs.

### Visual vs Snapshot Tests

| Aspect | Visual Tests | Snapshot Tests |
|--------|-------------|----------------|
| Compares | Rendered pixels | HTML markup |
| False positives | Few | Many |
| Catches | Visual regressions | Markup changes |
| Tool | Chromatic | Vitest/Jest |
| Cost | Paid service | Free |

## Chromatic Integration

Chromatic is the official visual testing service built by the Storybook team. Every story automatically becomes a visual test.

### Installation

```bash
npx storybook@latest add @chromatic-com/storybook
```

### Setup

1. Sign up at chromatic.com
2. Create a project and get a token
3. Install the CLI:

```bash
npm install chromatic --save-dev
```

4. Run visual tests:

```bash
npx chromatic --project-token=<your-token>
```

### Configuration

Create `chromatic.config.json`:

```json
{
  "projectId": "Project:abc123",
  "buildScriptName": "build-storybook",
  "zip": true,
  "debug": false
}
```

| Option | Purpose |
|--------|---------|
| `projectId` | Auto-configured project identifier |
| `buildScriptName` | Custom build script name |
| `zip` | Compress uploads (recommended for large projects) |
| `debug` | Verbose console output |

## Visual Test Workflow

1. **Establish baselines** — First run captures initial snapshots
2. **Develop** — Make component changes
3. **Run tests** — Chromatic captures new snapshots
4. **Review changes** — Stories with visual diffs are highlighted in yellow
5. **Accept or reject** — Accept intentional changes as new baselines; fix regressions

### In Storybook UI

Use the testing widget sidebar or the Visual Tests addon panel to trigger test runs. Results appear inline with stories.

### CI Integration

```yaml
# GitHub Actions
name: Visual Tests
on: push
jobs:
  chromatic:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - uses: chromaui/action@latest
        with:
          projectToken: ${{ secrets.CHROMATIC_PROJECT_TOKEN }}
          token: ${{ secrets.GITHUB_TOKEN }}
```

## Accessibility Testing

The a11y addon audits rendered components using Deque's axe-core library, automatically catching up to 57% of WCAG issues. It includes a toolbar for simulating vision impairments and a panel for viewing violations.

## A11y Addon Setup

### Installation

```bash
npx storybook add @storybook/addon-a11y
```

### Vitest Integration

For CLI/CI a11y testing alongside component tests:

```bash
npx storybook add @storybook/addon-vitest
```

## A11y Configuration

### Global Configuration

```typescript
// .storybook/preview.ts
const preview: Preview = {
  parameters: {
    a11y: {
      context: 'body',         // CSS selector for audit scope
      config: {},               // Passed to axe.configure()
      options: {},              // Passed to axe.run()
    },
  },
  initialGlobals: {
    a11y: {
      manual: true,             // Disable automatic checks
    },
  },
};
```

### Component-Level Configuration

```typescript
const meta = {
  component: DataTable,
  parameters: {
    a11y: {
      test: 'error',           // 'off' | 'todo' | 'error'
      config: {
        rules: [
          { id: 'color-contrast', enabled: true },
        ],
      },
    },
  },
} satisfies Meta<typeof DataTable>;
```

### Story-Level Configuration

```typescript
export const HighContrast: Story = {
  parameters: {
    a11y: {
      test: 'error',
      context: {
        include: ['body'],
        exclude: ['.decorative-only'],
      },
    },
  },
};
```

### Configuration Properties

| Property | Default | Purpose |
|----------|---------|---------|
| `parameters.a11y.context` | `'body'` | DOM elements to audit |
| `parameters.a11y.config` | Default rules | axe.configure() options |
| `parameters.a11y.options` | `{}` | axe.run() options |
| `parameters.a11y.test` | `undefined` | Test behavior with Vitest |
| `globals.a11y.manual` | `undefined` | Disable automatic analysis |

## WCAG Standards

The addon evaluates against multiple WCAG standards by default:

- WCAG 2.0 Level A & AA
- WCAG 2.1 Level A & AA
- Best Practices

### Upgrading to AAA

```typescript
const preview: Preview = {
  parameters: {
    a11y: {
      options: {
        runOnly: [
          'wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa',
          'best-practice', 'wcag2aaa',
        ],
      },
    },
  },
};
```

## Rule Management

### Disable Specific Rules

```typescript
parameters: {
  a11y: {
    config: {
      rules: [
        { id: 'region', enabled: false },
        { id: 'image-alt', enabled: false },
      ],
    },
  },
}
```

### Custom Rule Selectors

```typescript
parameters: {
  a11y: {
    config: {
      rules: [
        {
          id: 'autocomplete-valid',
          selector: '*:not([autocomplete="nope"])',
        },
      ],
    },
  },
}
```

### Exclude Elements from Checks

```typescript
parameters: {
  a11y: {
    context: {
      include: ['body'],
      exclude: ['.no-a11y-check', '#third-party-widget'],
    },
  },
}
```

## Test Behavior Levels

The `parameters.a11y.test` parameter controls how violations are reported:

| Value | In Storybook UI | In CLI/CI |
|-------|-----------------|-----------|
| `'off'` | Panel only, no test results | No output |
| `'todo'` | Warnings in sidebar | Warnings (no failures) |
| `'error'` | Errors in sidebar | Test failures |

### Mixed Behaviors

```typescript
const meta = {
  component: Button,
  parameters: {
    a11y: { test: 'error' },
  },
} satisfies Meta<typeof Button>;

export const Primary: Story = {};  // Inherits 'error'

export const Legacy: Story = {
  parameters: {
    a11y: { test: 'todo' },  // Override to warnings only
  },
};

export const Decorative: Story = {
  parameters: {
    a11y: { test: 'off' },   // No testing
  },
};
```

## Progressive A11y Workflow

### Step 1: Enable Strict Globally

```typescript
const preview: Preview = {
  parameters: {
    a11y: { test: 'error' },
  },
};
```

### Step 2: Mark Components Needing Work

```typescript
const meta = {
  component: LegacyTable,
  parameters: {
    a11y: { test: 'todo' },
  },
} satisfies Meta<typeof LegacyTable>;
```

### Step 3: Fix and Promote

Remove the `todo` override once violations are fixed — the component inherits the global `error` level.

## Snapshot Testing

Snapshot tests compare rendered HTML markup against baselines:

```bash
# Run with Vitest
npx vitest --project=storybook
```

Snapshots are useful for detecting unexpected markup changes but produce more false positives than visual tests. Use them as a complement, not a replacement.

### When to Use Snapshots vs Visual Tests

| Use Case | Snapshot | Visual |
|----------|----------|--------|
| Detect layout breaks | No | Yes |
| Detect markup changes | Yes | No |
| Cross-browser testing | No | Yes |
| Free | Yes | No (Chromatic) |
| Maintenance overhead | Higher | Lower |

## Running A11y Tests

### In Storybook UI

1. Expand the testing widget
2. Check "Accessibility"
3. Click "Run component tests"

Violations appear with indicators in the sidebar. Click to see details including rule ID, affected element, and remediation suggestion.

### Via CLI

```bash
npx vitest --project=storybook
```

A11y tests produce errors in CI only when `parameters.a11y.test` is set to `'error'`.

## Common Pitfalls

1. **Region rule false positives** — Storybook disables the `region` rule by default
2. **Async component issues** — Enable `developmentModeForBuild` for Suspense/RSC
3. **`todo` not failing in CI** — Only `'error'` produces actual test failures
4. **Chromatic token in CI** — Store as a secret, never commit to code

## Related Topics

- [Interaction Testing](06-interaction-testing.md) — Behavior testing with play functions
- [Sharing & Publishing](11-sharing-publishing.md) — CI/CD deployment
- [Configuration](10-configuration.md) — Main and preview configuration
