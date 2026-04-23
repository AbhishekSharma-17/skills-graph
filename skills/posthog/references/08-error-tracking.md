# PostHog — Error Tracking

> Source: [posthog.com/docs/error-tracking](https://posthog.com/docs/error-tracking) | posthog-js / posthog-python / posthog-node

## Table of Contents

- [Error Tracking Overview](#error-tracking-overview)
- [Installation](#installation)
- [Autocapture Exceptions](#autocapture-exceptions)
- [Manual Exception Capture](#manual-exception-capture)
- [Source Maps](#source-maps)
- [Issue Grouping](#issue-grouping)
- [Monitoring & Alerts](#monitoring--alerts)
- [Issue Management](#issue-management)
- [Integration with Session Replay](#integration-with-session-replay)
- [Server-Side Error Tracking](#server-side-error-tracking)
- [Common Pitfalls](#common-pitfalls)

## Error Tracking Overview

PostHog Error Tracking captures, groups, and monitors exceptions in your application. It integrates with Session Replay so you can watch the exact user session when an error occurred.

Key features:
- **Autocapture** — automatically capture uncaught exceptions
- **Manual capture** — explicitly capture handled exceptions
- **Source maps** — readable stack traces for minified code
- **Issue grouping** — similar exceptions grouped into issues
- **Alerts** — get notified on new issues or spikes
- **Session Replay link** — click from error to user session

## Installation

### JavaScript — Automatic Setup

```typescript
posthog.init('<api_key>', {
  api_host: 'https://us.i.posthog.com',
  capture_exceptions: true,  // enable autocapture of uncaught errors
});
```

When enabled, PostHog automatically listens for:
- `window.onerror` — uncaught runtime errors
- `unhandledrejection` — unhandled Promise rejections
- `console.error` — console error calls (optional)

### Python

```python
import posthog

posthog.project_api_key = "<api_key>"
posthog.host = "https://us.i.posthog.com"
posthog.enable_exception_autocapture = True
```

### Node.js

```typescript
import { PostHog } from 'posthog-node';

const client = new PostHog('<api_key>', {
  host: 'https://us.i.posthog.com',
});

// Error tracking for Node.js requires manual capture
process.on('uncaughtException', (error) => {
  client.captureException(error, 'server_user_id');
});

process.on('unhandledRejection', (reason) => {
  client.captureException(reason as Error, 'server_user_id');
});
```

## Autocapture Exceptions

When `capture_exceptions: true` is set, PostHog captures `$exception` events automatically:

```json
{
  "event": "$exception",
  "properties": {
    "$exception_type": "TypeError",
    "$exception_message": "Cannot read property 'map' of undefined",
    "$exception_source": "https://yourapp.com/static/main.js",
    "$exception_lineno": 42,
    "$exception_colno": 15,
    "$exception_stack_trace_raw": "TypeError: Cannot read property...",
    "$exception_handled": false
  }
}
```

### What's Captured Automatically

| Error Type | Captured? | Notes |
|------------|-----------|-------|
| Uncaught runtime errors | Yes | `window.onerror` |
| Unhandled promise rejections | Yes | `unhandledrejection` |
| React error boundaries | Manual | Use `captureException` in `componentDidCatch` |
| Network errors (fetch/XHR) | No | Must capture manually |
| Handled try/catch | No | Must capture manually |

## Manual Exception Capture

### JavaScript

```typescript
try {
  await processPayment(order);
} catch (error) {
  posthog.captureException(error, {
    order_id: order.id,
    payment_method: order.paymentMethod,
  });
  showErrorMessage('Payment failed');
}
```

### Python

```python
try:
    result = process_webhook(payload)
except ValidationError as e:
    posthog.capture_exception(
        e,
        distinct_id="webhook_processor",
        properties={
            "webhook_type": payload.get("type"),
            "source": payload.get("source"),
        },
    )
    raise
```

### React Error Boundary

```tsx
import { usePostHog } from 'posthog-js/react';

class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    const posthog = (window as any).posthog;
    posthog?.captureException(error, {
      component_stack: errorInfo.componentStack,
    });
  }

  render() {
    if (this.state.hasError) {
      return <div>Something went wrong. Please refresh.</div>;
    }
    return this.props.children;
  }
}
```

## Source Maps

Upload source maps so PostHog can show original (unminified) stack traces:

### Automatic Upload (Webpack)

```bash
npm install @posthog/sourcemap-webpack-plugin
```

```javascript
// webpack.config.js
const PostHogSourcemapPlugin = require('@posthog/sourcemap-webpack-plugin');

module.exports = {
  plugins: [
    new PostHogSourcemapPlugin({
      apiKey: '<personal_api_key>',
      projectId: '<project_id>',
      host: 'https://us.posthog.com',
    }),
  ],
};
```

### Manual Upload (CLI)

```bash
# Upload source maps after build
curl -X POST 'https://us.posthog.com/api/projects/<project_id>/source_maps/' \
  -H 'Authorization: Bearer <personal_api_key>' \
  -F 'source_map=@dist/main.js.map' \
  -F 'js_url=https://yourapp.com/static/main.js'
```

### Vite / Rollup

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    sourcemap: true,  // generate source maps
  },
});
```

Then upload the generated `.map` files to PostHog.

## Issue Grouping

PostHog automatically groups similar exceptions into **issues** based on:
- Exception type (e.g., `TypeError`)
- Exception message (normalized — dynamic values stripped)
- Stack trace (file + line number patterns)

### Issue States

| State | Description |
|-------|-------------|
| **Active** | Currently occurring, needs attention |
| **Resolved** | Marked as fixed |
| **Suppressed** | Known issue, intentionally ignored |

### Issue Details

Each issue shows:
- Total occurrences and affected users
- First and last seen timestamps
- Stack trace (with source map resolution)
- Affected browser/OS breakdown
- Link to session replays

## Monitoring & Alerts

### Creating Alerts

```
Alert: New Error Spike
Condition: $exception count > 50 in 1 hour
Channel: Slack #engineering-alerts
```

### Alert Types

- **New issue** — alert when a new error type appears
- **Regression** — alert when a resolved issue reoccurs
- **Spike** — alert when error volume exceeds a threshold
- **Custom** — alert on any filtered error condition

## Issue Management

### Workflow

```
1. New exception captured → auto-grouped into issue
2. Issue appears in Error Tracking dashboard
3. Developer investigates (stack trace, session replay)
4. Fix deployed
5. Mark issue as "Resolved"
6. If it reoccurs → automatically moves back to "Active" + alert
```

### Assigning Issues

Assign issues to team members for triage and resolution tracking.

### Merging Issues

If two issues represent the same root cause, merge them to consolidate the view.

## Integration with Session Replay

The killer feature of PostHog error tracking: click any exception to watch the user's session at the exact moment the error occurred.

```
Error: TypeError: Cannot read property 'items' of null
  → Click "View session" 
  → Replay starts 5 seconds before the error
  → See exactly what the user did to trigger it
  → Console tab shows the full error with stack trace
```

This eliminates the "cannot reproduce" problem — you can see the exact state and user actions that led to the error.

## Server-Side Error Tracking

### Python (FastAPI / Django)

```python
# FastAPI middleware
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import posthog
import traceback

app = FastAPI()

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    user_id = getattr(request.state, "user_id", "anonymous")
    posthog.capture_exception(
        exc,
        distinct_id=user_id,
        properties={
            "endpoint": str(request.url),
            "method": request.method,
        },
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
```

### Node.js (Express)

```typescript
import { PostHog } from 'posthog-node';

const client = new PostHog('<api_key>');

// Express error handler middleware
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  client.captureException(err, req.user?.id || 'anonymous', {
    endpoint: req.path,
    method: req.method,
  });
  res.status(500).json({ error: 'Internal server error' });
});
```

## Common Pitfalls

1. **Not uploading source maps** — stack traces are unreadable without them; automate upload in CI
2. **Capturing too much noise** — filter out known third-party errors (e.g., browser extensions)
3. **Missing manual capture in try/catch** — autocapture only catches unhandled errors
4. **Not linking session replay** — the session link is the main value; ensure replay is enabled
5. **Ignoring error spikes** — set up alerts so new errors don't go unnoticed
6. **Server-side without distinct_id** — always pass a user identifier for server errors; use a service name for background jobs
