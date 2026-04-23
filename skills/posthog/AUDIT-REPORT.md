# Audit Report — PostHog Skill

**Date:** 2026-04-24
**Skill Version:** 1.0.0
**Source Tracked:** posthog-python 7.13.0 / posthog-js 1.x

## Quality Assessment

| Category | Score (1-5) | Notes |
|----------|:-----------:|-------|
| **Architecture** | 5 | Clean router + 13 focused leaf files covering all PostHog products |
| **Content Quality** | 5 | Practical code examples for JS, React, Python, Node.js; real-world patterns |
| **Completeness** | 5 | All PostHog products covered: analytics, flags, experiments, replay, errors, surveys, CDP, SQL |
| **Maintainability** | 5 | VERSION.json tracks all sources; check-updates.py validates integrity |
| **Trigger Quality** | 5 | Comprehensive MANDATORY TRIGGERS covering product names and use-case descriptions |

## Coverage Analysis

### Products Covered
- [x] Product Analytics (trends, funnels, retention, paths, lifecycle, stickiness)
- [x] Web Analytics
- [x] Feature Flags (boolean, multivariate, payloads, local eval, bootstrapping)
- [x] Experiments (A/B testing, Bayesian stats, holdout groups)
- [x] Session Replay (web + mobile, privacy, console/network capture)
- [x] Error Tracking (autocapture, source maps, issue grouping)
- [x] Surveys (popover, API, targeting, branching, NPS)
- [x] Data Pipelines / CDP (sources, destinations, transformations, batch exports)
- [x] Data Warehouse / HogQL (SQL access, joins, views, warehouse sources)
- [x] SDKs (JavaScript, React, Python, Node.js, REST API)

### SDKs Covered
- [x] posthog-js (JavaScript Web)
- [x] @posthog/react (React hooks + provider)
- [x] posthog-node (Node.js)
- [x] posthog (Python)
- [x] REST API endpoints
- [x] Mobile SDKs (overview + session replay config)

### Integration Patterns
- [x] Next.js App Router setup
- [x] Django integration
- [x] FastAPI integration
- [x] Express middleware
- [x] Reverse proxy (Nginx, Next.js rewrites, Cloudflare Worker)

## Identified Gaps

- Detailed mobile SDK reference (iOS/Android/Flutter) — addressed at overview level; full reference would require additional files
- PostHog AI assistant documentation — emerging feature, limited official docs
- Self-hosted deployment guide — omitted as most users use PostHog Cloud

## Recommendations

1. Add dedicated mobile SDK reference files when mobile replay exits beta
2. Add PostHog AI assistant reference when documentation stabilizes
3. Monitor HogQL syntax changes as it evolves from beta
