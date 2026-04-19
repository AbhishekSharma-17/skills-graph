# Dagster — Project Structure

> Source: [docs.dagster.io/guides/build/projects](https://docs.dagster.io/guides/build/projects/structuring-your-dagster-project)

## Table of Contents

- [Creating a New Project](#creating-a-new-project)
- [Default Project Layout](#default-project-layout)
- [Organization Approaches](#organization-approaches)
- [Code Locations](#code-locations)
- [workspace.yaml](#workspaceyaml)
- [Multi-Code-Location Setup](#multi-code-location-setup)
- [Scaffolding with dg CLI](#scaffolding-with-dg-cli)
- [Definitions Loading](#definitions-loading)
- [Best Practices](#best-practices)

---

## Creating a New Project

```bash
# Recommended
uvx create-dagster@latest project my-project
cd my-project

# Install dependencies
uv sync

# Start development
dg dev
```

## Default Project Layout

```
my-project/
├── pyproject.toml
├── README.md
├── src/
│   └── my_project/
│       ├── __init__.py
│       ├── definitions.py      # Definitions entry point
│       └── defs/
│           └── __init__.py
└── tests/
    └── __init__.py
```

## Organization Approaches

### Technology-based (group by tool)

```
src/my_project/defs/
├── dbt/
│   ├── assets.py
│   └── resources.py
├── dlt/
│   ├── assets.py
│   ├── pipelines/
│   │   ├── github.py
│   │   └── hubspot.py
│   └── resources.py
└── snowflake/
    ├── assets.py
    └── resources.py
```

### Concept-based (group by data workflow)

```
src/my_project/defs/
├── ingestion/
│   └── dlt/
│       ├── assets.py
│       └── resources.py
├── transformation/
│   ├── adhoc/
│   │   ├── assets.py
│   │   └── resources.py
│   └── dbt/
│       ├── assets.py
│       ├── partitions.py
│       └── resources.py
└── reporting/
    └── assets.py
```

### Team-based (for larger organizations)

```
src/my_project/defs/
├── data_eng/
│   ├── assets.py
│   ├── resources.py
│   └── schedules.py
├── ml_team/
│   ├── assets.py
│   ├── resources.py
│   └── sensors.py
└── analytics/
    ├── assets.py
    └── schedules.py
```

## Code Locations

A code location is a collection of Dagster definitions deployed in a specific environment. Each code location:
- Contains a single `Definitions` object
- Runs in its own process
- Has its own Python environment
- Communicates via gRPC

Most teams should start with a **single code location** and split only when needed (conflicting dependencies, different release cycles, different Python versions).

## workspace.yaml

### Single code location (Python module)

```yaml
load_from:
  - python_module:
      module_name: my_project.definitions
```

### Multiple code locations (different environments)

```yaml
load_from:
  - python_file:
      relative_path: path/to/data_eng.py
      location_name: data_engineering
      executable_path: venvs/data_eng/bin/python
  - python_file:
      relative_path: path/to/ml_team.py
      location_name: ml_team
      executable_path: venvs/ml/bin/python
```

### gRPC servers (Docker/K8s)

```yaml
load_from:
  - grpc_server:
      host: code-location-a
      port: 4266
      location_name: "location_a"
  - grpc_server:
      host: code-location-b
      port: 4266
      location_name: "location_b"
```

### Starting a gRPC server

```bash
dagster api grpc --python-file /path/to/file.py --host 0.0.0.0 --port 4266
dagster api grpc --module-name my_module.definitions --host 0.0.0.0 --port 4266
```

## Multi-Code-Location Setup

Deployment directory structure for monorepos:

```
my-deployment/
├── pyproject.toml
├── code_locations/
│   ├── location_a/
│   │   ├── pyproject.toml
│   │   └── src/
│   │       └── location_a/
│   │           └── definitions.py
│   └── location_b/
│       ├── pyproject.toml
│       └── src/
│           └── location_b/
│               └── definitions.py
└── workspace.yaml
```

When to split into multiple code locations:
- Multiple teams with conflicting dependencies
- Different release cycles
- Different Python version requirements
- Isolation between team domains

## Scaffolding with dg CLI

```bash
# Scaffold a new asset
dg scaffold defs dagster.asset my_asset

# Scaffold a dbt component
dg scaffold defs dagster_dbt.DbtProjectComponent transform \
  --project-path src/my_project/analytics

# List all definitions
dg list defs
```

## Definitions Loading

### Explicit (recommended)

```python
import dagster as dg

@dg.definitions
def defs():
    return dg.Definitions(
        assets=[asset_a, asset_b],
        resources={"db": DatabaseResource(url=dg.EnvVar("DB_URL"))},
    )
```

### Auto-discovery from modules

```python
import dagster as dg
import my_assets_module

defs = dg.load_definitions_from_module(my_assets_module)
defs = dg.load_definitions_from_modules([module_a, module_b])
defs = dg.load_definitions_from_package_name("my_dagster_package")
defs = dg.load_definitions_from_current_module()
```

### Merging definitions

```python
team_a_defs = dg.Definitions(assets=[...], resources={...})
team_b_defs = dg.Definitions(assets=[...], resources={...})
merged = dg.Definitions.merge(team_a_defs, team_b_defs)
```

## Best Practices

- **Start with a single code location** — split only when you have genuine environment or team isolation needs.
- **Use `group_name` on assets** for UI organization, not separate code locations.
- **Use `@definitions` decorator** for lazy loading — it defers expensive imports.
- **Use `Definitions.merge()`** to combine from multiple modules within one code location.
- **One `Definitions` object per code location** — do not try to register multiple.
- **Resources in Definitions auto-bind** to all assets that request them by parameter name.
- **Call `validate_loadable()` in CI** to catch misconfigurations early.
