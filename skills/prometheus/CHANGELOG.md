# Changelog

## [1.0.0] — 2026-06-30

**Source version tracked:** Prometheus 3.12.0 | Alertmanager 0.28.0 | Python client 0.25.0

### Added

- `00-overview.md` — Architecture, installation, quick start, Docker Compose, promtool CLI
- `01-data-model.md` — Time series, metric names, labels, naming conventions, exposition format
- `02-metric-types.md` — Counter, Gauge, Histogram (classic + native), Summary, Info, Stateset
- `03-configuration.md` — Global settings, scrape configs, service discovery, relabeling, remote write/read
- `04-promql-basics.md` — Expression types, selectors, range vectors, offset/@ modifiers, subqueries
- `05-promql-operators.md` — Arithmetic, comparison, logical/set, vector matching, aggregation operators
- `06-promql-functions.md` — rate, irate, histogram_quantile, predict_linear, label_replace, aggregation over time
- `07-rules.md` — Recording rules, alerting rules, rule groups, template variables, promtool validation
- `08-alertmanager.md` — Route tree, receivers (Slack/Email/PagerDuty/webhook), inhibition, silences, HA
- `09-storage.md` — TSDB architecture, WAL, compaction, retention, remote storage, backfilling, capacity planning
- `10-instrumentation.md` — Python/Go client libraries, FastAPI/Flask/Django integration, multiprocess mode
- `11-exporters.md` — Common exporters, custom exporter patterns, multi-target pattern, pushgateway
- `12-deployment.md` — Kubernetes (Operator, ServiceMonitor), Docker, federation, HA, scaling, security

### Stats

- Routing entries: 13
- Reference files: 13
- Total lines: ~4,700
