# PostHog — Surveys

> Source: [posthog.com/docs/surveys](https://posthog.com/docs/surveys) | posthog-js

## Table of Contents

- [Surveys Overview](#surveys-overview)
- [Survey Types](#survey-types)
- [Creating Surveys](#creating-surveys)
- [Question Types](#question-types)
- [Display Conditions](#display-conditions)
- [Targeting](#targeting)
- [Custom Survey UI](#custom-survey-ui)
- [Survey Results & Analysis](#survey-results--analysis)
- [NPS Surveys](#nps-surveys)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## Surveys Overview

PostHog Surveys let you collect qualitative feedback directly in your app. Surveys are targeted using the same user properties, cohorts, and feature flags used for analytics and experiments.

Key features:
- **Popover surveys** — pre-built UI, no code needed
- **API surveys** — bring your own UI, PostHog handles logic
- **Feedback button** — persistent feedback tab
- **Targeting** — show to specific users, pages, cohorts
- **Branching** — conditional question flows based on answers
- **Auto-link to users** — responses tied to identified users

## Survey Types

| Type | Description | Best For |
|------|-------------|----------|
| **Popover** | Bottom-corner popup with PostHog UI | Quick feedback, NPS, CSAT |
| **API** | Your custom UI, PostHog targeting + storage | Brand-consistent surveys |
| **Feedback button** | Persistent tab on screen edge | Always-available feedback |

## Creating Surveys

### Via PostHog UI

1. Navigate to Surveys → New Survey
2. Choose a template or start from scratch
3. Add questions
4. Set display conditions and targeting
5. Preview and launch

### Templates

- **NPS** — Net Promoter Score (0-10 rating + open text)
- **CSAT** — Customer Satisfaction (emoji scale)
- **CES** — Customer Effort Score
- **PMF** — Product-Market Fit ("How would you feel if you could no longer use...")
- **Custom** — build your own from scratch

## Question Types

| Type | Input | Output |
|------|-------|--------|
| **Open text** | Free-form text area | String response |
| **Single choice** | Radio buttons | Selected option string |
| **Multiple choice** | Checkboxes | Array of selected options |
| **Rating** | Numeric scale (1-5 or 1-10) | Number |
| **NPS** | 0-10 scale with labels | Number (0-10) |
| **Emoji rating** | Emoji faces (1-5) | Number (1-5) |
| **Link/CTA** | Button with URL | Click tracking |

### Multi-Question Surveys

Add multiple questions in sequence:

```
Question 1: "How satisfied are you with our product?" (Rating 1-5)
Question 2: "What could we improve?" (Open text)
Question 3: "Would you recommend us?" (NPS 0-10)
```

### Branching Logic

Route users to different questions based on answers:

```
Q1: "How do you use our product?" (Single choice)
  → If "Personal" → Q2a: "What personal projects?"
  → If "Work" → Q2b: "What team size?"
  → If "Both" → Q2c: "Which is primary?"
```

### Confirmation Message

Show a thank-you message after submission:

```
Confirmation: "Thanks for your feedback! 🎉"
Auto-dismiss: 3 seconds
```

## Display Conditions

Control when and where surveys appear:

### URL Targeting

```
Show on: /pricing (exact match)
Show on: /docs/* (wildcard)
Show on: URLs matching regex: /product/\d+
```

### Wait Period

```
Wait: 5 seconds after page load before showing
Minimum interval: Don't show again for 30 days
```

### Frequency

| Option | Behavior |
|--------|----------|
| **Once** | Show once, never again after dismissal or completion |
| **Until dismissed** | Show on every qualifying page until user dismisses |
| **Every time** | Show every time conditions are met |
| **Recurring** | Show again after N days |

### Events Trigger

```
Show survey when: checkout_completed event fires
Show survey when: error_page_viewed event fires
```

## Targeting

### User Properties

```
Show to users where:
  plan = 'enterprise'
  AND signup_date > '2026-01-01'
```

### Cohorts

```
Show to: Cohort "Power Users"
Exclude: Cohort "Already Surveyed"
```

### Feature Flags

```
Show when feature flag 'new-dashboard' is enabled
```

This links surveys to specific feature rollouts — get feedback only from users who see the new feature.

### Percentage Sampling

```
Show to: 10% of eligible users
```

## Custom Survey UI

Use the API mode to build your own survey UI while PostHog handles targeting and response storage:

### Getting Active Surveys

```typescript
posthog.getActiveMatchingSurveys((surveys) => {
  // surveys = [{ id, name, questions, appearance, ... }]
  surveys.forEach((survey) => {
    renderCustomSurvey(survey);
  });
});
```

### Rendering and Submitting

```typescript
// Check if a specific survey should show
posthog.getSurveys((surveys) => {
  const nps = surveys.find((s) => s.name === 'NPS Survey');
  if (nps) {
    showNPSModal(nps);
  }
});

// Submit a response
posthog.capture('survey sent', {
  $survey_id: survey.id,
  $survey_response: userAnswer,          // for single-question surveys
  $survey_response_0: firstAnswer,       // for multi-question (Q1)
  $survey_response_1: secondAnswer,      // Q2
  $survey_response_2: thirdAnswer,       // Q3
});

// Mark survey as dismissed (user closed without answering)
posthog.capture('survey dismissed', {
  $survey_id: survey.id,
});

// Mark survey as shown (for display frequency tracking)
posthog.capture('survey shown', {
  $survey_id: survey.id,
});
```

### React Custom Survey

```tsx
import { usePostHog } from 'posthog-js/react';
import { useEffect, useState } from 'react';

function CustomSurvey() {
  const posthog = usePostHog();
  const [survey, setSurvey] = useState(null);
  const [response, setResponse] = useState('');

  useEffect(() => {
    posthog.getActiveMatchingSurveys((surveys) => {
      const target = surveys.find((s) => s.name === 'Feature Feedback');
      if (target) {
        setSurvey(target);
        posthog.capture('survey shown', { $survey_id: target.id });
      }
    });
  }, [posthog]);

  const handleSubmit = () => {
    posthog.capture('survey sent', {
      $survey_id: survey.id,
      $survey_response: response,
    });
    setSurvey(null);
  };

  if (!survey) return null;

  return (
    <div className="survey-modal">
      <h3>{survey.questions[0].question}</h3>
      <textarea value={response} onChange={(e) => setResponse(e.target.value)} />
      <button onClick={handleSubmit}>Submit</button>
    </div>
  );
}
```

## Survey Results & Analysis

### Viewing Results

Navigate to Surveys → click a survey → Results tab:
- **Response rate** — submissions / impressions
- **NPS score** — calculated automatically for NPS surveys
- **Response breakdown** — distribution of answers for each question
- **Individual responses** — browse each response with user details

### Analyzing in Insights

Survey responses are events — analyze them like any other event:

```
Event: survey sent
Filter: $survey_id = 'survey_abc'
Breakdown: $survey_response
```

### Connecting to Session Replay

Click a survey response → view the user's session recording to understand the context behind their feedback.

## NPS Surveys

Net Promoter Score surveys use a 0-10 scale:

| Score | Category | Label |
|-------|----------|-------|
| 0-6 | Detractors | Unhappy, may churn |
| 7-8 | Passives | Satisfied but not enthusiastic |
| 9-10 | Promoters | Loyal, likely to recommend |

**NPS = % Promoters - % Detractors** (range: -100 to +100)

### NPS Survey Setup

```
Question 1: "How likely are you to recommend us?" (NPS 0-10)
Question 2: "What's the main reason for your score?" (Open text)
Targeting: Users with > 30 days since signup
Frequency: Every 90 days
```

## Common Patterns

### Post-Onboarding Survey

```
Trigger: onboarding_completed event
Wait: 2 minutes after trigger
Questions:
  1. "How easy was it to set up?" (Rating 1-5)
  2. "What was confusing, if anything?" (Open text)
Target: New users (signup < 7 days ago)
```

### Feature Feedback

```
Target: Feature flag 'new-editor' is enabled
URL: /editor/*
Questions:
  1. "How do you like the new editor?" (Emoji 1-5)
  2. "Any feedback?" (Open text)
```

### Churn Prevention

```
Target: Cohort "At-Risk Users" (inactive 14+ days)
Trigger: First pageview after inactivity
Questions:
  1. "What brought you back today?" (Single choice)
  2. "What almost made you leave?" (Open text)
```

## Common Pitfalls

1. **Survey fatigue** — don't show surveys too frequently; use minimum intervals
2. **Bad targeting** — showing surveys to the wrong audience reduces response quality
3. **Too many questions** — keep surveys short (1-3 questions); completion drops with length
4. **Not analyzing responses** — surveys without follow-up action waste user goodwill
5. **Missing `survey shown` event** — custom implementations must fire this event for frequency controls to work
6. **Not linking to feature flags** — always target surveys to users who actually experienced the feature
