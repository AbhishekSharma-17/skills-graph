# Expo — Overview

> Source: https://docs.expo.dev | Written for SDK 55.x

## What Is Expo

Expo is an open-source framework and cloud platform for building universal React Native apps that run on Android, iOS, and the web from a single codebase. It consists of two main pieces:

1. **Expo SDK** — a large set of cross-platform libraries (Camera, Notifications, FileSystem, etc.) that wrap native APIs and work out of the box, plus **Expo Router** for file-based navigation.
2. **EAS (Expo Application Services)** — managed cloud services for building (`eas build`), submitting (`eas submit`), and updating (`eas update`) apps without maintaining your own iOS/Android CI.

Expo is built on top of React Native. Any React Native library works in an Expo project, and you can eject to a "bare" workflow at any time without losing compatibility.

## When to Use Expo vs Bare React Native

| Scenario | Recommendation |
|----------|----------------|
| New mobile app, cross-platform | **Expo** (managed or dev-client workflow) |
| Need many native modules not in Expo SDK | Expo with **Dev Client** — still get EAS benefits |
| Need deep native customization, custom Xcode config | Bare React Native or **Expo with prebuild** |
| Want OTA updates without custom CI | **Expo** — EAS Update is built in |
| Existing React Native project wanting Expo features | Install `expo` package — integrates incrementally |

Since SDK 50+, all new Expo projects use **Continuous Native Generation (CNG)**: you declare native configuration in `app.json` / `app.config.ts`, and Expo regenerates the `ios/` and `android/` directories on demand via `npx expo prebuild`. This eliminates the managed-vs-bare split of older Expo versions.

## Core Concepts

### Continuous Native Generation (CNG)

Native code is a build artifact, not source:

- `app.json` / `app.config.ts` is the source of truth for native configuration.
- `npx expo prebuild` generates `ios/` and `android/` directories from your config plugins.
- You can still edit native files directly, but you lose `prebuild` idempotency.

### Config Plugins

Small JavaScript functions that modify native project files during `prebuild`. Many Expo SDK packages ship with config plugins — you just install the npm package and add it to `app.json` if needed.

### Dev Clients

A custom development build of your app that includes the Expo Dev Launcher. This replaces Expo Go for any project using custom native code. Created with `eas build --profile development` or `npx expo run:ios` / `run:android`.

### EAS

Three core services:

- **EAS Build** — builds `.ipa` and `.apk`/`.aab` binaries in the cloud.
- **EAS Update** — hosts JS bundles for over-the-air (OTA) updates.
- **EAS Submit** — submits built binaries to the App Store and Play Store.

## Installation

### Prerequisites

- Node.js 20+ (LTS recommended)
- Git
- For iOS development: macOS with Xcode 16+
- For Android development: Android Studio with Android SDK (API level 34+)
- An Expo account (free) for EAS usage

### Create a New Project

```bash
# Latest template (TypeScript, Expo Router, tabs)
npx create-expo-app@latest my-app

# Minimal template (blank, TypeScript)
npx create-expo-app@latest my-app --template blank-typescript

# Start the dev server
cd my-app
npx expo start
```

### Install EAS CLI

```bash
npm install -g eas-cli
eas login
# Configure the project for EAS
eas init
```

### Run on a Device

```bash
# Start Metro bundler
npx expo start

# Then:
# - Press 'i' to open iOS simulator
# - Press 'a' to open Android emulator
# - Scan QR code with Expo Go (or dev client) on a physical device
```

## First App Example

```tsx
// app/index.tsx — Expo Router picks this up automatically
import { View, Text, StyleSheet, Pressable } from 'react-native';
import { useState } from 'react';

export default function Home() {
  const [count, setCount] = useState(0);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Hello Expo!</Text>
      <Text style={styles.count}>{count}</Text>
      <Pressable style={styles.button} onPress={() => setCount(c => c + 1)}>
        <Text style={styles.buttonText}>Increment</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 16 },
  title: { fontSize: 32, fontWeight: 'bold' },
  count: { fontSize: 48 },
  button: { paddingHorizontal: 24, paddingVertical: 12, backgroundColor: '#0ea5e9', borderRadius: 8 },
  buttonText: { color: 'white', fontSize: 18, fontWeight: '600' },
});
```

## Project Structure (Expo Router default)

```
my-app/
├── app/                # File-based routes
│   ├── _layout.tsx     # Root layout
│   ├── index.tsx       # / route
│   └── (tabs)/         # Tab group
│       ├── _layout.tsx
│       ├── index.tsx
│       └── explore.tsx
├── assets/             # Images, fonts, splash/icon
├── components/         # Reusable UI
├── constants/          # Colors, config
├── hooks/              # Custom hooks
├── app.json            # Expo config (sync with app.config.ts if present)
├── eas.json            # EAS build/submit profiles
├── metro.config.js     # Metro bundler config
├── tsconfig.json
└── package.json
```

## SDK Release Cadence

Expo releases a new SDK approximately every 3–4 months. Each SDK is pinned to a specific React Native version. **You cannot mix SDK versions** — all Expo packages must match the SDK you're targeting.

- SDK 55 (current) — React Native 0.78, New Architecture enabled by default
- SDK 54 (Nov 2025) — React Native 0.77
- SDK 53 (Aug 2025) — React Native 0.76

Upgrade path: `npx expo install expo@latest --fix` followed by `npx expo install --check`.

## New Architecture

As of SDK 55, the React Native New Architecture (Fabric renderer + TurboModules) is **enabled by default** for all new projects. Existing projects can opt in via:

```json
{
  "expo": {
    "newArchEnabled": true
  }
}
```

Most Expo SDK packages are New-Arch compatible. Third-party libraries should be verified against https://reactnative.directory before upgrading.

## Pricing

- **Free tier** — 30 builds/month on shared workers, unlimited updates, community support.
- **Production** — $99/mo, 100 priority builds, faster queue, production SLA.
- **Enterprise** — Custom pricing.

OTA updates are free on all tiers (fair-use limits apply to very large apps).

## Common Pitfalls

- **Mixing SDK versions**: always use `npx expo install` instead of `npm install` so package versions are aligned to your current SDK.
- **Using Expo Go with custom native code**: if you install a library outside the SDK, you need a **Dev Client**, not Expo Go.
- **Editing ios/android directly then running prebuild**: `prebuild` with `--clean` will overwrite your edits. Use config plugins instead.
- **Missing `app.json` updates when adding permissions**: on iOS, the `NS*UsageDescription` strings must be set (usually via a config plugin in the SDK package) — otherwise the app crashes on first permission prompt.

## Related Topics

- Project setup & TypeScript → 01-project-setup.md
- Routing & navigation → 02-expo-router.md
- Native APIs → 03-expo-sdk.md
- Configuring native via plugins → 04-config-plugins.md
- Cloud builds → 06-eas-build.md
- OTA updates → 07-eas-update.md
