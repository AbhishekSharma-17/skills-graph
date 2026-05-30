# SvelteKit — Hooks

> Source: [svelte.dev/docs/kit/hooks](https://svelte.dev/docs/kit/hooks)

## Table of Contents

- [Overview](#overview)
- [Server Hooks](#server-hooks)
- [handle](#handle)
- [handleFetch](#handlefetch)
- [handleError](#handleerror)
- [reroute](#reroute)
- [Client Hooks](#client-hooks)
- [Composing Hooks](#composing-hooks)
- [Common Patterns](#common-patterns)

## Overview

Hooks are functions that intercept and modify SvelteKit's behavior at key points in the request lifecycle. They act as middleware — running before pages render, when fetches happen, or when errors occur.

| Hook | File | Runs On | Purpose |
|------|------|---------|---------|
| `handle` | `hooks.server.ts` | Server | Intercept every server request |
| `handleFetch` | `hooks.server.ts` | Server | Modify fetch calls in load functions |
| `handleError` | `hooks.server.ts` / `hooks.client.ts` | Both | Handle unexpected errors |
| `reroute` | `hooks.ts` | Both | Rewrite URL before routing |

## Server Hooks

Defined in `src/hooks.server.ts`. Run on every server request.

## handle

The most important hook. Runs on every request and controls the response pipeline:

```ts
// src/hooks.server.ts
import type { Handle } from '@sveltejs/kit';

export const handle: Handle = async ({ event, resolve }) => {
  // Before route handling:
  const start = Date.now();

  // resolve() renders the page or runs the endpoint:
  const response = await resolve(event);

  // After route handling:
  const duration = Date.now() - start;
  response.headers.set('X-Response-Time', `${duration}ms`);

  return response;
};
```

### event.locals

Attach per-request data (auth, session) for use in load functions and actions:

```ts
export const handle: Handle = async ({ event, resolve }) => {
  const sessionId = event.cookies.get('session');

  if (sessionId) {
    const user = await getUserFromSession(sessionId);
    event.locals.user = user;
  }

  return resolve(event);
};
```

`event.locals` is available in load functions and actions:

```ts
// +page.server.ts
export const load = async ({ locals }) => {
  return { user: locals.user };
};
```

### Resolve Options

```ts
export const handle: Handle = async ({ event, resolve }) => {
  return resolve(event, {
    // Transform HTML before sending
    transformPageChunk: ({ html }) => {
      return html.replace('%lang%', getLocale(event));
    },

    // Filter which nodes get serialized
    filterSerializedResponseHeaders: (name) => {
      return name === 'content-type' || name === 'cache-control';
    },

    // Control preloading behavior
    preload: ({ type }) => {
      return type === 'js' || type === 'css';
    }
  });
};
```

### Route Protection

```ts
export const handle: Handle = async ({ event, resolve }) => {
  // Parse session
  const session = event.cookies.get('session');
  event.locals.user = session ? await verifySession(session) : null;

  // Protect routes
  if (event.url.pathname.startsWith('/dashboard')) {
    if (!event.locals.user) {
      return new Response(null, {
        status: 303,
        headers: { location: '/login' }
      });
    }
  }

  // Admin routes
  if (event.url.pathname.startsWith('/admin')) {
    if (event.locals.user?.role !== 'admin') {
      return new Response('Forbidden', { status: 403 });
    }
  }

  return resolve(event);
};
```

## handleFetch

Intercepts `fetch` calls made inside server-side load functions:

```ts
import type { HandleFetch } from '@sveltejs/kit';

export const handleFetch: HandleFetch = async ({ event, request, fetch }) => {
  // Rewrite internal API calls to use the service URL directly
  if (request.url.startsWith('https://api.example.com')) {
    request = new Request(
      request.url.replace('https://api.example.com', 'http://internal-api:3000'),
      request
    );
  }

  // Forward cookies to same-origin fetches
  if (request.url.startsWith(event.url.origin)) {
    request.headers.set('cookie', event.request.headers.get('cookie') ?? '');
  }

  return fetch(request);
};
```

## handleError

Handles unexpected errors (not `error()` or `redirect()`). Runs for both server and client errors:

```ts
// src/hooks.server.ts
import type { HandleServerError } from '@sveltejs/kit';

export const handleError: HandleServerError = async ({ error, event, status, message }) => {
  const errorId = crypto.randomUUID();

  console.error(`[${errorId}] ${status} ${event.url.pathname}:`, error);

  // Report to error tracking service
  await reportError({ errorId, error, url: event.url.pathname, status });

  // Return a safe error object (exposed to the client)
  return {
    message: 'An unexpected error occurred',
    code: errorId
  };
};
```

```ts
// src/hooks.client.ts
import type { HandleClientError } from '@sveltejs/kit';

export const handleError: HandleClientError = async ({ error, status, message }) => {
  console.error('Client error:', error);

  return {
    message: 'Something went wrong',
    code: 'CLIENT_ERROR'
  };
};
```

## reroute

Rewrite the URL before SvelteKit resolves the route. Runs on both server and client:

```ts
// src/hooks.ts
import type { Reroute } from '@sveltejs/kit';

export const reroute: Reroute = ({ url }) => {
  // Locale-based rerouting
  const match = url.pathname.match(/^\/(en|fr|de)(\/.*)?$/);
  if (match) {
    return match[2] || '/';
  }

  // Legacy URL redirects
  if (url.pathname === '/old-path') {
    return '/new-path';
  }
};
```

## Client Hooks

Defined in `src/hooks.client.ts`. Currently only `handleError` runs on the client.

```ts
// src/hooks.client.ts
import type { HandleClientError } from '@sveltejs/kit';

export const handleError: HandleClientError = async ({ error, status }) => {
  // Send to client-side error tracking
  if (typeof window !== 'undefined' && window.Sentry) {
    window.Sentry.captureException(error);
  }

  return { message: 'An error occurred' };
};
```

## Composing Hooks

Use `sequence()` to combine multiple handle hooks:

```ts
// src/hooks.server.ts
import { sequence } from '@sveltejs/kit/hooks';
import type { Handle } from '@sveltejs/kit';

const auth: Handle = async ({ event, resolve }) => {
  const session = event.cookies.get('session');
  event.locals.user = session ? await verifySession(session) : null;
  return resolve(event);
};

const logging: Handle = async ({ event, resolve }) => {
  const start = Date.now();
  const response = await resolve(event);
  console.log(`${event.request.method} ${event.url.pathname} ${Date.now() - start}ms`);
  return response;
};

const security: Handle = async ({ event, resolve }) => {
  const response = await resolve(event);
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  return response;
};

const rateLimit: Handle = async ({ event, resolve }) => {
  if (event.url.pathname.startsWith('/api/')) {
    const ip = event.getClientAddress();
    if (await isRateLimited(ip)) {
      return new Response('Too Many Requests', { status: 429 });
    }
  }
  return resolve(event);
};

// Hooks run in order: auth → rateLimit → logging → security
export const handle = sequence(auth, rateLimit, logging, security);
```

## Common Patterns

### CSRF Token

```ts
const csrf: Handle = async ({ event, resolve }) => {
  if (event.request.method === 'POST') {
    const token = event.cookies.get('csrf');
    const formToken = (await event.request.clone().formData()).get('_csrf');
    if (token !== formToken) {
      return new Response('Invalid CSRF token', { status: 403 });
    }
  }
  return resolve(event);
};
```

### Response Caching

```ts
const caching: Handle = async ({ event, resolve }) => {
  const response = await resolve(event);

  if (event.url.pathname.startsWith('/api/public/')) {
    response.headers.set('Cache-Control', 'public, max-age=300');
  }

  return response;
};
```

### Internationalization

```ts
const i18n: Handle = async ({ event, resolve }) => {
  const lang = event.cookies.get('lang')
    ?? event.request.headers.get('accept-language')?.split(',')[0]?.split('-')[0]
    ?? 'en';

  event.locals.lang = lang;

  return resolve(event, {
    transformPageChunk: ({ html }) => html.replace('%lang%', lang)
  });
};
```

## Common Pitfalls

1. **Forgetting to call `resolve()`** — Every `handle` hook must call `resolve(event)` and return its response (unless returning early)
2. **Reading the request body twice** — Use `request.clone()` if you need to read the body in a hook AND in an action
3. **Blocking with heavy work** — Hooks run on every request. Keep them fast. Offload heavy operations.
4. **Not using `sequence()`** — Nesting handle functions manually is error-prone. Use `sequence()` for clean composition.

## Related

- Loading Data → `03-loading-data.md`
- Form Actions → `04-form-actions.md`
- API Routes → `05-api-routes.md`
