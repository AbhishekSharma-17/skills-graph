# Tauri Window Management

> Source: https://v2.tauri.app/develop/ | Version: 2.9.x

## Table of Contents

- [Window Configuration](#window-configuration)
- [Creating Windows at Runtime](#creating-windows-at-runtime)
- [WebviewWindow API](#webviewwindow-api)
- [Multi-Window Patterns](#multi-window-patterns)
- [System Tray](#system-tray)
- [Menus](#menus)
- [Common Pitfalls](#common-pitfalls)

## Window Configuration

Define windows in `tauri.conf.json`:

```json
{
  "app": {
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
        "decorations": true,
        "transparent": false,
        "fullscreen": false,
        "alwaysOnTop": false,
        "visible": true,
        "url": "index.html"
      },
      {
        "label": "settings",
        "title": "Settings",
        "width": 500,
        "height": 400,
        "resizable": false,
        "visible": false,
        "url": "settings.html"
      }
    ]
  }
}
```

### Window Properties

| Property | Type | Description |
|:---------|:-----|:------------|
| `label` | string | Unique identifier for the window |
| `title` | string | Window title bar text |
| `url` | string | URL or path to load |
| `width` / `height` | number | Initial dimensions |
| `minWidth` / `minHeight` | number | Minimum dimensions |
| `maxWidth` / `maxHeight` | number | Maximum dimensions |
| `x` / `y` | number | Initial position |
| `center` | bool | Center window on screen |
| `resizable` | bool | Allow user resizing |
| `decorations` | bool | Show OS title bar/borders |
| `transparent` | bool | Transparent background |
| `fullscreen` | bool | Start fullscreen |
| `alwaysOnTop` | bool | Keep above other windows |
| `visible` | bool | Show on creation |
| `skipTaskbar` | bool | Hide from taskbar |
| `closable` | bool | Show close button |
| `minimizable` | bool | Show minimize button |
| `maximizable` | bool | Show maximize button |

## Creating Windows at Runtime

### From Rust

```rust
use tauri::{Manager, WebviewUrl, WebviewWindowBuilder};

#[tauri::command]
fn open_settings(app: tauri::AppHandle) {
    // Create a new window
    let _window = WebviewWindowBuilder::new(
        &app,
        "settings",
        WebviewUrl::App("settings.html".into()),
    )
    .title("Settings")
    .inner_size(500.0, 400.0)
    .resizable(false)
    .center()
    .build()
    .unwrap();
}

#[tauri::command]
fn open_about(app: tauri::AppHandle) {
    // Check if window already exists
    if let Some(window) = app.get_webview_window("about") {
        window.set_focus().unwrap();
        return;
    }

    WebviewWindowBuilder::new(
        &app,
        "about",
        WebviewUrl::App("about.html".into()),
    )
    .title("About")
    .inner_size(300.0, 200.0)
    .build()
    .unwrap();
}
```

### From Frontend

```typescript
import { WebviewWindow } from "@tauri-apps/api/webviewWindow";

const settingsWindow = new WebviewWindow("settings", {
  url: "settings.html",
  title: "Settings",
  width: 500,
  height: 400,
  resizable: false,
  center: true,
});

settingsWindow.once("tauri://created", () => {
  console.log("Settings window created");
});

settingsWindow.once("tauri://error", (e) => {
  console.error("Failed to create window:", e);
});
```

## WebviewWindow API

```typescript
import { getCurrentWebviewWindow } from "@tauri-apps/api/webviewWindow";

const appWindow = getCurrentWebviewWindow();

// Window operations
await appWindow.setTitle("New Title");
await appWindow.setSize(new LogicalSize(800, 600));
await appWindow.setPosition(new LogicalPosition(100, 100));
await appWindow.center();
await appWindow.setResizable(false);
await appWindow.setAlwaysOnTop(true);
await appWindow.setDecorations(false);
await appWindow.setFullscreen(true);
await appWindow.minimize();
await appWindow.maximize();
await appWindow.unmaximize();
await appWindow.toggleMaximize();
await appWindow.setFocus();
await appWindow.show();
await appWindow.hide();
await appWindow.close();

// Get window info
const title = await appWindow.title();
const isMaximized = await appWindow.isMaximized();
const isMinimized = await appWindow.isMinimized();
const isFullscreen = await appWindow.isFullscreen();
const isFocused = await appWindow.isFocused();
const isVisible = await appWindow.isVisible();
const scaleFactor = await appWindow.scaleFactor();
const size = await appWindow.innerSize();
const position = await appWindow.innerPosition();
const theme = await appWindow.theme();

// Window label
const label = appWindow.label; // "main"
```

### Rust WebviewWindow API

```rust
use tauri::Manager;

#[tauri::command]
fn manage_window(window: tauri::WebviewWindow) {
    window.set_title("Updated").unwrap();
    window.center().unwrap();
    window.set_always_on_top(true).unwrap();

    let size = window.inner_size().unwrap();
    let position = window.inner_position().unwrap();
    let label = window.label();

    // Close with confirmation
    window.close().unwrap();
}
```

## Multi-Window Patterns

### Communication Between Windows

```rust
use tauri::{Emitter, Manager};

#[tauri::command]
fn send_to_window(app: tauri::AppHandle, target: String, data: String) {
    if let Some(window) = app.get_webview_window(&target) {
        window.emit("cross-window-message", &data).unwrap();
    }
}
```

### Window Manager Pattern

```rust
use tauri::Manager;
use std::sync::Mutex;
use std::collections::HashMap;

struct WindowManager {
    windows: Mutex<HashMap<String, WindowConfig>>,
}

#[derive(Clone)]
struct WindowConfig {
    url: String,
    title: String,
    width: f64,
    height: f64,
}

#[tauri::command]
fn open_window(
    app: tauri::AppHandle,
    manager: tauri::State<'_, WindowManager>,
    name: String,
) -> Result<(), String> {
    if app.get_webview_window(&name).is_some() {
        app.get_webview_window(&name).unwrap().set_focus().unwrap();
        return Ok(());
    }

    let configs = manager.windows.lock().unwrap();
    let config = configs.get(&name).ok_or("Unknown window")?;

    tauri::WebviewWindowBuilder::new(
        &app,
        &name,
        tauri::WebviewUrl::App(config.url.clone().into()),
    )
    .title(&config.title)
    .inner_size(config.width, config.height)
    .build()
    .map_err(|e| e.to_string())?;

    Ok(())
}
```

## System Tray

```rust
use tauri::{
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    Manager,
};

fn setup_tray(app: &tauri::App) -> Result<(), Box<dyn std::error::Error>> {
    let show = MenuItem::with_id(app, "show", "Show Window", true, None::<&str>)?;
    let quit = MenuItem::with_id(app, "quit", "Quit", true, None::<&str>)?;
    let menu = Menu::with_items(app, &[&show, &quit])?;

    TrayIconBuilder::new()
        .icon(app.default_window_icon().unwrap().clone())
        .menu(&menu)
        .tooltip("My Tauri App")
        .on_menu_event(|app, event| match event.id.as_ref() {
            "show" => {
                if let Some(w) = app.get_webview_window("main") {
                    w.show().unwrap();
                    w.set_focus().unwrap();
                }
            }
            "quit" => app.exit(0),
            _ => {}
        })
        .on_tray_icon_event(|tray, event| {
            if let TrayIconEvent::Click {
                button: MouseButton::Left,
                button_state: MouseButtonState::Up,
                ..
            } = event
            {
                let app = tray.app_handle();
                if let Some(w) = app.get_webview_window("main") {
                    w.show().unwrap();
                    w.set_focus().unwrap();
                }
            }
        })
        .build(app)?;

    Ok(())
}
```

## Menus

### Application Menu

```rust
use tauri::menu::{Menu, MenuItem, Submenu};

fn setup_menu(app: &tauri::App) -> Result<(), Box<dyn std::error::Error>> {
    let file_menu = Submenu::with_items(
        app,
        "File",
        true,
        &[
            &MenuItem::with_id(app, "new", "New", true, Some("CmdOrCtrl+N"))?,
            &MenuItem::with_id(app, "open", "Open...", true, Some("CmdOrCtrl+O"))?,
            &MenuItem::with_id(app, "save", "Save", true, Some("CmdOrCtrl+S"))?,
        ],
    )?;

    let menu = Menu::with_items(app, &[&file_menu])?;
    app.set_menu(menu)?;

    app.on_menu_event(|app, event| {
        match event.id.as_ref() {
            "new" => { /* create new file */ }
            "open" => { /* open file dialog */ }
            "save" => { /* save file */ }
            _ => {}
        }
    });

    Ok(())
}
```

## Common Pitfalls

- **Duplicate window labels**: Creating a window with an existing label will error — check with `get_webview_window()` first
- **Window permissions**: Multi-window apps need separate capabilities per window for proper security
- **Hidden windows still consume resources**: Use `destroy()` instead of `hide()` for windows you don't need
- **Tray icon on macOS**: Requires the `NSUIElement` key in Info.plist for dock-less tray-only apps
- **Menu shortcuts conflict**: System shortcuts take precedence — avoid common OS shortcuts
