---
name: temporal
description: "Durable execution platform for building fault-tolerant workflows, long-running processes, and resilient distributed applications. MANDATORY TRIGGERS: temporal, temporal.io, temporalio, durable execution, workflow orchestration engine. Also trigger when the user wants to build fault-tolerant workflows, implement saga patterns, create long-running distributed processes, orchestrate microservices with retries and timeouts, or build durable AI agent pipelines. When in doubt about whether to use this skill for workflow orchestration or durable execution tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["workflows", "durable-execution", "orchestration", "distributed-systems", "fault-tolerance", "microservices", "saga", "retries"]
---

# Temporal

> Source: [docs.temporal.io](https://docs.temporal.io) | Version tracked: 1.28.0 (Python SDK) | `pip install temporalio`

## Reference Files

| File | Read When |
|------|-----------|
| `references/00-overview.md` | Starting with Temporal, understanding durable execution, architecture, installation |
| `references/01-workflows.md` | Defining workflow classes, deterministic constraints, sandbox, parameters |
| `references/02-activities.md` | Defining activities, sync vs async, heartbeating, idempotency |
| `references/03-workers.md` | Running worker processes, task queues, registering workflows and activities |
| `references/04-client.md` | Connecting to Temporal, starting workflows, getting handles, listing executions |
| `references/05-message-passing.md` | Signals, queries, updates, dynamic handlers, wait conditions |
| `references/06-child-workflows.md` | Child workflows, parent close policies, continue-as-new |
| `references/07-error-handling.md` | Retries, timeouts, failure detection, saga pattern, cancellation |
| `references/08-testing.md` | Unit and integration testing, time-skipping, mocking activities, replay testing |
| `references/09-schedules.md` | Scheduling workflows, intervals, cron, backfill, pause/unpause |
| `references/10-versioning.md` | Patching workflows, worker versioning, safe code deployments |
| `references/11-observability.md` | Metrics, tracing, logging, search attributes, visibility |
| `references/12-nexus.md` | Temporal Nexus, cross-namespace services, operations, endpoints |

## Installation

```bash
# Python
pip install temporalio

# TypeScript
npm install @temporalio/client @temporalio/worker @temporalio/workflow @temporalio/activity
```

## Quick Reference

- [Docs](https://docs.temporal.io) | [GitHub](https://github.com/temporalio/temporal) | [PyPI](https://pypi.org/project/temporalio/) | [npm](https://www.npmjs.com/package/@temporalio/client)
