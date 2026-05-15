# Audiences & Contacts

> Source: https://resend.com/docs/dashboard/audiences/introduction

## Table of Contents
- [Overview](#overview)
- [Audiences API](#audiences-api)
- [Contacts API](#contacts-api)
- [Contact Properties](#contact-properties)
- [Segments](#segments)
- [Topics & Subscriptions](#topics--subscriptions)
- [Unsubscribe Management](#unsubscribe-management)
- [Code Examples](#code-examples)
- [Common Pitfalls](#common-pitfalls)

## Overview

Audiences are groups of contacts used for sending broadcasts (marketing emails). Resend manages the full contact lifecycle: creation, property management, segmentation, subscription preferences, and automatic unsubscribe handling.

**Free tier:** 1,000 contacts included. Paid plans start at $40/mo for 5,000 contacts.

## Audiences API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/audiences` | Create an audience |
| `GET` | `/audiences` | List all audiences |
| `GET` | `/audiences/:id` | Get audience details |
| `DELETE` | `/audiences/:id` | Delete an audience |

### Create Audience

```typescript
const { data } = await resend.audiences.create({
  name: 'Newsletter Subscribers',
});

console.log(data.id); // aud_xxxxx
```

```python
audience = resend.Audiences.create({"name": "Newsletter Subscribers"})
```

### List Audiences

```typescript
const { data } = await resend.audiences.list();
// data.data: [{ id, name, created_at }]
```

## Contacts API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/audiences/:aud_id/contacts` | Create a contact |
| `GET` | `/audiences/:aud_id/contacts` | List contacts in audience |
| `GET` | `/audiences/:aud_id/contacts/:id` | Get contact details |
| `PATCH` | `/audiences/:aud_id/contacts/:id` | Update contact |
| `DELETE` | `/audiences/:aud_id/contacts/:id` | Remove contact |

### Create Contact

```typescript
const { data } = await resend.contacts.create({
  audienceId: 'aud_xxxxx',
  email: 'alice@example.com',
  firstName: 'Alice',
  lastName: 'Smith',
  unsubscribed: false,
});
```

```python
contact = resend.Contacts.create({
    "audience_id": "aud_xxxxx",
    "email": "alice@example.com",
    "first_name": "Alice",
    "last_name": "Smith",
    "unsubscribed": False,
})
```

### Update Contact

```typescript
await resend.contacts.update({
  audienceId: 'aud_xxxxx',
  id: 'contact_xxxxx',
  firstName: 'Alicia',
  unsubscribed: false,
});
```

### Remove Contact

```typescript
// By ID
await resend.contacts.remove({
  audienceId: 'aud_xxxxx',
  id: 'contact_xxxxx',
});

// By email
await resend.contacts.remove({
  audienceId: 'aud_xxxxx',
  email: 'alice@example.com',
});
```

### List Contacts

```typescript
const { data } = await resend.contacts.list({
  audienceId: 'aud_xxxxx',
});
```

## Contact Properties

Custom properties allow dynamic data in broadcast templates.

### Property API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/contact-properties` | Create property |
| `GET` | `/contact-properties` | List properties |
| `GET` | `/contact-properties/:id` | Get property |
| `PATCH` | `/contact-properties/:id` | Update fallback value |
| `DELETE` | `/contact-properties/:id` | Delete property |

### Create Property

```typescript
await resend.contactProperties.create({
  key: 'company_name',
  type: 'string', // 'string' or 'number'
  fallbackValue: 'your company',
});
```

### Set Properties on Contact

```typescript
await resend.contacts.create({
  audienceId: 'aud_xxxxx',
  email: 'alice@example.com',
  firstName: 'Alice',
  properties: {
    company_name: 'Acme Corp',
    plan: 'pro',
  },
});
```

### Use in Broadcast Templates

Properties are accessible in broadcast HTML using triple-brace syntax:

```html
<p>Hi {{{contact.first_name|there}}},</p>
<p>Welcome to {{{contact.company_name|our platform}}}!</p>
```

The value after `|` is the fallback if the property is not set on the contact.

## Segments

Segments are filtered subsets of an audience.

### Add Contact to Segment

```typescript
await resend.contacts.segments.add({
  contactId: 'contact_xxxxx',
  segmentId: 'seg_xxxxx',
});

// Or by email
await resend.contacts.segments.add({
  email: 'alice@example.com',
  segmentId: 'seg_xxxxx',
});
```

### Remove from Segment

```typescript
await resend.contacts.segments.remove({
  contactId: 'contact_xxxxx',
  segmentId: 'seg_xxxxx',
});
```

Segments can be used when creating broadcasts to target specific subsets of an audience.

## Topics & Subscriptions

Topics allow contacts to subscribe to specific email categories.

```typescript
// Create a broadcast targeting a specific topic
await resend.broadcasts.create({
  segmentId: 'seg_xxxxx',
  from: 'Newsletter <news@yourdomain.com>',
  subject: 'Product Updates',
  html: '<p>New features this week...</p>',
});
```

Contacts can manage their preferences through the automatically-generated unsubscribe page.

## Unsubscribe Management

Resend handles unsubscribe compliance automatically:

1. **List-Unsubscribe header** — added to all broadcast emails
2. **One-click unsubscribe** — compliant with RFC 8058
3. **Unsubscribe page** — Resend hosts a branded unsubscribe page
4. **Automatic suppression** — unsubscribed contacts won't receive future broadcasts

### Manual Unsubscribe

```typescript
await resend.contacts.update({
  audienceId: 'aud_xxxxx',
  id: 'contact_xxxxx',
  unsubscribed: true,
});
```

### Check Subscription Status

```typescript
const { data } = await resend.contacts.get({
  audienceId: 'aud_xxxxx',
  id: 'contact_xxxxx',
});

if (data.unsubscribed) {
  // Don't send marketing emails to this contact
}
```

## Code Examples

### Bulk Import Contacts

```typescript
async function importContacts(
  audienceId: string,
  contacts: Array<{ email: string; firstName?: string; lastName?: string }>
) {
  const results = [];

  for (const contact of contacts) {
    const { data, error } = await resend.contacts.create({
      audienceId,
      email: contact.email,
      firstName: contact.firstName,
      lastName: contact.lastName,
    });

    if (error) {
      console.error(`Failed to import ${contact.email}:`, error.message);
    } else {
      results.push(data);
    }

    // Respect rate limits
    await new Promise((r) => setTimeout(r, 500));
  }

  return results;
}
```

### Sync Contacts from Database

```typescript
async function syncContacts(audienceId: string) {
  const users = await db.users.findMany({
    where: { emailVerified: true, marketingOptIn: true },
  });

  for (const user of users) {
    await resend.contacts.create({
      audienceId,
      email: user.email,
      firstName: user.name?.split(' ')[0],
      lastName: user.name?.split(' ').slice(1).join(' '),
      properties: {
        plan: user.plan,
        signup_date: user.createdAt.toISOString(),
      },
    });
  }
}
```

### Webhook-Driven Contact Cleanup

```typescript
// In your webhook handler
case 'email.bounced':
  if (data.bounce.type === 'hard') {
    const audiences = await resend.audiences.list();
    for (const audience of audiences.data.data) {
      await resend.contacts.remove({
        audienceId: audience.id,
        email: data.to[0],
      }).catch(() => {}); // Ignore if not in this audience
    }
  }
  break;
```

## Common Pitfalls

1. **Not using audience for broadcasts** — broadcasts require an audience. You cannot send to arbitrary email lists.
2. **Duplicate contacts** — creating a contact with an existing email updates it (upsert behavior).
3. **Property type mismatch** — property types (`string`/`number`) are set at creation and cannot be changed.
4. **Missing fallback values** — always provide fallbacks in templates: `{{{contact.name|Friend}}}`.
5. **Ignoring unsubscribes** — sending to unsubscribed contacts violates CAN-SPAM. Resend enforces this automatically for broadcasts.
6. **Rate limits on bulk import** — add delays when importing many contacts to avoid hitting the 2 req/s limit.
