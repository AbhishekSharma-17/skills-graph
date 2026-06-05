# dbt — Governance & Mesh

> Source: https://docs.getdbt.com/docs/collaborate/govern/model-access

## Table of Contents
- [Model Access](#model-access)
- [Groups](#groups)
- [Access Modifiers](#access-modifiers)
- [Model Contracts](#model-contracts)
- [Model Versions](#model-versions)
- [dbt Mesh](#dbt-mesh)
- [Cross-Project References](#cross-project-references)

## Model Access

Model access controls how models can be referenced across groups and projects. It establishes clear boundaries between teams and enforces API contracts.

## Groups

Groups organize models with shared ownership. Define who owns what:

```yaml
# models/marts/customers.yml
groups:
  - name: customer_success
    owner:
      name: Customer Success Team
      email: cx@jaffle.shop

  - name: finance
    owner:
      name: Finance Team
      email: finance@jaffle.shop
```

### Assigning models to groups

```yaml
# In YAML properties
models:
  - name: dim_customers
    config:
      group: customer_success

  - name: fct_revenue
    config:
      group: finance
```

```yaml
# In dbt_project.yml (apply to folders)
models:
  jaffle_shop:
    marts:
      customers:
        +group: customer_success
      finance:
        +group: finance
```

**Rules:**
- Each model belongs to exactly one group
- Groups cannot be nested
- Groups define ownership and access boundaries

## Access Modifiers

Three levels control who can `ref()` a model:

| Access | Who Can Reference |
|--------|------------------|
| `private` | Same group only |
| `protected` | Same project (or installed as package) |
| `public` | Any group, package, or project |

**Default:** All models are `protected`.

### Configuration

```yaml
models:
  # Public: stable, well-tested, designed for external use
  - name: dim_customers
    config:
      group: customer_success
      access: public

  # Private: internal implementation detail
  - name: int_customer_history_rollup
    config:
      group: customer_success
      access: private

  # Protected: available within this project only
  - name: stg_customer_surveys
    config:
      group: customer_success
      access: protected
```

### Enforcement

Referencing a model outside its allowed access level raises `DbtReferenceError`:

```
Node model.jaffle_shop.marketing_report attempted to reference
node model.jaffle_shop.int_customer_history_rollup, which is not
allowed because the referenced node is private to the customer_success group.
```

### Restrictions

- Ephemeral models cannot be `public`
- `access: public` does NOT automatically grant database SELECT permissions (use `grants` config for that)

## Model Contracts

Contracts define the expected schema of a model — column names, data types, and constraints. They prevent accidental breaking changes.

### Defining a contract

```yaml
models:
  - name: dim_customers
    config:
      contract:
        enforced: true
    columns:
      - name: customer_id
        data_type: int
        constraints:
          - type: not_null
          - type: primary_key
      - name: first_name
        data_type: varchar(100)
      - name: last_name
        data_type: varchar(100)
      - name: email
        data_type: varchar(255)
        constraints:
          - type: not_null
      - name: created_at
        data_type: timestamp
        constraints:
          - type: not_null
```

### What contracts enforce

- Column names must match exactly
- Data types must match (platform-specific)
- Constraints are applied as DDL (NOT NULL, PRIMARY KEY, etc.)
- Adding/removing columns without updating the contract fails

### Constraint types

| Type | Description |
|------|-------------|
| `not_null` | Column cannot be null |
| `primary_key` | Primary key constraint |
| `foreign_key` | Foreign key to another table |
| `unique` | Values must be unique |
| `check` | Custom SQL check expression |

```yaml
columns:
  - name: status
    data_type: varchar(20)
    constraints:
      - type: not_null
      - type: check
        expression: "status in ('active', 'inactive', 'pending')"
```

### When to use contracts

- Public models consumed by other teams/projects
- Critical mart models that feed dashboards
- Models with downstream consumers that depend on specific schemas
- NOT needed for staging or intermediate models (too early to lock down)

## Model Versions

Versions let you evolve a model's interface without breaking downstream consumers.

```yaml
models:
  - name: dim_customers
    latest_version: 2
    config:
      access: public
      contract:
        enforced: true

    versions:
      - v: 1
        columns:
          - name: customer_id
            data_type: int
          - name: name
            data_type: varchar(200)

      - v: 2
        columns:
          - include: all    # Inherit from model definition
          - name: first_name
            data_type: varchar(100)
          - name: last_name
            data_type: varchar(100)
```

### Referencing versioned models

```sql
-- Reference the latest version (default)
select * from {{ ref('dim_customers') }}

-- Reference a specific version
select * from {{ ref('dim_customers', v=1) }}
select * from {{ ref('dim_customers', v=2) }}
```

### Deprecating versions

```yaml
versions:
  - v: 1
    deprecation_date: 2024-12-31
    # dbt will warn consumers to migrate
  - v: 2
```

## dbt Mesh

dbt Mesh enables multiple dbt projects to work together as a unified data platform. Each team owns their project independently while sharing public models.

### Architecture

```
Team A Project              Team B Project
├── models/                 ├── models/
│   ├── staging/            │   ├── staging/
│   └── marts/              │   └── marts/
│       └── dim_customers   │       └── revenue_report
│           (access: public)│           uses ref('team_a', 'dim_customers')
└── dbt_project.yml         └── dbt_project.yml
```

### Setting up Mesh

**Producer project** (exposes public models):
```yaml
# models/marts/customers.yml
models:
  - name: dim_customers
    config:
      access: public
      contract:
        enforced: true
    columns:
      - name: customer_id
        data_type: int
      - name: email
        data_type: varchar(255)
```

**Consumer project** (references cross-project models):
```yaml
# dependencies.yml
projects:
  - name: team_a_project
    dbt_cloud:
      project_id: "12345"
```

```sql
-- models/revenue_report.sql
select
    c.customer_id,
    c.email,
    sum(o.amount) as total_revenue
from {{ ref('team_a_project', 'dim_customers') }} c
join {{ ref('stg_orders') }} o using (customer_id)
group by 1, 2
```

## Cross-Project References

### Two methods

**1. Project dependencies (dbt Cloud)**
- Lightweight metadata-only resolution
- Models must be `access: public`
- No code duplication

```yaml
# dependencies.yml
projects:
  - name: upstream_project
    dbt_cloud:
      project_id: "12345"
```

**2. Package dependencies (self-hosted)**
- Installs the full project source code
- Heavier but works without dbt Cloud

```yaml
# packages.yml
packages:
  - git: "https://github.com/my-org/upstream-project.git"
    revision: v1.0.0
```

### restrict-access flag

```yaml
# dbt_project.yml (consumer project)
restrict-access: true    # default: false
```

When `true`: Only `access: public` models from packages can be referenced.
When `false`: `protected` models are also accessible from the root project.

### Best practices

- Start with `protected` (default) — upgrade to `public` when models are stable
- Add contracts before making a model `public`
- Use versions for breaking changes to public models
- Keep private models for internal implementation details
- Governance applies only to models — not snapshots, seeds, or sources
