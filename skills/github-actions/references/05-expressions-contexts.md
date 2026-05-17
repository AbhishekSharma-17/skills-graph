# Expressions and Contexts

> Source: [docs.github.com/en/actions/reference/workflows-and-actions/contexts](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts)

## Table of Contents

- [Expression Syntax](#expression-syntax)
- [Where Expressions Can Be Used](#where-expressions-can-be-used)
- [Literal Types](#literal-types)
- [Operators](#operators)
- [Type Coercion Rules](#type-coercion-rules)
- [Built-in Functions](#built-in-functions)
- [Status Check Functions](#status-check-functions)
- [Context Objects](#context-objects)
- [Conditional Patterns](#conditional-patterns)
- [String Interpolation in Commands](#string-interpolation-in-commands)
- [Dynamic Job Names](#dynamic-job-names)

---

## Expression Syntax

Expressions use the `${{ }}` syntax and are evaluated at workflow runtime:

```yaml
env:
  BRANCH: ${{ github.ref_name }}

steps:
  - run: echo "Running on branch ${{ github.ref_name }}"
  - if: ${{ github.event_name == 'push' }}
    run: echo "Triggered by a push"
```

In `if` conditionals, the `${{ }}` wrapper is optional. GitHub Actions automatically evaluates `if` values as expressions:

```yaml
# Both forms are equivalent
- if: github.ref == 'refs/heads/main'
- if: ${{ github.ref == 'refs/heads/main' }}
```

Use the explicit `${{ }}` form when the expression starts with `!` to avoid YAML parsing issues:

```yaml
# WRONG — YAML interprets ! as a tag
- if: !startsWith(github.ref, 'refs/tags/')

# CORRECT — wrap in expression syntax
- if: ${{ !startsWith(github.ref, 'refs/tags/') }}
```

---

## Where Expressions Can Be Used

Expressions are valid in these locations:

```yaml
env:
  APP_ENV: ${{ github.event.inputs.environment || 'staging' }}  # Top-level env

jobs:
  deploy:
    if: github.ref == 'refs/heads/main'           # Job conditional
    runs-on: ubuntu-latest
    environment: ${{ github.event.inputs.environment }}  # Job property
    steps:
      - name: Step ${{ github.run_number }}        # Step name
        if: success()                               # Step conditional
        run: echo "${{ env.APP_ENV }}"             # Run command
        env:
          TOKEN: ${{ secrets.DEPLOY_TOKEN }}        # Step-level env
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.sha }}                   # Action input
```

---

## Literal Types

| Type | Examples |
|:-----|:--------|
| `null` | `null` |
| `boolean` | `true`, `false` |
| `number` | `42`, `3.14`, `-1` |
| `string` | `'single quotes'` (to escape a literal single quote, use `''`) |

Falsy values: `null`, `false`, `0`, `''`. Everything else is truthy.

---

## Operators

| Operator | Description | Example |
|:---------|:------------|:--------|
| `==` | Equality (loose, with coercion) | `github.ref == 'refs/heads/main'` |
| `!=` | Inequality | `github.actor != 'dependabot[bot]'` |
| `<` | Less than | `strategy.job-index < 3` |
| `<=` | Less than or equal | `github.run_attempt <= 2` |
| `>` | Greater than | `steps.count.outputs.total > 0` |
| `>=` | Greater than or equal | `job.status >= 'success'` |
| `&&` | Logical AND | `github.ref == 'refs/heads/main' && github.event_name == 'push'` |
| `\|\|` | Logical OR | `github.event_name == 'push' \|\| github.event_name == 'workflow_dispatch'` |
| `!` | Logical NOT | `!cancelled()` |
| `()` | Grouping | `(github.event_name == 'push') && (github.ref == 'refs/heads/main')` |

Operator precedence (highest to lowest): `()`, `!`, `<`, `<=`, `>`, `>=`, `==`, `!=`, `&&`, `||`.

---

## Type Coercion Rules

When comparing values of different types, GitHub Actions coerces them using these rules:

| From | To Number | To Boolean | To String |
|:-----|:----------|:-----------|:----------|
| `null` | `0` | `false` | `''` |
| `true` | `1` | `true` | `'true'` |
| `false` | `0` | `false` | `'false'` |
| `''` (empty string) | `0` | `false` | `''` |
| `'any string'` | `NaN` (equal only to `NaN`) | `true` | `'any string'` |
| `0` | `0` | `false` | `'0'` |
| `42` | `42` | `true` | `'42'` |

String-to-number coercion means `steps.count.outputs.value == 5` is `true` when the output is the string `'5'`.

---

## Built-in Functions

### String Functions

```yaml
steps:
  - if: contains(github.event.pull_request.title, '[WIP]')
    run: echo "This PR is a work in progress"

  - if: startsWith(github.ref, 'refs/tags/v')
    run: echo "Building a release tag"

  - if: endsWith(github.head_ref, '-hotfix')
    run: echo "Hotfix branch detected"

  - run: echo "${{ format('Build {0} on {1}', github.run_number, runner.os) }}"
```

`contains()` is case-insensitive for string comparisons. When passed an array, it checks for item membership:

```yaml
  - if: contains(github.event.pull_request.labels.*.name, 'deploy')
    run: echo "Deploy label is present"
```

### hashFiles

Produces a SHA-256 hash of one or more files. Commonly used for cache keys:

```yaml
  - uses: actions/cache@v4
    with:
      path: node_modules
      key: deps-${{ runner.os }}-${{ hashFiles('**/package-lock.json') }}
```

`hashFiles` accepts glob patterns and returns a single hash. If no files match, it returns an empty string.

### Object Functions

```yaml
steps:
  - name: Debug event payload
    run: echo '${{ toJSON(github.event) }}'

  - name: Parse JSON string into an object
    id: parse
    run: |
      echo 'config={"retries":3,"timeout":30}' >> "$GITHUB_OUTPUT"

  - name: Use parsed value
    run: echo "${{ fromJSON(steps.parse.outputs.config).retries }}"
```

`toJSON()` converts a context object to a pretty-printed JSON string. `fromJSON()` parses a JSON string back into an object for property access.

---

## Status Check Functions

Status functions evaluate the result of previous steps or the current job:

```yaml
steps:
  - name: Run tests
    id: tests
    run: npm test

  - name: Upload coverage on success
    if: success()
    run: npm run coverage:upload

  - name: Notify on failure
    if: failure()
    run: curl -X POST "$SLACK_WEBHOOK" -d '{"text":"Tests failed on ${{ github.ref }}"}'
    env:
      SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK }}

  - name: Cleanup always runs
    if: always()
    run: rm -rf ./tmp

  - name: Handle cancellation
    if: cancelled()
    run: echo "Workflow was cancelled"
```

| Function | Runs When |
|:---------|:----------|
| `success()` | All previous steps succeeded (default implicit condition) |
| `failure()` | Any previous step failed |
| `always()` | Regardless of success, failure, or cancellation |
| `cancelled()` | The workflow run was cancelled |

Combine status functions with other conditions:

```yaml
  - name: Notify only on main branch failure
    if: failure() && github.ref == 'refs/heads/main'
    run: echo "Main branch build is broken"
```

---

## Context Objects

### github

Information about the workflow run and the event that triggered it:

```yaml
steps:
  - run: |
      echo "Repository: ${{ github.repository }}"       # owner/repo
      echo "Event: ${{ github.event_name }}"             # push, pull_request, etc.
      echo "SHA: ${{ github.sha }}"                      # Full commit SHA
      echo "Ref: ${{ github.ref }}"                      # refs/heads/main, refs/tags/v1.0
      echo "Branch: ${{ github.ref_name }}"              # main, v1.0
      echo "Actor: ${{ github.actor }}"                  # Username that triggered
      echo "Workflow: ${{ github.workflow }}"             # Workflow name
      echo "Run ID: ${{ github.run_id }}"                # Unique run identifier
      echo "Run Number: ${{ github.run_number }}"        # Sequential run counter
      echo "Server URL: ${{ github.server_url }}"        # https://github.com
      echo "API URL: ${{ github.api_url }}"              # https://api.github.com
      echo "Token: ${{ github.token }}"                  # Automatic GITHUB_TOKEN
```

Access the full event payload through `github.event`:

```yaml
  - if: github.event.pull_request.draft == false
    run: echo "PR #${{ github.event.pull_request.number }} is ready for review"
```

### env

Access environment variables set at workflow, job, or step level:

```yaml
env:
  GLOBAL_VAR: hello

jobs:
  example:
    runs-on: ubuntu-latest
    env:
      JOB_VAR: world
    steps:
      - run: echo "${{ env.GLOBAL_VAR }} ${{ env.JOB_VAR }}"
```

### vars

Repository, organization, or environment-level configuration variables (not secrets):

```yaml
steps:
  - run: echo "Deploy URL is ${{ vars.DEPLOY_URL }}"
  - run: echo "Feature flag is ${{ vars.ENABLE_BETA }}"
```

### steps

Access outputs and outcome from previous steps within the same job:

```yaml
steps:
  - name: Get version
    id: ver
    run: echo "tag=v1.2.3" >> "$GITHUB_OUTPUT"

  - run: echo "Version is ${{ steps.ver.outputs.tag }}"
  - run: echo "Step outcome was ${{ steps.ver.outcome }}"      # success, failure, cancelled, skipped
  - run: echo "Step conclusion was ${{ steps.ver.conclusion }}" # same as outcome unless continue-on-error
```

### needs

Access outputs from jobs listed in the current job's `needs`:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      artifact-name: ${{ steps.name.outputs.value }}
    steps:
      - id: name
        run: echo "value=app-build-${{ github.run_number }}" >> "$GITHUB_OUTPUT"

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploying ${{ needs.build.outputs.artifact-name }}"
      - if: needs.build.result == 'success'
        run: echo "Build succeeded"
```

### secrets

Access encrypted secrets. Values are masked in logs:

```yaml
steps:
  - run: echo "Token length is ${#TOKEN}"
    env:
      TOKEN: ${{ secrets.API_TOKEN }}

  - run: echo "${{ secrets.GITHUB_TOKEN }}"  # Always available, auto-generated
```

### runner

Information about the runner executing the job:

```yaml
steps:
  - run: |
      echo "OS: ${{ runner.os }}"           # Linux, Windows, macOS
      echo "Arch: ${{ runner.arch }}"       # X64, ARM64
      echo "Name: ${{ runner.name }}"       # Runner name
      echo "Temp: ${{ runner.temp }}"       # Temp directory path
      echo "Tool cache: ${{ runner.tool_cache }}"  # Tool cache directory
```

### inputs

Available in `workflow_dispatch` and reusable workflows (`workflow_call`):

```yaml
on:
  workflow_dispatch:
    inputs:
      environment:
        type: choice
        options: [staging, production]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploying to ${{ inputs.environment }}"
```

### matrix and strategy

Access current matrix values inside a matrix job:

```yaml
jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        node: [20, 22]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node }}
      - run: echo "Job index ${{ strategy.job-index }} of ${{ strategy.job-total }}"
```

---

## Conditional Patterns

Common patterns used in real workflows:

```yaml
steps:
  # Run only on push to main
  - if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    run: npm run deploy

  # Run only on pull requests with a specific label
  - if: contains(github.event.pull_request.labels.*.name, 'deploy')
    run: npm run deploy:preview

  # Run on tag pushes matching a pattern
  - if: startsWith(github.ref, 'refs/tags/v')
    run: npm publish

  # Skip for bot actors
  - if: github.actor != 'dependabot[bot]'
    run: npm run lint

  # Run even if previous steps failed
  - if: always()
    run: npm run cleanup

  # Run only when a previous step failed
  - if: failure()
    run: npm run notify:failure

  # Check a dependent job result
  - if: needs.build.result == 'success'
    run: npm run deploy

  # Combine multiple conditions
  - if: |
      github.event_name == 'pull_request' &&
      github.event.action == 'opened' &&
      !contains(github.event.pull_request.title, '[skip ci]')
    run: npm test

  # Default value with OR operator
  - run: echo "Target is ${{ github.event.inputs.target || 'staging' }}"
```

---

## String Interpolation in Commands

Expressions inside `run` commands are replaced before the shell executes:

```yaml
steps:
  - run: |
      echo "Repository: ${{ github.repository }}"
      echo "Commit message: ${{ github.event.head_commit.message }}"
      curl -X POST https://api.example.com/builds \
        -H "Authorization: Bearer ${{ secrets.API_TOKEN }}" \
        -d '{"sha": "${{ github.sha }}", "ref": "${{ github.ref_name }}"}'
```

Expressions are interpolated as literal text. When building shell commands, be cautious with values that may contain special characters. Use environment variables for untrusted input:

```yaml
  - name: Safe interpolation
    env:
      COMMIT_MSG: ${{ github.event.head_commit.message }}
    run: echo "Message: $COMMIT_MSG"
```

---

## Dynamic Job Names

Use context values to create descriptive job names in the Actions UI:

```yaml
jobs:
  deploy:
    name: Deploy to ${{ inputs.environment }}
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploying"

  test:
    name: Test (Node ${{ matrix.node }} on ${{ matrix.os }})
    strategy:
      matrix:
        node: [20, 22]
        os: [ubuntu-latest, macos-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node }}
      - run: npm test
```
