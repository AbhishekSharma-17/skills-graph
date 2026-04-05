# Changelog — inngest

## [1.0.0] — 2026-04-05

**Source version tracked:** TS SDK v3.x, Python SDK v0.5.x

### Added
- `00-overview.md` — Core concepts, installation, quickstart for TS and Python
- `01-durable-execution.md` — Execution model, memoization, state persistence
- `02-functions-triggers.md` — createFunction config, event/cron/webhook triggers
- `03-steps-workflows.md` — Step primitives: run, sleep, sleepUntil, waitForEvent, invoke, sendEvent
- `04-parallel-execution.md` — Promise.all patterns, parallel steps, chunked processing
- `05-error-handling.md` — Retries, NonRetriableError, onFailure, step-level errors
- `06-flow-control.md` — Concurrency, throttle, rate limiting, debounce, priority
- `07-event-batching.md` — Batch processing config, keyed batching, constraints
- `08-cancellation.md` — cancelOn events, timeout, cleanup handlers
- `09-middleware.md` — Lifecycle hooks, dependency injection, encryption
- `10-serve-frameworks.md` — serve() API, framework adapters, deployment
- `11-python-sdk.md` — Python client, FastAPI/Flask/Django integration
- `12-typescript-patterns.md` — Type-safe events, Zod schemas, advanced patterns

### Stats
- Routing entries: 13
- Reference files: 13
- Total lines: ~4100
