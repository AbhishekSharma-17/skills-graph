# Changelog — temporal

## [1.0.0] — 2026-06-09

Source version tracked: `temporalio` 1.28.0 (Python SDK)

### Added

- `00-overview.md` — Durable execution concepts, architecture, installation, minimal examples (Python + TypeScript)
- `01-workflows.md` — Workflow definitions, deterministic constraints, sandbox, parameters, activity calling
- `02-activities.md` — Activity definitions, execution models (async/thread/process), heartbeating, idempotency
- `03-workers.md` — Worker setup, task queues, configuration, tuning, cloud connection, production deployment
- `04-client.md` — Client connection, starting workflows, handles, listing, cancellation, describing
- `05-message-passing.md` — Signals, queries, updates, validators, dynamic handlers, wait conditions
- `06-child-workflows.md` — Child workflows, parent close policies, continue-as-new, external signals
- `07-error-handling.md` — Exception types, retry policies, timeouts, cancellation, saga pattern
- `08-testing.md` — ActivityEnvironment, time-skipping, mocking activities, replay testing
- `09-schedules.md` — Schedule creation, intervals, calendars, cron, backfill, overlap policies
- `10-versioning.md` — Patching (3-step), worker versioning, replay testing, safe deployment checklist
- `11-observability.md` — Logging, Prometheus metrics, OpenTelemetry tracing, search attributes
- `12-nexus.md` — Nexus services, operations, endpoints, cross-namespace communication

### Stats

- Routing entries: 13
- Reference files: 13
- Total lines: ~4,400
