# Changelog

All notable changes to the `astro` skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-04-17

### Added

Initial release tracking Astro v5.17.0 (stable) with coverage of v6 beta features where stable.

Reference files:

- `00-overview.md` — What Astro is, when to use it, installation, first page, command cheatsheet.
- `01-project-structure.md` — Directory conventions, `astro.config.mjs`, TypeScript setup, path aliases, env vars (`import.meta.env` and `astro:env`).
- `02-pages-and-routing.md` — File-based routing, dynamic routes, `getStaticPaths`, SSR params, redirects, rewrites, pagination, 404/500 pages, per-route prerender.
- `03-astro-components.md` — `.astro` syntax, props, slots, scoped CSS, `class:list`, client-side scripts, `Astro.*` API reference.
- `04-content-collections.md` — Content Layer, `defineCollection`, Zod schemas, `glob()`/`file()` loaders, cross-collection references, rendering, custom loaders, Live Content Collections.
- `05-islands-and-client-directives.md` — Islands architecture, `client:load`/`idle`/`visible`/`media`/`only`, state sharing, Server Islands.
- `06-rendering-modes.md` — Static vs on-demand vs hybrid, `prerender` export, adapter matrix, partial prerendering pattern.
- `07-actions.md` — `defineAction`, form handling, `ActionError` codes, calling from client/server, progressive enhancement.
- `08-middleware.md` — `defineMiddleware`, `sequence`, typing `Astro.locals`, auth pattern, response headers, i18n detection, observability.
- `09-endpoints-and-api-routes.md` — HTTP method handlers, webhooks, streaming, file downloads, RSS, OG image generation, CORS.
- `10-view-transitions.md` — `<ClientRouter />`, `transition:name`/`animate`/`persist`, lifecycle events, programmatic navigation, prefetching, accessibility.
- `11-integrations-and-adapters.md` — `astro add`, framework integrations, Tailwind v4, MDX, common integrations, adapter configurations (Node/Cloudflare/Vercel/Netlify), writing custom integrations.
- `12-deployment-and-best-practices.md` — Deployment checklist, static/serverless/edge hosting, image optimization, SEO, security headers, monitoring.

Tracking infrastructure:

- `SKILL.md` — Router with 13 routing entries, MANDATORY TRIGGERS, install instructions.
- `VERSION.json` — Pinned to Astro v5.17.0 with per-file source page mapping.
- `scripts/check-updates.py` — Integrity + staleness + upstream-version checker.
- `AUDIT-REPORT.md` — Quality self-assessment.

### Stats

- **13** routing entries in `SKILL.md`.
- **13** leaf reference files.
- **~3,900** total reference lines.
- **Source version tracked:** Astro 5.17.0.
- **Docs snapshot date:** 2026-04-17.
