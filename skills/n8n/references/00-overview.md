# n8n Overview

> Source: https://docs.n8n.io | https://github.com/n8n-io/n8n

## What is n8n?

n8n (pronounced "nodemation") is a fair-code workflow automation platform that combines a visual canvas with custom code capabilities. It enables building and deploying AI agents and multi-step automations with 1500+ integrations, self-hosting or cloud options, and enterprise-grade security.

## When to Use n8n

- **API orchestration** — connect multiple APIs in a visual pipeline without boilerplate
- **AI agent workflows** — build agents with tool calling, memory, and vector stores using a visual builder
- **Webhook-driven automation** — create HTTP endpoints that trigger complex multi-step workflows
- **Data synchronization** — move and transform data between SaaS applications on schedule or in real-time
- **Internal tooling** — build forms, dashboards, and approval flows without a full application
- **DevOps automation** — CI/CD notifications, deployment pipelines, incident response
- **Content pipelines** — social media scheduling, email campaigns, document generation

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│  n8n Editor (Browser UI)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Trigger  │──│ Process  │──│ Output   │      │
│  │ Node     │  │ Nodes    │  │ Nodes    │      │
│  └──────────┘  └──────────┘  └──────────┘      │
├─────────────────────────────────────────────────┤
│  n8n Server (Node.js)                           │
│  ├── Workflow Engine (execution, scheduling)    │
│  ├── Credential Store (encrypted, per-user)     │
│  ├── REST API (/api/v1/*)                       │
│  ├── Webhook Server (test + production URLs)    │
│  └── Task Runners (Code node sandboxing)        │
├─────────────────────────────────────────────────┤
│  Database (SQLite default | PostgreSQL)         │
│  ├── Workflows, Executions, Credentials         │
│  └── Tags, Settings, Variables                  │
└─────────────────────────────────────────────────┘
```

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Workflow** | A collection of nodes connected together to automate a process |
| **Node** | A single integration or operation (trigger, action, or logic) |
| **Connection** | A link between nodes that defines data flow direction |
| **Trigger** | A special node type that starts workflow execution |
| **Execution** | A single run of a workflow (manual or production) |
| **Credential** | Stored authentication data for connecting to external services |
| **Expression** | Dynamic value using `{{ }}` syntax, evaluated at runtime |
| **Item** | A single data object flowing through the workflow |
| **Sub-workflow** | A workflow called from another workflow for modularity |

## Node Types

n8n has four categories of nodes:

1. **Trigger Nodes** — start workflow execution (Schedule, Webhook, App triggers, Polling)
2. **Core Nodes** — built-in utilities (Code, HTTP Request, If, Switch, Merge, Set, Filter)
3. **App Nodes** — integrations with specific services (Gmail, Slack, GitHub, Stripe, etc.)
4. **AI Nodes** — LLM, agent, tool, memory, and vector store nodes for AI workflows

## Installation

### Quick Start with npx

```bash
npx n8n
# Opens editor at http://localhost:5678
```

### Docker (Recommended for Production)

```bash
docker volume create n8n_data
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  docker.n8n.io/n8nio/n8n
```

### Docker Compose

```yaml
version: "3.8"
services:
  n8n:
    image: docker.n8n.io/n8nio/n8n
    restart: always
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=localhost
      - N8N_PORT=5678
      - N8N_PROTOCOL=https
      - WEBHOOK_URL=https://n8n.example.com/
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_DATABASE=n8n
      - DB_POSTGRESDB_USER=n8n
      - DB_POSTGRESDB_PASSWORD=changeme
    volumes:
      - n8n_data:/home/node/.n8n
    depends_on:
      - postgres

  postgres:
    image: postgres:16
    restart: always
    environment:
      - POSTGRES_USER=n8n
      - POSTGRES_PASSWORD=changeme
      - POSTGRES_DB=n8n
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  n8n_data:
  postgres_data:
```

### npm Global Install

```bash
npm install n8n -g
n8n start
# Or with tunnel for webhook testing:
n8n start --tunnel
```

### n8n Cloud

Sign up at [app.n8n.cloud](https://app.n8n.cloud) for a managed instance with automatic updates, backups, and no infrastructure management.

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Node.js | 18.17+ | 20 LTS |
| RAM | 256 MB | 2 GB+ |
| Database | SQLite (built-in) | PostgreSQL 14+ |
| OS | Linux, macOS, Windows | Linux (Docker) |

## Database Options

- **SQLite** (default) — zero-config, suitable for development and small deployments
- **PostgreSQL** — recommended for production, supports concurrent access and queue mode

```bash
# PostgreSQL configuration via environment variables
export DB_TYPE=postgresdb
export DB_POSTGRESDB_HOST=localhost
export DB_POSTGRESDB_PORT=5432
export DB_POSTGRESDB_DATABASE=n8n
export DB_POSTGRESDB_USER=n8n
export DB_POSTGRESDB_PASSWORD=your_password
```

## Licensing

n8n uses a **fair-code** model:

- **Sustainable Use License** — source-available, free for most use cases
- **n8n Enterprise License** — additional features for larger organizations
- Self-hosting is always available; cloud is an optional managed offering

## First Workflow Walkthrough

1. Open the editor at `http://localhost:5678`
2. Click **Create Workflow** or **Start from Scratch**
3. Add a **Schedule Trigger** node (e.g., run every Monday at 9 AM)
4. Connect an **HTTP Request** node to fetch data from an API
5. Add an **If** node for conditional logic
6. Connect output nodes (e.g., Slack, Email, Google Sheets)
7. Click **Execute Workflow** to test
8. Click **Save** then **Publish** to activate for production

## Environment Variables

Key configuration via environment variables:

```bash
N8N_HOST=0.0.0.0              # Listen address
N8N_PORT=5678                  # Server port
N8N_PROTOCOL=https             # http or https
WEBHOOK_URL=https://n8n.example.com/  # Public webhook URL
N8N_ENCRYPTION_KEY=your-key    # Credential encryption key
N8N_PAYLOAD_SIZE_MAX=16        # Max webhook payload (MB)
EXECUTIONS_DATA_SAVE_ON_ERROR=all
EXECUTIONS_DATA_SAVE_ON_SUCCESS=none
N8N_LOG_LEVEL=info             # error, warn, info, debug, verbose
```

## Common Pitfalls

- **Webhook URLs differ between test and production** — test URLs only work while the editor is open; production URLs require the workflow to be published
- **Forgetting to publish** — workflows only run automatically after clicking Publish
- **SQLite limitations** — not suitable for high-concurrency or queue mode; use PostgreSQL
- **Credential encryption** — always set `N8N_ENCRYPTION_KEY` in production; losing it means losing all stored credentials
- **Expression context** — expressions can only reference data from nodes that have already executed in the current run

## Related Topics

- Workflow Fundamentals → `01-workflow-fundamentals.md`
- Triggers and Webhooks → `02-triggers-and-webhooks.md`
- Deployment and Scaling → `10-deployment-and-scaling.md`
