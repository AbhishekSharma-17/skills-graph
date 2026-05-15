# Batch Emails & Idempotency

> Source: https://resend.com/docs/api-reference/emails/send-batch-emails

## Table of Contents
- [Batch Send Endpoint](#batch-send-endpoint)
- [Batch Parameters](#batch-parameters)
- [Batch Limitations](#batch-limitations)
- [Idempotency Keys](#idempotency-keys)
- [Idempotency in Batch](#idempotency-in-batch)
- [Retry Patterns](#retry-patterns)
- [Code Examples](#code-examples)
- [Common Pitfalls](#common-pitfalls)

## Batch Send Endpoint

Send up to 100 distinct emails in a single API call.

```
POST https://api.resend.com/emails/batch
Authorization: Bearer re_xxxxx
Content-Type: application/json
```

**Request body:** An array of email objects (same schema as single send, minus `attachments` and `scheduled_at`).

**Response:**

```json
{
  "data": [
    { "id": "ae2014de-c168-4c61-8267-70d2662a1ce1" },
    { "id": "bf3024ef-d279-5d72-9378-81e3773b2df2" }
  ]
}
```

## Batch Parameters

Each email in the array accepts:

| Parameter | Type | Required |
|-----------|------|----------|
| `from` | string | Yes |
| `to` | string \| string[] | Yes |
| `subject` | string | Yes |
| `html` or `text` | string | Yes (at least one) |
| `cc` | string \| string[] | No |
| `bcc` | string \| string[] | No |
| `reply_to` | string \| string[] | No |
| `tags` | Tag[] | No |
| `headers` | object | No |

## Batch Limitations

- **Maximum 100 emails** per request
- **No attachments** — use individual `/emails` endpoint for attachments
- **No scheduling** (`scheduled_at` not supported) — use individual sends
- **No `react` parameter** — render React Email to HTML first
- **Atomic validation** — if any email in the batch fails validation, the entire batch is rejected

## Idempotency Keys

Idempotency keys prevent duplicate email sends when retrying failed requests.

**How it works:**
1. Include an `Idempotency-Key` header with your request
2. If Resend receives a second request with the same key within 24 hours, it returns the original response without resending
3. Keys expire after 24 hours

**Key rules:**
- Maximum 256 characters
- Must be unique per distinct email operation
- Same key + same payload = returns cached response (no resend)
- Same key + different payload = returns `409 Conflict` error

### Single Email Idempotency

```typescript
const { data, error } = await resend.emails.send(
  {
    from: 'App <noreply@yourdomain.com>',
    to: 'user@example.com',
    subject: 'Order Confirmation',
    html: '<p>Order #1234 confirmed.</p>',
  },
  {
    idempotencyKey: 'order-confirmation/order_1234',
  }
);
```

### cURL with Idempotency

```bash
curl -X POST 'https://api.resend.com/emails' \
  -H 'Authorization: Bearer re_xxxxx' \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: order-confirmation/order_1234' \
  -d '{
    "from": "App <noreply@yourdomain.com>",
    "to": ["user@example.com"],
    "subject": "Order Confirmation",
    "html": "<p>Order #1234 confirmed.</p>"
  }'
```

## Idempotency in Batch

```typescript
const { data, error } = await resend.batch.send(
  [
    {
      from: 'App <noreply@yourdomain.com>',
      to: 'alice@example.com',
      subject: 'Weekly Report',
      html: '<p>Your weekly summary.</p>',
    },
    {
      from: 'App <noreply@yourdomain.com>',
      to: 'bob@example.com',
      subject: 'Weekly Report',
      html: '<p>Your weekly summary.</p>',
    },
  ],
  {
    idempotencyKey: 'weekly-report/2026-05-12',
  }
);
```

**Recommended key patterns:**

| Use Case | Key Pattern |
|----------|-------------|
| Order confirmation | `order-confirmation/order_1234` |
| Password reset | `password-reset/user_abc/1715000000` |
| Weekly digest | `weekly-digest/2026-W20` |
| Batch notification | `batch-notification/event_xyz` |

## Retry Patterns

### Exponential Backoff with Idempotency

```typescript
async function sendWithRetry(
  params: Parameters<typeof resend.emails.send>[0],
  idempotencyKey: string,
  maxRetries = 3
) {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const { data, error } = await resend.emails.send(params, {
      idempotencyKey,
    });

    if (data) return data;

    if (error) {
      const statusCode = (error as any).statusCode;

      // Don't retry client errors (except rate limits)
      if (statusCode >= 400 && statusCode < 500 && statusCode !== 429) {
        throw new Error(`Client error: ${error.message}`);
      }

      // Retry on 429 (rate limit) and 5xx (server errors)
      if (attempt < maxRetries) {
        const delay = Math.pow(2, attempt) * 1000;
        await new Promise((r) => setTimeout(r, delay));
        continue;
      }
    }

    throw new Error(`Failed after ${maxRetries + 1} attempts`);
  }
}
```

### Python Retry

```python
import time
import resend

def send_with_retry(params, idempotency_key, max_retries=3):
    for attempt in range(max_retries + 1):
        try:
            return resend.Emails.send(
                params,
                idempotency_key=idempotency_key,
            )
        except resend.exceptions.ResendError as e:
            if e.status_code and 400 <= e.status_code < 500 and e.status_code != 429:
                raise
            if attempt < max_retries:
                time.sleep(2 ** attempt)
                continue
            raise
```

## Code Examples

### Bulk Welcome Emails

```typescript
const newUsers = [
  { email: 'alice@example.com', name: 'Alice' },
  { email: 'bob@example.com', name: 'Bob' },
  { email: 'charlie@example.com', name: 'Charlie' },
];

const emails = newUsers.map((user) => ({
  from: 'App <welcome@yourdomain.com>',
  to: user.email,
  subject: `Welcome, ${user.name}!`,
  html: `<h1>Hi ${user.name}</h1><p>Welcome to our platform.</p>`,
  tags: [{ name: 'type', value: 'welcome' }],
}));

const { data, error } = await resend.batch.send(emails);
```

### Chunked Batch (>100 emails)

```typescript
function chunk<T>(arr: T[], size: number): T[][] {
  return Array.from({ length: Math.ceil(arr.length / size) }, (_, i) =>
    arr.slice(i * size, (i + 1) * size)
  );
}

async function sendBulk(emails: EmailParams[]) {
  const chunks = chunk(emails, 100);
  const results = [];

  for (const [i, batch] of chunks.entries()) {
    const { data, error } = await resend.batch.send(batch, {
      idempotencyKey: `bulk-send/batch_${i}/${Date.now()}`,
    });

    if (error) throw error;
    results.push(...data);

    // Respect rate limits between batches
    if (i < chunks.length - 1) {
      await new Promise((r) => setTimeout(r, 1000));
    }
  }

  return results;
}
```

## Common Pitfalls

1. **Exceeding 100 emails per batch** — split into chunks of 100.
2. **Using `react` in batch** — render to HTML first with `render()` from `@react-email/render`.
3. **Reusing idempotency keys** — each distinct send needs a unique key. Include timestamps or entity IDs.
4. **Changing payload with same key** — returns `409 Conflict`. Use a new key if the content changed.
5. **Not handling partial failures** — batch validation is atomic, but delivery is per-email. Check individual email statuses via webhooks.
6. **Ignoring rate limits** — add delays between batch calls when sending thousands of emails.
