# Tauri Distribution

> Source: https://v2.tauri.app/distribute/ | Version: 2.9.x

## Table of Contents

- [Building for Production](#building-for-production)
- [Platform-Specific Packaging](#platform-specific-packaging)
- [Code Signing](#code-signing)
- [Auto-Updater](#auto-updater)
- [CI/CD Builds](#cicd-builds)
- [Common Pitfalls](#common-pitfalls)

## Building for Production

```bash
# Build for the current platform with all default bundle formats
npm run tauri build

# Build specific targets
npm run tauri build -- --target universal-apple-darwin  # macOS universal
npm run tauri build -- --bundles deb                     # Linux .deb only
npm run tauri build -- --bundles nsis                    # Windows NSIS only

# Debug build (includes DevTools, unminified)
npm run tauri build -- --debug

# Output location
# src-tauri/target/release/bundle/
#   ├── deb/        (Linux)
#   ├── appimage/   (Linux)
#   ├── nsis/       (Windows)
#   ├── msi/        (Windows)
#   ├── dmg/        (macOS)
#   └── macos/      (macOS .app)
```

## Platform-Specific Packaging

### macOS

```bash
# Build .dmg and .app bundle
npm run tauri build

# Universal binary (Intel + Apple Silicon)
npm run tauri build -- --target universal-apple-darwin

# Requires both targets installed:
rustup target add x86_64-apple-darwin
rustup target add aarch64-apple-darwin
```

**Distribution options**:
- **Direct download**: Ship `.dmg` — requires code signing + notarization
- **Mac App Store**: Requires Apple Developer membership, sandboxing, App Review

### Windows

```bash
# NSIS installer (recommended) and MSI
npm run tauri build
```

**Installers**:
- **NSIS**: Modern installer with custom pages, auto-start, uninstaller
- **MSI**: Windows Installer package (enterprise deployment)

```json
// tauri.conf.json — NSIS customization
{
  "bundle": {
    "windows": {
      "nsis": {
        "oneClick": true,
        "perMachine": false,
        "installerIcon": "icons/icon.ico",
        "displayLanguageSelector": false
      }
    }
  }
}
```

### Linux

```bash
# Build all Linux formats
npm run tauri build

# Specific formats
npm run tauri build -- --bundles deb
npm run tauri build -- --bundles rpm
npm run tauri build -- --bundles appimage
```

```json
// tauri.conf.json — Linux packaging
{
  "bundle": {
    "linux": {
      "deb": {
        "depends": ["libwebkit2gtk-4.1-0", "libssl3"],
        "section": "utils",
        "priority": "optional"
      },
      "appimage": {
        "bundleMediaFramework": true
      },
      "rpm": {
        "depends": ["webkit2gtk4.1", "openssl"]
      }
    }
  }
}
```

## Code Signing

### macOS Code Signing & Notarization

```bash
# Environment variables for CI
export APPLE_CERTIFICATE="base64-encoded-p12"
export APPLE_CERTIFICATE_PASSWORD="password"
export APPLE_SIGNING_IDENTITY="Developer ID Application: Your Name (TEAMID)"
export APPLE_ID="your@email.com"
export APPLE_PASSWORD="app-specific-password"
export APPLE_TEAM_ID="TEAMID"
```

```json
// tauri.conf.json
{
  "bundle": {
    "macOS": {
      "signingIdentity": "Developer ID Application: Your Name (TEAMID)"
    }
  }
}
```

### Windows Code Signing

```json
{
  "bundle": {
    "windows": {
      "certificateThumbprint": "YOUR_THUMBPRINT",
      "digestAlgorithm": "sha256",
      "timestampUrl": "http://timestamp.digicert.com"
    }
  }
}
```

## Auto-Updater

The updater plugin provides automatic updates with signature verification.

### Setup

```bash
# Generate signing keys
npm run tauri signer generate -- -w ~/.tauri/myapp.key

# This outputs a public key — add it to tauri.conf.json
# And sets TAURI_SIGNING_PRIVATE_KEY for builds
```

```bash
# Install the plugin
npm run tauri add updater
```

```json
// tauri.conf.json
{
  "bundle": {
    "createUpdaterArtifacts": "v2Compatible"
  },
  "plugins": {
    "updater": {
      "pubkey": "YOUR_PUBLIC_KEY_HERE",
      "endpoints": [
        "https://releases.example.com/{{target}}/{{arch}}/{{current_version}}"
      ]
    }
  }
}
```

### Rust Registration

```rust
fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_updater::Builder::new().build())
        .setup(|app| {
            let handle = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                update(handle).await;
            });
            Ok(())
        })
        .run(tauri::generate_context!())
        .unwrap();
}

async fn update(app: tauri::AppHandle) {
    if let Some(update) = app
        .updater_builder()
        .build()
        .unwrap()
        .check()
        .await
        .unwrap()
    {
        // Download and install
        update.download_and_install(|_, _| {}, || {}).await.unwrap();
        // Restart the app
        app.restart();
    }
}
```

### Frontend Update Check

```typescript
import { check } from "@tauri-apps/plugin-updater";
import { relaunch } from "@tauri-apps/plugin-process";

async function checkForUpdates() {
  const update = await check();
  if (update) {
    console.log(`Update available: ${update.version}`);

    // Download and install
    await update.downloadAndInstall((event) => {
      switch (event.event) {
        case "Started":
          console.log(`Downloading ${event.data.contentLength} bytes`);
          break;
        case "Progress":
          console.log(`Downloaded ${event.data.chunkLength} bytes`);
          break;
        case "Finished":
          console.log("Download complete");
          break;
      }
    });

    // Restart to apply
    await relaunch();
  }
}
```

### Update Server Endpoint

Your server must return JSON in this format:

```json
{
  "version": "1.1.0",
  "notes": "Bug fixes and improvements",
  "pub_date": "2026-05-27T00:00:00Z",
  "platforms": {
    "darwin-aarch64": {
      "signature": "SIGNATURE_CONTENT",
      "url": "https://releases.example.com/myapp-1.1.0-aarch64.app.tar.gz"
    },
    "darwin-x86_64": {
      "signature": "SIGNATURE_CONTENT",
      "url": "https://releases.example.com/myapp-1.1.0-x86_64.app.tar.gz"
    },
    "linux-x86_64": {
      "signature": "SIGNATURE_CONTENT",
      "url": "https://releases.example.com/myapp-1.1.0-x86_64.AppImage.tar.gz"
    },
    "windows-x86_64": {
      "signature": "SIGNATURE_CONTENT",
      "url": "https://releases.example.com/myapp-1.1.0-x64-setup.nsis.zip"
    }
  }
}
```

### GitHub Releases as Update Server

Use GitHub releases with the `tauri-action` GitHub Action:

```yaml
# .github/workflows/release.yml
name: Release
on:
  push:
    tags: ["v*"]

jobs:
  release:
    strategy:
      matrix:
        include:
          - platform: macos-latest
            args: "--target universal-apple-darwin"
          - platform: ubuntu-22.04
            args: ""
          - platform: windows-latest
            args: ""
    runs-on: ${{ matrix.platform }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - uses: dtolnay/rust-toolchain@stable
      - uses: tauri-apps/tauri-action@v0
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          TAURI_SIGNING_PRIVATE_KEY: ${{ secrets.TAURI_SIGNING_PRIVATE_KEY }}
        with:
          tagName: v__VERSION__
          releaseName: "v__VERSION__"
          args: ${{ matrix.args }}
```

Update endpoint for GitHub releases:

```json
{
  "plugins": {
    "updater": {
      "endpoints": [
        "https://github.com/OWNER/REPO/releases/latest/download/latest.json"
      ]
    }
  }
}
```

## CI/CD Builds

### GitHub Actions Matrix

```yaml
jobs:
  build:
    strategy:
      fail-fast: false
      matrix:
        include:
          - platform: macos-latest
            args: "--target aarch64-apple-darwin"
          - platform: macos-latest
            args: "--target x86_64-apple-darwin"
          - platform: ubuntu-22.04
            args: ""
          - platform: windows-latest
            args: ""
    runs-on: ${{ matrix.platform }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: lts/*
      - uses: dtolnay/rust-toolchain@stable
        with:
          targets: ${{ matrix.platform == 'macos-latest' && 'aarch64-apple-darwin,x86_64-apple-darwin' || '' }}
      - name: Install Linux deps
        if: matrix.platform == 'ubuntu-22.04'
        run: |
          sudo apt-get update
          sudo apt-get install -y libwebkit2gtk-4.1-dev build-essential curl wget file libxdo-dev libssl-dev libayatana-appindicator3-dev librsvg2-dev
      - run: npm install
      - uses: tauri-apps/tauri-action@v0
        with:
          args: ${{ matrix.args }}
```

## Common Pitfalls

- **Cross-compilation is limited**: You generally must build on each target OS (no building macOS apps on Linux)
- **Missing signing keys**: Update artifacts require `TAURI_SIGNING_PRIVATE_KEY` — without it, the updater won't work
- **Update endpoint format**: The JSON format is strict — incorrect structure silently fails
- **macOS notarization**: Required for distribution outside the App Store since macOS 10.15
- **Linux dependencies**: Different distros need different WebKit packages — test on multiple distributions
- **Windows WebView2**: Pre-installed on Win 10+, but older systems may need the bootstrapper bundled
