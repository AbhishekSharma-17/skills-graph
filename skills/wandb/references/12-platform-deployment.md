# Platform & Deployment

> Source: [docs.wandb.ai/platform](https://docs.wandb.ai/platform/) | wandb 0.27.1

## Table of Contents

- [Deployment Options](#deployment-options)
- [Multi-Tenant Cloud](#multi-tenant-cloud)
- [Dedicated Cloud](#dedicated-cloud)
- [Self-Managed Server](#self-managed-server)
- [Teams and Organizations](#teams-and-organizations)
- [Access Control](#access-control)
- [Security](#security)
- [CLI Reference](#cli-reference)
- [MCP Server](#mcp-server)
- [Environment Setup](#environment-setup)
- [Common Pitfalls](#common-pitfalls)

## Deployment Options

| Option | Description | Best For |
|--------|-------------|----------|
| **Multi-Tenant Cloud** | Hosted at wandb.ai, shared infrastructure | Individual developers, small teams |
| **Dedicated Cloud** | Isolated instance managed by W&B | Enterprise with compliance needs |
| **Self-Managed** | Run W&B Server on your own infrastructure | Air-gapped environments, full control |

## Multi-Tenant Cloud

Default option — sign up at wandb.ai and start logging.

- Shared infrastructure, managed by W&B
- Free tier: unlimited public projects, limited private storage
- Teams plan: private projects, collaboration features
- Enterprise plan: SSO, audit logs, advanced permissions

## Dedicated Cloud

Isolated W&B instance in your cloud provider (AWS, GCP, Azure):

- Dedicated compute and storage
- Data residency compliance
- Network isolation (VPC peering, private endpoints)
- Managed by W&B team

## Self-Managed Server

Run W&B Server on your own infrastructure:

```bash
# Docker Compose (development/testing)
docker compose up -d

# Kubernetes (production)
helm repo add wandb https://charts.wandb.ai
helm install wandb wandb/wandb \
    --set license=YOUR_LICENSE_KEY \
    --set bucket=s3://your-bucket \
    --set mysql.host=your-db-host
```

Requirements:
- MySQL 8.0+
- Object storage (S3, GCS, Azure Blob, MinIO)
- Redis (optional, for caching)
- 4 CPU cores, 16 GB RAM minimum

### Server Versions

Self-managed deployments track W&B Server releases (e.g., v0.71.0+). Registry features require Server v0.71.0 or later.

## Teams and Organizations

### Organization Structure

```
Organization (billing entity)
├── Team A
│   ├── Members (users)
│   └── Projects
│       ├── Project 1
│       └── Project 2
├── Team B
│   └── ...
└── Registry (org-wide)
```

### Creating Teams

Teams are created in Organization Settings. Each team has its own projects, members, and service accounts.

### Project Visibility

| Level | Who Can View |
|-------|-------------|
| **Private** | Team members only |
| **Public** | Anyone with the URL |

## Access Control

### Organization Roles

| Role | Permissions |
|------|-------------|
| **Admin** | Full control: billing, teams, settings |
| **Member** | Create projects, join teams |
| **Viewer** | Read-only access to shared projects |

### Team Roles

| Role | Permissions |
|------|-------------|
| **Admin** | Manage team members, settings, service accounts |
| **Member** | Create runs, log artifacts, create reports |
| **Viewer** | Read-only access to team projects |

### Service Accounts

For CI/CD and automated systems:

1. Team Settings → Service Accounts → Create
2. Copy the API key (shown once)
3. Use as `WANDB_API_KEY` in automation

## Security

### Data Encryption

- **In transit**: TLS 1.2+ for all API communications
- **At rest**: AES-256 encryption for stored data
- **Bring Your Own Bucket (BYOB)**: Store artifacts in your own S3/GCS bucket

### Authentication

| Method | Availability |
|--------|-------------|
| Email/password | All plans |
| SSO (SAML/OIDC) | Enterprise |
| API keys | All plans |
| Service accounts | Teams plan+ |

### IP Allowlisting

Restrict API access to specific IP ranges (Dedicated Cloud and Self-Managed).

### Audit Logs

Enterprise plans include audit logs for:
- User authentication events
- Project and artifact access
- Configuration changes
- API key creation/deletion

## CLI Reference

### Authentication

```bash
wandb login                    # Interactive login
wandb login --host=https://your-instance.wandb.ai  # Self-hosted
wandb logout                   # Remove stored credentials
```

### Projects and Runs

```bash
wandb init                     # Initialize project in current directory
wandb status                   # Show current run status
wandb sync ./wandb/offline-*   # Sync offline runs
wandb sync --clean             # Sync and remove local data
```

### Artifacts

```bash
wandb artifact put ./data/ --name my-dataset --type dataset
wandb artifact get entity/project/my-dataset:latest
wandb artifact ls entity/project --type model
```

### Sweeps

```bash
wandb sweep sweep.yaml                      # Create sweep
wandb agent entity/project/sweep_id         # Start agent
wandb sweep --stop entity/project/sweep_id  # Stop sweep
wandb sweep --cancel entity/project/sweep_id # Cancel sweep
```

### Server (Self-Managed)

```bash
wandb server start      # Start local server
wandb server stop       # Stop local server
wandb server status     # Check server status
```

## MCP Server

W&B provides an MCP (Model Context Protocol) server for AI assistant integration:

```json
{
  "mcpServers": {
    "wandb": {
      "command": "npx",
      "args": ["-y", "@wandb/mcp-server"],
      "env": {
        "WANDB_API_KEY": "your-api-key"
      }
    }
  }
}
```

The MCP server enables AI assistants to query runs, compare experiments, and access artifacts programmatically.

## Environment Setup

### CI/CD Configuration

```yaml
# GitHub Actions example
- name: Train model
  env:
    WANDB_API_KEY: ${{ secrets.WANDB_API_KEY }}
    WANDB_PROJECT: my-project
    WANDB_ENTITY: my-team
  run: python train.py
```

### Docker

```dockerfile
FROM python:3.12-slim
RUN pip install wandb
ENV WANDB_API_KEY=${WANDB_API_KEY}
ENV WANDB_MODE=online
```

### Jupyter Notebooks

```python
import wandb
wandb.login()  # Prompts for API key in notebook

with wandb.init(project="notebook-experiment") as run:
    # Your experiment code
    pass
```

## Common Pitfalls

1. **Service account key rotation** — rotate keys regularly; old keys stop working immediately.
2. **Offline sync order** — sync runs in chronological order to avoid artifact dependency issues.
3. **Team vs personal entity** — runs logged to personal entity can't be moved to a team later.
4. **Self-managed upgrades** — always check release notes for breaking changes before upgrading.
5. **BYOB bucket permissions** — ensure W&B service has read/write access to your storage bucket.

## Related

- Reports & Automations → `references/08-reports-automations.md`
- Registry → `references/06-registry.md`
- Overview → `references/00-overview.md`
