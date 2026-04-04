# Changelog

All notable changes to the `opentelemetry` skill will be documented in this file.

## [1.0.0] — 2026-04-04

**Source version tracked:** OpenTelemetry Spec v1.55.0, Collector v1.49.0, Semantic Conventions v1.40.0

### Added

- `00-overview.md` — Architecture, installation, quickstarts (Python + Node.js), environment variables
- `01-traces.md` — Spans, span kinds, attributes, events, links, status, processors
- `02-metrics.md` — Instruments (counter, gauge, histogram, updowncounter), views, aggregation
- `03-logs.md` — Log data model, bridge API, Python/Node.js logging integration, trace correlation
- `04-python-sdk.md` — Full Python SDK: auto-instrumentation, manual API, FastAPI/Django/Flask integration
- `05-javascript-sdk.md` — Node.js SDK: NodeSDK setup, Express/Fastify/Next.js, browser instrumentation
- `06-collector.md` — Collector architecture, pipelines, deployment patterns, scaling
- `07-collector-config.md` — YAML configuration: receivers, processors, exporters, service pipelines
- `08-semantic-conventions.md` — Standard attributes for HTTP, database, messaging, RPC, resources
- `09-context-propagation.md` — W3C TraceContext, Baggage, B3, manual inject/extract
- `10-sampling.md` — Head/tail sampling, SDK samplers, collector-based sampling strategies
- `11-exporters.md` — OTLP, Jaeger, Prometheus, Zipkin, console exporters, backend compatibility
- `12-deployment.md` — Docker, Kubernetes (Helm, Operator), agent/gateway patterns, production checklist

### Stats

- Routing entries: 13
- Reference files: 13
- Total lines: ~4,800
