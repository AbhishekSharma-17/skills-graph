# Stripe — Connect Platforms

> Source: [docs.stripe.com/connect](https://docs.stripe.com/connect) | API `2026-05-27.dahlia`

## Table of Contents

- [Overview](#overview)
- [Use Cases](#use-cases)
- [Account Types](#account-types)
- [Charge Types](#charge-types)
- [Onboarding Connected Accounts](#onboarding-connected-accounts)
- [Creating Charges with Splits](#creating-charges-with-splits)
- [Payouts](#payouts)
- [Platform Fees](#platform-fees)
- [Embedded Components](#embedded-components)
- [Common Pitfalls](#common-pitfalls)

## Overview

Stripe Connect enables platforms and marketplaces to process payments for multiple parties. It handles onboarding, verification, payment splitting, payouts, and tax reporting (1099s) for your connected accounts.

## Use Cases

| Platform Type | Example | Money Flow |
|---------------|---------|------------|
| **Marketplace** | Etsy, Uber | Customer → Platform → Seller/Provider |
| **SaaS Platform** | Shopify, Squarespace | Customer → Merchant (via platform) |
| **Crowdfunding** | Kickstarter | Backer → Campaign Creator |
| **On-demand Services** | DoorDash, Fiverr | Customer → Platform → Service Provider |

## Account Types

| Type | Dashboard | Onboarding | Branding | Best For |
|------|-----------|------------|----------|----------|
| **Standard** | Full Stripe Dashboard | Stripe-hosted | Seller's | Platforms where sellers manage own payments |
| **Express** | Limited Dashboard | Stripe-hosted | Platform's | Marketplaces with lighter seller needs |
| **Custom** | None (you build UI) | You build it | Platform's | Full control over UX |

### Standard Account (Simplest)

```javascript
const account = await stripe.accounts.create({ type: "standard" });

// Generate onboarding link
const link = await stripe.accountLinks.create({
  account: account.id,
  refresh_url: "https://example.com/reauth",
  return_url: "https://example.com/complete",
  type: "account_onboarding",
});
// Redirect user to link.url
```

### Express Account

```javascript
const account = await stripe.accounts.create({
  type: "express",
  country: "US",
  capabilities: {
    card_payments: { requested: true },
    transfers: { requested: true },
  },
});
```

### Custom Account

```javascript
const account = await stripe.accounts.create({
  type: "custom",
  country: "US",
  capabilities: {
    card_payments: { requested: true },
    transfers: { requested: true },
  },
  business_type: "individual",
  business_profile: {
    mcc: "5734",
    url: "https://seller-example.com",
  },
});
```

## Charge Types

### Direct Charges

The connected account is the merchant of record. Use for platforms where sellers have a direct relationship with buyers:

```javascript
const paymentIntent = await stripe.paymentIntents.create(
  {
    amount: 2000,
    currency: "usd",
    application_fee_amount: 200, // Platform fee
  },
  { stripeAccount: "acct_seller_xxx" } // On behalf of connected account
);
```

### Destination Charges

The platform is the merchant of record. Payment is on the platform, funds transfer to connected account:

```javascript
const paymentIntent = await stripe.paymentIntents.create({
  amount: 2000,
  currency: "usd",
  transfer_data: {
    destination: "acct_seller_xxx",
  },
  application_fee_amount: 200,
});
```

### Separate Charges and Transfers

Full control — create the charge, then manually transfer:

```javascript
// Step 1: Charge the customer
const charge = await stripe.paymentIntents.create({
  amount: 2000,
  currency: "usd",
});

// Step 2: Transfer to seller
const transfer = await stripe.transfers.create({
  amount: 1800,
  currency: "usd",
  destination: "acct_seller_xxx",
  transfer_group: "order_123",
});
```

### Choosing a Charge Type

| Criteria | Direct | Destination | Separate |
|----------|--------|-------------|----------|
| Merchant of record | Connected account | Platform | Platform |
| Refund responsibility | Connected account | Platform | Platform |
| Dispute handling | Connected account | Platform | Platform |
| Multi-seller orders | No | No | Yes |
| Complexity | Low | Low | High |

## Onboarding Connected Accounts

### Account Links (Stripe-Hosted Onboarding)

```javascript
const accountLink = await stripe.accountLinks.create({
  account: "acct_xxx",
  refresh_url: "https://example.com/reauth",
  return_url: "https://example.com/onboarding-complete",
  type: "account_onboarding",
});
// Redirect to accountLink.url
```

### Check Onboarding Status

```javascript
const account = await stripe.accounts.retrieve("acct_xxx");

if (account.charges_enabled && account.payouts_enabled) {
  console.log("Account fully onboarded");
} else if (account.requirements.currently_due.length > 0) {
  console.log("Missing requirements:", account.requirements.currently_due);
}
```

### Listen for Account Updates

```javascript
case "account.updated":
  const account = event.data.object;
  if (account.charges_enabled) {
    enableSellerPayments(account.id);
  }
  break;
```

## Creating Charges with Splits

### Multi-Seller Order (Separate Charges)

```javascript
const paymentIntent = await stripe.paymentIntents.create({
  amount: 5000, // $50.00 total
  currency: "usd",
  transfer_group: "order_456",
});

// After payment succeeds, split to sellers
await stripe.transfers.create({
  amount: 2500,
  currency: "usd",
  destination: "acct_seller_1",
  transfer_group: "order_456",
});

await stripe.transfers.create({
  amount: 2000,
  currency: "usd",
  destination: "acct_seller_2",
  transfer_group: "order_456",
});
// Platform keeps $5.00
```

## Payouts

Connected account payouts are managed by Stripe by default:

```javascript
// Check payout schedule
const account = await stripe.accounts.retrieve("acct_xxx");
console.log(account.settings.payouts.schedule);

// Manual payout (if enabled)
const payout = await stripe.payouts.create(
  { amount: 1000, currency: "usd" },
  { stripeAccount: "acct_xxx" }
);
```

## Platform Fees

### Application Fee

```javascript
const paymentIntent = await stripe.paymentIntents.create({
  amount: 2000,
  currency: "usd",
  application_fee_amount: 200, // $2.00 platform fee
  transfer_data: { destination: "acct_xxx" },
});
```

### Refunding Application Fees

```javascript
const refund = await stripe.refunds.create({
  payment_intent: "pi_xxx",
  refund_application_fee: true, // Also refund the platform fee
});
```

## Embedded Components

Add Connect dashboard functionality to your platform UI:

```javascript
// Create an Account Session for embedded components
const accountSession = await stripe.accountSessions.create({
  account: "acct_xxx",
  components: {
    payments: { enabled: true },
    payouts: { enabled: true },
  },
});
// Use accountSession.client_secret to initialize embedded components
```

## Common Pitfalls

- **Not handling verification requirements** — Connected accounts may need additional documents; monitor `account.updated` webhooks
- **Ignoring payout failures** — Listen for `payout.failed` events to handle bank account issues
- **Wrong charge type for multi-seller** — Only separate charges/transfers support splitting across multiple sellers
- **Not configuring capabilities** — Request `card_payments` and `transfers` capabilities explicitly
- **Assuming instant onboarding** — Verification can take days; handle intermediate states
- **Forgetting the `stripeAccount` header** — For direct charges, you must pass the connected account ID
