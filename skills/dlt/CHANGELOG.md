# dlt Skill Changelog

## [1.0.0] — 2026-07-31

Source version tracked: dlt v1.29.1

### Added
- 00-overview.md — What dlt is, installation, quickstart, key concepts, supported destinations
- 01-pipeline.md — Pipeline creation, parameters, run(), write dispositions, refresh modes, load info
- 02-resources.md — @dlt.resource decorator, schema definition, Pydantic models, transformers, parallelism
- 03-sources.md — @dlt.source decorator, resource selection, configuration, nesting control
- 04-incremental-loading.md — Cursor-based incremental, merge strategies, backfills, deduplication, SCD2
- 05-schema-contracts.md — Contract modes (evolve/freeze/discard), Pydantic integration, event streams
- 06-credentials-config.md — secrets.toml, config.toml, environment variables, credential injection, vaults
- 07-rest-api-source.md — Declarative REST API source, authentication, pagination, endpoint relationships
- 08-destinations.md — 26+ destinations, DuckDB, BigQuery, Snowflake, Postgres, filesystem, staging
- 09-performance.md — Extract/normalize/load parallelism, buffer config, file rotation, workers
- 10-transformations.md — add_map, add_filter, transformers, processing steps, ELT, Dataset API
- 11-deployment.md — GitHub Actions, Airflow, Dagster, cloud functions, Docker, credential management
- 12-testing-debugging.md — Unit testing, load inspection, schema debugging, state management, logging

### Stats
- Routing entries: 13
- Reference files: 13
- Total lines: ~4,700
