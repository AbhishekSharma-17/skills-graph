# Expo Dev Clients

> Source: https://docs.expo.dev/develop/development-builds/introduction/ | Written for SDK 55.x

## Overview

A **Dev Client** is a custom development build of your app that includes the Expo Dev Launcher. It replaces Expo Go when your project uses:

- Custom native code (third-party libraries with native modules)
- Config plugins that modify native behavior
- Features not supported in Expo Go (push notifications, background tasks, in-app purchases, some SDK APIs)

Think of it as "Expo Go, but with *your* native dependencies".

### Expo Go vs Dev Client

| | Expo Go | Dev Client |
|---|---------|------------|
| Install | App Store / Play Store | EAS Build + manual install |
| Native modules | Only what Expo Go ships with | Any library |
| Config plugins | Ignored | Applied |
| App icon/splash | Expo's | Yours |
| Environment variables | Limited | Full access |
| Use case | Quick experiments | Real development |

## Creating a Dev Client

### Option 1: EAS Build (recommended for teams)

```bash
# Install EAS CLI + expo-dev-client
npx expo install expo-dev-client
npm install -g eas-cli
eas login
eas init

# Build for iOS simulator (no Apple account needed)
eas build --profile development-simulator --platform ios

# Build for iOS device (requires Apple Developer account)
eas build --profile development --platform ios

# Build for Android (APK, installable directly)
eas build --profile development --platform android
```

Your `eas.json` should include:

```json
{
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal",
      "ios": { "resourceClass": "m-medium" }
    },
    "development-simulator": {
      "extends": "development",
      "ios": { "simulator": true }
    }
  }
}
```

When the build completes, EAS provides a QR code and install URL:

- **iOS**: scan with camera (Apple Developer registered devices only) or drag `.app` onto simulator
- **Android**: scan the QR code or download the APK

### Option 2: Local Build

```bash
# Local iOS build (macOS only, requires Xcode)
npx expo run:ios
# → builds to your local simulator or connected device

# Local Android build (requires Android Studio + SDK)
npx expo run:android
```

`expo run:*` runs `prebuild` automatically, then compiles natively. Faster for solo development.

### Option 3: First-Run Hybrid

Use EAS Build once, then iterate with `npx expo run:*` locally using the same native project.

## Using the Dev Client

After installing:

```bash
# Start Metro with dev client mode
npx expo start --dev-client
```

Launch the Dev Client app on your device/simulator. It shows:

- **Recently opened projects** — tap to reconnect
- **Fetch development servers** — auto-discover running servers on the local network
- **Enter URL manually** — for tunnel or custom hosts

The Dev Client connects to Metro and downloads your JS bundle.

## Dev Menu

Shake the device (or press `⌘+D` on iOS sim, `⌘+M` on Android emulator) to open the dev menu:

- Reload
- Toggle element inspector
- Toggle performance monitor
- Open JS debugger
- Go home (return to Dev Launcher)
- Extensions (Reanimated, Redux DevTools, etc.)

## Internal Distribution

Share dev builds with teammates or testers **without** the App Store:

```json
// eas.json
{
  "build": {
    "preview": {
      "distribution": "internal",
      "ios": { "simulator": false },
      "android": { "buildType": "apk" }
    }
  }
}
```

```bash
eas build --profile preview --platform all
```

EAS produces a shareable link and QR code. On Android it downloads the APK directly. On iOS, testers must register their UDIDs:

```bash
eas device:create
```

Users visit the link, register, then install. UDIDs are added to your provisioning profile on the next build.

For larger-scale beta distribution, use TestFlight (iOS) or Google Play Internal Testing (see 08-eas-submit.md).

## Native Modules & Custom Code

Any React Native library works in a Dev Client. Install, then rebuild:

```bash
npm install react-native-mmkv
# Requires native code → rebuild
eas build --profile development
# or
npx expo run:ios
```

For config-plugin-driven libraries (most Expo libraries), `npx expo install` handles the plugin registration.

## Prebuild Workflow

`prebuild` transforms your `app.json` / config plugins into `ios/` and `android/` folders.

```bash
# Generate native folders
npx expo prebuild

# Specific platform
npx expo prebuild -p ios

# Clean regeneration (ignores manual edits)
npx expo prebuild --clean

# Inspect what would change without writing
npx expo prebuild --no-install
```

Two modes:

1. **Managed (recommended)**: don't commit `ios/`/`android/`. `prebuild` runs during each build. Config changes take effect automatically.
2. **Bare**: commit `ios/`/`android/`. You manage them like a standard RN project. Useful for deep customization not possible via config plugins.

Switch to bare:

```bash
npx expo prebuild
git add ios/ android/
# Manage natively from here
```

## Debugging

### React Native DevTools (SDK 50+)

Press `j` in the Metro server to open Chrome DevTools with:

- Console
- Network inspector (fetch, XHR, WebSocket)
- Source-mapped debugger
- React Component tree
- Performance profiler

### Flipper (deprecated, SDK 50-)

Use React Native DevTools instead.

### Reanimated Debugger

Requires `@shopify/react-native-performance` or bundled Reanimated debug UI. Access via the extensions panel in Metro.

## Environment Variables in Dev Clients

Dev clients honor `.env` files at **build time**:

```bash
# .env.development
EXPO_PUBLIC_API_URL=http://localhost:3000
```

For EAS Build env vars:

```bash
eas env:create                          # Interactive
eas env:list --environment development
eas env:pull --environment development  # Pulls to .env.local
```

## Updating the Dev Client

Rebuild your dev client when:

- Installing / removing a library with native code
- Changing `plugins` in `app.json`
- Upgrading the Expo SDK
- Changing `expo-dev-client` or `expo-updates` version

JS-only changes just need a Metro reload.

## Common Pitfalls

- **Trying to use Expo Go with a non-Expo-Go library**: you'll see "Main has not been registered" or "Native module X cannot be null". Build a dev client instead.
- **Mixed Dev Client + Expo Go on one device**: each connects to Metro differently. Uninstall Expo Go if confused.
- **Dev Client from SDK N doesn't work with Metro from SDK N+1**: rebuild after upgrading.
- **Connecting to Metro on a different network**: use `npx expo start --tunnel` — it proxies through Expo's servers.
- **"Network error" when loading JS**: firewall blocking port 8081, or Metro on a different interface. Check `localhost:8081/status` from the device's browser.

## Related Topics

- Config plugins that drive native → 04-config-plugins.md
- Cloud build profiles → 06-eas-build.md
- Managing build credentials → 06-eas-build.md
