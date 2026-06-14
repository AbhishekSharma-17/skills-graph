# Stripe — Payment Element

> Source: [docs.stripe.com/payments/payment-element](https://docs.stripe.com/payments/payment-element) | API `2026-05-27.dahlia`

## Table of Contents

- [Overview](#overview)
- [Payment Element vs Other Elements](#payment-element-vs-other-elements)
- [Setup with Checkout Sessions](#setup-with-checkout-sessions)
- [Layout Options](#layout-options)
- [Appearance Customization](#appearance-customization)
- [Configuration Options](#configuration-options)
- [Supported Payment Methods](#supported-payment-methods)
- [Combining Elements](#combining-elements)
- [Error Display](#error-display)
- [Common Pitfalls](#common-pitfalls)

## Overview

The Payment Element is a secure, pre-built UI component that accepts 100+ payment methods. It handles input validation, error messages, localization, and dynamically shows relevant payment methods based on customer location, currency, and transaction amount.

## Payment Element vs Other Elements

| Element | Purpose | Payment Methods |
|---------|---------|----------------|
| **Payment Element** | All-in-one payment form | 100+ methods, auto-detected |
| **Card Element** | Card-only input (legacy) | Cards only |
| **Express Checkout Element** | Wallet buttons (Apple Pay, Google Pay) | Wallets only |
| **Address Element** | Shipping/billing address collection | N/A |
| **Contact Details Element** | Autofill checkout info | N/A |

The Payment Element replaces the Card Element for new integrations.

## Setup with Checkout Sessions

### Server — Create Checkout Session

```javascript
const session = await stripe.checkout.sessions.create({
  ui_mode: "elements",
  line_items: [{ price: "price_xxx", quantity: 1 }],
  mode: "payment",
  return_url: "https://example.com/complete?session_id={CHECKOUT_SESSION_ID}",
});
res.json({ clientSecret: session.client_secret });
```

### Client — Mount Payment Element

```javascript
const stripe = Stripe("pk_test_...");

const checkout = stripe.initCheckoutElementsSdk({
  clientSecret: "cs_xxx_secret_yyy",
  elementsOptions: { appearance: { theme: "stripe" } },
});

const paymentElement = checkout.createPaymentElement();
paymentElement.mount("#payment-element");
```

### Client — Confirm Payment

```javascript
const loadActionsResult = await checkout.loadActions();
if (loadActionsResult.type === "success") {
  const { error } = await loadActionsResult.actions.confirm();
  if (error) {
    console.error(error.message);
  }
}
```

## Layout Options

### Tabs (Default)

Displays payment methods as horizontal tabs:

```javascript
const paymentElement = checkout.createPaymentElement({
  layout: {
    type: "tabs",
    defaultCollapsed: false,
  },
});
```

### Accordion with Radio Buttons

Vertical list with radio selection:

```javascript
const paymentElement = checkout.createPaymentElement({
  layout: {
    type: "accordion",
    defaultCollapsed: false,
    radios: "always",
    spacedAccordionItems: false,
  },
});
```

### Accordion without Radios

Vertical list with spacing:

```javascript
const paymentElement = checkout.createPaymentElement({
  layout: {
    type: "accordion",
    defaultCollapsed: false,
    radios: "never",
    spacedAccordionItems: true,
  },
});
```

## Appearance Customization

Use the Appearance API to control styling:

```javascript
const appearance = {
  theme: "stripe", // 'stripe' | 'flat' | 'night'
  variables: {
    colorPrimary: "#0066cc",
    colorBackground: "#ffffff",
    colorText: "#30313d",
    colorDanger: "#df1b41",
    fontFamily: "Inter, system-ui, sans-serif",
    spacingUnit: "4px",
    borderRadius: "8px",
  },
  rules: {
    ".Input": {
      border: "1px solid #e0e0e0",
      boxShadow: "none",
    },
    ".Input:focus": {
      border: "1px solid #0066cc",
      boxShadow: "0 0 0 1px #0066cc",
    },
    ".Tab--selected": {
      borderColor: "#0066cc",
      color: "#0066cc",
    },
  },
};

const checkout = stripe.initCheckoutElementsSdk({
  clientSecret,
  elementsOptions: { appearance },
});
```

### Available Themes

| Theme | Description |
|-------|-------------|
| `stripe` | Default Stripe styling |
| `flat` | Flat design, minimal shadows |
| `night` | Dark mode theme |

## Configuration Options

```javascript
const paymentElement = checkout.createPaymentElement({
  layout: { type: "tabs" },
  defaultValues: {
    billingDetails: {
      name: "Jenny Rosen",
      email: "jenny@example.com",
    },
  },
  business: { name: "RocketRides" },
  paymentMethodOrder: ["card", "apple_pay", "google_pay"],
  fields: {
    billingDetails: {
      address: { country: "never" },
    },
  },
  wallets: { applePay: "auto", googlePay: "auto" },
  terms: { card: "auto" },
});
```

| Option | Description |
|--------|-------------|
| `layout` | Tabs or accordion display |
| `defaultValues` | Pre-fill customer info |
| `business` | Business name display |
| `paymentMethodOrder` | Custom method ordering |
| `fields` | Show/hide specific fields |
| `readOnly` | Prevent editing |
| `wallets` | Apple Pay, Google Pay config |
| `terms` | Legal agreement display |

## Supported Payment Methods

Payment methods are dynamically shown based on:
- Customer location (IP-based)
- Transaction currency
- Transaction amount
- Dashboard configuration

### Major Categories

| Category | Methods |
|----------|---------|
| **Cards** | Visa, Mastercard, Amex, Discover, JCB, UnionPay, Diners |
| **Wallets** | Apple Pay, Google Pay, Link |
| **Europe** | iDEAL, Bancontact, SEPA, giropay, EPS, Sofort, Klarna |
| **Asia** | Alipay, WeChat Pay, GrabPay, PayNow, GCash |
| **Americas** | Boleto, OXXO, PSE |
| **BNPL** | Klarna, Affirm, Afterpay/Clearpay |

Manage enabled methods in the [Dashboard](https://dashboard.stripe.com/settings/payment_methods) — no code changes needed.

## Combining Elements

The Payment Element works with other Elements for a complete checkout:

```html
<div id="contact-details-element"></div>
<div id="address-element"></div>
<div id="payment-element"></div>
<button id="submit">Pay</button>
```

```javascript
const contactDetails = checkout.createContactDetailsElement();
contactDetails.mount("#contact-details-element");

const addressElement = checkout.createAddressElement({ mode: "shipping" });
addressElement.mount("#address-element");

const paymentElement = checkout.createPaymentElement();
paymentElement.mount("#payment-element");
```

When using Apple Pay or Google Pay via the Payment Element alongside the Express Checkout Element, set `wallets: { applePay: "never", googlePay: "never" }` on the Payment Element to avoid duplication.

## Error Display

The Payment Element automatically displays localized error messages for common card errors:

| Error Code | Meaning |
|------------|---------|
| `card_declined` | Card was declined |
| `expired_card` | Card has expired |
| `incorrect_cvc` | CVC is incorrect |
| `incorrect_number` | Card number is incorrect |
| `insufficient_funds` | Card has insufficient funds |
| `processing_error` | Processing error occurred |

Server-side errors from PaymentIntent confirmation are returned in the `confirm()` response:

```javascript
const { error } = await checkout.confirm();
if (error) {
  // error.type — 'card_error', 'validation_error', etc.
  // error.message — Human-readable message
  showError(error.message);
}
```

## Common Pitfalls

- **Not using `initCheckoutElementsSdk`** — This is the new recommended API; `elements.create('payment')` is the legacy path
- **Missing `clientSecret`** — The Payment Element requires a Checkout Session or PaymentIntent client secret to render
- **Wallet button duplication** — If using Express Checkout Element separately, disable wallets on the Payment Element
- **Not listening for `change` events** — Use `checkout.on('change', ...)` to enable/disable the submit button based on `canConfirm`
- **Custom fonts not loading** — Fonts must be specified in the `fonts` option of `elements()`, not just in CSS
