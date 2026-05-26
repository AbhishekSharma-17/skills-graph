# Tauri Plugins

> Source: https://v2.tauri.app/plugin/ | Version: 2.9.x

## Table of Contents

- [Plugin System Overview](#plugin-system-overview)
- [Installing Official Plugins](#installing-official-plugins)
- [Official Plugin Catalog](#official-plugin-catalog)
- [Using Plugins in Frontend](#using-plugins-in-frontend)
- [Using Plugins in Rust](#using-plugins-in-rust)
- [Developing Custom Plugins](#developing-custom-plugins)
- [Plugin Permissions](#plugin-permissions)
- [Common Pitfalls](#common-pitfalls)

## Plugin System Overview

Tauri plugins extend app functionality with native capabilities. Each plugin consists of:

- A **Cargo crate** (`tauri-plugin-*`) with Rust code
- An optional **npm package** (`@tauri-apps/plugin-*`) with JavaScript bindings
- **Permission definitions** for the ACL system

Plugins can define commands, events, manage state, hook into the app lifecycle, and provide mobile-specific code via Swift/Kotlin.

## Installing Official Plugins

```bash
# Using the Tauri CLI (adds both Cargo + npm dependencies)
npm run tauri add fs
npm run tauri add dialog
npm run tauri add http

# Or manually:
# 1. Add Cargo dependency
cd src-tauri && cargo add tauri-plugin-fs

# 2. Add npm package
npm install @tauri-apps/plugin-fs

# 3. Register in Rust
# tauri::Builder::default().plugin(tauri_plugin_fs::init())
```

After installation, add permissions to your capabilities:

```json
// src-tauri/capabilities/default.json
{
  "permissions": [
    "fs:default",
    "fs:allow-read",
    "dialog:default"
  ]
}
```

## Official Plugin Catalog

### File System & Storage

| Plugin | Package | Description |
|:-------|:--------|:------------|
| **File System** | `tauri-plugin-fs` | Read, write, watch files and directories |
| **Store** | `tauri-plugin-store` | Persistent key-value storage (JSON on disk) |
| **Localhost** | `tauri-plugin-localhost` | Serve frontend from localhost in production |

### UI & System

| Plugin | Package | Description |
|:-------|:--------|:------------|
| **Dialog** | `tauri-plugin-dialog` | Native file open/save and message dialogs |
| **Notification** | `tauri-plugin-notification` | OS notification messages |
| **Global Shortcut** | `tauri-plugin-global-shortcut` | Register system-wide hotkeys |
| **Clipboard** | `tauri-plugin-clipboard-manager` | Read/write clipboard (text, images, files) |
| **Window State** | `tauri-plugin-window-state` | Persist and restore window size/position |

### Network & HTTP

| Plugin | Package | Description |
|:-------|:--------|:------------|
| **HTTP** | `tauri-plugin-http` | HTTP client via Rust (bypasses CORS) |
| **Upload** | `tauri-plugin-upload` | File uploads with progress tracking |
| **WebSocket** | `tauri-plugin-websocket` | WebSocket client via Rust |

### Device & Mobile

| Plugin | Package | Description |
|:-------|:--------|:------------|
| **Barcode Scanner** | `tauri-plugin-barcode-scanner` | Camera-based QR/barcode scanning (mobile) |
| **Biometric** | `tauri-plugin-biometric` | Fingerprint/face authentication (mobile) |
| **Geolocation** | `tauri-plugin-geolocation` | Device GPS coordinates |
| **Haptics** | `tauri-plugin-haptics` | Vibration feedback (mobile) |
| **NFC** | `tauri-plugin-nfc` | NFC tag read/write (mobile) |

### System Integration

| Plugin | Package | Description |
|:-------|:--------|:------------|
| **Opener** | `tauri-plugin-opener` | Open URLs/files with default app |
| **Auto-Start** | `tauri-plugin-autostart` | Launch app at system startup |
| **Deep Link** | `tauri-plugin-deep-link` | Handle custom URL schemes |
| **Process** | `tauri-plugin-process` | Get process info, restart, exit |
| **OS** | `tauri-plugin-os` | OS info (platform, arch, version) |
| **Logging** | `tauri-plugin-log` | Configurable structured logging |

### Distribution

| Plugin | Package | Description |
|:-------|:--------|:------------|
| **Updater** | `tauri-plugin-updater` | Auto-update with signature verification |
| **Single Instance** | `tauri-plugin-single-instance` | Prevent multiple app instances |

## Using Plugins in Frontend

```typescript
// File System
import { readTextFile, writeTextFile, exists } from "@tauri-apps/plugin-fs";
const content = await readTextFile("$APPDATA/config.json");
await writeTextFile("$APPDATA/config.json", JSON.stringify(data));

// Dialog
import { open, save, message, confirm } from "@tauri-apps/plugin-dialog";
const selected = await open({
  multiple: true,
  filters: [{ name: "Images", extensions: ["png", "jpg"] }],
});
const savePath = await save({
  defaultPath: "export.csv",
  filters: [{ name: "CSV", extensions: ["csv"] }],
});
const yes = await confirm("Delete this item?", { title: "Confirm" });

// HTTP (bypasses CORS)
import { fetch } from "@tauri-apps/plugin-http";
const response = await fetch("https://api.example.com/data", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ key: "value" }),
});

// Notification
import { sendNotification } from "@tauri-apps/plugin-notification";
sendNotification({ title: "Download Complete", body: "Your file is ready." });

// Clipboard
import { writeText, readText } from "@tauri-apps/plugin-clipboard-manager";
await writeText("Copied text");
const text = await readText();

// Global Shortcut
import { register } from "@tauri-apps/plugin-global-shortcut";
await register("CommandOrControl+Shift+P", () => {
  console.log("Shortcut triggered!");
});

// Opener
import { openUrl, openPath } from "@tauri-apps/plugin-opener";
await openUrl("https://example.com");
await openPath("/path/to/file.pdf");
```

## Using Plugins in Rust

```rust
use tauri::Manager;

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_http::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_store::Builder::new().build())
        .plugin(tauri_plugin_log::Builder::new().build())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_window_state::Builder::new().build())
        .plugin(tauri_plugin_autostart::init(
            tauri_plugin_autostart::MacosLauncher::LaunchAgent,
            None,
        ))
        .plugin(tauri_plugin_single_instance::init(|app, args, _cwd| {
            // Handle second instance attempt
            let window = app.get_webview_window("main").unwrap();
            window.set_focus().unwrap();
        }))
        .run(tauri::generate_context!())
        .unwrap();
}
```

## Developing Custom Plugins

### Scaffold a Plugin

```bash
# Creates a plugin skeleton with Rust + JS + permissions
npm run tauri plugin new my-plugin
```

### Plugin Structure

```
tauri-plugin-my-plugin/
├── Cargo.toml
├── package.json
├── src/
│   ├── lib.rs           # Plugin entry point
│   ├── commands.rs      # Command implementations
│   └── models.rs        # Shared types
├── guest-js/
│   └── index.ts         # Frontend API bindings
├── permissions/
│   ├── default.toml     # Default permission set
│   └── schemas/         # Auto-generated schemas
├── ios/                  # Swift code (mobile)
├── android/              # Kotlin code (mobile)
└── build.rs
```

### Minimal Plugin Implementation

```rust
// src/lib.rs
use tauri::{
    plugin::{Builder, TauriPlugin},
    Manager, Runtime,
};

mod commands;

pub fn init<R: Runtime>() -> TauriPlugin<R> {
    Builder::new("my-plugin")
        .invoke_handler(tauri::generate_handler![
            commands::do_something,
        ])
        .setup(|app, _api| {
            // Plugin initialization
            app.manage(MyPluginState::default());
            Ok(())
        })
        .build()
}

// src/commands.rs
#[tauri::command]
pub fn do_something(state: tauri::State<'_, MyPluginState>) -> String {
    "Plugin result".into()
}
```

```typescript
// guest-js/index.ts
import { invoke } from "@tauri-apps/api/core";

export async function doSomething(): Promise<string> {
  return invoke("plugin:my-plugin|do_something");
}
```

## Plugin Permissions

Define permissions for your custom plugin:

```toml
# permissions/default.toml
[default]
description = "Default permissions for my-plugin"
permissions = ["allow-do-something"]

[[permission]]
identifier = "allow-do-something"
description = "Allow the do_something command"

[permission.commands]
allow = ["do_something"]
```

## Common Pitfalls

- **Forgetting to register plugins**: `.plugin(tauri_plugin_*::init())` must be called in the builder
- **Missing npm package**: The Cargo crate handles Rust side but you need the npm package for JS bindings
- **Permission not granted**: Plugins need permissions in capabilities even after installation
- **Plugin order matters**: Some plugins depend on others — register dependencies first
- **Mobile plugins need init**: Mobile targets (`ios init`, `android init`) must be re-run after adding plugins with native mobile code
