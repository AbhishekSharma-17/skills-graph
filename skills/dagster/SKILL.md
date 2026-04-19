---
name: dagster
description: "Asset-centric data orchestration platform for building, testing, and deploying data pipelines. MANDATORY TRIGGERS: dagster, software-defined assets, @asset, @op, @job, data orchestration, data pipeline, dagster-dbt, dagster pipes, asset materialization, dagster cloud, dagster partitions. Also trigger when user wants to build data pipelines, orchestrate ETL/ELT workflows, schedule data transformations, manage data assets with lineage, or integrate dbt/Snowflake/BigQuery into a pipeline. When in doubt about whether to use this skill for data engineering or pipeline orchestration tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["dagster", "data-orchestration", "data-pipeline", "etl", "assets", "dbt", "data-engineering", "python"]
---

# Dagster — Skill Router

> Asset-centric data orchestration: build, test, and deploy data pipelines with software-defined assets, declarative automation, and 87+ integrations.

**Source:** [docs.dagster.io](https://docs.dagster.io) | **Version:** 1.13.x | **Python:** ≥3.9, <3.15 | **License:** Apache 2.0

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Quickstart** | `references/00-overview.md` | Getting started, installation, core concepts, project scaffolding, architecture |
| **Software-Defined Assets** | `references/01-assets.md` | @asset, @multi_asset, AssetSpec, asset checks, asset groups, dependencies |
| **Resources & I/O Managers** | `references/02-resources-io-managers.md` | ConfigurableResource, ConfigurableIOManager, EnvVar, dependency injection |
| **Ops, Jobs & Graphs** | `references/03-ops-jobs-graphs.md` | @op, @job, @graph, graph-backed assets, RetryPolicy, Nothing type |
| **Schedules & Sensors** | `references/04-schedules-sensors.md` | Cron schedules, event-driven sensors, @asset_sensor, run_status_sensor |
| **Partitions & Backfills** | `references/05-partitions-backfills.md` | Daily/hourly/weekly partitions, static, dynamic, multi-dimensional, backfill policies |
| **Declarative Automation** | `references/06-automation.md` | AutomationCondition, on_cron, eager, on_missing, custom conditions |
| **Testing** | `references/07-testing.md` | Unit testing assets/ops, mock resources, build_asset_context, validate_loadable |
| **Dagster Pipes** | `references/08-dagster-pipes.md` | External process execution: subprocess, Kubernetes, Databricks, Docker |
| **Integrations** | `references/09-integrations.md` | dbt, Snowflake, BigQuery, DuckDB, Polars, S3, GCS, Airbyte, Fivetran |
| **Deployment** | `references/10-deployment.md` | Docker Compose, Kubernetes/Helm, Dagster Cloud (serverless/hybrid), dagster.yaml |
| **Project Structure** | `references/11-project-structure.md` | Scaffolding, code locations, workspace.yaml, multi-team organization |
| **AI/ML Pipelines** | `references/12-ai-ml-pipelines.md` | OpenAI integration, LLM fine-tuning, ML training pipelines, AI workflows |

## Installation

```bash
# Install core + UI
pip install dagster dagster-webserver
# or with uv
uv add dagster dagster-webserver

# Scaffold a new project
uvx create-dagster@latest project my-project

# Start dev server
cd my-project && dg dev
```

## Quick Reference

- **Docs:** https://docs.dagster.io
- **GitHub:** https://github.com/dagster-io/dagster
- **PyPI:** https://pypi.org/project/dagster/
- **Changelog:** https://github.com/dagster-io/dagster/releases
- **Dagster Cloud:** https://dagster.cloud
