# Triggers and Webhooks

> Source: https://docs.n8n.io/integrations/builtin/core-nodes/

## Table of Contents

- [Trigger Types](#trigger-types)
- [Schedule Trigger](#schedule-trigger)
- [Webhook Trigger](#webhook-trigger)
- [App Triggers](#app-triggers)
- [Manual and Other Triggers](#manual-and-other-triggers)
- [Webhook Configuration](#webhook-configuration)
- [Webhook Authentication](#webhook-authentication)
- [Webhook Response Modes](#webhook-response-modes)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## Trigger Types

Every workflow starts with a trigger node. n8n provides several trigger categories:

| Category | Examples | Use Case |
|----------|----------|----------|
| **Schedule** | Schedule Trigger | Time-based automation (cron) |
| **Webhook** | Webhook node | HTTP endpoint for external calls |
| **App Triggers** | Gmail Trigger, Slack Trigger | React to events in SaaS apps |
| **Polling** | Google Drive Trigger | Check for changes at intervals |
| **Manual** | Manual Trigger | Editor-only execution |
| **System** | Error Trigger, n8n Trigger | Internal n8n events |
| **AI** | Chat Trigger | Conversational AI interfaces |

## Schedule Trigger

Run workflows on a recurring schedule using cron-like configuration.

### Configuration Options

| Field | Options |
|-------|---------|
| **Trigger Interval** | Seconds, Minutes, Hours, Days, Weeks, Months, Custom (Cron) |
| **Day of Week** | Monday through Sunday (for weekly) |
| **Hour** | 0–23 |
| **Minute** | 0–59 |

### Examples

```
Every 5 minutes:
  Trigger Interval: Minutes
  Every: 5

Every Monday at 9:00 AM:
  Trigger Interval: Weeks
  Day: Monday
  Hour: 9
  Minute: 0

Custom cron (weekdays at 8:30 AM):
  Trigger Interval: Custom (Cron)
  Expression: 30 8 * * 1-5
```

### Cron Expression Format

```
┌───────────── minute (0–59)
│ ┌───────────── hour (0–23)
│ │ ┌───────────── day of month (1–31)
│ │ │ ┌───────────── month (1–12)
│ │ │ │ ┌───────────── day of week (0–7, 0 and 7 = Sunday)
│ │ │ │ │
* * * * *
```

### Schedule Trigger Output

The Schedule Trigger emits a single item with timestamp data:

```json
[
  {
    "json": {
      "timestamp": "2026-07-27T09:00:00.000Z",
      "Readable date": "July 27, 2026 at 9:00 AM",
      "Readable time": "9:00:00 AM",
      "Day of week": "Monday"
    }
  }
]
```

## Webhook Trigger

Create HTTP endpoints that trigger workflows when called externally.

### Dual URL System

n8n generates two URLs for each webhook:

| URL Type | When Active | Use Case |
|----------|-------------|----------|
| **Test URL** | While editor is open and listening | Development and debugging |
| **Production URL** | When workflow is published | Live integrations |

### URL Format

```
Test:       https://your-n8n.com/webhook-test/<path>
Production: https://your-n8n.com/webhook/<path>
```

The `<path>` is auto-generated but can be customized. It supports parameterized paths:

```
/order/:orderId
/api/:version/users/:userId
/hooks/github
```

### Webhook Configuration

```
HTTP Method: GET, POST, PUT, PATCH, DELETE, HEAD
Path: /my-webhook-path
Authentication: None, Basic Auth, Header Auth, JWT Auth
Response Mode: Immediately | When Last Node Finishes | Using Respond to Webhook
```

## App Triggers

App triggers poll or listen for events in specific SaaS applications.

### Polling Triggers

Check for new data at regular intervals:

```
Google Drive Trigger → New file added to folder
Google Sheets Trigger → Row added or updated
Airtable Trigger → Record created or updated
```

Polling triggers are configurable with a polling interval (default varies by node). Empty polls don't count toward execution quotas.

### Event-Based Triggers

Register webhooks with external services:

```
GitHub Trigger → Push, PR, Issue events
Slack Trigger → New message in channel
Stripe Trigger → Payment, subscription events
```

### Common App Triggers

| App | Trigger Events |
|-----|---------------|
| Gmail | New email received |
| Slack | Message posted, reaction added |
| GitHub | Push, PR opened, issue created |
| Stripe | Payment succeeded, subscription updated |
| Google Sheets | Row added/updated |
| Airtable | Record created/updated |
| Notion | Page updated, database item added |
| Jira | Issue created/updated |

## Manual and Other Triggers

### Manual Trigger

For workflows that only run on demand from the editor:

```
Manual Trigger → (only fires when you click Execute Workflow)
```

### Form Trigger

Create web forms that trigger workflows:

```
Form Trigger → Generates a hosted form URL
  → Collects user input fields
  → Triggers workflow on submission
  → Supports text, number, email, date, dropdown fields
```

### Chat Trigger

For AI chatbot workflows:

```
Chat Trigger → Opens a chat interface
  → Receives user messages
  → Routes to AI agent/chain nodes
  → Returns responses in the chat
```

### Error Trigger

Runs when another workflow fails:

```
Error Trigger → Receives error data from failed workflows
  → Use for alerting (email, Slack)
  → Access execution ID, error message, failed node info
```

### Other Triggers

| Trigger | Purpose |
|---------|---------|
| **SSE Trigger** | Server-Sent Events listener |
| **RSS Feed Trigger** | New items in RSS feeds |
| **Local File Trigger** | File system changes |
| **IMAP Email Trigger** | New emails via IMAP |
| **n8n Trigger** | Instance events (workflow activated, user updated) |

## Webhook Authentication

### Basic Auth

```
Authentication: Basic Auth
→ Configure username and password
→ Requests must include Authorization: Basic <base64> header
```

### Header Auth

```
Authentication: Header Auth
→ Configure header name (e.g., X-API-Key)
→ Configure expected value
→ Requests must include matching header
```

### JWT Auth

```
Authentication: JWT Auth
→ Configure JWT secret or JWKS endpoint
→ Requests must include valid JWT in Authorization header
→ Decoded JWT payload available in workflow data
```

### IP Whitelist

Restrict webhook access to specific IP addresses for additional security.

## Webhook Response Modes

### Immediately

Returns a default response right away:

```json
{ "message": "Workflow got started" }
```

The workflow continues executing in the background. Use when callers don't need the workflow's output.

### When Last Node Finishes

Waits for the entire workflow to complete, then returns the last node's output as the response body. The caller blocks until completion.

### Using Respond to Webhook Node

Full control over the HTTP response:

```
Webhook node → Process data → Respond to Webhook node
                                ├── Status Code: 200
                                ├── Headers: Content-Type: application/json
                                └── Body: {{ $json }}
```

### Streaming Response

For AI workflows, stream the response as it's generated:

```
Webhook → AI Agent → (streaming enabled)
  → Response streams back chunk by chunk
  → Requires compatible downstream nodes
```

## Common Patterns

### API Endpoint Pattern

```
Webhook (POST /api/orders)
  → Validate input (If node)
  → Process order (Code node)
  → Save to database (PostgreSQL node)
  → Respond to Webhook (200 OK with order data)
```

### Scheduled Data Sync

```
Schedule Trigger (every hour)
  → HTTP Request (fetch from source API)
  → Transform data (Code node)
  → Upsert to destination (Google Sheets / DB)
```

### GitHub Webhook Handler

```
Webhook (POST /hooks/github)
  → Switch (event type: push, pr, issue)
  → Branch 1: Notify Slack about pushes
  → Branch 2: Create Jira ticket for new issues
  → Branch 3: Update dashboard for PRs
```

## Common Pitfalls

- **Test URLs require the editor to be open** — if you close the browser tab, the test webhook stops listening
- **Production URLs require publishing** — the workflow must be published (active) for production webhooks to work
- **Webhook path conflicts** — two active workflows cannot share the same webhook path; use unique paths
- **Payload size limit** — default maximum is 16 MB; configure with `N8N_PAYLOAD_SIZE_MAX`
- **Polling frequency vs quotas** — frequent polling intervals consume more execution quota on cloud plans
- **Webhook URL changes** — if you change the base URL or move instances, all webhook URLs change

## Related Topics

- Workflow Fundamentals → `01-workflow-fundamentals.md`
- HTTP Request and APIs → `06-http-request-and-apis.md`
- Error Handling → `08-error-handling.md`
