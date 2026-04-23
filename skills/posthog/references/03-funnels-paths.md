# PostHog — Funnels & Paths

> Source: [posthog.com/docs/product-analytics/funnels](https://posthog.com/docs/product-analytics/funnels) | [posthog.com/docs/product-analytics/paths](https://posthog.com/docs/product-analytics/paths)

## Table of Contents

- [Funnel Analysis](#funnel-analysis)
- [Creating Funnels](#creating-funnels)
- [Funnel Types](#funnel-types)
- [Conversion Windows](#conversion-windows)
- [Funnel Breakdowns](#funnel-breakdowns)
- [Exclusion Steps](#exclusion-steps)
- [Funnel Trends](#funnel-trends)
- [Correlation Analysis](#correlation-analysis)
- [User Paths](#user-paths)
- [Path Configuration](#path-configuration)
- [Wildcard Groups](#wildcard-groups)
- [Funnels vs Paths](#funnels-vs-paths)
- [Common Patterns](#common-patterns)

## Funnel Analysis

Funnels measure conversion through an ordered sequence of steps. They answer: "What percentage of users who did Step 1 also completed Step 2, Step 3, etc.?"

Key metrics per step:
- **Conversion rate** — percentage of users who completed this step
- **Drop-off rate** — percentage who left at this step
- **Average time to convert** — median time between steps
- **Count** — absolute number of users at each step

## Creating Funnels

### Basic Funnel

```
Step 1: $pageview (URL contains /pricing)
Step 2: signup_started
Step 3: signup_completed
Step 4: purchase_completed

Conversion window: 7 days
Counting: Unique users
```

### Step Configuration

Each funnel step can be:
- **An event** — any captured event (e.g., `button_clicked`)
- **An action** — a saved PostHog action (combines multiple events)
- **A pageview with URL filter** — `$pageview` where `$current_url` contains a path

Add filters to steps:

```
Step 2: signup_started
  Filter: plan_type = 'pro'
  Filter: referrer contains 'google'
```

## Funnel Types

### Ordered Funnel (Default)
Steps must happen in the specified order. Steps in between are allowed:

```
Step 1 → (other events ok) → Step 2 → (other events ok) → Step 3
```

### Strict Funnel
Steps must happen in exact consecutive order — no events between steps:

```
Step 1 → Step 2 → Step 3 (no gaps allowed)
```

### Unordered Funnel
All steps must be completed, but in any order:

```
Any order: Step 1, Step 2, Step 3 all completed within the window
```

## Conversion Windows

The conversion window defines how long a user has to complete all funnel steps:

| Window | Use Case |
|--------|----------|
| **1 hour** | Quick actions (checkout, onboarding) |
| **1 day** | Same-session flows |
| **7 days** | Multi-session conversions |
| **14 days** | B2B signup flows |
| **30+ days** | Enterprise sales funnels |

Users who don't complete all steps within the window count as drop-offs.

## Funnel Breakdowns

Break down each step by a property to find what drives conversion:

```
Funnel: Signup → Purchase
Breakdown: $browser
Result:
  Chrome:  Signup=1000, Purchase=200 (20%)
  Safari:  Signup=800,  Purchase=120 (15%)
  Firefox: Signup=400,  Purchase=40  (10%)
```

Useful breakdowns:
- **$browser** / **$os** — technical issues affecting conversion
- **$referring_domain** — which traffic sources convert best
- **plan_type** — which plans have higher conversion
- **utm_source** — marketing campaign effectiveness
- **cohort** — compare user segments

## Exclusion Steps

Exclude users who performed a specific event between funnel steps:

```
Step 1: checkout_started
Step 2: purchase_completed
Exclude: support_ticket_created (between steps 1 and 2)
```

This filters out users who hit problems and contacted support, giving you clean conversion data for the happy path.

## Funnel Trends

Instead of showing the overall funnel, show how conversion rate changes over time:

```
Funnel: Signup → Purchase
Display: Conversion rate trend
Interval: Week
Date: Last 90 days
```

Shows a line chart of conversion rate per week — useful for tracking the impact of product changes on conversion.

## Correlation Analysis

PostHog automatically identifies factors that correlate with conversion or drop-off:

### Property Correlations
"Users with `plan=enterprise` are 3.2x more likely to convert"

### Event Correlations
"Users who completed `tutorial_watched` before Step 2 are 2.5x more likely to convert"

Correlations are shown automatically on funnel insights. They help identify:
- **Success signals** — events/properties that predict conversion
- **Failure signals** — events/properties that predict drop-off

## User Paths

Paths visualize the actual navigation sequences users take through your product. Unlike funnels (which test a specific hypothesis), paths are exploratory — they show you what users actually do.

### Path Visualization

Paths render as a Sankey diagram showing:
- Nodes (events/pages)
- Flows (transitions between nodes)
- Widths (proportional to user count)
- Drop-offs (users who leave)

### Path Types

| Type | What It Shows |
|------|---------------|
| **Page views** | Navigation between pages (`$current_url`) |
| **Screen views** | Mobile screen transitions (`$screen_name`) |
| **Custom events** | Transitions between any captured events |

## Path Configuration

### Starting Point

```
Start: /homepage
Steps: 5
Date: Last 30 days
```

Shows the 5 most common steps users take after visiting the homepage.

### Ending Point

```
End: purchase_completed
Steps: 5 (before)
```

Shows what users did in the 5 steps before making a purchase.

### Specific Path

```
Start: signup_page_viewed
End: first_project_created
Steps: 10
```

Shows all paths users take between signup and first project creation.

### Filters

```
Start: /dashboard
Person filter: plan = 'enterprise'
Date: Last 7 days
Min users: 10 (hide rare paths)
```

## Wildcard Groups

Group similar URLs or events together using wildcard patterns:

```
Wildcard: /blog/* → "Blog Posts"
Wildcard: /docs/api/* → "API Docs"
```

Without wildcards, `/blog/post-1`, `/blog/post-2`, etc. appear as separate nodes. Wildcards collapse them into a single "Blog Posts" node for cleaner visualization.

### Regex Patterns

```
Pattern: /user/\d+/settings → "User Settings"
Pattern: /project/.*/dashboard → "Project Dashboard"
```

## Funnels vs Paths

| Aspect | Funnels | Paths |
|--------|---------|-------|
| **Question** | "How many complete this flow?" | "What do users actually do?" |
| **Structure** | Predefined steps | Exploratory, no predefined steps |
| **Counting** | Unique users | Transitions between events |
| **Use case** | Test a hypothesis | Discover patterns |
| **Output** | Conversion rates | Sankey diagram |
| **Correlation** | Yes, built-in | No |

## Common Patterns

### E-Commerce Checkout Funnel

```
Step 1: product_viewed
Step 2: add_to_cart
Step 3: checkout_started
Step 4: payment_info_entered
Step 5: purchase_completed

Window: 24 hours
Breakdown: $device_type
```

### SaaS Onboarding Funnel

```
Step 1: signup_completed
Step 2: workspace_created
Step 3: first_invite_sent
Step 4: first_integration_connected
Step 5: first_report_generated

Window: 14 days
Breakdown: signup_source
```

### Discovering Drop-Off Reasons

```
1. Create funnel with suspected steps
2. Check correlation analysis for drop-off signals
3. Click on drop-off users at each step
4. Watch their session recordings
5. Create a cohort from drop-off users for follow-up surveys
```

### Feature Discovery Paths

```
Start: /dashboard (main app entry)
Steps: 8
Event type: Custom events
Filter: new users (first_seen < 7 days ago)
```

Shows how new users discover features in their first week.
