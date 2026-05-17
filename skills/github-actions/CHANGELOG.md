# Changelog

## [1.0.0] — 2026-05-18

Source version tracked: GitHub Actions platform (2026.05)

### Added

- **00-overview.md** — What GitHub Actions is, core terminology, runner types, billing, limits, status badges
- **01-workflow-syntax.md** — Full YAML syntax: name, on, permissions, env, defaults, concurrency, jobs, steps
- **02-event-triggers.md** — Push, pull_request, schedule/cron, workflow_dispatch, workflow_call, repository_dispatch, release events
- **03-jobs-runners.md** — Job dependencies, GitHub-hosted/self-hosted/larger runners, containers, service containers
- **04-steps-actions.md** — Step configuration, marketplace actions, composite/JavaScript/Docker action authoring
- **05-expressions-contexts.md** — Expression syntax, all context objects, functions, conditional patterns
- **06-matrix-strategy.md** — Matrix builds, include/exclude, fail-fast, max-parallel, dynamic matrix with fromJSON
- **07-caching-artifacts.md** — Dependency caching, language-specific cache patterns, artifact upload/download, retention
- **08-secrets-variables.md** — Repository/org/environment secrets, GITHUB_TOKEN permissions, variables, security
- **09-reusable-workflows.md** — Reusable workflows (workflow_call), composite actions, inputs/outputs/secrets, patterns
- **10-environments-deployments.md** — Environments, protection rules, approvals, deployment strategies, rollback
- **11-security-hardening.md** — OIDC cloud auth, SHA pinning, least-privilege tokens, fork security, supply chain
- **12-advanced-patterns.md** — Concurrency groups, path filtering, monorepo CI, release automation, self-hosted scaling

### Stats

- Routing entries: 13
- Reference files: 13
- Total lines: ~5,900
