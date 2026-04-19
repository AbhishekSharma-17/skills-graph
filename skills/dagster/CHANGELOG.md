# Changelog — dagster

## [1.0.0] — 2026-04-20

**Source version tracked:** 1.13.1

### Added
- `00-overview.md` — Core concepts, installation, quickstart, architecture, terminology
- `01-assets.md` — Software-defined assets, @asset, @multi_asset, AssetSpec, asset checks
- `02-resources-io-managers.md` — ConfigurableResource, ConfigurableIOManager, EnvVar, lifecycle
- `03-ops-jobs-graphs.md` — @op, @job, @graph, graph-backed assets, RetryPolicy, Nothing type
- `04-schedules-sensors.md` — Cron schedules, sensors, @asset_sensor, @run_status_sensor
- `05-partitions-backfills.md` — Daily/hourly/weekly/monthly, static, dynamic, multi-dimensional, backfill policies
- `06-automation.md` — AutomationCondition, on_cron, eager, on_missing, custom conditions, operators
- `07-testing.md` — Unit testing assets/ops, mock resources, build_asset_context, validate_loadable
- `08-dagster-pipes.md` — External process execution: subprocess, Kubernetes, Databricks, Docker
- `09-integrations.md` — dbt, Snowflake, BigQuery, DuckDB, Polars, S3, GCS, Airbyte, Fivetran
- `10-deployment.md` — Docker Compose, Kubernetes/Helm, Dagster Cloud (serverless/hybrid)
- `11-project-structure.md` — Scaffolding, code locations, workspace.yaml, organization patterns
- `12-ai-ml-pipelines.md` — OpenAI integration, LLM fine-tuning, ML training pipelines

### Stats
- Routing entries: 13
- Reference files: 13
- Total lines: ~4,500
