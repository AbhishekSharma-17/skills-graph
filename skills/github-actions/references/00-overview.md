# GitHub Actions Overview

> Source: [docs.github.com/en/actions](https://docs.github.com/en/actions) | CI/CD & Workflow Automation

## Table of Contents

- [What is GitHub Actions?](#what-is-github-actions)
- [Core Terminology](#core-terminology)
- [How It Works](#how-it-works)
- [Quick Start](#quick-start)
- [Runner Types](#runner-types)
- [Billing Model](#billing-model)
- [GitHub Actions vs Other CI/CD](#github-actions-vs-other-cicd)
- [Common Use Cases](#common-use-cases)
- [Workflow Visualization](#workflow-visualization)
- [Status Badges](#status-badges)
- [Platform Limits](#platform-limits)

---

## What is GitHub Actions?

GitHub Actions is a CI/CD and workflow automation platform built directly into GitHub. It lets you automate builds, tests, deployments, and any custom workflow in response to repository events like pushes, pull requests, issue creation, releases, and scheduled cron jobs.

Key characteristics:

- **Native GitHub integration** — first-class access to repository events, issues, PRs, packages, and deployments
- **Workflow as code** — YAML files stored in `.github/workflows/` alongside your source code
- **Marketplace ecosystem** — 20,000+ community and official actions for common tasks
- **Multi-platform** — run on Linux, Windows, macOS, ARM, and GPU runners
- **Matrix builds** — test across multiple language versions, OS combinations, and configurations in parallel
- **Reusable workflows** — share CI/CD logic across repositories with `workflow_call`

## Core Terminology

| Term | Definition |
|:-----|:-----------|
| **Workflow** | An automated process defined by a YAML file in `.github/workflows/`. A repository can have multiple workflows. |
| **Event** | A trigger that starts a workflow — push, pull_request, schedule, workflow_dispatch, and 40+ others. |
| **Job** | A set of steps that execute on the same runner. Jobs run in parallel by default, or sequentially with `needs`. |
| **Step** | A single task within a job — either runs a shell command (`run`) or uses a reusable action (`uses`). |
| **Action** | A reusable unit of code — can be JavaScript, Docker-based, or composite. Shared via the Marketplace. |
| **Runner** | The machine (virtual or physical) that executes a job. Can be GitHub-hosted or self-hosted. |
| **Artifact** | A file or set of files produced during a workflow run, persisted for download or use by other jobs. |
| **Secret** | An encrypted environment variable stored at the repository, environment, or organization level. |
| **Context** | An object providing information about the workflow run — `github`, `env`, `steps`, `secrets`, `matrix`, etc. |
| **Expression** | A syntax (`${{ }}`) for dynamically evaluating conditions, accessing contexts, and calling functions. |

## How It Works

```
Repository Event (push, PR, schedule, manual, etc.)
        │
        ▼
GitHub checks .github/workflows/*.yml for matching "on:" triggers
        │
        ▼
Matching workflow(s) are queued
        │
        ▼
Jobs are assigned to runners (parallel by default)
        │
        ▼
Each job runs steps sequentially on its runner
        │
        ▼
Results reported back to GitHub (checks, statuses, artifacts)
```

Workflow files must live in the `.github/workflows/` directory at the root of your repository. GitHub automatically discovers and registers any `.yml` or `.yaml` file in that directory.

## Quick Start

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: npm test

      - name: Run linter
        run: npm run lint
```

A Python equivalent:

```yaml
name: Python CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Set up Python
        run: uv python install 3.13

      - name: Install dependencies
        run: uv sync

      - name: Run tests
        run: uv run pytest -x -v

      - name: Type check
        run: uv run mypy src/ --strict

      - name: Lint
        run: uv run ruff check .
```

## Runner Types

### GitHub-Hosted Runners

| Label | OS | CPUs | RAM | Disk |
|:------|:---|:-----|:----|:-----|
| `ubuntu-latest` | Ubuntu 24.04 | 4 | 16 GB | 14 GB SSD |
| `ubuntu-24.04` | Ubuntu 24.04 | 4 | 16 GB | 14 GB SSD |
| `ubuntu-22.04` | Ubuntu 22.04 | 4 | 16 GB | 14 GB SSD |
| `windows-latest` | Windows Server 2022 | 4 | 16 GB | 14 GB SSD |
| `macos-latest` | macOS 15 (Sequoia) | 4 | 14 GB | 14 GB SSD |
| `macos-latest-xlarge` | macOS 15 (Apple Silicon) | 4 | 14 GB | 14 GB SSD |

### Larger Runners (GitHub Teams / Enterprise)

Available in 4, 8, 16, 32, and 64-core Linux configurations. GPU runners (NVIDIA T4, L4) available for ML workloads. ARM64 runners available for native ARM builds.

### Self-Hosted Runners

Install the runner agent on your own hardware. Useful for custom hardware, network access requirements, or cost control at scale. Label them with custom tags for targeting.

## Billing Model

| Plan | Linux Minutes | Windows Multiplier | macOS Multiplier | Storage |
|:-----|:-------------|:-------------------|:-----------------|:--------|
| Free | 2,000/month | 2x | 10x | 500 MB |
| Team | 3,000/month | 2x | 10x | 2 GB |
| Enterprise | 50,000/month | 2x | 10x | 50 GB |

Public repositories get unlimited free minutes on standard GitHub-hosted runners. The multipliers mean 1 macOS minute costs 10 Linux minutes from your quota. Self-hosted runners are free of per-minute charges.

## GitHub Actions vs Other CI/CD

| Feature | GitHub Actions | GitLab CI | Jenkins | CircleCI |
|:--------|:--------------|:----------|:--------|:---------|
| Config location | `.github/workflows/` | `.gitlab-ci.yml` | Jenkinsfile | `.circleci/config.yml` |
| Marketplace | 20,000+ actions | Smaller catalog | 1,800+ plugins | Orbs registry |
| Hosted runners | Yes (Linux/Win/Mac) | Yes (Linux) | No (self-host) | Yes (Linux/Mac) |
| Matrix builds | Native | Native | Plugin | Native |
| GitHub integration | First-party | Limited | Plugin | OAuth |
| Reusable pipelines | workflow_call | includes | Shared libraries | Orbs |
| Free tier | 2,000 min/month | 400 min/month | Free (self-host) | 6,000 min/month |

Key differentiators for GitHub Actions: deepest GitHub integration (checks API, deployments, packages), largest action marketplace, native OIDC for cloud authentication, and no separate platform to manage.

## Common Use Cases

### Continuous Integration
Run tests, linters, and type checks on every push and pull request. Matrix builds test across Node 18/20/22, Python 3.11/3.12/3.13, or multiple OS combinations.

### Continuous Deployment
Deploy to cloud providers (AWS, GCP, Azure, Vercel, Cloudflare) on merge to main. Use environments with protection rules for staging and production gates.

### Automation
- Auto-label issues and PRs based on file paths
- Draft releases with changelogs on tag push
- Run dependency updates with Dependabot
- Publish packages to npm/PyPI on release
- Sync documentation sites on content changes
- Stale issue cleanup on a schedule

### Security
- Run SAST/DAST scans with CodeQL
- Check for leaked secrets with secret scanning
- Audit dependencies with `npm audit` or `pip-audit`
- SBOM generation for supply chain transparency

## Workflow Visualization

GitHub provides a visual graph of your workflow in the Actions tab. Each job appears as a node, with edges showing dependencies defined by `needs`. You can click into any job to see real-time step logs, including timing and output for each step.

The visualization is useful for debugging job ordering, spotting parallelism opportunities, and understanding the critical path of your pipeline.

## Status Badges

Add a workflow status badge to your README:

```markdown
![CI](https://github.com/OWNER/REPO/actions/workflows/ci.yml/badge.svg)
```

Specify a branch:

```markdown
![CI](https://github.com/OWNER/REPO/actions/workflows/ci.yml/badge.svg?branch=main)
```

Specify an event:

```markdown
![CI](https://github.com/OWNER/REPO/actions/workflows/ci.yml/badge.svg?event=push)
```

The badge URL follows the pattern `https://github.com/{owner}/{repo}/actions/workflows/{workflow-file}/badge.svg`.

## Platform Limits

| Resource | Limit |
|:---------|:------|
| Workflow run duration | 35 days maximum |
| Job execution time | 6 hours maximum |
| Matrix jobs per workflow run | 256 |
| Concurrent jobs (Free plan) | 20 |
| Concurrent jobs (Teams) | 60 |
| Concurrent jobs (Enterprise) | 180 |
| Concurrent macOS jobs (Free) | 5 |
| API requests per workflow run | 1,000 |
| API requests per hour per repo | 500 (for GITHUB_TOKEN) |
| Workflow file size | 512 KB maximum |
| Artifact storage per repo | Plan-dependent (500 MB to 50 GB) |
| Artifact retention | 90 days (default), configurable 1-400 days |
| Cache storage per repo | 10 GB |
| Nested reusable workflows | 4 levels deep |
| Workflow runs queued in 10 seconds | 500 per repository |

These limits apply to GitHub-hosted runners. Self-hosted runners have different constraints based on your infrastructure. If you hit the concurrent job limit, additional jobs queue until a slot opens.
