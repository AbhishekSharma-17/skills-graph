# BullMQ Skill Changelog

## [1.0.0] — 2026-08-01

Source version tracked: **BullMQ 6.0.x**

### Added

- **00-overview.md** — What BullMQ is, architecture, quick start, Redis requirements
- **01-queues.md** — Queue creation, adding jobs, bulk operations, management methods
- **02-workers.md** — Worker creation, concurrency, sandboxed processors, stalled jobs, graceful shutdown
- **03-jobs.md** — Job types (FIFO/LIFO), IDs, data, state lifecycle, removal
- **04-delayed-scheduled.md** — Delayed jobs, Job Schedulers (v6), cron patterns, repeat strategies
- **05-prioritized.md** — Priority values, ordering, runtime priority changes
- **06-retries-backoff.md** — Retry attempts, fixed/exponential/custom backoff, stalled job handling
- **07-flows.md** — FlowProducer, parent-child dependencies, DAGs, child result access
- **08-rate-limiting-dedup.md** — Global rate limiting, manual limiting, deduplication modes
- **09-events.md** — Worker events, QueueEvents, progress tracking, metrics
- **10-connections.md** — Redis client adapters, connection reuse, Redis configuration
- **11-telemetry.md** — OpenTelemetry integration, bullmq-otel, Jaeger, Prometheus
- **12-production-nestjs.md** — Production checklist, graceful shutdown, NestJS integration

### Stats

- Routing entries: 13
- Reference files: 13
- Total lines: ~4,200
