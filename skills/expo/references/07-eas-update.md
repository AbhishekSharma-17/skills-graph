# EAS Update — Over-the-Air Updates

> Source: https://docs.expo.dev/eas-update/introduction/ | Written for eas-cli 18.x, SDK 55

## Table of Contents

- [Overview](#overview)
- [Setup](#setup)
- [Branches vs Channels](#branches-vs-channels)
- [Publishing Updates](#publishing-updates)
- [Runtime Version Policies](#runtime-version-policies)
- [Update Delivery](#update-delivery)
- [Rollbacks](#rollbacks)
- [Custom Update Logic](#custom-update-logic)
- [Assets & Size Limits](#assets--size-limits)
- [Troubleshooting](#troubleshooting)

## Overview

EAS Update delivers JavaScript and asset updates to installed apps without a new App Store / Play Store submission. Users get the latest version on next launch.

What can be updated OTA:

- JavaScript code (routes, components, business logic)
- Images, fonts, and other assets bundled with the JS
- `app.json` fields that don't affect native (name changes, splash colors, etc.)

What **cannot** be updated OTA:

- Native code changes (new SDK version, new native modules)
- Permissions (iOS Info.plist, Android manifest)
- Changes to `android/` or `ios/` folders

When native changes, you must submit a new build.

## Setup

```bash
# Install (if not already from create-expo-app)
npx expo install expo-updates

# Configure
eas update:configure
```

This updates `app.json`:

```json
{
  "expo": {
    "updates": {
      "url": "https://u.expo.dev/<project-id>"
    },
    "runtimeVersion": { "policy": "appVersion" }
  }
}
```

And adds the project ID reference to both platforms.

## Branches vs Channels

**Branch** = a stream of updates (like a git branch).

**Channel** = a named pointer your *binary* subscribes to. Each build sets `channel` in `eas.json`. The channel maps to one or more branches.

Example mapping:

```
channel "production" ──▶ branch "release-v2"
channel "preview"    ──▶ branch "staging"
channel "development"──▶ branch "main"
```

You publish updates to a **branch**. Binaries listening on a **channel** receive them.

This separation means you can:

- Hotfix production (`release-v2` branch) while preview continues on `staging`.
- Promote an update from `staging` → `release-v2` after QA.
- Run A/B tests by mapping two branches to one channel.

### Channel setup in eas.json

```json
{
  "build": {
    "development": { "channel": "development" },
    "preview":     { "channel": "preview" },
    "production":  { "channel": "production" }
  }
}
```

## Publishing Updates

```bash
# Publish to a branch (default: current git branch name)
eas update --branch production --message "Fix login bug"

# Shorthand: use the --auto flag (branch = git branch, message = git message)
eas update --auto

# Specific platform only
eas update --branch production --platform ios

# Republish a previous update (rollback or promote)
eas update:republish --branch production --group <update-group-id>
```

### Managing branches

```bash
# List branches
eas branch:list

# Create a branch
eas branch:create staging

# Rename a branch
eas branch:rename old-name new-name

# Delete
eas branch:delete old-name
```

### Mapping channels to branches

```bash
# Point channel to branch
eas channel:edit production --branch release-v2

# View channel config
eas channel:view production

# List all channels
eas channel:list
```

## Runtime Version Policies

`runtimeVersion` is the contract between a **binary** and an **update**. A binary only accepts updates with a matching runtime version.

Three policies in `app.json`:

### 1. `appVersion` (recommended for most apps)

```json
{ "runtimeVersion": { "policy": "appVersion" } }
```

Uses `expo.version` (e.g. `"1.2.0"`). Each new marketing version starts a new runtime — safer but requires rebuilding when bumping `version`.

### 2. `sdkVersion`

```json
{ "runtimeVersion": { "policy": "sdkVersion" } }
```

Tied to your Expo SDK (e.g. `"55.0.0"`). Updates across app versions work, but you must rebuild after every SDK upgrade.

### 3. `fingerprint` (most flexible, SDK 51+)

```json
{ "runtimeVersion": { "policy": "fingerprint" } }
```

Computes a hash of your native code + config. Updates are compatible as long as native layer hasn't changed — even across marketing versions. Requires `expo-fingerprint`:

```bash
npx expo install expo-updates expo-modules-autolinking
```

Compute current fingerprint:

```bash
npx @expo/fingerprint <project-dir>
```

### 4. Manual string

```json
{ "runtimeVersion": "1.0.0" }
```

You manage values manually. Useful if you want fine-grained control.

### Choosing a policy

- **Simple apps, frequent marketing releases** → `appVersion`
- **Many OTA hotfixes between releases** → `fingerprint`
- **Tight SDK-version alignment** → `sdkVersion`

## Update Delivery

When the app launches:

1. Client sends `{ channel, runtimeVersion, platform, appId }` to the update URL.
2. EAS resolves: `channel → branch → latest compatible update`.
3. If a new update exists, client downloads asynchronously.
4. On next launch (by default), the new JS bundle is loaded.

### Launch behavior

```json
// app.json
{
  "expo": {
    "updates": {
      "url": "https://u.expo.dev/<project-id>",
      "fallbackToCacheTimeout": 0,    // Don't wait for update on launch
      "checkAutomatically": "ON_LOAD" // or "ON_ERROR_RECOVERY" or "NEVER"
    }
  }
}
```

- `fallbackToCacheTimeout: 0` (default) — show cached content immediately, fetch update in background.
- `fallbackToCacheTimeout: 10000` — block launch up to 10s waiting for update.

### Forcing an immediate update

```tsx
import * as Updates from 'expo-updates';
import { useEffect } from 'react';

export default function App() {
  useEffect(() => {
    async function checkForUpdates() {
      try {
        const result = await Updates.checkForUpdateAsync();
        if (result.isAvailable) {
          await Updates.fetchUpdateAsync();
          await Updates.reloadAsync(); // Restart with new bundle
        }
      } catch (e) {
        // Network failure, etc.
      }
    }
    checkForUpdates();
  }, []);

  return <MyApp />;
}
```

## Rollbacks

If a bad update is live, republish the previous known-good update:

```bash
# List updates on a branch
eas update:list --branch production

# Republish a specific update group
eas update:republish --branch production --group <group-id>

# Or delete a bad update
eas update:delete <update-id>
```

Rolled-back users get the republished update on next launch.

## Custom Update Logic

### Download & prompt

```tsx
import * as Updates from 'expo-updates';
import { Alert } from 'react-native';

async function handleUpdate() {
  const res = await Updates.checkForUpdateAsync();
  if (!res.isAvailable) return;

  await Updates.fetchUpdateAsync();

  Alert.alert(
    'Update available',
    'Restart to install the latest version?',
    [
      { text: 'Later' },
      { text: 'Restart', onPress: () => Updates.reloadAsync() },
    ],
  );
}
```

### Hooks

```tsx
import { useUpdates } from 'expo-updates';

function UpdateBanner() {
  const { isUpdatePending, downloadedUpdate } = useUpdates();

  if (isUpdatePending) {
    return (
      <Banner>
        Update ready — <Button onPress={Updates.reloadAsync}>Restart</Button>
      </Banner>
    );
  }
  return null;
}
```

### Inspecting current update

```tsx
import * as Updates from 'expo-updates';

console.log('Channel:', Updates.channel);
console.log('Runtime:', Updates.runtimeVersion);
console.log('Update ID:', Updates.updateId);
console.log('Commit:', Updates.manifest?.extra?.expoClient?.extra?.git_commit);
```

## Assets & Size Limits

Assets imported via `require('./image.png')` or in `assetBundlePatterns` are included in the update:

```json
{
  "expo": {
    "assetBundlePatterns": ["**/*"]
  }
}
```

Size limits:

- Free tier: **30MB** per update (JS + assets)
- Production tier: **100MB** per update

Tips:

- Use remote URLs for large assets (S3, Cloudflare R2)
- Use `expo-image` with `cachePolicy="memory-disk"` for runtime-fetched images
- Enable Hermes and ProGuard to minimize JS size

## Troubleshooting

### Update doesn't appear on device

1. Check runtime version matches:
   ```bash
   eas update:list --branch production --json | jq '.[] | .runtimeVersion'
   ```
   Must match the binary's `runtimeVersion`.

2. Check channel mapping:
   ```bash
   eas channel:view production
   ```

3. Force a check:
   ```tsx
   const res = await Updates.checkForUpdateAsync();
   console.log(res);
   ```

### "No updates found" but you just published

- Wait a few seconds — CDN propagation
- Check that `EXPO_UPDATES_URL` in the binary matches your account

### Development builds ignore EAS Update

By default, updates only run in release builds. To test in dev:

```json
// eas.json
{
  "build": {
    "development": { "env": { "EXPO_USE_UPDATES_IN_DEV": "true" } }
  }
}
```

## Common Pitfalls

- **Publishing to the wrong branch**: `eas update --auto` uses git branch name. If you're on `feature/x`, the update goes to branch `feature/x`, not `production`. Always specify `--branch` for production.
- **Runtime version mismatch after SDK upgrade**: bumping Expo SDK changes the fingerprint/sdkVersion. Old binaries won't receive new updates — release a new build.
- **Native module added without rebuild**: OTA updates can't ship native code. Users crash with "Module X not found". Always rebuild when adding native deps.
- **Forgetting `autoIncrement`**: see 06-eas-build.md — submitting duplicate build numbers fails.
- **Misaligned `channel` and build profile**: binaries built with `channel: "preview"` never receive updates sent to `production`. Verify `eas build:view <id>` matches expected channel.

## Related Topics

- Build configuration → 06-eas-build.md
- Submission workflow → 08-eas-submit.md
- CI/CD pipelines → 12-common-patterns.md
