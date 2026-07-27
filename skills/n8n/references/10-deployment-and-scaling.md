# Deployment and Scaling

> Source: https://docs.n8n.io/deploy/

## Table of Contents

- [Deployment Options](#deployment-options)
- [Docker Deployment](#docker-deployment)
- [npm Installation](#npm-installation)
- [Cloud Provider Deployment](#cloud-provider-deployment)
- [n8n Cloud](#n8n-cloud)
- [Database Configuration](#database-configuration)
- [Queue Mode](#queue-mode)
- [Scaling Strategies](#scaling-strategies)
- [Monitoring](#monitoring)
- [Updates and Maintenance](#updates-and-maintenance)
- [Common Pitfalls](#common-pitfalls)

## Deployment Options

| Option | Best For | Complexity |
|--------|----------|-----------|
| **n8n Cloud** | Teams wanting zero ops | Lowest |
| **Docker** | Self-hosted production | Medium |
| **Docker Compose** | Self-hosted with database | Medium |
| **npm** | Development and testing | Low |
| **Cloud provider** | Enterprise/custom infra | Highest |

## Docker Deployment

### Basic Docker Run

```bash
docker volume create n8n_data
docker run -d \
  --name n8n \
  --restart always \
  -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  -e WEBHOOK_URL=https://n8n.example.com/ \
  -e N8N_ENCRYPTION_KEY=your-strong-key \
  docker.n8n.io/n8nio/n8n
```

### Docker Compose with PostgreSQL

```yaml
version: "3.8"
services:
  n8n:
    image: docker.n8n.io/n8nio/n8n
    restart: always
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=0.0.0.0
      - N8N_PORT=5678
      - N8N_PROTOCOL=https
      - WEBHOOK_URL=https://n8n.example.com/
      - N8N_ENCRYPTION_KEY=${ENCRYPTION_KEY}
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_DATABASE=n8n
      - DB_POSTGRESDB_USER=n8n
      - DB_POSTGRESDB_PASSWORD=${DB_PASSWORD}
      - EXECUTIONS_DATA_SAVE_ON_ERROR=all
      - EXECUTIONS_DATA_SAVE_ON_SUCCESS=none
      - EXECUTIONS_DATA_MAX_AGE=168
    volumes:
      - n8n_data:/home/node/.n8n
    depends_on:
      postgres:
        condition: service_healthy

  postgres:
    image: postgres:16
    restart: always
    environment:
      - POSTGRES_USER=n8n
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=n8n
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U n8n"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  n8n_data:
  postgres_data:
```

### Docker with Reverse Proxy (Caddy)

```
Caddyfile:
  n8n.example.com {
    reverse_proxy n8n:5678
  }
```

## npm Installation

### Global Install

```bash
npm install n8n -g
n8n start

# With custom port
N8N_PORT=8080 n8n start

# With tunnel (for webhook testing)
n8n start --tunnel
```

### Process Manager (PM2)

```bash
npm install pm2 -g
pm2 start n8n --name n8n
pm2 save
pm2 startup
```

## Cloud Provider Deployment

### Supported Providers

| Provider | Method |
|----------|--------|
| **DigitalOcean** | Docker on Droplet or App Platform |
| **AWS** | ECS, EC2, or Lambda (limited) |
| **Azure** | Container Instances or App Service |
| **Google Cloud** | Cloud Run or GKE |
| **Hetzner** | Docker on VPS |
| **Heroku** | Container deployment |
| **OpenShift** | Kubernetes deployment |

### AWS ECS Example

```bash
# Build and push to ECR
docker tag n8n:latest <account>.dkr.ecr.<region>.amazonaws.com/n8n:latest
docker push <account>.dkr.ecr.<region>.amazonaws.com/n8n:latest

# Configure ECS task with:
# - CPU: 512 (0.5 vCPU minimum)
# - Memory: 1024 MB minimum
# - Port mapping: 5678
# - Environment variables for DB, encryption key, webhook URL
# - EFS volume for persistent storage
```

### Google Cloud Run

```bash
gcloud run deploy n8n \
  --image docker.n8n.io/n8nio/n8n \
  --port 5678 \
  --memory 1Gi \
  --set-env-vars "DB_TYPE=postgresdb,DB_POSTGRESDB_HOST=/cloudsql/..." \
  --add-cloudsql-instances PROJECT:REGION:INSTANCE
```

## n8n Cloud

Managed hosting with zero infrastructure management:

### Features

- Automatic updates and backups
- Built-in SSL certificates
- Team collaboration (projects, sharing)
- AI Assistant for building workflows
- Execution quotas based on plan
- Support SLA

### Plans

| Plan | Executions/Month | Active Workflows |
|------|-------------------|-----------------|
| **Starter** | 2,500 | 5 |
| **Pro** | 10,000 | Unlimited |
| **Enterprise** | Custom | Unlimited |

## Database Configuration

### SQLite (Default)

- Zero configuration required
- Data stored in `~/.n8n/database.sqlite`
- Not suitable for queue mode or high concurrency
- Fine for development and small deployments

### PostgreSQL (Recommended for Production)

```bash
export DB_TYPE=postgresdb
export DB_POSTGRESDB_HOST=localhost
export DB_POSTGRESDB_PORT=5432
export DB_POSTGRESDB_DATABASE=n8n
export DB_POSTGRESDB_USER=n8n
export DB_POSTGRESDB_PASSWORD=your_password
export DB_POSTGRESDB_SCHEMA=public
```

### Connection Pooling

```bash
# For high-traffic instances
export DB_POSTGRESDB_POOL_SIZE=20
```

## Queue Mode

Scale n8n horizontally by separating the web server from execution workers.

### Architecture

```
┌──────────────┐     ┌──────────┐     ┌──────────────┐
│ n8n Main     │────▶│  Redis   │◀────│ n8n Worker 1 │
│ (webhooks,   │     │ (queue)  │     │ (executions) │
│  editor, API)│     └──────────┘     └──────────────┘
└──────────────┘           ▲          ┌──────────────┐
                           └──────────│ n8n Worker 2 │
                                      │ (executions) │
                                      └──────────────┘
```

### Configuration

```bash
# Main process
export EXECUTIONS_MODE=queue
export QUEUE_BULL_REDIS_HOST=redis
export QUEUE_BULL_REDIS_PORT=6379

# Worker process
n8n worker
```

### Docker Compose with Queue Mode

```yaml
services:
  n8n-main:
    image: docker.n8n.io/n8nio/n8n
    command: n8n start
    environment:
      - EXECUTIONS_MODE=queue
      - QUEUE_BULL_REDIS_HOST=redis
      # ... other env vars

  n8n-worker:
    image: docker.n8n.io/n8nio/n8n
    command: n8n worker
    deploy:
      replicas: 3
    environment:
      - EXECUTIONS_MODE=queue
      - QUEUE_BULL_REDIS_HOST=redis
      # ... other env vars

  redis:
    image: redis:7-alpine

  postgres:
    image: postgres:16
```

## Scaling Strategies

### Concurrency Control

```bash
# Limit concurrent workflow executions
export N8N_CONCURRENCY_PRODUCTION_LIMIT=20

# Per-workflow concurrency
# Set in workflow settings → Execution settings
```

### Execution Data Management

```bash
# Save execution data only on errors
export EXECUTIONS_DATA_SAVE_ON_SUCCESS=none
export EXECUTIONS_DATA_SAVE_ON_ERROR=all

# Prune old execution data
export EXECUTIONS_DATA_MAX_AGE=168  # Hours (7 days)
export EXECUTIONS_DATA_PRUNE=true
export EXECUTIONS_DATA_PRUNE_MAX_COUNT=50000
```

### Binary Data Storage

```bash
# Store binary data externally (S3, GCS)
export N8N_EXTERNAL_STORAGE_S3_BUCKET=my-n8n-files
export N8N_EXTERNAL_STORAGE_S3_REGION=us-east-1
export N8N_EXTERNAL_STORAGE_S3_ACCESS_KEY=...
export N8N_EXTERNAL_STORAGE_S3_SECRET_KEY=...
```

### Memory Optimization

```bash
# Increase Node.js memory limit
export NODE_OPTIONS=--max-old-space-size=4096

# Use streaming for large files
# Configure binary data handling via external storage
```

## Monitoring

### OpenTelemetry

n8n emits OpenTelemetry traces for workflow executions:

```bash
export N8N_OTEL_ENABLED=true
export N8N_OTEL_COLLECTOR_ENDPOINT=http://otel-collector:4318
```

Compatible backends: Jaeger, Datadog, Grafana Tempo, Honeycomb, New Relic, Splunk.

### Prometheus Metrics

```bash
export N8N_METRICS=true
export N8N_METRICS_PREFIX=n8n_
# Metrics available at /metrics endpoint
```

### Grafana Dashboard

n8n provides a ready-made Grafana dashboard for monitoring:

- Workflow execution counts and durations
- Error rates by workflow
- Queue depth (queue mode)
- Node execution performance
- Memory and CPU usage

### Health Check

```bash
# Health endpoint
curl http://localhost:5678/healthz
# Returns 200 OK when n8n is running
```

## Updates and Maintenance

### Docker Updates

```bash
docker pull docker.n8n.io/n8nio/n8n:latest
docker stop n8n
docker rm n8n
docker run -d --name n8n ... docker.n8n.io/n8nio/n8n:latest
```

### npm Updates

```bash
npm update -g n8n
```

### Database Migrations

n8n handles database migrations automatically on startup. Always backup before updating:

```bash
# PostgreSQL backup
pg_dump -U n8n n8n > n8n_backup_$(date +%Y%m%d).sql
```

## Common Pitfalls

- **SQLite in production** — doesn't support queue mode or concurrent access; migrate to PostgreSQL
- **Missing encryption key** — always set and back up `N8N_ENCRYPTION_KEY`; losing it means losing all credentials
- **Webhook URL mismatch** — `WEBHOOK_URL` must match the public URL where n8n is accessible
- **Queue mode without Redis** — queue mode requires a Redis instance; it won't fall back to direct execution
- **Memory exhaustion** — large binary files or many concurrent executions can exhaust Node.js memory
- **Execution data growth** — without pruning, execution data can fill the database; configure retention policies

## Related Topics

- Credentials and Security → `07-credentials-and-security.md`
- Workflow Management → `11-workflow-management.md`
- Integrations → `12-integrations-ecosystem.md`
