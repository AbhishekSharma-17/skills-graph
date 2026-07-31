---
name: bullmq
description: "BullMQ — fastest Redis-based distributed job queue for Node.js with parent-child flows, rate limiting, and OpenTelemetry. MANDATORY TRIGGERS: bullmq, BullMQ, bull queue, bull mq, bullmq-otel, @nestjs/bullmq, FlowProducer, job queue redis. Also trigger when user wants to build Redis-backed job queues, implement background job processing in Node.js, create distributed task pipelines, set up repeatable/scheduled jobs with Redis, or choose between BullMQ vs Trigger.dev vs Inngest. When in doubt about whether to use this skill for Node.js job queue tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["bullmq", "redis", "job-queue", "background-jobs", "nodejs", "typescript", "flows", "rate-limiting", "workers", "opentelemetry"]
---

# BullMQ — Skill Router

> The fastest, most reliable Redis-based distributed queue for Node.js, Python, Rust, Elixir, and more.

**Source:** [bullmq.io](https://bullmq.io/) | **Version:** `6.0.x` | **GitHub:** 9.2K+ stars

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Getting Started** | `references/00-overview.md` | What BullMQ is, installation, first queue/worker, architecture |
| **Queues** | `references/01-queues.md` | Creating queues, adding jobs, bulk operations, queue management |
| **Workers** | `references/02-workers.md` | Job processing, concurrency, sandboxed processors, shutdown |
| **Jobs** | `references/03-jobs.md` | FIFO, LIFO, job IDs, data, removing, state lifecycle |
| **Delayed & Scheduled Jobs** | `references/04-delayed-scheduled.md` | Delays, job schedulers, cron patterns, repeatable jobs |
| **Prioritized Jobs** | `references/05-prioritized.md` | Priority values, ordering, changing priority at runtime |
| **Retries & Backoff** | `references/06-retries-backoff.md` | Attempts, fixed/exponential/custom backoff, stalled jobs |
| **Flows & Dependencies** | `references/07-flows.md` | FlowProducer, parent-child jobs, DAGs, child results |
| **Rate Limiting & Deduplication** | `references/08-rate-limiting-dedup.md` | Global rate limit, manual limiting, dedup modes |
| **Events & Monitoring** | `references/09-events.md` | Worker events, QueueEvents, event streams, progress tracking |
| **Connections & Redis** | `references/10-connections.md` | ioredis, node-redis, Bun, connection reuse, Redis config |
| **Telemetry & Observability** | `references/11-telemetry.md` | OpenTelemetry, bullmq-otel, Jaeger, traces and metrics |
| **Production & NestJS** | `references/12-production-nestjs.md` | Production checklist, graceful shutdown, NestJS integration |

## Installation

```bash
# Node.js / Bun
npm install bullmq

# With NestJS
npm install @nestjs/bullmq bullmq

# OpenTelemetry support
npm install bullmq-otel

# Python
pip install bullmq

# Redis required (v6.2+)
docker run -d --name redis -p 6379:6379 redis:7
```

## Quick Reference

- [BullMQ Docs](https://docs.bullmq.io/)
- [API Reference](https://api.docs.bullmq.io/)
- [GitHub](https://github.com/taskforcesh/bullmq)
- [npm](https://www.npmjs.com/package/bullmq)
