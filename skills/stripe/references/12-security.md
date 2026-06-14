# Stripe — Security & Compliance

> Source: [docs.stripe.com](https://docs.stripe.com) | API `2026-05-27.dahlia`

## Overview

Stripe handles the hard parts of PCI compliance. By using Stripe Elements or Checkout, card numbers never touch your server. However, proper security practices on your side are critical for protecting customers and your business.

## PCI Compliance

### PCI DSS Levels

| Level | Requirement |
|-------|------------|
| **SAQ A** (Stripe Elements/Checkout) | Simplest — card data never touches your server |
| **SAQ A-EP** (Custom card forms) | Moderate — your page hosts the form but Stripe tokenizes |
| **SAQ D** (Direct API) | Full PCI audit — you handle raw card numbers |

Using Stripe Elements or Checkout = **SAQ A** (simplest compliance).

### What Stripe Handles

- Encryption of card data in transit and at rest
- PCI Level 1 certification (highest level)
- Tokenization — raw card numbers are never exposed to your server
- Secure iframe isolation for payment inputs

### Your Responsibilities

- Serve your site over HTTPS
- Keep API keys secure
- Validate webhook signatures
- Don't log sensitive payment data
- Keep dependencies updated

## API Key Security

### Key Management Rules

| Rule | Details |
|------|---------|
| **Never expose secret keys** | `sk_test_` and `sk_live_` are server-side only |
| **Use environment variables** | Never hardcode keys in source code |
| **Use restricted keys** | Create keys with minimal permissions for specific services |
| **Rotate regularly** | Rotate keys periodically; Stripe supports seamless rotation |
| **Never commit to git** | Add `.env` to `.gitignore` |

### Restricted Keys

```javascript
// Create via Dashboard: Developers → API Keys → Create restricted key
// Permissions: per-resource read/write/none

// Example: Read-only key for reporting
// Can read charges and customers but cannot create payments
```

### Key Rotation

1. Generate new key in Dashboard
2. Update environment variables
3. Deploy with new key
4. Revoke old key

Both old and new keys work during the transition period.

## HTTPS Requirements

- **Required in production** for all Stripe integrations
- Stripe.js refuses to load on HTTP pages in production
- Use TLS 1.2 or higher
- Ensure valid SSL certificate (test with SSL Labs)

```nginx
# Nginx HTTPS redirect
server {
    listen 80;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
}
```

## Webhook Security

### Signature Verification

```javascript
const sig = req.headers["stripe-signature"];
const event = stripe.webhooks.constructEvent(
  req.body, // Raw body, not parsed JSON
  sig,
  process.env.STRIPE_WEBHOOK_SECRET
);
```

### Security Checklist

- [ ] Verify signatures on every webhook
- [ ] Use HTTPS for webhook endpoints
- [ ] Return 2xx quickly (process async)
- [ ] Handle duplicate events (idempotency)
- [ ] Roll webhook secrets periodically
- [ ] IP allowlist Stripe's webhook IPs (optional)
- [ ] Set CSRF exemption for webhook routes

### CSRF Exemption

```javascript
// Express: webhook route before json middleware
app.post("/webhook", express.raw({ type: "application/json" }), webhookHandler);
app.use(express.json()); // JSON parsing for other routes
```

```python
# Django: exempt webhook from CSRF
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def webhook(request):
    # ...
```

## SCA (Strong Customer Authentication)

Required in the European Economic Area (EEA) for online payments:

- Stripe automatically handles SCA when using Payment Element or Checkout
- 3D Secure is triggered when required by regulations or Radar rules
- Customer authentication happens in the browser (redirect or popup)

### Automatic SCA

```javascript
// Using Checkout Sessions — SCA handled automatically
const session = await stripe.checkout.sessions.create({
  mode: "payment",
  // ...
});

// Using PaymentIntents — SCA handled automatically with Elements
const pi = await stripe.paymentIntents.create({
  amount: 2000,
  currency: "eur",
  automatic_payment_methods: { enabled: true },
});
```

### Manual 3DS Request

```javascript
const pi = await stripe.paymentIntents.create({
  amount: 2000,
  currency: "eur",
  payment_method_options: {
    card: {
      request_three_d_secure: "any",
    },
  },
});
```

## Content Security Policy (CSP)

If you use CSP headers, allow Stripe's domains:

```
Content-Security-Policy:
  script-src 'self' https://js.stripe.com;
  frame-src 'self' https://js.stripe.com https://hooks.stripe.com;
  connect-src 'self' https://api.stripe.com;
```

## Data Privacy

### What Stripe Stores

- Card fingerprints (not full card numbers)
- Customer email, name, address
- Transaction history
- Device fingerprints (for Radar)

### What You Should NOT Store

- Full card numbers
- CVC/CVV codes
- Full magnetic stripe data
- PIN numbers

### GDPR Compliance

```javascript
// Delete customer data
await stripe.customers.del("cus_xxx");

// Export customer data
const customer = await stripe.customers.retrieve("cus_xxx", {
  expand: ["subscriptions", "sources"],
});
```

## Security Monitoring

### Dashboard Alerts

- Failed payment attempts
- Unusual activity patterns
- API key usage anomalies
- Webhook delivery failures

### Recommended Monitoring

| What | How |
|------|-----|
| API errors | `stripe logs tail --filter-status-code=400` |
| Failed webhooks | Dashboard → Webhooks → delivery status |
| Disputes | Listen for `charge.dispute.created` |
| Radar blocks | Monitor Radar dashboard for false positives |
| Key usage | Review restricted key access logs |

## Common Pitfalls

- **Logging card details** — Never log request bodies that might contain payment data
- **Serving Stripe.js from your own server** — Always load from `js.stripe.com`; self-hosting violates PCI compliance
- **Using `express.json()` on webhook routes** — Breaks signature verification; use `express.raw()`
- **Sharing API keys across environments** — Use separate keys for development, staging, and production
- **Not using HTTPS in production** — Stripe.js won't load on HTTP pages
- **Storing payment method details** — Let Stripe store them; use PaymentMethod IDs in your database
