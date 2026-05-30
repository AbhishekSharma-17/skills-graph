# SvelteKit — Navigation & App Modules

> Source: [svelte.dev/docs/kit/$app-navigation](https://svelte.dev/docs/kit/$app-navigation)

## Table of Contents

- [$app/navigation](#appnavigation)
- [$app/stores](#appstores)
- [$app/environment](#appenvironment)
- [Remote Functions](#remote-functions)
- [Prefetching & Preloading](#prefetching--preloading)
- [Snapshot](#snapshot)

## $app/navigation

Functions for programmatic navigation and data invalidation.

### goto

Navigate programmatically to a URL:

```svelte
<script>
  import { goto } from '$app/navigation';

  async function handleLogin() {
    await login();
    goto('/dashboard');
  }

  function goBack() {
    goto('/', { replaceState: true }); // Replace history entry
  }
</script>
```

**Options:**

```ts
goto(url: string, {
  replaceState?: boolean;  // Replace instead of push history (default: false)
  noScroll?: boolean;      // Don't scroll to top (default: false)
  keepFocus?: boolean;     // Keep current element focused (default: false)
  invalidateAll?: boolean; // Rerun all load functions (default: false)
  state?: App.PageState;   // Push state data with navigation
});
```

### invalidate

Re-run load functions that depend on a specific URL or custom key:

```svelte
<script>
  import { invalidate, invalidateAll } from '$app/navigation';

  async function refreshPosts() {
    // Rerun load functions that fetched from or depend on this URL:
    await invalidate('/api/posts');

    // Rerun load functions with a custom dependency:
    await invalidate('app:posts');

    // Rerun load functions matching a predicate:
    await invalidate((url) => url.pathname.startsWith('/api/'));

    // Rerun ALL load functions on the page:
    await invalidateAll();
  }
</script>
```

### beforeNavigate / afterNavigate / onNavigate

Lifecycle hooks for navigation events:

```svelte
<script>
  import { beforeNavigate, afterNavigate, onNavigate } from '$app/navigation';

  // Before leaving the page — can cancel navigation
  beforeNavigate(({ cancel, to, from, type }) => {
    if (hasUnsavedChanges && !confirm('Discard changes?')) {
      cancel();
    }
  });

  // After navigation completes
  afterNavigate(({ from, to, type }) => {
    // Track page views
    analytics.track('pageview', { path: to?.url.pathname });
  });

  // During navigation — for view transitions
  onNavigate((navigation) => {
    if (!document.startViewTransition) return;

    return new Promise((resolve) => {
      document.startViewTransition(async () => {
        resolve();
        await navigation.complete;
      });
    });
  });
</script>
```

### preloadData / preloadCode

Programmatically preload data or code for a route:

```svelte
<script>
  import { preloadData, preloadCode } from '$app/navigation';

  // Preload data + code (as if hovering a link)
  function onMouseEnter() {
    preloadData('/dashboard');
  }

  // Preload only the route's code (no data fetching)
  function onVisible() {
    preloadCode('/settings');
  }
</script>
```

## $app/stores

Reactive stores providing page state. In Svelte 5, prefer `$page` from `$app/state`:

```svelte
<script>
  import { page } from '$app/state';
</script>

<p>Current path: {page.url.pathname}</p>
<p>Route ID: {page.route.id}</p>
<p>Params: {JSON.stringify(page.params)}</p>
<p>Status: {page.status}</p>
<p>Error: {page.error?.message}</p>
<p>Data: {JSON.stringify(page.data)}</p>
```

### Available Properties

| Property | Type | Description |
|----------|------|-------------|
| `page.url` | `URL` | Current page URL |
| `page.params` | `Record<string, string>` | Route parameters |
| `page.route` | `{ id: string }` | Route ID (e.g., `/blog/[slug]`) |
| `page.status` | `number` | HTTP status code |
| `page.error` | `App.Error \| null` | Error object if on error page |
| `page.data` | `App.PageData` | Merged page + layout data |
| `page.form` | `any` | Form action return data |
| `page.state` | `App.PageState` | Shallow routing state |

### Legacy Stores (Svelte 4 style)

```svelte
<script>
  import { page, navigating, updated } from '$app/stores';
</script>

<!-- $page — current page state -->
<p>Path: {$page.url.pathname}</p>

<!-- $navigating — null when idle, navigation info when navigating -->
{#if $navigating}
  <div class="loading-bar" />
{/if}

<!-- $updated — true when the app has been updated (new deployment) -->
{#if $updated}
  <div class="update-banner">
    New version available.
    <button onclick={() => location.reload()}>Reload</button>
  </div>
{/if}
```

## $app/environment

Runtime environment information:

```svelte
<script>
  import { browser, dev, building, version } from '$app/environment';
</script>
```

| Export | Type | Description |
|--------|------|-------------|
| `browser` | `boolean` | `true` if running in the browser |
| `dev` | `boolean` | `true` in development mode |
| `building` | `boolean` | `true` during `vite build` |
| `version` | `string` | App version from `config.kit.version.name` |

```svelte
<script>
  import { browser, dev } from '$app/environment';
  import { onMount } from 'svelte';

  // Guard browser-only code
  if (browser) {
    window.addEventListener('resize', handleResize);
  }

  // Dev-only logging
  if (dev) {
    console.log('Debug mode enabled');
  }

  // Or use onMount (always browser-only)
  onMount(() => {
    const observer = new IntersectionObserver(callback);
  });
</script>
```

## Remote Functions

SvelteKit 2.56+ introduces remote functions — server functions callable from the client as if they were local:

### Query Functions

```ts
// src/routes/dashboard/+page.server.ts
import { query } from '@sveltejs/kit';

export const analytics = query(async (event) => {
  const data = await db.analytics.getForUser(event.locals.user.id);
  return data;
});
```

```svelte
<!-- src/routes/dashboard/+page.svelte -->
<script>
  let { data } = $props();
</script>

{#await data.analytics}
  <p>Loading...</p>
{:then analytics}
  <Chart data={analytics} />
{/await}
```

### Command Functions

For mutations (write operations):

```ts
// src/routes/todos/+page.server.ts
import { command } from '@sveltejs/kit';

export const addTodo = command(async (event, text: string) => {
  await db.todo.create({ data: { text, userId: event.locals.user.id } });
});

export const deleteTodo = command(async (event, id: string) => {
  await db.todo.delete({ where: { id } });
});
```

```svelte
<script>
  import { addTodo, deleteTodo } from './+page.server';

  let text = $state('');

  async function handleSubmit() {
    await addTodo(text);
    text = '';
  }
</script>
```

## Prefetching & Preloading

Control preloading behavior via HTML attributes:

```html
<!-- Preload data when link is hovered (default) -->
<a href="/about">About</a>

<!-- Preload data eagerly when link enters viewport -->
<a href="/about" data-sveltekit-preload-data="hover">About</a>

<!-- Only preload code, not data -->
<a href="/about" data-sveltekit-preload-code="eager">About</a>

<!-- Disable preloading entirely -->
<a href="/about" data-sveltekit-preload-data="off">About</a>
```

Set defaults in `app.html`:

```html
<body data-sveltekit-preload-data="hover">
  %sveltekit.body%
</body>
```

## Snapshot

Preserve ephemeral UI state (scroll position, form input) across navigations:

```svelte
<script>
  import type { Snapshot } from './$types';

  let comment = $state('');
  let scrollY = $state(0);

  export const snapshot: Snapshot<{ comment: string; scrollY: number }> = {
    capture: () => ({ comment, scrollY }),
    restore: (value) => {
      comment = value.comment;
      scrollY = value.scrollY;
    }
  };
</script>

<textarea bind:value={comment}></textarea>
```

Snapshots are stored in session history — they survive back/forward navigation but not page refresh.

## Common Pitfalls

1. **Using `goto()` in load functions** — Use `throw redirect()` instead. `goto()` is for client-side navigation only.
2. **Accessing `$page` during SSR** — The store works during SSR, but `browser`-only APIs don't. Guard with `if (browser)`.
3. **Invalidating without `depends()`** — URL-based invalidation only works for URLs used in `fetch()`. For custom keys, use `depends('app:key')` in the load function.
4. **Forgetting `await` on navigation** — `goto()` and `invalidate()` return Promises. Await them if you need to ensure completion before proceeding.

## Related

- Routing → `01-routing.md`
- Loading Data → `03-loading-data.md`
- Page Options → `07-page-options.md`
