# Audit Report — dbt Skill

**Audit date:** 2026-06-06
**Skill version:** 1.0.0
**Source version:** dbt-core 1.11.11

## Quality Scores

| Dimension | Score (1-5) | Notes |
|-----------|-------------|-------|
| **Architecture** | 5 | Clean router + 13 leaf files. Logical topic separation. All files within size limits. |
| **Content Quality** | 5 | All content sourced from official docs.getdbt.com. Practical code examples throughout. Covers both basic and advanced usage. |
| **Completeness** | 5 | Covers the full dbt surface: models, tests, sources, macros, packages, snapshots, seeds, semantic layer, governance, CLI, and deployment. |
| **Maintainability** | 5 | VERSION.json tracks all references with source pages. check-updates.py validates against PyPI. Clear staleness thresholds. |
| **Trigger Quality** | 5 | MANDATORY TRIGGERS cover primary keywords (dbt, dbt-core, dbt Cloud, dbt run/build/test). Broader triggers catch data transformation and analytics engineering use cases. |

## Coverage Assessment

### Covered Topics
- Core concepts: models, sources, seeds, snapshots, tests, macros
- Materializations: table, view, incremental, ephemeral, materialized view
- Incremental strategies: merge, append, delete+insert, insert_overwrite
- Configuration: dbt_project.yml, profiles.yml, environment variables
- Testing: data tests, unit tests, custom generic tests, dbt-utils tests
- Packages: Hub, Git, private, local, tarball
- Semantic Layer: semantic models, metrics, MetricFlow
- Governance: model access, contracts, versions, groups, dbt Mesh
- Deployment: CLI commands, node selection, state-aware builds, CI/CD

### Areas for Future Expansion
- Python models deep dive (Snowpark, BigQuery DataFrames)
- Adapter-specific patterns (Snowflake Dynamic Tables, BigQuery partitioning)
- dbt Cloud platform features (IDE, scheduling, alerting)
- Advanced macro patterns (dispatch, materialization overrides)
- Unit testing deep dive

## File Size Validation

All reference files are within the 200-500 line target range. No file exceeds 500 lines. SKILL.md router is under 100 lines.
