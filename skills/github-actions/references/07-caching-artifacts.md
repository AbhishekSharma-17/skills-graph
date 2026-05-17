# Caching and Artifacts

> Source: [docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows](https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows)

## Table of Contents

- [Dependency Caching with actions/cache](#dependency-caching-with-actionscache)
- [Cache Key Strategies](#cache-key-strategies)
- [Language-Specific Caching](#language-specific-caching)
- [Built-in Caching in Setup Actions](#built-in-caching-in-setup-actions)
- [Cache Scope and Restore Behavior](#cache-scope-and-restore-behavior)
- [Cache Eviction and Limits](#cache-eviction-and-limits)
- [Cache Best Practices](#cache-best-practices)
- [Uploading Artifacts](#uploading-artifacts)
- [Downloading Artifacts](#downloading-artifacts)
- [Cross-Job Data Sharing](#cross-job-data-sharing)
- [Cross-Workflow Artifacts](#cross-workflow-artifacts)
- [Artifact vs Cache — When to Use Each](#artifact-vs-cache--when-to-use-each)
- [Artifact Retention](#artifact-retention)
- [Build Artifact Patterns](#build-artifact-patterns)

---

## Dependency Caching with actions/cache

The `actions/cache@v4` action stores and restores directories between workflow runs based on a cache key:

```yaml
steps:
  - uses: actions/checkout@v4

  - name: Cache node modules
    uses: actions/cache@v4
    with:
      path: node_modules
      key: ${{ runner.os }}-node-modules-${{ hashFiles('**/package-lock.json') }}
      restore-keys: |
        ${{ runner.os }}-node-modules-

  - run: npm ci
  - run: npm test
```

| Input | Purpose |
|:------|:--------|
| `path` | Directory or file path to cache (supports multiple paths with newlines) |
| `key` | Exact key for saving and restoring the cache |
| `restore-keys` | Ordered list of fallback key prefixes for partial matches |

When a cache hit occurs on the exact `key`, the restore step loads the cached directory and `npm ci` completes almost instantly (it detects `node_modules` is already correct). On a miss, the `restore-keys` prefixes are tried in order for the closest partial match, and the cache is saved under the full `key` at the end of the job.

---

## Cache Key Strategies

Build cache keys from components that reflect when the cache should invalidate:

```yaml
# Pattern: os-tool-hashOfLockfile
key: ${{ runner.os }}-npm-${{ hashFiles('**/package-lock.json') }}

# Include Node version if it matters
key: ${{ runner.os }}-node-${{ matrix.node-version }}-${{ hashFiles('**/package-lock.json') }}

# Include branch for isolation
key: ${{ runner.os }}-npm-${{ github.ref_name }}-${{ hashFiles('**/package-lock.json') }}
```

`hashFiles()` returns a SHA-256 hash of the matched files. When the lock file changes, the hash changes, and a fresh cache is created. The glob pattern `**/package-lock.json` finds the file regardless of nesting depth.

Restore keys provide graceful fallback when the exact key misses:

```yaml
restore-keys: |
  ${{ runner.os }}-npm-${{ github.ref_name }}-
  ${{ runner.os }}-npm-
```

GitHub matches prefixes from top to bottom, returning the most recently created cache that starts with the prefix. This means a branch can fall back to its own previous cache, then to any OS-matching cache.

---

## Language-Specific Caching

### npm

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.npm
    key: ${{ runner.os }}-npm-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-npm-
```

Cache `~/.npm` (the npm download cache), not `node_modules`. The download cache avoids re-downloading packages while `npm ci` still verifies the integrity of the installed tree.

### pnpm

```yaml
- name: Get pnpm store directory
  id: pnpm-cache
  run: echo "dir=$(pnpm store path)" >> "$GITHUB_OUTPUT"

- uses: actions/cache@v4
  with:
    path: ${{ steps.pnpm-cache.outputs.dir }}
    key: ${{ runner.os }}-pnpm-${{ hashFiles('**/pnpm-lock.yaml') }}
    restore-keys: |
      ${{ runner.os }}-pnpm-
```

### yarn (v3+ with PnP)

```yaml
- uses: actions/cache@v4
  with:
    path: .yarn/cache
    key: ${{ runner.os }}-yarn-${{ hashFiles('**/yarn.lock') }}
    restore-keys: |
      ${{ runner.os }}-yarn-
```

### Bun

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.bun/install/cache
    key: ${{ runner.os }}-bun-${{ hashFiles('**/bun.lockb') }}
    restore-keys: |
      ${{ runner.os }}-bun-
```

### pip (Python)

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```

For Poetry projects, cache the virtualenv:

```yaml
- uses: actions/cache@v4
  with:
    path: |
      ~/.cache/pip
      ~/.cache/pypoetry
    key: ${{ runner.os }}-poetry-${{ hashFiles('**/poetry.lock') }}
    restore-keys: |
      ${{ runner.os }}-poetry-
```

### Go, Gradle, Maven

| Ecosystem | Cache Path | Hash File |
|:----------|:-----------|:----------|
| Go | `~/go/pkg/mod`, `~/.cache/go-build` | `**/go.sum` |
| Gradle | `~/.gradle/caches`, `~/.gradle/wrapper` | `**/*.gradle*`, `**/gradle-wrapper.properties` |
| Maven | `~/.m2/repository` | `**/pom.xml` |

Use the same `key` / `restore-keys` pattern shown above, substituting the appropriate path and lock file hash.

---

## Built-in Caching in Setup Actions

Most `actions/setup-*` actions have built-in caching that eliminates the need for a separate `actions/cache` step:

```yaml
# Node.js — caches npm/pnpm/yarn download cache automatically
- uses: actions/setup-node@v4
  with:
    node-version: 22
    cache: npm              # Also accepts: pnpm, yarn

# Python — caches pip/pipenv/poetry
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
    cache: pip              # Also accepts: pipenv, poetry
    cache-dependency-path: requirements.txt

# Go — caches modules by default
- uses: actions/setup-go@v5
  with:
    go-version: "1.22"
    cache: true             # Default is true

# Java — caches Gradle/Maven/sbt
- uses: actions/setup-java@v4
  with:
    distribution: temurin
    java-version: "21"
    cache: gradle           # Also accepts: maven, sbt
```

Built-in caching uses `hashFiles` on the appropriate lock file automatically. For most projects, this is sufficient and simpler than manual cache configuration. Use `actions/cache` directly when you need custom cache paths, keys, or restore-key strategies.

---

## Cache Scope and Restore Behavior

Caches are scoped to a branch. The restore order is:

1. Exact key match on the **current branch**
2. Restore-key prefix matches on the **current branch** (most recently created first)
3. Exact key match on the **default branch** (typically `main`)
4. Restore-key prefix matches on the **default branch**

```
feature/auth branch creates cache: Linux-npm-abc123
  ↓ exact match first
feature/auth can restore: Linux-npm-abc123
  ↓ then prefix match
feature/auth can restore: Linux-npm-  (partial match from feature/auth)
  ↓ then default branch exact
feature/auth can restore: Linux-npm-abc123  (from main)
  ↓ then default branch prefix
feature/auth can restore: Linux-npm-  (partial match from main)
```

A pull request branch can read caches from the base branch but cannot write to it. This prevents a PR from poisoning the cache of the target branch.

---

## Cache Eviction and Limits

| Property | Value |
|:---------|:------|
| Maximum cache size per repository | 10 GB |
| Maximum single cache entry | 10 GB |
| Eviction policy when over limit | Least recently used (FIFO) |
| Unused cache eviction | 7 days since last access |

When the repository exceeds 10 GB of total cache storage, GitHub deletes the oldest caches until the total drops below the limit. Actively accessed caches reset their 7-day expiry timer on each restore.

Monitor cache usage with the GitHub CLI:

```bash
# List all caches for the repository
gh cache list --repo owner/repo

# Delete a specific cache by key
gh cache delete "Linux-npm-abc123" --repo owner/repo

# Delete all caches
gh cache list --repo owner/repo --json key -q '.[].key' | xargs -I{} gh cache delete {} --repo owner/repo
```

---

## Cache Best Practices

1. **Use `hashFiles` on lock files** for deterministic keys. Lock files change only when dependencies change, producing a new cache exactly when needed.

2. **Include `runner.os` in keys** to avoid cross-platform cache collisions. Native binaries compiled on Linux will not work on macOS.

3. **Use `restore-keys` for partial matches**. A partial restore followed by `npm ci` is faster than installing from scratch.

4. **Cache download caches, not `node_modules`**. Caching `~/.npm` is safer than `node_modules` because `npm ci` validates the tree. Caching `node_modules` can lead to subtle dependency drift.

5. **Prefer built-in setup action caching** for standard projects. Only use `actions/cache` directly when you need fine-grained control.

6. **Keep cache keys stable**. Avoid including volatile values like timestamps or run numbers in cache keys unless you intentionally want per-run caches.

---

## Uploading Artifacts

Use `actions/upload-artifact@v4` to persist files from a job for later download or use in other jobs:

```yaml
steps:
  - run: npm run build

  - uses: actions/upload-artifact@v4
    with:
      name: webapp-dist
      path: dist/
      retention-days: 7
      if-no-files-found: error     # warn (default), error, ignore
      compression-level: 6         # 0 (none) to 9 (max), default 6
      overwrite: false             # Set true to replace existing artifact with same name
```

Upload multiple paths with glob patterns:

```yaml
  - uses: actions/upload-artifact@v4
    with:
      name: test-results
      path: |
        coverage/
        test-results/*.xml
        !test-results/tmp/
```

The `!` prefix excludes paths from the upload.

---

## Downloading Artifacts

Use `actions/download-artifact@v4` to retrieve artifacts uploaded in the same workflow run:

```yaml
steps:
  - uses: actions/download-artifact@v4
    with:
      name: webapp-dist
      path: ./dist

  - run: ls -la ./dist
```

Download all artifacts from the current run:

```yaml
  - uses: actions/download-artifact@v4
    with:
      path: ./all-artifacts
      merge-multiple: true    # Merge all artifacts into a single directory
```

Without `merge-multiple`, each artifact is placed in a subdirectory named after the artifact. With `merge-multiple: true`, all files are extracted into the same directory (files with the same name from different artifacts will overwrite each other).

---

## Cross-Job Data Sharing

Upload in one job and download in a dependent job to share build outputs:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build
      - uses: actions/upload-artifact@v4
        with:
          name: production-build
          path: dist/
          retention-days: 1

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: production-build
          path: ./dist
      - run: echo "Deploying from ./dist"
```

This ensures the exact same build artifact is deployed without rebuilding.

---

## Cross-Workflow Artifacts

Artifacts are scoped to the workflow run that created them. To access artifacts from a different workflow run, use the `workflow_run` event and the GitHub REST API:

```yaml
on:
  workflow_run:
    workflows: ["Deploy"]
    types: [completed]

jobs:
  verify:
    if: github.event.workflow_run.conclusion == 'success'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/github-script@v7
        with:
          script: |
            const { data } = await github.rest.actions.listWorkflowRunArtifacts({
              ...context.repo,
              run_id: context.payload.workflow_run.id,
            });
            const artifact = data.artifacts.find((a) => a.name === 'deploy-manifest');
            if (artifact) {
              const download = await github.rest.actions.downloadArtifact({
                ...context.repo,
                artifact_id: artifact.id,
                archive_format: 'zip',
              });
              require('fs').writeFileSync('manifest.zip', Buffer.from(download.data));
            }
```

---

## Artifact vs Cache — When to Use Each

| Aspect | Cache | Artifact |
|:-------|:------|:---------|
| **Purpose** | Speed up dependency installation | Persist build outputs and reports |
| **Scope** | Branch-scoped, cross-run | Single workflow run |
| **Access** | Same job only (no cross-job) | Cross-job and downloadable from UI |
| **Typical content** | `node_modules`, `~/.npm`, `~/.cache/pip` | `dist/`, test reports, binaries |
| **Key-based** | Yes (exact + prefix matching) | No (name-based) |
| **Eviction** | 7 days unused, 10 GB repo limit | Retention-days based |
| **Download from UI** | No | Yes |

Use **cache** when you want to skip re-downloading dependencies on every run. Use **artifacts** when you need to pass files between jobs, store build outputs, or download results from the GitHub UI.

---

## Artifact Retention

| Setting | Default | Range |
|:--------|:--------|:------|
| Per-upload `retention-days` | Uses repo/org default | 1–90 days |
| Repository default | 90 days | Configurable in repo settings |
| Organization default | 90 days | Configurable in org settings |

The per-upload `retention-days` cannot exceed the repository or organization maximum. If no value is specified, the repository default applies.

---

## Build Artifact Patterns

### Test Results and Coverage Reports

```yaml
steps:
  - run: npm test -- --coverage --reporters=default --reporters=jest-junit
    env:
      JEST_JUNIT_OUTPUT_DIR: ./test-results

  - uses: actions/upload-artifact@v4
    if: always()      # Upload even when tests fail
    with:
      name: test-results
      path: |
        test-results/
        coverage/lcov-report/

  - name: Add coverage to job summary
    if: always()
    run: |
      echo "## Coverage Report" >> "$GITHUB_STEP_SUMMARY"
      echo '```' >> "$GITHUB_STEP_SUMMARY"
      npx coverage-summary || true >> "$GITHUB_STEP_SUMMARY"
      echo '```' >> "$GITHUB_STEP_SUMMARY"
```

### Docker Image Layer Caching

```yaml
steps:
  - uses: actions/checkout@v4

  - uses: docker/setup-buildx-action@v3

  - uses: actions/cache@v4
    with:
      path: /tmp/.buildx-cache
      key: ${{ runner.os }}-buildx-${{ hashFiles('Dockerfile', 'package-lock.json') }}
      restore-keys: |
        ${{ runner.os }}-buildx-

  - uses: docker/build-push-action@v6
    with:
      context: .
      push: false
      tags: myapp:latest
      cache-from: type=local,src=/tmp/.buildx-cache
      cache-to: type=local,dest=/tmp/.buildx-cache-new,mode=max

  - name: Rotate cache
    run: |
      rm -rf /tmp/.buildx-cache
      mv /tmp/.buildx-cache-new /tmp/.buildx-cache
```

The cache rotation step prevents the cache from growing unboundedly. The `mode=max` option caches all layers, not just the final image layers.
