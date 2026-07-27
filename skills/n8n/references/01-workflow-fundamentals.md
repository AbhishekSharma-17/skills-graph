# Workflow Fundamentals

> Source: https://docs.n8n.io/build/understand-workflows/

## Table of Contents

- [Workflow Components](#workflow-components)
- [Nodes](#nodes)
- [Connections](#connections)
- [Canvas Organization](#canvas-organization)
- [Creating Workflows](#creating-workflows)
- [Executing Workflows](#executing-workflows)
- [Publishing Workflows](#publishing-workflows)
- [Execution Types](#execution-types)
- [Debugging Executions](#debugging-executions)
- [Workflow Settings](#workflow-settings)

## Workflow Components

A workflow is a collection of nodes connected together to automate a process. Every workflow has four component types:

1. **Nodes** — integrations and operations that process data
2. **Connections** — links between nodes defining data flow direction
3. **Sticky Notes** — documentation annotations on the canvas
4. **Canvas Groups** — visual containers to organize related nodes

## Nodes

Nodes are the building blocks of every workflow. Each node represents a single operation — fetching data from an API, transforming JSON, sending an email, or evaluating a condition.

### Adding Nodes

```
Click the + button on the canvas
  → Search for a node by name or category
  → Click to add it to the canvas
  → Configure its parameters in the side panel
```

### Node Panel Sections

| Section | Contents |
|---------|----------|
| **Parameters** | Node-specific configuration fields |
| **Input** | Data received from the previous node |
| **Output** | Data produced by this node |
| **Settings** | Retry on fail, continue on fail, notes |

### Node Settings

Every node has a settings tab with:

- **Notes** — add documentation for this specific node
- **Display note in flow** — show the note text on the canvas
- **Always output data** — emit empty items even when the node produces nothing
- **Retry on fail** — automatically retry failed executions (configurable count and wait)
- **Continue on fail** — don't stop the workflow when this node errors
- **Execute once** — run only for the first input item, ignore the rest

## Connections

Connections define how data flows from one node to the next. Drag from the output handle (right side) of one node to the input handle (left side) of another.

### Connection Rules

- A node can have **multiple outputs** (e.g., If node has True and False branches)
- A node can receive connections from **multiple nodes** (data merges)
- Data flows left-to-right through the connection
- Connections carry **arrays of items** between nodes
- Disconnecting a link removes the data flow path

### Multiple Inputs

When a node receives data from multiple connected nodes:

- The node waits for all inputs before executing
- The Merge node provides explicit control over how multiple inputs combine
- Without a Merge node, data from multiple inputs arrives as separate runs

## Canvas Organization

### Sticky Notes

Add annotations directly on the canvas to document workflow sections:

```
Right-click canvas → Add Sticky Note
  → Write documentation, tips, or context
  → Resize and position near relevant nodes
```

### Canvas Groups

Group related nodes visually:

```
Select multiple nodes → Right-click → Create Group
  → Name the group for clarity
  → Moving the group moves all contained nodes
```

## Creating Workflows

### From Scratch

1. Click **Create Workflow** in the overview page
2. The canvas opens with an empty workflow
3. Click **+** to add your first node (usually a trigger)

### From Templates

n8n provides 9,000+ workflow templates:

1. Click **Templates** in the sidebar
2. Search by use case, app, or category
3. Click **Use this workflow** to import
4. Customize credentials and parameters

### Via the API

```bash
curl -X POST https://your-n8n.com/api/v1/workflows \
  -H "X-N8N-API-KEY: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Workflow",
    "nodes": [...],
    "connections": {...},
    "settings": {}
  }'
```

## Executing Workflows

### Manual Execution

Click **Execute Workflow** (or press Ctrl/Cmd + Enter) to run the workflow in the editor. Manual executions:

- Show output data inline on each node
- Don't count toward production execution quotas
- Use test webhook URLs (not production URLs)
- Are useful for debugging and development

### Testing Individual Nodes

Click **Execute Node** on any single node to test it in isolation using data from the previous node's last output.

### Pinning Test Data

Pin data to a node to use fixed test values:

```
Execute a node → Click the pin icon on the output panel
  → The node will use this pinned data in subsequent test runs
  → Unpin to use live data again
```

## Publishing Workflows

Workflows must be **published** (activated) to run automatically in production:

1. Click **Save** to persist the workflow
2. Click the **Publish** toggle (top-right) to activate
3. Published workflows respond to triggers and execute automatically
4. Unpublishing stops automatic execution

### Draft vs Published

| Aspect | Draft | Published |
|--------|-------|-----------|
| Trigger response | Test URLs only | Production URLs |
| Scheduled runs | No | Yes |
| Webhook endpoints | Active while editor open | Always active |
| Execution quota | Not counted | Counted |

## Execution Types

### Manual Executions

Initiated from the editor via Execute Workflow button. Show inline results. Not counted toward quotas.

### Production Executions

Run automatically via triggers. Quota-counted on cloud plans:

- **Schedule triggers** — each firing = one execution
- **Polling triggers** — only executions finding new data count; empty polls are free
- **Webhook triggers** — each inbound request = one execution
- **Sub-workflow calls** — only the parent execution counts

### Executions That Don't Count

- Manual executions from the editor
- Sub-workflow executions (parent counts only)
- Error workflow runs
- Polling triggers that return no new data

## Debugging Executions

### Execution History

View past executions from two locations:

1. **Workflow-level** — click Executions tab on a specific workflow
2. **Global** — click Executions in the main sidebar

Each execution record shows:

- Status (success, error, waiting)
- Start time and duration
- Input/output data for every node
- Error details if failed

### Dirty Nodes

When you modify a node after an execution, it becomes "dirty" (stale). The editor indicates that the cached output data may not reflect the current configuration. Re-execute to get fresh results.

### Custom Execution Data

Attach metadata to executions for filtering and identification:

```javascript
// In a Code node
$execution.customData.set('orderId', '12345');
$execution.customData.set('customer', 'acme-corp');
```

### Streaming Responses

For AI workflows, enable streaming to see responses in real-time as the LLM generates text, rather than waiting for the complete response.

## Workflow Settings

Access via the gear icon in the workflow header:

| Setting | Description |
|---------|-------------|
| **Error workflow** | Workflow to run when this workflow fails |
| **Timezone** | Override the instance timezone for this workflow |
| **Save execution data** | Control which execution data is persisted |
| **Execution timeout** | Maximum runtime before auto-cancellation |
| **Retry on fail** | Default retry behavior for all nodes |
| **Caller policy** | Control which workflows can call this as a sub-workflow |

## Common Pitfalls

- **Not publishing** — workflows don't run automatically until published
- **Test vs production webhook URLs** — they are different; test URLs only work with the editor open
- **Stale node data** — after editing a node, re-execute to see accurate output
- **Losing execution data** — configure save settings before relying on execution history

## Related Topics

- Triggers and Webhooks → `02-triggers-and-webhooks.md`
- Data Structure → `03-data-structure-and-expressions.md`
- Flow Logic → `04-flow-logic.md`
