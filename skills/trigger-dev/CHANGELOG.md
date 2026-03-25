# Trigger.dev Skill Changelog

## [1.0.0] — 2026-03-25

**Source tracked: @trigger.dev/sdk v4.4.3** | **Author: Abhishek Sharma**

### Added
- **SKILL.md Router** — 11 routing entries covering overview, tasks, triggering, runs, scheduling, queues, retries, wait/HITL, realtime, config, and deployment
- **Overview & Setup** (`00-overview.md`) — What Trigger.dev is, architecture, installation, quickstart, SDK imports, framework support, terminology
- **Writing Tasks** (`01-writing-tasks.md`) — Task definition, configuration options, lifecycle hooks (init/onStart/onSuccess/onFailure/catchError), machine presets, payload/output limits, logging, subtasks, common patterns
- **Triggering Tasks** (`02-triggering-tasks.md`) — Backend and inter-task triggering, batch operations, streaming batches, trigger options (delay/TTL/idempotency/debounce/concurrencyKey/queue), payload size handling
- **Runs** (`03-runs.md`) — Run lifecycle, 10 run states, metadata API, tags, runs list/retrieve/subscribe, cancellation, replaying, rescheduling
- **Scheduled Tasks** (`04-scheduled-tasks.md`) — Declarative and imperative cron schedules, cron syntax reference, timezone/DST handling, schedule management API, per-user scheduling pattern
- **Concurrency & Queues** (`05-concurrency-queues.md`) — Queue mechanics, environment concurrency (base + burst), task-level limits, shared queues, per-tenant queuing with concurrencyKey, queue management API, checkpointing/waitpoints
- **Error Handling & Retries** (`06-error-handling-retries.md`) — Retry configuration, global vs task-level, retry.onThrow, retry.fetch with status codes, catchError dynamic handling, AbortTaskRunError, common patterns
- **Wait & Human-in-the-Loop** (`07-wait-and-human-in-loop.md`) — wait.for/wait.until duration pauses, waitpoint tokens, token creation/completion (SDK/HTTP/client), approval workflows, multi-step chains, token management API
- **Realtime & Streaming** (`08-realtime-streaming.md`) — Run subscriptions, streaming with streams.define, React hooks (useRealtimeRun/useRealtimeStream/useRealtimeBatch), TriggerAuthContext, public access tokens, progress bar and AI chat patterns
- **Configuration** (`09-configuration.md`) — trigger.config.ts full reference, runtime options, build configuration, 8 build extensions (Prisma/Puppeteer/FFmpeg/Python/aptGet/envSync/packages/files), OpenTelemetry setup, process management
- **Deployment & CLI** (`10-deployment-cli.md`) — dev command, deploy command with all flags, 4 environments (DEV/STAGING/PREVIEW/PROD), CI/CD with GitHub Actions/GitLab, self-hosting with Docker/K8s, monorepo setup

### Stats
- 11 routing entries in SKILL.md
- 11 reference files (all leaf nodes)
- ~3,600 total lines
