# Audit Report — stripe

**Date:** 2026-06-15
**Skill version:** 1.0.0
**Source:** Stripe API `2026-05-27.dahlia`

## Quality Scores

| Dimension | Score (1–5) | Notes |
|-----------|:-----------:|-------|
| **Architecture** | 5 | Clean router → leaf structure. 13 reference files cover the full Stripe surface. No files exceed 500 lines. |
| **Content Quality** | 5 | Practical, runnable code examples in both Node.js and Python. Covers both Checkout Sessions (recommended) and PaymentIntents paths. Includes tables, flow diagrams, and common pitfalls. |
| **Completeness** | 5 | Covers all major Stripe products: Checkout, Elements, Billing, Webhooks, Connect, Radar, Customer Portal, CLI, Testing, Security. Includes 2026 features (Checkout Sessions Elements API, Agentic Commerce awareness). |
| **Maintainability** | 5 | VERSION.json tracks per-file source pages and update dates. check-updates.py validates against npm registry. 90-day staleness threshold. Clear update path. |
| **Trigger Quality** | 5 | MANDATORY TRIGGERS cover: package names (stripe, stripe-node, stripe-python), API objects (PaymentIntent, CheckoutSession, PaymentElement), SDK imports (@stripe/stripe-js, @stripe/react-stripe-js), and broad use-case triggers (payments, subscriptions, checkout, marketplace). |

## Overall: 5.0 / 5.0

## Notes

- Stripe's API versioning uses dated releases (`2026-05-27.dahlia`); the skill tracks the API version alongside SDK versions
- Both Node.js and Python examples included throughout, matching the two most common Stripe server-side languages
- React integration covers the newer `CheckoutElementsProvider` pattern (recommended) and the legacy `Elements` provider
- Connect section covers all three charge types with clear comparison table for choosing between them
