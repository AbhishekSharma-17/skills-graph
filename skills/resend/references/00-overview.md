# Resend — Overview

> Source: https://resend.com/docs/introduction

## Table of Contents
- [What Is Resend](#what-is-resend)
- [Core Products](#core-products)
- [When to Use Resend](#when-to-use-resend)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [SDK Ecosystem](#sdk-ecosystem)
- [Free Tier & Pricing](#free-tier--pricing)
- [Dashboard Overview](#dashboard-overview)
- [Key Concepts](#key-concepts)

## What Is Resend

Resend is a modern email API designed for developers. It provides a REST API and SDKs for sending transactional emails, marketing broadcasts, and managing email infrastructure. Built by the creators of React Email, Resend treats email as a first-class developer experience with type-safe SDKs, React-based templates, and real-time event tracking.

Key differentiators:
- **React Email integration** — build email templates with React components instead of raw HTML
- **Developer-first API** — clean REST endpoints, idempotency keys, structured error responses
- **Unified platform** — transactional emails + marketing broadcasts in one service
- **Multi-language SDKs** — Node.js, Python, Ruby, Go, Elixir, Java, PHP
- **Webhook-driven** — real-time delivery, bounce, open, and click events

## Core Products

### Transactional Emails
Individual emails triggered by application events (password resets, order confirmations, welcome emails). Sent via the `/emails` API endpoint with support for scheduling, attachments, and tags.

### Broadcasts
Marketing emails sent to audiences (newsletters, announcements, product updates). Managed via the `/broadcasts` API or the visual dashboard editor. Supports dynamic contact properties and audience segmentation.

### React Email
Open-source component library for building email templates using React and TypeScript. Renders to cross-client-compatible HTML. Includes a visual editor (React Email 6.0+).

### Audiences
Contact management system for organizing recipients into audiences. Supports custom properties, segments, topics, and automatic unsubscribe handling.

## When to Use Resend

**Good fit:**
- Transactional emails from web applications (Next.js, Express, FastAPI)
- Email templates that need to be version-controlled and tested
- Applications needing delivery tracking via webhooks
- Marketing broadcasts with audience segmentation
- Serverless/edge environments (Cloudflare Workers, Vercel Edge, AWS Lambda)

**Not the best fit:**
- High-volume cold outreach (use dedicated outreach tools)
- SMS or push notifications (email only)
- Legacy SMTP relay replacement without code changes (Resend is API-first)

## Architecture

```
Your Application
    │
    ├── resend.emails.send()     → POST /emails      → Email delivery
    ├── resend.batch.send()      → POST /emails/batch → Bulk delivery
    ├── resend.broadcasts.send() → POST /broadcasts   → Audience delivery
    │
    └── Webhook endpoint ← email.delivered / email.bounced / email.opened
```

**Authentication:** Bearer token via `Authorization: Bearer re_xxxxx` header.

**Base URL:** `https://api.resend.com`

**Rate limit:** 2 requests per second (default), with burst capacity.

## Quick Start

### Node.js

```typescript
import { Resend } from 'resend';

const resend = new Resend('re_xxxxx');

const { data, error } = await resend.emails.send({
  from: 'App <noreply@yourdomain.com>',
  to: ['user@example.com'],
  subject: 'Welcome!',
  html: '<h1>Hello</h1><p>Welcome to our platform.</p>',
});

if (error) {
  console.error(error);
} else {
  console.log('Email sent:', data.id);
}
```

### Python

```python
import resend

resend.api_key = "re_xxxxx"

params: resend.Emails.SendParams = {
    "from": "App <noreply@yourdomain.com>",
    "to": ["user@example.com"],
    "subject": "Welcome!",
    "html": "<h1>Hello</h1><p>Welcome to our platform.</p>",
}

email = resend.Emails.send(params)
print(f"Email sent: {email['id']}")
```

### cURL

```bash
curl -X POST 'https://api.resend.com/emails' \
  -H 'Authorization: Bearer re_xxxxx' \
  -H 'Content-Type: application/json' \
  -d '{
    "from": "App <noreply@yourdomain.com>",
    "to": ["user@example.com"],
    "subject": "Welcome!",
    "html": "<h1>Hello</h1>"
  }'
```

## SDK Ecosystem

| Language | Package | Install |
|----------|---------|---------|
| Node.js/TypeScript | `resend` | `npm install resend` |
| Python | `resend` | `pip install resend` |
| Ruby | `resend` | `gem install resend` |
| Go | `resend-go` | `go get github.com/resend/resend-go/v2` |
| Elixir | `resend` | `{:resend, "~> 0.4"}` |
| Java | `resend-java` | Maven/Gradle |
| PHP | `resend/resend-php` | `composer require resend/resend-php` |

All SDKs follow the same method naming: `emails.send()`, `batch.send()`, `domains.list()`, etc.

## Free Tier & Pricing

- **Free:** 3,000 emails/month, 1 custom domain, 1,000 contacts
- **Pro ($20/mo):** 50,000 emails/month, custom domains, priority support
- **Scale:** Volume pricing for high-throughput use cases
- **Enterprise:** Dedicated infrastructure, SLAs, SSO

No credit card required for the free tier.

## Dashboard Overview

The Resend dashboard at `resend.com` provides:
- **Emails tab** — delivery logs, status tracking, email detail view
- **Audiences tab** — contact management, audience creation, broadcast editor
- **Domains tab** — DNS record setup, verification status
- **Webhooks tab** — endpoint management, event selection
- **API Keys tab** — key creation, permissions, usage tracking
- **Logs tab** — real-time event stream for all email activity

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Transactional email** | Triggered by user action (signup, purchase). Sent via `/emails`. |
| **Broadcast** | Bulk email to an audience. Sent via `/broadcasts`. |
| **Audience** | Named group of contacts for broadcasts. |
| **Contact** | Individual recipient with properties (name, custom fields). |
| **Segment** | Filtered subset of an audience. |
| **Topic** | Subscription category contacts can opt in/out of. |
| **Domain** | Verified sending domain with DNS records (DKIM, SPF, DMARC). |
| **Webhook** | HTTP callback for email events (delivered, bounced, opened). |
| **Idempotency key** | Unique string preventing duplicate sends on retry. |
| **Tag** | Key-value pair attached to emails for filtering and analytics. |
| **React Email** | React component library for building email templates. |
