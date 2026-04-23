# PostHog — SDKs & API Reference

> Source: [posthog.com/docs/libraries](https://posthog.com/docs/libraries) | [posthog.com/docs/api](https://posthog.com/docs/api)

## Table of Contents

- [SDK Overview](#sdk-overview)
- [JavaScript Web SDK](#javascript-web-sdk)
- [React SDK](#react-sdk)
- [Python SDK](#python-sdk)
- [Node.js SDK](#nodejs-sdk)
- [REST API](#rest-api)
- [API Authentication](#api-authentication)
- [API Endpoints](#api-endpoints)
- [Rate Limits](#rate-limits)
- [Reverse Proxy Setup](#reverse-proxy-setup)
- [Common Pitfalls](#common-pitfalls)

## SDK Overview

| SDK | Environment | Install | Key Features |
|-----|-------------|---------|-------------|
| **posthog-js** | Browser | `npm install posthog-js` | Autocapture, session replay, feature flags, surveys |
| **@posthog/react** | React | `npm install posthog-js @posthog/react` | Provider, hooks for flags/analytics |
| **posthog-node** | Node.js server | `npm install posthog-node` | Server-side capture, local flag eval |
| **posthog (Python)** | Python server | `pip install posthog` | Server-side capture, local flag eval |
| **posthog-ios** | iOS | Swift Package Manager / CocoaPods | Mobile analytics, session replay |
| **posthog-android** | Android | Gradle | Mobile analytics, session replay |
| **posthog-react-native** | React Native | `npm install posthog-react-native` | Cross-platform mobile |
| **posthog-flutter** | Flutter | pub.dev | Cross-platform mobile |
| **posthog-go** | Go server | `go get github.com/posthog/posthog-go` | Lightweight server SDK |
| **posthog-ruby** | Ruby server | `gem install posthog-ruby` | Rails integration |

## JavaScript Web SDK

### Complete API

```typescript
import posthog from 'posthog-js';

// === Initialization ===
posthog.init('<api_key>', { api_host: 'https://us.i.posthog.com' });

// === Event Capture ===
posthog.capture('event_name', { key: 'value' });

// === User Identification ===
posthog.identify('user_id', { email: 'user@example.com' });  // $set
posthog.identify('user_id', {}, { first_seen: '2026-01-01' });  // $set_once
posthog.setPersonProperties({ plan: 'pro' });
posthog.setPersonPropertiesForFlags({ plan: 'pro' });  // for flag targeting
posthog.reset();  // clear identified user (e.g., on logout)

// === Groups ===
posthog.group('company', 'company_123', { name: 'Acme' });
posthog.resetGroups();

// === Feature Flags ===
posthog.isFeatureEnabled('flag-key');               // boolean
posthog.getFeatureFlag('flag-key');                  // string variant or boolean
posthog.getFeatureFlagPayload('flag-key');           // JSON payload
posthog.reloadFeatureFlags();                        // force refresh
posthog.onFeatureFlags((flags) => { /* ... */ });    // callback when loaded
posthog.featureFlags.override({ 'flag': true });     // dev override

// === Super Properties ===
posthog.register({ app_version: '2.0' });            // persist in all events
posthog.register_once({ first_utm: 'google' });      // set once
posthog.register_for_session({ view: 'pricing' });   // session only
posthog.unregister('app_version');                    // remove

// === Session Recording ===
posthog.startSessionRecording();
posthog.stopSessionRecording();
posthog.sessionRecordingStarted();  // boolean
posthog.get_session_replay_url();   // link to current recording

// === Surveys ===
posthog.getActiveMatchingSurveys((surveys) => { /* ... */ });
posthog.getSurveys((surveys) => { /* ... */ });
posthog.renderSurvey('survey_id', '#container');  // render popover

// === Error Tracking ===
posthog.captureException(error, { context: 'checkout' });

// === Utility ===
posthog.get_distinct_id();        // current distinct_id
posthog.get_session_id();         // current session ID
posthog.get_property('$browser'); // get a stored property
posthog.alias('new_id');          // merge distinct_ids
posthog.debug();                  // enable debug logging
posthog.opt_out_capturing();      // stop all tracking
posthog.opt_in_capturing();       // resume tracking
posthog.has_opted_out_capturing(); // check opt-out status
```

## React SDK

### Provider Setup

```tsx
import posthog from 'posthog-js';
import { PostHogProvider } from 'posthog-js/react';

// Initialize outside React
posthog.init('<api_key>', {
  api_host: 'https://us.i.posthog.com',
  person_profiles: 'identified_only',
});

function App() {
  return (
    <PostHogProvider client={posthog}>
      <Router />
    </PostHogProvider>
  );
}
```

### Hooks

```tsx
import {
  usePostHog,
  useFeatureFlagEnabled,
  useFeatureFlagVariantKey,
  useFeatureFlagPayload,
  useActiveFeatureFlags,
} from 'posthog-js/react';

function Component() {
  // Core PostHog instance
  const posthog = usePostHog();

  // Feature flags
  const isNewUI = useFeatureFlagEnabled('new-ui');
  const variant = useFeatureFlagVariantKey('experiment-1');
  const payload = useFeatureFlagPayload('experiment-1');
  const allFlags = useActiveFeatureFlags();

  posthog.capture('component_viewed');

  if (isNewUI) return <NewUI config={payload} />;
  return <OldUI />;
}
```

## Python SDK

### Complete API

```python
import posthog

# === Configuration ===
posthog.project_api_key = "<api_key>"
posthog.host = "https://us.i.posthog.com"
posthog.debug = True  # enable logging
posthog.on_error = lambda e, items: print(f"Error: {e}")

# === Event Capture ===
posthog.capture(
    distinct_id="user_123",
    event="purchase_completed",
    properties={"amount": 49.99},
    timestamp=datetime(2026, 4, 24),  # optional
    groups={"company": "company_123"},  # optional
)

# === User Identification ===
posthog.identify(
    distinct_id="user_123",
    properties={"email": "user@example.com"},         # $set
    properties_set_once={"first_seen": "2026-01-01"},  # $set_once
)

# === Groups ===
posthog.group_identify(
    group_type="company",
    group_key="company_123",
    properties={"name": "Acme Corp", "plan": "enterprise"},
)

# === Feature Flags ===
posthog.feature_enabled("flag-key", "user_123")
posthog.get_feature_flag("flag-key", "user_123")
posthog.get_feature_flag_payload("flag-key", "user_123")
posthog.get_all_flags("user_123")

# With properties for local evaluation
posthog.feature_enabled(
    "flag-key", "user_123",
    person_properties={"plan": "enterprise"},
    groups={"company": "company_123"},
    group_properties={"company": {"plan": "enterprise"}},
)

# === Error Tracking ===
try:
    risky_operation()
except Exception as e:
    posthog.capture_exception(e, distinct_id="user_123")

# === Alias ===
posthog.alias(previous_id="anon_id", distinct_id="user_123")

# === Lifecycle ===
posthog.flush()     # send all queued events immediately
posthog.shutdown()  # flush and close (call before process exit)
```

### Django Integration

```python
# settings.py
POSTHOG_API_KEY = "<api_key>"
POSTHOG_HOST = "https://us.i.posthog.com"

# In views or middleware
import posthog

def my_view(request):
    posthog.capture(
        distinct_id=str(request.user.id),
        event="page_viewed",
        properties={"path": request.path},
    )
```

### FastAPI Integration

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
import posthog

@asynccontextmanager
async def lifespan(app: FastAPI):
    posthog.project_api_key = "<api_key>"
    posthog.host = "https://us.i.posthog.com"
    yield
    posthog.shutdown()

app = FastAPI(lifespan=lifespan)

@app.post("/purchase")
async def create_purchase(user_id: str, amount: float):
    posthog.capture(user_id, "purchase_completed", {"amount": amount})
    return {"status": "ok"}
```

## Node.js SDK

### Complete API

```typescript
import { PostHog } from 'posthog-node';

// === Initialization ===
const client = new PostHog('<api_key>', {
  host: 'https://us.i.posthog.com',
  flushAt: 20,           // batch size (default: 20)
  flushInterval: 10000,  // flush interval ms (default: 10000)
  personalApiKey: '<key>',  // for local flag evaluation
});

// === Event Capture ===
client.capture({
  distinctId: 'user_123',
  event: 'purchase_completed',
  properties: { amount: 49.99 },
  groups: { company: 'company_123' },
  timestamp: new Date(),
});

// === User Identification ===
client.identify({
  distinctId: 'user_123',
  properties: { email: 'user@example.com', plan: 'pro' },
});

// === Groups ===
client.groupIdentify({
  groupType: 'company',
  groupKey: 'company_123',
  properties: { name: 'Acme Corp' },
});

// === Feature Flags (async) ===
const isEnabled = await client.isFeatureEnabled('flag-key', 'user_123');
const variant = await client.getFeatureFlag('flag-key', 'user_123');
const payload = await client.getFeatureFlagPayload('flag-key', 'user_123');
const allFlags = await client.getAllFlags('user_123');

// === Error Tracking ===
client.captureException(error, 'user_123', { endpoint: '/api/data' });

// === Lifecycle ===
await client.flush();     // send all queued events
await client.shutdown();  // flush and close
```

### Express Middleware

```typescript
import { PostHog } from 'posthog-node';

const posthog = new PostHog('<api_key>');

app.use((req, res, next) => {
  const userId = req.user?.id || req.sessionID;

  // Track page view
  posthog.capture({
    distinctId: userId,
    event: '$pageview',
    properties: {
      $current_url: `${req.protocol}://${req.get('host')}${req.originalUrl}`,
    },
  });

  next();
});

// Shutdown on process exit
process.on('SIGTERM', async () => {
  await posthog.shutdown();
  process.exit(0);
});
```

## REST API

### Base URLs

| Region | URL |
|--------|-----|
| US Cloud | `https://us.posthog.com/api/` |
| EU Cloud | `https://eu.posthog.com/api/` |

### Capture Endpoint (Public)

```bash
# Single event — uses Project API Key (public)
curl -X POST 'https://us.i.posthog.com/capture/' \
  -H 'Content-Type: application/json' \
  -d '{
    "api_key": "<project_api_key>",
    "event": "custom_event",
    "distinct_id": "user_123",
    "properties": { "key": "value" }
  }'

# Batch events
curl -X POST 'https://us.i.posthog.com/batch/' \
  -H 'Content-Type: application/json' \
  -d '{
    "api_key": "<project_api_key>",
    "batch": [
      { "event": "evt_1", "distinct_id": "u1", "properties": {} },
      { "event": "evt_2", "distinct_id": "u2", "properties": {} }
    ]
  }'
```

### Feature Flags Endpoint (Public)

```bash
# Evaluate flags for a user — uses Project API Key (public)
curl -X POST 'https://us.i.posthog.com/flags/' \
  -H 'Content-Type: application/json' \
  -d '{
    "api_key": "<project_api_key>",
    "distinct_id": "user_123"
  }'
```

## API Authentication

| Key Type | Usage | Prefix |
|----------|-------|--------|
| **Project API Key** | Client-side capture, flag evaluation | `phc_` |
| **Personal API Key** | Server-side CRUD operations | `phx_` |

```bash
# Authenticated API calls use Personal API Key in header
curl -H 'Authorization: Bearer phx_...' \
  'https://us.posthog.com/api/projects/<project_id>/events/'
```

## API Endpoints

### Key Endpoints

| Resource | List | Create | Detail |
|----------|------|--------|--------|
| Events | `GET /api/projects/:id/events/` | via capture endpoint | `GET .../events/:event_id/` |
| Persons | `GET /api/projects/:id/persons/` | via identify | `GET/DELETE .../persons/:id/` |
| Feature Flags | `GET /api/projects/:id/feature_flags/` | `POST` | `PATCH/DELETE .../feature_flags/:id/` |
| Experiments | `GET /api/projects/:id/experiments/` | `POST` | `GET .../experiments/:id/results/` |
| Cohorts | `GET /api/projects/:id/cohorts/` | `POST` | `PATCH/DELETE .../cohorts/:id/` |

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| Event capture (`/capture/`, `/batch/`) | No hard limit (fair use) |
| Feature flag evaluation (`/flags/`) | No hard limit (fair use) |
| API endpoints (`/api/...`) | 480 requests / minute per user |

For high-volume flag evaluation, use local evaluation to avoid API calls entirely.

## Reverse Proxy Setup

Prevent ad blockers from blocking PostHog by routing through your own domain:

### Nginx

```nginx
location /ingest/ {
    proxy_pass https://us.i.posthog.com/;
    proxy_set_header Host us.i.posthog.com;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

### Next.js Rewrites

```javascript
// next.config.js
module.exports = {
  async rewrites() {
    return [
      {
        source: '/ingest/static/:path*',
        destination: 'https://us-assets.i.posthog.com/static/:path*',
      },
      {
        source: '/ingest/:path*',
        destination: 'https://us.i.posthog.com/:path*',
      },
    ];
  },
};
```

Then point PostHog to your proxy:

```typescript
posthog.init('<key>', {
  api_host: '/ingest',
  ui_host: 'https://us.posthog.com',  // keep UI links working
});
```

## Common Pitfalls

1. **Not calling `shutdown()` in server SDKs** — last batch of events gets lost when process exits
2. **Using Personal API Key client-side** — never expose `phx_` keys in frontend code
3. **Not setting up a reverse proxy** — ad blockers block `posthog.com`; use a first-party proxy
4. **Mixing up project vs personal API keys** — capture uses project key; CRUD operations use personal key
5. **Not handling async flag evaluation** — Node.js `isFeatureEnabled` returns a Promise; always await
6. **Missing `person_profiles: 'identified_only'`** — creates unnecessary anonymous profiles and costs
