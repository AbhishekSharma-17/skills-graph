# Matrix Strategy

> Source: [docs.github.com/en/actions/using-jobs/using-a-matrix-for-your-jobs](https://docs.github.com/en/actions/using-jobs/using-a-matrix-for-your-jobs)

## Table of Contents

- [Basic Matrix](#basic-matrix)
- [Multi-Dimensional Matrix](#multi-dimensional-matrix)
- [Include — Adding Combinations](#include--adding-combinations)
- [Exclude — Removing Combinations](#exclude--removing-combinations)
- [Fail-Fast and Max-Parallel](#fail-fast-and-max-parallel)
- [Dynamic Matrix with fromJSON](#dynamic-matrix-with-fromjson)
- [Concurrency Limits](#concurrency-limits)
- [Common Patterns](#common-patterns)
- [Matrix with Reusable Workflows](#matrix-with-reusable-workflows)
- [Real-World Examples](#real-world-examples)

---

## Basic Matrix

A matrix generates multiple job runs by iterating over a set of values. Each combination runs as a separate job:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [18, 20, 22]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm ci
      - run: npm test
```

This produces three parallel jobs: one each for Node 18, 20, and 22. Each job appears in the Actions UI with its matrix values appended to the job name: `test (18)`, `test (20)`, `test (22)`.

Access the current matrix value with `${{ matrix.<key> }}`.

---

## Multi-Dimensional Matrix

Combine multiple dimensions to create a Cartesian product of all combinations:

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        node-version: [20, 22]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: npm
      - run: npm ci
      - run: npm test
```

This creates 6 jobs (3 OS variants times 2 Node versions):

| Job | OS | Node |
|:----|:---|:-----|
| test (ubuntu-latest, 20) | ubuntu-latest | 20 |
| test (ubuntu-latest, 22) | ubuntu-latest | 22 |
| test (windows-latest, 20) | windows-latest | 20 |
| test (windows-latest, 22) | windows-latest | 22 |
| test (macos-latest, 20) | macos-latest | 20 |
| test (macos-latest, 22) | macos-latest | 22 |

---

## Include — Adding Combinations

### Adding Extra Properties to Existing Combinations

Use `include` to attach additional values to combinations that already exist in the matrix:

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
        node-version: [20, 22]
        include:
          - os: ubuntu-latest
            node-version: 22
            coverage: true
          - os: windows-latest
            node-version: 20
            extra-flags: --experimental
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm test ${{ matrix.extra-flags }}
      - if: matrix.coverage
        run: npm run coverage
```

When an `include` entry matches an existing combination (same `os` and `node-version` values), the additional properties (`coverage`, `extra-flags`) are merged into that combination. Properties not set default to an empty string.

### Adding Entirely New Combinations

An `include` entry that does not match any existing combination is added as a new job:

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest]
        node-version: [20, 22]
        include:
          - os: macos-latest
            node-version: 22
            experimental: true
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm test
```

This produces three jobs: `(ubuntu-latest, 20)`, `(ubuntu-latest, 22)`, and the added `(macos-latest, 22)`.

### Include-Only Matrix

Use `include` without any matrix dimensions to define an explicit list of configurations:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        include:
          - environment: staging
            url: https://staging.example.com
            auto-approve: true
          - environment: production
            url: https://example.com
            auto-approve: false
    steps:
      - uses: actions/checkout@v4
      - run: |
          echo "Deploying to ${{ matrix.environment }}"
          echo "URL: ${{ matrix.url }}"
```

---

## Exclude — Removing Combinations

Remove specific combinations from the Cartesian product:

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ["3.10", "3.11", "3.12"]
        exclude:
          - os: windows-latest
            python-version: "3.10"
          - os: macos-latest
            python-version: "3.10"
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: python -m pytest
```

The full matrix would produce 9 jobs. After exclusions, 7 jobs remain (Windows/3.10 and macOS/3.10 are removed).

An `exclude` entry removes any combination where all specified properties match. You can exclude on a subset of dimensions.

---

## Fail-Fast and Max-Parallel

### fail-fast

When `fail-fast` is `true` (the default), GitHub cancels all in-progress matrix jobs as soon as any one job fails:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false    # Run ALL combinations even if some fail
      matrix:
        node-version: [18, 20, 22]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm test
```

Set `fail-fast: false` when you want to see results across all versions even if one fails. This is useful for compatibility testing where you want the full picture.

### max-parallel

Limit the number of matrix jobs running concurrently:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      max-parallel: 3    # Run at most 3 jobs at a time
      matrix:
        suite: [unit, integration, e2e, smoke, performance, a11y]
    steps:
      - uses: actions/checkout@v4
      - run: npm run test:${{ matrix.suite }}
```

By default, GitHub runs as many matrix jobs in parallel as runner availability allows. Use `max-parallel` to limit concurrent load on shared resources like databases, APIs, or self-hosted runner pools.

---

## Dynamic Matrix with fromJSON

Generate matrix values dynamically from a previous job's output. This is useful when the set of values is not known until runtime:

```yaml
jobs:
  discover:
    runs-on: ubuntu-latest
    outputs:
      packages: ${{ steps.find.outputs.packages }}
    steps:
      - uses: actions/checkout@v4
      - name: Find changed packages
        id: find
        run: |
          PACKAGES=$(ls packages/*/package.json | xargs -I{} dirname {} | xargs -I{} basename {} | jq -R -s -c 'split("\n") | map(select(. != ""))')
          echo "packages=$PACKAGES" >> "$GITHUB_OUTPUT"

  test:
    needs: discover
    if: needs.discover.outputs.packages != '[]'
    runs-on: ubuntu-latest
    strategy:
      matrix:
        package: ${{ fromJSON(needs.discover.outputs.packages) }}
    steps:
      - uses: actions/checkout@v4
      - run: |
          cd packages/${{ matrix.package }}
          npm ci
          npm test
```

The `fromJSON()` function converts a JSON string into an array or object that the matrix can iterate over. The discovery job runs first, computes the list, and the test job expands it into parallel runs.

The output JSON can include `include` and `exclude` keys alongside dimension arrays, giving full matrix control from dynamic data.

---

## Concurrency Limits

Matrix jobs are subject to GitHub Actions concurrency limits:

| Plan | Max Jobs per Matrix | Max Concurrent Jobs (account-wide) |
|:-----|:--------------------|:-----------------------------------|
| Free | 256 | 20 |
| Team | 256 | 40 |
| Enterprise | 256 | 500 |

A single workflow matrix can generate at most 256 jobs. If you exceed this limit, the workflow fails to start.

Self-hosted runners have no platform-imposed concurrency limit but are constrained by the number of registered runners. Use `max-parallel` or runner labels to manage capacity:

```yaml
jobs:
  test:
    runs-on: [self-hosted, linux, x64]
    strategy:
      max-parallel: 5    # Don't overwhelm the self-hosted runner pool
      matrix:
        shard: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    steps:
      - uses: actions/checkout@v4
      - run: npm run test -- --shard=${{ matrix.shard }}/10
```

---

## Common Patterns

### Cross-Platform Testing

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    steps:
      - uses: actions/checkout@v4
      - run: cargo test
```

### Multi-Version Language Testing

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[test]"
      - run: pytest
```

### Database Version Testing with Services

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        postgres-version: [14, 15, 16]
    services:
      postgres:
        image: postgres:${{ matrix.postgres-version }}
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: testdb
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - run: npm test
        env:
          DATABASE_URL: postgresql://postgres:testpass@localhost:5432/testdb
```

---

## Matrix with Reusable Workflows

Call a reusable workflow for each matrix combination:

```yaml
# .github/workflows/ci.yml
jobs:
  test:
    strategy:
      matrix:
        environment: [staging, production]
    uses: ./.github/workflows/deploy.yml
    with:
      environment: ${{ matrix.environment }}
    secrets: inherit
```

```yaml
# .github/workflows/deploy.yml
on:
  workflow_call:
    inputs:
      environment:
        required: true
        type: string

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}
    steps:
      - uses: actions/checkout@v4
      - run: echo "Deploying to ${{ inputs.environment }}"
```

Matrix values are passed through the `with` keyword to the reusable workflow's inputs.

---

## Real-World Example — Build Matrix with Deploy

```yaml
name: Release

on:
  push:
    tags: ["v*"]

jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        include:
          - os: ubuntu-latest
            target: x86_64-unknown-linux-gnu
            artifact: myapp-linux-amd64
          - os: macos-latest
            target: aarch64-apple-darwin
            artifact: myapp-macos-arm64
          - os: windows-latest
            target: x86_64-pc-windows-msvc
            artifact: myapp-windows-amd64
    steps:
      - uses: actions/checkout@v4
      - run: cargo build --release --target ${{ matrix.target }}
      - uses: actions/upload-artifact@v4
        with:
          name: ${{ matrix.artifact }}
          path: target/${{ matrix.target }}/release/myapp*

  release:
    needs: build
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/download-artifact@v4
        with:
          merge-multiple: true
          path: ./artifacts
      - uses: softprops/action-gh-release@v2
        with:
          files: artifacts/**
```
