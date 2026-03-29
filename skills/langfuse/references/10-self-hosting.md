# Self-Hosting

> Source: [langfuse.com/docs/deployment/self-host](https://langfuse.com/docs/deployment/self-host)

## Table of Contents

- [Overview](#overview)
- [Architecture Components](#architecture-components)
- [Docker Compose (Development)](#docker-compose-development)
- [Kubernetes / Helm (Production)](#kubernetes--helm-production)
- [Cloud Deployments](#cloud-deployments)
- [Environment Variables](#environment-variables)
- [Database Configuration](#database-configuration)
- [Storage Configuration](#storage-configuration)
- [Authentication & SSO](#authentication--sso)
- [Scaling Considerations](#scaling-considerations)
- [Maintenance & Upgrades](#maintenance--upgrades)
- [Pitfalls](#pitfalls)

---

## Overview

Langfuse can be self-hosted for data sovereignty, compliance, or air-gapped environments. Deployment options:

| Option | Scale | HA | Use Case |
|--------|-------|----|----------|
| Docker Compose | Low | No | Development, testing |
| Kubernetes (Helm) | Production | Yes | Production workloads |
| AWS (Terraform) | Production | Yes | AWS-native |
| Azure (Terraform) | Production | Yes | Azure-native |
| GCP (Terraform) | Production | Yes | GCP-native |
| Railway | Low-Medium | No | Quick managed hosting |

## Architecture Components

### Application Layer

| Component | Description | Replicas |
|-----------|-------------|----------|
| **Web Server** | Serves UI, API, and ingestion endpoint | Scale horizontally |
| **Async Worker** | Processes events, computes metrics | Scale horizontally |

### Storage Layer

| Component | Purpose | Notes |
|-----------|---------|-------|
| **Postgres** | Transactional data (users, projects, prompts) | OLTP workload |
| **ClickHouse** | Observability data (traces, spans, generations) | OLAP workload |
| **Redis/Valkey** | Caching (API keys, prompts) and job queues | In-memory |
| **S3/Blob Storage** | Raw events and multi-modal attachments | Durable storage |

### Data Flow

```
SDK → Web Server → S3 (raw events)
                 → Redis (queue)
                        ↓
                   Async Worker → ClickHouse (processed data)
                               → Postgres (metadata)
```

Key architectural decisions:
- Events persisted to S3 before processing (crash recovery)
- In-memory API key caching reduces DB load
- Read-through prompt caching in Redis
- Background migrations minimize upgrade downtime

## Docker Compose (Development)

```yaml
# docker-compose.yml
version: "3.8"
services:
  langfuse-web:
    image: langfuse/langfuse:latest
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/langfuse
      - CLICKHOUSE_URL=http://clickhouse:8123
      - REDIS_CONNECTION_STRING=redis://redis:6379
      - NEXTAUTH_SECRET=your-secret-key
      - NEXTAUTH_URL=http://localhost:3000
      - SALT=your-salt-value
    depends_on:
      - db
      - clickhouse
      - redis

  langfuse-worker:
    image: langfuse/langfuse:latest
    command: ["node", "packages/worker/dist/index.js"]
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/langfuse
      - CLICKHOUSE_URL=http://clickhouse:8123
      - REDIS_CONNECTION_STRING=redis://redis:6379
    depends_on:
      - db
      - clickhouse
      - redis

  db:
    image: postgres:16
    environment:
      - POSTGRES_DB=langfuse
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data

  clickhouse:
    image: clickhouse/clickhouse-server:latest
    volumes:
      - clickhouse_data:/var/lib/clickhouse
    environment:
      - TZ=UTC  # CRITICAL: must be UTC

  redis:
    image: redis:7

volumes:
  postgres_data:
  clickhouse_data:
```

```bash
docker compose up -d
# Access UI at http://localhost:3000
```

## Kubernetes / Helm (Production)

```bash
helm repo add langfuse https://langfuse.github.io/langfuse-k8s
helm repo update

helm install langfuse langfuse/langfuse \
  --set postgresql.enabled=true \
  --set clickhouse.enabled=true \
  --set redis.enabled=true \
  --set langfuse.nextauth.secret="your-secret" \
  --set langfuse.salt="your-salt" \
  --namespace langfuse \
  --create-namespace
```

For production, use external managed databases:

```yaml
# values.yaml
postgresql:
  enabled: false
langfuse:
  database:
    url: "postgresql://user:pass@rds-instance:5432/langfuse"
  clickhouse:
    url: "https://clickhouse-cloud-instance:8443"
  redis:
    url: "redis://elasticache:6379"
```

## Cloud Deployments

### AWS (Terraform)

```hcl
module "langfuse" {
  source = "langfuse/langfuse/aws"

  vpc_id            = var.vpc_id
  subnet_ids        = var.private_subnet_ids
  domain            = "langfuse.example.com"
  certificate_arn   = var.acm_certificate_arn
}
```

Uses: ECS Fargate, RDS PostgreSQL, ElastiCache Redis, S3, ClickHouse Cloud.

### Azure / GCP

Similar Terraform modules available. See [langfuse.com/docs/deployment](https://langfuse.com/docs/deployment/self-host) for cloud-specific guides.

## Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `CLICKHOUSE_URL` | ClickHouse connection string |
| `REDIS_CONNECTION_STRING` | Redis connection string |
| `NEXTAUTH_SECRET` | Random secret for session encryption |
| `NEXTAUTH_URL` | Public URL of your Langfuse instance |
| `SALT` | Random salt for API key hashing |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `LANGFUSE_ENABLE_EXPERIMENTAL_FEATURES` | `false` | Enable experimental features |
| `AUTH_DISABLE_SIGNUP` | `false` | Disable self-registration |
| `SMTP_CONNECTION_URL` | — | Email for invites and notifications |
| `S3_ENDPOINT` | — | S3-compatible storage endpoint |
| `S3_BUCKET_NAME` | — | Bucket for raw events |
| `S3_ACCESS_KEY_ID` | — | S3 access key |
| `S3_SECRET_ACCESS_KEY` | — | S3 secret key |
| `LANGFUSE_LOG_LEVEL` | `info` | Logging level |
| `PORT` | `3000` | Web server port |

## Database Configuration

### PostgreSQL

- Minimum: PostgreSQL 14+
- Recommended: PostgreSQL 16 with connection pooling (PgBouncer)
- Storage: Grows slowly (metadata only)
- **CRITICAL: Timezone must be UTC**

### ClickHouse

- Minimum: ClickHouse 23.8+
- Recommended: ClickHouse Cloud for managed operations
- Storage: Grows with trace volume (primary data store)
- **CRITICAL: Timezone must be UTC**

### Redis

- Minimum: Redis 7+ or Valkey
- Used for: API key cache, prompt cache, job queues
- Memory: Typically 256MB-1GB sufficient
- Persistence: Not required (cache-only)

## Storage Configuration

### S3/Blob Storage

Used for raw event persistence and multi-modal attachments:

```bash
S3_ENDPOINT="https://s3.amazonaws.com"
S3_BUCKET_NAME="langfuse-events"
S3_REGION="us-east-1"
S3_ACCESS_KEY_ID="..."
S3_SECRET_ACCESS_KEY="..."
```

Compatible with: AWS S3, MinIO, Cloudflare R2, GCS (S3-compatible mode).

## Authentication & SSO

### Built-in Auth

Email/password authentication enabled by default.

### SSO (Enterprise)

Langfuse supports SSO via:
- SAML 2.0
- OpenID Connect (OIDC)
- Google Workspace
- GitHub OAuth
- Azure AD / Entra ID

```bash
AUTH_GOOGLE_CLIENT_ID="..."
AUTH_GOOGLE_CLIENT_SECRET="..."

# Or generic OIDC
AUTH_CUSTOM_CLIENT_ID="..."
AUTH_CUSTOM_CLIENT_SECRET="..."
AUTH_CUSTOM_ISSUER="https://auth.example.com"
```

## Scaling Considerations

### Horizontal Scaling

| Component | Scale Strategy |
|-----------|---------------|
| Web Server | Add replicas behind load balancer |
| Async Worker | Add replicas (work distributed via Redis queues) |
| PostgreSQL | Read replicas for dashboard queries |
| ClickHouse | Sharding for very high volume |

### Sizing Guidelines

| Scale | Traces/Day | Web Replicas | Worker Replicas |
|-------|-----------|--------------|-----------------|
| Small | <10K | 1-2 | 1 |
| Medium | 10K-100K | 2-4 | 2-4 |
| Large | 100K-1M | 4-8 | 4-8 |
| XL | >1M | 8+ | 8+ |

## Maintenance & Upgrades

### Upgrades

```bash
# Docker Compose
docker compose pull
docker compose up -d

# Kubernetes
helm repo update
helm upgrade langfuse langfuse/langfuse
```

Langfuse runs background migrations during startup — no manual migration steps needed.

### Backups

- PostgreSQL: Standard pg_dump or managed DB snapshots
- ClickHouse: Built-in backup/restore or cloud snapshots
- S3: Enable versioning for event data durability

## Pitfalls

1. **Non-UTC timezone** — ClickHouse and PostgreSQL MUST run with UTC. Non-UTC causes incorrect query results in dashboards.

2. **Missing S3 configuration** — Without S3, raw events are stored temporarily in Redis. High volume can exhaust Redis memory.

3. **ClickHouse disk space** — Monitor disk usage. ClickHouse stores all observability data and can grow rapidly at high trace volume.

4. **NEXTAUTH_SECRET rotation** — Changing this invalidates all existing sessions. Plan for a brief re-login period.

5. **Network isolation** — Langfuse works in air-gapped environments. Internet access is optional — only needed for model cost registry updates.
