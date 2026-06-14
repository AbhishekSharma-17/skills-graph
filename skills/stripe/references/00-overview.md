# Stripe — Overview & Setup

> Source: [docs.stripe.com](https://docs.stripe.com) | API version `2026-05-27.dahlia`

## What Is Stripe?

Stripe is a payment processing platform that provides APIs and tools for accepting payments, managing subscriptions, building marketplaces, and handling financial operations. It processes payments in 135+ currencies across 195+ countries.

## Core Concepts

| Concept | Description |
|---------|-------------|
| **PaymentIntent** | Tracks a payment lifecycle from creation through confirmation |
| **Checkout Session** | Server-side object that controls the checkout flow |
| **Customer** | Represents a buyer — stores payment methods, subscriptions, invoices |
| **Price** | Defines a unit price, currency, and billing cycle for a product |
| **Product** | Goods or services your business sells |
| **Subscription** | Recurring purchase schedule that generates invoices automatically |
| **Invoice** | Statement of amounts owed, tracks payment status |
| **PaymentMethod** | Customer's payment instrument (card, bank, wallet) |
| **Webhook** | HTTP callback for real-time event notifications |

## Architecture

Stripe follows a client-server model:

1. **Server-side SDK** — Creates payment objects (Checkout Sessions, PaymentIntents)
2. **Client-side SDK** — Renders secure payment forms (Payment Element, Checkout)
3. **Webhooks** — Delivers asynchronous event notifications to your server
4. **Dashboard** — Web UI for configuration, monitoring, and management

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  Your Client │───▶│  Your Server │───▶│ Stripe API  │
│  (Browser)   │    │  (Node/Py)   │    │             │
│              │◀───│              │◀───│             │
│ PaymentElem  │    │ clientSecret │    │ Webhooks    │──▶ Your Server
└─────────────┘    └──────────────┘    └─────────────┘
```

## Installation

### Node.js

```bash
npm install stripe
```

```javascript
const Stripe = require("stripe");
const stripe = new Stripe("sk_test_...");

// Create a Checkout Session
const session = await stripe.checkout.sessions.create({
  ui_mode: "elements",
  line_items: [{ price: "price_xxx", quantity: 1 }],
  mode: "payment",
  return_url: "https://example.com/complete?session_id={CHECKOUT_SESSION_ID}",
});

console.log(session.client_secret);
```

### Python

```bash
pip install stripe
```

```python
from stripe import StripeClient

client = StripeClient("sk_test_...")

session = client.v1.checkout.sessions.create(params={
    "ui_mode": "elements",
    "line_items": [{"price": "price_xxx", "quantity": 1}],
    "mode": "payment",
    "return_url": "https://example.com/complete?session_id={CHECKOUT_SESSION_ID}",
})

print(session.client_secret)
```

### Client-Side (Browser)

```html
<script src="https://js.stripe.com/dahlia/stripe.js"></script>
<script>
  const stripe = Stripe("pk_test_...");
</script>
```

Or with npm:

```bash
npm install @stripe/stripe-js @stripe/react-stripe-js
```

```javascript
import { loadStripe } from "@stripe/stripe-js";
const stripePromise = loadStripe("pk_test_...");
```

## API Keys

| Key Type | Prefix | Use |
|----------|--------|-----|
| **Publishable (test)** | `pk_test_` | Client-side, safe to expose |
| **Secret (test)** | `sk_test_` | Server-side only, never expose |
| **Publishable (live)** | `pk_live_` | Client-side, production |
| **Secret (live)** | `sk_live_` | Server-side, production |
| **Restricted** | `rk_test_` / `rk_live_` | Limited permissions per resource |

**Never commit secret keys to source control.** Use environment variables:

```bash
# .env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

## Choosing an Integration Path

| Path | Best For | Complexity |
|------|----------|------------|
| **Checkout Sessions + Payment Element** | Most integrations (recommended) | Low |
| **Payment Links** | No-code, shareable payment URLs | Minimal |
| **Checkout Sessions + Full Page** | Stripe-hosted checkout page | Low |
| **PaymentIntents + Elements** | Advanced custom checkout | High |

Stripe recommends **Checkout Sessions API with `ui_mode: "elements"`** for most integrations. It handles tax, discounts, shipping, adaptive pricing, and 100+ payment methods with minimal code.

## Payment Modes

| Mode | Use Case |
|------|----------|
| `"payment"` | One-time payments |
| `"subscription"` | Recurring billing |
| `"setup"` | Save a payment method for later |

## SDK Versions

| SDK | Package | Latest |
|-----|---------|--------|
| Node.js | `stripe` | 22.2.x |
| Python | `stripe` | 15.2.x |
| React | `@stripe/react-stripe-js` | 6.x |
| Stripe.js | `@stripe/stripe-js` | 9.x |
| CLI | `stripe` | Install via Homebrew |

## Common Pitfalls

- **Using `sk_live_` keys in test mode** — Always use `sk_test_` for development
- **Not verifying webhook signatures** — Always validate `Stripe-Signature` header
- **Handling payments client-side only** — Always create PaymentIntents/Sessions server-side
- **Polling instead of webhooks** — Use webhooks for async events (payment success, failures)
- **Hardcoding prices** — Use the Products/Prices API or Dashboard to manage pricing
- **Not using idempotency keys** — Always use them for create/update operations to prevent duplicates
