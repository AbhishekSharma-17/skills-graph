# Broadcasts

> Source: https://resend.com/docs/api-reference/broadcasts

## Table of Contents
- [Overview](#overview)
- [Broadcast API Endpoints](#broadcast-api-endpoints)
- [Creating Broadcasts](#creating-broadcasts)
- [Sending Broadcasts](#sending-broadcasts)
- [Scheduling Broadcasts](#scheduling-broadcasts)
- [Dynamic Content](#dynamic-content)
- [Broadcast Lifecycle](#broadcast-lifecycle)
- [Dashboard Editor](#dashboard-editor)
- [Code Examples](#code-examples)
- [Common Pitfalls](#common-pitfalls)

## Overview

Broadcasts are marketing emails sent to an audience (newsletter, product updates, announcements). Unlike transactional emails (triggered by user actions), broadcasts are sent to many recipients at once with optional personalization via contact properties.

**Key differences from transactional emails:**
- Sent to audiences, not individual addresses
- Include automatic unsubscribe handling
- Support contact property interpolation
- Can be created as drafts and sent later
- Managed via dashboard visual editor or API

## Broadcast API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/broadcasts` | Create a broadcast (draft or send immediately) |
| `GET` | `/broadcasts` | List all broadcasts |
| `GET` | `/broadcasts/:id` | Get broadcast details |
| `PATCH` | `/broadcasts/:id` | Update a draft broadcast |
| `POST` | `/broadcasts/:id/send` | Send or schedule a draft broadcast |
| `DELETE` | `/broadcasts/:id` | Delete a draft broadcast |

## Creating Broadcasts

### Create and Send Immediately

```typescript
const { data } = await resend.broadcasts.create({
  segmentId: 'seg_xxxxx', // or audienceId
  from: 'Newsletter <news@yourdomain.com>',
  subject: 'Weekly Product Update',
  replyTo: 'support@yourdomain.com',
  html: '<h1>New Features</h1><p>Check out what we shipped this week.</p>',
  send: true, // Send immediately
});
```

### Create as Draft

```typescript
const { data } = await resend.broadcasts.create({
  segmentId: 'seg_xxxxx',
  from: 'Newsletter <news@yourdomain.com>',
  subject: 'Coming Soon',
  html: '<p>Draft content to review.</p>',
  // send: false is the default
});

// data.id — use this to send later
```

### Python

```python
broadcast = resend.Broadcasts.create({
    "segment_id": "seg_xxxxx",
    "from": "Newsletter <news@yourdomain.com>",
    "subject": "Weekly Update",
    "html": "<h1>This Week</h1><p>News and updates.</p>",
    "send": True,
})
```

## Sending Broadcasts

### Send a Draft

```typescript
await resend.broadcasts.send('broadcast_xxxxx');
```

### Send with Schedule

```typescript
await resend.broadcasts.send('broadcast_xxxxx', {
  scheduledAt: '2026-06-01T09:00:00Z',
});

// Natural language
await resend.broadcasts.send('broadcast_xxxxx', {
  scheduledAt: 'tomorrow at 9am ET',
});
```

## Scheduling Broadcasts

Broadcasts can be scheduled at creation or when sending a draft:

```typescript
// Schedule at creation
await resend.broadcasts.create({
  segmentId: 'seg_xxxxx',
  from: 'Newsletter <news@yourdomain.com>',
  subject: 'Scheduled Newsletter',
  html: '<p>This goes out next Monday.</p>',
  send: true,
  scheduledAt: 'next Monday at 9am ET',
});

// Schedule a draft
await resend.broadcasts.send(broadcastId, {
  scheduledAt: '2026-06-01T14:00:00Z',
});
```

## Dynamic Content

Use contact properties in broadcast HTML with triple-brace syntax:

```html
<h1>Hi {{{contact.first_name|there}}}!</h1>
<p>Thanks for being a {{{contact.plan|free}}} customer at {{{contact.company_name|our platform}}}.</p>
<p>You have been with us since {{{contact.signup_date|the beginning}}}.</p>
```

**Syntax:** `{{{contact.property_key|fallback_value}}}`

- `contact.first_name` — built-in field
- `contact.last_name` — built-in field
- `contact.email` — built-in field
- `contact.custom_key` — custom property you defined

The fallback value after `|` is used when the property is not set on a contact. Always provide meaningful fallbacks.

### Example with Conditional Layout

```html
<h1>Hi {{{contact.first_name|there}}}!</h1>

<p>Here's your personalized update:</p>

<table>
  <tr>
    <td>Plan:</td>
    <td>{{{contact.plan|Free}}}</td>
  </tr>
  <tr>
    <td>Company:</td>
    <td>{{{contact.company_name|—}}}</td>
  </tr>
</table>
```

## Broadcast Lifecycle

```
Draft → Queued → Sending → Sent
  │                          │
  └── Delete (drafts only)   └── View stats (delivered, opened, clicked)
  │
  └── Schedule → Scheduled → Sending → Sent
```

**Statuses:**
- `draft` — editable, not yet sent
- `scheduled` — queued for future delivery
- `sending` — actively being delivered
- `sent` — delivery complete

You can only edit or delete broadcasts in `draft` status.

### Update a Draft

```typescript
await resend.broadcasts.update('broadcast_xxxxx', {
  subject: 'Updated Subject',
  html: '<p>Updated content</p>',
});
```

### Delete a Draft

```typescript
await resend.broadcasts.remove('broadcast_xxxxx');
```

### List Broadcasts

```typescript
const { data } = await resend.broadcasts.list();
// data.data: [{ id, name, audience_id, from, subject, status, created_at }]
```

## Dashboard Editor

The Resend dashboard includes a visual broadcast editor:

1. Go to **Audiences** → select your audience
2. Click **Create Broadcast**
3. Use the visual editor to compose your email
4. Preview across email clients
5. Send immediately or schedule

The editor supports:
- Rich text editing
- Image insertion
- Contact property insertion
- Preview text configuration
- Subject line editing
- Sender address selection

## Code Examples

### Weekly Newsletter Pipeline

```typescript
async function sendWeeklyNewsletter(audienceId: string) {
  const content = await generateNewsletterContent();

  const { data: broadcast } = await resend.broadcasts.create({
    segmentId: audienceId,
    from: 'Weekly <newsletter@yourdomain.com>',
    subject: `Week of ${new Date().toLocaleDateString()}`,
    replyTo: 'feedback@yourdomain.com',
    html: content,
    send: true,
  });

  console.log(`Newsletter sent: ${broadcast.id}`);
  return broadcast.id;
}
```

### A/B Test Subject Lines

```typescript
async function abTestBroadcast(audienceId: string, html: string) {
  const subjects = [
    'New features you will love',
    'This week in product updates',
  ];

  for (const [i, subject] of subjects.entries()) {
    await resend.broadcasts.create({
      segmentId: `seg_test_${i}`, // Pre-created test segments
      from: 'News <news@yourdomain.com>',
      subject,
      html,
      send: true,
    });
  }
}
```

### Scheduled Product Launch

```typescript
await resend.broadcasts.create({
  segmentId: 'seg_all_subscribers',
  from: 'Launch <hello@yourdomain.com>',
  subject: 'Introducing Our New Product',
  html: `
    <h1>Hi {{{contact.first_name|there}}}!</h1>
    <p>We are thrilled to announce our new product.</p>
    <a href="https://yourdomain.com/new-product">Learn More</a>
  `,
  send: true,
  scheduledAt: '2026-06-15T14:00:00Z',
});
```

## Common Pitfalls

1. **No audience** — broadcasts require a segment or audience ID. You cannot send to arbitrary emails.
2. **Editing sent broadcasts** — only drafts can be updated. Sent broadcasts are immutable.
3. **Missing fallbacks in templates** — `{{{contact.name}}}` without a fallback shows nothing if the property is missing. Always use `{{{contact.name|Friend}}}`.
4. **Double-brace vs triple-brace** — Resend uses triple braces `{{{...}}}` for contact properties, not double braces.
5. **Sending to full audience without segmentation** — for large audiences, use segments to target relevant contacts.
6. **Not previewing** — always preview broadcasts before sending. Dashboard shows how personalization renders.
