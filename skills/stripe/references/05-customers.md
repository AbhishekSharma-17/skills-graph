# Stripe — Customer Management

> Source: [docs.stripe.com/customer-management](https://docs.stripe.com/customer-management) | API `2026-05-27.dahlia`

## Table of Contents

- [Overview](#overview)
- [Creating Customers](#creating-customers)
- [Payment Methods](#payment-methods)
- [Customer Portal](#customer-portal)
- [Customer Portal Configuration](#customer-portal-configuration)
- [Portal Sessions](#portal-sessions)
- [Deep Links](#deep-links)
- [Cancellation Deflection](#cancellation-deflection)
- [Common Pitfalls](#common-pitfalls)

## Overview

Customers are central to Stripe — they store payment methods, subscriptions, invoices, and billing details. The Customer Portal provides a self-service UI where customers manage their accounts without contacting support.

## Creating Customers

### Node.js

```javascript
const customer = await stripe.customers.create({
  email: "jenny@example.com",
  name: "Jenny Rosen",
  metadata: {
    user_id: "user_12345",
  },
  address: {
    city: "San Francisco",
    country: "US",
    line1: "123 Main Street",
    postal_code: "94105",
    state: "CA",
  },
});
```

### Python

```python
customer = client.v1.customers.create(params={
    "email": "jenny@example.com",
    "name": "Jenny Rosen",
    "metadata": {"user_id": "user_12345"},
    "address": {
        "city": "San Francisco",
        "country": "US",
        "line1": "123 Main Street",
        "postal_code": "94105",
        "state": "CA",
    },
})
```

### Auto-Create During Checkout

```javascript
const session = await stripe.checkout.sessions.create({
  customer_creation: "always",
  customer_email: "jenny@example.com",
  // ...
});
```

## Payment Methods

### List Customer's Payment Methods

```javascript
const paymentMethods = await stripe.paymentMethods.list({
  customer: "cus_xxx",
  type: "card",
});
```

### Attach a Payment Method

```javascript
await stripe.paymentMethods.attach("pm_xxx", {
  customer: "cus_xxx",
});

// Set as default
await stripe.customers.update("cus_xxx", {
  invoice_settings: {
    default_payment_method: "pm_xxx",
  },
});
```

### Detach a Payment Method

```javascript
await stripe.paymentMethods.detach("pm_xxx");
```

### Save During Checkout

```javascript
const session = await stripe.checkout.sessions.create({
  saved_payment_method_options: {
    payment_method_save: "enabled",
  },
  // ...
});
```

## Customer Portal

The Customer Portal is a Stripe-hosted self-service page where customers can:

| Feature | Capability |
|---------|------------|
| **Billing Info** | Update address, tax IDs |
| **Payment Methods** | Add, update, remove payment methods |
| **Subscriptions** | Upgrade, downgrade, change quantity |
| **Cancellation** | Cancel immediately or at period end |
| **Invoices** | View, download, and pay invoices |

### Key Properties

- Sessions expire after 5 minutes of inactivity (extend to 1 hour when active)
- Supports 40+ languages, auto-localized
- 50+ payment methods including cards, wallets, bank transfers, BNPL
- Cannot be displayed in an iframe

## Customer Portal Configuration

### No-Code Setup (Dashboard)

1. Navigate to **Settings → Billing**
2. Enable the Customer Portal
3. Configure which features are available
4. Customize branding (logo, colors, business name)

### API Configuration

```javascript
const config = await stripe.billingPortal.configurations.create({
  business_profile: {
    headline: "Manage your subscription",
  },
  features: {
    subscription_update: {
      enabled: true,
      default_allowed_updates: ["price", "quantity"],
      products: [
        {
          product: "prod_xxx",
          prices: ["price_basic", "price_pro", "price_enterprise"],
        },
      ],
    },
    subscription_cancel: {
      enabled: true,
      mode: "at_period_end",
      cancellation_reason: {
        enabled: true,
        options: [
          "too_expensive",
          "missing_features",
          "switched_service",
          "unused",
          "other",
        ],
      },
    },
    invoice_history: { enabled: true },
    payment_method_update: { enabled: true },
  },
});
```

## Portal Sessions

### Create a Portal Session (Node.js)

```javascript
app.post("/create-portal-session", async (req, res) => {
  const session = await stripe.billingPortal.sessions.create({
    customer: req.body.customerId,
    return_url: "https://example.com/account",
  });

  res.redirect(303, session.url);
});
```

### Create a Portal Session (Python)

```python
@app.route("/create-portal-session", methods=["POST"])
def create_portal_session():
    session = client.v1.billing_portal.sessions.create(params={
        "customer": request.json["customerId"],
        "return_url": "https://example.com/account",
    })
    return redirect(session.url, code=303)
```

## Deep Links

Direct customers to specific portal actions:

### Update Payment Method

```javascript
const session = await stripe.billingPortal.sessions.create({
  customer: "cus_xxx",
  return_url: "https://example.com/account",
  flow_data: {
    type: "payment_method_update",
  },
});
```

### Cancel Subscription

```javascript
const session = await stripe.billingPortal.sessions.create({
  customer: "cus_xxx",
  return_url: "https://example.com/account",
  flow_data: {
    type: "subscription_cancel",
    subscription_cancel: {
      subscription: "sub_xxx",
    },
  },
});
```

### Update Subscription

```javascript
const session = await stripe.billingPortal.sessions.create({
  customer: "cus_xxx",
  return_url: "https://example.com/account",
  flow_data: {
    type: "subscription_update_confirm",
    subscription_update_confirm: {
      subscription: "sub_xxx",
      items: [{ id: "si_xxx", price: "price_new" }],
    },
  },
});
```

## Cancellation Deflection

Reduce churn with built-in retention tools:

```javascript
const config = await stripe.billingPortal.configurations.create({
  features: {
    subscription_cancel: {
      enabled: true,
      cancellation_reason: { enabled: true },
      proration_behavior: "create_prorations",
    },
  },
});
```

- Offer coupons when customers attempt to cancel
- Collect cancellation reasons via webhooks
- Track reasons for analytics and product improvement

## Common Pitfalls

- **Not storing the Stripe `customer.id`** — Always save it in your database alongside your user record
- **Creating duplicate customers** — Check if a customer exists before creating a new one
- **Not using `customer_creation: "always"` in Checkout** — Without this, guest checkouts won't create customer records
- **Ignoring payment method expiration** — Monitor `payment_method.updated` webhooks for card updates
- **Not configuring the Customer Portal** — It requires explicit configuration of allowed features before use
- **Maximum 10 products for plan switching** — The portal supports at most 10 products for subscription updates
