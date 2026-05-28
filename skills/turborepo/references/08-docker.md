# Turborepo — Docker Deployment

> Source: [turborepo.dev/docs/guides/tools/docker](https://turborepo.dev/docs/guides/tools/docker)

## Table of Contents

- [The Problem](#the-problem)
- [turbo prune](#turbo-prune)
- [Multi-Stage Dockerfile](#multi-stage-dockerfile)
- [The --docker Flag](#the---docker-flag)
- [Package Manager Examples](#package-manager-examples)
- [Docker Compose](#docker-compose)
- [Common Pitfalls](#common-pitfalls)

## The Problem

In a monorepo, a naive Dockerfile copies the entire repository into the image — including packages that the target app doesn't need. This wastes:

- **Build time** — Installing unnecessary dependencies
- **Image size** — Shipping unused code
- **Cache invalidation** — Any file change in any package triggers a full rebuild

`turbo prune` solves this by generating a minimal monorepo subset containing only the target package and its dependencies.

## turbo prune

### Basic Usage

```bash
# Create a pruned monorepo for the "web" package
turbo prune @repo/web
```

This generates an `out/` directory:

```
out/
├── package.json          # Root package.json
├── pnpm-lock.yaml        # Pruned lockfile (only needed deps)
├── pnpm-workspace.yaml   # Workspace config
├── packages/
│   ├── ui/               # @repo/ui (dependency of web)
│   └── utils/            # @repo/utils (dependency of web)
└── apps/
    └── web/              # @repo/web (target)
```

### With --docker Flag

```bash
turbo prune @repo/web --docker
```

Splits output into two directories for optimal Docker layer caching:

```
out/
├── json/                 # Only package.json files (for install step)
│   ├── package.json
│   ├── pnpm-lock.yaml
│   ├── apps/web/package.json
│   ├── packages/ui/package.json
│   └── packages/utils/package.json
├── full/                 # Full source code (for build step)
│   ├── apps/web/
│   ├── packages/ui/
│   └── packages/utils/
└── pnpm-lock.yaml
```

**Why this matters:** Docker caches each layer. By copying `package.json` files first and installing, then copying source code, you only re-install dependencies when `package.json` changes — not when source code changes.

## Multi-Stage Dockerfile

### Standard Pattern

```dockerfile
FROM node:22-alpine AS base
RUN corepack enable

# Stage 1: Prune the monorepo
FROM base AS pruner
WORKDIR /app
COPY . .
RUN npx turbo prune @repo/web --docker

# Stage 2: Install dependencies
FROM base AS installer
WORKDIR /app

# Copy pruned package.json files first (cached layer)
COPY --from=pruner /app/out/json/ .

# Install only the dependencies needed
RUN pnpm install --frozen-lockfile

# Copy full source code
COPY --from=pruner /app/out/full/ .

# Build the target app
RUN pnpm turbo run build --filter=@repo/web

# Stage 3: Production runner
FROM node:22-alpine AS runner
WORKDIR /app

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 appuser

# Copy only the built output
COPY --from=installer /app/apps/web/.next/standalone ./
COPY --from=installer /app/apps/web/.next/static ./apps/web/.next/static
COPY --from=installer /app/apps/web/public ./apps/web/public

USER appuser
EXPOSE 3000
ENV PORT=3000
CMD ["node", "apps/web/server.js"]
```

### Without --docker Flag (Simpler)

```dockerfile
FROM node:22-alpine AS base
RUN corepack enable

FROM base AS pruner
WORKDIR /app
COPY . .
RUN npx turbo prune @repo/web

FROM base AS builder
WORKDIR /app
COPY --from=pruner /app/out/ .
RUN pnpm install --frozen-lockfile
RUN pnpm turbo run build --filter=@repo/web

FROM node:22-alpine AS runner
WORKDIR /app
COPY --from=builder /app/apps/web/.next/standalone ./
COPY --from=builder /app/apps/web/.next/static ./apps/web/.next/static
COPY --from=builder /app/apps/web/public ./apps/web/public
CMD ["node", "apps/web/server.js"]
```

## The --docker Flag

The `--docker` flag optimizes the `turbo prune` output for Docker:

| Without `--docker` | With `--docker` |
|---------------------|-----------------|
| Single `out/` directory | Split into `json/` and `full/` |
| COPY once | COPY twice (better layer caching) |
| Any file change → re-install | Only package.json changes → re-install |

### When to Use

- **Use `--docker`** when you want maximum Docker cache efficiency (recommended)
- **Skip `--docker`** for simpler Dockerfiles when build time isn't critical

## Package Manager Examples

### pnpm

```dockerfile
FROM node:22-alpine AS base
RUN corepack enable

FROM base AS pruner
WORKDIR /app
COPY . .
RUN npx turbo prune @repo/api --docker

FROM base AS installer
WORKDIR /app
COPY --from=pruner /app/out/json/ .
RUN pnpm install --frozen-lockfile
COPY --from=pruner /app/out/full/ .
RUN pnpm turbo run build --filter=@repo/api
```

### npm

```dockerfile
FROM node:22-alpine AS base

FROM base AS pruner
WORKDIR /app
COPY . .
RUN npx turbo prune @repo/api --docker

FROM base AS installer
WORKDIR /app
COPY --from=pruner /app/out/json/ .
RUN npm ci
COPY --from=pruner /app/out/full/ .
RUN npx turbo run build --filter=@repo/api
```

### yarn (Berry)

```dockerfile
FROM node:22-alpine AS base
RUN corepack enable

FROM base AS pruner
WORKDIR /app
COPY . .
RUN npx turbo prune @repo/api --docker

FROM base AS installer
WORKDIR /app
COPY --from=pruner /app/out/json/ .
RUN yarn install --immutable
COPY --from=pruner /app/out/full/ .
RUN yarn turbo run build --filter=@repo/api
```

## Docker Compose

For local development with Docker Compose:

```yaml
# docker-compose.yml
services:
  web:
    build:
      context: .
      dockerfile: apps/web/Dockerfile
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/mydb

  api:
    build:
      context: .
      dockerfile: apps/api/Dockerfile
    ports:
      - "4000:4000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/mydb

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_PASSWORD: password
      POSTGRES_DB: mydb
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

**Important:** The `context` must be the monorepo root (`.`) so that `turbo prune` has access to all packages.

## Common Pitfalls

1. **Wrong build context** — Docker context must be the monorepo root, not the individual app directory. `turbo prune` needs to see the entire workspace.

2. **Not pinning turbo version** — `npx turbo prune` in Docker may fetch a different version. Pin it: `npx turbo@2.9.15 prune`.

3. **Missing .dockerignore** — Always add a `.dockerignore` to avoid copying `node_modules/`, `.turbo/`, `.git/` into the build context:

```
# .dockerignore
node_modules
.turbo
.git
.next
dist
```

4. **Forgetting to copy lockfile** — The lockfile must be available in the prune stage. It's at the root of the monorepo.

5. **Large images** — Use Alpine-based images and multi-stage builds. The runner stage should only contain the built output, not source code or dev dependencies.

## Related

- [Workspace Structure](04-workspace-structure.md) — How packages are organized
- [CI/CD Integration](07-ci-cd.md) — Docker builds in CI pipelines
- [CLI Reference](12-cli-reference.md) — turbo prune command reference
