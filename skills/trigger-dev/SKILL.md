---
name: trigger-dev
description: "Build and deploy TypeScript background jobs, AI workflows, and scheduled tasks with Trigger.dev v4. MANDATORY TRIGGERS: trigger.dev, trigger dev, triggerdev, background jobs, background tasks typescript, long-running tasks, durable workflows, cron jobs typescript. Also trigger when user wants to build background processing in TypeScript, create scheduled tasks with cron, implement retry logic for jobs, set up task queues and concurrency, add human-in-the-loop approval workflows, or deploy serverless background workers. When in doubt about whether to use this skill for background job tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["trigger-dev", "background-jobs", "typescript", "cron", "queues", "workflows", "serverless"]
---

# Trigger.dev — Skill Router

> Build and deploy TypeScript background jobs, AI workflows, and scheduled tasks with retries, queues, observability, and elastic scaling.

**Source:** [trigger.dev](https://trigger.dev) v4.4.3 | **SDK:** `@trigger.dev/sdk` | **License:** Apache 2.0

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Setup** | `references/00-overview.md` | Getting started, installation, project setup, what Trigger.dev is, quickstart |
| **Writing Tasks** | `references/01-writing-tasks.md` | Defining tasks, task configuration, lifecycle hooks, init, machine presets |
| **Triggering Tasks** | `references/02-triggering-tasks.md` | trigger(), batchTrigger(), triggerAndWait(), delays, TTL, debounce, idempotency |
| **Runs** | `references/03-runs.md` | Run lifecycle, states, metadata, tags, cancellation, replaying, runs API |
| **Scheduled Tasks** | `references/04-scheduled-tasks.md` | Cron jobs, declarative/imperative schedules, timezones, schedule management |
| **Concurrency & Queues** | `references/05-concurrency-queues.md` | Queue configuration, concurrency limits, shared queues, per-tenant, burst |
| **Error Handling & Retries** | `references/06-error-handling-retries.md` | Retry config, exponential backoff, retry.onThrow, retry.fetch, AbortTaskRunError |
| **Wait & Human-in-the-Loop** | `references/07-wait-and-human-in-loop.md` | wait.for, wait.until, wait.forToken, approval workflows, token management |
| **Realtime & Streaming** | `references/08-realtime-streaming.md` | Realtime API, React hooks, run subscriptions, streaming, SSE |
| **Configuration** | `references/09-configuration.md` | trigger.config.ts, build extensions, runtime, telemetry, machines |
| **Deployment & CLI** | `references/10-deployment-cli.md` | dev command, deploy command, CI/CD, environments, self-hosting |

## Installation

```bash
# Initialize a new Trigger.dev project
npx trigger.dev@latest init

# Or add to existing project
npm install @trigger.dev/sdk
```

## Quick Reference

- **Docs:** https://trigger.dev/docs
- **GitHub:** https://github.com/triggerdotdev/trigger.dev
- **npm:** https://www.npmjs.com/package/@trigger.dev/sdk
- **Dashboard:** https://cloud.trigger.dev
