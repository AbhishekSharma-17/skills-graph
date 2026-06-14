# Stripe — Testing

> Source: [docs.stripe.com/testing](https://docs.stripe.com/testing) | API `2026-05-27.dahlia`

## Table of Contents

- [Overview](#overview)
- [Sandbox Environment](#sandbox-environment)
- [Test Card Numbers](#test-card-numbers)
- [Test Payment Methods (API)](#test-payment-methods-api)
- [Simulating Scenarios](#simulating-scenarios)
- [Test Clocks (Subscriptions)](#test-clocks-subscriptions)
- [Integration Testing Patterns](#integration-testing-patterns)
- [Going Live Checklist](#going-live-checklist)
- [Common Pitfalls](#common-pitfalls)

## Overview

Stripe provides a full sandbox environment for testing. All test transactions use test API keys (`sk_test_`, `pk_test_`) and never move real money. Test the complete payment flow before going live.

## Sandbox Environment

- Access via the account picker in the Dashboard
- Use test API keys for all API calls
- Separate from live data — different customers, subscriptions, etc.
- No rate limiting differences from live mode

```bash
# Environment variables
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
```

## Test Card Numbers

### By Brand

| Brand | Number | CVC | Expiry |
|-------|--------|-----|--------|
| **Visa** | `4242 4242 4242 4242` | Any 3 | Any future |
| **Visa (debit)** | `4000 0566 5566 5556` | Any 3 | Any future |
| **Mastercard** | `5555 5555 5555 4444` | Any 3 | Any future |
| **Mastercard (debit)** | `5200 8282 8282 8210` | Any 3 | Any future |
| **Amex** | `3782 822463 10005` | Any 4 | Any future |
| **Discover** | `6011 1111 1111 1117` | Any 3 | Any future |
| **JCB** | `3566 0020 2036 0505` | Any 3 | Any future |
| **UnionPay** | `6200 0000 0000 0005` | Any 3 | Any future |
| **Diners** | `3056 9300 0902 0004` | Any 3 | Any future |

For all test cards, use any future expiry date and any CVC (3 digits, 4 for Amex).

### By Country

| Country | Number | Brand |
|---------|--------|-------|
| US | `4242 4242 4242 4242` | Visa |
| UK | `4000 0082 6000 0000` | Visa |
| Canada | `4000 0012 4000 0000` | Visa |
| Germany | `4000 0027 6000 0016` | Visa |
| France | `4000 0025 0000 0003` | Visa |
| Australia | `4000 0003 6000 0006` | Visa |
| Japan | `4000 0039 2000 0003` | Visa |
| India | `4000 0035 6000 0008` | Visa |

## Test Payment Methods (API)

Use PaymentMethod IDs instead of card numbers in server-side tests:

```javascript
const paymentIntent = await stripe.paymentIntents.create({
  amount: 2000,
  currency: "usd",
  payment_method: "pm_card_visa",
  confirm: true,
});
```

| Brand | PaymentMethod ID |
|-------|-----------------|
| Visa | `pm_card_visa` |
| Visa (debit) | `pm_card_visa_debit` |
| Mastercard | `pm_card_mastercard` |
| Mastercard (debit) | `pm_card_mastercard_debit` |
| Amex | `pm_card_amex` |
| Discover | `pm_card_discover` |
| JCB | `pm_card_jcb` |
| UnionPay | `pm_card_unionpay` |

## Simulating Scenarios

### Declined Payments

| Scenario | Card/PM |
|----------|---------|
| Generic decline | `pm_card_visa_chargeDeclined` |
| Insufficient funds | `4000 0000 0000 9995` |
| Lost card | `4000 0000 0000 9987` |
| Stolen card | `4000 0000 0000 9979` |
| Expired card | `pm_card_chargeDeclinedExpiredCard` |
| Incorrect CVC | `pm_card_chargeDeclinedIncorrectCvc` |
| Processing error | `pm_card_chargeDeclinedProcessingError` |

### 3D Secure Authentication

| Scenario | Card |
|----------|------|
| 3DS required | `4000 0025 0000 3155` |
| 3DS required (always) | `4000 0027 6000 3184` |
| 3DS optional | `4000 0000 0000 3055` |
| 3DS auth fails | `4000 0084 0000 1629` |

### Disputes

| Scenario | Card |
|----------|------|
| Triggers dispute | `4000 0000 0000 0259` |
| Fraud dispute (early) | `4000 0000 0000 1976` |

### Radar (Fraud)

| Scenario | Card/PM |
|----------|---------|
| Blocked by Radar | `pm_card_radarBlock` |
| Highest risk score | `4100 0000 0000 0019` |
| Elevated risk | `4000 0000 0000 9235` |

### Bank Payments

| Method | Test Value |
|--------|------------|
| SEPA (success) | `AT321904300235473204` |
| SEPA (failure) | `AT861904300235473202` |
| BECS (success) | Account `900123456`, BSB `000000` |
| ACH (success) | Routing `110000000`, Account `000123456789` |

## Test Clocks (Subscriptions)

Test clocks let you simulate time passing for subscription testing:

```javascript
// Create a test clock
const clock = await stripe.testHelpers.testClocks.create({
  frozen_time: Math.floor(Date.now() / 1000),
});

// Create customer with test clock
const customer = await stripe.customers.create({
  test_clock: clock.id,
  email: "test@example.com",
});

// Create subscription
const subscription = await stripe.subscriptions.create({
  customer: customer.id,
  items: [{ price: "price_xxx" }],
  trial_period_days: 14,
});

// Advance time to end of trial
await stripe.testHelpers.testClocks.advance(clock.id, {
  frozen_time: Math.floor(Date.now() / 1000) + 15 * 86400,
});
// Subscription transitions from trialing → active, invoice is created
```

### Test Clock Scenarios

```javascript
// Test renewal
await stripe.testHelpers.testClocks.advance(clock.id, {
  frozen_time: Math.floor(Date.now() / 1000) + 31 * 86400,
});

// Test payment failure + retry
// Use pm_card_visa_chargeDeclinedInsufficientFunds
// Advance to retry date
```

## Integration Testing Patterns

### Node.js (Jest)

```javascript
const stripe = require("stripe")(process.env.STRIPE_SECRET_KEY);

describe("Payment flow", () => {
  test("creates and confirms a PaymentIntent", async () => {
    const pi = await stripe.paymentIntents.create({
      amount: 2000,
      currency: "usd",
      payment_method: "pm_card_visa",
      confirm: true,
    });

    expect(pi.status).toBe("succeeded");
    expect(pi.amount).toBe(2000);
  });

  test("handles declined card", async () => {
    await expect(
      stripe.paymentIntents.create({
        amount: 2000,
        currency: "usd",
        payment_method: "pm_card_visa_chargeDeclined",
        confirm: true,
      })
    ).rejects.toThrow("Your card was declined");
  });
});
```

### Python (pytest)

```python
import pytest
from stripe import StripeClient, CardError

client = StripeClient("sk_test_...")

def test_successful_payment():
    pi = client.v1.payment_intents.create(params={
        "amount": 2000,
        "currency": "usd",
        "payment_method": "pm_card_visa",
        "confirm": True,
    })
    assert pi.status == "succeeded"

def test_declined_card():
    with pytest.raises(CardError):
        client.v1.payment_intents.create(params={
            "amount": 2000,
            "currency": "usd",
            "payment_method": "pm_card_visa_chargeDeclined",
            "confirm": True,
        })
```

### Webhook Testing with CLI

```bash
# Forward events to local server
stripe listen --forward-to localhost:4242/webhook

# Trigger specific events
stripe trigger payment_intent.succeeded
stripe trigger invoice.payment_failed
stripe trigger customer.subscription.created
```

## Going Live Checklist

- [ ] Replace `sk_test_` with `sk_live_` keys (via environment variables)
- [ ] Replace `pk_test_` with `pk_live_` keys
- [ ] Set up production webhook endpoint (HTTPS required)
- [ ] Remove all test card numbers from code
- [ ] Verify error handling for all decline scenarios
- [ ] Enable Radar rules appropriate for your business
- [ ] Test the Customer Portal with real branding
- [ ] Verify email notifications are configured
- [ ] Set up monitoring for webhook failures
- [ ] Store API keys in a secrets vault, not source code

## Common Pitfalls

- **Using real cards in test mode** — Violates the Stripe Services Agreement; only use test cards
- **Hardcoding test keys** — Use environment variables; switching to live requires only changing the env
- **Not testing webhook signature verification** — Use `stripe listen` locally to verify your handler works
- **Skipping decline scenarios** — Test all common decline codes, not just the happy path
- **Load testing against Stripe** — Don't use sandbox for load testing; follow Stripe's load testing guide
- **Forgetting test clock cleanup** — Test clocks persist; delete them when done
