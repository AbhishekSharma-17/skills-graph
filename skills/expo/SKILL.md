---
name: expo
description: "Expo framework and platform for universal React Native apps on iOS, Android, and Web. Covers Expo SDK, Expo Router file-based routing, EAS Build/Update/Submit, config plugins, push notifications, and dev clients. MANDATORY TRIGGERS: expo, expo sdk, expo-router, eas build, eas update, eas submit, create-expo-app, expo-dev-client. Also trigger when building React Native apps with managed workflow, OTA updates, cloud iOS/Android builds, universal apps, or file-based routing for native apps. When in doubt about whether to use this skill for React Native or mobile development tasks with Expo, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["expo", "react-native", "mobile", "ios", "android", "eas", "expo-router", "universal-app", "push-notifications"]
---

# Expo

> Version tracked: SDK 55.x (expo 55.0.15, expo-router 55.0.12, eas-cli 18.7.0) | Source: https://docs.expo.dev

## Reference Files

| File | Read When |
|------|-----------|
| [00-overview](references/00-overview.md) | Starting with Expo, installation, managed vs bare workflow, core concepts |
| [01-project-setup](references/01-project-setup.md) | Creating projects with create-expo-app, TypeScript, dev server, project structure |
| [02-expo-router](references/02-expo-router.md) | File-based routing, layouts, navigation, typed routes, tabs, modals |
| [03-expo-sdk](references/03-expo-sdk.md) | Core APIs — Camera, Location, MediaLibrary, Sensors, FileSystem, SQLite |
| [04-config-plugins](references/04-config-plugins.md) | app.json/app.config.ts, config plugins, native permissions, icon/splash |
| [05-dev-clients](references/05-dev-clients.md) | Custom dev clients, expo-dev-client, native modules, prebuild |
| [06-eas-build](references/06-eas-build.md) | Cloud iOS/Android builds, build profiles, credentials, internal distribution |
| [07-eas-update](references/07-eas-update.md) | OTA updates, channels, branches, rollbacks, runtime version |
| [08-eas-submit](references/08-eas-submit.md) | App Store & Play Store submission, credentials, release workflow |
| [09-push-notifications](references/09-push-notifications.md) | expo-notifications, tokens, push service, FCM/APNS, handlers |
| [10-authentication](references/10-authentication.md) | expo-auth-session, OAuth, SecureStore, biometrics, session management |
| [11-styling-ui](references/11-styling-ui.md) | NativeWind, styled-components, safe areas, theming, responsive layouts |
| [12-common-patterns](references/12-common-patterns.md) | Best practices, pitfalls, testing, monorepos, migration from bare RN |

## Installation

```bash
# Create a new project
npx create-expo-app@latest my-app
cd my-app

# Install EAS CLI globally
npm install -g eas-cli
eas login

# Run the dev server
npx expo start

# Add Expo SDK package to existing project
npx expo install expo-router expo-image expo-notifications

# Verify
npx expo --version
eas --version
```

## Quick Reference

- Docs: https://docs.expo.dev
- SDK API: https://docs.expo.dev/versions/latest/
- EAS: https://expo.dev/eas
- GitHub: https://github.com/expo/expo
- Snack (browser playground): https://snack.expo.dev
- Discord: https://chat.expo.dev
