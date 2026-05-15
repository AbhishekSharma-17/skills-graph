# Sending Emails

> Source: https://resend.com/docs/api-reference/emails/send-email

## Table of Contents
- [Send Email Endpoint](#send-email-endpoint)
- [Required Parameters](#required-parameters)
- [Optional Parameters](#optional-parameters)
- [Content Types](#content-types)
- [Attachments](#attachments)
- [Scheduling](#scheduling)
- [Tags](#tags)
- [Custom Headers](#custom-headers)
- [Reply-To](#reply-to)
- [Response Format](#response-format)
- [Retrieving Sent Emails](#retrieving-sent-emails)
- [Canceling Scheduled Emails](#canceling-scheduled-emails)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## Send Email Endpoint

```
POST https://api.resend.com/emails
Authorization: Bearer re_xxxxx
Content-Type: application/json
```

## Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `from` | string | Sender address. Format: `Name <email@domain.com>` or `email@domain.com` |
| `to` | string \| string[] | Recipient(s). Maximum 50 recipients. |
| `subject` | string | Email subject line. |

You must include at least one of: `html`, `text`, or `react` (Node.js SDK only).

## Optional Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `html` | string | HTML body content |
| `text` | string | Plain text body (fallback for non-HTML clients) |
| `react` | ReactElement | React Email component (Node.js SDK only) |
| `cc` | string \| string[] | Carbon copy recipients |
| `bcc` | string \| string[] | Blind carbon copy recipients |
| `reply_to` | string \| string[] | Reply-to address(es) |
| `scheduled_at` | string | ISO 8601 date or natural language. Up to 30 days ahead. |
| `attachments` | Attachment[] | File attachments (40MB total limit) |
| `tags` | Tag[] | Key-value pairs for categorization |
| `headers` | object | Custom email headers |

## Content Types

### HTML Content

```typescript
await resend.emails.send({
  from: 'App <noreply@yourdomain.com>',
  to: 'user@example.com',
  subject: 'Order Confirmation',
  html: '<h1>Order #1234</h1><p>Your order has been confirmed.</p>',
});
```

### Plain Text

```typescript
await resend.emails.send({
  from: 'App <noreply@yourdomain.com>',
  to: 'user@example.com',
  subject: 'Order Confirmation',
  text: 'Order #1234 - Your order has been confirmed.',
});
```

### React Email Component (Node.js only)

```typescript
import { WelcomeEmail } from '@/emails/welcome';

await resend.emails.send({
  from: 'App <noreply@yourdomain.com>',
  to: 'user@example.com',
  subject: 'Welcome!',
  react: WelcomeEmail({ name: 'Alice' }),
});
```

### Combined HTML + Text

```typescript
await resend.emails.send({
  from: 'App <noreply@yourdomain.com>',
  to: 'user@example.com',
  subject: 'Update',
  html: '<h1>New Feature</h1><p>Check out our new feature.</p>',
  text: 'New Feature - Check out our new feature.',
});
```

## Attachments

Attachments support two formats: file path or inline content.

```typescript
// Inline content (Buffer or base64)
await resend.emails.send({
  from: 'App <noreply@yourdomain.com>',
  to: 'user@example.com',
  subject: 'Invoice',
  html: '<p>Please find your invoice attached.</p>',
  attachments: [
    {
      filename: 'invoice.pdf',
      content: Buffer.from(pdfBytes),
    },
  ],
});

// Remote URL
await resend.emails.send({
  from: 'App <noreply@yourdomain.com>',
  to: 'user@example.com',
  subject: 'Report',
  html: '<p>Your report is attached.</p>',
  attachments: [
    {
      filename: 'report.pdf',
      path: 'https://example.com/report.pdf',
    },
  ],
});
```

**Attachment limits:**
- Maximum total size: 40MB
- Not supported in batch emails — use individual sends
- `content` accepts Buffer, ArrayBuffer, or base64 string
- `path` accepts a URL (Resend fetches the file)

## Scheduling

Schedule emails up to 30 days in advance using ISO 8601 or natural language.

```typescript
// ISO 8601 format
await resend.emails.send({
  from: 'App <noreply@yourdomain.com>',
  to: 'user@example.com',
  subject: 'Reminder',
  html: '<p>Your trial expires tomorrow.</p>',
  scheduled_at: '2026-06-01T09:00:00Z',
});

// Natural language
await resend.emails.send({
  from: 'App <noreply@yourdomain.com>',
  to: 'user@example.com',
  subject: 'Follow Up',
  html: '<p>How are you finding the product?</p>',
  scheduled_at: 'in 2 hours',
});
```

**Natural language examples:** `"in 1 hour"`, `"tomorrow at 9am"`, `"Friday at 3pm ET"`, `"in 30 minutes"`.

**Constraints:** Not available in batch emails. Maximum 30 days ahead.

## Tags

Attach key-value tags for filtering and analytics.

```typescript
await resend.emails.send({
  from: 'App <noreply@yourdomain.com>',
  to: 'user@example.com',
  subject: 'Welcome',
  html: '<p>Welcome!</p>',
  tags: [
    { name: 'category', value: 'onboarding' },
    { name: 'user_id', value: 'usr_abc123' },
  ],
});
```

Tags appear in webhook payloads and can be used to filter in the dashboard.

## Custom Headers

```typescript
await resend.emails.send({
  from: 'App <noreply@yourdomain.com>',
  to: 'user@example.com',
  subject: 'Thread Reply',
  html: '<p>Reply content</p>',
  headers: {
    'X-Entity-Ref-ID': 'thread_123',
    'In-Reply-To': '<original-message-id@yourdomain.com>',
    'References': '<original-message-id@yourdomain.com>',
  },
});
```

Useful for email threading, custom tracking, and third-party integrations.

## Reply-To

```typescript
await resend.emails.send({
  from: 'noreply@yourdomain.com',
  to: 'user@example.com',
  subject: 'Support',
  html: '<p>We received your request.</p>',
  reply_to: 'support@yourdomain.com',
});

// Multiple reply-to addresses
await resend.emails.send({
  from: 'noreply@yourdomain.com',
  to: 'user@example.com',
  subject: 'Team Update',
  html: '<p>Project update.</p>',
  reply_to: ['alice@yourdomain.com', 'bob@yourdomain.com'],
});
```

## Response Format

**Success (200):**
```json
{
  "id": "ae2014de-c168-4c61-8267-70d2662a1ce1"
}
```

**Error (4xx/5xx):**
```json
{
  "statusCode": 422,
  "name": "validation_error",
  "message": "The 'to' field must contain a valid email address."
}
```

## Retrieving Sent Emails

```
GET https://api.resend.com/emails/:email_id
```

```typescript
const { data } = await resend.emails.get('ae2014de-c168-4c61-8267-70d2662a1ce1');
// data: { id, from, to, subject, created_at, last_event, ... }
```

## Canceling Scheduled Emails

```
POST https://api.resend.com/emails/:email_id/cancel
```

```typescript
await resend.emails.cancel('ae2014de-c168-4c61-8267-70d2662a1ce1');
```

Only works for emails with status `scheduled`. Already-sent emails cannot be canceled.

## Common Patterns

### Transactional with Error Handling

```typescript
async function sendWelcomeEmail(userEmail: string, userName: string) {
  const { data, error } = await resend.emails.send({
    from: 'App <welcome@yourdomain.com>',
    to: userEmail,
    subject: `Welcome, ${userName}!`,
    react: WelcomeEmail({ name: userName }),
    tags: [{ name: 'type', value: 'welcome' }],
  });

  if (error) {
    console.error('Failed to send welcome email:', error.message);
    throw new Error(`Email send failed: ${error.name}`);
  }

  return data.id;
}
```

### Scheduled Reminder

```typescript
await resend.emails.send({
  from: 'App <reminders@yourdomain.com>',
  to: 'user@example.com',
  subject: 'Your trial expires in 3 days',
  html: '<p>Upgrade now to keep your data.</p>',
  scheduled_at: 'in 3 days',
  tags: [{ name: 'type', value: 'trial-reminder' }],
});
```

## Common Pitfalls

1. **Using `onboarding@resend.dev` in production** — this is a test-only sender. Verify your own domain.
2. **Exceeding 50 recipients** — use batch API or broadcasts for larger sends.
3. **Attachments in batch** — not supported. Use individual sends for attachments.
4. **Missing `text` fallback** — always include plain text for clients that don't render HTML.
5. **Scheduling without timezone** — natural language defaults to UTC. Specify timezone explicitly: `"tomorrow at 9am ET"`.
6. **Not handling errors** — always destructure `{ data, error }` and handle failures.
