# PostHog — Data Pipelines (CDP)

> Source: [posthog.com/docs/cdp](https://posthog.com/docs/cdp) | PostHog Cloud / Self-Hosted

## Table of Contents

- [Data Pipelines Overview](#data-pipelines-overview)
- [Sources — Ingest External Data](#sources--ingest-external-data)
- [Destinations — Export Data](#destinations--export-data)
- [Transformations](#transformations)
- [Batch Exports](#batch-exports)
- [Realtime Destinations](#realtime-destinations)
- [Webhooks](#webhooks)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## Data Pipelines Overview

PostHog Data Pipelines (formerly CDP — Customer Data Platform) enable you to:
- **Sources** — ingest data from external databases and services into PostHog
- **Destinations** — send PostHog data to external tools (warehouses, CRMs, messaging)
- **Transformations** — modify events in-flight before they're stored
- **Batch Exports** — periodic bulk exports to data warehouses

## Sources — Ingest External Data

Link external data sources to PostHog and join them with your analytics data:

### Database Sources

| Source | Sync Methods |
|--------|-------------|
| **PostgreSQL** | Incremental, Full refresh |
| **MySQL** | Incremental, Full refresh |
| **Snowflake** | Incremental, Full refresh |
| **BigQuery** | Incremental, Full refresh |
| **Microsoft SQL** | Incremental, Full refresh |

### Object Storage Sources

| Source | Format |
|--------|--------|
| **Amazon S3** | Parquet, CSV, JSON |
| **Google Cloud Storage** | Parquet, CSV, JSON |
| **Cloudflare R2** | Parquet, CSV, JSON |
| **Azure Blob Storage** | Parquet, CSV, JSON |

### SaaS Sources

| Source | Data |
|--------|------|
| **Stripe** | Charges, customers, invoices, subscriptions |
| **Hubspot** | Contacts, companies, deals |
| **Salesforce** | Accounts, contacts, opportunities |
| **Zendesk** | Tickets, users, organizations |

### Setting Up a Source

```
1. Navigate to Data Pipeline → Sources → New Source
2. Select the source type (e.g., PostgreSQL)
3. Enter connection details (host, port, database, credentials)
4. Select tables to sync
5. Choose sync method per table
6. Set sync frequency (hourly, daily, weekly)
7. Run initial sync
```

### Sync Methods

| Method | Description | Best For |
|--------|-------------|----------|
| **Incremental** | Only syncs new/updated rows since last sync | Large tables with timestamps |
| **Full refresh** | Reloads entire table each sync | Small tables, no reliable timestamp |
| **Append only** | Only adds new rows, never updates | Event/log tables |

### Querying Synced Data

Once synced, external data appears as tables in the data warehouse:

```sql
-- Join PostHog events with Stripe charges
SELECT
  events.distinct_id,
  events.event,
  stripe_charges.amount,
  stripe_charges.status
FROM events
JOIN stripe_charges ON events.distinct_id = stripe_charges.customer_email
WHERE events.event = 'purchase_completed'
```

## Destinations — Export Data

Send PostHog events and data to external services:

### Available Destinations

| Destination | Type | Use Case |
|-------------|------|----------|
| **Snowflake** | Data Warehouse | Central analytics warehouse |
| **BigQuery** | Data Warehouse | Google analytics stack |
| **Redshift** | Data Warehouse | AWS analytics stack |
| **S3** | Object Storage | Data lake, archival |
| **Google Cloud Storage** | Object Storage | GCP data lake |
| **Hubspot** | CRM | Sync user events to contacts |
| **Salesforce** | CRM | Update lead/contact records |
| **Slack** | Messaging | Alert on specific events |
| **Intercom** | Support | Enrich user context |
| **Customer.io** | Email | Trigger email campaigns |
| **Rudderstack** | CDP | Fan-out to multiple tools |
| **Webhook** | Custom | Send to any HTTP endpoint |

## Transformations

Modify events before they're stored in PostHog:

### Use Cases

- **Enrich events** — add properties from external lookups
- **Filter events** — drop events that match certain criteria
- **Normalize data** — standardize property names and values
- **PII scrubbing** — remove or hash sensitive properties

### Creating a Transformation

Transformations are written as JavaScript/TypeScript functions:

```typescript
// Example: Add geo data based on IP
export function processEvent(event) {
  if (event.properties?.$ip) {
    const geo = lookupGeo(event.properties.$ip);
    event.properties.$geoip_country = geo.country;
    event.properties.$geoip_city = geo.city;
  }
  return event;
}

// Return null to drop the event
export function processEvent(event) {
  if (event.properties?.$current_url?.includes('/health')) {
    return null;  // drop health check events
  }
  return event;
}
```

## Batch Exports

Periodically export PostHog data to external destinations:

### Configuration

```
Destination: Snowflake
Frequency: Hourly
Data: All events
Format: Parquet
```

### Supported Batch Destinations

- **Snowflake** — exports to a Snowflake table
- **BigQuery** — exports to a BigQuery table
- **Redshift** — exports to a Redshift table
- **S3** — exports as Parquet/JSON files to S3
- **GCS** — exports to Google Cloud Storage
- **Azure Blob** — exports to Azure storage

### Export Schema

Exported events include:

```json
{
  "uuid": "event-uuid",
  "event": "purchase_completed",
  "distinct_id": "user_123",
  "properties": { "amount": 49.99 },
  "timestamp": "2026-04-24T10:30:00Z",
  "team_id": 1,
  "created_at": "2026-04-24T10:30:01Z"
}
```

## Realtime Destinations

Send events to external services as they happen (not batched):

### Slack Notifications

```
Trigger: event = 'enterprise_signup'
Channel: #sales-leads
Message: "New enterprise signup: {person.email} from {person.company}"
```

### Webhook

```
Trigger: event = 'purchase_completed'
URL: https://api.yourservice.com/webhooks/posthog
Headers: { "Authorization": "Bearer <token>" }
Body: Full event payload
```

### Hubspot Contact Update

```
Trigger: event = 'subscription_changed'
Action: Update Hubspot contact
Mapping:
  email → person.email
  plan → event.properties.new_plan
  mrr → event.properties.new_mrr
```

## Webhooks

Send event data to any HTTP endpoint:

### Setup

```
1. Data Pipeline → Destinations → New Destination → Webhook
2. Enter URL: https://your-api.com/webhooks/posthog
3. Set headers (e.g., Authorization)
4. Configure event filters
5. Test with a sample event
6. Enable
```

### Webhook Payload

```json
{
  "hook": {
    "id": "hook_123",
    "event": "purchase_completed",
    "target": "https://your-api.com/webhooks/posthog"
  },
  "data": {
    "event": "purchase_completed",
    "distinct_id": "user_123",
    "properties": {
      "amount": 49.99,
      "currency": "USD"
    },
    "timestamp": "2026-04-24T10:30:00Z",
    "person": {
      "properties": {
        "email": "jane@example.com",
        "plan": "pro"
      }
    }
  }
}
```

### Filtering Webhook Events

```
Send only: event = 'purchase_completed' AND properties.amount > 100
```

## Common Patterns

### Sync Product Usage to CRM

```
Source: PostHog (product events)
Destination: Hubspot
Trigger: Daily batch
Mapping:
  - Total events last 7 days → "Product Usage Score"
  - Last active date → "Last Seen"
  - Feature flags active → "Beta Features"
```

### Build a Data Warehouse

```
Source 1: PostHog events → BigQuery (batch, hourly)
Source 2: Stripe charges → PostHog → BigQuery
Source 3: Hubspot contacts → PostHog → BigQuery
Join: All data in BigQuery for cross-platform analytics
```

### Alert on Important Events

```
Destination: Slack webhook
Filter: event = 'enterprise_trial_started'
Channel: #sales-pipeline
Message: "🎯 {person.properties.name} ({person.properties.company}) started an enterprise trial"
```

## Common Pitfalls

1. **Source sync failures silently** — check sync status regularly; set up alerts for failures
2. **Schema changes breaking syncs** — column additions are fine, but renaming/removing columns breaks incremental syncs
3. **Large initial syncs** — first full sync of large tables can take hours; schedule during off-hours
4. **Webhook rate limits** — destination APIs may rate-limit; configure retry policies
5. **Not filtering batch exports** — exporting all events to a warehouse gets expensive; filter to relevant events
6. **Transformation errors dropping events** — a bug in your transformation function can silently drop events; monitor event volumes
