# Audit Report — dagster

**Date:** 2026-04-20
**Skill Version:** 1.0.0
**Source Version Tracked:** 1.13.1

## Quality Scores

| Dimension | Score (1-5) | Notes |
|-----------|-------------|-------|
| **Architecture** | 5 | Clean router + 13 leaf references, all under 500 lines, logical topic separation |
| **Content Quality** | 4 | Comprehensive coverage with practical code examples; advanced topics (custom executors, branch deployments) could be deeper |
| **Completeness** | 4 | Covers core asset model, ops/jobs, automation, testing, deployment, integrations, AI/ML. Missing: detailed Dagster UI walkthrough, advanced config patterns, custom type loaders |
| **Maintainability** | 5 | VERSION.json tracks all 13 references with per-file metadata, check-updates.py validates integrity, 90-day staleness threshold |
| **Trigger Quality** | 5 | MANDATORY TRIGGERS cover dagster, @asset, @op, data pipeline, dbt, partitions; description includes broad use-case triggers |

## Coverage Analysis

### Covered Topics
- Software-defined assets (@asset, @multi_asset, AssetSpec, asset checks, AssetSelection)
- Resources and I/O managers (ConfigurableResource, ConfigurableIOManager, EnvVar, lifecycle)
- Ops, jobs, and graphs (@op, @job, @graph, graph-backed assets, RetryPolicy)
- Schedules and sensors (cron, event-driven, asset sensors, run status sensors)
- Partitions and backfills (5 partition types, partition mappings, BackfillPolicy)
- Declarative automation (AutomationCondition, operators, custom conditions)
- Testing (direct invocation, mock resources, context builders, validate_loadable)
- Dagster Pipes (subprocess, Kubernetes, Databricks, Docker)
- Integrations (dbt, Snowflake, BigQuery, DuckDB, Polars, S3, GCS, Airbyte, Fivetran)
- Deployment (Docker Compose, Kubernetes/Helm, Dagster Cloud)
- Project structure (scaffolding, code locations, workspace.yaml, organization patterns)
- AI/ML pipelines (OpenAI, fine-tuning, training pipelines, drift sensors)

### Gaps for Future Versions
- Dagster UI detailed walkthrough (asset catalog, launchpad, lineage view)
- Advanced config patterns (discriminated unions, PermissiveConfig, Enum config)
- Custom Dagster types and type loaders
- Branch deployments and CI/CD patterns
- Dagster+ Insights and cost monitoring
- Additional integrations (OpenAI Agents, LangChain, W&B, MLflow)

## Recommendations
1. Add UI walkthrough reference when skill reaches v1.1
2. Expand integrations reference with AI/ML providers (Anthropic, W&B)
3. Monitor Dagster 2.0 migration path for breaking changes
4. Add advanced config patterns reference for complex use cases
