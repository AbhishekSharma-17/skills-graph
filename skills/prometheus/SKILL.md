---
name: prometheus
description: "Prometheus monitoring system — time series database, PromQL, metric types, alerting, recording rules, Alertmanager, service discovery, exporters, and client libraries. MANDATORY TRIGGERS: prometheus, Prometheus, PromQL, promql, prometheus.yml, alertmanager, Alertmanager, prometheus-client, prom/prometheus, scrape_configs, recording_rules, alerting_rules, node_exporter, pushgateway. Also trigger when user wants to monitor applications or infrastructure, set up metrics collection, write PromQL queries, configure alerting rules, instrument code with Prometheus client libraries, deploy exporters, set up service discovery, or design a metrics pipeline. When in doubt about whether to use this skill for monitoring or metrics tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["prometheus", "monitoring", "metrics", "alerting", "promql", "time-series", "observability", "tsdb", "alertmanager", "exporters"]
---

# Prometheus — Skill Router

> Open-source monitoring and alerting toolkit with a dimensional data model and powerful query language.

**Source:** [prometheus.io/docs](https://prometheus.io/docs/introduction/overview/) | **Version:** `3.12.0` | **GitHub:** 56K+ stars

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Architecture** | `references/00-overview.md` | Installation, architecture components, when to use Prometheus |
| **Data Model** | `references/01-data-model.md` | Metric names, labels, samples, time series, naming conventions |
| **Metric Types** | `references/02-metric-types.md` | Counter, Gauge, Histogram, Summary, native histograms |
| **Configuration** | `references/03-configuration.md` | prometheus.yml, global settings, scrape configs, relabeling |
| **PromQL Basics** | `references/04-promql-basics.md` | Selectors, range vectors, offset/@ modifiers, subqueries |
| **PromQL Operators** | `references/05-promql-operators.md` | Arithmetic, comparison, logical/set, vector matching, aggregation |
| **PromQL Functions** | `references/06-promql-functions.md` | rate, irate, histogram_quantile, predict_linear, label_replace |
| **Rules** | `references/07-rules.md` | Recording rules, alerting rules, rule groups, promtool validation |
| **Alertmanager** | `references/08-alertmanager.md` | Routing, receivers, grouping, inhibition, silences, templates |
| **Storage** | `references/09-storage.md` | TSDB, WAL, blocks, compaction, retention, remote read/write |
| **Instrumentation** | `references/10-instrumentation.md` | Client libraries, Python/Go/Java, best practices, what to instrument |
| **Exporters** | `references/11-exporters.md` | Node exporter, writing exporters, multi-target pattern, pushgateway |
| **Deployment** | `references/12-deployment.md` | Service discovery, Kubernetes, Docker, federation, high availability |

## Installation

```bash
# Docker (recommended)
docker run -d -p 9090:9090 -v ./prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus:v3.12.0

# Homebrew (macOS)
brew install prometheus && prometheus --config.file=prometheus.yml

# Download binary
curl -LO https://github.com/prometheus/prometheus/releases/download/v3.12.0/prometheus-3.12.0.linux-amd64.tar.gz
tar xvfz prometheus-*.tar.gz && cd prometheus-* && ./prometheus

# Python client
pip install prometheus-client
```

## Quick Reference

- [Prometheus Docs](https://prometheus.io/docs/introduction/overview/)
- [PromQL Cheat Sheet](https://promlabs.com/promql-cheat-sheet/)
- [Awesome Prometheus](https://github.com/roaldnefs/awesome-prometheus)
- [GitHub](https://github.com/prometheus/prometheus)
- [Exporters List](https://prometheus.io/docs/instrumenting/exporters/)
