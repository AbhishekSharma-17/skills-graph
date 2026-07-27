# Integrations Ecosystem

> Source: https://docs.n8n.io/integrations/

## Table of Contents

- [Integration Overview](#integration-overview)
- [Core Nodes](#core-nodes)
- [App Nodes](#app-nodes)
- [AI and LangChain Nodes](#ai-and-langchain-nodes)
- [Trigger Nodes Summary](#trigger-nodes-summary)
- [Popular Integrations](#popular-integrations)
- [Community Nodes](#community-nodes)
- [Building Custom Nodes](#building-custom-nodes)
- [Common Patterns by Category](#common-patterns-by-category)
- [Common Pitfalls](#common-pitfalls)

## Integration Overview

n8n provides 1500+ integrations organized into categories:

| Category | Count | Examples |
|----------|-------|---------|
| **Core Nodes** | ~60 | Code, HTTP Request, Webhook, If, Merge, Filter |
| **App Nodes** | ~500 | Gmail, Slack, GitHub, Stripe, Salesforce |
| **Trigger Nodes** | ~200 | Schedule, Webhook, App-specific triggers |
| **AI Nodes** | ~50 | LLM, Agent, Tools, Memory, Vector Store |
| **Community Nodes** | ~700+ | Custom community-built integrations |

## Core Nodes

Built-in nodes that handle data processing, flow control, and utilities.

### Data Processing

| Node | Purpose |
|------|---------|
| **Code** | Custom JavaScript/Python logic |
| **Edit Fields (Set)** | Add, rename, remove fields |
| **Filter** | Remove items not matching criteria |
| **Sort** | Order items by field values |
| **Limit** | Cap the number of output items |
| **Remove Duplicates** | Deduplicate by field |
| **Aggregate** | Group and summarize items |
| **Summarize** | Compute statistics (sum, avg, min, max) |
| **Split Out** | Split array field into separate items |
| **Rename Keys** | Rename JSON field names |
| **Compare Datasets** | Find differences between two data sets |
| **Compression** | Gzip/zip/unzip data |

### Flow Control

| Node | Purpose |
|------|---------|
| **If** | Binary condition branching |
| **Switch** | Multi-path routing |
| **Merge** | Combine data from multiple inputs |
| **Loop Over Items** | Process items in batches |
| **Wait** | Pause execution (time, webhook, or date) |
| **Execute Workflow** | Call a sub-workflow |
| **Stop and Error** | Force workflow failure |
| **No Op** | Pass-through (useful for routing) |

### Triggers

| Node | Purpose |
|------|---------|
| **Schedule Trigger** | Time-based (cron) |
| **Webhook** | HTTP endpoint |
| **Manual Trigger** | Editor-only execution |
| **Error Trigger** | Failed workflow events |
| **Form Trigger** | Web form submissions |
| **Chat Trigger** | Conversational AI interface |
| **Execute Workflow Trigger** | Sub-workflow entry point |
| **Local File Trigger** | File system changes |
| **SSE Trigger** | Server-Sent Events |
| **RSS Feed Trigger** | New RSS items |

### I/O and Format

| Node | Purpose |
|------|---------|
| **HTTP Request** | REST API calls |
| **Webhook** | Receive HTTP requests |
| **Respond to Webhook** | Custom webhook responses |
| **GraphQL** | GraphQL API queries |
| **FTP** | File transfer protocol |
| **SSH** | Remote command execution |
| **Read/Write File** | Local filesystem operations |
| **Convert to File** | JSON → CSV, HTML, XML, etc. |
| **Extract from File** | CSV, spreadsheet, PDF → JSON |
| **HTML** | Parse and extract HTML content |
| **XML** | Parse and generate XML |
| **Markdown** | Convert between Markdown and HTML |
| **Crypto** | Hash, encrypt, HMAC operations |
| **JWT** | Create and verify JSON Web Tokens |
| **TOTP** | Time-based OTP generation |
| **DateTime** | Date/time formatting and calculation |
| **Send Email** | SMTP email sending |
| **IMAP Email** | Read emails via IMAP |

## App Nodes

Dedicated integrations for specific SaaS applications.

### Productivity & Collaboration

| App | Operations |
|-----|-----------|
| **Google Sheets** | Read/write rows, create sheets |
| **Google Drive** | Upload, download, manage files |
| **Google Calendar** | Create/update events, check availability |
| **Google Docs** | Create and update documents |
| **Notion** | Pages, databases, blocks |
| **Airtable** | Records, tables, views |
| **Slack** | Messages, channels, reactions |
| **Microsoft Teams** | Messages, channels, meetings |
| **Microsoft Excel** | Read/write spreadsheets |
| **Microsoft Outlook** | Email, calendar, contacts |
| **Jira** | Issues, projects, sprints |
| **Linear** | Issues, projects, cycles |
| **Asana** | Tasks, projects, sections |
| **Todoist** | Tasks, projects, labels |
| **Trello** | Cards, boards, lists |

### Developer Tools

| App | Operations |
|-----|-----------|
| **GitHub** | Repos, issues, PRs, actions |
| **GitLab** | Repos, issues, MRs, pipelines |
| **Jenkins** | Build jobs, pipelines |
| **CircleCI** | Pipelines, workflows |
| **Docker** | Containers, images |
| **Sentry** | Issues, events, releases |
| **Grafana** | Dashboards, alerts |
| **Elasticsearch** | Index, search, manage |

### CRM & Marketing

| App | Operations |
|-----|-----------|
| **Salesforce** | Contacts, leads, opportunities |
| **HubSpot** | Contacts, deals, companies |
| **Mailchimp** | Campaigns, subscribers, lists |
| **ActiveCampaign** | Contacts, deals, automation |
| **Brevo (Sendinblue)** | Email, SMS, contacts |
| **ConvertKit** | Subscribers, sequences |

### Payments & E-Commerce

| App | Operations |
|-----|-----------|
| **Stripe** | Charges, subscriptions, customers |
| **Shopify** | Orders, products, customers |
| **WooCommerce** | Orders, products, categories |
| **PayPal** | Payments, payouts |
| **Chargebee** | Subscriptions, invoices |

### Communication

| App | Operations |
|-----|-----------|
| **Gmail** | Send, read, label, draft emails |
| **Discord** | Messages, channels, webhooks |
| **Telegram** | Messages, bots, keyboards |
| **WhatsApp** | Messages via Meta API |
| **Twilio** | SMS, voice, WhatsApp |
| **Matrix** | Messages, rooms |

### Cloud Services

| App | Operations |
|-----|-----------|
| **AWS S3** | Upload, download, list objects |
| **AWS Lambda** | Invoke functions |
| **AWS SQS** | Send/receive messages |
| **AWS SNS** | Publish notifications |
| **Azure Cosmos DB** | Documents, queries |
| **Azure Storage** | Blobs, containers |
| **Google Cloud Storage** | Upload, download, list |
| **Cloudflare** | DNS, zones, workers |

### Databases

| App | Operations |
|-----|-----------|
| **PostgreSQL** | Query, insert, update, delete |
| **MySQL** | Query, insert, update, delete |
| **MongoDB** | Find, insert, update, delete |
| **Microsoft SQL** | Query, insert, update |
| **Redis** | Get, set, delete, publish |
| **Supabase** | Rows, storage, functions |
| **Airtable** | Records, tables, views |

## AI and LangChain Nodes

### LLM Provider Nodes

| Node | Provider |
|------|----------|
| **OpenAI** | GPT-4o, GPT-4o-mini, etc. |
| **Anthropic** | Claude Sonnet, Opus, Haiku |
| **Google Gemini** | Gemini Pro, Flash |
| **Azure OpenAI** | Azure-hosted OpenAI models |
| **Mistral AI** | Mistral models |
| **Ollama** | Local open-source models |
| **Groq** | Fast inference |
| **Cohere** | Command models |
| **Hugging Face** | HF Inference API |

### AI Utility Nodes

| Node | Purpose |
|------|---------|
| **Agent** | Decision-making with tools |
| **Basic LLM Chain** | Simple prompt-response |
| **Information Extractor** | Structured data extraction |
| **Text Classifier** | Categorize text |
| **Sentiment Analysis** | Analyze tone/sentiment |
| **Summarization Chain** | Summarize long text |
| **Guardrails** | Input/output validation |
| **Evaluation** | Test AI output quality |
| **AI Transform** | Transform data using AI |

## Trigger Nodes Summary

n8n supports triggers from 200+ services. Each app node often has a corresponding trigger node:

```
Gmail Trigger → New email received
GitHub Trigger → New push, PR, or issue
Stripe Trigger → Payment, subscription event
Slack Trigger → New message in channel
Google Drive Trigger → File added or modified
Airtable Trigger → Record created or updated
```

## Popular Integrations

### Most Used Combinations

| Pattern | Nodes |
|---------|-------|
| **Data sync** | Google Sheets ↔ Airtable, PostgreSQL ↔ Salesforce |
| **Notifications** | Webhook → Slack / Discord / Email |
| **CRM pipeline** | Form Trigger → HubSpot → Email → Google Sheets |
| **DevOps alerts** | GitHub Trigger → Slack, Sentry → PagerDuty |
| **Content pipeline** | RSS → AI Summarize → WordPress → Social Media |
| **Order processing** | Shopify → Stripe → Email → Google Sheets |

## Community Nodes

### Discovery

Browse community nodes at the n8n community nodes directory or search npm:

```bash
npm search n8n-nodes-
```

### Popular Community Packages

Community packages extend n8n with integrations not available in the core:

- Custom CRM integrations
- Regional payment processors
- Industry-specific tools
- Custom AI model connectors

### Installing

```
Settings → Community Packages → Install
  Package Name: n8n-nodes-example
  → Install → Restart n8n if prompted
```

## Building Custom Nodes

### Node Starter Template

```bash
npx n8n-node-dev new
# Creates a scaffolded node project with:
# - Node definition file
# - Credential definition
# - Package configuration
# - Build scripts
```

### Node Structure

```typescript
// Example node definition
export class MyCustomNode implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'My Custom Node',
    name: 'myCustomNode',
    group: ['transform'],
    version: 1,
    inputs: ['main'],
    outputs: ['main'],
    properties: [
      {
        displayName: 'Operation',
        name: 'operation',
        type: 'options',
        options: [
          { name: 'Get', value: 'get' },
          { name: 'Create', value: 'create' },
        ],
        default: 'get',
      },
    ],
  };

  async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
    const items = this.getInputData();
    // Process items...
    return [items];
  }
}
```

### Publishing

```bash
# Build
npm run build

# Test locally
npm link
# Add to n8n via NODE_EXTRA_PATHS

# Publish to npm
npm publish
```

## Common Patterns by Category

### SaaS-to-SaaS Sync

```
Schedule Trigger (every 15 min)
  → Source API (fetch updated records)
  → Code (transform to target format)
  → Destination API (upsert records)
  → Slack (notify on errors)
```

### AI-Powered Processing

```
Gmail Trigger (new email)
  → AI Text Classifier (support/sales/spam)
  → Switch (by category)
    → Support: Create Jira ticket
    → Sales: Add to HubSpot
    → Spam: Archive email
```

### Multi-Channel Notification

```
Webhook (alert event)
  → Edit Fields (format message)
  → Parallel branches:
    → Slack (post to channel)
    → Email (send to team)
    → Discord (post to webhook)
    → PagerDuty (create incident)
```

## Common Pitfalls

- **Node version compatibility** — some node operations require specific n8n versions; check documentation
- **API rate limits** — high-frequency automations can exceed service rate limits; add delays between calls
- **OAuth token management** — some services require periodic re-authorization; monitor credential health
- **Community node maintenance** — community packages may become unmaintained; have a fallback plan
- **Data format assumptions** — different APIs return data in different shapes; always inspect output before building downstream logic
- **Trigger polling frequency** — frequent polling of external services can trigger rate limits or increase costs

## Related Topics

- HTTP Request → `06-http-request-and-apis.md`
- AI Agents → `09-ai-agents-and-tools.md`
- Workflow Management → `11-workflow-management.md`
