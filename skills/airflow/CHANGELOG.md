# Changelog

## [1.0.0] — 2026-07-29

**Source version tracked:** Apache Airflow 3.3.0

### Added
- 00-overview.md — Architecture, installation, Airflow 3.x changes, CLI reference
- 01-dags.md — DAG declaration, dependencies, control flow, branching, trigger rules
- 02-taskflow-api.md — @task/@dag decorators, data passing, context, specialized decorators
- 03-operators-and-sensors.md — Built-in operators, Jinja templating, sensors, deferrable operators
- 04-xcoms-and-variables.md — XCom push/pull, custom backends, Variables, Params
- 05-connections-and-hooks.md — Connection management, hooks, secrets backends
- 06-scheduling.md — Cron, time zones, data intervals, asset-aware scheduling, timetables
- 07-dynamic-task-mapping.md — expand(), partial(), task groups, zip, filtering
- 08-assets.md — @asset decorator, partitions, aliases, rollup/fan-out mappers
- 09-executors.md — Local, Celery, Kubernetes, multi-executor configuration
- 10-testing.md — DAG validation, unit tests, mocking, CI/CD integration
- 11-deployment.md — Docker Compose, Kubernetes Helm, custom images, production checklist
- 12-best-practices.md — Idempotency, performance, anti-patterns, security, DAG organization

### Stats
- Routing entries: 13
- Reference files: 13
- Total lines: ~5,200
