# Changelog

## [1.0.0] — 2026-08-08

Source version tracked: Celery 5.6.3

### Added

- **00-overview.md** — What is Celery, architecture, installation, broker/backend comparison, concurrency models
- **01-application-config.md** — App setup, Django integration, FastAPI integration, configuration reference
- **02-tasks.md** — Task decorators, bound tasks, naming, options, Pydantic validation, custom classes
- **03-calling-tasks.md** — delay(), apply_async(), signatures, partials, callbacks, ETA/countdown
- **04-canvas-workflows.md** — Chains, groups, chords, starmap, chunks, complex compositions
- **05-workers.md** — Starting workers, concurrency pools, autoscaling, time limits, remote control
- **06-periodic-tasks.md** — Celery Beat, crontab, solar schedules, django-celery-beat
- **07-routing-queues.md** — Task routing, exchanges, priority queues, broadcast, custom routers
- **08-result-backends.md** — Backend comparison, Redis/SQLAlchemy/Django ORM, task states, AsyncResult API
- **09-error-handling.md** — Retries, autoretry, exponential backoff, semipredicates, idempotency patterns
- **10-monitoring.md** — Flower, celery events, programmatic inspection, custom event listeners
- **11-signals-hooks.md** — Task/worker/beat signals, practical examples (Sentry, duration logging)
- **12-testing-deployment.md** — pytest plugin, eager mode, Docker/systemd/supervisor deployment

### Stats

- Routing entries: 13
- Reference files: 13
- Total lines: ~4,800
