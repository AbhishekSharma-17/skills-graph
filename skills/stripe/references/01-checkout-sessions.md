# Stripe — Checkout Sessions

> Source: [docs.stripe.com/payments/checkout](https://docs.stripe.com/payments/checkout) | API `2026-05-27.dahlia`

## Table of Contents

- [Overview](#overview)
- [Creating a Checkout Session](#creating-a-checkout-session)
- [UI Modes](#ui-modes)
- [Line Items](#line-items)
- [Payment Modes](#payment-modes)
- [Server-Side: Node.js](#server-side-nodejs)
- [Server-Side: Python](#server-side-python)
- [Client-Side Integration](#client-side-integration)
- [Handling Completion](#handling-completion)
- [Advanced Options](#advanced-options)
- [Common Pitfalls](#common-pitfalls)

## Overview

Checkout Sessions API is Stripe's recommended integration path. A Checkout Session represents a single payment or subscription flow and controls what the customer sees, what they pay, and where they return after payment.

## Creating a Checkout Session

The flow:
1. Customer clicks "Pay" on your site
2. Your server creates a Checkout Session via the API
3. Server returns the `client_secret` to the client
4. Client renders the Payment Element using the `client_secret`
5. Customer submits payment
6. Stripe processes and sends webhooks

## UI Modes

| Mode | Description | Hosting |
|------|-------------|---------|
| `elements` (recommended) | Embedded payment form on your site | Your domain |
| `hosted` (full page) | Redirect to Stripe-hosted page | stripe.com |

### Embedded (Elements) — Recommended

```javascript
const session = await stripe.checkout.sessions.create({
  ui_mode: "elements",
  line_items: [{ price: "price_xxx", quantity: 1 }],
  mode: "payment",
  return_url: "https://example.com/complete?session_id={CHECKOUT_SESSION_ID}",
});
// Returns session.client_secret for client-side
```

### Hosted (Full Page)

```javascript
const session = await stripe.checkout.sessions.create({
  line_items: [{ price: "price_xxx", quantity: 1 }],
  mode: "payment",
  success_url: "https://example.com/success?session_id={CHECKOUT_SESSION_ID}",
  cancel_url: "https://example.com/cancel",
});
// Returns session.url for redirect
```

## Line Items

### Using Predefined Prices (Dashboard or API)

```javascript
line_items: [
  { price: "price_1ABC123", quantity: 1 },
  { price: "price_2DEF456", quantity: 2 },
]
```

### Using Dynamic Pricing (price_data)

```javascript
line_items: [
  {
    price_data: {
      product_data: { name: "Custom Widget" },
      currency: "usd",
      unit_amount: 2500, // $25.00 in cents
    },
    quantity: 1,
  },
]
```

### Recurring Price Data (Subscriptions)

```javascript
line_items: [
  {
    price_data: {
      product_data: { name: "Pro Plan" },
      currency: "usd",
      unit_amount: 1500,
      recurring: { interval: "month" },
    },
    quantity: 1,
  },
]
```

## Payment Modes

| Mode | Use Case | Line Items |
|------|----------|------------|
| `"payment"` | One-time charge | One-time prices |
| `"subscription"` | Recurring billing | Recurring prices |
| `"setup"` | Save payment method | No prices needed |

## Server-Side: Node.js

```javascript
const express = require("express");
const Stripe = require("stripe");
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);

const app = express();
app.use(express.json());

const YOUR_DOMAIN = "http://localhost:3000";

app.post("/create-checkout-session", async (req, res) => {
  try {
    const session = await stripe.checkout.sessions.create({
      ui_mode: "elements",
      customer_email: req.body.email,
      billing_address_collection: "auto",
      shipping_address_collection: {
        allowed_countries: ["US", "CA", "GB"],
      },
      line_items: [
        { price: req.body.priceId, quantity: 1 },
      ],
      mode: "payment",
      return_url: `${YOUR_DOMAIN}/complete?session_id={CHECKOUT_SESSION_ID}`,
      automatic_tax: { enabled: true },
      customer_creation: "always",
      saved_payment_method_options: {
        payment_method_save: "enabled",
      },
    });

    res.json({ clientSecret: session.client_secret });
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

app.get("/session-status", async (req, res) => {
  const session = await stripe.checkout.sessions.retrieve(
    req.query.session_id,
    { expand: ["payment_intent", "subscription"] }
  );
  res.json({
    status: session.status,
    payment_status: session.payment_status,
    customer_email: session.customer_details?.email,
  });
});

app.listen(4242, () => console.log("Server on port 4242"));
```

## Server-Side: Python

```python
import os
from flask import Flask, jsonify, request
from stripe import StripeClient

app = Flask(__name__)
client = StripeClient(os.environ["STRIPE_SECRET_KEY"])
YOUR_DOMAIN = "http://localhost:3000"

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    data = request.json
    session = client.v1.checkout.sessions.create(params={
        "ui_mode": "elements",
        "customer_email": data.get("email"),
        "billing_address_collection": "auto",
        "line_items": [
            {"price": data["priceId"], "quantity": 1},
        ],
        "mode": "payment",
        "return_url": f"{YOUR_DOMAIN}/complete?session_id={{CHECKOUT_SESSION_ID}}",
        "automatic_tax": {"enabled": True},
        "customer_creation": "always",
    })
    return jsonify(clientSecret=session.client_secret)

@app.route("/session-status")
def session_status():
    session = client.v1.checkout.sessions.retrieve(
        request.args["session_id"],
        params={"expand": ["payment_intent"]},
    )
    return jsonify(
        status=session.status,
        payment_status=session.payment_status,
    )
```

## Client-Side Integration

### Vanilla JavaScript

```html
<div id="payment-element"></div>
<button id="submit">Pay now</button>
<div id="error-message"></div>

<script src="https://js.stripe.com/dahlia/stripe.js"></script>
<script>
  const stripe = Stripe("pk_test_...");

  const clientSecret = fetch("/create-checkout-session", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ priceId: "price_xxx" }),
  })
    .then((r) => r.json())
    .then((r) => r.clientSecret);

  const checkout = stripe.initCheckoutElementsSdk({
    clientSecret,
    elementsOptions: { appearance: { theme: "stripe" } },
  });

  const paymentElement = checkout.createPaymentElement();
  paymentElement.mount("#payment-element");

  checkout.on("change", (session) => {
    document.getElementById("submit").disabled = !session.canConfirm;
  });

  document.getElementById("submit").addEventListener("click", async () => {
    const { error } = await checkout.confirm();
    if (error) {
      document.getElementById("error-message").textContent = error.message;
    }
  });
</script>
```

## Handling Completion

After payment, the customer is redirected to `return_url` with `session_id`:

```javascript
// complete.html or React return page
const params = new URLSearchParams(window.location.search);
const sessionId = params.get("session_id");

fetch(`/session-status?session_id=${sessionId}`)
  .then((r) => r.json())
  .then((data) => {
    if (data.status === "complete") {
      showSuccessMessage();
    } else {
      showFailureMessage();
    }
  });
```

## Advanced Options

### Metadata

```javascript
const session = await stripe.checkout.sessions.create({
  // ...
  metadata: {
    order_id: "order_12345",
    user_id: "user_abc",
  },
});
```

### Discounts

```javascript
const session = await stripe.checkout.sessions.create({
  // ...
  discounts: [{ coupon: "SAVE20" }],
  allow_promotion_codes: true,
});
```

### Custom Fields

```javascript
const session = await stripe.checkout.sessions.create({
  // ...
  custom_fields: [
    {
      key: "company",
      label: { type: "custom", custom: "Company Name" },
      type: "text",
    },
  ],
});
```

### Expiration

```javascript
const session = await stripe.checkout.sessions.create({
  // ...
  expires_at: Math.floor(Date.now() / 1000) + 1800, // 30 minutes
});
```

## Common Pitfalls

- **Not using `ui_mode: "elements"`** — This is the recommended mode; it gives you more control than hosted checkout
- **Missing `return_url`** — Required for `elements` mode; use `{CHECKOUT_SESSION_ID}` placeholder
- **Mixing one-time and recurring prices** — All line items must match the `mode` (`payment` vs `subscription`)
- **Not expanding related objects** — Use `expand` to include nested objects like `payment_intent` and `subscription`
- **Ignoring `session.status`** — Always check the session status on the return page; don't assume payment succeeded from the redirect alone
