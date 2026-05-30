# SvelteKit Skill — Changelog

## [1.0.0] — 2026-05-31

**Source version tracked:** @sveltejs/kit 2.57.x / svelte 5.55.x

### Added

- **00-overview.md** — What is SvelteKit, when to use it, project structure, installation, configuration, $lib alias, TypeScript support
- **01-routing.md** — File-based routing, pages, layouts, dynamic parameters, rest params, optional params, matchers, route groups, breaking out of layouts, error pages, preloading
- **02-runes-reactivity.md** — Svelte 5 runes: $state, $state.raw, $state.snapshot, $derived, $derived.by, $effect, $effect.pre, $props, $bindable, $inspect, reactive proxies, .svelte.ts files, stores vs runes migration
- **03-loading-data.md** — Server vs universal load functions, page data, layout data, parent data, depends/invalidation, error handling, redirects, streaming with promises
- **04-form-actions.md** — Default and named actions, progressive enhancement with use:enhance, validation with fail(), returning data, POST-redirect-GET, file uploads
- **05-api-routes.md** — +server.ts endpoints, HTTP methods (GET/POST/PUT/DELETE), request handling (JSON, FormData, URL params, cookies), response helpers, streaming (SSE), CORS, content negotiation
- **06-hooks.md** — handle hook (middleware), event.locals, resolve options, route protection, handleFetch, handleError, reroute, client hooks, composing with sequence()
- **07-page-options.md** — SSR, CSR, prerendering (SSG), trailing slash, per-route options, rendering modes comparison, project types (full SSR, static, SPA, hybrid)
- **08-navigation.md** — goto, invalidate, beforeNavigate/afterNavigate/onNavigate, preloading, $app/stores, $app/state, $app/environment, remote functions (query/command), snapshot
- **09-components.md** — Component structure, $props, snippets, children, template syntax ({#if}, {#each}, {#await}, {@html}, {@const}), bindings, actions (use:), lifecycle (onMount, tick), context API, special elements
- **10-styling.md** — Scoped CSS, :global, dynamic classes/styles, CSS variables as props, Tailwind CSS integration, transitions (fade, fly, slide, scale), animations (flip), motion (spring, tweened)
- **11-environment.md** — $env/static/private, $env/static/public, $env/dynamic/private, $env/dynamic/public, $app modules, svelte.config.js options, Vite configuration, .env files
- **12-deployment.md** — adapter-auto, adapter-node, adapter-vercel, adapter-cloudflare, adapter-netlify, adapter-static, Docker deployment, environment variables in production

### Stats

- Routing entries: 13
- Reference files: 13
- Total lines: ~4,300
