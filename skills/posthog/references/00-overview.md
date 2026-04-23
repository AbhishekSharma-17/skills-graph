# PostHog — Overview & Setup

> Source: [posthog.com/docs](https://posthog.com/docs) | Python SDK 7.x / posthog-js 1.x

## Table of Contents

- [What Is PostHog](#what-is-posthog)
- [Platform Products](#platform-products)
- [Getting Started](#getting-started)
- [JavaScript Web Setup](#javascript-web-setup)
- [React Setup](#react-setup)
- [Next.js Setup](#nextjs-setup)
- [Python Setup](#python-setup)
- [Node.js Setup](#nodejs-setup)
- [Autocapture](#autocapture)
- [Configuration Options](#configuration-options)
- [Self-Hosted vs Cloud](#self-hosted-vs-cloud)
- [Pricing Overview](#pricing-overview)
- [Common Pitfalls](#common-pitfalls)

## What Is PostHog

PostHog is an open-source, all-in-one product analytics platform that replaces multiple tools (Mixpanel, LaunchDarkly, Hotjar, Sentry, Typeform) with a single platform. Built on ClickHouse for fast analytics at scale.

Key characteristics:
- **All-in-one** — analytics, feature flags, experiments, replay, error tracking, surveys, CDP
- **Open source** — MIT licensed, self-hostable
- **Event-driven** — everything is an event with properties
- **SQL access** — HogQL provides direct ClickHouse SQL queries
- **Privacy-first** — EU hosting, data masking, cookieless tracking options
- **32K+ GitHub stars** — large, active community

## Platform Products

| Product | Purpose | Key Feature |
|---------|---------|-------------|
| **Product Analytics** | Track events, build insights, dashboards | Trends, funnels, paths, retention |
| **Web Analytics** | Privacy-friendly website metrics | Cookieless, GDPR-compliant |
| **Session Replay** | Watch user sessions | Web + mobile, console logs, network |
| **Feature Flags** | Control feature rollouts | Targeting rules, % rollout, payloads |
| **Experiments** | A/B and multivariate tests | Statistical significance, goal metrics |
| **Error Tracking** | Monitor exceptions | Autocapture, source maps, issue grouping |
| **Surveys** | In-app user feedback | Popover, API, targeting, branching |
| **Data Pipelines** | Move data in/out | Sources, destinations, transformations |
| **Data Warehouse** | Query external sources | HogQL SQL, joins with PostHog data |
| **AI Assistant** | Natural language queries | Ask questions about your data |

## Getting Started

### Prerequisites

- PostHog Cloud account (free tier: 1M events/month) or self-hosted instance
- Your project's API key (found in Project Settings)
- One of the supported SDKs installed

### Project API Key

Every PostHog project has two keys:
- **Project API Key** (public) — used in client-side SDKs, safe to expose in frontend code
- **Personal API Key** (private) — used for server-side operations, never expose in client code

## JavaScript Web Setup

The simplest way to add PostHog to any website:

```html
<!-- HTML snippet — paste in <head> -->
<script>
  !function(t,e){var o,n,p,r;e.__SV||(window.posthog=e,e._i=[],e.init=function(i,s,a){function g(t,e){var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}(p=t.createElement("script")).type="text/javascript",p.crossOrigin="anonymous",p.async=!0,p.src=s.api_host.replace(".i.posthog.com","-assets.i.posthog.com")+"/static/array.js",(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r);var u=e;for(void 0!==a?u=e[a]=[]:a="posthog",u.people=u.people||[],u.toString=function(t){var e="posthog";return"posthog"!==a&&(e+="."+a),t||(e+=" (stub)"),e},u.people.toString=function(){return u.toString(1)+".people (stub)"},o="init capture register register_once register_for_session unregister unregister_for_session getFeatureFlag getFeatureFlagPayload isFeatureEnabled reloadFeatureFlags updateEarlyAccessFeatureEnrollment getEarlyAccessFeatures on onFeatureFlags onSessionId getSurveys getActiveMatchingSurveys renderSurvey canRenderSurvey getNextSurveyStep identify setPersonProperties group resetGroups setPersonPropertiesForFlags resetPersonPropertiesForFlags setGroupPropertiesForFlags resetGroupPropertiesForFlags reset get_distinct_id getGroups get_session_id get_session_replay_url alias set_config startSessionRecording stopSessionRecording sessionRecordingStarted captureException loadToolbar get_property getSessionProperty createPersonProfile opt_in_capturing opt_out_capturing has_opted_in_capturing has_opted_out_capturing clear_opt_in_out_capturing debug".split(" "),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])},e.__SV=1)}(document,window.posthog||[]);
  posthog.init('<ph_project_api_key>', {
    api_host: 'https://us.i.posthog.com',  // or https://eu.i.posthog.com
    person_profiles: 'identified_only',
  });
</script>
```

Or install via npm:

```bash
npm install posthog-js
```

```typescript
import posthog from 'posthog-js';

posthog.init('<ph_project_api_key>', {
  api_host: 'https://us.i.posthog.com',
  person_profiles: 'identified_only',
});
```

## React Setup

```bash
npm install posthog-js @posthog/react
```

```tsx
// app/providers.tsx
'use client';
import posthog from 'posthog-js';
import { PostHogProvider as PHProvider } from 'posthog-js/react';
import { useEffect } from 'react';

export function PostHogProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
      api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST!,
      person_profiles: 'identified_only',
      capture_pageview: false,  // we capture manually in Next.js
    });
  }, []);

  return <PHProvider client={posthog}>{children}</PHProvider>;
}
```

```tsx
// Using the hook in components
import { usePostHog } from 'posthog-js/react';

function MyComponent() {
  const posthog = usePostHog();

  const handleClick = () => {
    posthog.capture('button_clicked', { button_name: 'signup' });
  };

  return <button onClick={handleClick}>Sign Up</button>;
}
```

## Next.js Setup

```tsx
// app/layout.tsx
import { PostHogProvider } from './providers';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <PostHogProvider>{children}</PostHogProvider>
      </body>
    </html>
  );
}
```

```tsx
// app/PostHogPageView.tsx — capture pageviews in Next.js App Router
'use client';
import { usePathname, useSearchParams } from 'next/navigation';
import { usePostHog } from 'posthog-js/react';
import { useEffect } from 'react';

export function PostHogPageView() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const posthog = usePostHog();

  useEffect(() => {
    if (pathname && posthog) {
      let url = window.origin + pathname;
      if (searchParams.toString()) {
        url = url + '?' + searchParams.toString();
      }
      posthog.capture('$pageview', { $current_url: url });
    }
  }, [pathname, searchParams, posthog]);

  return null;
}
```

## Python Setup

```bash
pip install posthog
```

```python
import posthog

# Initialize — call once at app startup
posthog.project_api_key = "<ph_project_api_key>"
posthog.host = "https://us.i.posthog.com"  # or eu.i.posthog.com

# Capture an event
posthog.capture(
    distinct_id="user_123",
    event="purchase_completed",
    properties={"amount": 49.99, "currency": "USD"},
)

# Identify a user
posthog.identify(
    distinct_id="user_123",
    properties={"email": "user@example.com", "name": "Jane Doe"},
)

# Shutdown — flush pending events before exit
posthog.shutdown()
```

### Django Integration

```python
# settings.py
POSTHOG_API_KEY = "<ph_project_api_key>"
POSTHOG_HOST = "https://us.i.posthog.com"

# middleware or signal
import posthog
posthog.project_api_key = POSTHOG_API_KEY
posthog.host = POSTHOG_HOST
```

## Node.js Setup

```bash
npm install posthog-node
```

```typescript
import { PostHog } from 'posthog-node';

const client = new PostHog('<ph_project_api_key>', {
  host: 'https://us.i.posthog.com',
});

// Capture event
client.capture({
  distinctId: 'user_123',
  event: 'purchase_completed',
  properties: { amount: 49.99, currency: 'USD' },
});

// Shutdown — must call before process exits
await client.shutdown();
```

## Autocapture

PostHog's JavaScript SDK can automatically capture:
- **Pageviews** — `$pageview` on every page load
- **Pageleaves** — `$pageleave` when user navigates away
- **Clicks** — `$autocapture` on clickable elements (`a`, `button`, `input`, `select`, `textarea`)
- **Form submissions** — `$autocapture` when forms are submitted
- **Rage clicks** — `$rageclick` when user clicks rapidly on same area

Disable selectively:

```typescript
posthog.init('<key>', {
  autocapture: {
    dom_event_allowlist: ['click'],  // only capture clicks
    url_allowlist: ['posthog.com./docs/.*'],  // only on matching URLs
    element_allowlist: ['a', 'button'],  // only these elements
    css_selector_allowlist: ['.track-this'],  // only matching selectors
  },
});
```

## Configuration Options

Key initialization options for `posthog-js`:

```typescript
posthog.init('<key>', {
  api_host: 'https://us.i.posthog.com',
  person_profiles: 'identified_only',  // 'always' | 'identified_only'
  autocapture: true,
  capture_pageview: true,
  capture_pageleave: true,
  capture_performance: true,
  disable_session_recording: false,
  enable_recording_console_log: true,
  session_recording: {
    maskAllInputs: true,
    maskTextContent: false,
  },
  loaded: (posthog) => {
    if (process.env.NODE_ENV === 'development') posthog.debug();
  },
  bootstrap: {
    featureFlags: { 'my-flag': true },  // immediate flag values
  },
});
```

## Self-Hosted vs Cloud

| Aspect | Cloud | Self-Hosted |
|--------|-------|-------------|
| **Hosting** | PostHog manages everything | You manage infrastructure |
| **Data** | Stored on PostHog servers (US/EU) | Your servers, full control |
| **Updates** | Automatic | Manual upgrades |
| **Scale** | Unlimited | Depends on your infra |
| **Cost** | Usage-based pricing | Free (infra costs apply) |
| **Support** | Included | Community |

## Pricing Overview

PostHog Cloud free tier (per month):
- **Product analytics:** 1M events free
- **Session replay:** 5K recordings free
- **Feature flags:** 1M API requests free
- **Surveys:** 250 responses free
- **Data pipelines:** 5M events free

## Common Pitfalls

1. **Not calling `shutdown()`** — server-side SDKs batch events; without shutdown, the last batch is lost
2. **Using Personal API Key client-side** — never expose the private key in frontend code
3. **Not setting `person_profiles: 'identified_only'`** — creates anonymous profiles by default, increasing costs
4. **Missing pageview capture in SPAs** — React/Next.js apps need manual `$pageview` capture on route changes
5. **Blocking `us.i.posthog.com`** — ad blockers may block PostHog; consider a reverse proxy
6. **Not awaiting `shutdown()`** — in serverless (Lambda), the process may exit before events flush
