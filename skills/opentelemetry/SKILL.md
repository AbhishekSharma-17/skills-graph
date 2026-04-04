---
name: opentelemetry
description: "Vendor-neutral observability framework for traces, metrics, and logs. MANDATORY TRIGGERS: opentelemetry, otel, otlp, distributed tracing, observability, telemetry, span, tracer, meter, opentelemetry-sdk, opentelemetry-api. Also trigger when user wants to instrument applications, set up distributed tracing, collect metrics or logs, configure an OTel Collector, implement context propagation, or use semantic conventions. When in doubt about whether to use this skill for observability tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["opentelemetry", "observability", "tracing", "metrics", "logs", "otlp", "collector", "distributed-tracing"]
---

# OpenTelemetry — Skill Router

> The CNCF standard for vendor-neutral observability: traces, metrics, logs, and profiles across any language and backend.

**Source:** [opentelemetry.io](https://opentelemetry.io/docs/) Spec v1.55.0 | **Collector:** v1.49.0 | **License:** Apache 2.0

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Architecture** | `references/00-overview.md` | Getting started, installation, core architecture, quickstart |
| **Traces** | `references/01-traces.md` | Spans, span kinds, attributes, events, links, status, trace context |
| **Metrics** | `references/02-metrics.md` | Instruments (counter, gauge, histogram), views, aggregation |
| **Logs** | `references/03-logs.md` | Log data model, bridge API, correlation with traces and metrics |
| **Python SDK** | `references/04-python-sdk.md` | Python instrumentation: traces, metrics, logs, auto-instrumentation |
| **JavaScript SDK** | `references/05-javascript-sdk.md` | Node.js/browser instrumentation: traces, metrics, exporters |
| **Collector Architecture** | `references/06-collector.md` | Collector pipelines, deployment patterns, scaling |
| **Collector Configuration** | `references/07-collector-config.md` | YAML config, receivers, processors, exporters, service pipelines |
| **Semantic Conventions** | `references/08-semantic-conventions.md` | Standard attribute names for HTTP, database, messaging, RPC |
| **Context Propagation** | `references/09-context-propagation.md` | W3C TraceContext, Baggage, B3, propagators, cross-service correlation |
| **Sampling** | `references/10-sampling.md` | Head/tail sampling, ratio-based, parent-based, custom samplers |
| **Exporters** | `references/11-exporters.md` | OTLP, Jaeger, Prometheus, Zipkin, console exporters |
| **Deployment** | `references/12-deployment.md` | Docker, Kubernetes, agent/gateway patterns, production best practices |

## Installation

```bash
# Python
pip install opentelemetry-api opentelemetry-sdk
pip install opentelemetry-exporter-otlp       # OTLP exporter
pip install opentelemetry-instrumentation      # Auto-instrumentation

# Node.js
npm install @opentelemetry/api @opentelemetry/sdk-node
npm install @opentelemetry/auto-instrumentations-node

# Collector (Docker)
docker pull otel/opentelemetry-collector-contrib
docker run -p 4317:4317 -p 4318:4318 otel/opentelemetry-collector-contrib
```

## Quick Reference

- **Docs:** https://opentelemetry.io/docs/
- **GitHub:** https://github.com/open-telemetry
- **Spec:** https://opentelemetry.io/docs/specs/otel/
- **Collector:** https://github.com/open-telemetry/opentelemetry-collector
- **PyPI:** https://pypi.org/project/opentelemetry-api/
- **npm:** https://www.npmjs.com/package/@opentelemetry/api
