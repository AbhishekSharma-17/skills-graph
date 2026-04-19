# Supabase — Edge Functions

> Source: https://supabase.com/docs/guides/functions

## Overview

Supabase Edge Functions are globally distributed, server-side TypeScript functions powered by the Deno runtime. They execute close to your users at the edge, handling webhooks, integrations, background processing, and custom API endpoints that go beyond what PostgREST provides.

## Creating a Function

```bash
# Generate a new function
supabase functions new hello-world
```

This creates `supabase/functions/hello-world/index.ts`:

```typescript
import "jsr:@supabase/functions-js/edge-runtime.d.ts"

Deno.serve(async (req) => {
  const { name } = await req.json()

  return new Response(
    JSON.stringify({ message: `Hello ${name}!` }),
    { headers: { 'Content-Type': 'application/json' } }
  )
})
```

## Local Development

```bash
# Serve all functions locally (hot-reload)
supabase functions serve

# Serve a specific function
supabase functions serve hello-world

# Serve with environment variables
supabase functions serve --env-file ./supabase/.env.local
```

Test locally with curl:

```bash
curl -i --location --request POST \
  'http://localhost:54321/functions/v1/hello-world' \
  --header 'Authorization: Bearer <anon-key>' \
  --header 'Content-Type: application/json' \
  --data '{"name": "World"}'
```

## Deploying Functions

```bash
# Deploy a specific function
supabase functions deploy hello-world

# Deploy all functions
supabase functions deploy

# Deploy with --no-verify-jwt for public endpoints
supabase functions deploy hello-world --no-verify-jwt
```

## Invoking from the Client

```typescript
const { data, error } = await supabase.functions.invoke('hello-world', {
  body: { name: 'World' },
})

// With custom headers
const { data, error } = await supabase.functions.invoke('process-payment', {
  body: { amount: 2999, currency: 'usd' },
  headers: { 'x-idempotency-key': crypto.randomUUID() },
})
```

## CORS Handling

Edge Functions need CORS headers for browser invocation:

```typescript
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

Deno.serve(async (req) => {
  // Handle preflight
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  const data = { message: 'Hello!' }

  return new Response(JSON.stringify(data), {
    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
  })
})
```

## Environment Variables & Secrets

```bash
# Set a secret
supabase secrets set STRIPE_SECRET_KEY=sk_live_xxx

# List secrets
supabase secrets list

# Unset a secret
supabase secrets unset STRIPE_SECRET_KEY
```

Access in functions:

```typescript
Deno.serve(async (req) => {
  const stripeKey = Deno.env.get('STRIPE_SECRET_KEY')

  // Built-in environment variables (auto-available):
  const supabaseUrl = Deno.env.get('SUPABASE_URL')
  const supabaseAnonKey = Deno.env.get('SUPABASE_ANON_KEY')
  const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')
})
```

## Connecting to the Database

```typescript
import { createClient } from "jsr:@supabase/supabase-js@2"

Deno.serve(async (req) => {
  const authHeader = req.headers.get('Authorization')!

  // Client that respects RLS (uses the user's JWT)
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_ANON_KEY')!,
    { global: { headers: { Authorization: authHeader } } }
  )

  const { data, error } = await supabase.from('todos').select('*')

  return new Response(JSON.stringify(data), {
    headers: { 'Content-Type': 'application/json' },
  })
})
```

For admin operations (bypassing RLS):

```typescript
const supabaseAdmin = createClient(
  Deno.env.get('SUPABASE_URL')!,
  Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
)
```

## Webhook Handler Pattern

```typescript
import { createHmac } from "node:crypto"

Deno.serve(async (req) => {
  const body = await req.text()
  const signature = req.headers.get('x-webhook-signature')

  // Verify webhook signature
  const expectedSig = createHmac('sha256', Deno.env.get('WEBHOOK_SECRET')!)
    .update(body)
    .digest('hex')

  if (signature !== expectedSig) {
    return new Response('Invalid signature', { status: 401 })
  }

  const event = JSON.parse(body)

  // Process the webhook event
  switch (event.type) {
    case 'payment.completed':
      // Handle payment
      break
    case 'subscription.cancelled':
      // Handle cancellation
      break
  }

  return new Response(JSON.stringify({ received: true }), {
    headers: { 'Content-Type': 'application/json' },
  })
})
```

## Stripe Integration Example

```typescript
import Stripe from "npm:stripe@17"

const stripe = new Stripe(Deno.env.get('STRIPE_SECRET_KEY')!)

Deno.serve(async (req) => {
  const { priceId, userId } = await req.json()

  const session = await stripe.checkout.sessions.create({
    payment_method_types: ['card'],
    line_items: [{ price: priceId, quantity: 1 }],
    mode: 'subscription',
    success_url: 'https://myapp.com/success',
    cancel_url: 'https://myapp.com/cancel',
    client_reference_id: userId,
  })

  return new Response(JSON.stringify({ url: session.url }), {
    headers: { 'Content-Type': 'application/json' },
  })
})
```

## Shared Code

Place shared modules in `supabase/functions/_shared/`:

```
supabase/functions/
├── _shared/
│   ├── cors.ts
│   ├── supabase-client.ts
│   └── utils.ts
├── hello-world/
│   └── index.ts
└── process-payment/
    └── index.ts
```

```typescript
// _shared/cors.ts
export const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

// hello-world/index.ts
import { corsHeaders } from '../_shared/cors.ts'
```

## Scheduling Functions with pg_cron

```sql
-- Call an edge function every hour
select cron.schedule(
  'hourly-cleanup',
  '0 * * * *',
  $$
  select net.http_post(
    url := 'https://<ref>.supabase.co/functions/v1/cleanup',
    headers := jsonb_build_object(
      'Authorization', 'Bearer ' || '<service-role-key>',
      'Content-Type', 'application/json'
    ),
    body := '{}'::jsonb
  );
  $$
);
```

## Common Pitfalls

1. **Not handling CORS** — Browser requests fail without CORS headers. Always handle `OPTIONS` preflight requests.
2. **Using `service_role` key from client** — Never pass the service role key from browser code. Use Edge Functions as a proxy for privileged operations.
3. **Cold starts** — Edge Functions can have cold starts. Design for short-lived, idempotent operations. Don't rely on in-memory state between invocations.
4. **Import maps** — Deno uses URL imports or JSR. Use `npm:` prefix for npm packages (`import Stripe from "npm:stripe@17"`).
5. **Missing auth header** — By default, functions require a valid JWT. Deploy with `--no-verify-jwt` for public endpoints like webhooks.
6. **Heavy computation** — Edge Functions have execution time limits. Offload heavy work to background jobs or database functions.
