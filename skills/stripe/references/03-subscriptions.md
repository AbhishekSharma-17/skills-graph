# Stripe — Subscriptions & Billing

> Source: [docs.stripe.com/billing](https://docs.stripe.com/billing) | API `2026-05-27.dahlia`

## Table of Contents

- [Overview](#overview)
- [Pricing Models](#pricing-models)
- [Creating Products and Prices](#creating-products-and-prices)
- [Building a Subscription Flow](#building-a-subscription-flow)
- [Subscription Lifecycle](#subscription-lifecycle)
- [Trial Periods](#trial-periods)
- [Plan Changes and Proration](#plan-changes-and-proration)
- [Cancellation](#cancellation)
- [Subscription Webhooks](#subscription-webhooks)
- [Entitlements](#entitlements)
- [Common Pitfalls](#common-pitfalls)

## Overview

Stripe Billing automates recurring payments with subscriptions. A subscription ties a customer to a price, automatically generates invoices at each billing cycle, and creates PaymentIntents for collection.

## Pricing Models

| Model | Description | Price Config |
|-------|-------------|-------------|
| **Flat-rate** | Fixed monthly/yearly fee | `unit_amount: 1500, recurring: { interval: "month" }` |
| **Per-seat** | Per-user pricing | Use `quantity` on the subscription item |
| **Tiered** | Volume-based pricing tiers | `billing_scheme: "tiered"` with `tiers` |
| **Usage-based** | Metered billing | `recurring: { usage_type: "metered" }` |

## Creating Products and Prices

### Via API (Node.js)

```javascript
const product = await stripe.products.create({
  name: "Pro Plan",
  description: "Full access to all features",
});

const monthlyPrice = await stripe.prices.create({
  product: product.id,
  unit_amount: 2000, // $20.00
  currency: "usd",
  recurring: { interval: "month" },
});

const yearlyPrice = await stripe.prices.create({
  product: product.id,
  unit_amount: 19200, // $192.00 (20% savings)
  currency: "usd",
  recurring: { interval: "year" },
});
```

### Via API (Python)

```python
product = client.v1.products.create(params={
    "name": "Pro Plan",
    "description": "Full access to all features",
})

monthly_price = client.v1.prices.create(params={
    "product": product.id,
    "unit_amount": 2000,
    "currency": "usd",
    "recurring": {"interval": "month"},
})
```

## Building a Subscription Flow

### Option 1: Checkout Sessions (Recommended)

```javascript
const session = await stripe.checkout.sessions.create({
  ui_mode: "elements",
  customer: "cus_xxx",
  line_items: [{ price: "price_xxx", quantity: 1 }],
  mode: "subscription",
  return_url: "https://example.com/complete?session_id={CHECKOUT_SESSION_ID}",
});
```

### Option 2: Create Subscription Directly

```javascript
const subscription = await stripe.subscriptions.create({
  customer: "cus_xxx",
  items: [{ price: "price_xxx" }],
  payment_behavior: "default_incomplete",
  payment_settings: {
    save_default_payment_method: "on_subscription",
  },
  expand: ["latest_invoice.confirmation_secret"],
});

// Use latest_invoice.confirmation_secret on client to collect payment
const clientSecret = subscription.latest_invoice.confirmation_secret;
```

## Subscription Lifecycle

```
 created ──▶ incomplete ──▶ active ──▶ past_due ──▶ canceled
                │                        │              ▲
                │                        ▼              │
                ▼                    unpaid ─────────────┘
           incomplete_expired
```

| Status | Meaning |
|--------|---------|
| `incomplete` | Initial payment pending |
| `incomplete_expired` | Initial payment not completed in time |
| `trialing` | In free trial period |
| `active` | Payments current, subscription active |
| `past_due` | Latest invoice payment failed |
| `unpaid` | Multiple payment failures |
| `canceled` | Subscription canceled |
| `paused` | Subscription paused |

## Trial Periods

### On the Price

```javascript
const price = await stripe.prices.create({
  product: product.id,
  unit_amount: 2000,
  currency: "usd",
  recurring: {
    interval: "month",
    trial_period_days: 14,
  },
});
```

### On the Subscription

```javascript
const subscription = await stripe.subscriptions.create({
  customer: "cus_xxx",
  items: [{ price: "price_xxx" }],
  trial_period_days: 14,
  // or: trial_end: Math.floor(Date.now() / 1000) + 14 * 86400,
});
```

### Trial with Payment Method Upfront

```javascript
const session = await stripe.checkout.sessions.create({
  mode: "subscription",
  line_items: [{ price: "price_xxx", quantity: 1 }],
  subscription_data: { trial_period_days: 14 },
  payment_method_collection: "always", // Collect card during trial
  return_url: "...",
  ui_mode: "elements",
});
```

## Plan Changes and Proration

### Upgrade/Downgrade

```javascript
const subscription = await stripe.subscriptions.retrieve("sub_xxx");

const updated = await stripe.subscriptions.update("sub_xxx", {
  cancel_at_period_end: false,
  items: [
    {
      id: subscription.items.data[0].id,
      price: "price_new_plan",
    },
  ],
});
```

### Preview Proration

```javascript
const invoice = await stripe.invoices.createPreview({
  customer: "cus_xxx",
  subscription: "sub_xxx",
  subscription_details: {
    items: [
      { id: subscription.items.data[0].id, deleted: true },
      { price: "price_new_plan", deleted: false },
    ],
  },
});

console.log("Prorated amount:", invoice.amount_due);
```

### Proration Behavior

| Value | Behavior |
|-------|----------|
| `create_prorations` (default) | Creates credit/debit line items |
| `none` | No proration, change applies next cycle |
| `always_invoice` | Creates and immediately invoices proration |

## Cancellation

### Cancel at Period End

```javascript
await stripe.subscriptions.update("sub_xxx", {
  cancel_at_period_end: true,
});
// Subscription stays active until current period ends
```

### Cancel Immediately

```javascript
await stripe.subscriptions.cancel("sub_xxx");
// Subscription ends immediately
```

### Cancel at Specific Date

```javascript
await stripe.subscriptions.update("sub_xxx", {
  cancel_at: Math.floor(Date.now() / 1000) + 7 * 86400, // 7 days
});
```

Canceled subscriptions cannot be reactivated — create a new one instead.

## Subscription Webhooks

| Event | When |
|-------|------|
| `customer.subscription.created` | New subscription created |
| `customer.subscription.updated` | Plan change, status change, renewal |
| `customer.subscription.deleted` | Subscription canceled |
| `customer.subscription.trial_will_end` | Trial ending in 3 days |
| `customer.subscription.paused` | Subscription paused |
| `customer.subscription.resumed` | Subscription resumed |
| `invoice.created` | New invoice generated |
| `invoice.paid` | Invoice payment succeeded |
| `invoice.payment_failed` | Invoice payment failed |
| `invoice.finalized` | Invoice finalized |

### Webhook Handler Example

```javascript
app.post("/webhook", express.raw({ type: "application/json" }), (req, res) => {
  const event = stripe.webhooks.constructEvent(
    req.body,
    req.headers["stripe-signature"],
    process.env.STRIPE_WEBHOOK_SECRET
  );

  switch (event.type) {
    case "invoice.paid":
      const invoice = event.data.object;
      grantAccess(invoice.customer, invoice.subscription);
      break;
    case "invoice.payment_failed":
      const failedInvoice = event.data.object;
      notifyCustomer(failedInvoice.customer);
      break;
    case "customer.subscription.deleted":
      const sub = event.data.object;
      revokeAccess(sub.customer);
      break;
  }

  res.sendStatus(200);
});
```

## Entitlements

Entitlements represent customer access to features included in their subscription:

```javascript
const product = await stripe.products.create({
  name: "Pro Plan",
  features: [
    { name: "Advanced Analytics" },
    { name: "Priority Support" },
    { name: "API Access" },
  ],
});

// Check entitlements
const entitlements = await stripe.entitlements.activeEntitlements.list({
  customer: "cus_xxx",
});
```

Use entitlements instead of querying subscription status to check feature access.

## Common Pitfalls

- **Not handling `invoice.payment_failed`** — Always notify customers and have a retry strategy
- **Not using `payment_behavior: "default_incomplete"`** — Without this, the subscription activates before payment confirmation
- **Ignoring proration on plan changes** — Always preview the invoice before changing plans
- **Reactivating canceled subscriptions** — Cannot be done; create a new subscription
- **Not saving default payment method** — Use `save_default_payment_method: "on_subscription"` for higher renewal rates
- **Modifying trialing subscriptions** — Changing a trialing subscription ends the trial immediately and creates an invoice
