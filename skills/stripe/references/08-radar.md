# Stripe — Fraud Protection (Radar)

> Source: [docs.stripe.com/radar](https://docs.stripe.com/radar) | API `2026-05-27.dahlia`

## Overview

Stripe Radar is a machine-learning fraud detection system that evaluates every transaction in real time. It's built into all Stripe accounts and uses data from millions of businesses on the Stripe network to assess risk.

## How Radar Works

1. Customer submits payment
2. Radar evaluates transaction using ML models
3. Risk score is computed (0–100)
4. Rules are applied (block, allow, review, request 3DS)
5. Decision: **allow**, **block**, or **send to review**

Radar uses 1,000+ signals including:
- Card fingerprint and velocity
- Device fingerprint (IP, browser, device)
- Customer behavioral patterns
- Network-wide fraud patterns
- Geographic signals

## Risk Levels

| Level | Score Range | Default Action |
|-------|------------|---------------|
| **Normal** | 0–64 | Allow |
| **Elevated** | 65–74 | Allow (flag) |
| **Highest** | 75+ | Block |

Configure risk thresholds in **Dashboard → Radar → Settings**.

## Radar Rules

### Built-in Rules

Stripe provides default rules that catch common fraud patterns. These are enabled by default and customizable.

### Custom Rules

Create rules to block, allow, review, or request 3DS:

| Action | Syntax Example |
|--------|---------------|
| **Block** | `Block if :card_country: != :ip_country:` |
| **Allow** | `Allow if :is_recurring:` |
| **Review** | `Review if :risk_score: >= 50` |
| **Request 3DS** | `Request 3D Secure if :amount_in_usd: > 500` |

### Rule Attributes

| Attribute | Description |
|-----------|-------------|
| `:risk_score:` | Radar risk score (0–100) |
| `:card_country:` | Card-issuing country |
| `:ip_country:` | Customer IP country |
| `:amount_in_usd:` | Transaction amount in USD |
| `:is_recurring:` | Whether charge is recurring |
| `:card_funding:` | Card type: credit, debit, prepaid |
| `:customer_email:` | Customer email address |
| `:card_bin:` | First 6 digits of card number |
| `:metadata:` | Custom metadata fields |

### Creating Rules via Dashboard

1. Go to **Radar → Rules**
2. Click **Add rule**
3. Enter rule condition
4. Test against recent transactions
5. Enable in sandbox, then live

## 3D Secure (3DS)

3D Secure adds an authentication step for high-risk transactions:

```javascript
const paymentIntent = await stripe.paymentIntents.create({
  amount: 2000,
  currency: "eur",
  payment_method: "pm_card_visa",
  payment_method_options: {
    card: {
      request_three_d_secure: "any", // 'any' or 'automatic'
    },
  },
});
```

| Option | Behavior |
|--------|----------|
| `automatic` (default) | 3DS only when required by regulations or Radar |
| `any` | Request 3DS for all transactions |

### SCA (Strong Customer Authentication)

Required in the European Economic Area (EEA). Stripe automatically handles SCA when using the Payment Element or Checkout.

## Allow and Block Lists

### Block List

Block specific attributes:

```javascript
// Dashboard: Radar → Lists
// Or via API:
const rule = await stripe.radar.valueListItems.create({
  value_list: "rsl_xxx", // ID of your block list
  value: "suspicious@example.com",
});
```

Block by:
- Email address
- IP address
- Card fingerprint
- Card BIN
- Customer ID

### Allow List

Trust known-good customers:

```javascript
await stripe.radar.valueListItems.create({
  value_list: "rsl_allow_xxx",
  value: "trusted@company.com",
});
```

## Manual Reviews

For Radar for Fraud Teams (paid plan):

1. Transactions flagged for review appear in **Dashboard → Radar → Reviews**
2. Reviewers see risk signals, customer history, and similar transactions
3. Actions: **Approve** or **Refund**

### Webhook for Reviews

```javascript
case "review.opened":
  const review = event.data.object;
  notifyFraudTeam(review);
  break;

case "review.closed":
  const closedReview = event.data.object;
  if (closedReview.reason === "refunded") {
    handleFraudRefund(closedReview);
  }
  break;
```

## Radar Sessions

Extend Radar protection to non-Stripe tokenized payments:

```javascript
const radarSession = await stripe.radar.sessions.create({
  payment_method: "pm_xxx",
});
```

## Reading Risk Data

### From PaymentIntent

```javascript
const pi = await stripe.paymentIntents.retrieve("pi_xxx", {
  expand: ["latest_charge"],
});
const outcome = pi.latest_charge.outcome;
console.log(`Risk level: ${outcome.risk_level}`);  // 'normal', 'elevated', 'highest'
console.log(`Risk score: ${outcome.risk_score}`);   // 0-100
console.log(`Rule: ${outcome.rule?.id}`);
```

### From Charge Object

```javascript
const charge = await stripe.charges.retrieve("ch_xxx");
console.log(charge.outcome);
// {
//   network_status: 'approved_by_network',
//   risk_level: 'normal',
//   risk_score: 12,
//   seller_message: 'Payment complete.',
//   type: 'authorized'
// }
```

## 2026 Radar Enhancements

- **Free trial abuse prevention** — Detect users creating multiple free trials
- **Bot abuse detection** (preview) — Identify automated fraud attacks
- **Multi-account abuse signals** (preview) — Detect shared/duplicate accounts
- **Smart Disputes** — AI-powered evidence recommendations for dispute responses
- **Issuing authorization signals** (preview) — Predict fraudulent card attempts

## Testing Radar

| Test Card | Behavior |
|-----------|----------|
| `pm_card_radarBlock` | Blocked by Radar as fraud |
| `4100 0000 0000 0019` | Always triggers highest risk |
| `4000 0000 0000 9235` | Triggers elevated risk |

```bash
# Test Radar via CLI
stripe trigger charge.succeeded
```

## Common Pitfalls

- **Not using the Payment Element** — Radar works best with Stripe's pre-built payment forms that collect device fingerprints
- **Overly aggressive rules** — Blocking too many legitimate customers reduces revenue; start conservative
- **Ignoring review queue** — Unreviewed transactions auto-approve; set SLAs for your fraud team
- **Not passing metadata** — Custom metadata enables more precise rules
- **Relying solely on Radar** — Combine with application-level fraud checks (velocity limits, account verification)
