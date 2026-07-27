# Workflow Management

> Source: https://docs.n8n.io/build/manage-workflows/

## Table of Contents

- [Workflow Settings](#workflow-settings)
- [Tags and Organization](#tags-and-organization)
- [Change History](#change-history)
- [Import and Export](#import-and-export)
- [Sharing and Collaboration](#sharing-and-collaboration)
- [Variables and Environment](#variables-and-environment)
- [MCP Server Integration](#mcp-server-integration)
- [Source Control](#source-control)
- [Community Packages](#community-packages)
- [Common Pitfalls](#common-pitfalls)

## Workflow Settings

Access workflow settings via the gear icon in the workflow header.

### Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| **Error Workflow** | Workflow to trigger on failure | None |
| **Timezone** | Override instance timezone | Instance default |
| **Save Execution on Success** | Persist data for successful runs | Instance default |
| **Save Execution on Error** | Persist data for failed runs | Instance default |
| **Save Manual Executions** | Persist data for editor test runs | Instance default |
| **Execution Timeout** | Max runtime (seconds, 0 = no limit) | 0 |
| **Caller Policy** | Who can call this as sub-workflow | Same owner |

### Execution Timeout

```
Timeout: 300 (seconds)
→ Workflow automatically stops after 5 minutes
→ Triggers the error workflow if configured
→ 0 means no timeout (default)
```

### Caller Policy

Controls access to this workflow as a sub-workflow:

| Policy | Description |
|--------|-------------|
| **Workflows from same owner** | Only your own workflows can call it |
| **Any workflow** | Any workflow on the instance |
| **None** | Cannot be called as sub-workflow |

## Tags and Organization

### Tagging Workflows

Apply tags for filtering and grouping:

```
Tags: production, data-sync, hourly
→ Filter the workflow list by tag
→ Multiple tags per workflow
→ Tags are shared across the instance
```

### Folder Organization (Projects)

Enterprise feature for organizing workflows into projects:

```
Projects:
  ├── Marketing/
  │   ├── Email Campaign
  │   └── Social Media Sync
  ├── Engineering/
  │   ├── Deploy Notifications
  │   └── CI Webhook Handler
  └── Operations/
      ├── Daily Report
      └── Inventory Sync
```

## Change History

Track and restore previous versions of workflows.

### Viewing History

```
Workflow → History (clock icon)
→ List of saved versions with timestamps
→ Click a version to preview
→ Restore to revert the workflow
```

### Version Comparison

- See what changed between versions
- Restore a previous version without losing the current one
- History retention based on plan and instance configuration

### History Retention

```bash
# Self-hosted configuration
export WORKFLOW_HISTORY_PRUNE_TIME=336  # Hours (14 days)
```

## Import and Export

### Export Workflows

```bash
# CLI export (all workflows)
n8n export:workflow --all --output=workflows.json

# CLI export (specific workflow)
n8n export:workflow --id=123 --output=my_workflow.json

# API export
curl -H "X-N8N-API-KEY: key" \
  https://n8n.example.com/api/v1/workflows/123 \
  -o workflow.json
```

### Import Workflows

```bash
# CLI import
n8n import:workflow --input=workflow.json

# API import
curl -X POST -H "X-N8N-API-KEY: key" \
  -H "Content-Type: application/json" \
  -d @workflow.json \
  https://n8n.example.com/api/v1/workflows
```

### Export Format

Workflows export as JSON with:

- Node configurations and positions
- Connection definitions
- Workflow settings
- Tags
- Credential references (IDs only, not secrets)

### Credential Handling

Exported workflows reference credentials by ID. When importing to a new instance:

1. Import the workflow
2. Open each node with credentials
3. Select or create matching credentials on the new instance

## Sharing and Collaboration

### Sharing Workflows

```
Workflow → Share (people icon)
→ Add team members by email
→ Set permission level: Editor | Viewer
→ Shared workflows appear in recipients' list
```

### Permission Levels

| Level | Can View | Can Edit | Can Execute | Can Delete |
|-------|----------|----------|-------------|------------|
| **Viewer** | Yes | No | No | No |
| **Editor** | Yes | Yes | Yes | No |
| **Owner** | Yes | Yes | Yes | Yes |

### Templates

Share workflows publicly or within your team:

```
Workflow → Share → Copy Link
→ Share the link for import
→ Recipients get a copy (not a live link)
```

## Variables and Environment

### Instance Variables

Define reusable values accessible across all workflows:

```
Settings → Variables
  API_BASE_URL = https://api.production.com
  SLACK_CHANNEL = #engineering
  MAX_RETRIES = 3
```

Access in workflows:

```javascript
{{ $vars.API_BASE_URL }}
{{ $vars.SLACK_CHANNEL }}
{{ parseInt($vars.MAX_RETRIES) }}
```

### Environment Variables

Access system environment variables (if allowed by configuration):

```javascript
{{ $env.MY_SECRET }}

// Requires:
// N8N_ALLOW_ENV_IN_NODE=true
// or specific variables allowlisted
```

### Custom Data in Executions

```javascript
// Set custom metadata in Code node
$execution.customData.set('batchId', '2026-07-27-001');
$execution.customData.set('recordCount', items.length.toString());

// Retrieve in downstream nodes
$execution.customData.get('batchId')
```

## MCP Server Integration

n8n provides a built-in MCP (Model Context Protocol) server for AI tool integration.

### Instance-Level MCP

Connect AI assistants (Claude Desktop, custom agents) to manage n8n programmatically:

```
Capabilities:
  - Create and edit workflows from descriptions
  - Search and execute existing workflows
  - Manage data tables
  - Test and debug workflows
```

### MCP Server Trigger Node

Expose a single workflow as an MCP server:

```
MCP Server Trigger
  → Define available tools
  → AI clients connect and call tools
  → Workflow processes tool calls
```

### MCP Client Tool Node

Use n8n as an MCP client to call external MCP servers:

```
Agent
  └── MCP Client Tool
       Server URL: http://localhost:3000/mcp
       → Agent can call tools from external MCP servers
```

### Setup

```
Instance Settings → MCP
  → Enable MCP access
  → Configure authentication (OAuth2 or access tokens)
  → Expose specific workflows as tools
```

## Source Control

Sync workflows with a Git repository for version control and CI/CD.

### Git Integration

```
Settings → Source Control
  → Repository URL: git@github.com:org/n8n-workflows.git
  → Branch: main
  → SSH Key: (generate or paste)
```

### Push and Pull

```
Push: Send local workflow changes to the Git repository
Pull: Apply changes from the repository to the local instance
```

### Multi-Environment Setup

```
Development instance → Push to Git (dev branch)
  → PR review → Merge to main
  → Production instance → Pull from Git (main branch)
```

### Environment Variables Per Instance

```bash
# Development
export WEBHOOK_URL=https://n8n-dev.example.com/
export API_URL=https://api-staging.example.com

# Production
export WEBHOOK_URL=https://n8n.example.com/
export API_URL=https://api.example.com
```

## Community Packages

### Installing Community Packages

Community-built nodes extend n8n's capabilities:

```
Settings → Community Packages
  → Enter npm package name
  → Click Install
  → New nodes appear in the node palette
```

### API-Based Management

```bash
# List installed packages
curl -H "X-N8N-API-KEY: key" \
  https://n8n.example.com/api/v1/community-packages

# Install a package
curl -X POST -H "X-N8N-API-KEY: key" \
  -H "Content-Type: application/json" \
  -d '{"name": "n8n-nodes-custom-package"}' \
  https://n8n.example.com/api/v1/community-packages
```

### Creating Custom Nodes

Build your own n8n nodes using the n8n node starter:

```bash
npx n8n-node-dev new
# Follow prompts to scaffold a custom node project
# Publish to npm for community use
```

## Common Pitfalls

- **Variables vs environment variables** — `$vars` are set in the n8n UI; `$env` reads OS environment variables (requires explicit enablement)
- **Credential IDs in exports** — exported workflows reference credential IDs that may not exist on the import target
- **Source control conflicts** — simultaneous edits on multiple instances can cause Git conflicts; use a push/pull discipline
- **Community package compatibility** — community packages may not support the latest n8n version; check compatibility
- **MCP authentication** — MCP endpoints must be properly secured; don't expose without authentication

## Related Topics

- Workflow Fundamentals → `01-workflow-fundamentals.md`
- Credentials → `07-credentials-and-security.md`
- Deployment → `10-deployment-and-scaling.md`
