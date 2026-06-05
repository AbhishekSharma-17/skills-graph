# Changelog — dbt Skill

## [1.0.0] — 2026-06-06

**Source version tracked:** dbt-core 1.11.11

### Added
- `00-overview.md` — What dbt is, core concepts, installation, engines, workflow
- `01-project-structure.md` — dbt_project.yml, profiles.yml, directory layout, naming conventions
- `02-models-materializations.md` — SQL/Python models, materializations (table, view, incremental, ephemeral, materialized view)
- `03-sources-refs.md` — Sources, ref(), source(), freshness, lineage, exposures
- `04-incremental-models.md` — Incremental strategies (merge, append, delete+insert, insert_overwrite), is_incremental(), unique_key
- `05-tests.md` — Data tests, unit tests, built-in tests, singular tests, custom generic tests, store_failures
- `06-jinja-macros.md` — Jinja syntax, control structures, variables, macros, built-in functions
- `07-seeds-snapshots.md` — CSV seeds, SCD Type 2 snapshots, timestamp/check strategies, meta-fields
- `08-packages.md` — packages.yml, Hub/Git/private/local packages, dbt-utils, dbt-expectations, codegen
- `09-hooks-operations.md` — Pre/post hooks, on-run-start/end, run-operation, grants
- `10-semantic-layer.md` — Semantic models, entities, measures, dimensions, metrics, MetricFlow
- `11-governance-mesh.md` — Model access (public/protected/private), contracts, versions, groups, dbt Mesh
- `12-cli-deployment.md` — CLI commands, node selection, state-aware builds, CI/CD, production deployment

### Stats
- Routing entries: 13
- Reference files: 13
- Total lines: ~4,800
