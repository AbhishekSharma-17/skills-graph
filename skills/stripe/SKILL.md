---
name: stripe
description: "Stripe payment processing — Checkout Sessions, Payment Element, subscriptions, webhooks, Connect platforms, Customer Portal, Radar fraud protection, and testing. MANDATORY TRIGGERS: stripe, Stripe, stripe-node, stripe-python, PaymentIntent, CheckoutSession, PaymentElement, stripe.checkout.sessions.create, StripeClient, @stripe/stripe-js, @stripe/react-stripe-js. Also trigger when user wants to accept payments, build a checkout flow, add subscriptions or recurring billing, handle payment webhooks, build a marketplace with Connect, manage customers and payment methods, set up fraud protection, or integrate Stripe into a web application. When in doubt about whether to use this skill for payment tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["stripe", "payments", "checkout", "subscriptions", "webhooks", "connect", "billing", "payment-element", "radar", "saas"]
---

# Stripe — Skill Router

> Complete payment processing platform for internet businesses.

**Source:** [docs.stripe.com](https://docs.stripe.com) | **API:** `2026-05-27.dahlia` | **Node:** `stripe@22.2` | **Python:** `stripe@15.2`

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Setup** | `references/00-overview.md` | Getting started, installation, API keys, SDK setup, architecture |
| **Checkout Sessions** | `references/01-checkout-sessions.md` | Creating checkout flows, embedded vs hosted, line items, modes |
| **Payment Element** | `references/02-payment-element.md` | Embeddable UI, layout options, appearance, 100+ payment methods |
| **Subscriptions & Billing** | `references/03-subscriptions.md` | Recurring payments, plans, trials, proration, cancellation |
| **Webhooks** | `references/04-webhooks.md` | Event handling, signature verification, retries, endpoint setup |
| **Customer Management** | `references/05-customers.md` | Customer Portal, payment methods, saved cards, billing info |
| **Connect Platforms** | `references/06-connect.md` | Marketplaces, SaaS platforms, account types, payouts, fees |
| **Error Handling** | `references/07-error-handling.md` | Error types, decline codes, idempotency, retry strategies |
| **Fraud Protection (Radar)** | `references/08-radar.md` | ML fraud detection, rules, 3DS, risk levels, allow/block lists |
| **Testing** | `references/09-testing.md` | Sandbox mode, test cards, simulating scenarios, Stripe CLI |
| **Stripe CLI** | `references/10-cli.md` | Installation, webhook forwarding, triggers, fixtures, commands |
| **React Integration** | `references/11-react-integration.md` | React hooks, CheckoutElementsProvider, confirm flow, SSR |
| **Security & Compliance** | `references/12-security.md` | PCI compliance, API key management, HTTPS, SCA/3DS, best practices |

## Installation

```bash
# Node.js
npm install stripe @stripe/stripe-js @stripe/react-stripe-js

# Python
pip install stripe

# Stripe CLI
brew install stripe/stripe-cli/stripe   # macOS
stripe login
```

## Quick Reference

- [Stripe Docs](https://docs.stripe.com)
- [API Reference](https://docs.stripe.com/api)
- [Stripe Dashboard](https://dashboard.stripe.com)
- [GitHub (Node)](https://github.com/stripe/stripe-node)
- [GitHub (Python)](https://github.com/stripe/stripe-python)
- [Changelog](https://stripe.com/blog/changelog)
