---
name: turborepo
description: "Turborepo monorepo build system for JavaScript/TypeScript — task orchestration, caching, workspace management, and CI/CD optimization. MANDATORY TRIGGERS: turborepo, turbo, turbo.json, turbo run, turbo prune, monorepo, workspace. Also trigger when user wants to set up a monorepo, configure task pipelines, optimize CI builds with caching, structure apps and packages in a single repo, use remote caching, or deploy from a monorepo with Docker. When in doubt about whether to use this skill for monorepo tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["turborepo", "monorepo", "build-system", "caching", "workspaces", "ci-cd", "vercel", "typescript"]
---

# Turborepo — Skill Router

> High-performance build system for JavaScript and TypeScript monorepos, written in Rust.

**Source:** [turborepo.dev/docs](https://turborepo.dev/docs) | **Package:** `turbo` v2.9.x | **License:** MPL-2.0

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Setup** | `references/00-overview.md` | Getting started, installation, when to use Turborepo, project init |
| **Configuration** | `references/01-configuration.md` | turbo.json tasks, dependsOn, inputs, outputs, extends |
| **Caching** | `references/02-caching.md` | Local caching, cache hits, content hashing, outputs, cache busting |
| **Remote Caching** | `references/03-remote-caching.md` | Vercel Remote Cache, self-hosted cache, team sharing |
| **Workspace Structure** | `references/04-workspace-structure.md` | apps/ vs packages/, internal packages, creating packages |
| **Environment Variables** | `references/05-environment-variables.md` | env, globalEnv, passThroughEnv, strict/loose mode, wildcards |
| **Running Tasks** | `references/06-running-tasks.md` | turbo run, --filter, --affected, concurrency, dry runs |
| **CI/CD Integration** | `references/07-ci-cd.md` | GitHub Actions, CI pipelines, caching in CI, --affected in CI |
| **Docker Deployment** | `references/08-docker.md` | turbo prune, multi-stage builds, --docker flag, deployment |
| **Watch Mode** | `references/09-watch-mode.md` | turbo watch, development workflow, task-level filtering |
| **Code Generation** | `references/10-generators.md` | turbo gen, workspace scaffolding, custom generators, Plop |
| **Boundaries** | `references/11-boundaries.md` | Package boundaries, tags, dependency rules, import linting |
| **CLI Reference** | `references/12-cli-reference.md` | All CLI commands, flags, options, turbo query, turbo ls |

## Installation

```bash
# Create new monorepo
npx create-turbo@latest

# Add to existing monorepo
npm install turbo --save-dev

# Global install (optional)
npm install turbo --global
```

## Quick Reference

- **Docs:** https://turborepo.dev/docs
- **GitHub:** https://github.com/vercel/turborepo
- **npm:** https://www.npmjs.com/package/turbo
- **Blog:** https://turborepo.dev/blog
- **Examples:** https://github.com/vercel/turborepo/tree/main/examples
