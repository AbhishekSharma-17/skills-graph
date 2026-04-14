# EAS Build

> Source: https://docs.expo.dev/build/introduction/ | Written for eas-cli 18.x, SDK 55

## Table of Contents

- [Overview](#overview)
- [Setup](#setup)
- [eas.json Profiles](#easjson-profiles)
- [Build Commands](#build-commands)
- [Credentials Management](#credentials-management)
- [Build Environments & Secrets](#build-environments--secrets)
- [Resource Classes](#resource-classes)
- [Monorepos](#monorepos)
- [CI Integration](#ci-integration)
- [Troubleshooting](#troubleshooting)

## Overview

EAS Build compiles `.ipa` (iOS) and `.apk`/`.aab` (Android) binaries in the cloud. It eliminates the need for a local iOS/Android toolchain and handles code signing, certificates, and provisioning automatically.

Key features:

- Managed Apple/Google credentials (one-click generation)
- Fully configurable build environment
- Build profiles for dev / preview / production
- Supports any React Native library, not just Expo SDK
- Cached dependencies across builds

## Setup

```bash
# Install CLI
npm install -g eas-cli
eas login

# Initialize project (generates eas.json, links to Expo account)
eas init

# Install expo-dev-client for development builds (optional)
npx expo install expo-dev-client
```

This creates an `eas.json` with default profiles and adds `extra.eas.projectId` to `app.json`.

## eas.json Profiles

A **profile** is a named build configuration. You invoke builds via `eas build --profile <name>`.

```json
{
  "cli": { "version": ">= 18.0.0" },
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal",
      "channel": "development",
      "ios": { "resourceClass": "m-medium" },
      "android": { "buildType": "apk" },
      "env": { "APP_VARIANT": "development" }
    },
    "preview": {
      "distribution": "internal",
      "channel": "preview",
      "ios": { "resourceClass": "m-medium" },
      "android": { "buildType": "apk" }
    },
    "production": {
      "channel": "production",
      "autoIncrement": true,
      "ios": { "resourceClass": "m-large" },
      "android": { "buildType": "app-bundle" }
    }
  },
  "submit": {
    "production": {}
  }
}
```

### Key fields

- `developmentClient: true` — bundles the Dev Launcher UI
- `distribution` — `"store"` (default) or `"internal"` (shareable link, TestFlight/Play Internal)
- `channel` — EAS Update channel to connect to
- `autoIncrement` — bumps `ios.buildNumber` and `android.versionCode` automatically
- `resourceClass` — compute power for the build (iOS only)
- `env` — environment variables injected into Metro

### Profile inheritance

```json
{
  "preview-ios-sim": {
    "extends": "preview",
    "ios": { "simulator": true }
  }
}
```

## Build Commands

```bash
# Interactive — prompts for platform
eas build

# Specific profile and platform
eas build --profile production --platform ios
eas build --profile production --platform android
eas build --profile production --platform all

# Local build (runs on your machine, uses EAS config)
eas build --platform ios --local

# Skip uploading the project tarball (faster re-runs)
eas build --profile development --clear-cache

# Don't wait for completion (background build)
eas build --profile production --platform all --non-interactive --no-wait

# Cancel a running build
eas build:cancel
```

### Monitoring

```bash
# List recent builds
eas build:list

# View specific build
eas build:view <build-id>

# Download artifact
eas build:download --platform ios --profile production
```

The EAS dashboard (https://expo.dev/accounts/<account>/projects/<project>/builds) shows full logs, metrics, and download links.

## Credentials Management

### iOS

You need:

- Apple Developer account ($99/year)
- Distribution certificate
- Provisioning profile (+ push notification cert if using notifications)

EAS can manage these automatically:

```bash
eas credentials
# → ios → <profile> → Set up credentials

# EAS will:
# 1. Log into App Store Connect
# 2. Generate a distribution cert
# 3. Generate a provisioning profile for your bundleID
# 4. Store them encrypted in EAS
```

For internal distribution, register testers' UDIDs:

```bash
eas device:create
# Tester opens the URL, installs the profile, registers their device
```

### Android

EAS auto-generates a keystore on first build — that's enough for most apps.

To use an existing keystore:

```bash
eas credentials
# → android → <profile> → Upload keystore
```

⚠️ **Back up your keystore**. If you lose it, you can't publish updates to an existing Play Store listing. Download it:

```bash
eas credentials
# → android → Download keystore
```

## Build Environments & Secrets

Three logical environments: `development`, `preview`, `production`.

```bash
# Create an env var (interactive)
eas env:create

# List vars for an environment
eas env:list --environment production

# Pull all vars into .env.local
eas env:pull --environment development

# Delete a var
eas env:delete
```

Secrets are encrypted at rest and injected into the build container. Variables prefixed with `EXPO_PUBLIC_` are also exposed to the JS bundle.

**Per-platform vars**:

```bash
eas env:create --platform android --environment production
```

## Resource Classes

Control compute power for iOS builds (affects queue time and cost):

| Class | Cores | RAM | Notes |
|-------|-------|-----|-------|
| `default` | 3 | 6GB | Shared, slower |
| `m-medium` | 4 | 8GB | Default for paid plans |
| `m-large` | 8 | 16GB | Fastest, production only |
| `m1-medium` | 4 | 8GB | Apple Silicon |
| `m1-large` | 8 | 16GB | Apple Silicon, largest |

Android builds use a single shared class; no resource class needed.

## Monorepos

If your app is inside a monorepo (e.g. `apps/mobile/`), configure `eas.json`:

```json
{
  "build": {
    "production": {
      "cache": {
        "paths": ["../../node_modules"]
      },
      "ios": { "resourceClass": "m-medium" }
    }
  },
  "cli": {
    "requireCommit": true
  }
}
```

And ensure `app.json` points to the monorepo root for workspaces:

```js
// metro.config.js (see 01-project-setup.md)
config.watchFolders = [workspaceRoot];
```

EAS auto-detects pnpm/yarn/npm workspaces.

## CI Integration

### GitHub Actions

```yaml
name: EAS Build
on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - uses: expo/expo-github-action@v8
        with:
          eas-version: latest
          token: ${{ secrets.EXPO_TOKEN }}
      - run: npm ci
      - run: eas build --profile production --platform all --non-interactive
```

Generate `EXPO_TOKEN`:

```bash
eas account:create-token
# Add to GitHub secrets as EXPO_TOKEN
```

### Pre-install / Post-install Hooks

```json
{
  "build": {
    "production": {
      "node": "20.11.1",
      "yarn": "1.22.22",
      "image": "latest",
      "prebuildCommand": "npm run build:prebuild",
      "env": {
        "NODE_ENV": "production"
      }
    }
  }
}
```

You can also hook via npm scripts:

```json
// package.json
{
  "scripts": {
    "eas-build-pre-install": "echo 'before install'",
    "eas-build-post-install": "echo 'after install'",
    "eas-build-on-success": "echo 'build succeeded'"
  }
}
```

## Troubleshooting

### Build fails with "No matching provisioning profile"

Regenerate credentials:

```bash
eas credentials
# Remove existing → let EAS recreate
```

### "Failed to resolve plugin" during prebuild

Your `plugins` array in `app.json` references a package that isn't installed. Run:

```bash
npx expo install --check
npm install <missing-plugin>
```

### Gradle "compileSdkVersion" errors

Add `expo-build-properties`:

```json
{
  "plugins": [
    ["expo-build-properties", {
      "android": { "compileSdkVersion": 34, "targetSdkVersion": 34 }
    }]
  ]
}
```

### Build artifact too large

- Enable R8/ProGuard (Android): automatic with `buildType: "app-bundle"`
- Enable Hermes (default): no action needed
- Remove unused assets from `assetBundlePatterns`

## Common Pitfalls

- **Hardcoded bundle identifiers**: if you use dynamic config for `bundleIdentifier` / `package`, each profile variant will generate different app IDs — make sure credentials exist for each.
- **Forgetting `autoIncrement`**: submitting a build with the same build number as a previous submission fails. Set `autoIncrement: true` or increment manually.
- **Running EAS Build from a dirty git state**: by default EAS uses your last committed state. Commit first, or use `--local` for a local build.
- **New Architecture + incompatible libs**: if a library doesn't support Fabric/TurboModules, your build fails with obscure errors. Check https://reactnative.directory.

## Related Topics

- OTA updates pair with builds → 07-eas-update.md
- App Store submission after build → 08-eas-submit.md
- Creating dev clients → 05-dev-clients.md
