# Tauri Events

> Source: https://v2.tauri.app/develop/calling-rust/#events | Version: 2.9.x

## Table of Contents

- [Event System Overview](#event-system-overview)
- [Emitting Events from Rust](#emitting-events-from-rust)
- [Listening for Events in Rust](#listening-for-events-in-rust)
- [Emitting Events from Frontend](#emitting-events-from-frontend)
- [Listening for Events in Frontend](#listening-for-events-in-frontend)
- [Window-Specific Events](#window-specific-events)
- [Channels for Streaming](#channels-for-streaming)
- [Events vs Commands](#events-vs-commands)
- [Common Pitfalls](#common-pitfalls)

## Event System Overview

Events are fire-and-forget, one-way IPC messages for broadcasting state changes and lifecycle notifications. Unlike commands, events:

- Can be emitted by both Core and Frontend
- Are always async
- Cannot return values
- Only support JSON-serializable payloads
- Can target specific windows or broadcast globally

## Emitting Events from Rust

### Global Events (All Windows)

```rust
use tauri::Emitter;

#[tauri::command]
fn start_processing(app: tauri::AppHandle) {
    std::thread::spawn(move || {
        for i in 0..=100 {
            app.emit("progress", i).unwrap();
            std::thread::sleep(std::time::Duration::from_millis(50));
        }
        app.emit("processing-complete", "done").unwrap();
    });
}
```

### Window-Specific Events

```rust
use tauri::Emitter;

#[tauri::command]
fn notify_window(app: tauri::AppHandle) {
    // Emit to a specific window only
    app.emit_to("main", "notification", "Hello main window!").unwrap();

    // Emit to the window that called this command
    // (use WebviewWindow parameter)
}

#[tauri::command]
fn notify_caller(window: tauri::WebviewWindow) {
    window.emit("caller-event", "Sent to calling window only").unwrap();
}
```

### Typed Event Payloads

```rust
use serde::Serialize;
use tauri::Emitter;

#[derive(Clone, Serialize)]
struct DownloadProgress {
    url: String,
    percent: f64,
    bytes_downloaded: u64,
    total_bytes: u64,
}

#[tauri::command]
async fn download_file(app: tauri::AppHandle, url: String) {
    // ... download logic ...
    app.emit("download-progress", DownloadProgress {
        url: url.clone(),
        percent: 50.0,
        bytes_downloaded: 5000,
        total_bytes: 10000,
    }).unwrap();
}
```

## Listening for Events in Rust

```rust
use tauri::Listener;

fn setup(app: &mut tauri::App) -> Result<(), Box<dyn std::error::Error>> {
    // Listen for events from the frontend
    app.listen("frontend-event", |event| {
        println!("Received: {:?}", event.payload());
    });

    // Listen on a specific window
    let window = app.get_webview_window("main").unwrap();
    window.listen("window-event", |event| {
        println!("Window event: {:?}", event.payload());
    });

    // Listen once (auto-removes after first trigger)
    app.once("init-complete", |event| {
        println!("Frontend initialized: {:?}", event.payload());
    });

    Ok(())
}
```

### Unlisten

```rust
let handler_id = app.listen("my-event", |event| {
    // handle event
});

// Remove the listener
app.unlisten(handler_id);
```

## Emitting Events from Frontend

```typescript
import { emit, emitTo } from "@tauri-apps/api/event";

// Emit global event (Core + all windows receive it)
await emit("frontend-event", { action: "clicked", item: "button-1" });

// Emit to a specific window
await emitTo("settings", "update-theme", { theme: "dark" });

// Emit to the current window only (use the window module)
import { getCurrentWebviewWindow } from "@tauri-apps/api/webviewWindow";
const currentWindow = getCurrentWebviewWindow();
await currentWindow.emit("local-event", { data: "only this window" });
```

## Listening for Events in Frontend

```typescript
import { listen, once } from "@tauri-apps/api/event";

// Listen for events (returns an unlisten function)
const unlisten = await listen<number>("progress", (event) => {
  console.log(`Progress: ${event.payload}%`);
  console.log(`Event ID: ${event.id}`);
  console.log(`Window label: ${event.windowLabel}`);
});

// Stop listening when done
unlisten();

// Listen only once
await once<string>("init-complete", (event) => {
  console.log("App initialized:", event.payload);
});

// Listen on a specific window
import { getCurrentWebviewWindow } from "@tauri-apps/api/webviewWindow";
const appWindow = getCurrentWebviewWindow();
const unlisten2 = await appWindow.listen("window-specific", (event) => {
  console.log(event.payload);
});
```

### React Pattern

```typescript
import { useEffect, useState } from "react";
import { listen } from "@tauri-apps/api/event";

function ProgressBar() {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const unlisten = listen<number>("progress", (event) => {
      setProgress(event.payload);
    });

    return () => {
      unlisten.then((fn) => fn());
    };
  }, []);

  return <div style={{ width: `${progress}%` }} />;
}
```

## Window-Specific Events

### Built-in Window Events

Tauri emits lifecycle events you can listen for:

```typescript
import { getCurrentWebviewWindow } from "@tauri-apps/api/webviewWindow";

const appWindow = getCurrentWebviewWindow();

// Window lifecycle events
appWindow.onCloseRequested(async (event) => {
  // Prevent close (e.g., for unsaved changes)
  const confirmed = await confirm("Are you sure?");
  if (!confirmed) {
    event.preventDefault();
  }
});

appWindow.onMoved(({ payload: position }) => {
  console.log(`Window moved to: ${position.x}, ${position.y}`);
});

appWindow.onResized(({ payload: size }) => {
  console.log(`Window resized: ${size.width}x${size.height}`);
});

appWindow.onFocusChanged(({ payload: focused }) => {
  console.log(`Window ${focused ? "focused" : "unfocused"}`);
});

appWindow.onScaleChanged(({ payload }) => {
  console.log(`Scale factor: ${payload.scaleFactor}`);
});

appWindow.onThemeChanged(({ payload: theme }) => {
  console.log(`Theme: ${theme}`);
});
```

## Channels for Streaming

Channels provide a more efficient mechanism for streaming data from Core to Frontend:

```rust
use tauri::ipc::Channel;

#[tauri::command]
fn stream_logs(channel: Channel<String>) {
    std::thread::spawn(move || {
        loop {
            let log_line = read_next_log();
            if channel.send(log_line).is_err() {
                break; // Frontend closed the channel
            }
        }
    });
}

// With typed payloads
use serde::Serialize;

#[derive(Clone, Serialize)]
struct LogEntry {
    level: String,
    message: String,
    timestamp: u64,
}

#[tauri::command]
fn stream_typed_logs(channel: Channel<LogEntry>) {
    std::thread::spawn(move || {
        channel.send(LogEntry {
            level: "info".into(),
            message: "App started".into(),
            timestamp: 1234567890,
        }).unwrap();
    });
}
```

```typescript
import { invoke, Channel } from "@tauri-apps/api/core";

const channel = new Channel<string>();
channel.onmessage = (message) => {
  console.log("Log:", message);
};

await invoke("stream_logs", { channel });
```

## Events vs Commands

| Feature | Commands | Events |
|:--------|:---------|:-------|
| Direction | Frontend → Core | Bidirectional |
| Response | Returns a value | Fire-and-forget |
| Type safety | Full (serde) | Payload is opaque JSON |
| Use case | Request/response | Broadcast notifications |
| Permissions | Required in capabilities | `core:event:default` |
| Performance | Slight overhead (response) | Lightweight |

**Use commands when**: You need a return value, type safety, or request/response semantics.

**Use events when**: Broadcasting state changes, lifecycle notifications, or decoupled communication between windows.

## Common Pitfalls

- **Memory leaks from unlistened events**: Always call the `unlisten` function in React `useEffect` cleanup
- **Events are not type-safe**: Payloads are JSON — use a shared TypeScript interface and validate
- **Missing `core:event:default` permission**: Event emit/listen requires the core event permission in capabilities
- **Payload must be serializable**: Event payloads must implement `serde::Serialize` (Rust) or be JSON-serializable (JS)
- **Events are async only**: You can't synchronously wait for an event response — use commands for that
