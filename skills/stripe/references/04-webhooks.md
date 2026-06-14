# Stripe — Webhooks

> Source: [docs.stripe.com/webhooks](https://docs.stripe.com/webhooks) | API `2026-05-27.dahlia`

## Table of Contents

- [Overview](#overview)
- [Setting Up a Webhook Endpoint](#setting-up-a-webhook-endpoint)
- [Signature Verification](#signature-verification)
- [Node.js Implementation](#nodejs-implementation)
- [Python Implementation](#python-implementation)
- [Event Types](#event-types)
- [Thin Events vs Snapshot Events](#thin-events-vs-snapshot-events)
- [Retries and Reliability](#retries-and-reliability)
- [Best Practices](#best-practices)
- [Debugging](#debugging)
- [Common Pitfalls](#common-pitfalls)

## Overview

Webhooks deliver real-time HTTP POST notifications when events occur in your Stripe account (payments, subscriptions, disputes). They replace polling and enable event-driven architectures.

## Setting Up a Webhook Endpoint

### Via Dashboard

1. Go to **Workbench → Webhooks**
2. Click **Create an event destination**
3. Enter your endpoint URL (must be HTTPS in production)
4. Select event types to receive
5. Save — note the `whsec_` signing secret

### Via API

```bash
curl -X POST https://api.stripe.com/v2/core/event_destinations \
  -H "Authorization: Bearer sk_live_..." \
  --json '{
    "name": "Production webhook",
    "type": "webhook_endpoint",
    "enabled_events": [
      "payment_intent.succeeded",
      "invoice.paid",
      "customer.subscription.deleted"
    ],
    "webhook_endpoint": {
      "url": "https://example.com/webhook"
    }
  }'
```

## Signature Verification

**Always verify webhook signatures** to prevent attackers from sending fake events.

The `Stripe-Signature` header contains:
```
t=1492774577,v1=5257a869...,v0=...
```

Verification steps:
1. Extract timestamp (`t`) and signature (`v1`) from header
2. Create `signed_payload = "{timestamp}.{json_body}"`
3. Compute HMAC-SHA256 with webhook secret
4. Compare signatures using constant-time comparison

Use the SDK — it handles this automatically.

## Node.js Implementation

```javascript
const express = require("express");
const stripe = require("stripe")(process.env.STRIPE_SECRET_KEY);

const app = express();

app.post(
  "/webhook",
  express.raw({ type: "application/json" }),
  (req, res) => {
    const sig = req.headers["stripe-signature"];

    let event;
    try {
      event = stripe.webhooks.constructEvent(
        req.body,
        sig,
        process.env.STRIPE_WEBHOOK_SECRET
      );
    } catch (err) {
      console.error(`Signature verification failed: ${err.message}`);
      return res.status(400).send(`Webhook Error: ${err.message}`);
    }

    switch (event.type) {
      case "payment_intent.succeeded":
        const paymentIntent = event.data.object;
        handlePaymentSuccess(paymentIntent);
        break;

      case "payment_intent.payment_failed":
        const failedIntent = event.data.object;
        handlePaymentFailure(failedIntent);
        break;

      case "customer.subscription.created":
        const subscription = event.data.object;
        provisionSubscription(subscription);
        break;

      case "customer.subscription.deleted":
        const canceledSub = event.data.object;
        revokeAccess(canceledSub);
        break;

      case "invoice.paid":
        const invoice = event.data.object;
        fulfillOrder(invoice);
        break;

      default:
        console.log(`Unhandled event type: ${event.type}`);
    }

    res.json({ received: true });
  }
);

app.listen(4242);
```

**Important:** Use `express.raw()` for the webhook route — `express.json()` will modify the body and break signature verification.

## Python Implementation

```python
import os
from flask import Flask, request, jsonify
from stripe import StripeClient

app = Flask(__name__)
client = StripeClient(os.environ["STRIPE_SECRET_KEY"])
webhook_secret = os.environ["STRIPE_WEBHOOK_SECRET"]

@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = client.parse_event_notification(
            payload, sig_header, webhook_secret
        )
    except Exception as e:
        return jsonify(error=str(e)), 400

    if event.type == "payment_intent.succeeded":
        payment_intent = event.data.object
        handle_payment_success(payment_intent)

    elif event.type == "invoice.paid":
        invoice = event.data.object
        fulfill_order(invoice)

    elif event.type == "customer.subscription.deleted":
        subscription = event.data.object
        revoke_access(subscription)

    return jsonify(success=True), 200
```

## Event Types

### Payment Events

| Event | Description |
|-------|-------------|
| `payment_intent.created` | PaymentIntent created |
| `payment_intent.succeeded` | Payment completed |
| `payment_intent.payment_failed` | Payment failed |
| `payment_intent.canceled` | PaymentIntent canceled |
| `charge.succeeded` | Charge succeeded |
| `charge.failed` | Charge failed |
| `charge.refunded` | Charge refunded |
| `charge.dispute.created` | Dispute opened |

### Subscription Events

| Event | Description |
|-------|-------------|
| `customer.subscription.created` | Subscription created |
| `customer.subscription.updated` | Subscription modified |
| `customer.subscription.deleted` | Subscription canceled |
| `customer.subscription.trial_will_end` | Trial ending (3 days notice) |
| `invoice.created` | Invoice generated |
| `invoice.paid` | Invoice payment succeeded |
| `invoice.payment_failed` | Invoice payment failed |

### Checkout Events

| Event | Description |
|-------|-------------|
| `checkout.session.completed` | Checkout completed |
| `checkout.session.expired` | Checkout session expired |

### Customer Events

| Event | Description |
|-------|-------------|
| `customer.created` | Customer created |
| `customer.updated` | Customer updated |
| `customer.deleted` | Customer deleted |
| `payment_method.attached` | Payment method saved |

## Thin Events vs Snapshot Events

### Snapshot Events (Default)

Full object data at the time of the event:

```python
event = client.parse_event_notification(payload, sig, secret)
payment_intent = event.data.object  # Full PaymentIntent object
```

### Thin Events (V2)

Minimal data — fetch the full object when needed:

```python
event = client.parse_event_notification(payload, sig, secret)
full_object = event.fetch_related_object()  # Fetch current state from API
```

Thin events reduce payload size and always give you the current object state.

## Retries and Reliability

| Environment | Retry Behavior |
|-------------|---------------|
| **Live mode** | Retries for up to 3 days with exponential backoff |
| **Sandbox** | 3 retry attempts over a few hours |

Stripe retries when your endpoint:
- Returns a non-2xx status code
- Times out (no response within timeout period)
- Is unreachable

### Manual Retry

```bash
# Via CLI (up to 30 days)
stripe events resend evt_xxx --webhook-endpoint=we_xxx

# Via Dashboard (up to 15 days)
# Webhooks → Select event → Resend
```

## Best Practices

### 1. Return 2xx Immediately

```javascript
app.post("/webhook", express.raw({ type: "application/json" }), (req, res) => {
  const event = verifyAndParse(req);
  
  // Return immediately
  res.json({ received: true });
  
  // Process asynchronously
  processEventAsync(event);
});
```

### 2. Handle Duplicates (Idempotency)

```javascript
const processedEvents = new Set();

function handleEvent(event) {
  if (processedEvents.has(event.id)) return;
  processedEvents.add(event.id);
  // Process event...
}
```

In production, use a database to track processed event IDs.

### 3. Handle Out-of-Order Events

Stripe does not guarantee event delivery order. Design handlers that work regardless of order:

```javascript
case "customer.subscription.updated":
  // Don't assume subscription.created was already processed
  // Fetch the current subscription state from the API if needed
  const current = await stripe.subscriptions.retrieve(event.data.object.id);
  updateDatabase(current);
  break;
```

### 4. Subscribe Only to Needed Events

```bash
stripe listen --events payment_intent.succeeded,invoice.paid \
  --forward-to localhost:4242/webhook
```

### 5. Roll Secrets Periodically

In Dashboard: **Webhooks → endpoint → Roll secret**. During transition, Stripe signs with both old and new secrets.

## Debugging

### Common HTTP Errors

| Status | Issue | Fix |
|--------|-------|-----|
| ERR (connection) | Endpoint not publicly accessible | Expose endpoint or use `stripe listen` for local dev |
| 302 | Redirect | Use the final URL directly |
| 400 | Client error | Check endpoint accepts POST |
| 500 | Server error | Check application logs |
| TLS error | Certificate issue | Ensure TLS 1.2+ and valid certificate |
| Timeout | Handler too slow | Return 2xx immediately, process async |

### Test Locally with Stripe CLI

```bash
# Forward all events
stripe listen --forward-to localhost:4242/webhook

# Forward specific events
stripe listen --events payment_intent.succeeded,invoice.paid \
  --forward-to localhost:4242/webhook

# Trigger a test event
stripe trigger payment_intent.succeeded
```

## Common Pitfalls

- **Using `express.json()` on the webhook route** — Breaks signature verification; use `express.raw({ type: "application/json" })`
- **Not verifying signatures** — Always verify; never trust unverified webhooks
- **Blocking the response** — Return 2xx immediately; Stripe times out if you do heavy processing synchronously
- **Assuming event order** — Events may arrive out of order; don't depend on sequence
- **Using the webhook secret as API key** — The `whsec_` secret is only for signature verification
- **Not handling duplicates** — The same event may be delivered multiple times
