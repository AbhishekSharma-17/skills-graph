---
name: posthog
description: "PostHog all-in-one product analytics platform with feature flags, A/B testing, session replay, error tracking, surveys, and data pipelines. MANDATORY TRIGGERS: posthog, PostHog, product analytics, feature flags posthog, session replay, A/B testing posthog, experiment posthog, HogQL, posthog-js, posthog-node, posthog-python. Also trigger when user wants to add product analytics, track user events, run experiments, set up feature flags with analytics, capture session recordings, monitor errors, create in-app surveys, or build a data pipeline from product events. When in doubt about whether to use this skill for analytics or experimentation tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["posthog", "product-analytics", "feature-flags", "ab-testing", "session-replay", "error-tracking", "surveys", "cdp", "hogql", "experimentation"]
---

# PostHog — Skill Router

> All-in-one product analytics platform — event tracking, feature flags, experiments, session replay, error tracking, surveys, and data pipelines.

**Source:** [posthog.com/docs](https://posthog.com/docs) | **SDK:** `posthog-js` / `posthog-python` / `posthog-node` | **License:** MIT (self-hosted) + Cloud

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Setup** | `references/00-overview.md` | Getting started, installation, SDK setup, project configuration |
| **Event Capture** | `references/01-event-capture.md` | Capturing events, identify users, group analytics, properties |
| **Product Analytics** | `references/02-product-analytics.md` | Insights, trends, dashboards, breakdowns, formulas |
| **Funnels & Paths** | `references/03-funnels-paths.md` | Funnel analysis, conversion tracking, user path exploration |
| **Retention & Cohorts** | `references/04-retention-cohorts.md` | Retention insights, cohorts, lifecycle analysis, stickiness |
| **Feature Flags** | `references/05-feature-flags.md` | Creating flags, targeting, rollouts, multivariate flags, payloads |
| **Experiments** | `references/06-experiments.md` | A/B testing, multivariate experiments, statistical significance |
| **Session Replay** | `references/07-session-replay.md` | Recording sessions, configuration, privacy controls, mobile replay |
| **Error Tracking** | `references/08-error-tracking.md` | Exception capture, autocapture, source maps, issue monitoring |
| **Surveys** | `references/09-surveys.md` | In-app surveys, popover/API modes, targeting, question types |
| **Data Pipelines** | `references/10-data-pipelines.md` | CDP sources, destinations, transformations, batch exports |
| **HogQL & Data Warehouse** | `references/11-hogql-data-warehouse.md` | SQL access, HogQL syntax, external sources, data warehouse |
| **SDKs & API** | `references/12-sdks-api.md` | Python, Node.js, JavaScript, React SDKs, REST API reference |

## Installation

```bash
# JavaScript / React (client-side)
npm install posthog-js

# React provider
npm install posthog-js @posthog/react

# Node.js (server-side)
npm install posthog-node

# Python (server-side)
pip install posthog
```

## Quick Reference

- **Docs:** https://posthog.com/docs
- **GitHub:** https://github.com/PostHog/posthog
- **PyPI:** https://pypi.org/project/posthog/
- **npm:** https://www.npmjs.com/package/posthog-js
- **Community:** https://posthog.com/community
