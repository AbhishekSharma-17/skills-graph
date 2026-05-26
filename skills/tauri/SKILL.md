---
name: tauri
description: "Build lightweight, secure desktop and mobile applications with web frontends and Rust backends using Tauri v2. MANDATORY TRIGGERS: Tauri, tauri, tauri v2, tauri::command, tauri.conf.json, @tauri-apps/api, tauri-apps, WebviewWindow, IPC bridge, Tauri plugins, Tauri permissions, Tauri capabilities. Also trigger when building cross-platform desktop apps with web technologies, creating Rust-backed desktop/mobile apps, migrating from Electron to Tauri, configuring Tauri security permissions, developing Tauri plugins, or shipping apps for Windows/macOS/Linux/iOS/Android from a single codebase. When in doubt about whether to use this skill for desktop app or Tauri tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["tauri", "desktop", "mobile", "rust", "cross-platform", "webview", "electron-alternative"]
---

# Tauri

> Cross-platform desktop & mobile apps with web frontends — v2.9.x | [Docs](https://v2.tauri.app/) | [GitHub](https://github.com/tauri-apps/tauri) | [Plugins](https://github.com/tauri-apps/plugins-workspace)

## Reference Files

| File | Read When |
|:-----|:----------|
| `references/00-overview.md` | Starting with Tauri, installation, project structure, dev workflow, Electron comparison |
| `references/01-architecture.md` | Understanding process model, webview, Rust core, IPC bridge, trust boundaries |
| `references/02-commands.md` | Defining #[tauri::command] handlers, async commands, return types, error handling |
| `references/03-events.md` | Fire-and-forget event system, emit/listen, frontend-backend messaging, channels |
| `references/04-state-management.md` | Managed state, AppHandle, cross-command sharing, Store plugin, multi-window sync |
| `references/05-security-model.md` | Permissions, capabilities, ACL system, CSP, scopes, remote URL access |
| `references/06-plugins.md` | Official plugins catalog, installing plugins, developing custom plugins |
| `references/07-window-management.md` | Multi-window, WebviewWindow API, system tray, menus, window configuration |
| `references/08-mobile-development.md` | iOS/Android targets, Swift/Kotlin bindings, prerequisites, mobile dev workflow |
| `references/09-configuration.md` | tauri.conf.json schema, Cargo.toml, build config, environment variables |
| `references/10-distribution.md` | Building, bundling, code signing, auto-updater, platform-specific packaging |
| `references/11-frontend-integration.md` | React/Vue/Svelte setup, @tauri-apps/api, dev server, type-safe bindings |
| `references/12-debugging-testing.md` | DevTools, debug builds, logging, Rust backtraces, testing patterns |

## Quick Start

```bash
# Prerequisites: Rust, Node.js, platform-specific deps
# Create a new Tauri project
npm create tauri-app@latest

# Dev mode (hot-reload frontend + Rust backend)
npm run tauri dev

# Build for production
npm run tauri build
```

## Quick Reference

- [Getting Started](https://v2.tauri.app/start/) — Prerequisites and project setup
- [API Reference](https://v2.tauri.app/reference/) — JavaScript and Rust API docs
- [Plugins](https://v2.tauri.app/plugin/) — Official plugin catalog
