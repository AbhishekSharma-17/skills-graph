# Hono Skill — Changelog

## [1.0.0] — 2026-03-28

**Source version tracked:** Hono v4.12.0

### Added
- `00-overview.md` — What Hono is, installation, quickstart, runtime comparison
- `01-routing.md` — HTTP methods, path params, wildcards, regex, chaining, app.route(), router selection
- `02-context-api.md` — Response methods, request access, context variables, env bindings, streaming
- `03-middleware.md` — Built-in middleware (CORS, logger, etag, compress, etc.), custom middleware, factory pattern
- `04-authentication.md` — JWT, Bearer, Basic auth, API key patterns, combining auth methods
- `05-validation.md` — Built-in validator, Zod validator, multiple targets, custom error handling, RPC integration
- `06-rpc-type-safety.md` — hc client setup, chaining routes, AppType export, SWR/TanStack Query integration
- `07-jsx-rendering.md` — Server-side JSX, components, Suspense streaming, jsxRenderer, client components
- `08-error-handling.md` — HTTPException, app.onError, app.notFound, structured error patterns
- `09-testing.md` — app.request(), Vitest setup, env mocking, middleware testing, validation testing
- `10-runtime-adapters.md` — Node.js, Cloudflare Workers/Pages, Bun, Deno, AWS Lambda, Vercel, static files
- `11-best-practices.md` — Project structure, factory pattern, performance, security, deployment CI/CD

### Stats
- Routing entries: 12
- Reference files: 12
- Total lines: ~3,600
