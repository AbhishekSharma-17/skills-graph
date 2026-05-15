# Webhooks

> Source: https://resend.com/docs/webhooks/introduction

## Table of Contents
- [Overview](#overview)
- [Event Types](#event-types)
- [Webhook Payload](#webhook-payload)
- [Setting Up Webhooks](#setting-up-webhooks)
- [Webhook API Endpoints](#webhook-api-endpoints)
- [Signature Verification](#signature-verification)
- [Event Details](#event-details)
- [Handling Webhooks](#handling-webhooks)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## Overview

Resend webhooks deliver real-time HTTP notifications when email events occur. They use Svix for reliable delivery with at-least-once semantics, automatic retries, and cryptographic signature verification.

**Key characteristics:**
- HTTPS-only endpoints
- JSON payloads
- At-least-once delivery (design handlers to be idempotent)
- Automatic retries with exponential backoff
- Svix-based signature verification

## Event Types

| Event | Description |
|-------|-------------|
| `email.sent` | Email accepted by Resend, delivery attempt starting |
| `email.delivered` | Successfully delivered to recipient's mail server |
| `email.delivery_delayed` | Temporary delivery failure, will retry |
| `email.bounced` | Permanent delivery failure (invalid address, etc.) |
| `email.complained` | Recipient marked email as spam |
| `email.opened` | Recipient opened the email (tracking pixel) |
| `email.clicked` | Recipient clicked a link in the email |
| `email.failed` | Email could not be sent (internal error) |
| `email.scheduled` | Email scheduled for future delivery |
| `email.suppressed` | Email suppressed (previously bounced/complained address) |
| `email.received` | Inbound email received (agent inbox feature) |
| `contact.created` | New contact added to an audience |
| `contact.updated` | Contact properties changed |
| `contact.deleted` | Contact removed from audience |
| `domain.verified` | Domain DNS verification completed |

## Webhook Payload

All events share a common structure:

```json
{
  "type": "email.delivered",
  "created_at": "2026-05-15T10:30:00.000Z",
  "data": {
    "email_id": "ae2014de-c168-4c61-8267-70d2662a1ce1",
    "from": "noreply@yourdomain.com",
    "to": ["user@example.com"],
    "subject": "Welcome!",
    "created_at": "2026-05-15T10:29:55.000Z",
    "tags": {
      "category": "onboarding"
    }
  }
}
```

Bounce events include additional data:

```json
{
  "type": "email.bounced",
  "data": {
    "email_id": "...",
    "bounce": {
      "message": "550 5.1.1 The email account does not exist",
      "type": "hard"
    }
  }
}
```

## Setting Up Webhooks

### Via Dashboard

1. Go to **Webhooks** tab in the Resend dashboard
2. Click **Add Webhook**
3. Enter your endpoint URL (must be HTTPS)
4. Select the events to subscribe to
5. Save — the webhook secret is displayed once

### Via API

```typescript
const webhook = await resend.webhooks.create({
  url: 'https://yourdomain.com/api/webhooks/resend',
  events: ['email.delivered', 'email.bounced', 'email.complained'],
});

// webhook.id and webhook.secret are in the response
```

## Webhook API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/webhooks` | Create a webhook |
| `GET` | `/webhooks` | List all webhooks |
| `GET` | `/webhooks/:id` | Retrieve a webhook |
| `PATCH` | `/webhooks/:id` | Update webhook URL or events |
| `DELETE` | `/webhooks/:id` | Delete a webhook |

### SDK Methods

```typescript
await resend.webhooks.create({ url, events });
await resend.webhooks.list();
await resend.webhooks.get(webhookId);
await resend.webhooks.update(webhookId, { url, events });
await resend.webhooks.remove(webhookId);
```

## Signature Verification

Resend signs webhook payloads using Svix. Every request includes three headers:

| Header | Description |
|--------|-------------|
| `svix-id` | Unique message identifier |
| `svix-timestamp` | Unix timestamp (seconds) |
| `svix-signature` | HMAC-SHA256 signature(s) |

### Node.js Verification

```typescript
import { Webhook } from 'svix';

const webhookSecret = process.env.RESEND_WEBHOOK_SECRET; // whsec_xxxxx

export async function POST(request: Request) {
  const body = await request.text();
  const headers = {
    'svix-id': request.headers.get('svix-id')!,
    'svix-timestamp': request.headers.get('svix-timestamp')!,
    'svix-signature': request.headers.get('svix-signature')!,
  };

  const wh = new Webhook(webhookSecret);

  try {
    const event = wh.verify(body, headers);
    // event is verified — safe to process
    return handleEvent(event);
  } catch (err) {
    return new Response('Invalid signature', { status: 401 });
  }
}
```

### Python Verification

```python
from svix.webhooks import Webhook, WebhookVerificationError

webhook_secret = os.environ["RESEND_WEBHOOK_SECRET"]

def verify_webhook(payload: bytes, headers: dict) -> dict:
    wh = Webhook(webhook_secret)
    try:
        return wh.verify(payload, headers)
    except WebhookVerificationError:
        raise HTTPException(status_code=401, detail="Invalid signature")
```

Install the Svix library: `npm install svix` or `pip install svix`.

## Event Details

### email.opened

Triggered when the recipient opens the email. Uses a tracking pixel — not 100% reliable (some clients block images).

```json
{
  "type": "email.opened",
  "data": {
    "email_id": "...",
    "opened_at": "2026-05-15T11:00:00.000Z"
  }
}
```

### email.clicked

Triggered when a recipient clicks a tracked link.

```json
{
  "type": "email.clicked",
  "data": {
    "email_id": "...",
    "clicked_at": "2026-05-15T11:05:00.000Z",
    "url": "https://yourdomain.com/activate"
  }
}
```

### email.bounced

```json
{
  "type": "email.bounced",
  "data": {
    "email_id": "...",
    "bounce": {
      "message": "550 5.1.1 The email account does not exist",
      "type": "hard"
    }
  }
}
```

Bounce types: `hard` (permanent, remove from list) or `soft` (temporary, retry later).

## Handling Webhooks

### Next.js App Router

```typescript
// app/api/webhooks/resend/route.ts
import { Webhook } from 'svix';

const webhookSecret = process.env.RESEND_WEBHOOK_SECRET!;

export async function POST(request: Request) {
  const body = await request.text();
  const wh = new Webhook(webhookSecret);

  const event = wh.verify(body, {
    'svix-id': request.headers.get('svix-id')!,
    'svix-timestamp': request.headers.get('svix-timestamp')!,
    'svix-signature': request.headers.get('svix-signature')!,
  });

  const { type, data } = event as { type: string; data: any };

  switch (type) {
    case 'email.delivered':
      await markEmailDelivered(data.email_id);
      break;
    case 'email.bounced':
      await handleBounce(data.email_id, data.bounce);
      break;
    case 'email.complained':
      await handleComplaint(data.email_id);
      break;
  }

  return new Response('OK', { status: 200 });
}
```

### FastAPI

```python
from fastapi import FastAPI, Request, HTTPException
from svix.webhooks import Webhook, WebhookVerificationError

app = FastAPI()

@app.post("/api/webhooks/resend")
async def handle_webhook(request: Request):
    body = await request.body()
    headers = {
        "svix-id": request.headers.get("svix-id"),
        "svix-timestamp": request.headers.get("svix-timestamp"),
        "svix-signature": request.headers.get("svix-signature"),
    }

    wh = Webhook(os.environ["RESEND_WEBHOOK_SECRET"])
    try:
        event = wh.verify(body.decode(), headers)
    except WebhookVerificationError:
        raise HTTPException(status_code=401)

    event_type = event["type"]
    data = event["data"]

    if event_type == "email.bounced":
        await remove_bounced_email(data["to"][0])
    elif event_type == "email.complained":
        await suppress_email(data["to"][0])

    return {"status": "ok"}
```

## Common Patterns

### Bounce List Management

```typescript
case 'email.bounced':
  if (data.bounce.type === 'hard') {
    await db.suppressedEmails.create({
      email: data.to[0],
      reason: 'hard_bounce',
      message: data.bounce.message,
      created_at: new Date(),
    });
  }
  break;
```

### Delivery Analytics

```typescript
case 'email.delivered':
  await analytics.track('email_delivered', {
    emailId: data.email_id,
    tags: data.tags,
    latencyMs: Date.now() - new Date(data.created_at).getTime(),
  });
  break;
```

## Common Pitfalls

1. **Not verifying signatures** — always verify Svix signatures to prevent spoofed events.
2. **Non-idempotent handlers** — at-least-once delivery means duplicate events are possible. Use `email_id` as a dedup key.
3. **Blocking webhook responses** — return `200` quickly. Process events asynchronously.
4. **Trusting `email.opened`** — tracking pixels are blocked by many clients. Treat open rates as estimates.
5. **Ignoring `email.suppressed`** — Resend auto-suppresses previously bounced addresses. Handle this to keep your contact lists clean.
6. **HTTP endpoints** — webhooks require HTTPS. Use tools like ngrok for local development.
