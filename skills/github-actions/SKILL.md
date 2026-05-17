---
name: github-actions
description: "GitHub Actions CI/CD platform for workflow automation, testing, building, and deploying code. MANDATORY TRIGGERS: GitHub Actions, github actions, github workflow, CI/CD pipeline, workflow YAML, .github/workflows, actions runner, reusable workflow, composite action, workflow_dispatch, matrix strategy. Also trigger when building CI/CD pipelines, automating tests on push/PR, deploying from GitHub, configuring caching or artifacts in workflows, setting up OIDC cloud auth, or hardening workflow security. When in doubt about whether to use this skill for GitHub CI/CD tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["ci-cd", "github", "automation", "devops", "workflows", "deployment", "testing"]
---

# GitHub Actions

> CI/CD & workflow automation platform — 2026 | [Docs](https://docs.github.com/en/actions) | [Marketplace](https://github.com/marketplace?type=actions) | [Changelog](https://github.blog/changelog/label/actions/)

## Reference Files

| File | Read When |
|:-----|:----------|
| `references/00-overview.md` | Starting with GitHub Actions, core concepts, terminology, quick start |
| `references/01-workflow-syntax.md` | Writing workflow YAML, name, on, jobs, steps, defaults, permissions |
| `references/02-event-triggers.md` | Configuring push, pull_request, schedule, workflow_dispatch, repository_dispatch triggers |
| `references/03-jobs-runners.md` | Job configuration, runner types (hosted/self-hosted), containers, services, job dependencies |
| `references/04-steps-actions.md` | Step configuration, uses vs run, action types (composite/JavaScript/Docker), marketplace |
| `references/05-expressions-contexts.md` | Expression syntax, contexts (github, env, steps, secrets), functions, conditionals |
| `references/06-matrix-strategy.md` | Matrix builds, include/exclude, max-parallel, fail-fast, dynamic matrix generation |
| `references/07-caching-artifacts.md` | Dependency caching, artifact upload/download, retention, cross-job data sharing |
| `references/08-secrets-variables.md` | Secrets management, variables, GITHUB_TOKEN, environment-scoped secrets, permissions |
| `references/09-reusable-workflows.md` | Reusable workflows (workflow_call), inputs/outputs, secrets inheritance, composite actions |
| `references/10-environments-deployments.md` | Environments, protection rules, approvals, wait timers, deployment strategies |
| `references/11-security-hardening.md` | OIDC cloud auth, SHA pinning, least-privilege tokens, supply chain security, dependencies |
| `references/12-advanced-patterns.md` | Concurrency groups, path filtering, monorepo CI, conditional jobs, self-hosted autoscaling |

## Quick Start

Create `.github/workflows/ci.yml` in your repository:

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm test
```

## Quick Reference

- [Workflow syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions) — Full YAML reference
- [Events](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows) — All trigger events
- [Contexts](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts) — Expression contexts
- [Marketplace](https://github.com/marketplace?type=actions) — Community actions
