---
name: celery
description: "Python distributed task queue for asynchronous job processing with Redis/RabbitMQ. MANDATORY TRIGGERS: Celery, celery, distributed task queue, background tasks Python, async workers, task scheduling Python, celery beat, celery worker. Also trigger when the user wants to run background jobs in Python, schedule periodic tasks, build task pipelines with chains/groups/chords, integrate async processing with Django or FastAPI, or set up distributed message processing. When in doubt about whether to use this skill for Python background job tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["python", "celery", "task-queue", "distributed", "background-jobs", "redis", "rabbitmq", "async"]
---

# Celery — Distributed Task Queue for Python

> Source: [Celery 5.6.3 documentation](https://docs.celeryq.dev/) | PyPI: `celery`

## Reference Files

| # | File | Read When |
|---|------|-----------|
| 00 | [Overview](references/00-overview.md) | Understanding what Celery is, installation, architecture, quick start |
| 01 | [Application & Configuration](references/01-application-config.md) | Setting up the Celery app, Django integration, configuration settings |
| 02 | [Tasks](references/02-tasks.md) | Defining tasks, decorators, bound tasks, task options, naming, Pydantic validation |
| 03 | [Calling Tasks](references/03-calling-tasks.md) | Using delay(), apply_async(), signatures, partials, ETA, countdown, retry policy |
| 04 | [Canvas Workflows](references/04-canvas-workflows.md) | Chains, groups, chords, starmap, chunks, complex task pipelines |
| 05 | [Workers](references/05-workers.md) | Starting workers, concurrency pools, autoscaling, time limits, remote control |
| 06 | [Periodic Tasks](references/06-periodic-tasks.md) | Celery Beat, crontab schedules, solar schedules, django-celery-beat |
| 07 | [Routing & Queues](references/07-routing-queues.md) | Task routing, exchanges, priority queues, broadcast, manual routing |
| 08 | [Result Backends](references/08-result-backends.md) | Storing results, task states, custom states, backend selection |
| 09 | [Error Handling & Retries](references/09-error-handling.md) | Retries, autoretry, exponential backoff, error callbacks, idempotency |
| 10 | [Monitoring](references/10-monitoring.md) | Flower, celery events, inspect/control commands, event listeners |
| 11 | [Signals & Hooks](references/11-signals-hooks.md) | Task signals, worker signals, beat signals, custom handlers |
| 12 | [Testing & Deployment](references/12-testing-deployment.md) | pytest fixtures, eager mode, deployment, daemonization |

## Installation

```bash
pip install celery                       # Core
pip install "celery[redis]"              # Redis broker + backend
pip install "celery[librabbitmq]"        # RabbitMQ broker (C extension)
pip install "celery[redis,msgpack]"      # Multiple extras
```

## Quick Reference

- Docs: https://docs.celeryq.dev/
- GitHub: https://github.com/celery/celery
- PyPI: https://pypi.org/project/celery/
- Changelog: https://docs.celeryq.dev/en/stable/changelog.html
