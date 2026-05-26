# Tauri Debugging & Testing

> Source: https://v2.tauri.app/develop/debug/ | Version: 2.9.x

## Table of Contents

- [Debug Builds](#debug-builds)
- [WebView DevTools](#webview-devtools)
- [Rust Debugging](#rust-debugging)
- [Logging](#logging)
- [Environment Diagnostics](#environment-diagnostics)
- [Testing Patterns](#testing-patterns)
- [Common Issues](#common-issues)
- [Common Pitfalls](#common-pitfalls)

## Debug Builds

```bash
# Build a debug version (unoptimized, with DevTools and debug symbols)
npm run tauri build -- --debug

# Output at: src-tauri/target/debug/
# Bundle at: src-tauri/target/debug/bundle/
```

Debug builds include:
- WebView DevTools (inspector)
- Unminified Rust code with debug symbols
- Rust panic messages in the console
- Slower performance (no optimizations)

## WebView DevTools

### Opening DevTools

In development mode (`tauri dev`), DevTools are always available:

- **macOS**: `Cmd + Option + I` or right-click → "Inspect Element"
- **Windows**: `Ctrl + Shift + I` or right-click → "Inspect"
- **Linux**: `Ctrl + Shift + I` or right-click → "Inspect Element"

### Enabling DevTools in Production

```toml
# src-tauri/Cargo.toml
[features]
default = ["custom-protocol", "devtools"]
devtools = ["tauri/devtools"]
```

```rust
// Open programmatically
#[tauri::command]
fn open_devtools(window: tauri::WebviewWindow) {
    #[cfg(debug_assertions)]
    window.open_devtools();
}
```

### Platform-Specific Inspectors

| Platform | Engine | Inspector |
|:---------|:-------|:----------|
| macOS | WebKit | Safari Web Inspector |
| Windows | WebView2 (Edge) | Edge DevTools |
| Linux | WebKitGTK | WebKit Inspector |
| iOS | WKWebView | Safari Remote Inspector |
| Android | Android WebView | Chrome `chrome://inspect` |

### Remote Debugging (Mobile)

**iOS**: Connect device via USB → Safari → Develop → [Device Name] → [App]

**Android**: Connect device via USB → Chrome → `chrome://inspect` → Select WebView

## Rust Debugging

### Panic Messages

```rust
// Panics show in the terminal where `tauri dev` runs
#[tauri::command]
fn risky_operation() {
    panic!("Something went wrong!"); // Visible in terminal
}
```

### Backtraces

```bash
# Enable full backtraces
RUST_BACKTRACE=1 npm run tauri dev

# Full backtrace with all frames
RUST_BACKTRACE=full npm run tauri dev
```

### LLDB / GDB Debugging

```bash
# Build debug and attach a debugger
npm run tauri build -- --debug

# macOS — attach LLDB
lldb src-tauri/target/debug/my-app

# Linux — attach GDB
gdb src-tauri/target/debug/my-app

# VS Code — use the CodeLLDB extension for Rust debugging
# .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "lldb",
      "request": "launch",
      "name": "Debug Tauri",
      "program": "${workspaceFolder}/src-tauri/target/debug/my-app",
      "cwd": "${workspaceFolder}/src-tauri",
      "sourceLanguages": ["rust"]
    }
  ]
}
```

## Logging

### tauri-plugin-log

```bash
npm run tauri add log
```

```rust
use log::{info, warn, error, debug, trace};

fn main() {
    tauri::Builder::default()
        .plugin(
            tauri_plugin_log::Builder::new()
                .targets([
                    tauri_plugin_log::Target::new(
                        tauri_plugin_log::TargetKind::Stdout,
                    ),
                    tauri_plugin_log::Target::new(
                        tauri_plugin_log::TargetKind::LogDir {
                            file_name: Some("app".into()),
                        },
                    ),
                    tauri_plugin_log::Target::new(
                        tauri_plugin_log::TargetKind::Webview,
                    ),
                ])
                .level(log::LevelFilter::Info)
                .build(),
        )
        .run(tauri::generate_context!())
        .unwrap();
}

#[tauri::command]
fn process_data(data: String) {
    info!("Processing: {}", data);
    debug!("Data length: {}", data.len());

    if data.is_empty() {
        warn!("Empty data received");
    }
}
```

### Frontend Logging

```typescript
import { info, warn, error, debug, trace } from "@tauri-apps/plugin-log";

// Log from JavaScript — appears in Rust log output
await info("User clicked button");
await warn("Slow network detected");
await error("Failed to load config");
await debug("State updated: " + JSON.stringify(state));

// Attach the logger to the frontend (forwards console.log → Rust log)
import { attachConsole } from "@tauri-apps/plugin-log";
const detach = await attachConsole();
// Now console.log() and friends also appear in the Rust log targets
```

### Log File Location

Logs from `TargetKind::LogDir` are written to:
- **macOS**: `~/Library/Logs/{identifier}/`
- **Windows**: `%APPDATA%/{identifier}/logs/`
- **Linux**: `~/.config/{identifier}/logs/`

## Environment Diagnostics

```bash
# Show full environment info
npm run tauri info

# Output includes:
# - Tauri CLI version
# - Rust version and targets
# - Node.js version
# - Platform-specific deps (WebKit version, etc.)
# - Cargo dependencies
# - npm dependencies
```

Example output:

```
Operating System - macOS 14.2.0 (23C71)
Node.js - v20.10.0
Rust - 1.77.0
Cargo - 1.77.0

Tauri CLI - 2.1.0
@tauri-apps/api - 2.1.1
@tauri-apps/cli - 2.1.0
tauri (Cargo) - 2.1.1

App
  framework: React
  bundler: Vite

Webview
  macOS: WebKit 605.1.15
```

## Testing Patterns

### Unit Testing Rust Commands

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_greet() {
        let result = greet("World");
        assert_eq!(result, "Hello, World!");
    }

    #[test]
    fn test_calculation() {
        let result = calculate(10, 20);
        assert_eq!(result, 30);
    }
}
```

```bash
# Run Rust tests
cd src-tauri && cargo test
```

### Integration Testing with WebDriver

```bash
# Install tauri-driver (WebDriver server for Tauri)
cargo install tauri-driver
```

```typescript
// tests/e2e.test.ts (using WebdriverIO)
import { browser } from "@wdio/globals";

describe("App", () => {
  it("should greet the user", async () => {
    const input = await browser.$("input");
    await input.setValue("World");

    const button = await browser.$("button");
    await button.click();

    const greeting = await browser.$("p");
    await expect(greeting).toHaveText("Hello, World!");
  });
});
```

### Testing with Playwright (Webview)

```typescript
// For testing the frontend layer independently
import { test, expect } from "@playwright/test";

test("frontend renders correctly", async ({ page }) => {
  await page.goto("http://localhost:1420");
  await expect(page.locator("h1")).toBeVisible();
});
```

### Mocking Tauri API in Tests

```typescript
// __mocks__/@tauri-apps/api/core.ts
export const invoke = vi.fn().mockImplementation((cmd: string, args?: any) => {
  switch (cmd) {
    case "greet":
      return Promise.resolve(`Hello, ${args.name}!`);
    case "list_users":
      return Promise.resolve([{ id: 1, name: "Alice" }]);
    default:
      return Promise.reject(`Unknown command: ${cmd}`);
  }
});
```

```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    alias: {
      "@tauri-apps/api": "./__mocks__/@tauri-apps/api",
    },
  },
});
```

## Common Issues

### "Command Not Found" Error

```
// Cause: Command not in generate_handler!
// Fix:
.invoke_handler(tauri::generate_handler![
    my_command,  // ← Make sure it's listed here
])
```

### "Permission Denied" / Silent Failure

```
// Cause: Missing capability permission
// Fix: Add to capabilities/default.json
{
  "permissions": [
    "my-commands:allow-my-command"
  ]
}
```

### WebView Blank Screen

```
// Cause: Wrong frontendDist or devUrl
// Check tauri.conf.json:
{
  "build": {
    "devUrl": "http://localhost:1420",     // Must match your dev server
    "frontendDist": "../dist"              // Must point to build output
  }
}
```

### Cargo Build Fails

```bash
# Check environment
npm run tauri info

# Common Linux fix
sudo apt install libwebkit2gtk-4.1-dev build-essential libssl-dev

# Common macOS fix
xcode-select --install
```

## Common Pitfalls

- **DevTools not showing in production**: Enable the `devtools` Cargo feature — it's disabled by default
- **Console.log not visible**: Use `tauri-plugin-log` with `attachConsole()` to forward frontend logs
- **Wrong WebView for debugging**: macOS uses Safari inspector, Windows uses Edge, Linux uses WebKit — not Chrome DevTools
- **Debug builds are slow**: Rust debug builds are significantly slower — only use for debugging, not benchmarking
- **Missing Rust backtrace**: Set `RUST_BACKTRACE=1` before running — it's not enabled by default
- **Test isolation**: Mock `@tauri-apps/api` in frontend tests — real IPC won't work outside a Tauri runtime
