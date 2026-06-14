# Stripe — React Integration

> Source: [docs.stripe.com](https://docs.stripe.com) | `@stripe/react-stripe-js@6.x` | `@stripe/stripe-js@9.x`

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Checkout Sessions Flow (Recommended)](#checkout-sessions-flow-recommended)
- [Payment Element with PaymentIntents](#payment-element-with-paymentintents)
- [Hooks Reference](#hooks-reference)
- [Express Checkout Element](#express-checkout-element)
- [Address and Contact Elements](#address-and-contact-elements)
- [Server-Side Rendering](#server-side-rendering)
- [Common Pitfalls](#common-pitfalls)

## Overview

`@stripe/react-stripe-js` provides React components and hooks for Stripe Elements. The recommended flow uses Checkout Sessions with `CheckoutElementsProvider`.

## Installation

```bash
npm install @stripe/stripe-js @stripe/react-stripe-js
```

## Checkout Sessions Flow (Recommended)

### 1. Server — Create Checkout Session

```javascript
// /api/create-checkout-session
const stripe = require("stripe")(process.env.STRIPE_SECRET_KEY);

export default async function handler(req, res) {
  const session = await stripe.checkout.sessions.create({
    ui_mode: "elements",
    line_items: [{ price: req.body.priceId, quantity: 1 }],
    mode: "payment",
    return_url: `${process.env.NEXT_PUBLIC_URL}/complete?session_id={CHECKOUT_SESSION_ID}`,
  });
  res.json({ clientSecret: session.client_secret });
}
```

### 2. Client — Provider Setup

```jsx
import { useMemo } from "react";
import { loadStripe } from "@stripe/stripe-js";
import {
  CheckoutElementsProvider,
} from "@stripe/react-stripe-js/checkout";
import CheckoutForm from "./CheckoutForm";

const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_KEY);

export default function CheckoutPage() {
  const clientSecret = useMemo(() => {
    return fetch("/api/create-checkout-session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ priceId: "price_xxx" }),
    })
      .then((r) => r.json())
      .then((d) => d.clientSecret);
  }, []);

  return (
    <CheckoutElementsProvider
      stripe={stripePromise}
      options={{
        clientSecret,
        elementsOptions: { appearance: { theme: "stripe" } },
      }}
    >
      <CheckoutForm />
    </CheckoutElementsProvider>
  );
}
```

### 3. Client — Checkout Form

```jsx
import { useState } from "react";
import {
  PaymentElement,
  ContactDetailsElement,
  useCheckoutElements,
} from "@stripe/react-stripe-js/checkout";

export default function CheckoutForm() {
  const [message, setMessage] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const checkoutState = useCheckoutElements();

  if (checkoutState.type === "loading") return <div>Loading...</div>;
  if (checkoutState.type === "error") {
    return <div>Error: {checkoutState.error.message}</div>;
  }

  const { checkout } = checkoutState;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);

    const result = await checkout.confirm();
    if (result.type === "error") {
      setMessage(result.error.message);
    }
    setIsSubmitting(false);
  };

  return (
    <form onSubmit={handleSubmit}>
      <ContactDetailsElement />
      <PaymentElement options={{ layout: "accordion" }} />
      <button disabled={isSubmitting || !checkout.canConfirm}>
        {isSubmitting ? "Processing..." : `Pay ${checkout.total.total.amount}`}
      </button>
      {message && <p className="error">{message}</p>}
    </form>
  );
}
```

### 4. Return Page

```jsx
import { useEffect, useState } from "react";

export default function CompletePage() {
  const [status, setStatus] = useState(null);

  useEffect(() => {
    const sessionId = new URLSearchParams(window.location.search).get("session_id");
    fetch(`/api/session-status?session_id=${sessionId}`)
      .then((r) => r.json())
      .then(setStatus);
  }, []);

  if (!status) return <div>Loading...</div>;

  return (
    <div>
      {status.status === "complete" ? (
        <h2>Payment successful!</h2>
      ) : (
        <h2>Payment failed. Please try again.</h2>
      )}
    </div>
  );
}
```

## Payment Element with PaymentIntents

For advanced use cases where you need more control:

```jsx
import { loadStripe } from "@stripe/stripe-js";
import { Elements, PaymentElement, useStripe, useElements } from "@stripe/react-stripe-js";

const stripePromise = loadStripe("pk_test_...");

function PaymentForm() {
  const stripe = useStripe();
  const elements = useElements();
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!stripe || !elements) return;

    const { error } = await stripe.confirmPayment({
      elements,
      confirmParams: {
        return_url: "https://example.com/complete",
      },
    });

    if (error) setError(error.message);
  };

  return (
    <form onSubmit={handleSubmit}>
      <PaymentElement />
      <button disabled={!stripe}>Pay</button>
      {error && <p>{error}</p>}
    </form>
  );
}

export default function App({ clientSecret }) {
  return (
    <Elements stripe={stripePromise} options={{ clientSecret }}>
      <PaymentForm />
    </Elements>
  );
}
```

## Hooks Reference

### Checkout Sessions Hooks

| Hook | Purpose |
|------|---------|
| `useCheckoutElements()` | Access checkout state, total, confirm |

### PaymentIntents Hooks

| Hook | Purpose |
|------|---------|
| `useStripe()` | Access Stripe instance for confirmations |
| `useElements()` | Access Elements instance |

### useCheckoutElements Return

```typescript
type CheckoutState =
  | { type: "loading" }
  | { type: "error"; error: StripeError }
  | {
      type: "success";
      checkout: {
        canConfirm: boolean;
        total: { total: { amount: string } };
        lineItems: LineItem[];
        confirm(): Promise<{ type: "success" } | { type: "error"; error: StripeError }>;
      };
    };
```

## Express Checkout Element

Add Apple Pay, Google Pay, and Link buttons:

```jsx
import { ExpressCheckoutElement } from "@stripe/react-stripe-js";

function ExpressCheckout() {
  return (
    <ExpressCheckoutElement
      onConfirm={async (event) => {
        const { error } = await stripe.confirmPayment({
          elements,
          clientSecret,
          confirmParams: { return_url: "https://example.com/complete" },
        });
        if (error) event.complete("fail");
        else event.complete("success");
      }}
      options={{
        wallets: { applePay: "auto", googlePay: "auto" },
      }}
    />
  );
}
```

## Address and Contact Elements

```jsx
import { AddressElement, ContactDetailsElement } from "@stripe/react-stripe-js/checkout";

function ShippingForm() {
  return (
    <>
      <ContactDetailsElement />
      <AddressElement options={{ mode: "shipping" }} />
      <PaymentElement />
    </>
  );
}
```

## Server-Side Rendering

### Next.js App Router

```jsx
// app/checkout/page.tsx — Server Component
import CheckoutClient from "./CheckoutClient";

export default async function CheckoutPage() {
  return <CheckoutClient />;
}

// app/checkout/CheckoutClient.tsx — Client Component
"use client";
import { loadStripe } from "@stripe/stripe-js";
import { CheckoutElementsProvider } from "@stripe/react-stripe-js/checkout";

const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_KEY!);

export default function CheckoutClient() {
  // ... same as above
}
```

### Important: `loadStripe` must be called client-side only.

```jsx
"use client";
import { loadStripe } from "@stripe/stripe-js";

// Call outside component to avoid re-initialization
const stripePromise = loadStripe("pk_test_...");
```

## Common Pitfalls

- **Calling `loadStripe` inside a component** — Initialize once outside the component to avoid re-creating the Stripe instance
- **Missing `"use client"` directive** — Stripe components are client-only; mark the file or parent as a Client Component in Next.js
- **Not passing `stripe` to provider** — Both `Elements` and `CheckoutElementsProvider` require the Stripe promise
- **Using `Elements` for Checkout Sessions** — Use `CheckoutElementsProvider` for the Checkout Sessions flow, `Elements` for the PaymentIntents flow
- **Not handling the loading state** — `useCheckoutElements()` starts as `{ type: "loading" }`; render a skeleton while loading
- **Accessing `stripe` before initialization** — `useStripe()` returns `null` until Stripe.js loads; always check before using
