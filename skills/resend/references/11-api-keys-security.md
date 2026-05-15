# API Keys & Security

> Source: https://resend.com/docs/knowledge-base/how-to-handle-api-keys

## Table of Contents
- [API Key Management](#api-key-management)
- [Permission Levels](#permission-levels)
- [API Key Endpoints](#api-key-endpoints)
- [Rate Limits](#rate-limits)
- [Error Codes](#error-codes)
- [Security Best Practices](#security-best-practices)
- [Environment Configuration](#environment-configuration)
- [Webhook Security](#webhook-security)
- [Common Pitfalls](#common-pitfalls)

## API Key Management

API keys authenticate your application with the Resend API. Every request must include an `Authorization: Bearer re_xxxxx` header.

**Key format:** All Resend API keys start with `re_` prefix.

**Key visibility:** API keys are shown only once at creation. Store them securely immediately.

### Create via Dashboard

1. Go to **API Keys** in the Resend dashboard
2. Click **Create API Key**
3. Name the key (e.g., "Production", "Staging")
4. Choose permission level
5. Copy the key — it won't be shown again

### Create via API

```typescript
const { data } = await resend.apiKeys.create({
  name: 'Production API Key',
  permission: 'full_access',
});

console.log(data.token); // re_xxxxx — store this securely!
```

## Permission Levels

| Permission | Can Send | Can Manage Resources | Domain Restriction |
|-----------|----------|---------------------|-------------------|
| `full_access` | Yes | Yes (domains, audiences, webhooks, API keys) | No |
| `sending_access` | Yes | No | Optional |

### Sending-Only Key with Domain Restriction

```typescript
const { data } = await resend.apiKeys.create({
  name: 'Marketing Sender',
  permission: 'sending_access',
  domainId: 'domain_xxxxx', // Restricts to this domain only
});
```

This key can only send emails from the specified domain. Useful for isolating different services or environments.

## API Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api-keys` | Create a new API key |
| `GET` | `/api-keys` | List all API keys |
| `DELETE` | `/api-keys/:id` | Delete an API key |

### List Keys

```typescript
const { data } = await resend.apiKeys.list();
// data: [{ id, name, created_at }]
// Note: the actual key value is NOT returned in list
```

### Delete Key

```typescript
await resend.apiKeys.remove('api_key_id');
```

### Python

```python
key = resend.ApiKeys.create({"name": "Staging", "permission": "sending_access"})
keys = resend.ApiKeys.list()
resend.ApiKeys.remove("api_key_id")
```

## Rate Limits

| Limit | Value |
|-------|-------|
| API requests | 2 per second (default) |
| Batch size | 100 emails per request |
| Recipients per email | 50 (`to` + `cc` + `bcc`) |
| Attachment size | 40 MB total per email |
| Scheduled ahead | 30 days maximum |
| Idempotency key TTL | 24 hours |
| Free tier volume | 3,000 emails/month |

**Rate limit response:**

```json
{
  "statusCode": 429,
  "name": "rate_limit_exceeded",
  "message": "Rate limit exceeded. Please retry after 1 second."
}
```

**Headers returned:**
- `X-RateLimit-Limit` — requests allowed per window
- `X-RateLimit-Remaining` — requests remaining
- `X-RateLimit-Reset` — seconds until window resets

### Handling Rate Limits

```typescript
async function sendWithRateLimit(
  emails: Array<Parameters<typeof resend.emails.send>[0]>
) {
  for (const email of emails) {
    const { data, error } = await resend.emails.send(email);

    if (error && (error as any).statusCode === 429) {
      await new Promise((r) => setTimeout(r, 1000));
      await resend.emails.send(email); // Retry once
    }
  }
}
```

## Error Codes

| Code | Name | Description | Action |
|------|------|-------------|--------|
| 400 | `bad_request` | Malformed request | Fix request format |
| 401 | `missing_api_key` | No or invalid API key | Check API key |
| 403 | `forbidden` | Key lacks permission | Use key with higher permission |
| 404 | `not_found` | Resource doesn't exist | Check resource ID |
| 409 | `idempotency_conflict` | Key reused with different payload | Use new idempotency key |
| 422 | `validation_error` | Invalid parameters | Fix parameter values |
| 429 | `rate_limit_exceeded` | Too many requests | Retry with backoff |
| 500 | `internal_server_error` | Server error | Retry with backoff |

### Error Response Format

```json
{
  "statusCode": 422,
  "name": "validation_error",
  "message": "The 'to' field must contain a valid email address."
}
```

### Comprehensive Error Handler

```typescript
function handleResendError(error: any): never {
  switch (error.name) {
    case 'validation_error':
      throw new Error(`Invalid email params: ${error.message}`);
    case 'missing_api_key':
      throw new Error('Resend API key not configured');
    case 'rate_limit_exceeded':
      throw new Error('Email rate limit hit — retry later');
    default:
      throw new Error(`Resend error: ${error.message}`);
  }
}
```

## Security Best Practices

1. **Never commit API keys** — use environment variables, not source code
2. **Use `sending_access` in production** — minimize permissions
3. **Restrict by domain** — lock sending keys to specific domains
4. **Rotate keys regularly** — delete unused keys older than 30 days
5. **Separate keys per environment** — production, staging, development
6. **Verify webhook signatures** — always validate Svix signatures
7. **Use HTTPS only** — all Resend endpoints require HTTPS
8. **Monitor key usage** — check dashboard for unexpected activity

### Key Rotation Pattern

```typescript
// 1. Create new key
const { data: newKey } = await resend.apiKeys.create({
  name: `Production ${new Date().toISOString().slice(0, 10)}`,
  permission: 'sending_access',
  domainId: 'domain_xxxxx',
});

// 2. Update environment variable with new key
// (deployment-specific: Vercel, Railway, etc.)

// 3. Delete old key after deployment
await resend.apiKeys.remove('old_key_id');
```

## Environment Configuration

### Node.js / Next.js

```bash
# .env.local
RESEND_API_KEY=re_xxxxx
RESEND_WEBHOOK_SECRET=whsec_xxxxx
```

```typescript
const resend = new Resend(process.env.RESEND_API_KEY);
```

### Python

```bash
# .env
RESEND_API_KEY=re_xxxxx
```

```python
import os
resend.api_key = os.environ["RESEND_API_KEY"]
```

### Cloudflare Workers

```bash
npx wrangler secret put RESEND_API_KEY
```

```typescript
const resend = new Resend(env.RESEND_API_KEY);
```

### Vercel

```bash
vercel env add RESEND_API_KEY
```

### Docker

```dockerfile
# docker-compose.yml
services:
  app:
    environment:
      - RESEND_API_KEY=${RESEND_API_KEY}
```

## Webhook Security

### Signature Verification

Always verify webhook signatures using the Svix library:

```typescript
import { Webhook } from 'svix';

const wh = new Webhook(process.env.RESEND_WEBHOOK_SECRET);
const event = wh.verify(rawBody, {
  'svix-id': headers['svix-id'],
  'svix-timestamp': headers['svix-timestamp'],
  'svix-signature': headers['svix-signature'],
});
```

### Timestamp Validation

Svix automatically rejects events older than 5 minutes, preventing replay attacks.

### IP Allowlisting

For additional security, you can allowlist Svix webhook IPs in your firewall. Check Svix documentation for their current IP ranges.

## Common Pitfalls

1. **Hardcoding API keys** — always use environment variables, never string literals.
2. **Using `full_access` everywhere** — use `sending_access` for services that only send emails.
3. **Not handling 429** — always implement retry with backoff for rate limits.
4. **Ignoring error responses** — always check `error` in Node SDK, catch exceptions in Python.
5. **Exposing keys client-side** — never use Resend API keys in browser/frontend code. Always call from server.
6. **Single key for all services** — create separate keys per service/environment for auditability and revocation.
