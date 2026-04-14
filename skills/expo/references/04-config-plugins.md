# Expo Config & Config Plugins

> Source: https://docs.expo.dev/config-plugins/introduction/ | Written for SDK 55.x

## Table of Contents

- [Overview](#overview)
- [app.json vs app.config.ts](#appjson-vs-appconfigts)
- [Core Config Fields](#core-config-fields)
- [iOS Configuration](#ios-configuration)
- [Android Configuration](#android-configuration)
- [Icons & Splash Screen](#icons--splash-screen)
- [Config Plugins](#config-plugins)
- [Writing a Custom Plugin](#writing-a-custom-plugin)
- [Prebuild Workflow](#prebuild-workflow)
- [Dynamic Config & Environment](#dynamic-config--environment)

## Overview

Expo treats native configuration (Info.plist, AndroidManifest.xml, build.gradle, etc.) as **derived from your JS config**. Instead of editing native files directly, you declare the config in `app.json` or `app.config.ts`, and `npx expo prebuild` regenerates the native projects.

Benefits:

- One config file, both platforms
- Upgrades are clean — Expo can regenerate native code for a new SDK
- Config plugins provide reusable native customizations

## app.json vs app.config.ts

Expo reads config in this order (first match wins):

1. `app.config.ts` or `app.config.js` (dynamic — can read env vars, compute values)
2. `app.json` or `app.config.json` (static)

If you have both, `app.config.ts` is primary but can read `app.json` via its `config` argument:

```ts
// app.config.ts
import { ExpoConfig, ConfigContext } from 'expo/config';

export default ({ config }: ConfigContext): ExpoConfig => ({
  ...config,
  name: process.env.APP_ENV === 'production' ? 'MyApp' : 'MyApp (Dev)',
  ios: {
    ...config.ios,
    bundleIdentifier:
      process.env.APP_ENV === 'production'
        ? 'com.example.myapp'
        : 'com.example.myapp.dev',
  },
  extra: {
    apiUrl: process.env.API_URL,
    eas: { projectId: '...' },
  },
});
```

View the effective config:

```bash
npx expo config
npx expo config --type public   # What ships in the JS bundle
```

## Core Config Fields

```json
{
  "expo": {
    "name": "My App",                 // Display name
    "slug": "my-app",                 // URL-friendly ID (used in dev URLs)
    "version": "1.0.0",               // Marketing version (shown in stores)
    "orientation": "portrait",        // portrait | landscape | default
    "icon": "./assets/icon.png",
    "scheme": "myapp",                // URL scheme for deep links
    "userInterfaceStyle": "automatic", // light | dark | automatic
    "newArchEnabled": true,
    "splash": {
      "image": "./assets/splash.png",
      "resizeMode": "contain",
      "backgroundColor": "#ffffff"
    },
    "assetBundlePatterns": ["**/*"],
    "runtimeVersion": { "policy": "appVersion" }
  }
}
```

## iOS Configuration

```json
{
  "expo": {
    "ios": {
      "bundleIdentifier": "com.example.myapp",
      "buildNumber": "1",
      "supportsTablet": true,
      "requireFullScreen": false,
      "associatedDomains": ["applinks:myapp.example.com"],
      "infoPlist": {
        "NSCameraUsageDescription": "Take photos",
        "UIBackgroundModes": ["audio", "location"]
      },
      "entitlements": {
        "aps-environment": "production"
      },
      "googleServicesFile": "./GoogleService-Info.plist"
    }
  }
}
```

## Android Configuration

```json
{
  "expo": {
    "android": {
      "package": "com.example.myapp",
      "versionCode": 1,
      "adaptiveIcon": {
        "foregroundImage": "./assets/adaptive-icon.png",
        "backgroundColor": "#ffffff"
      },
      "permissions": [
        "android.permission.CAMERA",
        "android.permission.ACCESS_FINE_LOCATION"
      ],
      "intentFilters": [
        {
          "action": "VIEW",
          "autoVerify": true,
          "data": [{ "scheme": "https", "host": "myapp.example.com" }],
          "category": ["BROWSABLE", "DEFAULT"]
        }
      ],
      "googleServicesFile": "./google-services.json"
    }
  }
}
```

## Icons & Splash Screen

Drop these files in `assets/` and reference them:

| File | Size | Purpose |
|------|------|---------|
| `icon.png` | 1024×1024 | iOS app icon |
| `adaptive-icon.png` | 1024×1024 | Android adaptive icon foreground |
| `splash.png` | 1242×2436 | Splash screen |
| `favicon.png` | 48×48 | Web favicon |

**Splash screen** (SDK 51+ uses `expo-splash-screen` plugin):

```json
{
  "plugins": [
    ["expo-splash-screen", {
      "backgroundColor": "#ffffff",
      "image": "./assets/splash.png",
      "dark": { "image": "./assets/splash-dark.png", "backgroundColor": "#000000" },
      "imageWidth": 200
    }]
  ]
}
```

Control splash visibility programmatically:

```tsx
import * as SplashScreen from 'expo-splash-screen';

SplashScreen.preventAutoHideAsync();

// After fonts/data are loaded
await SplashScreen.hideAsync();
```

## Config Plugins

Config plugins are functions that modify the native project during `prebuild`. Many Expo SDK packages ship plugins — just add them to `plugins` in your config.

```json
{
  "expo": {
    "plugins": [
      "expo-router",
      ["expo-camera", { "cameraPermission": "Take photos" }],
      ["expo-notifications", {
        "icon": "./assets/notification-icon.png",
        "color": "#ffffff"
      }],
      ["expo-build-properties", {
        "ios": { "deploymentTarget": "15.1", "useFrameworks": "static" },
        "android": { "minSdkVersion": 24, "compileSdkVersion": 34 }
      }]
    ]
  }
}
```

### Useful community plugins

- `expo-build-properties` — tweak native build config (SDK versions, frameworks, etc.)
- `expo-font` — custom fonts
- `expo-image-picker` — permissions
- `react-native-firebase` — firebase modules (requires dev client)

## Writing a Custom Plugin

```ts
// plugins/with-custom-urlscheme.ts
import { ConfigPlugin, withInfoPlist } from 'expo/config-plugins';

const withCustomUrlScheme: ConfigPlugin<{ scheme: string }> = (config, { scheme }) => {
  return withInfoPlist(config, (c) => {
    const arr = (c.modResults.CFBundleURLTypes ||= []);
    arr.push({ CFBundleURLSchemes: [scheme] });
    return c;
  });
};

export default withCustomUrlScheme;
```

Use it:

```json
{
  "plugins": [
    ["./plugins/with-custom-urlscheme", { "scheme": "myapp" }]
  ]
}
```

### Available mod APIs

- `withInfoPlist` / `withEntitlementsPlist` — iOS plist files
- `withAndroidManifest` — `AndroidManifest.xml`
- `withStringsXml` / `withColorsXml` — Android resources
- `withAppDelegate` — modify `AppDelegate.swift`/`AppDelegate.mm`
- `withMainActivity` / `withMainApplication` — Android Java/Kotlin
- `withGradleProperties` / `withProjectBuildGradle` / `withAppBuildGradle` — Android Gradle

## Prebuild Workflow

```bash
# Generate ios/ and android/ from config
npx expo prebuild

# Specific platform
npx expo prebuild -p ios
npx expo prebuild -p android

# Regenerate from scratch (overwrite manual edits)
npx expo prebuild --clean

# Run directly (prebuild + native run)
npx expo run:ios
npx expo run:android
```

Two workflows:

1. **Managed** (no `ios/` or `android/` folders committed): `prebuild` runs on every EAS Build. Upgrades are seamless.
2. **Bare** (native folders committed): `prebuild` generates one-time, you edit natively from there. Upgrades require merging.

## Dynamic Config & Environment

Dynamic config with `app.config.ts` + environment variables:

```ts
import { ExpoConfig, ConfigContext } from 'expo/config';

const IS_DEV = process.env.APP_VARIANT === 'development';
const IS_PREVIEW = process.env.APP_VARIANT === 'preview';

export default ({ config }: ConfigContext): ExpoConfig => ({
  ...config,
  name: IS_DEV ? 'MyApp Dev' : IS_PREVIEW ? 'MyApp Preview' : 'MyApp',
  ios: {
    bundleIdentifier: IS_DEV
      ? 'com.example.myapp.dev'
      : IS_PREVIEW
      ? 'com.example.myapp.preview'
      : 'com.example.myapp',
  },
  android: {
    package: IS_DEV
      ? 'com.example.myapp.dev'
      : IS_PREVIEW
      ? 'com.example.myapp.preview'
      : 'com.example.myapp',
  },
  extra: {
    apiUrl: process.env.EXPO_PUBLIC_API_URL,
    eas: { projectId: 'xxx' },
  },
});
```

Wire into EAS profiles:

```json
// eas.json
{
  "build": {
    "development": { "env": { "APP_VARIANT": "development" } },
    "preview":     { "env": { "APP_VARIANT": "preview" } },
    "production":  { "env": { "APP_VARIANT": "production" } }
  }
}
```

Now `eas build --profile development` produces a dev-variant app side-installable with production.

## Reading Config at Runtime

```tsx
import Constants from 'expo-constants';

const apiUrl = Constants.expoConfig?.extra?.apiUrl;
```

## Common Pitfalls

- **Editing `app.json` alone isn't enough** — you need to rebuild (`eas build` or `expo run:ios`) for native config changes to take effect. JS-only changes can be delivered via EAS Update.
- **`plugins` order matters** — some plugins modify the same file. If two plugins conflict, order in the array determines precedence.
- **Dynamic config breaks static inspection** — don't use dynamic values for `slug`, `owner`, or `eas.projectId`. Those must be static.
- **Don't commit `ios/` and `android/` in managed projects** — add them to `.gitignore`. They're regenerated on each build.

## Related Topics

- Creating a dev client → 05-dev-clients.md
- Build profiles → 06-eas-build.md
- EAS Update channels → 07-eas-update.md
