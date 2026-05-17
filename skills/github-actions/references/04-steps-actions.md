# Steps and Actions

> Source: [docs.github.com/en/actions](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#jobsjob_idsteps)

## Table of Contents

- [Step Configuration](#step-configuration)
- [Using Actions (uses)](#using-actions-uses)
- [Running Shell Commands (run)](#running-shell-commands-run)
- [Step Outputs via GITHUB_OUTPUT](#step-outputs-via-github_output)
- [Setting Environment Variables via GITHUB_ENV](#setting-environment-variables-via-github_env)
- [Job Summaries via GITHUB_STEP_SUMMARY](#job-summaries-via-github_step_summary)
- [Adding to PATH via GITHUB_PATH](#adding-to-path-via-github_path)
- [Essential Marketplace Actions](#essential-marketplace-actions)
- [Action Types Overview](#action-types-overview)
- [Creating a Custom Composite Action](#creating-a-custom-composite-action)
- [Creating a Custom JavaScript Action](#creating-a-custom-javascript-action)
- [Shell Selection](#shell-selection)

---

## Step Configuration

Every step in a job supports the following properties:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Descriptive step name
        id: my_step
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
        env:
          NODE_ENV: production
        if: github.event_name == 'push'
        continue-on-error: true
        timeout-minutes: 10
        working-directory: ./frontend
```

| Property | Purpose |
|:---------|:--------|
| `name` | Display name shown in the Actions UI |
| `id` | Unique identifier for referencing outputs and outcomes |
| `uses` | Reference an action to run |
| `run` | Shell commands to execute |
| `with` | Input parameters passed to the action |
| `env` | Environment variables scoped to this step |
| `if` | Conditional expression controlling whether the step runs |
| `continue-on-error` | When `true`, the job continues even if this step fails |
| `timeout-minutes` | Maximum minutes before the step is killed (default: 360) |
| `working-directory` | Directory where `run` commands execute |

A step must have either `uses` or `run`, never both.

---

## Using Actions (uses)

The `uses` keyword references an action to execute. Four reference formats exist:

```yaml
steps:
  # Public action from GitHub Marketplace — owner/repo@ref
  - uses: actions/checkout@v4

  # Action in a subdirectory of a repository — owner/repo/path@ref
  - uses: actions/aws/ec2@main

  # Action from the same repository — ./local-path
  - uses: ./.github/actions/my-custom-action

  # Docker Hub image — docker://image:tag
  - uses: docker://alpine:3.20
```

Pin public actions to a full commit SHA for security in production workflows:

```yaml
steps:
  - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
```

The `@ref` can be a tag (`v4`), branch (`main`), or commit SHA. Tags are convenient but mutable. SHA pinning prevents supply chain attacks where a tag is force-pushed to malicious code.

---

## Running Shell Commands (run)

The `run` keyword executes shell commands directly:

```yaml
steps:
  - name: Single command
    run: echo "Hello from the runner"

  - name: Multi-line commands with pipe literal
    run: |
      echo "Installing dependencies"
      npm ci
      echo "Running tests"
      npm test

  - name: Explicit shell selection
    run: |
      import os
      print(f"Running on {os.name}")
    shell: python

  - name: Working directory override
    run: npm run build
    working-directory: ./packages/frontend
```

Multi-line commands use the YAML `|` literal block scalar. Each line runs sequentially in the same shell session. By default, `run` uses `bash --noprofile --norc -eo pipefail` on Linux/macOS, which means the step fails immediately on any non-zero exit code.

---

## Step Outputs via GITHUB_OUTPUT

Steps communicate data to later steps through the `$GITHUB_OUTPUT` file:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Set version output
        id: version
        run: |
          VERSION=$(node -p "require('./package.json').version")
          echo "pkg_version=$VERSION" >> "$GITHUB_OUTPUT"
          echo "short_sha=$(git rev-parse --short HEAD)" >> "$GITHUB_OUTPUT"

      - name: Use the outputs
        run: |
          echo "Version: ${{ steps.version.outputs.pkg_version }}"
          echo "SHA: ${{ steps.version.outputs.short_sha }}"
```

For multi-line values, use a heredoc delimiter:

```yaml
      - name: Set multi-line output
        id: changelog
        run: |
          DELIM=$(dd if=/dev/urandom bs=15 count=1 status=none | base64)
          echo "content<<$DELIM" >> "$GITHUB_OUTPUT"
          git log --oneline -10 >> "$GITHUB_OUTPUT"
          echo "$DELIM" >> "$GITHUB_OUTPUT"
```

---

## Setting Environment Variables via GITHUB_ENV

Set environment variables that persist for all subsequent steps in the same job:

```yaml
steps:
  - name: Set environment variables
    run: |
      echo "DEPLOY_ENV=staging" >> "$GITHUB_ENV"
      echo "BUILD_NUMBER=${{ github.run_number }}" >> "$GITHUB_ENV"

  - name: Use the variables
    run: |
      echo "Deploying to $DEPLOY_ENV"
      echo "Build #$BUILD_NUMBER"
```

Multi-line values use the same heredoc pattern as `$GITHUB_OUTPUT`.

---

## Job Summaries via GITHUB_STEP_SUMMARY

Write Markdown content to the job summary panel visible on the workflow run page:

```yaml
steps:
  - name: Generate test summary
    run: |
      echo "## Test Results" >> "$GITHUB_STEP_SUMMARY"
      echo "| Suite | Passed | Failed |" >> "$GITHUB_STEP_SUMMARY"
      echo "|:------|-------:|-------:|" >> "$GITHUB_STEP_SUMMARY"
      echo "| Unit  | 142    | 0      |" >> "$GITHUB_STEP_SUMMARY"
      echo "| E2E   | 38     | 2      |" >> "$GITHUB_STEP_SUMMARY"
```

Summaries support GitHub-flavored Markdown including tables, images, collapsible sections, and code blocks. Each step appends to the same summary.

---

## Adding to PATH via GITHUB_PATH

Prepend directories to `$PATH` for all subsequent steps:

```yaml
steps:
  - name: Install custom tool
    run: |
      mkdir -p "$HOME/.local/bin"
      curl -sL https://example.com/tool -o "$HOME/.local/bin/mytool"
      chmod +x "$HOME/.local/bin/mytool"
      echo "$HOME/.local/bin" >> "$GITHUB_PATH"

  - run: mytool --version   # Available because the directory was added to PATH
```

---

## Essential Marketplace Actions

### actions/checkout@v4

Checks out the repository so the workflow can access its contents:

```yaml
- uses: actions/checkout@v4

- uses: actions/checkout@v4
  with:
    fetch-depth: 0          # Full history (needed for git log, tags, changelogs)
    ref: develop             # Check out a specific branch, tag, or SHA
    token: ${{ secrets.PAT }} # Use a PAT to trigger workflows on push
    submodules: recursive    # Clone submodules
    persist-credentials: false # Don't store token in git config
```

### actions/setup-node@v4

```yaml
- uses: actions/setup-node@v4
  with:
    node-version: 22
    node-version-file: .nvmrc    # Read version from .nvmrc or .node-version
    cache: npm                    # Cache npm dependencies automatically
    registry-url: https://npm.pkg.github.com  # For publishing to GitHub Packages
```

### actions/setup-python@v5

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
    cache: pip                # Also supports pipenv, poetry
    cache-dependency-path: requirements.txt
```

### actions/setup-go@v5

```yaml
- uses: actions/setup-go@v5
  with:
    go-version: "1.22"
    cache: true               # Caches Go modules by default
```

### actions/setup-java@v4

```yaml
- uses: actions/setup-java@v4
  with:
    distribution: temurin
    java-version: "21"
    cache: gradle             # Also supports maven, sbt
```

### actions/cache@v4

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.npm
    key: ${{ runner.os }}-npm-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-npm-
```

### actions/upload-artifact@v4 and actions/download-artifact@v4

```yaml
- uses: actions/upload-artifact@v4
  with:
    name: build-output
    path: dist/
    retention-days: 7

- uses: actions/download-artifact@v4
  with:
    name: build-output
    path: ./downloaded-dist
```

### actions/github-script@v7

Run inline JavaScript with access to the Octokit API client and workflow context:

```yaml
- uses: actions/github-script@v7
  with:
    script: |
      const { data: pullRequests } = await github.rest.pulls.list({
        owner: context.repo.owner,
        repo: context.repo.repo,
        state: 'open',
        per_page: 5
      });
      for (const pr of pullRequests) {
        console.log(`#${pr.number}: ${pr.title}`);
      }
```

Return values are available via `steps.<id>.outputs.result` when you `return` from the script. Set `result-encoding: string` or `json` on the action input.

---

## Action Types Overview

| Type | Runtime | Platform | Startup | Use Case |
|:-----|:--------|:---------|:--------|:---------|
| **JavaScript** | `node20` | All (Linux, macOS, Windows) | Fast | Cross-platform, bundled deps |
| **Docker** | Any language | Linux only | Slower (image pull) | Custom runtimes, complex deps |
| **Composite** | YAML steps | All | Fast | Reusing step sequences, no code |

Composite actions are the simplest way to extract reusable workflow logic. They can call other actions, run shell commands, and define inputs and outputs.

---

## Creating a Custom Composite Action

Place the action in `.github/actions/setup-and-test/action.yml`:

```yaml
name: Setup and Test
description: Install dependencies and run the test suite

inputs:
  node-version:
    description: Node.js version to use
    required: false
    default: "22"

outputs:
  test-result:
    description: Whether tests passed or failed
    value: ${{ steps.tests.outputs.result }}

runs:
  using: composite
  steps:
    - uses: actions/setup-node@v4
      with:
        node-version: ${{ inputs.node-version }}
        cache: npm

    - shell: bash
      run: npm ci

    - id: tests
      shell: bash
      run: |
        if npm test; then
          echo "result=pass" >> "$GITHUB_OUTPUT"
        else
          echo "result=fail" >> "$GITHUB_OUTPUT"
          exit 1
        fi
```

Reference it from a workflow:

```yaml
steps:
  - uses: actions/checkout@v4
  - uses: ./.github/actions/setup-and-test
    with:
      node-version: "22"
```

---

## Creating a Custom JavaScript Action

### action.yml

```yaml
name: PR Label Check
description: Verify that a pull request has at least one required label

inputs:
  required-labels:
    description: Comma-separated list of acceptable labels
    required: true
  github-token:
    description: GitHub token for API access
    required: true
    default: ${{ github.token }}

outputs:
  matched-label:
    description: The first matching label found on the PR

runs:
  using: node20
  main: index.js
```

### index.js

```javascript
const core = require("@actions/core");
const github = require("@actions/github");

async function run() {
  try {
    const token = core.getInput("github-token");
    const octokit = github.getOctokit(token);
    const prNumber = github.context.payload.pull_request?.number;

    if (!prNumber) {
      core.setFailed("This action only works on pull_request events.");
      return;
    }

    const requiredLabels = core.getInput("required-labels").split(",").map((l) => l.trim());
    const { data: labels } = await octokit.rest.issues.listLabelsOnIssue({
      ...github.context.repo,
      issue_number: prNumber,
    });

    const matched = requiredLabels.find((rl) => labels.some((l) => l.name === rl));
    if (matched) {
      core.setOutput("matched-label", matched);
    } else {
      core.setFailed(`PR #${prNumber} needs one of: ${requiredLabels.join(", ")}`);
    }
  } catch (error) {
    core.setFailed(error.message);
  }
}

run();
```

Bundle dependencies with `ncc`, then update `action.yml` to `main: dist/index.js`:

```bash
npm install @actions/core @actions/github
npx @vercel/ncc build index.js -o dist
```

---

## Shell Selection

The `shell` keyword controls which interpreter runs `run` commands:

| Shell | Default On | Command Template |
|:------|:-----------|:-----------------|
| `bash` | Linux, macOS | `bash --noprofile --norc -eo pipefail {0}` |
| `pwsh` | Windows | `pwsh -command ". '{0}'"` |
| `python` | All | `python {0}` |
| `sh` | Linux, macOS | `sh -e {0}` |
| `cmd` | Windows | `cmd /D /E:ON /V:OFF /S /C "CALL "{0}""` |
| `powershell` | Windows | `powershell -command ". '{0}'"` |

```yaml
steps:
  - name: Python inline script
    run: |
      import json
      print(json.dumps({"step": "validate"}, indent=2))
    shell: python

  - name: Cross-platform PowerShell
    run: Write-Output "Works on all runner OSes"
    shell: pwsh
```

When `shell` is omitted, GitHub Actions selects `bash` on Linux/macOS and `pwsh` on Windows. Specify `shell: bash` explicitly in cross-platform workflows for consistent behavior.
