---
name: grafana
description: "Grafana observability platform — dashboards, visualizations, alerting, Prometheus/Loki integration, data transformations, provisioning as code, Explore mode, and plugin ecosystem. MANDATORY TRIGGERS: grafana, Grafana, grafana-server, GF_*, PromQL, LogQL, grafana.ini, grafana/grafana, dashboard JSON, Grafana alerting, Grafana Cloud. Also trigger when user wants to build monitoring dashboards, visualize metrics or logs, set up alerting with contact points and notification policies, provision dashboards as code, query Prometheus or Loki from Grafana, create dynamic dashboards with variables, explore logs and traces, or extend Grafana with plugins. When in doubt about whether to use this skill for observability or dashboard tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["grafana", "observability", "dashboards", "monitoring", "alerting", "prometheus", "loki", "visualization", "metrics", "logs"]
---

# Grafana — Skill Router

> The open and composable observability and data visualization platform.

**Source:** [grafana.com/docs](https://grafana.com/docs/grafana/latest/) | **Version:** `13.0` | **GitHub:** 73K+ stars

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Setup** | `references/00-overview.md` | Installation, configuration, architecture, editions, Docker setup |
| **Dashboards** | `references/01-dashboards.md` | Creating dashboards, panels, rows, settings, JSON model, sharing |
| **Visualizations** | `references/02-visualizations.md` | Panel types, time series, stat, gauge, table, heatmap, bar chart |
| **Data Sources** | `references/03-data-sources.md` | Adding data sources, built-in connectors, permissions, correlations |
| **Prometheus & PromQL** | `references/04-prometheus.md` | Prometheus data source, PromQL query builder, range/instant vectors |
| **Loki & LogQL** | `references/05-loki.md` | Loki data source, LogQL, log queries, metric queries, parsers |
| **Alerting** | `references/06-alerting.md` | Alert rules, conditions, evaluation groups, recording rules |
| **Notifications** | `references/07-notifications.md` | Contact points, notification policies, silences, mute timings, templates |
| **Variables & Templating** | `references/08-variables.md` | Dashboard variables, query/custom/constant/interval types, chaining |
| **Transformations** | `references/09-transformations.md` | Data transforms, join, filter, group by, calculate field, organize |
| **Explore** | `references/10-explore.md` | Ad-hoc querying, logs/traces/metrics exploration, split view |
| **Provisioning** | `references/11-provisioning.md` | Configuration as code, YAML provisioning, Terraform provider |
| **Plugins & API** | `references/12-plugins-api.md` | Plugin types, installation, HTTP API, service accounts, automation |

## Installation

```bash
# Docker (recommended)
docker run -d -p 3000:3000 --name grafana grafana/grafana-oss:13.0.2

# Docker Compose
docker compose up -d   # see 00-overview.md for compose file

# macOS
brew install grafana && brew services start grafana

# Debian/Ubuntu
sudo apt-get install -y adduser libfontconfig1 musl
wget https://dl.grafana.com/oss/release/grafana_13.0.2_amd64.deb
sudo dpkg -i grafana_13.0.2_amd64.deb
sudo systemctl start grafana-server
```

## Quick Reference

- [Grafana Docs](https://grafana.com/docs/grafana/latest/)
- [Grafana Playground](https://play.grafana.org)
- [Dashboard Gallery](https://grafana.com/grafana/dashboards/)
- [Plugin Catalog](https://grafana.com/grafana/plugins/)
- [GitHub](https://github.com/grafana/grafana)
- [GrafanaCON 2026](https://grafana.com/about/events/grafanacon/)
