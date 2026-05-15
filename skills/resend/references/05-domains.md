# Domains & Deliverability

> Source: https://resend.com/docs/dashboard/domains/introduction

## Table of Contents
- [Overview](#overview)
- [Domain API Endpoints](#domain-api-endpoints)
- [Adding a Domain](#adding-a-domain)
- [DNS Records](#dns-records)
- [Verification Process](#verification-process)
- [SPF Configuration](#spf-configuration)
- [DKIM Configuration](#dkim-configuration)
- [DMARC Configuration](#dmarc-configuration)
- [Custom Return-Path](#custom-return-path)
- [Multiple Domains](#multiple-domains)
- [Deliverability Best Practices](#deliverability-best-practices)
- [Common Pitfalls](#common-pitfalls)

## Overview

Domain verification is required before sending emails from your own domain. Resend handles SPF and DKIM configuration automatically — you add the DNS records Resend generates, and they verify them. This ensures your emails pass authentication checks and reach inboxes.

**Without domain verification**, you can only send from the shared `onboarding@resend.dev` address (for testing only).

## Domain API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/domains` | Add a new domain |
| `GET` | `/domains` | List all domains |
| `GET` | `/domains/:id` | Get domain details and DNS records |
| `PATCH` | `/domains/:id` | Update domain settings |
| `DELETE` | `/domains/:id` | Remove a domain |
| `POST` | `/domains/:id/verify` | Trigger DNS verification |

### SDK Methods

```typescript
const domain = await resend.domains.create({ name: 'yourdomain.com' });
const domains = await resend.domains.list();
const details = await resend.domains.get(domainId);
await resend.domains.update(domainId, { openTracking: true });
await resend.domains.verify(domainId);
await resend.domains.remove(domainId);
```

```python
domain = resend.Domains.create({"name": "yourdomain.com"})
domains = resend.Domains.list()
details = resend.Domains.get(domain_id)
resend.Domains.verify(domain_id)
resend.Domains.remove(domain_id)
```

## Adding a Domain

### Via Dashboard

1. Navigate to **Domains** in the Resend dashboard
2. Click **Add Domain**
3. Enter your domain name (e.g., `yourdomain.com`)
4. Choose the region (US or EU)
5. Resend generates DNS records for you to add

### Via API

```typescript
const { data } = await resend.domains.create({
  name: 'yourdomain.com',
  region: 'us-east-1', // or 'eu-west-1'
});

// data.records contains the DNS records to add
```

## DNS Records

When you add a domain, Resend generates these records:

| Type | Name | Value | Purpose |
|------|------|-------|---------|
| TXT | `yourdomain.com` | `v=spf1 include:_spf.resend.com -all` | SPF authentication |
| CNAME | `resend._domainkey.yourdomain.com` | `(provided by Resend)` | DKIM signing |
| CNAME | `(provided)` | `(provided by Resend)` | DKIM signing (second key) |
| MX | `(subdomain, if using inbound)` | `(provided by Resend)` | Inbound email receiving |

Add these records at your DNS provider (Cloudflare, Route 53, Namecheap, GoDaddy, Vercel, etc.).

## Verification Process

1. Add DNS records at your provider
2. Click **Verify DNS Records** in the dashboard (or call the verify API)
3. Resend queries your DNS and checks each record
4. Status changes to **Verified** (green) when all records are confirmed
5. DNS propagation can take up to 24–48 hours (typically minutes)

```typescript
// Trigger verification via API
await resend.domains.verify(domainId);
```

You can also check domain status:

```typescript
const domain = await resend.domains.get(domainId);
console.log(domain.data.status); // 'pending' | 'verified' | 'failed'
```

## SPF Configuration

SPF (Sender Policy Framework) specifies which mail servers can send on behalf of your domain.

**Record:**
```
Type: TXT
Name: yourdomain.com (or @)
Value: v=spf1 include:_spf.resend.com -all
```

**If you already have an SPF record**, merge the `include`:
```
v=spf1 include:_spf.google.com include:_spf.resend.com -all
```

- `v=spf1` — SPF version
- `include:_spf.resend.com` — authorizes Resend to send
- `-all` — reject mail from unauthorized servers (`~all` for soft fail)

## DKIM Configuration

DKIM (DomainKeys Identified Mail) adds a cryptographic signature to verify email authenticity.

Resend provides CNAME records that point to their DKIM keys. This means key rotation is handled automatically by Resend — you never need to update the DNS records.

**Records (2 CNAME records):**
```
Type: CNAME
Name: resend._domainkey.yourdomain.com
Value: (provided by Resend)

Type: CNAME
Name: (provided by Resend)
Value: (provided by Resend)
```

Resend supports custom DKIM signing domains, enabling DMARC compliance via DKIM alignment.

## DMARC Configuration

DMARC builds on SPF and DKIM to define a policy for handling authentication failures. While optional, it significantly improves deliverability and protects against spoofing.

**Recommended record:**
```
Type: TXT
Name: _dmarc.yourdomain.com
Value: v=DMARC1; p=quarantine; rua=mailto:dmarc@yourdomain.com
```

**Policy options:**
- `p=none` — monitor only, no enforcement (start here)
- `p=quarantine` — send failing emails to spam
- `p=reject` — block failing emails entirely

**Gradual rollout:**
1. Start with `p=none` and `rua=mailto:...` to collect reports
2. Review reports to ensure legitimate emails pass
3. Move to `p=quarantine` then `p=reject`

## Custom Return-Path

By default, bounces go to Resend's servers. You can configure a custom return-path for your own bounce handling. This is set up automatically when you verify your domain and helps with SPF alignment.

## Multiple Domains

You can verify multiple domains for different use cases:

- `marketing.yourdomain.com` — for newsletters and broadcasts
- `transactional.yourdomain.com` — for order confirmations, password resets
- `yourdomain.com` — general email

Each domain gets its own DNS records and verification status.

```typescript
// Send from different domains
await resend.emails.send({
  from: 'Team <hello@marketing.yourdomain.com>',
  to: 'user@example.com',
  subject: 'Newsletter',
  html: '...',
});
```

## Deliverability Best Practices

1. **Verify your domain** — never use `onboarding@resend.dev` in production
2. **Set up DMARC** — even `p=none` improves trust signals
3. **Warm up new domains** — start with small volumes and increase gradually
4. **Monitor bounces** — remove hard-bounced addresses immediately
5. **Handle complaints** — unsubscribe users who mark emails as spam
6. **Include unsubscribe links** — required by CAN-SPAM and GDPR
7. **Use consistent sender names** — recipients recognize trusted senders
8. **Avoid spam trigger words** — "FREE!!!", excessive caps, misleading subjects
9. **Keep lists clean** — remove inactive contacts after 6 months
10. **Send from subdomains** — isolate transactional from marketing reputation

## Common Pitfalls

1. **Not verifying domain before go-live** — emails from unverified domains are rejected.
2. **Conflicting SPF records** — only one SPF record per domain. Merge `include:` directives.
3. **CNAME at root domain** — some DNS providers don't support CNAME at the root. Use ALIAS or ANAME if available.
4. **Impatient verification** — DNS propagation takes time. Wait 15–30 minutes before retrying.
5. **Forgetting DMARC** — not required but strongly recommended for inbox placement.
6. **Hard-coding `onboarding@resend.dev`** — test-only sender, not for production use.
