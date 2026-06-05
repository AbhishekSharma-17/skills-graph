# dbt — Packages

> Source: https://docs.getdbt.com/docs/build/packages

## Table of Contents
- [What Are Packages](#what-are-packages)
- [packages.yml vs dependencies.yml](#packagesyml-vs-dependenciesyml)
- [Installing Packages](#installing-packages)
- [Hub Packages](#hub-packages)
- [Git Packages](#git-packages)
- [Private Packages](#private-packages)
- [Local Packages](#local-packages)
- [Popular Packages](#popular-packages)
- [Version Pinning](#version-pinning)
- [Configuring Packages](#configuring-packages)
- [Managing Packages](#managing-packages)

## What Are Packages

dbt packages are standalone dbt projects containing models, macros, tests, and other resources. They function like libraries — install once, use everywhere.

```yaml
# packages.yml
packages:
  - package: dbt-labs/dbt_utils
    version: 1.3.0
```

```bash
dbt deps    # Install packages
```

```sql
-- Use a macro from the package
select {{ dbt_utils.generate_surrogate_key(['user_id', 'event_date']) }} as event_key
from {{ ref('stg_events') }}
```

## packages.yml vs dependencies.yml

| Feature | packages.yml | dependencies.yml |
|---------|-------------|-----------------|
| **Jinja rendering** | Yes | No |
| **Private packages (tokens)** | Yes | No |
| **dbt Mesh (projects)** | No | Yes |
| **Both packages + projects** | No | Yes |

**Recommendation:** Use `packages.yml` unless you need dbt Mesh cross-project references.

## Installing Packages

### Basic setup

1. Create `packages.yml` at the project root:

```yaml
packages:
  - package: dbt-labs/dbt_utils
    version: 1.3.0
  - package: calogica/dbt_expectations
    version: 0.10.4
```

2. Run `dbt deps`:

```bash
dbt deps
# Installs to dbt_packages/ directory
```

3. Commit `package-lock.yml` (auto-generated):

```bash
git add package-lock.yml
```

### Add to .gitignore

```
# .gitignore
dbt_packages/
target/
logs/
```

## Hub Packages

Packages from [hub.getdbt.com](https://hub.getdbt.com). Recommended method — dbt resolves dependencies automatically.

```yaml
packages:
  - package: dbt-labs/dbt_utils
    version: 1.3.0

  # Semantic version range (recommended)
  - package: dbt-labs/dbt_utils
    version: [">=1.0.0", "<2.0.0"]
```

### Prerelease versions

```yaml
packages:
  - package: brooklyn-data/dbt_artifacts
    version: 0.4.5-a2    # Explicit prerelease

  - package: brooklyn-data/dbt_artifacts
    version: [">=0.4.4", "<0.4.6"]
    install_prerelease: true    # Allow prereleases in range
```

## Git Packages

Install from any Git repository:

```yaml
packages:
  # HTTPS
  - git: "https://github.com/dbt-labs/dbt-utils.git"
    revision: 1.3.0    # Tag, branch, or 40-char commit hash

  # Specific branch
  - git: "https://github.com/my-org/analytics-utils.git"
    revision: main

  # Monorepo subdirectory
  - git: "https://github.com/my-org/mono-repo.git"
    subdirectory: "dbt-packages/utils"
    revision: v2.0.0
```

## Private Packages

### Native private packages (recommended)

```yaml
packages:
  - private: my-org/analytics-utils
    provider: "github"    # "github", "gitlab", "ado"
    revision: "v1.0.0"
```

Requires SSH key configured locally or Git provider configured in dbt Cloud.

### SSH method (CLI only)

```yaml
packages:
  - git: "git@github.com:my-org/analytics-utils.git"
    revision: v1.0.0
```

### Token method (requires packages.yml for Jinja)

```yaml
packages:
  # GitHub
  - git: "https://{{ env_var('DBT_ENV_SECRET_GIT_TOKEN') }}@github.com/my-org/repo.git"
    revision: v1.0.0

  # GitLab
  - git: "https://{{ env_var('DBT_USER') }}:{{ env_var('DBT_ENV_SECRET_TOKEN') }}@gitlab.com/my-org/repo.git"
    revision: v1.0.0

  # Azure DevOps
  - git: "https://{{ env_var('DBT_ENV_SECRET_PAT') }}@dev.azure.com/my-org/project/_git/repo"
    revision: v1.0.0
```

## Local Packages

For monorepos and testing:

```yaml
packages:
  - local: ../shared-macros
  - local: relative/path/to/other-project
```

```
monorepo/
├── project-a/
│   └── packages.yml    # - local: ../shared-macros
├── project-b/
└── shared-macros/
    └── dbt_project.yml
```

### Tarball packages

For security-restricted environments:

```yaml
packages:
  - tarball: https://codeload.github.com/dbt-labs/dbt-utils/tar.gz/1.3.0
    name: 'dbt_utils'
```

## Popular Packages

### dbt-utils (essential)

The most widely used dbt package. SQL helpers, tests, and utilities.

```yaml
packages:
  - package: dbt-labs/dbt_utils
    version: [">=1.0.0", "<2.0.0"]
```

**Key macros:**
```sql
-- Generate surrogate keys
{{ dbt_utils.generate_surrogate_key(['col1', 'col2']) }}

-- Star (select all except specific columns)
{{ dbt_utils.star(ref('model'), except=['_loaded_at', '_deleted']) }}

-- Date spine (generate date series)
{{ dbt_utils.date_spine(datepart="day", start_date="'2020-01-01'", end_date="current_date") }}

-- Unpivot
{{ dbt_utils.unpivot(ref('model'), cast_to='varchar', exclude=['id']) }}

-- Get column values
{% set methods = dbt_utils.get_column_values(table=ref('payments'), column='method') %}
```

**Key tests:**
```yaml
data_tests:
  - dbt_utils.unique_combination_of_columns:
      combination_of_columns: [order_id, item_id]
  - dbt_utils.expression_is_true:
      expression: "total_amount >= 0"
  - dbt_utils.recency:
      datepart: day
      field: created_at
      interval: 1
  - dbt_utils.at_least_one
  - dbt_utils.not_constant
```

### dbt-expectations

Great Expectations-style data quality tests.

```yaml
packages:
  - package: calogica/dbt_expectations
    version: [">=0.10.0", "<0.11.0"]
```

```yaml
data_tests:
  - dbt_expectations.expect_column_values_to_be_between:
      min_value: 0
      max_value: 100
  - dbt_expectations.expect_column_values_to_match_regex:
      regex: "^[A-Z]{2}$"
  - dbt_expectations.expect_table_row_count_to_be_between:
      min_value: 1000
```

### codegen

Auto-generate dbt code from database schemas.

```yaml
packages:
  - package: dbt-labs/codegen
    version: [">=0.12.0", "<0.13.0"]
```

```bash
# Generate a staging model from a source table
dbt run-operation generate_model_yaml --args '{"model_names": ["stg_orders"]}'
dbt run-operation generate_source --args '{"schema_name": "raw", "table_names": ["orders", "customers"]}'
```

### audit_helper

Compare models for data differences.

```yaml
packages:
  - package: dbt-labs/audit_helper
    version: [">=0.10.0", "<0.11.0"]
```

```sql
-- Compare two models
{{ audit_helper.compare_relations(
    a_relation=ref('orders_v1'),
    b_relation=ref('orders_v2'),
    primary_key='order_id'
) }}
```

## Version Pinning

### Recommended: Pin to minor version

```yaml
packages:
  - package: dbt-labs/dbt_utils
    version: [">=1.3.0", "<1.4.0"]
```

### package-lock.yml

Auto-generated by `dbt deps`. Records exact installed versions:
- Commit to version control
- Ensures reproducible installs across environments

```bash
# Update to new versions
dbt deps --upgrade

# Or delete lock file and reinstall
rm package-lock.yml
dbt deps
```

## Configuring Packages

Override package defaults in `dbt_project.yml`:

```yaml
# dbt_project.yml
vars:
  dbt_utils:
    'dbt_utils:schema_override': 'custom_schema'

models:
  dbt_utils:
    +schema: utils
    +materialized: view

seeds:
  dbt_utils:
    +schema: utils_seeds
```

## Managing Packages

### Update packages

```yaml
# Change version in packages.yml
packages:
  - package: dbt-labs/dbt_utils
    version: 1.4.0    # Updated from 1.3.0
```

```bash
dbt deps
dbt run --full-refresh    # May be needed for schema changes
```

### Remove a package

```bash
# Option 1: Delete manually
rm -rf dbt_packages/dbt_utils

# Option 2: Clean all and reinstall
dbt clean    # Deletes dbt_packages/ and target/
dbt deps     # Reinstalls from packages.yml
```

### Suppress unpinned warnings

```yaml
packages:
  - git: https://github.com/my-org/utils.git
    revision: main
    warn-unpinned: false    # Not recommended for production
```
