# Tauri Commands

> Source: https://v2.tauri.app/develop/calling-rust/ | Version: 2.9.x

## Table of Contents

- [Defining Commands](#defining-commands)
- [Command Parameters](#command-parameters)
- [Return Types](#return-types)
- [Error Handling](#error-handling)
- [Async Commands](#async-commands)
- [Accessing State in Commands](#accessing-state-in-commands)
- [Accessing Window and AppHandle](#accessing-window-and-apphandle)
- [Raw IPC Requests](#raw-ipc-requests)
- [Registering Commands](#registering-commands)
- [Calling Commands from Frontend](#calling-commands-from-frontend)
- [Type-Safe Bindings with tauri-specta](#type-safe-bindings-with-tauri-specta)
- [Common Pitfalls](#common-pitfalls)

## Defining Commands

Commands are Rust functions annotated with `#[tauri::command]` that the frontend can invoke via IPC.

```rust
#[tauri::command]
fn my_command() {
    println!("Command invoked!");
}

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {name}!")
}
```

## Command Parameters

All parameters must implement `serde::Deserialize`. Standard types (`String`, `u32`, `bool`, `Vec<T>`) work automatically.

```rust
use serde::Deserialize;

#[derive(Deserialize)]
struct CreateUserInput {
    name: String,
    email: String,
    age: Option<u32>,
}

#[tauri::command]
fn create_user(input: CreateUserInput) -> String {
    format!("Created user: {} ({})", input.name, input.email)
}
```

### Frontend Invocation

```typescript
import { invoke } from "@tauri-apps/api/core";

// Arguments are passed as a single object with snake_case keys
const result = await invoke<string>("create_user", {
  input: { name: "Alice", email: "alice@example.com", age: 30 },
});

// Rename parameters with #[tauri::command(rename_all = "camelCase")]
#[tauri::command(rename_all = "camelCase")]
fn get_user_data(userId: String) -> String { ... }
// Frontend: invoke("get_user_data", { userId: "123" })
```

## Return Types

Commands can return any type that implements `serde::Serialize`.

```rust
use serde::Serialize;

#[derive(Serialize)]
struct User {
    id: u64,
    name: String,
    active: bool,
}

#[tauri::command]
fn get_user(id: u64) -> User {
    User { id, name: "Alice".into(), active: true }
}

// Returning Vec, HashMap, etc.
#[tauri::command]
fn list_items() -> Vec<String> {
    vec!["item1".into(), "item2".into()]
}

// Returning nothing (void command)
#[tauri::command]
fn do_something() {
    // No return value — resolves to undefined in JS
}
```

## Error Handling

Commands that can fail should return `Result<T, E>` where `E` implements `Into<tauri::ipc::InvokeError>`.

### Simple String Errors

```rust
#[tauri::command]
fn read_config(path: String) -> Result<String, String> {
    std::fs::read_to_string(&path).map_err(|e| e.to_string())
}
```

### Custom Error Types

```rust
use serde::Serialize;

#[derive(Debug, Serialize)]
enum AppError {
    NotFound { id: String },
    PermissionDenied,
    Internal(String),
}

// Implement Display + Into<InvokeError> via thiserror or manually
impl std::fmt::Display for AppError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::NotFound { id } => write!(f, "Not found: {id}"),
            Self::PermissionDenied => write!(f, "Permission denied"),
            Self::Internal(msg) => write!(f, "Internal error: {msg}"),
        }
    }
}

impl From<AppError> for tauri::ipc::InvokeError {
    fn from(error: AppError) -> Self {
        // Serialize the error so the frontend gets structured data
        tauri::ipc::InvokeError::from_serde_json(
            serde_json::to_value(error).unwrap()
        )
    }
}

#[tauri::command]
fn get_item(id: String) -> Result<String, AppError> {
    if id == "secret" {
        return Err(AppError::PermissionDenied);
    }
    Ok(format!("Item: {id}"))
}
```

### Frontend Error Handling

```typescript
try {
  const item = await invoke<string>("get_item", { id: "123" });
} catch (error) {
  // error is the serialized AppError or a string
  console.error("Command failed:", error);
}
```

## Async Commands

Async commands run on a thread pool (`tauri::async_runtime::spawn`) and don't block the Core main thread.

```rust
#[tauri::command]
async fn fetch_data(url: String) -> Result<String, String> {
    let response = reqwest::get(&url)
        .await
        .map_err(|e| e.to_string())?;
    response.text().await.map_err(|e| e.to_string())
}

// Access state in async commands (must clone AppHandle)
#[tauri::command]
async fn save_data(
    app: tauri::AppHandle,
    data: String,
) -> Result<(), String> {
    let state = app.state::<MyState>();
    // Use state...
    Ok(())
}
```

**Important**: Async commands with `&State` references won't compile. Use `AppHandle` + `app.state()` instead.

## Accessing State in Commands

```rust
use std::sync::Mutex;

struct AppState {
    counter: Mutex<i32>,
    db: DatabasePool,
}

// Sync commands can take State<T> directly
#[tauri::command]
fn increment(state: tauri::State<'_, AppState>) -> i32 {
    let mut counter = state.counter.lock().unwrap();
    *counter += 1;
    *counter
}

// Async commands must use AppHandle
#[tauri::command]
async fn get_count(app: tauri::AppHandle) -> i32 {
    let state = app.state::<AppState>();
    *state.counter.lock().unwrap()
}
```

## Accessing Window and AppHandle

Commands can inject special Tauri types as parameters:

```rust
use tauri::{AppHandle, WebviewWindow};

#[tauri::command]
fn with_window(window: WebviewWindow) {
    println!("Called from window: {}", window.label());
    window.set_title("New Title").unwrap();
}

#[tauri::command]
fn with_app(app: AppHandle) {
    let data_dir = app.path().app_data_dir().unwrap();
    println!("App data dir: {:?}", data_dir);
}

// Both at once
#[tauri::command]
fn with_both(app: AppHandle, window: WebviewWindow) {
    // Access app-wide resources and the calling window
}
```

## Raw IPC Requests

For performance-critical binary transfer, use `tauri::ipc::Request` and `tauri::ipc::Response`:

```rust
use tauri::ipc::{Request, Response};

#[tauri::command]
fn upload_binary(request: Request<'_>) -> Result<(), String> {
    let data = request.body().to_vec();
    std::fs::write("uploaded.bin", &data).map_err(|e| e.to_string())
}

#[tauri::command]
fn download_binary() -> Response {
    let bytes = std::fs::read("file.bin").unwrap();
    Response::new(bytes)
}
```

## Registering Commands

Commands must be registered with `generate_handler!` in the builder:

```rust
fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            greet,
            create_user,
            get_item,
            fetch_data,
            increment,
        ])
        .run(tauri::generate_context!())
        .expect("error running app");
}
```

**Critical**: If you forget to add a command to `generate_handler!`, the frontend `invoke()` call will fail with a cryptic "command not found" error.

## Calling Commands from Frontend

```typescript
import { invoke } from "@tauri-apps/api/core";

// Basic invocation
const greeting = await invoke<string>("greet", { name: "World" });

// With complex arguments
const user = await invoke<User>("get_user", { id: 42 });

// Void commands
await invoke("do_something");

// Error handling
try {
  await invoke("risky_operation");
} catch (e) {
  console.error(e);
}
```

## Type-Safe Bindings with tauri-specta

Generate TypeScript bindings from Rust types automatically:

```rust
// Cargo.toml: tauri-specta = { version = "2", features = ["typescript"] }
use tauri_specta::{collect_commands, Builder};

#[tauri::command]
#[specta::specta]
fn greet(name: String) -> String {
    format!("Hello, {name}!")
}

fn main() {
    let builder = Builder::<tauri::Wry>::new()
        .commands(collect_commands![greet]);

    #[cfg(debug_assertions)]
    builder.export(
        specta_typescript::Typescript::default(),
        "../src/bindings.ts",
    ).unwrap();

    tauri::Builder::default()
        .invoke_handler(builder.invoke_handler())
        .run(tauri::generate_context!())
        .unwrap();
}
```

```typescript
// Auto-generated bindings with full type safety
import { commands } from "./bindings";
const result: string = await commands.greet("World");
```

## Common Pitfalls

- **Missing `generate_handler!` entry**: The #1 mistake — commands silently fail if not registered
- **`&State` in async commands**: Use `AppHandle` + `app.state()` instead — references can't cross await points
- **Argument name mismatch**: Frontend `invoke()` args must match Rust parameter names (snake_case by default)
- **Forgetting `Serialize`/`Deserialize`**: Return types need `Serialize`, parameters need `Deserialize`
- **Blocking in sync commands**: Long operations in sync commands freeze the main thread — use async
- **Missing capability permissions**: Even registered commands need permissions granted in `capabilities/`
