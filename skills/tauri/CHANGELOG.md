# Changelog

## [1.0.0] — 2026-05-27

Source version tracked: Tauri 2.9.x

### Added

- **00-overview.md** — What Tauri is, installation, project structure, dev workflow, Electron comparison, CLI reference
- **01-architecture.md** — Process model, Core/WebView processes, IPC transport, trust boundaries, isolation pattern, app lifecycle
- **02-commands.md** — #[tauri::command] macro, parameters, return types, error handling, async commands, state access, type-safe bindings
- **03-events.md** — Event system, emit/listen from Rust and frontend, window-specific events, Channels for streaming
- **04-state-management.md** — Managed state, Mutex/RwLock patterns, AppHandle access, database pools, Store plugin, multi-window sync
- **05-security-model.md** — Permissions, capabilities, ACL system, scopes, CSP, remote URL access, platform-specific capabilities
- **06-plugins.md** — Official plugin catalog (20+ plugins), installation, usage in Rust/JS, developing custom plugins
- **07-window-management.md** — Multi-window config, runtime window creation, WebviewWindow API, system tray, menus
- **08-mobile-development.md** — iOS/Android prerequisites, project setup, dev workflow, Swift/Kotlin bindings, mobile plugins
- **09-configuration.md** — tauri.conf.json schema, build/app/bundle config, Cargo.toml features, env variables, platform overrides
- **10-distribution.md** — Building, platform-specific packaging, code signing, auto-updater, CI/CD with GitHub Actions
- **11-frontend-integration.md** — React/Vue/Svelte setup, @tauri-apps/api, dev server config, asset protocol, tauri-specta
- **12-debugging-testing.md** — DevTools, Rust debugging, logging plugin, environment diagnostics, testing patterns

### Stats

- Routing entries: 13
- Reference files: 13
- Total lines: ~5,100
