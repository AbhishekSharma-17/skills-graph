# Playwright — Visual Testing

> Source: [playwright.dev/docs/test-snapshots](https://playwright.dev/docs/test-snapshots) | Version: 1.59

## Table of Contents

- [Overview](#overview)
- [Basic Screenshot Comparison](#basic-screenshot-comparison)
- [Configuration Options](#configuration-options)
- [Handling Dynamic Content](#handling-dynamic-content)
- [Element Screenshots](#element-screenshots)
- [Update Baselines](#update-baselines)
- [CI Strategies](#ci-strategies)
- [Common Pitfalls](#common-pitfalls)

## Overview

Playwright's visual testing compares screenshots pixel-by-pixel against stored baselines. On first run, it creates reference images. On subsequent runs, it compares and fails if differences exceed thresholds.

Visual tests catch:
- Unintended layout shifts
- CSS regressions
- Font rendering changes
- Responsive breakage
- Missing or misaligned elements

## Basic Screenshot Comparison

### Full Page

```typescript
import { test, expect } from '@playwright/test';

test('homepage visual', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveScreenshot('homepage.png');
});
```

On first run, this creates `tests/homepage-visual-1-chromium-darwin.png` as the baseline.

### Auto-Generated Names

```typescript
// Playwright generates a name from the test title
await expect(page).toHaveScreenshot();
// Creates: test-title-1-chromium-darwin.png
```

### Snapshot Directory

By default, snapshots are stored next to the test file in a directory named `<test-file-name>-snapshots/`.

```typescript
// Override in config
export default defineConfig({
  snapshotDir: './snapshots',
  snapshotPathTemplate: '{snapshotDir}/{testFileDir}/{testFileName}-snapshots/{arg}{-projectName}{ext}',
});
```

## Configuration Options

### Comparison Thresholds

```typescript
await expect(page).toHaveScreenshot('dashboard.png', {
  // Maximum number of different pixels (absolute)
  maxDiffPixels: 100,

  // Maximum ratio of different pixels (0-1)
  maxDiffPixelRatio: 0.01,

  // Per-pixel color difference threshold (0-1, default 0.2)
  threshold: 0.3,
});
```

### Global Configuration

```typescript
// playwright.config.ts
export default defineConfig({
  expect: {
    toHaveScreenshot: {
      maxDiffPixels: 50,
      threshold: 0.2,
      animations: 'disabled',
    },
    toMatchSnapshot: {
      maxDiffPixelRatio: 0.01,
    },
  },
});
```

### Screenshot Options

```typescript
await expect(page).toHaveScreenshot('full.png', {
  fullPage: true,                // Capture entire scrollable area
  animations: 'disabled',       // Freeze CSS animations
  caret: 'hide',               // Hide text cursor
  scale: 'css',                // Consistent pixel density
  mask: [page.getByTestId('timestamp')], // Mask dynamic elements
  maskColor: '#FF00FF',        // Color for masked areas
  stylePath: 'test-styles.css', // Custom CSS during screenshot
});
```

## Handling Dynamic Content

Dynamic content (timestamps, avatars, ads) causes snapshot flakiness. Strategies:

### Masking Elements

```typescript
await expect(page).toHaveScreenshot('dashboard.png', {
  mask: [
    page.getByTestId('timestamp'),
    page.getByTestId('avatar'),
    page.locator('.ad-banner'),
  ],
});
```

### Custom Stylesheet

```typescript
// test-visual.css
.timestamp, .ad-banner, .random-avatar {
  visibility: hidden !important;
}
.animated-element {
  animation: none !important;
  transition: none !important;
}
```

```typescript
await expect(page).toHaveScreenshot('page.png', {
  stylePath: 'test-visual.css',
});
```

### Disabling Animations

```typescript
await expect(page).toHaveScreenshot('animated.png', {
  animations: 'disabled',
});
```

### Waiting for Stability

```typescript
// Wait for fonts to load
await page.evaluate(() => document.fonts.ready);

// Wait for images
await page.waitForLoadState('networkidle');

// Wait for specific element to be stable
await page.getByTestId('chart').waitFor({ state: 'visible' });

await expect(page).toHaveScreenshot('chart.png');
```

## Element Screenshots

Compare specific elements instead of the full page:

```typescript
// Single element
const card = page.getByTestId('product-card');
await expect(card).toHaveScreenshot('product-card.png');

// Header component
await expect(page.getByRole('banner')).toHaveScreenshot('header.png');

// Navigation
await expect(page.getByRole('navigation')).toHaveScreenshot('nav.png');
```

## Update Baselines

### Command Line

```bash
# Update all snapshots
npx playwright test --update-snapshots

# Update specific test file
npx playwright test tests/visual.spec.ts --update-snapshots

# Update specific project
npx playwright test --project=chromium --update-snapshots
```

### Workflow

1. Run tests — new tests create baselines automatically
2. Review baseline images in your PR
3. If visual changes are intentional, run `--update-snapshots`
4. Commit updated baselines

## CI Strategies

### Platform-Specific Baselines

Fonts and rendering differ across OS. Options:

**Option A: Run in Docker (Recommended)**

```yaml
# GitHub Actions
jobs:
  test:
    runs-on: ubuntu-latest
    container:
      image: mcr.microsoft.com/playwright:v1.59.0-noble
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npx playwright test
```

**Option B: Separate baselines per OS**

```typescript
// playwright.config.ts
export default defineConfig({
  snapshotPathTemplate: '{snapshotDir}/{testFileDir}/{testFileName}-snapshots/{arg}-{projectName}-{platform}{ext}',
});
```

### Uploading Diff Artifacts

```yaml
- uses: actions/upload-artifact@v4
  if: failure()
  with:
    name: playwright-visual-diffs
    path: test-results/
    retention-days: 7
```

### Diff Report

When a visual test fails, Playwright generates three images in `test-results/`:
- `*-expected.png` — the baseline
- `*-actual.png` — what was captured
- `*-diff.png` — highlighted differences

## Common Pitfalls

1. **Cross-platform baseline mismatch** — fonts render differently on macOS vs Linux; use Docker in CI for consistency
2. **Flaky due to animations** — always set `animations: 'disabled'` for visual tests
3. **Not waiting for content** — ensure fonts, images, and async content are loaded before capturing
4. **Too strict thresholds** — anti-aliasing and sub-pixel rendering cause minor differences; allow some tolerance
5. **Committing test-results** — add `test-results/` to `.gitignore`; only commit baseline snapshots
6. **Snapshot bloat** — each browser/OS combination creates separate baselines; standardize on Docker to reduce count

## Related

- Assertions — `references/03-assertions.md`
- Configuration — `references/11-configuration-cli.md`
- CI/CD — `references/12-ci-cd.md`
