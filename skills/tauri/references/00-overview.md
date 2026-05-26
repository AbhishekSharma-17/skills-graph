# Tauri Overview

> Source: https://v2.tauri.app/start/ | Version: 2.9.x

## What Is Tauri

Tauri is a framework for building tiny, fast, and secure desktop and mobile applications with web frontends and Rust backends. Apps use the system webview (WebKitGTK on Linux, WebKit/WKWebView on macOS/iOS, WebView2 on Windows, Android WebView on Android) instead of bundling Chromium, resulting in binaries as small as ~3 MB compared to Electron's ~96 MB.

### Key Characteristics

- **Tiny binaries**: ~3 MB vs ~96 MB for Electron
- **Low memory**: ~50% less RAM than Electron
- **Security-first**: Explicit permission model, no Node.js in the renderer
- **Cross-platform**: Windows, macOS, Linux, iOS, Android from one codebase
- **Any frontend**: React, Vue, Svelte, Angular, vanilla HTML/JS — anything that runs in a browser
- **Rust backend**: System-level performance and memory safety
- **Plugin ecosystem**: 20+ official plugins for common native features

## Installation & Prerequisites

### System Requirements

```bash
# Install Rust (required for all platforms)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Linux: Install system dependencies
# Ubuntu/Debian
sudo apt install libwebkit2gtk-4.1-dev build-essential curl wget file \
  libxdo-dev libssl-dev libayatana-appindicator3-dev librsvg2-dev

# Fedora
sudo dnf install webkit2gtk4.1-devel openssl-devel curl wget file \
  libappindicator-gtk3-devel librsvg2-devel

# macOS: Install Xcode Command Line Tools
xcode-select --install

# Windows: Install Visual Studio Build Tools + WebView2
# WebView2 is pre-installed on Windows 10 (1803+) and Windows 11
```

### Create a New Project

```bash
# Interactive project creation (choose frontend framework)
npm create tauri-app@latest

# Or with specific package managers
pnpm create tauri-app
yarn create tauri-app
bunx create-tauri-app

# Add Tauri to an existing frontend project
cd my-existing-app
npm install -D @tauri-apps/cli@latest
npm run tauri init
```

## Project Structure

```
my-tauri-app/
├── src/                      # Frontend source (React/Vue/Svelte/etc.)
│   ├── App.tsx
│   └── main.tsx
├── src-tauri/                # Rust backend
│   ├── Cargo.toml            # Rust dependencies
│   ├── build.rs              # Build script (generates handler glue)
│   ├── tauri.conf.json       # Tauri configuration
│   ├── capabilities/         # Security capabilities
│   │   └── default.json      # Default window permissions
│   ├── icons/                # App icons (all sizes)
│   ├── src/
│   │   ├── main.rs           # Entry point (or lib.rs for mobile)
│   │   └── lib.rs            # Shared logic for desktop + mobile
│   └── gen/                  # Auto-generated (mobile project files)
├── package.json
└── index.html
```

## Development Workflow

```bash
# Start dev mode (frontend hot-reload + Rust recompile on change)
npm run tauri dev

# Build for production
npm run tauri build

# Build debug version (with DevTools)
npm run tauri build -- --debug

# Generate app icons from a source image
npm run tauri icon ./app-icon.png

# Initialize mobile targets
npm run tauri ios init
npm run tauri android init

# Run on mobile
npm run tauri ios dev
npm run tauri android dev
```

## CLI Commands Reference

| Command | Description |
|:--------|:------------|
| `tauri dev` | Start development mode with hot reload |
| `tauri build` | Build production app with bundler |
| `tauri build --debug` | Build debug version with DevTools |
| `tauri init` | Initialize Tauri in existing project |
| `tauri icon <path>` | Generate icons from source image |
| `tauri ios init` | Initialize iOS target |
| `tauri ios dev` | Run on iOS simulator or device |
| `tauri ios build` | Build iOS app |
| `tauri android init` | Initialize Android target |
| `tauri android dev` | Run on Android emulator or device |
| `tauri android build` | Build Android app |
| `tauri info` | Show environment diagnostic info |
| `tauri signer generate` | Generate update signing keys |
| `tauri add <plugin>` | Add an official Tauri plugin |
| `tauri plugin new <name>` | Scaffold a custom plugin |

## Tauri vs Electron Comparison

| Feature | Tauri | Electron |
|:--------|:------|:---------|
| Binary size | ~3 MB | ~96 MB |
| RAM usage | ~30-80 MB | ~100-300 MB |
| Backend language | Rust | Node.js |
| Rendering engine | System webview | Bundled Chromium |
| Mobile support | Yes (iOS + Android) | No (use Capacitor) |
| Security model | Explicit permissions | Full Node.js access |
| Startup time | ~100-300ms | ~500ms-2s |
| Auto-updater | Built-in plugin | electron-updater |
| Cross-compilation | Limited (needs target OS) | electron-builder |

## Minimal Example

### Rust Backend (src-tauri/src/lib.rs)

```rust
use tauri::Manager;

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![greet])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

### Frontend (src/App.tsx)

```typescript
import { invoke } from "@tauri-apps/api/core";
import { useState } from "react";

function App() {
  const [greeting, setGreeting] = useState("");
  const [name, setName] = useState("");

  async function handleGreet() {
    const result = await invoke<string>("greet", { name });
    setGreeting(result);
  }

  return (
    <div>
      <input value={name} onChange={(e) => setName(e.target.value)} />
      <button onClick={handleGreet}>Greet</button>
      <p>{greeting}</p>
    </div>
  );
}
```

## Common Pitfalls

- **Forgetting `generate_handler!`**: Commands must be registered in `tauri::generate_handler![cmd1, cmd2]` or they silently don't exist
- **Missing capabilities**: Unlike v1, Tauri v2 requires explicit permission grants — commands fail silently without them
- **Wrong API import**: The v1 `@tauri-apps/api/tauri` module was renamed to `@tauri-apps/api/core` in v2
- **Cross-compilation limitations**: You generally need to build on each target OS (macOS for macOS/iOS, Windows for Windows, Linux for Linux)
- **WebView differences**: System webviews vary across platforms — test on all targets, not just your dev machine
