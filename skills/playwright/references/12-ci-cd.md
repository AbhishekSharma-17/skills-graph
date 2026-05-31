# Playwright — CI/CD Integration

> Source: [playwright.dev/docs/ci](https://playwright.dev/docs/ci) | Version: 1.59

## Table of Contents

- [GitHub Actions](#github-actions)
- [Docker](#docker)
- [Sharding in CI](#sharding-in-ci)
- [Artifact Management](#artifact-management)
- [Other CI Platforms](#other-ci-platforms)
- [Performance Optimization](#performance-optimization)
- [Common Pitfalls](#common-pitfalls)

## GitHub Actions

### Basic Workflow

```yaml
# .github/workflows/playwright.yml
name: Playwright Tests
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    timeout-minutes: 30
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright browsers
        run: npx playwright install --with-deps

      - name: Run tests
        run: npx playwright test

      - uses: actions/upload-artifact@v4
        if: ${{ !cancelled() }}
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 30
```

### With Docker Container (Recommended)

```yaml
jobs:
  test:
    timeout-minutes: 30
    runs-on: ubuntu-latest
    container:
      image: mcr.microsoft.com/playwright:v1.59.0-noble
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npx playwright test
        env:
          HOME: /root
      - uses: actions/upload-artifact@v4
        if: ${{ !cancelled() }}
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 30
```

### With Sharding

```yaml
jobs:
  test:
    timeout-minutes: 30
    runs-on: ubuntu-latest
    container:
      image: mcr.microsoft.com/playwright:v1.59.0-noble
    strategy:
      fail-fast: false
      matrix:
        shard: [1/4, 2/4, 3/4, 4/4]
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - name: Run tests
        run: npx playwright test --shard=${{ matrix.shard }}
        env:
          HOME: /root
      - uses: actions/upload-artifact@v4
        if: ${{ !cancelled() }}
        with:
          name: blob-report-${{ strategy.job-index }}
          path: blob-report/
          retention-days: 1

  merge-reports:
    if: ${{ !cancelled() }}
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - name: Download blob reports
        uses: actions/download-artifact@v4
        with:
          path: all-blob-reports
          pattern: blob-report-*
          merge-multiple: true
      - name: Merge reports
        run: npx playwright merge-reports --reporter html ./all-blob-reports
      - uses: actions/upload-artifact@v4
        with:
          name: html-report
          path: playwright-report/
          retention-days: 14
```

## Docker

### Official Images

```bash
# Latest
mcr.microsoft.com/playwright:v1.59.0-noble

# Focal (Ubuntu 20.04)
mcr.microsoft.com/playwright:v1.59.0-focal

# Jammy (Ubuntu 22.04)
mcr.microsoft.com/playwright:v1.59.0-jammy
```

### Custom Dockerfile

```dockerfile
FROM mcr.microsoft.com/playwright:v1.59.0-noble

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .

CMD ["npx", "playwright", "test"]
```

### Docker Compose (with App)

```yaml
# docker-compose.test.yml
services:
  app:
    build: .
    ports:
      - "3000:3000"

  playwright:
    image: mcr.microsoft.com/playwright:v1.59.0-noble
    depends_on:
      - app
    environment:
      BASE_URL: http://app:3000
    volumes:
      - .:/app
    working_dir: /app
    command: npx playwright test
```

## Sharding in CI

### How Sharding Works

```
Total: 100 tests, 4 shards
├── Shard 1/4: tests 1-25
├── Shard 2/4: tests 26-50
├── Shard 3/4: tests 51-75
└── Shard 4/4: tests 76-100
```

### Blob Reporter for Merging

```typescript
// playwright.config.ts
export default defineConfig({
  reporter: process.env.CI
    ? 'blob'   // Binary format optimized for merging
    : 'html',
});
```

### Merge Command

```bash
npx playwright merge-reports --reporter=html ./all-blob-reports
npx playwright merge-reports --reporter=json ./all-blob-reports
```

## Artifact Management

### What to Upload

| Artifact | When | Size Impact |
|----------|------|-------------|
| HTML Report | Always | Small (~1MB) |
| Traces | On failure/retry | Medium (~5-50MB per test) |
| Screenshots | On failure | Small (~100KB each) |
| Videos | On failure | Large (~5-20MB each) |
| JUnit XML | Always | Tiny (~50KB) |

### Configuration for CI

```typescript
// playwright.config.ts
export default defineConfig({
  use: {
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  reporter: [
    ['html', { open: 'never' }],
    ['junit', { outputFile: 'results/junit.xml' }],
  ],
});
```

### Upload Pattern

```yaml
# Upload everything including traces
- uses: actions/upload-artifact@v4
  if: ${{ !cancelled() }}
  with:
    name: test-artifacts
    path: |
      playwright-report/
      test-results/
    retention-days: 14
```

## Other CI Platforms

### GitLab CI

```yaml
# .gitlab-ci.yml
tests:
  image: mcr.microsoft.com/playwright:v1.59.0-noble
  script:
    - npm ci
    - npx playwright test
  artifacts:
    when: always
    paths:
      - playwright-report/
      - test-results/
    expire_in: 1 week
```

### Azure Pipelines

```yaml
# azure-pipelines.yml
trigger:
  - main

pool:
  vmImage: ubuntu-latest

container: mcr.microsoft.com/playwright:v1.59.0-noble

steps:
  - task: NodeTool@0
    inputs:
      versionSpec: '20'
  - script: npm ci
  - script: npx playwright test
  - publish: playwright-report
    artifact: playwright-report
    condition: succeededOrFailed()
```

### Jenkins

```groovy
pipeline {
    agent {
        docker {
            image 'mcr.microsoft.com/playwright:v1.59.0-noble'
        }
    }
    stages {
        stage('Install') {
            steps {
                sh 'npm ci'
            }
        }
        stage('Test') {
            steps {
                sh 'npx playwright test'
            }
        }
    }
    post {
        always {
            archiveArtifacts artifacts: 'playwright-report/**', fingerprint: true
        }
    }
}
```

## Performance Optimization

### Caching

```yaml
# Cache node_modules
- uses: actions/cache@v4
  with:
    path: node_modules
    key: ${{ runner.os }}-node-${{ hashFiles('package-lock.json') }}

# Cache Playwright browsers (if not using Docker)
- uses: actions/cache@v4
  with:
    path: ~/.cache/ms-playwright
    key: ${{ runner.os }}-playwright-${{ hashFiles('package-lock.json') }}
```

### Reduce Browser Count

```typescript
// CI-specific: test only Chromium
projects: process.env.CI
  ? [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }]
  : [
      { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
      { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
      { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    ],
```

### Limit Workers

```typescript
workers: process.env.CI ? 1 : undefined,
```

### Skip Visual Tests in PR

```typescript
test('visual regression @visual', async ({ page }) => {
  test.skip(!!process.env.SKIP_VISUAL, 'Visual tests disabled');
  await expect(page).toHaveScreenshot();
});
```

## Common Pitfalls

1. **Missing `--with-deps`** — without system dependencies, browser launch fails on Linux; use Docker or `install --with-deps`
2. **Not using `if: ${{ !cancelled() }}`** — upload artifacts even if tests fail; `if: failure()` misses cancellations
3. **Overloading CI machines** — too many workers cause OOM and flaky failures; start with `workers: 1`
4. **Not pinning Playwright version in Docker** — `latest` tag changes; pin to `v1.59.0` to match your `package.json`
5. **Forgetting `HOME: /root`** — GitHub Actions containers need this env var for Playwright to find browser binaries
6. **Large artifact retention** — traces and videos add up; set `retention-days` to 7-14 for failure artifacts

## Related

- Configuration — `references/11-configuration-cli.md`
- Tracing — `references/10-tracing-debugging.md`
- Visual Testing — `references/09-visual-testing.md`
