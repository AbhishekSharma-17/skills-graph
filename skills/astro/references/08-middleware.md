# Middleware

> Source: https://docs.astro.build/en/guides/middleware/

Middleware lets you intercept **every on-demand request** and mutate the response, inject per-request state into `Astro.locals`, redirect, or rewrite. It is the standard place for authentication, logging, i18n detection, and feature flags.

## Where It Lives

Astro looks for middleware in one of:

- `src/middleware.ts` (single file)
- `src/middleware/index.ts` (folder with index re-exporting)

## Minimal Middleware

```ts
// src/middleware.ts
import { defineMiddleware } from "astro:middleware";

export const onRequest = defineMiddleware(async (context, next) => {
  console.log(`→ ${context.request.method} ${context.url.pathname}`);
  const response = await next();
  console.log(`← ${response.status}`);
  return response;
});
```

`defineMiddleware` gives you typing. The function receives:

- `context` — `APIContext` (same as inside `.astro` frontmatter: `request`, `url`, `params`, `cookies`, `locals`, `redirect`, `rewrite`, `clientAddress`, `site`).
- `next()` — call the next middleware (or the route handler). Returns a `Response`.

## Authenticating Every Request

```ts
// src/middleware.ts
import { defineMiddleware } from "astro:middleware";
import { verifySessionCookie } from "~/server/auth";

export const onRequest = defineMiddleware(async (context, next) => {
  const token = context.cookies.get("session")?.value;
  context.locals.user = token ? await verifySessionCookie(token) : null;

  // Gate specific paths
  const requiresAuth = context.url.pathname.startsWith("/dashboard");
  if (requiresAuth && !context.locals.user) {
    return context.redirect(`/login?redirect=${encodeURIComponent(context.url.pathname)}`);
  }

  return next();
});
```

## Typing `Astro.locals`

Add a global type in `src/env.d.ts`:

```ts
// src/env.d.ts
/// <reference path="../.astro/types.d.ts" />

declare namespace App {
  interface Locals {
    user: { id: string; email: string; role: "admin" | "user" } | null;
    requestId: string;
  }
}
```

Now every `context.locals` / `Astro.locals` access is typed.

## Composing Multiple Middlewares with `sequence`

```ts
// src/middleware.ts
import { defineMiddleware, sequence } from "astro:middleware";

const logger = defineMiddleware(async (ctx, next) => {
  const start = Date.now();
  const res = await next();
  console.log(`${ctx.request.method} ${ctx.url.pathname} → ${res.status} in ${Date.now() - start}ms`);
  return res;
});

const auth = defineMiddleware(async (ctx, next) => {
  ctx.locals.user = await getUserFromCookies(ctx.cookies);
  return next();
});

const requestId = defineMiddleware(async (ctx, next) => {
  ctx.locals.requestId = crypto.randomUUID();
  const res = await next();
  res.headers.set("x-request-id", ctx.locals.requestId);
  return res;
});

export const onRequest = sequence(logger, requestId, auth);
```

Execution order: `logger` runs first (outermost), then `requestId`, then `auth`, then the route. Responses unwind in reverse.

## Modifying the Response

```ts
export const onRequest = defineMiddleware(async (context, next) => {
  const response = await next();
  response.headers.set("X-Frame-Options", "DENY");
  response.headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
  response.headers.set("Permissions-Policy", "interest-cohort=()");
  return response;
});
```

### Rewriting the Body

Because `Response` is streaming, rewriting requires reading and re-creating:

```ts
export const onRequest = defineMiddleware(async (context, next) => {
  const response = await next();
  if (response.headers.get("content-type")?.startsWith("text/html")) {
    const html = await response.text();
    const modified = html.replace("</head>", '<meta name="x-custom" content="1"></head>');
    return new Response(modified, {
      status: response.status,
      headers: response.headers,
    });
  }
  return response;
});
```

## Redirects and Rewrites in Middleware

```ts
// Send any http request to https
export const onRequest = defineMiddleware(async (context, next) => {
  if (import.meta.env.PROD && context.url.protocol === "http:") {
    const secureUrl = context.url.href.replace("http:", "https:");
    return context.redirect(secureUrl, 308);
  }
  return next();
});

// Internally rewrite old URLs to new handlers
export const onRequest = defineMiddleware(async (context, next) => {
  if (context.url.pathname.startsWith("/legacy/")) {
    return context.rewrite(context.url.pathname.replace("/legacy/", "/"));
  }
  return next();
});
```

## Running Only on Specific Routes

Middleware runs for every on-demand route by default. Filter inside the handler:

```ts
export const onRequest = defineMiddleware(async (context, next) => {
  if (!context.url.pathname.startsWith("/api/")) return next();
  // API-only logic here
  // ...
  return next();
});
```

## Middleware and Prerendered Routes

- **In dev mode**, middleware runs for every route request (to support HMR and previews).
- **In production**, middleware only runs for **on-demand** routes. Prerendered routes are served as static HTML without going through the adapter — so no middleware execution.

To set headers for static pages, use your CDN / hosting's redirect/header file (`_headers` on Cloudflare, `vercel.json` on Vercel, etc.), not middleware.

## Calling Actions from Middleware

```ts
import { defineMiddleware } from "astro:middleware";
import { actions } from "astro:actions";

export const onRequest = defineMiddleware(async (context, next) => {
  // Auto-increment a visit counter for every page load
  const { error } = await context.callAction(actions.analytics.track, {
    path: context.url.pathname,
  });
  if (error) console.warn("track failed", error);
  return next();
});
```

## i18n Detection

```ts
export const onRequest = defineMiddleware(async (context, next) => {
  const cookieLocale = context.cookies.get("locale")?.value;
  const acceptLang = context.request.headers.get("accept-language") ?? "";
  const locale = cookieLocale ?? acceptLang.split(",")[0]?.split("-")[0] ?? "en";

  context.locals.locale = ["en", "fr", "de"].includes(locale) ? locale : "en";
  return next();
});
```

Combined with Astro's built-in i18n routing (`i18n.routing` in `astro.config.mjs`) for full localization.

## Observability Pattern

```ts
export const onRequest = defineMiddleware(async (ctx, next) => {
  const start = performance.now();
  try {
    const res = await next();
    metrics.histogram("http.request.duration_ms", performance.now() - start, {
      route: ctx.url.pathname,
      status: String(res.status),
    });
    return res;
  } catch (err) {
    metrics.counter("http.request.errors", 1, { route: ctx.url.pathname });
    throw err;
  }
});
```

## Common Pitfalls

- **Forgetting to `return next()`** → Astro returns an empty response. Always `return` the result of `next()` unless you're explicitly handling the request.
- **Mutating `context.url`** → it's a `URL` object but the route matcher has already resolved by the time middleware runs. For URL changes, use `context.rewrite()`.
- **Relying on middleware for prerendered pages in production** → it won't run. Put such logic in a build-time step or CDN config.
- **Swallowing errors silently** — re-throw after logging; otherwise the route never sees them.
- **Setting `locals` with non-serializable values and expecting them in client components** — `locals` is server-only. Client components only see what you pass via props from the `.astro` template.
- **Treating `sequence()` order as insignificant** — the first argument runs first/outermost. Put auth before logic that depends on it.
