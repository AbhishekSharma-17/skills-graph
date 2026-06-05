---
name: dbt
description: "Data transformation with dbt (data build tool) — SQL-based modeling, testing, documentation, incremental builds, Jinja macros, snapshots, semantic layer, and deployment. MANDATORY TRIGGERS: dbt, data build tool, dbt-core, dbt Cloud, dbt run, dbt build, dbt test. Also trigger when the user wants to build SQL transformation pipelines, define data models with refs, write data quality tests, create incremental models, use Jinja macros in SQL, manage data warehouse transformations, or set up analytics engineering workflows. When in doubt about whether to use this skill for data transformation tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["dbt", "data-transformation", "sql", "analytics-engineering", "data-modeling", "elt"]
---

# dbt — Data Build Tool

> Version tracked: dbt-core 1.11.11 (stable) / 2.0.0a1 (alpha) · Source: https://docs.getdbt.com

## Reference Files

| File | Read When |
|------|-----------|
| `references/00-overview.md` | Starting with dbt, understanding core concepts, installation |
| `references/01-project-structure.md` | Setting up dbt_project.yml, profiles.yml, directory layout, naming conventions |
| `references/02-models-materializations.md` | Writing SQL/Python models, choosing materializations (table, view, incremental, ephemeral) |
| `references/03-sources-refs.md` | Declaring sources, using ref() and source(), source freshness, lineage |
| `references/04-incremental-models.md` | Building incremental models, strategies (merge, append, delete+insert), is_incremental() |
| `references/05-tests.md` | Writing data tests (unique, not_null, relationships), singular tests, custom generic tests |
| `references/06-jinja-macros.md` | Jinja templating in SQL, writing macros, built-in functions, whitespace control |
| `references/07-seeds-snapshots.md` | Loading CSV seeds, SCD Type 2 snapshots, timestamp/check strategies |
| `references/08-packages.md` | Installing packages (dbt-utils, dbt-expectations), Hub/Git/private packages |
| `references/09-hooks-operations.md` | Pre/post hooks, on-run-start/end, run-operation, grants, custom SQL execution |
| `references/10-semantic-layer.md` | Defining metrics, semantic models, entities, measures, dimensions, MetricFlow |
| `references/11-governance-mesh.md` | Model access (public/protected/private), contracts, versions, groups, dbt Mesh |
| `references/12-cli-deployment.md` | CLI commands (run, build, test), node selection, CI/CD, state-aware builds |

## Installation

```bash
# dbt Core (Python)
pip install dbt-core dbt-postgres    # or dbt-snowflake, dbt-bigquery, dbt-databricks

# Initialize a new project
dbt init my_project

# Install dependencies
dbt deps
```

## Quick Reference

- [Official Documentation](https://docs.getdbt.com)
- [dbt Hub — Packages](https://hub.getdbt.com)
- [GitHub — dbt-core](https://github.com/dbt-labs/dbt-core)
- [PyPI — dbt-core](https://pypi.org/project/dbt-core/)
- [dbt Learn — Free Courses](https://learn.getdbt.com)
