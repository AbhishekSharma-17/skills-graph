# Tauri Mobile Development

> Source: https://v2.tauri.app/develop/ | Version: 2.9.x

## Table of Contents

- [Mobile Support Overview](#mobile-support-overview)
- [Prerequisites](#prerequisites)
- [Project Setup](#project-setup)
- [Development Workflow](#development-workflow)
- [Platform-Specific Code](#platform-specific-code)
- [Mobile Plugins](#mobile-plugins)
- [Configuration](#configuration)
- [Building for Production](#building-for-production)
- [Common Pitfalls](#common-pitfalls)

## Mobile Support Overview

Tauri v2 supports iOS and Android alongside desktop targets, all from the same codebase. Mobile apps use:

- **iOS**: WKWebView for the frontend, Rust core, Swift for platform-specific code
- **Android**: Android WebView for the frontend, Rust core, Kotlin for platform-specific code

The same `#[tauri::command]` handlers, events, and state work across all platforms. The main difference is the entry point and available APIs.

## Prerequisites

### iOS (macOS only)

```bash
# Install Xcode (full app, NOT just Command Line Tools)
# Download from Mac App Store or developer.apple.com

# Install Rust iOS targets
rustup target add aarch64-apple-ios            # Physical devices
rustup target add aarch64-apple-ios-sim        # ARM64 simulator
rustup target add x86_64-apple-ios             # x86 simulator

# Install CocoaPods (if using plugins with native iOS code)
sudo gem install cocoapods
# Or via Homebrew
brew install cocoapods
```

### Android

```bash
# Install Android Studio (includes SDK + emulator)
# Install JDK 17+
brew install openjdk@17

# Install Rust Android targets
rustup target add aarch64-linux-android        # ARM64 devices
rustup target add armv7-linux-androideabi      # ARM32 devices
rustup target add i686-linux-android           # x86 emulator
rustup target add x86_64-linux-android         # x86_64 emulator

# Set environment variables (add to ~/.zshrc or ~/.bashrc)
export JAVA_HOME="/opt/homebrew/opt/openjdk@17"
export ANDROID_HOME="$HOME/Library/Android/sdk"
export NDK_HOME="$ANDROID_HOME/ndk/$(ls -1 $ANDROID_HOME/ndk | sort -V | tail -1)"
export PATH="$PATH:$ANDROID_HOME/platform-tools"
```

In Android Studio SDK Manager, install:
- Android SDK Platform (latest API level)
- Android SDK Build-Tools
- NDK (Side by side)
- Android SDK Command-line Tools

## Project Setup

### Initialize Mobile Targets

```bash
# From your existing Tauri project
npm run tauri ios init      # Creates src-tauri/gen/apple/
npm run tauri android init  # Creates src-tauri/gen/android/
```

This generates platform-specific project files:

```
src-tauri/
├── gen/
│   ├── apple/              # Xcode project
│   │   ├── MyApp.xcodeproj
│   │   ├── MyApp/
│   │   │   ├── MyApp.swift     # iOS entry point
│   │   │   └── Info.plist
│   │   └── Podfile
│   └── android/            # Android Gradle project
│       ├── app/
│       │   ├── src/main/
│       │   │   ├── java/.../MainActivity.kt
│       │   │   └── AndroidManifest.xml
│       │   └── build.gradle.kts
│       ├── build.gradle.kts
│       └── settings.gradle.kts
```

### Shared Entry Point

```rust
// src-tauri/src/lib.rs — shared between desktop and mobile
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![greet])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

// src-tauri/src/main.rs — desktop entry point
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    my_app_lib::run()
}
```

## Development Workflow

### Running on Mobile

```bash
# iOS: Run on simulator (default) or device
npm run tauri ios dev
npm run tauri ios dev -- --device       # Physical device

# Android: Run on emulator or connected device
npm run tauri android dev
npm run tauri android dev -- --device   # Physical device

# Open in IDE for native debugging
npm run tauri ios dev -- --open         # Opens Xcode
npm run tauri android dev -- --open     # Opens Android Studio
```

### Dev Server Configuration

For physical devices, the dev server must be accessible over the network:

```json
// tauri.conf.json — the CLI sets TAURI_DEV_HOST automatically
{
  "build": {
    "devUrl": "http://localhost:1420",
    "frontendDist": "../dist"
  }
}
```

For Vite:

```typescript
// vite.config.ts
export default defineConfig({
  server: {
    host: process.env.TAURI_DEV_HOST || "localhost",
    port: 1420,
    strictPort: true,
  },
});
```

## Platform-Specific Code

### Rust Conditional Compilation

```rust
#[tauri::command]
fn platform_feature() -> String {
    #[cfg(target_os = "ios")]
    {
        "Running on iOS".to_string()
    }
    #[cfg(target_os = "android")]
    {
        "Running on Android".to_string()
    }
    #[cfg(desktop)]
    {
        "Running on desktop".to_string()
    }
}

// Desktop-only features
#[cfg(desktop)]
#[tauri::command]
fn desktop_only() -> String {
    "Only available on desktop".to_string()
}
```

### Frontend Platform Detection

```typescript
import { platform } from "@tauri-apps/plugin-os";

const currentPlatform = await platform();
// "linux", "macos", "windows", "ios", "android"

if (currentPlatform === "ios" || currentPlatform === "android") {
  // Mobile-specific UI
} else {
  // Desktop UI
}
```

### Swift (iOS-Specific)

```swift
// src-tauri/gen/apple/MyApp/MyAppApp.swift
import SwiftUI
import Tauri
import WebKit

@main
struct MyApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}

struct ContentView: View {
    var body: some View {
        TauriView()
            .ignoresSafeArea()
    }
}
```

### Kotlin (Android-Specific)

```kotlin
// src-tauri/gen/android/app/src/main/java/.../MainActivity.kt
package com.example.myapp

import android.os.Bundle

class MainActivity : TauriActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // Android-specific setup
    }
}
```

## Mobile Plugins

Plugins that work specifically on mobile:

```typescript
// Barcode Scanner (iOS + Android)
import { scan } from "@tauri-apps/plugin-barcode-scanner";
const result = await scan({ formats: ["QR_CODE", "EAN_13"] });

// Biometric Auth (iOS + Android)
import { authenticate } from "@tauri-apps/plugin-biometric";
const auth = await authenticate("Verify your identity");

// Haptics (iOS + Android)
import { vibrate, impactFeedback } from "@tauri-apps/plugin-haptics";
await vibrate({ duration: 100 });
await impactFeedback("medium");

// NFC (iOS + Android)
import { scan as nfcScan } from "@tauri-apps/plugin-nfc";
const tag = await nfcScan();

// Geolocation (all platforms)
import { getCurrentPosition } from "@tauri-apps/plugin-geolocation";
const pos = await getCurrentPosition();
```

## Configuration

### iOS-Specific Configuration

```json
// tauri.conf.json
{
  "bundle": {
    "iOS": {
      "minimumSystemVersion": "13.0",
      "frameworks": [],
      "developmentTeam": "YOUR_TEAM_ID"
    }
  }
}
```

### Android-Specific Configuration

```json
{
  "bundle": {
    "android": {
      "minSdkVersion": 24
    }
  }
}
```

## Building for Production

```bash
# iOS
npm run tauri ios build
npm run tauri ios build -- --export-method app-store-connect

# Android
npm run tauri android build
npm run tauri android build -- --apk       # APK instead of AAB
npm run tauri android build -- --split-per-abi  # Separate per architecture
```

### iOS Distribution

1. Set up an Apple Developer account
2. Configure signing in Xcode (Team ID + provisioning profiles)
3. Build and archive via Xcode or CLI
4. Upload to App Store Connect

### Android Distribution

1. Generate a signing keystore
2. Configure signing in `build.gradle.kts`
3. Build a signed AAB (Android App Bundle)
4. Upload to Google Play Console

## Common Pitfalls

- **iOS requires macOS + full Xcode**: Not just Command Line Tools — the full Xcode app is mandatory
- **TAURI_DEV_HOST for physical devices**: Physical device testing requires the dev server to bind to a network address
- **Separate capabilities for mobile**: Use platform-specific capability files with `"platforms": ["iOS", "android"]`
- **Re-init after adding plugins**: After adding plugins with native mobile code, re-run `tauri ios init` / `tauri android init`
- **Android NDK version**: Ensure the NDK version matches what Tauri expects — check `tauri info`
- **iOS simulator architecture**: Apple Silicon Macs need `aarch64-apple-ios-sim`, not `x86_64-apple-ios`
- **WebView differences**: iOS WKWebView and Android WebView have different JS engine behaviors — test on both
