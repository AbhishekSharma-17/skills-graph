# PostHog — Feature Flags

> Source: [posthog.com/docs/feature-flags](https://posthog.com/docs/feature-flags) | posthog-js / posthog-python / posthog-node

## Table of Contents

- [Feature Flags Overview](#feature-flags-overview)
- [Creating Feature Flags](#creating-feature-flags)
- [Release Conditions](#release-conditions)
- [Percentage Rollouts](#percentage-rollouts)
- [Multivariate Flags](#multivariate-flags)
- [Flag Payloads](#flag-payloads)
- [Evaluating Flags — JavaScript](#evaluating-flags--javascript)
- [Evaluating Flags — Python](#evaluating-flags--python)
- [Evaluating Flags — Node.js](#evaluating-flags--nodejs)
- [Local Evaluation](#local-evaluation)
- [Bootstrapping](#bootstrapping)
- [Early Access Features](#early-access-features)
- [Testing Feature Flags](#testing-feature-flags)
- [Best Practices](#best-practices)
- [Common Pitfalls](#common-pitfalls)

## Feature Flags Overview

PostHog feature flags let you toggle features for specific users without deploying new code. Every flag evaluation is tracked as a `$feature_flag_called` event, enabling analytics on flag usage.

Key capabilities:
- **Boolean flags** — on/off for targeted users
- **Multivariate flags** — multiple string variants with percentage splits
- **Payloads** — attach JSON data to flag variants
- **Targeting** — by user properties, cohorts, groups, percentages
- **Local evaluation** — server-side evaluation without API calls
- **Experiments** — flags power A/B tests with statistical analysis

## Creating Feature Flags

### Via UI

1. Navigate to Feature Flags → New Feature Flag
2. Set the flag key (e.g., `new-checkout-flow`)
3. Configure release conditions
4. Optionally add a payload
5. Save and enable

### Via API

```bash
curl -X POST 'https://us.posthog.com/api/projects/<project_id>/feature_flags/' \
  -H 'Authorization: Bearer <personal_api_key>' \
  -H 'Content-Type: application/json' \
  -d '{
    "key": "new-checkout-flow",
    "name": "New Checkout Flow",
    "filters": {
      "groups": [{
        "properties": [],
        "rollout_percentage": 50
      }]
    },
    "active": true
  }'
```

### Flag Key Naming Conventions

```
✓ new-checkout-flow        (kebab-case, descriptive)
✓ enable-dark-mode         (action-oriented)
✓ beta-ai-assistant        (prefixed by stage)
✗ flag_123                 (non-descriptive)
✗ newCheckoutFlow          (avoid camelCase for flag keys)
```

## Release Conditions

Release conditions define which users see a flag. Multiple condition sets are OR'd together (user matches any set).

### User Property Targeting

```
Release condition 1:
  Match users where:
    email contains '@acme.com'
    AND plan = 'enterprise'
  Rollout: 100%
```

### Cohort Targeting

```
Release condition 1:
  Match users in cohort: "Beta Testers"
  Rollout: 100%
```

### Group Targeting

```
Release condition 1:
  Match groups where:
    group_type = 'company'
    AND company.plan = 'enterprise'
  Rollout: 100%
```

### Multiple Conditions (OR Logic)

```
Condition 1: email contains '@acme.com' → 100%
OR
Condition 2: cohort = 'Beta Testers' → 100%
OR
Condition 3: All users → 10%
```

Conditions are evaluated top to bottom; the first match wins.

## Percentage Rollouts

Gradual rollouts let you expose a flag to a percentage of users:

```
Release condition:
  All users
  Rollout: 25%   ← 25% of users see the feature
```

Rollout is deterministic per user — the same user always gets the same result (based on a hash of their `distinct_id` and the flag key).

### Progressive Rollout Strategy

```
Day 1:   5%  — internal team
Day 3:  25%  — check error rates
Day 5:  50%  — monitor metrics
Day 7: 100%  — full rollout
```

## Multivariate Flags

Instead of boolean on/off, multivariate flags return one of several string variants:

```
Flag: checkout-layout
Variants:
  - control:    33%
  - single-page: 33%
  - multi-step:  34%
```

Evaluation returns the variant name (e.g., `"single-page"`) or `false` if the user is not in the flag.

## Flag Payloads

Attach JSON data to each variant:

```json
{
  "control": {
    "button_color": "blue",
    "heading": "Welcome back"
  },
  "variant-a": {
    "button_color": "green",
    "heading": "Start your free trial"
  }
}
```

Payloads let you configure UI without code changes — colors, copy, limits, thresholds.

## Evaluating Flags — JavaScript

```typescript
// Check boolean flag
if (posthog.isFeatureEnabled('new-checkout-flow')) {
  showNewCheckout();
}

// Get multivariate variant
const variant = posthog.getFeatureFlag('checkout-layout');
if (variant === 'single-page') {
  renderSinglePageCheckout();
} else if (variant === 'multi-step') {
  renderMultiStepCheckout();
}

// Get payload
const payload = posthog.getFeatureFlagPayload('checkout-layout');
// { button_color: 'green', heading: 'Start your free trial' }

// React hook
import { useFeatureFlagEnabled, useFeatureFlagVariantKey, useFeatureFlagPayload } from 'posthog-js/react';

function MyComponent() {
  const isEnabled = useFeatureFlagEnabled('new-checkout-flow');
  const variant = useFeatureFlagVariantKey('checkout-layout');
  const payload = useFeatureFlagPayload('checkout-layout');

  if (!isEnabled) return <OldCheckout />;
  return <NewCheckout variant={variant} config={payload} />;
}

// Listen for flag changes
posthog.onFeatureFlags((flags, variants) => {
  console.log('Flags loaded:', flags);
  console.log('Variants:', variants);
});
```

## Evaluating Flags — Python

```python
import posthog

# Boolean check
is_enabled = posthog.feature_enabled(
    key="new-checkout-flow",
    distinct_id="user_123",
)

# Get variant
variant = posthog.get_feature_flag(
    key="checkout-layout",
    distinct_id="user_123",
)
# Returns: 'single-page', 'multi-step', 'control', or False

# Get payload
payload = posthog.get_feature_flag_payload(
    key="checkout-layout",
    distinct_id="user_123",
)

# With person properties (for targeting)
is_enabled = posthog.feature_enabled(
    key="enterprise-features",
    distinct_id="user_123",
    person_properties={"plan": "enterprise", "company_size": 200},
)

# With group properties
is_enabled = posthog.feature_enabled(
    key="company-dashboard",
    distinct_id="user_123",
    groups={"company": "company_123"},
    group_properties={"company": {"plan": "enterprise"}},
)
```

## Evaluating Flags — Node.js

```typescript
import { PostHog } from 'posthog-node';

const client = new PostHog('<api_key>', { host: 'https://us.i.posthog.com' });

// Boolean check
const isEnabled = await client.isFeatureEnabled('new-checkout-flow', 'user_123');

// Get variant
const variant = await client.getFeatureFlag('checkout-layout', 'user_123');

// Get payload
const payload = await client.getFeatureFlagPayload('checkout-layout', 'user_123');

// With properties for server-side targeting
const isEnabled = await client.isFeatureEnabled('enterprise-features', 'user_123', {
  personProperties: { plan: 'enterprise' },
  groups: { company: 'company_123' },
  groupProperties: { company: { plan: 'enterprise' } },
});
```

## Local Evaluation

Server-side SDKs can evaluate flags locally, avoiding an API call per evaluation:

```python
# Python — local evaluation
from posthog import Posthog

posthog = Posthog(
    api_key="<ph_project_api_key>",
    host="https://us.i.posthog.com",
    personal_api_key="<personal_api_key>",  # required for local eval
)

# Flag definitions are fetched and cached locally
# Evaluations happen instantly without API calls
is_enabled = posthog.feature_enabled(
    key="new-checkout-flow",
    distinct_id="user_123",
    person_properties={"plan": "enterprise"},  # must provide properties
)
```

```typescript
// Node.js — local evaluation
const client = new PostHog('<api_key>', {
  host: 'https://us.i.posthog.com',
  personalApiKey: '<personal_api_key>',
  featureFlagsPollingInterval: 30000, // refresh every 30s
});
```

Local evaluation limitations:
- Must provide person/group properties at evaluation time (can't look up from PostHog)
- Cohort-based flags fall back to API evaluation
- Flag definitions are polled (default: every 30s)

## Bootstrapping

Load flags instantly on page load by bootstrapping values:

```typescript
posthog.init('<key>', {
  bootstrap: {
    featureFlags: {
      'new-checkout-flow': true,
      'checkout-layout': 'single-page',
    },
    featureFlagPayloads: {
      'checkout-layout': { button_color: 'green' },
    },
  },
});
```

Bootstrap values from server-side rendering:

```typescript
// Next.js getServerSideProps
export async function getServerSideProps(context) {
  const client = new PostHog('<api_key>');
  const flags = await client.getAllFlags('user_123');
  const payloads = await client.getAllFeatureFlagPayloads('user_123');

  return {
    props: {
      bootstrapData: { featureFlags: flags, featureFlagPayloads: payloads },
    },
  };
}
```

## Early Access Features

Let users opt into beta features themselves:

1. Create a feature flag with "Early Access" enabled
2. Users see an opt-in UI (or use the API)
3. Track adoption and feedback before full rollout

```typescript
// Get available early access features
posthog.getEarlyAccessFeatures((features) => {
  // features = [{ id, name, description, flagKey, stage }]
});

// Opt a user in
posthog.updateEarlyAccessFeatureEnrollment('feature-id', true);
```

## Testing Feature Flags

### Override Flags in Development

```typescript
// JavaScript — override for testing
posthog.featureFlags.override({
  'new-checkout-flow': true,
  'checkout-layout': 'single-page',
});

// Clear overrides
posthog.featureFlags.override(false);
```

### URL-Based Override

Add `__posthog_flag_key=value` to the URL:
```
https://yourapp.com?__posthog_flag_new-checkout-flow=true
```

### Python Testing

```python
# Mock feature flags in tests
from unittest.mock import patch

@patch('posthog.feature_enabled', return_value=True)
def test_new_checkout(mock_flag):
    result = show_checkout()
    assert result == 'new_checkout'
```

## Best Practices

1. **Name flags descriptively** — `enable-ai-assistant` not `flag-42`
2. **Clean up stale flags** — remove flags after full rollout
3. **Use payloads for configuration** — avoid hardcoding values behind flags
4. **Monitor flag evaluations** — check `$feature_flag_called` events for unexpected patterns
5. **Start with small rollouts** — 5% → 25% → 50% → 100%
6. **Use cohorts for targeting** — cleaner than complex property conditions
7. **Default to `false`** — new flags should be off by default; enable explicitly

## Common Pitfalls

1. **Flickering on page load** — use bootstrapping to eliminate the delay before flags load
2. **Not providing properties for local evaluation** — local eval needs properties passed explicitly
3. **Stale flags accumulating** — set reminders to clean up flags after rollout
4. **Testing with wrong distinct_id** — percentage rollouts are deterministic per user; switch users to test both paths
5. **Not handling the `false` case** — always provide a fallback for when a flag is disabled
