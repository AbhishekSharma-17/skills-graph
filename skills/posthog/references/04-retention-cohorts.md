# PostHog — Retention & Cohorts

> Source: [posthog.com/docs/product-analytics/retention](https://posthog.com/docs/product-analytics/retention) | [posthog.com/docs/data/cohorts](https://posthog.com/docs/data/cohorts)

## Table of Contents

- [Retention Analysis](#retention-analysis)
- [Retention Configuration](#retention-configuration)
- [Retention Types](#retention-types)
- [Reading Retention Tables](#reading-retention-tables)
- [Cohorts Overview](#cohorts-overview)
- [Creating Cohorts](#creating-cohorts)
- [Behavioral Cohorts](#behavioral-cohorts)
- [Lifecycle Cohorts](#lifecycle-cohorts)
- [Using Cohorts as Filters](#using-cohorts-as-filters)
- [Dynamic vs Static Cohorts](#dynamic-vs-static-cohorts)
- [Common Patterns](#common-patterns)

## Retention Analysis

Retention measures how often users come back to perform an action after an initial event. It answers: "Of users who did X on day 0, how many came back to do Y on day 1, day 2, etc.?"

### Key Metrics

- **Day 0** — users who performed the start event (always 100%)
- **Day N retention** — percentage of Day 0 users who came back on Day N
- **Week 1 retention** — percentage who returned in week 1
- **Benchmark** — typical Day 7 retention for SaaS: 15-25%; consumer apps: 10-20%

## Retention Configuration

### Basic Setup

```
Start event:  signup_completed
Return event: $pageview
Period:       Day
Date range:   Last 12 weeks
```

### Parameters

| Parameter | Options | Default |
|-----------|---------|---------|
| **Start event** | Any event or action | Required |
| **Return event** | Any event or action | Same as start |
| **Period** | Hour, Day, Week, Month | Day |
| **Counting** | Users, Groups | Users |

### Same Event Retention

```
Start event:  $pageview
Return event: $pageview
Period:       Week
```

Measures: "Of users who visited this week, how many came back next week?"

### Different Event Retention

```
Start event:  signup_completed
Return event: feature_used
Period:       Day
```

Measures: "Of users who signed up, how many used a feature on subsequent days?"

## Retention Types

### First Time Retention (Default)

Only counts the first time each user performs the start event. Each user appears in exactly one cohort row.

```
Start: First time signup_completed
Return: $pageview

Day 0: 100 users signed up on Jan 1
Day 1: 40 returned (40%)
Day 7: 20 returned (20%)
Day 30: 10 returned (10%)
```

### Recurring Retention

Counts every time a user performs the start event. Users can appear in multiple cohort rows.

```
Start: Every time $pageview
Return: $pageview

Users who visited on both Jan 1 and Jan 3 appear in both rows.
```

## Reading Retention Tables

The retention table is a triangular matrix:

```
Cohort    | Size | Day 0  | Day 1 | Day 2 | Day 3 | Day 7
----------|------|--------|-------|-------|-------|------
Jan 1     | 100  | 100%   | 40%   | 35%   | 30%   | 20%
Jan 2     | 120  | 100%   | 45%   | 38%   | 32%   | 22%
Jan 3     | 90   | 100%   | 38%   | 33%   | 28%   | 18%
```

Reading tips:
- **Rows** = cohorts grouped by when they performed the start event
- **Columns** = days/weeks/months after the start event
- **Color coding** = darker = higher retention
- **Click a cell** to see the actual users in that cell
- **Compare rows** to see if retention is improving over time

## Cohorts Overview

Cohorts are reusable groups of users defined by shared characteristics or behaviors. They serve as filters across all PostHog insights.

### Use Cases

- Filter dashboards to specific user segments
- Compare conversion rates between cohorts
- Target feature flags and experiments to cohorts
- Target surveys to specific user groups
- Create email lists for outreach

## Creating Cohorts

### Property-Based Cohorts

```
Name: Enterprise Users
Match users where:
  person.plan = 'enterprise'
  AND person.signup_date > '2026-01-01'
```

### Event-Based Cohorts

```
Name: Power Users
Match users who:
  performed $pageview at least 10 times
  in the last 7 days
```

### Combining Conditions

```
Name: At-Risk Enterprise
Match users where:
  person.plan = 'enterprise'
  AND performed $pageview less than 2 times
  in the last 30 days
```

Conditions can be combined with AND/OR logic.

## Behavioral Cohorts

Define cohorts based on user behavior patterns:

### Frequency-Based

```
Match users who performed 'feature_used'
  at least 5 times
  in the last 14 days
```

### Sequence-Based

```
Match users who performed 'signup_completed'
  AND did NOT perform 'onboarding_completed'
  in the last 7 days
```

### Recency-Based

```
Match users who performed '$pageview'
  at least once
  in the last 3 days
  (active users)
```

```
Match users who performed '$pageview'
  zero times
  in the last 30 days
  (churned users)
```

## Lifecycle Cohorts

Create cohorts from lifecycle insight results:

```
1. Build a lifecycle insight (Event: $pageview, Interval: Week)
2. Click on the "Dormant" segment
3. Save as cohort: "Churned Users — Last Week"
```

You can create cohorts from any lifecycle segment (New, Returning, Resurrecting, Dormant).

## Using Cohorts as Filters

Cohorts can be used as filters in:

### Trends
```
Event: purchase_completed
Filter: Cohort = "Power Users"
Compare: Cohort = "Casual Users"
```

### Funnels
```
Step 1: pricing_page_viewed → Step 2: purchase_completed
Filter: Cohort = "Enterprise Users"
```

### Feature Flags
```
Flag: new-dashboard-ui
Target: Cohort = "Beta Testers"
Rollout: 100% of cohort
```

### Experiments
```
Experiment: new_checkout_flow
Target: Cohort = "US Users with > 3 purchases"
```

### Surveys
```
Survey: NPS Survey
Display: Cohort = "Users active > 30 days"
```

## Dynamic vs Static Cohorts

### Dynamic Cohorts (Default)
- Membership recalculated on every query
- Users automatically enter/leave as they match/unmatch criteria
- Best for: ongoing analysis, targeting active segments

### Static Cohorts
- Membership fixed at creation time
- Users don't enter/leave the cohort
- Created by uploading a CSV of distinct IDs or saving from an insight
- Best for: specific user lists, one-time campaigns

### Uploading Static Cohorts

```csv
distinct_id
user_123
user_456
user_789
```

Upload via Cohorts → New Cohort → Upload CSV.

## Common Patterns

### Measuring Feature Impact on Retention

```
1. Create cohort A: users who used Feature X in their first week
2. Create cohort B: users who did NOT use Feature X in their first week
3. Build retention insight:
   Start: signup_completed
   Return: $pageview
   Breakdown: Cohort A vs Cohort B
4. Compare Day 7, Day 14, Day 30 retention
```

### Building a Health Score

```
Healthy: performed core_action ≥ 5 times in last 7 days
At-risk: performed core_action 1-4 times in last 7 days
Churning: performed core_action 0 times in last 14 days
```

### Cohort-Based Onboarding Analysis

```
Cohort: "Completed Onboarding" — signed up AND completed all steps
Cohort: "Abandoned Onboarding" — signed up AND did NOT complete

Compare: 30-day retention for each cohort
Result: quantify the value of onboarding completion
```

### Weekly Retention Report

```
Retention Insight:
  Start: $pageview
  Return: $pageview
  Period: Week
  Filter: person.plan IN ['pro', 'enterprise']
  Date: Last 8 weeks

Subscribe to weekly email digest.
```
