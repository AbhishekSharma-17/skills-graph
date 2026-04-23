# PostHog — Event Capture

> Source: [posthog.com/docs/product-analytics/capture-events](https://posthog.com/docs/product-analytics/capture-events) | posthog-js / posthog-python / posthog-node

## Table of Contents

- [Event Model](#event-model)
- [Capturing Events](#capturing-events)
- [Event Properties](#event-properties)
- [Identifying Users](#identifying-users)
- [Anonymous vs Identified Events](#anonymous-vs-identified-events)
- [Person Profiles](#person-profiles)
- [Group Analytics](#group-analytics)
- [Super Properties](#super-properties)
- [Aliasing Users](#aliasing-users)
- [Autocaptured Events](#autocaptured-events)
- [Custom Event Best Practices](#custom-event-best-practices)
- [Server-Side Capture](#server-side-capture)
- [API Capture Endpoint](#api-capture-endpoint)
- [Common Pitfalls](#common-pitfalls)

## Event Model

Everything in PostHog is an event. Each event has:

| Field | Type | Description |
|-------|------|-------------|
| `event` | string | Event name (e.g., `purchase_completed`) |
| `distinct_id` | string | Unique user identifier |
| `properties` | object | Key-value metadata about the event |
| `timestamp` | ISO 8601 | When the event occurred (auto-set if omitted) |

Special properties (auto-captured by JS SDK):
- `$current_url` — page URL where event occurred
- `$host` — hostname
- `$pathname` — URL path
- `$browser` — user's browser
- `$device_type` — desktop/mobile/tablet
- `$os` — operating system
- `$referrer` — referring URL
- `$screen_height` / `$screen_width` — screen dimensions
- `$lib` — SDK that sent the event

## Capturing Events

### JavaScript (Client-Side)

```typescript
// Basic event
posthog.capture('button_clicked');

// Event with properties
posthog.capture('purchase_completed', {
  product_id: 'prod_123',
  amount: 49.99,
  currency: 'USD',
  payment_method: 'credit_card',
});

// Event with timestamp
posthog.capture('signup_completed', {
  plan: 'pro',
  $timestamp: '2026-04-24T10:30:00Z',
});
```

### Python (Server-Side)

```python
import posthog

posthog.capture(
    distinct_id="user_123",
    event="subscription_renewed",
    properties={
        "plan": "enterprise",
        "mrr": 299.00,
        "renewal_count": 3,
    },
)
```

### Node.js (Server-Side)

```typescript
client.capture({
  distinctId: 'user_123',
  event: 'invoice_paid',
  properties: {
    invoiceId: 'inv_456',
    amount: 150.00,
    currency: 'USD',
  },
});
```

## Event Properties

Properties are key-value pairs attached to events. Two categories:

### Event Properties
Set on individual events, describe what happened:

```typescript
posthog.capture('file_uploaded', {
  file_type: 'image/png',
  file_size_mb: 2.5,
  upload_duration_ms: 1200,
});
```

### Person Properties
Attached to the user, persist across events:

```typescript
posthog.setPersonProperties({
  email: 'jane@example.com',
  plan: 'enterprise',
  company_size: 50,
});
```

Property types are auto-detected:
- **String** — text values
- **Numeric** — integers and floats (enable math operations in insights)
- **Boolean** — true/false
- **DateTime** — ISO 8601 strings
- **Array** — list of values

### Property Naming Conventions

```
✓ purchase_completed    (snake_case, verb_noun)
✓ $pageview             ($ prefix = PostHog internal)
✗ PurchaseCompleted     (avoid PascalCase)
✗ purchase completed    (avoid spaces)
```

## Identifying Users

`identify()` links a `distinct_id` to a person profile and sets person properties:

```typescript
// JavaScript
posthog.identify('user_123', {
  email: 'jane@example.com',
  name: 'Jane Doe',
  plan: 'pro',
});
```

```python
# Python
posthog.identify(
    distinct_id="user_123",
    properties={
        "email": "jane@example.com",
        "name": "Jane Doe",
        "plan": "pro",
    },
)
```

### Set Properties vs Set Once

```typescript
posthog.setPersonProperties(
  { plan: 'enterprise' },    // $set — overwrites every time
  { first_seen: '2026-01-15' },  // $set_once — only sets if not already set
);
```

```python
posthog.identify(
    distinct_id="user_123",
    properties={"plan": "enterprise"},        # $set
    properties_set_once={"first_seen": "2026-01-15"},  # $set_once
)
```

## Anonymous vs Identified Events

PostHog handles two types of events:

| Type | Has Person Profile | When |
|------|-------------------|------|
| **Anonymous** | No | Before `identify()` is called |
| **Identified** | Yes | After `identify()` is called |

With `person_profiles: 'identified_only'`:
- Pre-identify events are captured but not linked to a person
- After `identify()`, events are linked and a person profile is created
- Previous anonymous events on the same `distinct_id` are retroactively linked

With `person_profiles: 'always'`:
- A person profile is created for every `distinct_id`, even anonymous ones
- Higher cost (more person profiles)

## Person Profiles

Person profiles store persistent properties about a user:

```typescript
// Update person properties without capturing an event
posthog.setPersonPropertiesForFlags({
  plan: 'enterprise',
  team_size: 25,
});

// These properties are used for feature flag targeting
```

## Group Analytics

Groups let you analyze entities like companies, teams, or projects:

```typescript
// Associate current user with a group
posthog.group('company', 'company_123', {
  name: 'Acme Corp',
  plan: 'enterprise',
  employee_count: 200,
});

// Events after this call include the group association
posthog.capture('feature_used', { feature: 'export' });
// This event is linked to both the user AND company_123
```

```python
# Python — group on a specific event
posthog.capture(
    distinct_id="user_123",
    event="report_generated",
    properties={"report_type": "quarterly"},
    groups={"company": "company_123"},
)

# Set group properties
posthog.group_identify(
    group_type="company",
    group_key="company_123",
    properties={"name": "Acme Corp", "plan": "enterprise"},
)
```

Group types must be defined in Project Settings before use (max 5 group types).

## Super Properties

Super properties are automatically included in every subsequent event:

```typescript
// Register — persists in localStorage, included in every future event
posthog.register({ app_version: '2.1.0', environment: 'production' });

// Register once — only sets if not already set
posthog.register_once({ first_touch_utm: 'google_cpc' });

// Session-only — clears when session ends
posthog.register_for_session({ current_experiment: 'new_onboarding' });

// Unregister
posthog.unregister('app_version');
```

## Aliasing Users

Alias merges two distinct IDs into one person:

```typescript
// Link anonymous ID to authenticated ID
posthog.alias('authenticated_user_123');
// Now the anonymous distinct_id and 'authenticated_user_123' are the same person
```

Use `alias` when you need to explicitly merge two known distinct IDs. For most cases, `identify()` handles merging automatically.

## Autocaptured Events

The JS SDK automatically captures these events:

| Event | Trigger |
|-------|---------|
| `$pageview` | Page load |
| `$pageleave` | Navigation away |
| `$autocapture` | Click, change, submit on interactive elements |
| `$rageclick` | 3+ clicks in 5 seconds in same area |
| `$exception` | Uncaught JavaScript error (if error tracking enabled) |
| `$feature_flag_called` | Feature flag evaluated |

### Controlling Autocapture

```typescript
// Use data attributes to control capture
<button data-ph-capture="true">Tracked</button>
<button data-ph-no-capture>Not tracked</button>

// CSS class to prevent capture
<div class="ph-no-capture">
  <input type="text" /> <!-- inputs here are not captured -->
</div>
```

## Custom Event Best Practices

### Naming Convention
- Use `noun_verb` or `verb_noun` pattern: `purchase_completed`, `file_uploaded`
- Lowercase with underscores
- Be specific: `checkout_step_2_completed` not just `step_completed`
- Avoid dynamic names: `button_clicked` with `{ button_name: 'signup' }`, not `signup_button_clicked`

### Property Design
```typescript
// Good — structured, queryable
posthog.capture('search_performed', {
  query: 'posthog analytics',
  results_count: 15,
  page: 1,
  filters_used: ['date_range', 'category'],
  response_time_ms: 230,
});

// Bad — flat, hard to analyze
posthog.capture('search_posthog_analytics_page1_15results');
```

## Server-Side Capture

### Batch Events

```python
# Python — events are auto-batched (default: 100 events or 0.5s)
posthog.capture("user_1", "event_1")
posthog.capture("user_2", "event_2")
posthog.capture("user_3", "event_3")
# All sent in a single HTTP request

# Configure batching
posthog.max_queue_size = 100  # events per batch
posthog.on_error = lambda e, items: print(f"Error: {e}")
```

### Historical Events

```python
from datetime import datetime

posthog.capture(
    distinct_id="user_123",
    event="order_placed",
    properties={"order_id": "ord_789"},
    timestamp=datetime(2026, 1, 15, 10, 30, 0),
)
```

## API Capture Endpoint

Send events directly via HTTP when no SDK is available:

```bash
curl -X POST 'https://us.i.posthog.com/capture/' \
  -H 'Content-Type: application/json' \
  -d '{
    "api_key": "<ph_project_api_key>",
    "event": "custom_event",
    "distinct_id": "user_123",
    "properties": {
      "key": "value"
    }
  }'
```

### Batch API

```bash
curl -X POST 'https://us.i.posthog.com/batch/' \
  -H 'Content-Type: application/json' \
  -d '{
    "api_key": "<ph_project_api_key>",
    "batch": [
      {"event": "evt_1", "distinct_id": "user_1", "properties": {}, "timestamp": "2026-04-24T10:00:00Z"},
      {"event": "evt_2", "distinct_id": "user_2", "properties": {}, "timestamp": "2026-04-24T10:01:00Z"}
    ]
  }'
```

## Common Pitfalls

1. **Sending PII in event names** — use properties for PII, keep event names generic
2. **Too many unique event names** — high cardinality event names hurt query performance
3. **Not using `$set_once`** — first-touch properties get overwritten by `$set` on every identify
4. **Capturing on page load** — put capture calls in event handlers, not at module scope
5. **Missing `distinct_id` in server-side calls** — every capture must include it; the server SDK doesn't have a session
6. **Not grouping events** — if you need company-level analytics, set up group analytics from the start
