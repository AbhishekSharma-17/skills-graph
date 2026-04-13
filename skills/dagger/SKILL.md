---
name: dagger
description: "Dagger CI/CD engine for writing pipelines as code in Python, Go, and TypeScript with containerized execution, caching, and cross-language modules. MANDATORY TRIGGERS: dagger, dagger.io, Daggerverse, dagger pipeline, CI/CD as code. Also trigger when building CI/CD pipelines in code instead of YAML, containerized workflows, portable CI pipelines, or reusable pipeline modules. When in doubt about whether to use this skill for CI/CD pipeline tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["ci-cd", "pipelines", "containers", "devops", "python", "typescript", "go", "dagger", "automation"]
---

# Dagger

> Version tracked: 0.20.x (v0.20.3) | Source: https://docs.dagger.io

## Reference Files

| File | Read When |
|------|-----------|
| [00-overview](references/00-overview.md) | Starting with Dagger, installation, core concepts |
| [01-core-types](references/01-core-types.md) | Working with Container, Directory, File, Secret, Service types |
| [02-functions](references/02-functions.md) | Writing custom Dagger Functions in Python, Go, TypeScript |
| [03-modules](references/03-modules.md) | Creating, publishing, and consuming Dagger modules |
| [04-caching](references/04-caching.md) | Layer caching, volume caching, cache invalidation |
| [05-services](references/05-services.md) | Ephemeral service containers, networking, databases for testing |
| [06-secrets](references/06-secrets.md) | Secrets management, providers, secure credential injection |
| [07-ci-integrations](references/07-ci-integrations.md) | GitHub Actions, GitLab CI, Jenkins, CircleCI integration |
| [08-dagger-shell](references/08-dagger-shell.md) | Interactive shell, pipe operator, debugging workflows |
| [09-llm-integration](references/09-llm-integration.md) | AI agents, LLM tool use, MCP support in pipelines |
| [10-observability](references/10-observability.md) | OpenTelemetry tracing, terminal UI, Dagger Cloud |
| [11-daggerverse](references/11-daggerverse.md) | Publishing modules, discovering community modules |
| [12-common-patterns](references/12-common-patterns.md) | Build/test/deploy recipes, multi-platform, monorepo patterns |

## Installation

```bash
# macOS
brew install dagger/tap/dagger

# Linux / macOS (curl)
curl -fsSL https://dl.dagger.io/dagger/install.sh | BIN_DIR=/usr/local/bin sh

# Windows
winget install Dagger.Cli

# Python SDK
pip install dagger-io

# Verify
dagger version
```

## Quick Reference

- Docs: https://docs.dagger.io
- GitHub: https://github.com/dagger/dagger
- Daggerverse: https://daggerverse.dev
- PyPI: https://pypi.org/project/dagger-io/
- Discord: https://discord.gg/dagger-io
