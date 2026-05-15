# Node.js SDK

> Source: https://github.com/resend/resend-node

## Table of Contents
- [Installation](#installation)
- [Initialization](#initialization)
- [Email Methods](#email-methods)
- [Batch Methods](#batch-methods)
- [Domain Methods](#domain-methods)
- [Audience Methods](#audience-methods)
- [Contact Methods](#contact-methods)
- [Broadcast Methods](#broadcast-methods)
- [Webhook Methods](#webhook-methods)
- [API Key Methods](#api-key-methods)
- [Contact Property Methods](#contact-property-methods)
- [Error Handling](#error-handling)
- [TypeScript Types](#typescript-types)
- [Common Patterns](#common-patterns)

## Installation

```bash
npm install resend
# or
yarn add resend
# or
pnpm add resend
```

## Initialization

```typescript
import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);
```

The SDK automatically uses `https://api.resend.com` as the base URL.

## Email Methods

### Send Email

```typescript
const { data, error } = await resend.emails.send({
  from: 'App <noreply@yourdomain.com>',
  to: ['user@example.com'],
  subject: 'Hello',
  html: '<p>Hello world</p>',
});

// With all options
const { data, error } = await resend.emails.send({
  from: 'App <noreply@yourdomain.com>',
  to: ['user@example.com'],
  cc: ['cc@example.com'],
  bcc: ['bcc@example.com'],
  replyTo: 'support@yourdomain.com',
  subject: 'Full Example',
  html: '<p>Content</p>',
  text: 'Content (plain text)',
  tags: [{ name: 'type', value: 'transactional' }],
  headers: { 'X-Custom': 'value' },
  attachments: [{ filename: 'file.pdf', content: Buffer.from('...') }],
  scheduledAt: 'in 1 hour',
});
```

### Send with React Component

```typescript
import { WelcomeEmail } from '@/emails/welcome';

const { data, error } = await resend.emails.send({
  from: 'App <noreply@yourdomain.com>',
  to: 'user@example.com',
  subject: 'Welcome',
  react: WelcomeEmail({ name: 'Alice' }),
});
```

### Send with Idempotency

```typescript
const { data, error } = await resend.emails.send(
  {
    from: 'App <noreply@yourdomain.com>',
    to: 'user@example.com',
    subject: 'Order #123',
    html: '<p>Confirmed</p>',
  },
  { idempotencyKey: 'order-confirm/123' }
);
```

### Get Email

```typescript
const { data, error } = await resend.emails.get('email_id');
// data: { id, from, to, subject, created_at, last_event, ... }
```

### Cancel Scheduled Email

```typescript
const { data, error } = await resend.emails.cancel('email_id');
```

## Batch Methods

```typescript
const { data, error } = await resend.batch.send([
  {
    from: 'App <noreply@yourdomain.com>',
    to: 'alice@example.com',
    subject: 'Hello Alice',
    html: '<p>Hi Alice</p>',
  },
  {
    from: 'App <noreply@yourdomain.com>',
    to: 'bob@example.com',
    subject: 'Hello Bob',
    html: '<p>Hi Bob</p>',
  },
]);

// With idempotency
const { data, error } = await resend.batch.send(emails, {
  idempotencyKey: 'batch/weekly-digest/2026-W20',
});
```

## Domain Methods

```typescript
// Create
const { data } = await resend.domains.create({ name: 'yourdomain.com' });

// List
const { data } = await resend.domains.list();

// Get (includes DNS records)
const { data } = await resend.domains.get('domain_id');

// Verify
const { data } = await resend.domains.verify('domain_id');

// Update
const { data } = await resend.domains.update('domain_id', {
  openTracking: true,
  clickTracking: true,
});

// Delete
const { data } = await resend.domains.remove('domain_id');
```

## Audience Methods

```typescript
const { data } = await resend.audiences.create({ name: 'Newsletter' });
const { data } = await resend.audiences.list();
const { data } = await resend.audiences.get('audience_id');
const { data } = await resend.audiences.remove('audience_id');
```

## Contact Methods

```typescript
// Create
const { data } = await resend.contacts.create({
  audienceId: 'aud_xxxxx',
  email: 'alice@example.com',
  firstName: 'Alice',
  lastName: 'Smith',
  unsubscribed: false,
  properties: { plan: 'pro' },
});

// List
const { data } = await resend.contacts.list({ audienceId: 'aud_xxxxx' });

// Get
const { data } = await resend.contacts.get({
  audienceId: 'aud_xxxxx',
  id: 'contact_id',
});

// Update
const { data } = await resend.contacts.update({
  audienceId: 'aud_xxxxx',
  id: 'contact_id',
  firstName: 'Alicia',
});

// Remove by ID
const { data } = await resend.contacts.remove({
  audienceId: 'aud_xxxxx',
  id: 'contact_id',
});

// Remove by email
const { data } = await resend.contacts.remove({
  audienceId: 'aud_xxxxx',
  email: 'alice@example.com',
});

// Segment operations
await resend.contacts.segments.add({ contactId: '...', segmentId: '...' });
await resend.contacts.segments.remove({ contactId: '...', segmentId: '...' });
```

## Broadcast Methods

```typescript
// Create (draft)
const { data } = await resend.broadcasts.create({
  segmentId: 'seg_xxxxx',
  from: 'News <news@yourdomain.com>',
  subject: 'Weekly Update',
  html: '<p>Content</p>',
});

// Create and send immediately
const { data } = await resend.broadcasts.create({
  segmentId: 'seg_xxxxx',
  from: 'News <news@yourdomain.com>',
  subject: 'Breaking News',
  html: '<p>Big announcement!</p>',
  send: true,
});

// Send draft
await resend.broadcasts.send('broadcast_id');

// Send with schedule
await resend.broadcasts.send('broadcast_id', {
  scheduledAt: 'tomorrow at 9am',
});

// List / Get / Update / Delete
const { data } = await resend.broadcasts.list();
const { data } = await resend.broadcasts.get('broadcast_id');
await resend.broadcasts.update('broadcast_id', { html: '<p>Updated</p>' });
await resend.broadcasts.remove('broadcast_id');
```

## Webhook Methods

```typescript
const { data } = await resend.webhooks.create({
  url: 'https://yourdomain.com/webhooks/resend',
  events: ['email.delivered', 'email.bounced'],
});

const { data } = await resend.webhooks.list();
const { data } = await resend.webhooks.get('webhook_id');
await resend.webhooks.update('webhook_id', { events: ['email.delivered'] });
await resend.webhooks.remove('webhook_id');
```

## API Key Methods

```typescript
const { data } = await resend.apiKeys.create({
  name: 'Production Key',
  permission: 'full_access', // or 'sending_access'
  domainId: 'domain_id', // optional, restricts to specific domain
});

const { data } = await resend.apiKeys.list();
await resend.apiKeys.remove('api_key_id');
```

## Contact Property Methods

```typescript
await resend.contactProperties.create({
  key: 'company_name',
  type: 'string',
  fallbackValue: 'your company',
});

const { data } = await resend.contactProperties.list();
const { data } = await resend.contactProperties.get('prop_id');
await resend.contactProperties.update({ id: 'prop_id', fallbackValue: 'N/A' });
await resend.contactProperties.remove('prop_id');
```

## Error Handling

All SDK methods return `{ data, error }`. Never throws — check for errors explicitly.

```typescript
const { data, error } = await resend.emails.send({
  from: 'App <noreply@yourdomain.com>',
  to: 'user@example.com',
  subject: 'Test',
  html: '<p>Test</p>',
});

if (error) {
  console.error('Resend error:', {
    name: error.name,        // 'validation_error', 'not_found', etc.
    message: error.message,  // Human-readable description
  });
  return;
}

console.log('Sent:', data.id);
```

**Error types:**

| Name | Code | Description |
|------|------|-------------|
| `validation_error` | 422 | Invalid parameters |
| `not_found` | 404 | Resource doesn't exist |
| `rate_limit_exceeded` | 429 | Too many requests |
| `internal_server_error` | 500 | Server error (retry) |
| `missing_api_key` | 401 | Invalid or missing API key |

## TypeScript Types

The SDK exports all parameter and response types:

```typescript
import type {
  CreateEmailOptions,
  CreateEmailResponse,
  CreateBatchEmailsOptions,
  GetEmailResponse,
} from 'resend';
```

## Common Patterns

### Wrapper Service

```typescript
class EmailService {
  private resend: Resend;

  constructor(apiKey: string) {
    this.resend = new Resend(apiKey);
  }

  async sendTransactional(to: string, template: string, data: Record<string, any>) {
    const templates: Record<string, (data: any) => JSX.Element> = {
      welcome: WelcomeEmail,
      reset: PasswordResetEmail,
      invoice: InvoiceEmail,
    };

    const Component = templates[template];
    if (!Component) throw new Error(`Unknown template: ${template}`);

    const { data: result, error } = await this.resend.emails.send({
      from: 'App <noreply@yourdomain.com>',
      to,
      subject: this.getSubject(template, data),
      react: Component(data),
      tags: [{ name: 'template', value: template }],
    });

    if (error) throw new Error(error.message);
    return result.id;
  }

  private getSubject(template: string, data: Record<string, any>): string {
    const subjects: Record<string, string> = {
      welcome: `Welcome, ${data.name}!`,
      reset: 'Reset your password',
      invoice: `Invoice #${data.invoiceId}`,
    };
    return subjects[template] ?? template;
  }
}
```
