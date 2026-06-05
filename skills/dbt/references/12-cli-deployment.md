# dbt — CLI Commands & Deployment

> Source: https://docs.getdbt.com/reference/dbt-commands

## Table of Contents
- [Core Commands](#core-commands)
- [Node Selection](#node-selection)
- [State-Aware Builds](#state-aware-builds)
- [dbt build](#dbt-build)
- [dbt run](#dbt-run)
- [dbt test](#dbt-test)
- [Other Commands](#other-commands)
- [CI/CD Patterns](#cicd-patterns)
- [Production Deployment](#production-deployment)

## Core Commands

### Write commands (one at a time)

| Command | Purpose |
|---------|---------|
| `dbt build` | Run models, tests, seeds, snapshots together |
| `dbt run` | Execute models |
| `dbt seed` | Load CSV files into warehouse |
| `dbt snapshot` | Execute snapshot jobs |
| `dbt clone` | Clone models from a specified state |
| `dbt run-operation` | Invoke a macro manually |

### Read commands (can run in parallel)

| Command | Purpose |
|---------|---------|
| `dbt test` | Execute tests |
| `dbt compile` | Compile SQL (don't execute) |
| `dbt parse` | Parse project, output timing info |
| `dbt ls` / `dbt list` | List project resources |
| `dbt docs generate` | Generate documentation |
| `dbt docs serve` | Serve documentation locally |
| `dbt source freshness` | Check source data freshness |
| `dbt show` | Preview table rows post-transformation |
| `dbt debug` | Debug connections and project config |
| `dbt clean` | Delete artifacts (target/, dbt_packages/) |
| `dbt deps` | Install package dependencies |
| `dbt init` | Initialize a new project |
| `dbt retry` | Retry from point of failure |
| `dbt lint` | Lint SQL files (Fusion engine) |

## Node Selection

dbt uses a powerful selection syntax to target specific resources.

### Basic selection

```bash
# Run a specific model
dbt run --select customers

# Run multiple models
dbt run --select customers orders payments

# Run all models in a directory
dbt run --select staging.*

# Run models with a tag
dbt run --select tag:daily
```

### Graph operators

```bash
# Upstream dependencies (ancestors)
dbt run --select +customers           # customers and all upstream

# Downstream dependents
dbt run --select customers+           # customers and all downstream

# Both directions
dbt run --select +customers+          # Full lineage

# Immediate parents only (1 level)
dbt run --select 1+customers          # customers and direct parents

# Immediate children only
dbt run --select customers+1          # customers and direct children
```

### Selector methods

```bash
# By resource type
dbt ls --select "resource_type:model"
dbt ls --select "resource_type:test"
dbt ls --select "resource_type:source"

# By materialization
dbt ls --select "config.materialized:incremental"

# By tag
dbt run --select "tag:daily"

# By path/directory
dbt run --select "path:models/marts/finance"

# By package
dbt run --select "package:dbt_utils"

# By source
dbt test --select "source:jaffle_shop"
dbt test --select "source:jaffle_shop.orders"
dbt run --select "source:jaffle_shop+"

# By test type
dbt test --select "test_type:data"
dbt test --select "test_type:unit"

# By source freshness
dbt build --select "source_status:fresher+"
```

### Exclusion

```bash
# Run all except specific models
dbt run --exclude customers

# Run staging except one source
dbt run --select staging.* --exclude staging.stripe.*
```

### Set operators

```bash
# Union (either)
dbt run --select "tag:daily tag:finance"

# Intersection (both)
dbt run --select "tag:daily,config.materialized:table"
```

## State-Aware Builds

Compare the current project against a previous state to build only what changed.

### Setup

```bash
# Save current state (artifacts)
dbt run            # Creates target/manifest.json
cp target/manifest.json previous_state/manifest.json
```

### State selectors

```bash
# Models with modified SQL or config
dbt run --select "state:modified" --state ./previous_state

# Modified models + downstream
dbt build --select "state:modified+" --state ./previous_state

# New models only
dbt run --select "state:new" --state ./previous_state
```

### In CI/CD

```bash
# Typically: compare PR branch against production state
dbt build --select "state:modified+" \
  --state ./prod-artifacts \
  --defer --favor-state
```

### Defer and favor-state

```bash
# --defer: Use production state for unmodified upstream models
# --favor-state: Prefer production artifacts when both exist
dbt run --select "state:modified+" \
  --defer \
  --state ./prod-artifacts
```

This avoids rebuilding the entire project in CI — only changed models and their downstream dependencies are built.

## dbt build

The all-in-one command. Runs resources in DAG order: seeds → snapshots → models → tests.

```bash
# Build everything
dbt build

# Build specific models and their tests
dbt build --select customers+

# Build with full refresh
dbt build --full-refresh

# Build only modified (CI)
dbt build --select "state:modified+" --state ./prod-artifacts
```

**Advantages over individual commands:**
- Tests run immediately after their associated model (fail-fast)
- Proper DAG ordering across resource types
- Single command for the full pipeline

## dbt run

Execute model SQL against the warehouse.

```bash
# Run all models
dbt run

# Run specific model
dbt run --select customers

# Run with threads override
dbt run --threads 8

# Run against a specific target
dbt run --target prod

# Full refresh of incremental models
dbt run --full-refresh

# Run with variable override
dbt run --vars '{"start_date": "2024-01-01"}'

# Fail fast (stop on first error)
dbt run --fail-fast
```

## dbt test

Execute data and unit tests.

```bash
# Run all tests
dbt test

# Run tests on specific model
dbt test --select customers

# Run only data tests
dbt test --select "test_type:data"

# Run only unit tests
dbt test --select "test_type:unit"

# Store failures for debugging
dbt test --store-failures

# Run tests on sources
dbt test --select "source:*"
```

## Other Commands

### dbt docs

```bash
# Generate documentation (creates target/catalog.json)
dbt docs generate

# Serve documentation locally
dbt docs serve
dbt docs serve --port 8080
```

### dbt source freshness

```bash
# Check all source freshness
dbt source freshness

# Check specific source
dbt source freshness --select source:jaffle_shop
```

### dbt debug

```bash
# Check connection and project setup
dbt debug
# Verifies: profiles.yml, dbt_project.yml, database connection, git
```

### dbt compile

```bash
# Compile all models to SQL (don't execute)
dbt compile

# Compile specific model
dbt compile --select customers
# Output: target/compiled/<project>/models/customers.sql
```

### dbt show

```bash
# Preview model output (5 rows default)
dbt show --select customers

# Specify row count
dbt show --select customers --limit 20
```

### dbt retry

```bash
# Retry failed nodes from last run
dbt retry
```

### dbt ls / dbt list

```bash
# List all models
dbt ls

# List with output format
dbt ls --output json
dbt ls --output name
dbt ls --output path

# List specific resource types
dbt ls --resource-type model
dbt ls --resource-type source
dbt ls --resource-type test
```

## CI/CD Patterns

### GitHub Actions example

```yaml
# .github/workflows/dbt-ci.yml
name: dbt CI
on:
  pull_request:
    branches: [main]

jobs:
  dbt-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dbt
        run: pip install dbt-core dbt-snowflake

      - name: Install deps
        run: dbt deps

      - name: Download production artifacts
        # Download manifest.json from production
        run: |
          mkdir -p prod-artifacts
          # Fetch from dbt Cloud API or artifact storage

      - name: Build modified models
        run: |
          dbt build \
            --select "state:modified+" \
            --defer \
            --state ./prod-artifacts \
            --target ci
        env:
          DBT_USER: ${{ secrets.DBT_CI_USER }}
          DBT_PASSWORD: ${{ secrets.DBT_CI_PASSWORD }}
```

### Slim CI (build only changes)

```bash
# Compare against production state
dbt build \
  --select "state:modified+" \
  --defer \
  --state ./prod-artifacts \
  --fail-fast
```

## Production Deployment

### Full production run

```bash
# Standard production pipeline
dbt deps                                  # Install packages
dbt seed                                  # Load seed data
dbt snapshot                              # Capture SCD history
dbt run                                   # Build all models
dbt test                                  # Validate data
dbt source freshness                      # Check source freshness
dbt docs generate                         # Update documentation
```

### Orchestrated with dbt build

```bash
# Single command for production
dbt build --target prod

# With failure handling
dbt build --target prod --fail-fast || dbt retry
```

### Common production flags

```bash
dbt run --target prod             # Use production profile
dbt run --threads 16              # Higher parallelism
dbt run --full-refresh            # Force full rebuild
dbt run --fail-fast               # Stop on first failure
dbt run --warn-error              # Treat warnings as errors
```
