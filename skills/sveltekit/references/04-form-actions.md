# SvelteKit — Form Actions

> Source: [svelte.dev/docs/kit/form-actions](https://svelte.dev/docs/kit/form-actions)

## Table of Contents

- [Overview](#overview)
- [Default Actions](#default-actions)
- [Named Actions](#named-actions)
- [Progressive Enhancement](#progressive-enhancement)
- [Validation](#validation)
- [Returning Data](#returning-data)
- [Redirecting After Actions](#redirecting-after-actions)
- [File Uploads](#file-uploads)

## Overview

Form actions handle `<form>` submissions on the server. They are defined in `+page.server.ts` and run exclusively server-side. Forms work without JavaScript (progressive enhancement), and SvelteKit enhances them with `use:enhance` for no-reload submissions.

## Default Actions

A page can have a single default action:

```ts
// src/routes/login/+page.server.ts
import type { Actions } from './$types';
import { fail } from '@sveltejs/kit';

export const actions: Actions = {
  default: async ({ request, cookies }) => {
    const data = await request.formData();
    const email = data.get('email') as string;
    const password = data.get('password') as string;

    const user = await authenticate(email, password);

    if (!user) {
      return fail(401, { email, message: 'Invalid credentials' });
    }

    cookies.set('session', user.sessionId, {
      path: '/',
      httpOnly: true,
      sameSite: 'lax',
      secure: true,
      maxAge: 60 * 60 * 24 * 7 // 1 week
    });

    return { success: true };
  }
};
```

```svelte
<!-- src/routes/login/+page.svelte -->
<script>
  let { form } = $props();
</script>

{#if form?.message}
  <p class="error">{form.message}</p>
{/if}

<form method="POST">
  <input name="email" value={form?.email ?? ''} />
  <input name="password" type="password" />
  <button>Log In</button>
</form>

{#if form?.success}
  <p>Logged in successfully!</p>
{/if}
```

## Named Actions

Multiple actions per page, invoked via `?/actionName`:

```ts
// src/routes/todos/+page.server.ts
import type { Actions, PageServerLoad } from './$types';
import { fail } from '@sveltejs/kit';

export const load: PageServerLoad = async ({ locals }) => {
  return { todos: await getTodos(locals.user.id) };
};

export const actions: Actions = {
  create: async ({ request, locals }) => {
    const data = await request.formData();
    const text = data.get('text') as string;

    if (!text?.trim()) {
      return fail(400, { text, error: 'Todo text is required' });
    }

    await createTodo(locals.user.id, text);
    return { success: true };
  },

  delete: async ({ request, locals }) => {
    const data = await request.formData();
    const id = data.get('id') as string;

    await deleteTodo(locals.user.id, id);
  },

  toggle: async ({ request, locals }) => {
    const data = await request.formData();
    const id = data.get('id') as string;

    await toggleTodo(locals.user.id, id);
  }
};
```

```svelte
<!-- src/routes/todos/+page.svelte -->
<script>
  let { data, form } = $props();
</script>

<!-- Named action via ?/create -->
<form method="POST" action="?/create">
  <input name="text" value={form?.text ?? ''} />
  {#if form?.error}
    <span class="error">{form.error}</span>
  {/if}
  <button>Add</button>
</form>

{#each data.todos as todo}
  <div>
    <form method="POST" action="?/toggle" style="display:inline">
      <input type="hidden" name="id" value={todo.id} />
      <button>{todo.done ? '✓' : '○'}</button>
    </form>

    <span class:done={todo.done}>{todo.text}</span>

    <form method="POST" action="?/delete" style="display:inline">
      <input type="hidden" name="id" value={todo.id} />
      <button>×</button>
    </form>
  </div>
{/each}
```

## Progressive Enhancement

`use:enhance` upgrades forms to submit without a full page reload while keeping the no-JS fallback:

```svelte
<script>
  import { enhance } from '$app/forms';
</script>

<!-- Basic enhance — handles everything automatically -->
<form method="POST" use:enhance>
  <input name="email" />
  <button>Subscribe</button>
</form>
```

### Custom Enhance Behavior

```svelte
<script>
  import { enhance } from '$app/forms';

  let submitting = $state(false);
</script>

<form
  method="POST"
  action="?/create"
  use:enhance={() => {
    submitting = true;

    return async ({ result, update }) => {
      submitting = false;

      if (result.type === 'success') {
        // Custom success handling
        showToast('Created!');
      }

      // Call update() to apply the default behavior
      // (rerun load functions, update form prop)
      await update();

      // Or handle manually:
      // await update({ reset: false }); // Don't reset the form
      // await applyAction(result);      // Apply result manually
    };
  }}
>
  <input name="text" />
  <button disabled={submitting}>
    {submitting ? 'Saving...' : 'Create'}
  </button>
</form>
```

### Result Types

The `result` object in enhance callbacks has these types:

| Type | Meaning |
|------|---------|
| `success` | Action returned data (2xx) |
| `failure` | Action called `fail()` (4xx) |
| `redirect` | Action threw `redirect()` (3xx) |
| `error` | Unexpected error (5xx) |

## Validation

Use `fail()` to return validation errors while preserving form data:

```ts
import { fail } from '@sveltejs/kit';

export const actions = {
  register: async ({ request }) => {
    const data = await request.formData();
    const email = data.get('email') as string;
    const password = data.get('password') as string;
    const name = data.get('name') as string;

    const errors: Record<string, string> = {};

    if (!email?.includes('@')) errors.email = 'Invalid email';
    if (!password || password.length < 8) errors.password = 'Min 8 characters';
    if (!name?.trim()) errors.name = 'Name is required';

    if (Object.keys(errors).length > 0) {
      return fail(400, { errors, email, name });
    }

    await createUser({ email, password, name });
    return { success: true };
  }
};
```

```svelte
<form method="POST" action="?/register" use:enhance>
  <label>
    Name
    <input name="name" value={form?.name ?? ''} />
    {#if form?.errors?.name}<span class="error">{form.errors.name}</span>{/if}
  </label>

  <label>
    Email
    <input name="email" type="email" value={form?.email ?? ''} />
    {#if form?.errors?.email}<span class="error">{form.errors.email}</span>{/if}
  </label>

  <label>
    Password
    <input name="password" type="password" />
    {#if form?.errors?.password}<span class="error">{form.errors.password}</span>{/if}
  </label>

  <button>Register</button>
</form>
```

## Returning Data

Actions return data that becomes available via the `form` prop:

```ts
export const actions = {
  search: async ({ request }) => {
    const data = await request.formData();
    const query = data.get('q') as string;
    const results = await searchDatabase(query);

    return { query, results, count: results.length };
  }
};
```

```svelte
<script>
  let { form } = $props();
</script>

{#if form?.results}
  <p>Found {form.count} results for "{form.query}"</p>
  {#each form.results as result}
    <div>{result.title}</div>
  {/each}
{/if}
```

## Redirecting After Actions

Use `redirect()` after successful mutations (POST-redirect-GET pattern):

```ts
import { redirect } from '@sveltejs/kit';

export const actions = {
  create: async ({ request, locals }) => {
    const data = await request.formData();
    const post = await createPost(data, locals.user.id);

    // 303 See Other — correct status for POST redirects
    throw redirect(303, `/blog/${post.slug}`);
  }
};
```

## File Uploads

Handle file uploads via FormData:

```ts
export const actions = {
  upload: async ({ request }) => {
    const data = await request.formData();
    const file = data.get('avatar') as File;

    if (!file || file.size === 0) {
      return fail(400, { error: 'No file selected' });
    }

    if (file.size > 5 * 1024 * 1024) {
      return fail(400, { error: 'File too large (max 5MB)' });
    }

    const buffer = await file.arrayBuffer();
    const path = await saveFile(buffer, file.name);

    return { avatarUrl: path };
  }
};
```

```svelte
<form method="POST" action="?/upload" enctype="multipart/form-data" use:enhance>
  <input name="avatar" type="file" accept="image/*" />
  <button>Upload</button>
</form>
```

## Common Pitfalls

1. **Forgetting `method="POST"`** — Forms default to GET. Actions require POST.
2. **Using `action` without `?/`** — Named actions need `action="?/actionName"`, not `action="/actionName"`
3. **Not using `fail()`** — Returning an object with an error doesn't set the HTTP status. Use `fail(400, data)` for validation errors.
4. **Mutating without redirecting** — After create/update/delete, redirect with 303 to prevent duplicate submissions on refresh
5. **Missing `enctype` for files** — File uploads need `enctype="multipart/form-data"`

## Related

- Loading Data → `03-loading-data.md`
- API Routes → `05-api-routes.md`
- Navigation → `08-navigation.md`
