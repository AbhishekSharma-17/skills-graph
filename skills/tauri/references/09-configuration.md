# Tauri Configuration

> Source: https://v2.tauri.app/develop/configuration-files/ | Version: 2.9.x

## Table of Contents

- [Configuration Files Overview](#configuration-files-overview)
- [tauri.conf.json Schema](#tauriconfjson-schema)
- [Build Configuration](#build-configuration)
- [App Configuration](#app-configuration)
- [Bundle Configuration](#bundle-configuration)
- [Cargo.toml Configuration](#cargotoml-configuration)
- [Environment Variables](#environment-variables)
- [Platform-Specific Overrides](#platform-specific-overrides)
- [Common Pitfalls](#common-pitfalls)

## Configuration Files Overview

```
src-tauri/
├── tauri.conf.json          # Primary config (required)
├── tauri.linux.conf.json    # Linux overrides (optional)
├── tauri.macos.conf.json    # macOS overrides (optional)
├── tauri.windows.conf.json  # Windows overrides (optional)
├── tauri.ios.conf.json      # iOS overrides (optional)
├── tauri.android.conf.json  # Android overrides (optional)
├── Cargo.toml               # Rust dependencies and features
├── capabilities/            # ACL capability files
│   └── default.json
└── build.rs                 # Build script
```

Tauri merges configs: base `tauri.conf.json` + platform-specific overrides (deep merge, platform wins).

## tauri.conf.json Schema

```json
{
  "$schema": "https://raw.githubusercontent.com/tauri-apps/tauri/dev/crates/tauri-cli/schema.json",
  "productName": "My App",
  "version": "1.0.0",
  "identifier": "com.mycompany.myapp",
  "build": { },
  "app": { },
  "bundle": { }
}
```

### Top-Level Fields

| Field | Type | Description |
|:------|:-----|:------------|
| `$schema` | string | JSON schema for IDE autocomplete |
| `productName` | string | Human-readable app name |
| `version` | string | App version (semver) |
| `identifier` | string | Reverse-domain identifier (e.g., `com.company.app`) |
| `build` | object | Build and dev server settings |
| `app` | object | App behavior, windows, security |
| `bundle` | object | Packaging and distribution settings |

## Build Configuration

```json
{
  "build": {
    "devUrl": "http://localhost:1420",
    "frontendDist": "../dist",
    "beforeDevCommand": "npm run dev",
    "beforeBuildCommand": "npm run build"
  }
}
```

| Field | Description |
|:------|:------------|
| `devUrl` | URL of the dev server for `tauri dev` |
| `frontendDist` | Path to built frontend files for `tauri build` |
| `beforeDevCommand` | Shell command to start the dev server |
| `beforeBuildCommand` | Shell command to build the frontend |

## App Configuration

```json
{
  "app": {
    "withGlobalTauri": false,
    "windows": [
      {
        "label": "main",
        "title": "My App",
        "width": 1024,
        "height": 768,
        "minWidth": 600,
        "minHeight": 400,
        "resizable": true,
        "center": true,
        "url": "index.html"
      }
    ],
    "security": {
      "csp": "default-src 'self'; script-src 'self'",
      "capabilities": [],
      "pattern": {
        "use": "brownfield"
      }
    },
    "enableGTKAppId": false
  }
}
```

### Key App Fields

| Field | Description |
|:------|:------------|
| `withGlobalTauri` | Expose `window.__TAURI__` (prefer ES imports) |
| `windows` | Array of window configurations |
| `security.csp` | Content Security Policy |
| `security.capabilities` | Inline capabilities (or use files in `capabilities/`) |
| `security.pattern` | `brownfield` (default) or `isolation` |

## Bundle Configuration

```json
{
  "bundle": {
    "active": true,
    "icon": [
      "icons/32x32.png",
      "icons/128x128.png",
      "icons/128x128@2x.png",
      "icons/icon.icns",
      "icons/icon.ico"
    ],
    "targets": "all",
    "category": "DeveloperTool",
    "shortDescription": "A great app",
    "longDescription": "A more detailed description of the app.",
    "copyright": "Copyright 2026",
    "licenseFile": "../LICENSE",
    "resources": [
      "assets/*"
    ],
    "externalBin": [],
    "windows": {
      "certificateThumbprint": null,
      "digestAlgorithm": "sha256",
      "timestampUrl": ""
    },
    "macOS": {
      "minimumSystemVersion": "10.15",
      "exceptionDomain": "",
      "entitlements": null,
      "signingIdentity": null,
      "providerShortName": null
    },
    "linux": {
      "deb": {
        "depends": ["libwebkit2gtk-4.1-0"]
      },
      "appimage": {
        "bundleMediaFramework": false
      }
    }
  }
}
```

### Bundle Targets

| Target | Platform | Format |
|:-------|:---------|:-------|
| `deb` | Linux | Debian package |
| `rpm` | Linux | RPM package |
| `appimage` | Linux | AppImage |
| `msi` | Windows | MSI installer |
| `nsis` | Windows | NSIS installer (recommended) |
| `dmg` | macOS | DMG disk image |
| `app` | macOS | .app bundle |

### Bundled Resources

Include non-code files in the app bundle:

```json
{
  "bundle": {
    "resources": [
      "assets/*",
      "config/defaults.json",
      "models/*.onnx"
    ]
  }
}
```

Access in Rust:

```rust
use tauri::Manager;

#[tauri::command]
fn read_resource(app: tauri::AppHandle) -> Result<String, String> {
    let resource_path = app
        .path()
        .resolve("assets/data.json", tauri::path::BaseDirectory::Resource)
        .map_err(|e| e.to_string())?;
    std::fs::read_to_string(resource_path).map_err(|e| e.to_string())
}
```

### External Binaries (Sidecars)

Bundle executables alongside your app:

```json
{
  "bundle": {
    "externalBin": [
      "binaries/ffmpeg"
    ]
  }
}
```

```rust
use tauri_plugin_shell::ShellExt;

#[tauri::command]
async fn run_ffmpeg(app: tauri::AppHandle) -> Result<String, String> {
    let output = app
        .shell()
        .sidecar("ffmpeg")
        .map_err(|e| e.to_string())?
        .args(["-version"])
        .output()
        .await
        .map_err(|e| e.to_string())?;
    Ok(String::from_utf8_lossy(&output.stdout).to_string())
}
```

## Cargo.toml Configuration

```toml
[package]
name = "my-app"
version = "1.0.0"
edition = "2021"

[lib]
name = "my_app_lib"
crate-type = ["staticlib", "cdylib", "rlib"]

[build-dependencies]
tauri-build = { version = "2", features = [] }

[dependencies]
tauri = { version = "2", features = [] }
tauri-plugin-opener = "2"
serde = { version = "1", features = ["derive"] }
serde_json = "1"

# Optional features to enable
[features]
default = ["custom-protocol"]
custom-protocol = ["tauri/custom-protocol"]
devtools = ["tauri/devtools"]
```

### Useful Tauri Cargo Features

| Feature | Description |
|:--------|:------------|
| `custom-protocol` | Use `tauri://` protocol for production assets |
| `devtools` | Enable DevTools in production builds |
| `protocol-asset` | Enable `asset://` protocol for local files |
| `isolation` | Enable the isolation pattern |
| `tray-icon` | Enable system tray support |

## Environment Variables

| Variable | Description |
|:---------|:------------|
| `TAURI_DEV_HOST` | Dev server host for mobile (set by CLI) |
| `TAURI_SIGNING_PRIVATE_KEY` | Private key for update signatures |
| `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` | Private key password |
| `TAURI_ENV_PLATFORM` | Target platform during build |
| `TAURI_ENV_ARCH` | Target architecture during build |
| `TAURI_ENV_FAMILY` | OS family (`unix` or `windows`) |
| `TAURI_ENV_TARGET_TRIPLE` | Full target triple |
| `TAURI_ENV_DEBUG` | `true` for debug builds |

Access in Rust at build time:

```rust
// build.rs
fn main() {
    let platform = std::env::var("TAURI_ENV_PLATFORM").unwrap_or_default();
    println!("Building for: {}", platform);
    tauri_build::build();
}
```

## Platform-Specific Overrides

Create platform-specific config files that merge with the base config:

```json
// tauri.macos.conf.json
{
  "bundle": {
    "macOS": {
      "minimumSystemVersion": "11.0"
    }
  }
}

// tauri.windows.conf.json
{
  "app": {
    "windows": [
      {
        "label": "main",
        "titleBarStyle": "Overlay"
      }
    ]
  }
}
```

## Common Pitfalls

- **Identifier format**: Must be a valid reverse-domain identifier — `com.company.app`, not `my-app`
- **Missing `beforeBuildCommand`**: Without this, `tauri build` packages the old/missing frontend build
- **Wrong `frontendDist` path**: Relative to `tauri.conf.json` — typically `"../dist"` not `"./dist"`
- **Icon sizes**: Generate icons with `tauri icon` — manual icons must include all required sizes
- **crate-type for mobile**: `lib.rs` needs `crate-type = ["staticlib", "cdylib", "rlib"]` for mobile targets
- **`custom-protocol` feature**: Required for production builds but often forgotten in features list
