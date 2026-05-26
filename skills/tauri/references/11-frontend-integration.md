# Tauri Frontend Integration

> Source: https://v2.tauri.app/start/ | Version: 2.9.x

## Table of Contents

- [Frontend Framework Support](#frontend-framework-support)
- [React Setup](#react-setup)
- [Vue Setup](#vue-setup)
- [Svelte Setup](#svelte-setup)
- [The @tauri-apps/api Package](#the-tauri-appsapi-package)
- [Dev Server Configuration](#dev-server-configuration)
- [Asset Protocol](#asset-protocol)
- [Type-Safe Bindings](#type-safe-bindings)
- [Common Pitfalls](#common-pitfalls)

## Frontend Framework Support

Tauri works with any web framework. `create-tauri-app` supports:

| Framework | Bundler | Template |
|:----------|:--------|:---------|
| React | Vite | `react`, `react-ts` |
| Vue | Vite | `vue`, `vue-ts` |
| Svelte | Vite | `svelte`, `svelte-ts` |
| SvelteKit | SvelteKit | `sveltekit`, `sveltekit-ts` |
| Angular | Angular CLI | `angular` |
| Solid | Vite | `solid`, `solid-ts` |
| Next.js | Next.js | `next`, `next-ts` |
| Vanilla | Vite | `vanilla`, `vanilla-ts` |
| Leptos | Trunk | `leptos` (Rust WASM frontend) |

```bash
# Create with a specific template
npm create tauri-app@latest -- --template react-ts
pnpm create tauri-app --template vue-ts
```

## React Setup

### New Project

```bash
npm create tauri-app@latest my-app -- --template react-ts
cd my-app
npm install
npm run tauri dev
```

### Add Tauri to Existing React App

```bash
cd my-react-app
npm install -D @tauri-apps/cli@latest
npm run tauri init
# Set devUrl to http://localhost:5173 (Vite) or http://localhost:3000 (CRA)
# Set frontendDist to ../dist (Vite) or ../build (CRA)
```

### React + Tauri Pattern

```typescript
// src/hooks/useTauriCommand.ts
import { invoke } from "@tauri-apps/api/core";
import { useState, useCallback } from "react";

function useTauriCommand<TArgs, TResult>(command: string) {
  const [data, setData] = useState<TResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const execute = useCallback(async (args?: TArgs) => {
    setLoading(true);
    setError(null);
    try {
      const result = await invoke<TResult>(command, args ?? {});
      setData(result);
      return result;
    } catch (e) {
      setError(String(e));
      throw e;
    } finally {
      setLoading(false);
    }
  }, [command]);

  return { data, error, loading, execute };
}

// Usage
function UserList() {
  const { data: users, loading, execute } = useTauriCommand<void, User[]>("list_users");

  useEffect(() => { execute(); }, []);

  if (loading) return <p>Loading...</p>;
  return <ul>{users?.map(u => <li key={u.id}>{u.name}</li>)}</ul>;
}
```

### React Event Listener Hook

```typescript
import { useEffect } from "react";
import { listen, UnlistenFn } from "@tauri-apps/api/event";

function useTauriEvent<T>(event: string, handler: (payload: T) => void) {
  useEffect(() => {
    let unlisten: UnlistenFn;
    listen<T>(event, (e) => handler(e.payload)).then((fn) => {
      unlisten = fn;
    });
    return () => {
      unlisten?.();
    };
  }, [event, handler]);
}

// Usage
function StatusBar() {
  const [status, setStatus] = useState("idle");
  useTauriEvent<string>("backend-status", setStatus);
  return <span>{status}</span>;
}
```

## Vue Setup

```bash
npm create tauri-app@latest my-app -- --template vue-ts
```

```vue
<!-- src/App.vue -->
<script setup lang="ts">
import { ref } from "vue";
import { invoke } from "@tauri-apps/api/core";

const name = ref("");
const greeting = ref("");

async function greet() {
  greeting.value = await invoke<string>("greet", { name: name.value });
}
</script>

<template>
  <input v-model="name" placeholder="Enter a name" />
  <button @click="greet">Greet</button>
  <p>{{ greeting }}</p>
</template>
```

### Vue Composable

```typescript
// src/composables/useTauri.ts
import { ref, onMounted, onUnmounted } from "vue";
import { invoke } from "@tauri-apps/api/core";
import { listen, UnlistenFn } from "@tauri-apps/api/event";

export function useTauriEvent<T>(eventName: string) {
  const data = ref<T | null>(null);
  let unlisten: UnlistenFn;

  onMounted(async () => {
    unlisten = await listen<T>(eventName, (event) => {
      data.value = event.payload;
    });
  });

  onUnmounted(() => unlisten?.());

  return data;
}
```

## Svelte Setup

```bash
npm create tauri-app@latest my-app -- --template svelte-ts
```

```svelte
<!-- src/App.svelte -->
<script lang="ts">
  import { invoke } from "@tauri-apps/api/core";

  let name = "";
  let greeting = "";

  async function greet() {
    greeting = await invoke<string>("greet", { name });
  }
</script>

<input bind:value={name} placeholder="Enter a name" />
<button on:click={greet}>Greet</button>
<p>{greeting}</p>
```

## The @tauri-apps/api Package

```bash
npm install @tauri-apps/api
```

### Core Modules

```typescript
// Core — invoke commands, channels
import { invoke, Channel, convertFileSrc } from "@tauri-apps/api/core";

// Events — emit/listen
import { emit, listen, once, emitTo } from "@tauri-apps/api/event";

// Window — current window operations
import {
  getCurrentWebviewWindow,
  WebviewWindow,
} from "@tauri-apps/api/webviewWindow";

// Path — resolve platform paths
import { appDataDir, desktopDir, join } from "@tauri-apps/api/path";

// Menu — create menus programmatically
import { Menu, MenuItem, Submenu } from "@tauri-apps/api/menu";

// Tray — system tray
import { TrayIcon } from "@tauri-apps/api/tray";

// Image — create images for tray/menu
import { Image } from "@tauri-apps/api/image";
```

### Converting File Paths to URLs

Use `convertFileSrc` to display local files in the webview:

```typescript
import { convertFileSrc } from "@tauri-apps/api/core";

// Convert a filesystem path to a URL the webview can load
const assetUrl = convertFileSrc("/path/to/image.png");
// Returns: "asset://localhost/path/to/image.png" (or platform equivalent)

// Use in an img tag
<img src={assetUrl} alt="Local file" />
```

## Dev Server Configuration

### Vite (Recommended)

```typescript
// vite.config.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const host = process.env.TAURI_DEV_HOST;

export default defineConfig({
  plugins: [react()],
  clearScreen: false,
  server: {
    host: host || false,
    port: 1420,
    strictPort: true,
    hmr: host ? { protocol: "ws", host, port: 1421 } : undefined,
    watch: {
      ignored: ["**/src-tauri/**"],
    },
  },
});
```

### Next.js (Static Export)

```javascript
// next.config.js
const nextConfig = {
  output: "export",
  images: { unoptimized: true },
};
module.exports = nextConfig;
```

```json
// tauri.conf.json
{
  "build": {
    "devUrl": "http://localhost:3000",
    "frontendDist": "../out",
    "beforeDevCommand": "npm run dev",
    "beforeBuildCommand": "npm run build"
  }
}
```

## Asset Protocol

Load local files in the webview using the `asset://` protocol:

```json
// Cargo.toml — enable the feature
[dependencies]
tauri = { version = "2", features = ["protocol-asset"] }
```

```json
// capabilities/default.json — add permission
{
  "permissions": [
    "core:default",
    {
      "identifier": "core:asset:default",
      "allow": [
        { "path": "$APPDATA/**" },
        { "path": "$RESOURCE/**" }
      ]
    }
  ]
}
```

```typescript
import { convertFileSrc } from "@tauri-apps/api/core";
import { appDataDir, join } from "@tauri-apps/api/path";

const dataDir = await appDataDir();
const imagePath = await join(dataDir, "images", "photo.jpg");
const url = convertFileSrc(imagePath);
// <img src={url} />
```

## Type-Safe Bindings

### tauri-specta

Generate TypeScript types from Rust automatically:

```toml
# Cargo.toml
[dependencies]
tauri-specta = { version = "2", features = ["typescript"] }
specta = "2"
specta-typescript = "0.0.7"
```

```rust
use tauri_specta::{collect_commands, collect_events, Builder};

#[derive(serde::Serialize, specta::Type)]
struct User { id: u64, name: String }

#[tauri::command]
#[specta::specta]
fn list_users() -> Vec<User> {
    vec![User { id: 1, name: "Alice".into() }]
}

fn main() {
    let builder = Builder::<tauri::Wry>::new()
        .commands(collect_commands![list_users]);

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

## Common Pitfalls

- **Wrong API import path**: Use `@tauri-apps/api/core` (v2), not `@tauri-apps/api/tauri` (v1)
- **Missing `TAURI_DEV_HOST` for mobile**: The dev server must bind to the network for physical device testing
- **`src-tauri` in watch ignore**: Always exclude `src-tauri/` from Vite's file watcher to avoid rebuild loops
- **Next.js must use static export**: Tauri doesn't run a Node.js server — use `output: "export"`
- **`convertFileSrc` needs protocol-asset**: Enable the Cargo feature and grant permissions
- **HMR on mobile**: WebSocket-based HMR may need explicit host/port configuration for mobile dev
