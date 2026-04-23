# PostHog — Session Replay

> Source: [posthog.com/docs/session-replay](https://posthog.com/docs/session-replay) | posthog-js

## Table of Contents

- [Session Replay Overview](#session-replay-overview)
- [Installation & Setup](#installation--setup)
- [Recording Configuration](#recording-configuration)
- [Privacy Controls](#privacy-controls)
- [Controlling Which Sessions to Record](#controlling-which-sessions-to-record)
- [Console Log Capture](#console-log-capture)
- [Network Request Capture](#network-request-capture)
- [Mobile Session Replay](#mobile-session-replay)
- [Watching Replays](#watching-replays)
- [Playlists & Filters](#playlists--filters)
- [Integration with Other Products](#integration-with-other-products)
- [Performance Considerations](#performance-considerations)
- [Common Pitfalls](#common-pitfalls)

## Session Replay Overview

Session Replay records user sessions as a series of DOM mutations (not video), allowing you to play back exactly what users saw and did. It captures clicks, scrolls, form interactions, console logs, and network requests.

Key features:
- **DOM-based recording** — lightweight, captures structure changes not pixels
- **Console logs** — see JavaScript errors and logs alongside the replay
- **Network requests** — view API calls, response times, and status codes
- **Click maps** — visualize where users click
- **Mobile support** — iOS, Android, React Native, Flutter
- **Privacy controls** — mask text, inputs, and images

## Installation & Setup

### Web — JavaScript SDK

```typescript
posthog.init('<api_key>', {
  api_host: 'https://us.i.posthog.com',
  session_recording: {
    maskAllInputs: true,
    maskTextContent: false,
  },
});
```

Session replay is enabled by default when using the JavaScript SDK. You must also enable it in Project Settings → Session Recording.

### Manual Start/Stop

```typescript
// Start recording manually (if disabled by default)
posthog.startSessionRecording();

// Stop recording
posthog.stopSessionRecording();

// Check if recording is active
const isRecording = posthog.sessionRecordingStarted();
```

## Recording Configuration

### Initialization Options

```typescript
posthog.init('<key>', {
  disable_session_recording: false,  // set true to disable entirely
  session_recording: {
    // DOM recording
    maskAllInputs: true,         // mask input field values
    maskTextContent: false,      // mask all text (aggressive)
    maskInputFn: (text, element) => {
      if (element?.dataset.record === 'true') return text;
      return '*'.repeat(text.length);
    },

    // Console logs
    consoleLogRecordingEnabled: true,
    consoleLevels: ['log', 'warn', 'error'],  // which levels to capture

    // Network
    recordCrossOriginIframes: false,

    // Canvas
    recordCanvas: false,  // record <canvas> elements (performance cost)
    canvasFps: 4,         // frames per second for canvas capture
  },
});
```

### Project Settings

In PostHog UI → Project Settings → Session Recording:
- **Enable/disable** recording globally
- **Sampling rate** — record a percentage of sessions (e.g., 50%)
- **Minimum duration** — only keep recordings longer than N seconds
- **Record console logs** — enable/disable
- **Record network requests** — enable/disable

## Privacy Controls

### Input Masking

All inputs are masked by default — the recording shows `***` instead of typed values:

```html
<!-- Override: allow recording this input -->
<input type="text" data-ph-record="true" />

<!-- Force mask (even if maskAllInputs is false) -->
<input type="text" class="ph-mask" />
```

Password inputs (`type="password"`) are always masked regardless of settings.

### Text Content Masking

```typescript
session_recording: {
  maskTextContent: true,  // replace all text with asterisks
}
```

### Element-Level Control

```html
<!-- Do not capture this element at all -->
<div class="ph-no-capture">
  Sensitive content — not recorded
</div>

<!-- Mask text in this element -->
<div data-ph-mask>
  This text becomes ****
</div>
```

### Image Masking

```typescript
session_recording: {
  maskAllImages: true,  // replace images with placeholders
}
```

## Controlling Which Sessions to Record

### Sampling

Record only a percentage of sessions:

```
Project Settings → Session Recording → Sampling rate: 50%
```

Or programmatically:

```typescript
posthog.init('<key>', {
  session_recording: {
    sample_rate: 0.5,  // 50% of sessions
  },
});
```

### Conditional Recording

```typescript
// Only record for specific users
posthog.init('<key>', {
  disable_session_recording: true,  // disabled by default
  loaded: (posthog) => {
    const user = getCurrentUser();
    if (user.plan === 'enterprise') {
      posthog.startSessionRecording();
    }
  },
});
```

### Feature Flag-Based Recording

```typescript
posthog.init('<key>', {
  disable_session_recording: true,
  loaded: (posthog) => {
    if (posthog.isFeatureEnabled('record-sessions')) {
      posthog.startSessionRecording();
    }
  },
});
```

### URL-Based Filtering

In Project Settings, define URL allow/block lists:
```
Record only: /app/*, /dashboard/*
Block: /settings/billing, /admin/*
```

## Console Log Capture

See JavaScript console output alongside the replay:

```typescript
session_recording: {
  consoleLogRecordingEnabled: true,
  consoleLevels: ['warn', 'error'],  // only capture warnings and errors
}
```

Console logs appear in a panel below the replay player, time-synced with user actions. Extremely useful for debugging — see the error at the exact moment the user encountered it.

## Network Request Capture

View API calls made during the session:

```typescript
session_recording: {
  recordHeaders: true,     // capture request/response headers
  recordBody: true,        // capture request/response bodies
  networkPayloadCapture: {
    recordHeaders: true,
    recordBody: true,
  },
}
```

The network tab shows:
- Request URL and method
- Status code
- Duration
- Request/response headers (if enabled)
- Request/response body (if enabled)
- Timing waterfall

### Sanitizing Network Data

```typescript
session_recording: {
  networkPayloadCapture: {
    recordHeaders: true,
    recordBody: (request) => {
      // Don't record auth endpoint bodies
      if (request.url.includes('/auth/')) return false;
      return true;
    },
  },
}
```

## Mobile Session Replay

### iOS (Swift)

```swift
import PostHog

let config = PostHogConfig(apiKey: "<api_key>")
config.sessionReplay = true
config.sessionReplayConfig.maskAllTextInputs = true
config.sessionReplayConfig.maskAllImages = false
config.sessionReplayConfig.screenshotMode = true  // high-fidelity

PostHogSDK.shared.setup(config)
```

### Android (Kotlin)

```kotlin
val config = PostHogAndroidConfig("<api_key>").apply {
    sessionReplay = true
    sessionReplayConfig.maskAllTextInputs = true
    sessionReplayConfig.maskAllImages = false
    sessionReplayConfig.screenshot = true
}
PostHogAndroid.setup(this, config)
```

### React Native

```typescript
import PostHog from 'posthog-react-native';

const posthog = new PostHog('<api_key>', {
  enableSessionReplay: true,
  sessionReplayConfig: {
    maskAllTextInputs: true,
    maskAllImages: false,
  },
});
```

Mobile replay modes:
- **Wireframe mode** (default) — lightweight structural representation
- **Screenshot mode** — higher fidelity but more data transfer

## Watching Replays

### Replay Player Controls

- **Play/Pause** — standard playback controls
- **Speed** — 1x, 2x, 4x, 8x, 16x playback speed
- **Skip inactivity** — automatically skip idle periods
- **Timeline** — scrub through the recording
- **Events** — click event markers to jump to that moment
- **Tabs** — Console, Network, Events panels below the player

### Finding Specific Moments

Click events in the timeline to jump to:
- Page navigations
- Clicks and form submissions
- Console errors
- Rage clicks
- Custom events

## Playlists & Filters

### Filtering Recordings

```
Filter: Duration > 30 seconds
Filter: Has console error = true
Filter: Visited URL contains /checkout
Filter: Person property: plan = 'pro'
Filter: Event: rage_click occurred
```

### Playlists

Save filtered views as playlists for quick access:
- "Error Sessions" — sessions with console errors
- "Long Sessions" — sessions > 10 minutes
- "Checkout Drop-offs" — visited checkout but didn't purchase

## Integration with Other Products

### From Funnels
Click on drop-off users in a funnel → watch their session recordings to understand why they dropped off.

### From Error Tracking
Click an exception → see the session recording at the moment the error occurred.

### From Feature Flags
Filter recordings by feature flag value to compare experiences between variants.

### From Experiments
Watch recordings from each experiment variant to understand qualitative behavior differences.

## Performance Considerations

- **Payload size** — recordings generate ~10-50 KB per minute of recording
- **CPU overhead** — minimal DOM mutation observer; typically <1% CPU impact
- **Canvas recording** — significantly higher overhead; only enable when needed
- **Network recording with body** — can increase payload; sanitize large responses
- **Mobile screenshot mode** — higher bandwidth than wireframe mode

### Optimization Tips

1. Use sampling to reduce volume
2. Set a minimum duration to filter out bot sessions
3. Disable canvas recording unless needed
4. Limit network body capture to specific endpoints
5. Use URL allowlists to only record key pages

## Common Pitfalls

1. **Not enabling in Project Settings** — SDK config alone isn't enough; must also enable in PostHog UI
2. **Recording everything** — high-traffic sites should use sampling to control costs
3. **Not masking sensitive data** — always review what's being recorded in the first few sessions
4. **Canvas-heavy apps** — canvas recording is expensive; consider if you really need it
5. **Mobile wireframe quality** — wireframe mode is lower fidelity; switch to screenshot mode for critical debugging
6. **Ad blockers** — may prevent the recording SDK from loading; use a reverse proxy
