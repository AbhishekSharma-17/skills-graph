# SvelteKit — Loading Data

> Source: [svelte.dev/docs/kit/load](https://svelte.dev/docs/kit/load)

## Table of Contents

- [Overview](#overview)
- [Server Load Functions](#server-load-functions)
- [Universal Load Functions](#universal-load-functions)
- [Server vs Universal](#server-vs-universal)
- [Page Data](#page-data)
- [Layout Data](#layout-data)
- [Using Parent Data](#using-parent-data)
- [Depends & Invalidation](#depends--invalidation)
- [Error Handling](#error-handling)
- [Redirects](#redirects)
- [Streaming](#streaming)

## Overview

SvelteKit uses **load functions** to fetch data before rendering a page. Load functions run on the server during SSR and in the browser during client-side navigation. Data returned from a load function becomes available to the page as the `data` prop.

Two types exist:
- **Server load** (`+page.server.ts`) — Runs only on the server. Has access to databases, filesystem, secrets.
- **Universal load** (`+page.ts`) — Runs on both server and client. Can return non-serializable data (component references, functions).

## Server Load Functions

Defined in `+page.server.ts` or `+layout.server.ts`. Run exclusively on the server.

```ts
// src/routes/blog/+page.server.ts
import type { PageServerLoad } from './$types';
import { db } from '$lib/server/db';

export const load: PageServerLoad = async ({ params, locals, url }) => {
  const page = Number(url.searchParams.get('page') ?? '1');
  const posts = await db.post.findMany({
    skip: (page - 1) * 10,
    take: 10,
    orderBy: { createdAt: 'desc' }
  });

  return {
    posts,
    page,
    totalPages: Math.ceil(await db.post.count() / 10)
  };
};
```

### Available Parameters

| Parameter | Description |
|-----------|-------------|
| `params` | Route parameters (e.g., `{ slug: 'hello' }`) |
| `url` | URL object with pathname, searchParams, etc. |
| `route` | Route info (`{ id: '/blog/[slug]' }`) |
| `locals` | Per-request data set in hooks (auth, session) |
| `cookies` | Read/set cookies |
| `request` | The raw Request object |
| `fetch` | Enhanced fetch (preserves cookies, resolves relative URLs) |
| `depends` | Declare custom invalidation dependencies |
| `parent` | Get data from parent layout load functions |
| `platform` | Platform-specific context (Cloudflare bindings, etc.) |

## Universal Load Functions

Defined in `+page.ts` or `+layout.ts`. Run on both server (SSR) and client (navigation).

```ts
// src/routes/docs/+page.ts
import type { PageLoad } from './$types';
import TableOfContents from '$lib/components/TOC.svelte';

export const load: PageLoad = async ({ fetch, params }) => {
  const res = await fetch('/api/docs');
  const docs = await res.json();

  return {
    docs,
    // Can return non-serializable values:
    component: TableOfContents,
    formatDate: (d: string) => new Date(d).toLocaleDateString()
  };
};
```

### When Universal Runs on Server vs Client

- **First page load (SSR):** Runs on the server
- **Client-side navigation:** Runs in the browser
- **After invalidation:** Runs in the browser

## Server vs Universal

| Feature | Server (`+page.server.ts`) | Universal (`+page.ts`) |
|---------|---------------------------|------------------------|
| Runs on | Server only | Server + Client |
| Access to | DB, filesystem, secrets, cookies | fetch, non-serializable data |
| Return values | Must be serializable (JSON) | Any value (components, functions) |
| Use for | Database queries, auth checks, secrets | API calls, returning components |

**Rule of thumb:** Use server load for anything touching secrets, databases, or the filesystem. Use universal load when you need to return non-serializable data or want the load to run client-side.

### Both Together

You can have both `+page.server.ts` and `+page.ts` for the same route. The server load runs first, and its data is passed to the universal load via the `data` property:

```ts
// +page.server.ts
export const load = async () => {
  return { serverData: 'from server' };
};

// +page.ts
export const load = async ({ data }) => {
  return {
    ...data,
    clientEnhanced: true
  };
};
```

## Page Data

Pages receive load function data via `$props()`:

```svelte
<!-- +page.svelte -->
<script>
  let { data } = $props();
</script>

<h1>{data.post.title}</h1>
<div>{@html data.post.content}</div>
```

### Typed Data

Auto-generated types ensure type safety:

```svelte
<script lang="ts">
  import type { PageData } from './$types';
  let { data }: { data: PageData } = $props();
  // data is fully typed based on what your load function returns
</script>
```

## Layout Data

Layout load functions provide data to all child routes:

```ts
// src/routes/+layout.server.ts
import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ locals }) => {
  return {
    user: locals.user,
    notifications: await getNotifications(locals.user?.id)
  };
};
```

Layout data merges with page data. Page load data takes precedence on key conflicts.

```svelte
<!-- src/routes/dashboard/+page.svelte -->
<script>
  let { data } = $props();
  // data.user        ← from layout
  // data.notifications ← from layout
  // data.dashboardStats ← from this page's load
</script>
```

## Using Parent Data

Access parent layout data from a child load function:

```ts
// src/routes/dashboard/settings/+page.server.ts
export const load = async ({ parent }) => {
  const { user } = await parent();
  // user comes from the layout load function

  const settings = await getSettings(user.id);
  return { settings };
};
```

**Caution:** `await parent()` creates a waterfall. Only use it when you genuinely need parent data to make your query. Prefer parallel data loading when possible.

## Depends & Invalidation

Declare custom invalidation keys to control when data reloads:

```ts
// +page.server.ts
export const load = async ({ depends, fetch }) => {
  depends('app:posts');

  const posts = await fetch('/api/posts').then(r => r.json());
  return { posts };
};
```

```svelte
<script>
  import { invalidate, invalidateAll } from '$app/navigation';

  async function refresh() {
    // Rerun load functions that depend on 'app:posts':
    await invalidate('app:posts');

    // Or rerun ALL load functions:
    await invalidateAll();

    // Or invalidate by URL pattern:
    await invalidate((url) => url.pathname === '/api/posts');
  }
</script>
```

## Error Handling

Throw `error()` from load functions to show error pages:

```ts
import { error } from '@sveltejs/kit';

export const load = async ({ params }) => {
  const post = await getPost(params.slug);

  if (!post) {
    throw error(404, {
      message: 'Post not found'
    });
  }

  return { post };
};
```

The nearest `+error.svelte` catches and displays the error.

## Redirects

Throw `redirect()` to navigate away:

```ts
import { redirect } from '@sveltejs/kit';

export const load = async ({ locals }) => {
  if (!locals.user) {
    throw redirect(303, '/login');
  }

  return { user: locals.user };
};
```

Common status codes: `301` (permanent), `302` (found), `303` (see other — use after form submissions), `307` (temporary).

## Streaming

Return promises to stream data — the page renders immediately with available data, and streams in the rest:

```ts
export const load = async ({ fetch }) => {
  return {
    // Fast — available immediately:
    title: 'Dashboard',

    // Slow — streamed in when ready:
    analytics: fetch('/api/analytics').then(r => r.json()),
    recommendations: fetch('/api/recommendations').then(r => r.json())
  };
};
```

```svelte
<script>
  let { data } = $props();
</script>

<h1>{data.title}</h1>

{#await data.analytics}
  <p>Loading analytics...</p>
{:then analytics}
  <AnalyticsChart data={analytics} />
{:catch error}
  <p>Failed to load analytics</p>
{/await}
```

## Common Pitfalls

1. **Returning non-serializable data from server load** — Server load functions must return JSON-serializable data. Use universal load for components/functions.
2. **Creating waterfalls with `parent()`** — Only await parent when you need its data for your query
3. **Fetching from your own API** — In server load, call your database directly instead of fetching `/api/...`
4. **Not using the provided `fetch`** — Always use the `fetch` parameter, not the global `fetch`, to preserve cookies and handle relative URLs

## Related

- Form Actions → `04-form-actions.md`
- Navigation → `08-navigation.md`
- Hooks → `06-hooks.md`
