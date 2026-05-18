# Changelog

## [1.0.0] — 2026-05-19

Source version tracked: Bun 1.3.x

### Added

- **00-overview.md** — What Bun is, installation methods, CLI commands, Node.js compatibility, performance benchmarks
- **01-runtime-fundamentals.md** — Module resolution, TypeScript/JSX transpilation, environment variables, globals, watch mode, plugins
- **02-http-server.md** — Bun.serve() API, routing, request/response handling, TLS, static file serving, streaming
- **03-websockets.md** — Server-side WebSockets, pub/sub topics, compression, backpressure, scalable messaging
- **04-package-manager.md** — bun install/add/remove, workspaces, lockfile format, registries, overrides, patching
- **05-bundler.md** — Bun.build() API, entrypoints, targets, code splitting, plugins, minification, loaders, sourcemaps
- **06-test-runner.md** — bun:test describe/test/expect, mocks, snapshots, lifecycle hooks, watch mode, coverage
- **07-file-io.md** — Bun.file(), Bun.write(), BunFile, streaming, Glob, FileSink incremental writing
- **08-shell-api.md** — Bun.$ template literal shell, piping, env vars, escaping, error handling
- **09-database-clients.md** — Bun.SQL unified API (Postgres/MySQL/SQLite), Bun.redis client, tagged templates, pooling
- **10-child-processes.md** — Bun.spawn(), Bun.spawnSync(), IPC channels, worker threads, structured cloning
- **11-ffi.md** — bun:ffi module, dlopen, C ABI interop, type mapping, callbacks, pointer management
- **12-frontend-dev.md** — HTML imports, fullstack dev server, HMR, React Fast Refresh, zero-config frontend

### Stats

- Routing entries: 13
- Reference files: 13
- Total lines: ~5,240
