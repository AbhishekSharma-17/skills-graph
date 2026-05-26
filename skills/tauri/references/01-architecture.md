# Tauri Architecture

> Source: https://v2.tauri.app/concept/ | Version: 2.9.x

## Table of Contents

- [Process Model](#process-model)
- [The Core Process](#the-core-process)
- [The WebView Process](#the-webview-process)
- [Inter-Process Communication](#inter-process-communication)
- [IPC Transport](#ipc-transport)
- [Trust Boundaries](#trust-boundaries)
- [Brownfield vs Isolation Pattern](#brownfield-vs-isolation-pattern)
- [App Lifecycle](#app-lifecycle)

## Process Model

Tauri uses a multi-process architecture inspired by Chromium's model but with important differences. Every Tauri app has exactly **one Core process** (Rust) and **one or more WebView processes** (system webview rendering HTML/CSS/JS).

```
┌─────────────────────────────────────────────┐
│                 Tauri App                    │
│                                             │
│  ┌───────────────────────────────────────┐  │
│  │          Core Process (Rust)          │  │
│  │                                       │  │
│  │  ┌─────────┐  ┌──────────────────┐   │  │
│  │  │  State  │  │ Command Handlers │   │  │
│  │  └─────────┘  └──────────────────┘   │  │
│  │  ┌─────────┐  ┌──────────────────┐   │  │
│  │  │ Plugins │  │  Event Emitters  │   │  │
│  │  └─────────┘  └──────────────────┘   │  │
│  └───────────┬───────────────┬───────────┘  │
│              │  IPC Bridge   │               │
│  ┌───────────▼───────┐ ┌────▼────────────┐  │
│  │  WebView 1 (Main) │ │  WebView 2      │  │
│  │  HTML/CSS/JS       │ │  HTML/CSS/JS    │  │
│  └───────────────────┘ └─────────────────┘  │
└─────────────────────────────────────────────┘
```

## The Core Process

The Core process is the Rust application that serves as the backend. It:

- **Owns the application lifecycle**: Creates windows, manages the event loop, handles shutdown
- **Runs Rust code**: All `#[tauri::command]` handlers execute here with full system access
- **Manages state**: Application state lives in the Core and is accessed via `tauri::State<T>`
- **Handles IPC**: Receives and dispatches incoming IPC requests from WebViews
- **Runs plugins**: All plugin Rust code executes in the Core process

```rust
// The Core process entry point
fn main() {
    tauri::Builder::default()
        .manage(AppState::default())           // Register state
        .plugin(tauri_plugin_fs::init())        // Register plugins
        .invoke_handler(tauri::generate_handler![
            my_command,                         // Register commands
        ])
        .setup(|app| {
            // Runs once at startup — access app handle, create windows, etc.
            let window = app.get_webview_window("main").unwrap();
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error running app");
}
```

### The Manager Trait

Types that implement `tauri::Manager` provide access to application resources:

```rust
use tauri::Manager;

// Manager is implemented by: App, AppHandle, WebviewWindow, Webview, Window
fn example(app: &tauri::AppHandle) {
    let state = app.state::<MyState>();         // Access managed state
    let window = app.get_webview_window("main"); // Get a window by label
    app.emit("event-name", payload);             // Emit global event
    let path = app.path();                       // Access path resolver
}
```

## The WebView Process

Each window/webview is a separate process running the system's web engine. WebViews:

- **Render the UI**: HTML, CSS, JavaScript — any frontend framework
- **Are sandboxed**: No direct access to the filesystem, network, or OS APIs
- **Communicate via IPC**: Must use `invoke()` or events to talk to the Core
- **Are platform-specific**: WebKitGTK (Linux), WebKit (macOS/iOS), WebView2 (Windows), Android WebView

```typescript
// Frontend code runs in the WebView process
import { invoke } from "@tauri-apps/api/core";

// This IPC call crosses the process boundary to the Core
const result = await invoke<string>("my_command", { arg: "value" });
```

## Inter-Process Communication

Tauri provides two IPC mechanisms: **Commands** (request/response) and **Events** (fire-and-forget).

### Commands (Request/Response)

```
Frontend                    Core Process
   │                            │
   │──── invoke("greet") ──────>│
   │                            │── execute #[tauri::command]
   │<──── Ok("Hello!") ────────│
   │                            │
```

### Events (Fire-and-Forget)

```
Frontend                    Core Process
   │                            │
   │──── emit("clicked") ─────>│  (frontend → core)
   │                            │
   │<── emit("updated") ───────│  (core → frontend)
   │                            │
```

### Channels (Streaming)

Tauri v2 introduces Channels for streaming data from Core to Frontend:

```rust
#[tauri::command]
fn stream_data(channel: tauri::ipc::Channel<String>) {
    std::thread::spawn(move || {
        for i in 0..100 {
            channel.send(format!("Progress: {i}%")).unwrap();
            std::thread::sleep(std::time::Duration::from_millis(50));
        }
    });
}
```

```typescript
import { invoke, Channel } from "@tauri-apps/api/core";

const channel = new Channel<string>();
channel.onmessage = (msg) => console.log(msg);
await invoke("stream_data", { channel });
```

## IPC Transport

In Tauri v2, the IPC layer was rewritten for performance:

- **JSON payloads**: Default serialization for structured data (serde)
- **Raw payloads**: Binary data transfer without JSON overhead via `tauri::ipc::Response`
- **Request format**: Frontend sends `{ cmd, args, key }` to the Core
- **postMessage on WebKit**: Uses `window.webkit.messageHandlers` on macOS/iOS
- **Chrome DevTools Protocol**: Uses the WebView2 message channel on Windows

### Raw Binary Transfer

```rust
use tauri::ipc::Response;

#[tauri::command]
fn get_image() -> Response {
    let bytes = std::fs::read("image.png").unwrap();
    Response::new(bytes)
}
```

## Trust Boundaries

Tauri enforces a strict trust boundary between Core and WebView:

| Aspect | Core Process | WebView Process |
|:-------|:-------------|:----------------|
| Trust level | Fully trusted | Untrusted |
| System access | Full OS access | Sandboxed |
| File system | Direct access | Via IPC + permissions |
| Network | Direct access | Via IPC + permissions |
| Code origin | Your Rust code | Any web content |

**Key principle**: Never trust data from the WebView. Always validate and sanitize inputs in your command handlers.

```rust
#[tauri::command]
fn read_file(path: &str) -> Result<String, String> {
    // ALWAYS validate paths — the frontend could send "../../../etc/passwd"
    let safe_path = std::path::Path::new(path);
    if safe_path.components().any(|c| c == std::path::Component::ParentDir) {
        return Err("Path traversal not allowed".into());
    }
    std::fs::read_to_string(safe_path).map_err(|e| e.to_string())
}
```

## Brownfield vs Isolation Pattern

### Brownfield (Default)

The default mode where the frontend JavaScript context has direct access to the IPC layer. Commands are called via `window.__TAURI_INTERNALS__`.

### Isolation Pattern

An advanced security pattern that injects an isolation application between the IPC layer and your frontend. The isolation app runs in a sandboxed iframe and can intercept/validate all IPC messages before they reach the Core.

```json
// tauri.conf.json
{
  "app": {
    "security": {
      "pattern": {
        "use": "isolation",
        "options": {
          "dir": "../isolation-app"
        }
      }
    }
  }
}
```

## App Lifecycle

```
1. main() / run()
   └─ tauri::Builder::default()
      ├─ .manage()          → Register state
      ├─ .plugin()          → Initialize plugins
      ├─ .invoke_handler()  → Register commands
      ├─ .setup()           → One-time init (after webview created)
      └─ .run()             → Start event loop
         ├─ RunEvent::Ready          → App is fully initialized
         ├─ RunEvent::WindowEvent    → Window lifecycle events
         ├─ RunEvent::ExitRequested  → User/OS requests close
         └─ RunEvent::Exit           → Final cleanup
```

```rust
tauri::Builder::default()
    .build(tauri::generate_context!())
    .expect("error building app")
    .run(|app, event| match event {
        tauri::RunEvent::ExitRequested { api, .. } => {
            // Prevent the app from exiting (e.g., for system tray apps)
            api.prevent_exit();
        }
        tauri::RunEvent::Exit => {
            // Final cleanup before process terminates
        }
        _ => {}
    });
```

## Common Pitfalls

- **Assuming webview consistency**: The rendering engine differs per OS — CSS/JS behavior varies
- **Blocking the Core thread**: Long-running sync commands freeze the entire app — use async commands
- **Trusting frontend input**: Always validate data crossing the IPC bridge — the webview is untrusted
- **Ignoring multi-window isolation**: Each webview is a separate process — they don't share JS state
