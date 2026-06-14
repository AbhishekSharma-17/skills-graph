# Stripe — CLI

> Source: [docs.stripe.com/stripe-cli](https://docs.stripe.com/stripe-cli) | API `2026-05-27.dahlia`

## Overview

The Stripe CLI is a command-line tool for managing Stripe resources, testing webhooks locally, triggering events, and debugging integrations without leaving the terminal.

## Installation

### macOS

```bash
brew install stripe/stripe-cli/stripe
```

### Windows (Scoop)

```bash
scoop bucket add stripe https://github.com/stripe/scoop-stripe-cli.git
scoop install stripe
```

### Linux (apt)

```bash
curl -s https://packages.stripe.dev/api/security/keypair/stripe-cli-gpg/public | gpg --dearmor | sudo tee /usr/share/keyrings/stripe.gpg
echo "deb [signed-by=/usr/share/keyrings/stripe.gpg] https://packages.stripe.dev/stripe-cli-debian-local stable main" | sudo tee -a /etc/apt/sources.list.d/stripe.list
sudo apt update && sudo apt install stripe
```

### Docker

```bash
docker run --rm -it stripe/stripe-cli
```

## Authentication

```bash
# Interactive login (opens browser)
stripe login

# Login with API key
stripe login --api-key sk_test_...

# Check current status
stripe config --list
```

## Webhook Forwarding

The most common CLI use case — forward Stripe events to your local server:

```bash
# Forward all events
stripe listen --forward-to localhost:4242/webhook
# Output: Ready! Your webhook signing secret is 'whsec_...'

# Forward specific events
stripe listen \
  --events payment_intent.succeeded,invoice.paid,customer.subscription.deleted \
  --forward-to localhost:4242/webhook

# Forward from a registered webhook endpoint
stripe listen --load-from-webhooks-api --forward-to localhost:4242/webhook
```

Use the `whsec_` secret printed by `stripe listen` as your `STRIPE_WEBHOOK_SECRET` environment variable.

## Triggering Events

```bash
# Trigger a predefined event
stripe trigger payment_intent.succeeded
stripe trigger invoice.payment_failed
stripe trigger customer.subscription.created
stripe trigger charge.dispute.created
stripe trigger checkout.session.completed

# List all available triggers
stripe trigger --help
```

## Resource Management

### Create Resources

```bash
# Create a customer
stripe customers create --email="test@example.com" --name="Test User"

# Create a product
stripe products create --name="Pro Plan" --description="Monthly subscription"

# Create a price
stripe prices create \
  --product=prod_xxx \
  --unit-amount=2000 \
  --currency=usd \
  --recurring-interval=month
```

### Retrieve Resources

```bash
# Get a specific resource
stripe customers retrieve cus_xxx
stripe payment_intents retrieve pi_xxx
stripe subscriptions retrieve sub_xxx

# List resources
stripe customers list --limit=5
stripe charges list --limit=10
stripe invoices list --customer=cus_xxx
```

### Update Resources

```bash
stripe customers update cus_xxx --name="Updated Name"
stripe subscriptions update sub_xxx --cancel-at-period-end=true
```

## Logs and Events

```bash
# View recent API logs
stripe logs tail

# Filter logs by status
stripe logs tail --filter-status-code=400

# View recent events
stripe events list --limit=10

# Resend a failed event
stripe events resend evt_xxx --webhook-endpoint=we_xxx
```

## Sandbox Management

```bash
# Create a new sandbox
stripe sandbox create --name="feature-test"

# List sandboxes
stripe sandbox list

# Switch to a sandbox
stripe sandbox activate sandbox_xxx
```

## Fixtures

Fixtures create a set of related API objects for testing:

```bash
# Run a built-in fixture
stripe fixtures path/to/fixture.json
```

### Custom Fixture File

```json
{
  "_meta": {
    "template_version": 0
  },
  "fixtures": [
    {
      "name": "product",
      "path": "/v1/products",
      "method": "post",
      "params": {
        "name": "Test Product",
        "description": "A test product"
      }
    },
    {
      "name": "price",
      "path": "/v1/prices",
      "method": "post",
      "params": {
        "product": "${product:id}",
        "unit_amount": 2000,
        "currency": "usd",
        "recurring": {
          "interval": "month"
        }
      }
    },
    {
      "name": "customer",
      "path": "/v1/customers",
      "method": "post",
      "params": {
        "email": "test@example.com",
        "name": "Test Customer"
      }
    }
  ]
}
```

```bash
stripe fixtures my-fixture.json
```

## Useful Commands Reference

| Command | Purpose |
|---------|---------|
| `stripe login` | Authenticate |
| `stripe listen` | Forward webhooks locally |
| `stripe trigger <event>` | Fire a test event |
| `stripe logs tail` | Stream API logs |
| `stripe customers create` | Create a customer |
| `stripe products create` | Create a product |
| `stripe prices create` | Create a price |
| `stripe payment_intents create` | Create a PaymentIntent |
| `stripe events list` | List recent events |
| `stripe events resend` | Retry a webhook delivery |
| `stripe sandbox create` | Create a test sandbox |
| `stripe fixtures` | Run a fixture file |
| `stripe config --list` | Show current configuration |
| `stripe help` | Show help |
| `stripe completion` | Shell autocompletion setup |

## Common Pitfalls

- **Forgetting to run `stripe listen`** — Webhooks won't reach your local server without it
- **Using the wrong webhook secret** — The `whsec_` from `stripe listen` is different from Dashboard webhook secrets
- **Not filtering events** — Forward only the events you handle; reduces noise
- **Ignoring `stripe logs tail`** — Great for debugging API errors in real time
- **Not using fixtures** — Manually creating test data via the Dashboard is slower than fixtures
