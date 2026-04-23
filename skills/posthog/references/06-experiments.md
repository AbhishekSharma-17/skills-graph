# PostHog — Experiments (A/B Testing)

> Source: [posthog.com/docs/experiments](https://posthog.com/docs/experiments) | PostHog Cloud / Self-Hosted

## Table of Contents

- [Experiments Overview](#experiments-overview)
- [How Experiments Work](#how-experiments-work)
- [Creating an Experiment](#creating-an-experiment)
- [Goal Metrics](#goal-metrics)
- [Statistical Methodology](#statistical-methodology)
- [Interpreting Results](#interpreting-results)
- [Multivariate Experiments](#multivariate-experiments)
- [Experiment Without Feature Flags](#experiment-without-feature-flags)
- [Holdout Groups](#holdout-groups)
- [Implementation Patterns](#implementation-patterns)
- [Common Pitfalls](#common-pitfalls)

## Experiments Overview

PostHog experiments are A/B tests built on top of feature flags. They add measurement and statistical analysis to flag variants — you define a goal metric, PostHog splits users randomly, and you get a statistically rigorous answer about which variant wins.

Key capabilities:
- **Powered by feature flags** — same targeting and rollout controls
- **Bayesian statistics** — probability of each variant winning
- **Funnel and trend goals** — measure conversion or event frequency
- **Minimum sample size** — calculates required sample size upfront
- **Significance tracking** — shows when results are statistically significant
- **Secondary metrics** — track guardrail metrics alongside the primary goal

## How Experiments Work

```
1. Create experiment with a feature flag key
2. Define control + variant(s) with percentage splits
3. Set primary goal metric (funnel conversion or trend)
4. Launch experiment → flag starts serving variants
5. PostHog tracks goal events per variant
6. Results page shows conversion rates + statistical significance
7. End experiment → roll out winning variant or revert
```

Each experiment is backed by a feature flag. The flag handles random assignment; the experiment adds:
- Goal metric tracking
- Statistical significance calculation
- Recommended sample size
- Results visualization

## Creating an Experiment

### Step 1: Define the Hypothesis

```
Hypothesis: "Changing the CTA button from blue to green will increase
             signup conversion by 10%"
```

### Step 2: Configure the Experiment

```
Name: Green CTA Button Test
Feature flag key: cta-button-color
Variants:
  - control (50%): existing blue button
  - test (50%): green button

Minimum acceptable improvement: 10%
```

### Step 3: Set the Goal Metric

```
Primary metric:
  Type: Funnel
  Steps: cta_button_clicked → signup_completed
  
Secondary metrics:
  - Trend: page_bounce (guardrail — should not increase)
  - Trend: time_on_page (secondary observation)
```

### Step 4: Calculate Sample Size

PostHog calculates the recommended sample size based on:
- Current baseline conversion rate
- Minimum detectable effect (MDE)
- Statistical power (default: 80%)
- Significance level (default: 95%)

```
Baseline: 5% conversion
MDE: 10% relative improvement (5% → 5.5%)
Required: ~30,000 users per variant
Estimated duration: ~14 days at current traffic
```

### Step 5: Launch

Click "Launch" to start the experiment. The feature flag begins serving variants immediately.

## Goal Metrics

### Funnel Goal

Measures conversion through a series of steps:

```
Steps:
  1. pricing_page_viewed
  2. checkout_started
  3. purchase_completed

Metric: Conversion rate from step 1 to step 3
```

### Trend Goal

Measures event count or property value:

```
Event: purchase_completed
Aggregation: Count per user
  OR
Event: purchase_completed
Aggregation: Sum of amount property (revenue)
```

### Secondary Metrics

Monitor guardrail metrics to ensure the variant doesn't hurt other areas:

```
Primary: signup conversion rate (should increase)
Secondary 1: page load time (should not increase)
Secondary 2: support ticket rate (should not increase)
Secondary 3: revenue per user (observation)
```

## Statistical Methodology

PostHog uses **Bayesian statistics** for experiment analysis:

### Key Concepts

| Metric | Description |
|--------|-------------|
| **Probability of winning** | Likelihood that a variant is the best (0-100%) |
| **Credible interval** | Range where the true value likely falls (95%) |
| **Expected improvement** | Estimated lift over control |
| **Significance** | Whether results are conclusive (>95% probability) |

### When to Call an Experiment

PostHog recommends calling an experiment when:
1. The winning variant has >95% probability of being best
2. The experiment has run for at least the recommended sample size
3. There's been enough time to account for day-of-week effects (at least 1 full week)

### Statistical Power

```
Low traffic:  Need more time, consider larger MDE
High traffic: Results come faster, can detect smaller effects
```

## Interpreting Results

### Results Dashboard

```
Variant    | Users  | Conversion | Improvement | Win Probability
-----------|--------|------------|-------------|----------------
Control    | 15,432 | 4.8%       | baseline    | 12%
Test       | 15,501 | 5.6%       | +16.7%      | 88%
```

### Decision Framework

| Win Probability | Action |
|-----------------|--------|
| >95% for test | Ship the test variant |
| >95% for control | Revert to control |
| 50-95% | Continue running, need more data |
| ~50% | No meaningful difference; pick based on other criteria |

### After Calling the Experiment

1. **Winner identified** → Set the feature flag to 100% for the winning variant
2. **No winner** → Revert to control or redesign the test
3. **Document results** → Record the experiment outcome and learnings

## Multivariate Experiments

Test more than two variants simultaneously:

```
Flag: onboarding-flow
Variants:
  - control (25%): existing flow
  - variant-a (25%): simplified 3-step flow
  - variant-b (25%): video-guided flow
  - variant-c (25%): interactive tutorial

Goal: onboarding_completed (Trend, unique users)
```

Considerations:
- More variants = more users needed for significance
- Each variant needs enough traffic independently
- Recommended: max 4-5 variants per experiment

## Experiment Without Feature Flags

Run experiments on changes that don't use feature flags:

```python
# Backend: expose an event with the variant
posthog.capture(
    distinct_id="user_123",
    event="$feature_flag_called",
    properties={
        "$feature_flag": "email-subject-test",
        "$feature_flag_response": "variant-a",
    },
)
```

Use cases:
- Email subject line A/B tests
- Backend algorithm changes
- Marketing campaign variations
- Pricing page experiments managed outside PostHog

## Holdout Groups

Reserve a percentage of users who never see any experiment variant:

```
Experiment: new-checkout
  Control: 45%
  Test: 45%
  Holdout: 10% (see nothing, baseline measurement)
```

Holdout groups let you measure the cumulative effect of all experiments over time.

## Implementation Patterns

### React Component A/B Test

```tsx
import { useFeatureFlagVariantKey } from 'posthog-js/react';

function CheckoutPage() {
  const variant = useFeatureFlagVariantKey('checkout-experiment');

  switch (variant) {
    case 'single-page':
      return <SinglePageCheckout />;
    case 'multi-step':
      return <MultiStepCheckout />;
    default:
      return <DefaultCheckout />;  // control
  }
}
```

### Python Backend Experiment

```python
import posthog

def get_pricing(user_id: str) -> dict:
    variant = posthog.get_feature_flag(
        key="pricing-experiment",
        distinct_id=user_id,
    )

    if variant == "annual-first":
        return {"default_plan": "annual", "discount": 20}
    elif variant == "monthly-first":
        return {"default_plan": "monthly", "discount": 0}
    else:
        return {"default_plan": "monthly", "discount": 10}  # control
```

### Tracking Custom Goal Events

```typescript
// Make sure to capture the goal event with relevant properties
posthog.capture('purchase_completed', {
  amount: 49.99,
  plan: 'pro',
  payment_method: 'credit_card',
});
```

## Common Pitfalls

1. **Ending experiments too early** — wait for the recommended sample size; early results are unreliable
2. **Not accounting for novelty effects** — run experiments for at least 1-2 weeks to normalize
3. **Testing too many things at once** — each variant should change one thing; compound changes make it impossible to know what worked
4. **Ignoring secondary metrics** — a variant may boost conversion but hurt retention
5. **Peeking at results** — checking daily and stopping when you see significance inflates false positive rates
6. **Not segmenting results** — overall winner may not be the winner for all segments (check by device, plan, geography)
7. **Forgetting to clean up** — after calling an experiment, set the flag to 100% winner and eventually remove the experiment code
