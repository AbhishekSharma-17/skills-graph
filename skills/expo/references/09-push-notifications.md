# Push Notifications (expo-notifications)

> Source: https://docs.expo.dev/push-notifications/overview/ | Written for SDK 55.x

## Table of Contents

- [Overview](#overview)
- [Setup](#setup)
- [Getting a Push Token](#getting-a-push-token)
- [Sending Notifications](#sending-notifications)
- [Receiving & Handling](#receiving--handling)
- [Local Notifications](#local-notifications)
- [Categories & Actions](#categories--actions)
- [Rich Content](#rich-content)
- [Silent / Background Push](#silent--background-push)
- [Platform Credentials](#platform-credentials)
- [Troubleshooting](#troubleshooting)

## Overview

`expo-notifications` handles both local and remote push notifications on iOS and Android. For remote push, Expo's **Push Service** (free) forwards messages to APNS (iOS) and FCM (Android) on your behalf — you just call one REST endpoint.

**Requires a dev client or production build** — Expo Go does not support push notifications.

## Setup

```bash
npx expo install expo-notifications expo-device expo-constants
```

Configure `app.json`:

```json
{
  "expo": {
    "plugins": [
      ["expo-notifications", {
        "icon": "./assets/notification-icon.png",
        "color": "#0ea5e9",
        "sounds": ["./assets/notification-sound.wav"]
      }]
    ]
  }
}
```

### iOS

In `app.json`:

```json
{
  "ios": {
    "infoPlist": {
      "UIBackgroundModes": ["remote-notification"]
    },
    "entitlements": {
      "aps-environment": "production"
    }
  }
}
```

### Android

Add an FCM server key:

1. Create a Firebase project at https://console.firebase.google.com
2. Add Android app with your `android.package`
3. Download `google-services.json` → save to repo root
4. Configure:

```json
{
  "android": {
    "googleServicesFile": "./google-services.json"
  }
}
```

5. Upload FCM credentials to Expo:

```bash
eas credentials
# → Android → Push Notifications → Upload Google Service Account JSON
```

## Getting a Push Token

```tsx
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import Constants from 'expo-constants';
import { Platform } from 'react-native';

async function registerForPushNotifications() {
  if (!Device.isDevice) {
    alert('Push notifications require a physical device');
    return null;
  }

  // Check / request permission
  const { status: existing } = await Notifications.getPermissionsAsync();
  let status = existing;
  if (status !== 'granted') {
    const req = await Notifications.requestPermissionsAsync();
    status = req.status;
  }
  if (status !== 'granted') return null;

  // Android: set up default channel
  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('default', {
      name: 'Default',
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: '#0ea5e9',
    });
  }

  // Get the Expo push token
  const projectId = Constants.expoConfig?.extra?.eas?.projectId;
  const token = (await Notifications.getExpoPushTokenAsync({ projectId })).data;
  return token; // Store this on your server
}
```

Token format: `ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]` — not a raw APNS/FCM token.

## Sending Notifications

### Using Expo Push API

```bash
curl -X POST https://exp.host/--/api/v2/push/send \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "to": "ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]",
    "title": "Hello",
    "body": "World",
    "data": { "url": "/profile/42" },
    "sound": "default",
    "badge": 1
  }'
```

Batch up to 100 messages per request:

```json
[
  { "to": "Token1", "title": "Hi" },
  { "to": "Token2", "title": "Hi" }
]
```

### Using the Node SDK

```bash
npm install expo-server-sdk
```

```ts
import { Expo, ExpoPushMessage } from 'expo-server-sdk';

const expo = new Expo({ accessToken: process.env.EXPO_ACCESS_TOKEN });

async function sendPush(tokens: string[]) {
  const messages: ExpoPushMessage[] = tokens
    .filter(t => Expo.isExpoPushToken(t))
    .map(t => ({
      to: t,
      sound: 'default',
      title: 'New message',
      body: 'You have a new message',
      data: { type: 'chat' },
    }));

  const chunks = expo.chunkPushNotifications(messages);
  for (const chunk of chunks) {
    const tickets = await expo.sendPushNotificationsAsync(chunk);
    // Store tickets to check status later
  }
}
```

### Check receipts

```ts
// 15-30 minutes after sending, check receipts for delivery status
const receipts = await expo.getPushNotificationReceiptsAsync(['receipt-id']);
for (const id in receipts) {
  const { status, message, details } = receipts[id];
  if (status === 'error' && details?.error === 'DeviceNotRegistered') {
    // Remove this token from DB
  }
}
```

## Receiving & Handling

### Foreground handler

```tsx
import * as Notifications from 'expo-notifications';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowBanner: true,
    shouldShowList: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});
```

### Listeners

```tsx
import * as Notifications from 'expo-notifications';
import { useEffect } from 'react';

function useNotifications() {
  useEffect(() => {
    // Received while app in foreground
    const receivedSub = Notifications.addNotificationReceivedListener(notification => {
      console.log('Received:', notification.request.content);
    });

    // User tapped a notification
    const responseSub = Notifications.addNotificationResponseReceivedListener(response => {
      const { data } = response.notification.request.content;
      if (data.url) router.push(data.url as any);
    });

    return () => {
      receivedSub.remove();
      responseSub.remove();
    };
  }, []);
}
```

### Handling app-launched-from-notification

```tsx
useEffect(() => {
  (async () => {
    const last = await Notifications.getLastNotificationResponseAsync();
    if (last?.notification.request.content.data.url) {
      router.push(last.notification.request.content.data.url);
    }
  })();
}, []);
```

## Local Notifications

Schedule notifications without a server:

```tsx
import * as Notifications from 'expo-notifications';

// Fire after 10 seconds
await Notifications.scheduleNotificationAsync({
  content: {
    title: 'Reminder',
    body: 'Drink water!',
    sound: 'default',
  },
  trigger: { seconds: 10 },
});

// Daily at 8 AM
await Notifications.scheduleNotificationAsync({
  content: { title: 'Good morning' },
  trigger: { hour: 8, minute: 0, repeats: true },
});

// Cancel all
await Notifications.cancelAllScheduledNotificationsAsync();

// Cancel specific
const id = await Notifications.scheduleNotificationAsync({ ... });
await Notifications.cancelScheduledNotificationAsync(id);
```

## Categories & Actions

Interactive notifications with action buttons:

```tsx
await Notifications.setNotificationCategoryAsync('message', [
  { identifier: 'reply', buttonTitle: 'Reply', textInput: { placeholder: 'Reply...' } },
  { identifier: 'archive', buttonTitle: 'Archive' },
]);

// Send with the category
await fetch('https://exp.host/--/api/v2/push/send', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    to: token,
    title: 'John',
    body: 'Hey!',
    categoryId: 'message',
  }),
});

// Handle the action
Notifications.addNotificationResponseReceivedListener(response => {
  const { actionIdentifier, userText } = response;
  if (actionIdentifier === 'reply') {
    sendReply(userText);
  }
});
```

## Rich Content

### Images (iOS)

Send image via push message:

```json
{
  "to": "ExponentPushToken[...]",
  "title": "New photo",
  "body": "Check this out",
  "richContent": { "image": "https://example.com/photo.jpg" }
}
```

Requires iOS Notification Service Extension (via `expo-build-properties` or custom plugin).

### Android channels

```tsx
await Notifications.setNotificationChannelAsync('messages', {
  name: 'Messages',
  importance: Notifications.AndroidImportance.HIGH,
  sound: 'custom.wav',
  vibrationPattern: [0, 250, 250, 250],
  lightColor: '#0ea5e9',
});

// Send targeting the channel
// Expo API: set "channelId": "messages" in the push message
```

## Silent / Background Push

Deliver data to the app without showing a notification:

```json
{
  "to": "ExponentPushToken[...]",
  "_contentAvailable": true,
  "data": { "type": "sync", "version": 42 }
}
```

On iOS, set `"aps-environment"` to `"production"` and enable the `remote-notification` background mode. On Android, use FCM's data-only message.

Handle in a background task:

```tsx
import * as TaskManager from 'expo-task-manager';
import * as Notifications from 'expo-notifications';

const BG_TASK = 'BACKGROUND-NOTIFICATION-TASK';

TaskManager.defineTask(BG_TASK, ({ data, error }) => {
  if (error) return;
  // Sync data, update cache, etc.
});

Notifications.registerTaskAsync(BG_TASK);
```

## Platform Credentials

### APNS (iOS)

```bash
eas credentials
# → iOS → Push Notifications → Generate APNS key
```

EAS creates an APNS key valid for all your apps. Reused across builds.

### FCM v1 (Android)

Required as of 2024 — legacy FCM server keys no longer work.

Upload the service-account JSON:

```bash
eas credentials
# → Android → Google Service Account Key for Push Notifications
```

## Troubleshooting

### "No push tokens received"

- Running in Expo Go: rebuild with dev client.
- Running on simulator: push doesn't work on iOS simulators (use a real device).
- Permission denied: check settings.

### "InvalidCredentials" errors

- iOS: regenerate APNS key (`eas credentials`).
- Android: re-upload FCM service account JSON.

### Notifications arrive but don't open app

- Missing foreground handler — ensure `setNotificationHandler` is called at app start.

### Tokens change unexpectedly

Tokens can rotate on reinstall, OS upgrade, or app reset. Always store tokens on the server keyed by user, and update on every app launch.

## Common Pitfalls

- **Expo Go has no push**: always test on a dev client.
- **Token storage**: push tokens are device-specific. Store per user, not per account — users can have multiple devices.
- **Testing from simulator**: iOS sim supports simulated local notifications but not remote push. Use a real device.
- **Rate limits**: Expo Push Service allows 600 notifications per second. For higher throughput, send directly to APNS/FCM.
- **Foreground display on iOS requires `setNotificationHandler`**: otherwise notifications arriving while the app is open are silently consumed.

## Related Topics

- Permissions setup → 04-config-plugins.md
- Dev clients required → 05-dev-clients.md
- CI-driven push → 12-common-patterns.md
