# SvelteKit — Routing

> Source: [svelte.dev/docs/kit/routing](https://svelte.dev/docs/kit/routing)

## Table of Contents

- [File-Based Routing](#file-based-routing)
- [Pages](#pages)
- [Layouts](#layouts)
- [Dynamic Parameters](#dynamic-parameters)
- [Rest Parameters](#rest-parameters)
- [Optional Parameters](#optional-parameters)
- [Parameter Matchers](#parameter-matchers)
- [Route Groups](#route-groups)
- [Breaking Out of Layouts](#breaking-out-of-layouts)
- [Error Pages](#error-pages)
- [Advanced Routing](#advanced-routing)

## File-Based Routing

SvelteKit uses the filesystem to define routes. Every directory inside `src/routes/` that contains a `+page.svelte` file creates a route in your app. The route URL maps directly to the directory path.

```
src/routes/
├── +page.svelte              → /
├── about/
│   └── +page.svelte          → /about
├── blog/
│   ├── +page.svelte          → /blog
│   └── [slug]/
│       └── +page.svelte      → /blog/:slug
└── api/
    └── health/
        └── +server.ts        → /api/health (API only)
```

### Route File Types

| File | Purpose |
|------|---------|
| `+page.svelte` | Page component (UI) |
| `+page.ts` | Universal load function (runs on server + client) |
| `+page.server.ts` | Server-only load function + form actions |
| `+layout.svelte` | Layout component wrapping child routes |
| `+layout.ts` | Universal layout load function |
| `+layout.server.ts` | Server-only layout load function |
| `+error.svelte` | Error page component |
| `+server.ts` | API endpoint (no page) |

## Pages

Every `+page.svelte` file defines a page component. Pages receive data from their load function via the `data` prop:

```svelte
<!-- src/routes/about/+page.svelte -->
<script>
  let { data } = $props();
</script>

<h1>About {data.company}</h1>
<p>{data.description}</p>
```

```ts
// src/routes/about/+page.ts
export function load() {
  return {
    company: 'Acme Corp',
    description: 'We make things.'
  };
}
```

## Layouts

Layouts wrap child pages and persist across navigations. Create `+layout.svelte` to define a layout:

```svelte
<!-- src/routes/+layout.svelte -->
<script>
  import Nav from '$lib/components/Nav.svelte';
  let { children } = $props();
</script>

<Nav />
<main>
  {@render children()}
</main>
<footer>Copyright 2026</footer>
```

### Nested Layouts

Each directory level can have its own layout. They nest automatically:

```
src/routes/
├── +layout.svelte              ← Root layout (nav, footer)
├── dashboard/
│   ├── +layout.svelte          ← Dashboard layout (sidebar)
│   ├── +page.svelte            ← /dashboard
│   └── settings/
│       └── +page.svelte        ← /dashboard/settings
```

The dashboard pages get both the root layout AND the dashboard layout.

### Layout Data

Layouts can load data, which is available to all child pages:

```ts
// src/routes/dashboard/+layout.server.ts
import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ locals }) => {
  return { user: locals.user };
};
```

```svelte
<!-- src/routes/dashboard/+layout.svelte -->
<script>
  let { data, children } = $props();
</script>

<aside>Welcome, {data.user.name}</aside>
<div>{@render children()}</div>
```

## Dynamic Parameters

Square brackets create dynamic route segments:

```
src/routes/blog/[slug]/+page.svelte    → /blog/hello-world
src/routes/users/[id]/+page.svelte     → /users/42
```

Parameters are available in load functions and the `$page` store:

```ts
// src/routes/blog/[slug]/+page.server.ts
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params }) => {
  const post = await getPost(params.slug);
  if (!post) throw error(404, 'Post not found');
  return { post };
};
```

### Multiple Parameters

```
src/routes/[category]/[slug]/+page.svelte   → /tech/my-article
```

```ts
export const load = async ({ params }) => {
  // params.category = 'tech'
  // params.slug = 'my-article'
};
```

## Rest Parameters

Use `[...rest]` to capture multiple path segments:

```
src/routes/docs/[...path]/+page.svelte
```

- `/docs/getting-started` → `params.path = 'getting-started'`
- `/docs/api/auth/login` → `params.path = 'api/auth/login'`

```ts
export const load = async ({ params }) => {
  const segments = params.path.split('/');
  // ['api', 'auth', 'login']
};
```

## Optional Parameters

Double brackets make a parameter optional:

```
src/routes/[[lang]]/about/+page.svelte
```

- `/about` → `params.lang = undefined`
- `/en/about` → `params.lang = 'en'`

## Parameter Matchers

Validate parameters with custom matchers in `src/params/`:

```ts
// src/params/integer.ts
import type { ParamMatcher } from '@sveltejs/kit';

export const match: ParamMatcher = (param) => {
  return /^\d+$/.test(param);
};
```

```
src/routes/users/[id=integer]/+page.svelte
```

Only numeric IDs match. A request like `/users/abc` falls through to a 404 or the next matching route.

## Route Groups

Parenthesized directories create groups that affect layout inheritance without affecting the URL:

```
src/routes/
├── (marketing)/
│   ├── +layout.svelte       ← Marketing layout
│   ├── +page.svelte          ← /  (home page)
│   ├── about/
│   │   └── +page.svelte      ← /about
│   └── pricing/
│       └── +page.svelte      ← /pricing
├── (app)/
│   ├── +layout.svelte       ← App layout (sidebar, auth)
│   ├── dashboard/
│   │   └── +page.svelte      ← /dashboard
│   └── settings/
│       └── +page.svelte      ← /settings
```

The parenthesized names `(marketing)` and `(app)` do not appear in the URL. Each group can have its own layout.

## Breaking Out of Layouts

Use `@` to "reset" to a specific layout level:

```
src/routes/
├── +layout.svelte              ← Layout A (root)
├── (app)/
│   ├── +layout.svelte          ← Layout B (app)
│   ├── dashboard/
│   │   └── +page.svelte        ← Uses Layout A + B
│   └── login/
│       └── +page@.svelte       ← Uses only root layout A (skips B)
```

- `+page@.svelte` — Reset to root layout
- `+page@(app).svelte` — Reset to the `(app)` group layout

## Error Pages

Create `+error.svelte` to customize error display. Error pages cascade up the layout tree:

```svelte
<!-- src/routes/+error.svelte -->
<script>
  import { page } from '$app/stores';
</script>

<h1>{$page.status}</h1>
<p>{$page.error?.message}</p>
```

Each route directory can have its own `+error.svelte` for localized error handling.

## Advanced Routing

### Preload Strategies

Control when SvelteKit preloads data for links:

```html
<!-- Preload on hover (default) -->
<a href="/about">About</a>

<!-- Preload on viewport entry -->
<a href="/about" data-sveltekit-preload-data="hover">About</a>

<!-- Disable preloading -->
<a href="/about" data-sveltekit-preload-data="off">About</a>

<!-- Preload code only (not data) -->
<a href="/about" data-sveltekit-preload-code="eager">About</a>
```

### Preventing Navigation

```html
<!-- Disable client-side navigation for this link -->
<a href="/external" data-sveltekit-reload>External</a>

<!-- Disable scroll reset on navigation -->
<a href="/same-page-section" data-sveltekit-noscroll>Section</a>

<!-- Replace history entry instead of pushing -->
<a href="/login" data-sveltekit-replacestate>Login</a>
```

## Common Pitfalls

1. **Missing `+page.svelte`** — A directory without `+page.svelte` is not a route (it may only be a layout group or API route)
2. **Conflicting routes** — `src/routes/a/[b]` and `src/routes/a/c` can conflict; the specific route (`a/c`) wins over the dynamic one
3. **Layout data not flowing** — Layout load data is merged with page data; if keys collide, the page load wins
4. **Forgetting `@render children()`** — Layouts must render their children or child pages won't appear

## Related

- Loading Data → `03-loading-data.md`
- Page Options → `07-page-options.md`
- Navigation → `08-navigation.md`
