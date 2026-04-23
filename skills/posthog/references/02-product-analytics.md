# PostHog — Product Analytics

> Source: [posthog.com/docs/product-analytics](https://posthog.com/docs/product-analytics) | PostHog Cloud / Self-Hosted

## Table of Contents

- [Insights Overview](#insights-overview)
- [Trends](#trends)
- [Breakdowns](#breakdowns)
- [Formulas](#formulas)
- [Dashboards](#dashboards)
- [Filters](#filters)
- [Lifecycle](#lifecycle)
- [Stickiness](#stickiness)
- [Web Analytics](#web-analytics)
- [Notebooks](#notebooks)
- [Subscriptions & Alerts](#subscriptions--alerts)
- [Common Patterns](#common-patterns)

## Insights Overview

Insights are the core building block of PostHog analytics. Each insight is a query visualization that can be saved, shared, and added to dashboards.

Insight types:
- **Trends** — event counts, unique users, property values over time
- **Funnels** — conversion between ordered steps
- **Retention** — how often users return
- **Paths** — user navigation flows
- **Stickiness** — how frequently users perform an action
- **Lifecycle** — new, returning, resurrecting, dormant user segments

## Trends

Trends show how events or actions change over time.

### Basic Trend Query

```
Series:   $pageview
Count:    Total count
Interval: Day
Date:     Last 30 days
```

### Aggregation Types

| Aggregation | Description | Example |
|-------------|-------------|---------|
| **Total count** | Number of times event fired | 1,234 pageviews |
| **Unique users** | Distinct users who performed event | 456 unique visitors |
| **Weekly active users** | Users active in rolling 7-day window | WAU metric |
| **Monthly active users** | Users active in rolling 30-day window | MAU metric |
| **Property value — Sum** | Sum of a numeric property | Total revenue |
| **Property value — Avg** | Average of a numeric property | Avg order value |
| **Property value — Min/Max** | Extremes of numeric property | Largest purchase |
| **Unique values** | Count of distinct property values | Unique countries |

### Multi-Series Trends

Compare multiple events in a single chart:

```
Series A: signup_completed (Total count)
Series B: purchase_completed (Total count)
Compare:  Previous period
Interval: Week
```

### Display Options

- **Line chart** — default, best for time series
- **Bar chart** — good for comparing discrete periods
- **Area chart** — emphasize volume
- **Number** — single aggregate value
- **Table** — raw data rows
- **Pie chart** — proportional breakdown
- **World map** — geographic distribution

## Breakdowns

Break down any insight by event or person properties:

```
Event:     purchase_completed
Breakdown: payment_method
Result:    credit_card: 450, paypal: 120, apple_pay: 85
```

### Multiple Breakdowns

You can break down by multiple properties simultaneously:

```
Event:       signup_completed
Breakdown 1: $browser
Breakdown 2: plan_type
Result:      Chrome + Free: 200, Chrome + Pro: 50, Safari + Free: 180...
```

### Breakdown Options

- **Event property** — property on the specific event
- **Person property** — property on the user's profile
- **Group property** — property on the associated group
- **Cohort** — membership in defined cohorts
- **Session property** — session duration, entry/exit URLs

## Formulas

Combine series using mathematical formulas:

```
Series A: purchase_completed (Total count)
Series B: checkout_started (Total count)
Formula:  A / B * 100
Label:    Conversion Rate (%)
```

Supported operators: `+`, `-`, `*`, `/`

Common formula patterns:
- **Conversion rate**: `purchases / pageviews * 100`
- **Revenue per user**: `SUM(amount) / unique_users`
- **Ratio**: `event_A / event_B`

## Dashboards

Dashboards collect multiple insights into a single view.

### Creating Dashboards

1. Navigate to Dashboards → New Dashboard
2. Choose a template or start blank
3. Add existing insights or create new ones
4. Arrange with drag-and-drop grid layout

### Dashboard Features

- **Date range override** — apply a single date range to all insights
- **Filters** — add dashboard-level filters that apply to all insights
- **Auto-refresh** — dashboards refresh on configurable intervals
- **Sharing** — share via link, embed with iframe, or restrict access
- **Templates** — start from pre-built templates (Product, Web, Revenue)
- **Tags** — organize dashboards with tags

### Embedding Dashboards

```html
<!-- Embed a shared dashboard -->
<iframe
  src="https://us.posthog.com/embedded/dashboard/abc123"
  width="100%"
  height="800"
  frameborder="0"
></iframe>
```

## Filters

Filters narrow the data in any insight:

### Event Filters
```
Event:  purchase_completed
Filter: amount > 50 AND currency = 'USD'
```

### Person Filters
```
Event:  any event
Filter: person.plan = 'enterprise' AND person.signup_date > '2026-01-01'
```

### Filter Operators

| Operator | Types | Example |
|----------|-------|---------|
| `=` / `≠` | All | `country = US` |
| `>` / `<` / `≥` / `≤` | Numeric, DateTime | `amount > 100` |
| `contains` / `not contains` | String | `email contains @acme.com` |
| `matches regex` | String | `path matches /api/.*` |
| `is set` / `is not set` | All | `email is set` |
| `in` / `not in` | String, Numeric | `plan in [pro, enterprise]` |

### Test Accounts Filter

Exclude internal users from analytics:

1. Go to Project Settings → Test Accounts
2. Add filters (e.g., `email contains @yourcompany.com`)
3. Enable "Filter out internal and test users" on insights

## Lifecycle

Lifecycle analysis segments users into four categories each period:

| Segment | Definition |
|---------|-----------|
| **New** | Performed event for the first time this period |
| **Returning** | Performed event this period AND the previous period |
| **Resurrecting** | Performed event this period but NOT the previous period (came back) |
| **Dormant** | Performed event the previous period but NOT this period (churned) |

```
Event:    $pageview
Interval: Week
Result:   Week 1: New=100, Returning=500, Resurrecting=50, Dormant=-80
```

Dormant count is shown as negative to emphasize churn.

## Stickiness

Stickiness shows how many days/weeks a user performs an action within a time period:

```
Event:  $pageview
Period: Last 30 days
Result: 1 day=5000, 2 days=2000, 3 days=1200, ..., 30 days=50
```

A "stickier" product shows a flatter distribution — users come back repeatedly.

## Web Analytics

PostHog's privacy-friendly web analytics (no cookies required):

- **Page views** — top pages, entry/exit pages
- **Sessions** — duration, bounce rate, pages per session
- **Sources** — referrers, UTM parameters, channels
- **Geography** — country, region, city
- **Devices** — browser, OS, screen size
- **Core Web Vitals** — LCP, FID, CLS performance metrics

Access via the "Web Analytics" tab — works automatically once PostHog JS is installed.

## Notebooks

Notebooks combine text, insights, session replays, and queries in a single document:

- Write analysis narratives alongside charts
- Embed any insight inline
- Share with team members
- Export findings

## Subscriptions & Alerts

### Subscriptions
Get periodic insight snapshots delivered:
- Email — daily, weekly, or monthly
- Slack — post to a channel on schedule

### Alerts
Get notified when metrics change:
- **Threshold alerts** — notify when a value exceeds or drops below a threshold
- **Anomaly detection** — automatic alerting on unusual metric changes

## Common Patterns

### Product KPI Dashboard

```
Insight 1: DAU / MAU ratio (Stickiness)
Insight 2: Weekly signup trend (Trend)
Insight 3: Onboarding funnel (Funnel)
Insight 4: Feature adoption breakdown (Trend + Breakdown)
Insight 5: Revenue trend (Trend, SUM property)
Insight 6: User lifecycle (Lifecycle)
```

### Comparing Releases

```
Event:   any_event
Filter:  app_version = '2.1.0'
Compare: Filter app_version = '2.0.0'
```

### Measuring Feature Adoption

```
Event:    feature_used
Breakdown: feature_name
Period:   Last 90 days
Compare:  Previous 90 days
```
