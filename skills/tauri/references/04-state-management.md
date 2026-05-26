# Tauri State Management

> Source: https://v2.tauri.app/develop/state-management/ | Version: 2.9.x

## Table of Contents

- [Managed State Basics](#managed-state-basics)
- [Thread-Safe State](#thread-safe-state)
- [Accessing State Outside Commands](#accessing-state-outside-commands)
- [Multiple State Types](#multiple-state-types)
- [Database Connection Pools](#database-connection-pools)
- [Store Plugin for Persistent State](#store-plugin-for-persistent-state)
- [Multi-Window State Sync](#multi-window-state-sync)
- [Common Pitfalls](#common-pitfalls)

## Managed State Basics

Tauri's state management system lets you register data at app startup and inject it into commands via dependency injection.

```rust
use std::sync::Mutex;

struct AppConfig {
    api_url: String,
    debug_mode: bool,
}

struct Counter {
    value: Mutex<i32>,
}

fn main() {
    tauri::Builder::default()
        .manage(AppConfig {
            api_url: "https://api.example.com".into(),
            debug_mode: cfg!(debug_assertions),
        })
        .manage(Counter {
            value: Mutex::new(0),
        })
        .invoke_handler(tauri::generate_handler![get_config, increment])
        .run(tauri::generate_context!())
        .unwrap();
}

#[tauri::command]
fn get_config(config: tauri::State<'_, AppConfig>) -> String {
    config.api_url.clone()
}

#[tauri::command]
fn increment(counter: tauri::State<'_, Counter>) -> i32 {
    let mut val = counter.value.lock().unwrap();
    *val += 1;
    *val
}
```

## Thread-Safe State

Since commands can run on multiple threads, mutable state must be wrapped in synchronization primitives.

### Mutex for Simple State

```rust
use std::sync::Mutex;

struct AppState {
    items: Mutex<Vec<String>>,
    count: Mutex<u32>,
}

#[tauri::command]
fn add_item(state: tauri::State<'_, AppState>, item: String) -> Vec<String> {
    let mut items = state.items.lock().unwrap();
    items.push(item);
    items.clone()
}
```

### RwLock for Read-Heavy State

```rust
use std::sync::RwLock;

struct Cache {
    data: RwLock<std::collections::HashMap<String, String>>,
}

#[tauri::command]
fn get_cached(state: tauri::State<'_, Cache>, key: String) -> Option<String> {
    let data = state.data.read().unwrap();
    data.get(&key).cloned()
}

#[tauri::command]
fn set_cached(state: tauri::State<'_, Cache>, key: String, value: String) {
    let mut data = state.data.write().unwrap();
    data.insert(key, value);
}
```

### Atomic Types for Simple Counters

```rust
use std::sync::atomic::{AtomicU64, Ordering};

struct Metrics {
    request_count: AtomicU64,
}

#[tauri::command]
fn track_request(metrics: tauri::State<'_, Metrics>) -> u64 {
    metrics.request_count.fetch_add(1, Ordering::Relaxed)
}
```

## Accessing State Outside Commands

Use the `Manager` trait's `state()` method on `AppHandle`, `App`, or `WebviewWindow`:

```rust
use tauri::Manager;

fn setup(app: &mut tauri::App) -> Result<(), Box<dyn std::error::Error>> {
    // Access state during setup
    let config = app.state::<AppConfig>();
    println!("API URL: {}", config.api_url);

    // Save AppHandle for later state access
    let handle = app.handle().clone();
    std::thread::spawn(move || {
        let state = handle.state::<Counter>();
        // Use state in a background thread
    });

    Ok(())
}

// In plugin code or event handlers
fn on_event(app: &tauri::AppHandle) {
    let state = app.state::<AppState>();
    // ...
}
```

## Multiple State Types

Register as many state types as you need — each is identified by its concrete type:

```rust
struct DatabasePool { /* ... */ }
struct UserSession { /* ... */ }
struct FeatureFlags { /* ... */ }

fn main() {
    tauri::Builder::default()
        .manage(DatabasePool::new())
        .manage(UserSession::default())
        .manage(FeatureFlags::load())
        .invoke_handler(tauri::generate_handler![handler])
        .run(tauri::generate_context!())
        .unwrap();
}

#[tauri::command]
fn handler(
    db: tauri::State<'_, DatabasePool>,
    session: tauri::State<'_, UserSession>,
    flags: tauri::State<'_, FeatureFlags>,
) -> String {
    // Access all three state types
    "ok".into()
}
```

## Database Connection Pools

A common pattern is managing a database connection pool as state:

```rust
use sqlx::SqlitePool;
use std::sync::Mutex;

struct Db {
    pool: SqlitePool,
}

#[tauri::command]
async fn query_users(app: tauri::AppHandle) -> Result<Vec<User>, String> {
    let db = app.state::<Db>();
    sqlx::query_as::<_, User>("SELECT * FROM users")
        .fetch_all(&db.pool)
        .await
        .map_err(|e| e.to_string())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            let data_dir = app.path().app_data_dir()?;
            std::fs::create_dir_all(&data_dir)?;
            let db_path = data_dir.join("app.db");

            let pool = tauri::async_runtime::block_on(async {
                SqlitePool::connect(&format!("sqlite:{}?mode=rwc", db_path.display()))
                    .await
                    .expect("Failed to connect to database")
            });

            app.manage(Db { pool });
            Ok(())
        })
        .run(tauri::generate_context!())
        .unwrap();
}
```

## Store Plugin for Persistent State

The `tauri-plugin-store` provides a key-value store persisted to disk — useful for settings and preferences:

```bash
# Install the plugin
cargo add tauri-plugin-store -F tauri-plugin-store/build
npm install @tauri-apps/plugin-store
```

```rust
// Register in Rust
fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_store::Builder::new().build())
        .run(tauri::generate_context!())
        .unwrap();
}
```

```typescript
import { Store } from "@tauri-apps/plugin-store";

// Create or open a store (persisted to disk as JSON)
const store = new Store("settings.json");

// Set values
await store.set("theme", "dark");
await store.set("fontSize", 14);
await store.set("recentFiles", ["/path/to/file.txt"]);

// Get values
const theme = await store.get<string>("theme");  // "dark"
const size = await store.get<number>("fontSize"); // 14

// Check existence
const has = await store.has("theme"); // true

// Delete
await store.delete("theme");

// Save (writes to disk)
await store.save();

// Listen for changes
await store.onKeyChange("theme", (value) => {
  console.log("Theme changed to:", value);
});

// React hook pattern
import { useEffect, useState } from "react";

function useStoreSetting<T>(store: Store, key: string, defaultValue: T) {
  const [value, setValue] = useState<T>(defaultValue);

  useEffect(() => {
    store.get<T>(key).then((v) => v !== null && setValue(v));
    const unlisten = store.onKeyChange<T>(key, (v) => {
      if (v !== null) setValue(v);
    });
    return () => { unlisten.then((fn) => fn()); };
  }, [key]);

  const update = async (newValue: T) => {
    await store.set(key, newValue);
    await store.save();
  };

  return [value, update] as const;
}
```

## Multi-Window State Sync

Webviews are isolated processes — they don't share JavaScript memory. To synchronize state:

### Pattern 1: Rust-Managed State + Events

```rust
use tauri::Emitter;

#[tauri::command]
fn update_setting(
    app: tauri::AppHandle,
    state: tauri::State<'_, Settings>,
    key: String,
    value: String,
) {
    state.set(&key, &value);
    // Broadcast change to all windows
    app.emit("setting-changed", (&key, &value)).unwrap();
}
```

```typescript
// In every window — listen for updates
listen("setting-changed", ([key, value]) => {
  localState[key] = value;
});
```

### Pattern 2: Store Plugin (Automatic Sync)

The Store plugin automatically syncs between windows when using `onKeyChange`.

## Common Pitfalls

- **Deadlocks with nested Mutex locks**: Never lock the same Mutex twice in one call chain — restructure to avoid nesting
- **Poisoned Mutex**: If a thread panics while holding a lock, the Mutex is poisoned — use `.lock().unwrap_or_else(|e| e.into_inner())`
- **State not available in setup**: State registered with `.manage()` is available in `.setup()` only if `.manage()` is called before `.setup()`
- **`State<T>` in async commands**: Use `AppHandle` + `app.state::<T>()` instead of direct `State` injection in async commands
- **Forgetting `.manage()`**: If you use `State<MyType>` in a command but never call `.manage(MyType {...})`, the app panics at runtime
