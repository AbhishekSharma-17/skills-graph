---
name: inngest
description: "Durable workflow orchestration platform for serverless and server environments. MANDATORY TRIGGERS: inngest, durable functions, durable execution, step functions, background jobs, workflow orchestration, inngest.createFunction, step.run, step.sleep, step.waitForEvent. Also trigger when user wants to build reliable background jobs, event-driven workflows, scheduled tasks with retries, or orchestrate multi-step serverless functions. When in doubt about whether to use this skill for background job or workflow tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["inngest", "durable-execution", "workflow", "background-jobs", "serverless", "event-driven", "step-functions", "orchestration"]
---

# Inngest — Skill Router

> Durable workflow orchestration: reliable step functions and AI workflows on serverless, servers, or the edge — without queues or infrastructure.

**Source:** [inngest.com/docs](https://www.inngest.com/docs) | **TS SDK:** v3.x | **Python SDK:** v0.5.x | **License:** Source Available (Server), MIT (SDKs)

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Quickstart** | `references/00-overview.md` | Getting started, installation, core concepts, project setup |
| **Durable Execution Model** | `references/01-durable-execution.md` | How functions execute, memoization, state persistence, fault tolerance |
| **Functions & Triggers** | `references/02-functions-triggers.md` | createFunction config, event triggers, cron triggers, webhooks |
| **Steps & Workflows** | `references/03-steps-workflows.md` | step.run, step.sleep, step.waitForEvent, step.invoke, step.sendEvent |
| **Parallel Execution** | `references/04-parallel-execution.md` | Promise.all patterns, parallel steps, chunked processing |
| **Error Handling & Retries** | `references/05-error-handling.md` | Retries, NonRetriableError, onFailure, step-level error handling |
| **Flow Control** | `references/06-flow-control.md` | Concurrency, throttle, rate limiting, debounce, priority |
| **Event Batching** | `references/07-event-batching.md` | Batch processing, maxSize, timeout, keyed batching |
| **Cancellation** | `references/08-cancellation.md` | cancelOn, timeout, event-based cancellation, cleanup handlers |
| **Middleware** | `references/09-middleware.md` | Lifecycle hooks, dependency injection, encryption, observability |
| **Serve API & Frameworks** | `references/10-serve-frameworks.md` | serve() config, Next.js, Express, FastAPI, Hono, deployment |
| **Python SDK** | `references/11-python-sdk.md` | Python client, FastAPI/Flask/Django integration, async functions |
| **TypeScript Patterns** | `references/12-typescript-patterns.md` | Type-safe events, Zod schemas, advanced TS patterns |

## Installation

```bash
# TypeScript / JavaScript
npm install inngest

# Python
pip install inngest

# Dev Server (required for local development)
npx inngest-cli@latest dev
```

## Quick Reference

- **Docs:** https://www.inngest.com/docs
- **GitHub:** https://github.com/inngest/inngest
- **TypeScript SDK:** https://github.com/inngest/inngest-js
- **Python SDK:** https://github.com/inngest/inngest-py
- **npm:** https://www.npmjs.com/package/inngest
- **PyPI:** https://pypi.org/project/inngest/
- **Changelog:** https://www.inngest.com/changelog
