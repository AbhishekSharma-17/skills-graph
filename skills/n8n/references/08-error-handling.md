# Error Handling

> Source: https://docs.n8n.io/build/flow-logic/handle-errors-gracefully/

## Table of Contents

- [Error Handling Overview](#error-handling-overview)
- [Error Workflows](#error-workflows)
- [Error Trigger Node](#error-trigger-node)
- [Stop and Error Node](#stop-and-error-node)
- [Node-Level Error Settings](#node-level-error-settings)
- [Debugging Executions](#debugging-executions)
- [Error Data Structure](#error-data-structure)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## Error Handling Overview

n8n provides multiple mechanisms for handling errors:

| Mechanism | Scope | Purpose |
|-----------|-------|---------|
| **Error Workflow** | Per-workflow | Run a separate workflow when execution fails |
| **Error Trigger** | Workflow-level | Start node in the error-handling workflow |
| **Stop and Error** | Node-level | Force execution to fail with a custom message |
| **Continue on Fail** | Node-level | Skip failed nodes and continue |
| **Retry on Fail** | Node-level | Automatically retry failed nodes |
| **Error Output** | Node-level | Branch on error instead of failing |

## Error Workflows

An error workflow runs automatically when another workflow fails. Use it for alerting, logging, and recovery.

### Setting Up an Error Workflow

1. **Create the error-handling workflow:**
   - Add an **Error Trigger** node as the start
   - Add notification nodes (Slack, Email, etc.)
   - Save and **publish** the workflow

2. **Assign it to a workflow:**
   - Open the target workflow's **Settings** (gear icon)
   - Set **Error workflow** to your error-handling workflow
   - Save

### One Error Workflow, Many Sources

The same error workflow can serve multiple workflows. The Error Trigger node receives metadata about which workflow failed.

### Example Error Notification Workflow

```
Error Trigger
  → Edit Fields (format error message)
  → Slack (post to #alerts channel)
  → Gmail (send to ops team)
```

## Error Trigger Node

The Error Trigger node is a specialized trigger that fires when a connected workflow fails.

### Error Data Received

When a workflow fails, the Error Trigger receives:

```json
{
  "execution": {
    "id": "12345",
    "url": "https://n8n.example.com/execution/12345",
    "retryOf": null,
    "error": {
      "message": "HTTP Request failed: 500 Internal Server Error",
      "stack": "Error: Request failed...",
      "name": "NodeApiError"
    },
    "lastNodeExecuted": "HTTP Request",
    "mode": "trigger"
  },
  "workflow": {
    "id": "100",
    "name": "Daily Data Sync"
  }
}
```

### Trigger Node Failure

When the trigger node itself fails (not a downstream node), the error data structure differs:

```json
{
  "trigger": {
    "error": {
      "message": "Could not connect to webhook",
      "name": "NodeOperationError"
    },
    "mode": "trigger"
  },
  "workflow": {
    "id": "100",
    "name": "Webhook Handler"
  }
}
```

## Stop and Error Node

Force a workflow to fail intentionally under specific conditions.

### Configuration

```
Error Type: Error Message | Error Object

Error Message: "Order validation failed: missing required field 'email'"

Error Object: {{ JSON.stringify({ code: 'VALIDATION_ERROR', field: 'email' }) }}
```

### Use Cases

```
If (order.total < 0)
  → True: Stop and Error ("Invalid order: negative total")
  → False: Continue processing

If (API response status !== 200)
  → True: Stop and Error with response details
  → False: Process response data
```

## Node-Level Error Settings

### Continue on Fail

When enabled, a failing node doesn't stop the workflow. The node outputs its error as data instead.

```
Node Settings → Continue on Fail: ON

Output when node fails:
{
  "json": {
    "error": {
      "message": "Request failed with status 404",
      "name": "NodeApiError"
    }
  }
}
```

Access error info in the next node:

```javascript
{{ $json.error.message }}
```

### Retry on Fail

Automatically retry a failed node:

```
Node Settings → Retry on Fail: ON
  Max Retries: 3
  Wait Between Retries: 1000ms
  → Retries up to 3 times with 1 second between attempts
```

### Error Output Branch

Some nodes support an **Error** output alongside their regular output:

```
HTTP Request
  ├── Success output → Process data
  └── Error output   → Handle failure

→ The error output receives items that failed
→ The success output receives items that succeeded
→ Workflow continues on both paths
```

## Debugging Executions

### Execution History

View past executions to diagnose failures:

1. Click **Executions** in the sidebar (all workflows) or on a specific workflow
2. Filter by status: Success, Error, Waiting
3. Click an execution to see:
   - Data at each node (input and output)
   - Error messages and stack traces
   - Execution timing

### Loading Failed Executions

Click on a failed execution to:

- View the exact data that caused the failure
- See which node failed and why
- Retry the execution from the failed node
- Copy the execution data for debugging

### Custom Execution Data

Add metadata to executions for easier filtering:

```javascript
// In a Code node
$execution.customData.set('orderId', $json.orderId);
$execution.customData.set('customer', $json.customerName);
$execution.customData.set('region', $json.region);

// These appear in the execution list for filtering
```

### Log Streaming

Send execution logs to external systems:

```
Settings → Log Streaming
  → Connect to Sentry, Datadog, Splunk, etc.
  → Stream execution events in real-time
  → Filter by workflow, status, or node
```

## Error Data Structure

### Standard Error

```json
{
  "message": "Human-readable error description",
  "name": "NodeApiError",
  "description": "Additional context",
  "httpCode": "404",
  "stack": "Error: ...\n    at ..."
}
```

### Node-Specific Error Types

| Error Type | Cause |
|-----------|-------|
| `NodeApiError` | External API returned an error |
| `NodeOperationError` | Internal node operation failed |
| `NodeConnectionError` | Cannot connect to external service |
| `ExpressionError` | Expression evaluation failed |
| `WorkflowOperationError` | Workflow-level execution error |

## Common Patterns

### Alert on Any Failure

```
Error Trigger
  → Edit Fields:
      Workflow: {{ $json.workflow.name }}
      Error: {{ $json.execution.error.message }}
      Node: {{ $json.execution.lastNodeExecuted }}
      URL: {{ $json.execution.url }}
  → Slack (#ops-alerts):
      ":red_circle: Workflow '{{ $json.workflow }}' failed at '{{ $json.node }}'"
```

### Retry with Exponential Backoff

```
HTTP Request (continue on fail)
  → If ($json.error exists)
    → True:
      → Code (calculate wait: Math.pow(2, $runIndex) * 1000)
      → If ($runIndex < 5)
        → True: Wait (calculated time) → Loop back to HTTP Request
        → False: Stop and Error ("Max retries exceeded")
    → False: Continue processing
```

### Graceful Degradation

```
Primary API (continue on fail)
  → If ($json.error exists)
    → True: Fallback API → Process
    → False: Process
```

### Error Recovery with Retry

```
Failed execution:
  → View in Execution History
  → Click "Retry" on the failed node
  → Execution resumes from the failed point
  → Previous successful nodes are not re-run
```

### Validation Before Processing

```
Webhook (receives order)
  → If (required fields present)
    → True: Process order
    → False: Respond to Webhook (400 Bad Request, "Missing fields")
```

## Common Pitfalls

- **Error workflow not published** — the error-handling workflow must be published to receive error events
- **Error workflow errors** — if the error workflow itself fails, there's no cascade; the error is logged but not re-handled
- **Continue on Fail + downstream expectations** — downstream nodes must handle the error data shape (`$json.error`) alongside the normal shape
- **Retry loops** — unlimited retries can cause infinite loops; always set a maximum retry count
- **Execution data retention** — execution data is pruned based on settings; configure retention before relying on history for debugging
- **Expression errors** — referencing a non-existent field in an expression fails silently (returns undefined); use optional chaining or null coalescing

## Related Topics

- Flow Logic → `04-flow-logic.md`
- Workflow Fundamentals → `01-workflow-fundamentals.md`
- Deployment → `10-deployment-and-scaling.md`
