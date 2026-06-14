# Clerk — Webhooks

> Source: [clerk.com/docs/webhooks/overview](https://clerk.com/docs/webhooks/overview)

## Table of Contents

- [Overview](#overview)
- [Available Events](#available-events)
- [Setting Up Webhooks](#setting-up-webhooks)
- [Webhook Payload Structure](#webhook-payload-structure)
- [Verifying Webhook Signatures](#verifying-webhook-signatures)
- [Next.js Webhook Handler](#nextjs-webhook-handler)
- [Database Sync Pattern](#database-sync-pattern)
- [Delivery and Retries](#delivery-and-retries)
- [Testing Webhooks Locally](#testing-webhooks-locally)
- [Common Patterns](#common-patterns)
- [Troubleshooting](#troubleshooting)

## Overview

Clerk webhooks send HTTP POST requests to your endpoint when events occur (user created, updated, deleted, org membership changed, etc.). They're powered by Svix and include cryptographic signatures for verification.

Webhooks are asynchronous — they're not suitable for flows that need immediate confirmation of delivery.

## Available Events

### User Events
| Event | Triggered When |
|-------|----------------|
| `user.created` | New user signs up |
| `user.updated` | User profile changes |
| `user.deleted` | User account deleted |

### Session Events
| Event | Triggered When |
|-------|----------------|
| `session.created` | User signs in |
| `session.ended` | Session expires or user signs out |
| `session.removed` | Session explicitly revoked |

### Organization Events
| Event | Triggered When |
|-------|----------------|
| `organization.created` | New org created |
| `organization.updated` | Org settings changed |
| `organization.deleted` | Org deleted |
| `organizationMembership.created` | User joins org |
| `organizationMembership.updated` | Member role changed |
| `organizationMembership.deleted` | User leaves or removed |
| `organizationInvitation.created` | Invitation sent |
| `organizationInvitation.accepted` | Invitation accepted |
| `organizationInvitation.revoked` | Invitation revoked |

### Other Events
| Event | Triggered When |
|-------|----------------|
| `email.created` | Clerk sends an email |
| `sms.created` | Clerk sends an SMS |

## Setting Up Webhooks

### Via Dashboard

1. Go to **Clerk Dashboard > Webhooks**
2. Click **Add Endpoint**
3. Enter your endpoint URL (e.g., `https://myapp.com/api/webhooks/clerk`)
4. Select events to subscribe to
5. Copy the **Signing Secret** (`whsec_...`)

### Via CLI

```bash
# List webhook routes
npx clerk@latest api ls webhook

# Create endpoint
npx clerk@latest api webhooks create \
  --url "https://myapp.com/api/webhooks/clerk" \
  --events "user.created,user.updated,user.deleted"
```

## Webhook Payload Structure

Every webhook payload has this shape:

```json
{
  "data": {
    "id": "user_abc123",
    "first_name": "Jane",
    "last_name": "Doe",
    "email_addresses": [
      {
        "id": "idn_abc",
        "email_address": "jane@example.com"
      }
    ],
    "public_metadata": {},
    "private_metadata": {},
    "unsafe_metadata": {},
    "created_at": 1234567890,
    "updated_at": 1234567890
  },
  "object": "event",
  "type": "user.created",
  "timestamp": 1234567890123,
  "instance_id": "ins_abc123"
}
```

The `data` field varies by event type — it contains the full object (User, Organization, etc.) at the time of the event.

## Verifying Webhook Signatures

Clerk webhooks are signed by Svix. Always verify signatures to prevent spoofing.

### Using Clerk's verifyWebhook Helper

```bash
npm install @clerk/nextjs
# verifyWebhook is included in @clerk/nextjs/webhooks
```

### Using Svix Directly

```bash
npm install svix
```

```tsx
import { Webhook } from 'svix'

function verifyWebhook(req: Request, body: string, secret: string) {
  const wh = new Webhook(secret)

  const headers = {
    'svix-id': req.headers.get('svix-id')!,
    'svix-timestamp': req.headers.get('svix-timestamp')!,
    'svix-signature': req.headers.get('svix-signature')!,
  }

  return wh.verify(body, headers)
}
```

## Next.js Webhook Handler

Complete webhook handler for Next.js App Router:

```tsx
// app/api/webhooks/clerk/route.ts
import { Webhook } from 'svix'
import { headers } from 'next/headers'
import { NextResponse } from 'next/server'

const webhookSecret = process.env.CLERK_WEBHOOK_SECRET!

interface WebhookEvent {
  data: Record<string, unknown>
  object: 'event'
  type: string
  timestamp: number
  instance_id: string
}

export async function POST(req: Request) {
  const headerPayload = await headers()
  const svixId = headerPayload.get('svix-id')
  const svixTimestamp = headerPayload.get('svix-timestamp')
  const svixSignature = headerPayload.get('svix-signature')

  if (!svixId || !svixTimestamp || !svixSignature) {
    return NextResponse.json(
      { error: 'Missing svix headers' },
      { status: 400 }
    )
  }

  const body = await req.text()

  const wh = new Webhook(webhookSecret)
  let event: WebhookEvent

  try {
    event = wh.verify(body, {
      'svix-id': svixId,
      'svix-timestamp': svixTimestamp,
      'svix-signature': svixSignature,
    }) as WebhookEvent
  } catch {
    return NextResponse.json(
      { error: 'Invalid signature' },
      { status: 400 }
    )
  }

  switch (event.type) {
    case 'user.created':
      await handleUserCreated(event.data)
      break
    case 'user.updated':
      await handleUserUpdated(event.data)
      break
    case 'user.deleted':
      await handleUserDeleted(event.data)
      break
    default:
      console.log(`Unhandled event: ${event.type}`)
  }

  return NextResponse.json({ received: true })
}

async function handleUserCreated(data: Record<string, unknown>) {
  const { id, first_name, last_name, email_addresses } = data as {
    id: string
    first_name: string | null
    last_name: string | null
    email_addresses: Array<{ email_address: string }>
  }

  await db.user.create({
    data: {
      clerkId: id,
      firstName: first_name,
      lastName: last_name,
      email: email_addresses[0]?.email_address,
    },
  })
}

async function handleUserUpdated(data: Record<string, unknown>) {
  const { id, first_name, last_name, email_addresses } = data as {
    id: string
    first_name: string | null
    last_name: string | null
    email_addresses: Array<{ email_address: string }>
  }

  await db.user.update({
    where: { clerkId: id },
    data: {
      firstName: first_name,
      lastName: last_name,
      email: email_addresses[0]?.email_address,
    },
  })
}

async function handleUserDeleted(data: Record<string, unknown>) {
  const { id } = data as { id: string }
  await db.user.delete({ where: { clerkId: id } })
}
```

**Important:** Make the webhook route public in your middleware:

```tsx
const isPublicRoute = createRouteMatcher([
  '/api/webhooks(.*)',
  // other public routes
])
```

## Database Sync Pattern

The most common webhook use case is syncing Clerk users to your database:

```tsx
// prisma/schema.prisma
model User {
  id        String   @id @default(cuid())
  clerkId   String   @unique
  email     String
  firstName String?
  lastName  String?
  imageUrl  String?
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  projects  Project[]
  // other relations
}
```

Subscribe to these events: `user.created`, `user.updated`, `user.deleted`.

## Delivery and Retries

- Svix retries failed webhooks automatically on a schedule
- Endpoints must respond with 2xx status within 30 seconds
- Failed deliveries can be replayed from the Dashboard (**Webhooks > Message Attempts**)
- Svix provides IP addresses you can allowlist for additional security

**Best practices:**
- Respond quickly — do heavy processing asynchronously
- Make handlers idempotent — the same event may be delivered multiple times
- Log the `svix-id` header for debugging duplicate deliveries

## Testing Webhooks Locally

### Using Clerk CLI

```bash
# Forward webhooks to local development server
clerk webhooks proxy --url http://localhost:3000/api/webhooks/clerk
```

### Using ngrok

```bash
ngrok http 3000
# Use the ngrok URL as your webhook endpoint in the Dashboard
```

### Using Svix CLI

```bash
# Replay a specific webhook for testing
svix message retry <message-id> --endpoint <endpoint-id>
```

## Common Patterns

**Sync users + org memberships:**
```tsx
switch (event.type) {
  case 'user.created':
    await createUser(event.data)
    break
  case 'organizationMembership.created':
    await addOrgMember(event.data)
    break
  case 'organizationMembership.deleted':
    await removeOrgMember(event.data)
    break
}
```

**Trigger welcome email on signup:**
```tsx
case 'user.created':
  await sendWelcomeEmail(event.data.email_addresses[0].email_address)
  break
```

**Audit logging:**
```tsx
// Log all events for compliance
await db.auditLog.create({
  data: {
    eventType: event.type,
    payload: JSON.stringify(event.data),
    timestamp: new Date(event.timestamp),
  },
})
```

## Troubleshooting

**Webhook not receiving events:**
- Verify the endpoint URL is publicly accessible
- Check the endpoint is not behind middleware auth
- Confirm the events are selected in the Dashboard

**Signature verification failing:**
- Ensure you're using the raw request body (not parsed JSON)
- Verify the signing secret matches (`whsec_...`)
- Check that svix headers are being forwarded (not stripped by a proxy)

**Events arriving out of order:**
- Use the `timestamp` field to determine event ordering
- Design handlers to be idempotent
- Use the `data` field as the current state, not a delta
