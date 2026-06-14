# Stripe — Error Handling

> Source: [docs.stripe.com/error-handling](https://docs.stripe.com/error-handling) | API `2026-05-27.dahlia`

## Table of Contents

- [Overview](#overview)
- [Error Object Structure](#error-object-structure)
- [Error Types](#error-types)
- [HTTP Status Codes](#http-status-codes)
- [Node.js Error Handling](#nodejs-error-handling)
- [Python Error Handling](#python-error-handling)
- [Payment-Specific Errors](#payment-specific-errors)
- [Decline Codes](#decline-codes)
- [Idempotency Keys](#idempotency-keys)
- [Retry Strategies](#retry-strategies)
- [Common Pitfalls](#common-pitfalls)

## Overview

Stripe returns errors as structured objects with type, code, message, and additional context. Proper error handling is critical for providing good user experiences and preventing data inconsistencies.

## Error Object Structure

```json
{
  "error": {
    "type": "card_error",
    "code": "card_declined",
    "decline_code": "insufficient_funds",
    "message": "Your card has insufficient funds.",
    "param": "payment_method",
    "doc_url": "https://docs.stripe.com/error-codes/card-declined",
    "request_log_url": "https://dashboard.stripe.com/logs/req_xxx"
  }
}
```

| Property | Description |
|----------|-------------|
| `type` | Error category |
| `code` | Specific error code |
| `message` | Human-readable description |
| `param` | The parameter that caused the error |
| `decline_code` | Card-specific decline reason |
| `doc_url` | Link to documentation for this error |
| `request_log_url` | Dashboard link for debugging |
| `requestId` | Unique request identifier (SDK only) |

## Error Types

| Type | SDK Class | Meaning |
|------|-----------|---------|
| `card_error` | `StripeCardError` | Payment declined, fraud block, or card issue |
| `invalid_request_error` | `StripeInvalidRequestError` | Invalid parameters, missing fields, wrong state |
| `api_error` | `StripeAPIError` | Stripe server-side error (rare) |
| `authentication_error` | `StripeAuthenticationError` | Invalid or revoked API key |
| `rate_limit_error` | `StripeRateLimitError` | Too many requests |
| `idempotency_error` | `StripeIdempotencyError` | Idempotency key conflict |
| `connection_error` | `StripeConnectionError` | Network connectivity issue |
| `permission_error` | `StripePermissionError` | API key lacks required permissions |

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| `200` | Success |
| `400` | Bad request — invalid parameters |
| `401` | Unauthorized — invalid API key |
| `402` | Request failed — parameters valid but request failed (card declined) |
| `403` | Forbidden — insufficient permissions |
| `404` | Not found — resource doesn't exist |
| `409` | Conflict — idempotency key conflict |
| `429` | Rate limited — too many requests |
| `500` | Server error — Stripe internal issue |

## Node.js Error Handling

### Basic Pattern

```javascript
try {
  const paymentIntent = await stripe.paymentIntents.create({
    amount: 2000,
    currency: "usd",
    payment_method: "pm_card_visa",
    confirm: true,
  });
} catch (err) {
  switch (err.type) {
    case "StripeCardError":
      // Payment was declined
      console.log(`Payment failed: ${err.message}`);
      console.log(`Decline code: ${err.decline_code}`);
      break;

    case "StripeInvalidRequestError":
      // Invalid parameters
      console.log(`Invalid request: ${err.message}`);
      console.log(`Bad parameter: ${err.param}`);
      break;

    case "StripeAuthenticationError":
      console.log("Check your API key");
      break;

    case "StripeRateLimitError":
      console.log("Rate limited — retry later");
      break;

    case "StripeConnectionError":
      // Network issue — result is indeterminate
      console.log("Network error — check payment status");
      break;

    case "StripeAPIError":
      // Stripe internal error
      console.log("Stripe server error — retry later");
      break;

    default:
      console.log(`Unexpected error: ${err.message}`);
  }

  // Always available on Stripe errors
  console.log(`Request ID: ${err.requestId}`);
  console.log(`Status: ${err.statusCode}`);
}
```

### Fraud Detection

```javascript
try {
  const paymentIntent = await stripe.paymentIntents.create(args);
} catch (err) {
  if (err.type === "StripeCardError") {
    const charge = await stripe.charges.retrieve(
      err.payment_intent.latest_charge
    );
    if (charge.outcome.type === "blocked") {
      console.log("Payment blocked by Radar for suspected fraud");
    }
  }
}
```

## Python Error Handling

```python
from stripe import StripeClient
import stripe

client = StripeClient("sk_test_...")

try:
    payment_intent = client.v1.payment_intents.create(params={
        "amount": 2000,
        "currency": "usd",
        "payment_method": "pm_card_visa",
        "confirm": True,
    })
except stripe.CardError as e:
    print(f"Payment failed: {e.user_message}")
    print(f"Code: {e.code}, Decline: {e.error.decline_code}")
except stripe.InvalidRequestError as e:
    print(f"Invalid request: {e.user_message}")
    print(f"Param: {e.param}")
except stripe.AuthenticationError:
    print("Invalid API key")
except stripe.RateLimitError:
    print("Rate limited")
except stripe.APIConnectionError:
    print("Network error — verify payment status")
except stripe.APIError:
    print("Stripe server error")
```

## Payment-Specific Errors

### From Webhooks

```javascript
app.post("/webhook", express.raw({ type: "application/json" }), (req, res) => {
  const event = stripe.webhooks.constructEvent(
    req.body,
    req.headers["stripe-signature"],
    webhookSecret
  );

  if (event.type === "payment_intent.payment_failed") {
    const pi = event.data.object;
    const error = pi.last_payment_error;
    console.log(`Type: ${error.type}, Code: ${error.code}`);
    console.log(`Message: ${error.message}`);
  }

  res.sendStatus(200);
});
```

### From Stored Objects

```javascript
const pi = await stripe.paymentIntents.retrieve("pi_xxx");
if (pi.last_payment_error) {
  const err = pi.last_payment_error;
  console.log(`Error on ${pi.id}: ${err.type} — ${err.message}`);
}
```

## Decline Codes

| Code | Meaning | Action |
|------|---------|--------|
| `generic_decline` | Generic decline | Ask customer to try another card |
| `insufficient_funds` | Not enough funds | Try a different card |
| `lost_card` | Card reported lost | Use a different card |
| `stolen_card` | Card reported stolen | Use a different card |
| `expired_card` | Card has expired | Update card details |
| `incorrect_cvc` | CVC is wrong | Re-enter card details |
| `incorrect_number` | Card number is wrong | Re-enter card details |
| `card_velocity_exceeded` | Too many attempts | Wait and retry |
| `do_not_honor` | Issuer refused | Contact card issuer |
| `fraudulent` | Suspected fraud | Use a different card |
| `processing_error` | Temporary issue | Retry after a moment |

## Idempotency Keys

Prevent duplicate operations when retrying after network errors:

```javascript
const paymentIntent = await stripe.paymentIntents.create(
  {
    amount: 2000,
    currency: "usd",
    payment_method: "pm_card_visa",
  },
  { idempotencyKey: `order_${orderId}_payment` }
);
```

Rules:
- Keys must be unique per operation (max 255 characters)
- Same key + same parameters = cached response returned
- Same key + different parameters = `StripeIdempotencyError`
- Keys expire after 24 hours

### Auto-Generated Keys

```javascript
const stripe = new Stripe("sk_test_...", {
  maxNetworkRetries: 2, // Stripe auto-generates idempotency keys for retries
});
```

## Retry Strategies

### Exponential Backoff

```javascript
async function withRetry(fn, maxRetries = 3) {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err) {
      const isRetryable =
        err.type === "StripeRateLimitError" ||
        err.type === "StripeAPIError" ||
        err.type === "StripeConnectionError";

      if (!isRetryable || attempt === maxRetries) throw err;

      const delay = Math.pow(2, attempt) * 1000; // 1s, 2s, 4s
      await new Promise((r) => setTimeout(r, delay));
    }
  }
}

const result = await withRetry(() =>
  stripe.paymentIntents.create(
    { amount: 2000, currency: "usd" },
    { idempotencyKey: "unique_key" }
  )
);
```

### SDK Auto-Retry

```javascript
const stripe = new Stripe("sk_test_...", {
  maxNetworkRetries: 2,
  timeout: 10000, // 10 seconds
});
```

## Common Pitfalls

- **Showing raw Stripe error messages to users** — Use `decline_code` to map to friendly messages
- **Not using idempotency keys** — Always use them for create/update operations
- **Retrying non-retryable errors** — Only retry on rate limit, API, and connection errors; don't retry card declines
- **Ignoring `connection_error`** — The payment may have succeeded; check the object state before retrying
- **Not logging `requestId`** — Include it in error reports for faster Stripe support resolution
