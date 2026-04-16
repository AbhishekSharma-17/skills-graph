# Astro Actions

> Source: https://docs.astro.build/en/guides/actions/

Astro Actions (stable since 4.15, first-class in 5.x) are **type-safe, server-executed functions** callable from both the server and the client. They replace the need to hand-write API endpoints for common mutations: form submissions, button clicks, data writes.

Think: tRPC-style RPC without the setup, with automatic form-handling, input validation via Zod, and error types that flow to the caller.

## Table of Contents

- [Enabling Actions](#enabling-actions)
- [Defining an Action](#defining-an-action)
- [Calling from the Client](#calling-from-the-client)
- [Calling from Server Code](#calling-from-server-code)
- [Form Handling](#form-handling)
- [Error Handling](#error-handling)
- [Auth and Middleware Integration](#auth-and-middleware-integration)
- [Common Pitfalls](#common-pitfalls)

## Enabling Actions

Actions require **on-demand rendering**. Either:

- Set `output: "server"` in `astro.config.mjs`, OR
- Keep `output: "static"` but ensure the page calling the action is NOT prerendered (or don't call from prerendered pages).

```js
// astro.config.mjs
import { defineConfig } from "astro/config";
import node from "@astrojs/node";

export default defineConfig({
  output: "server",
  adapter: node({ mode: "standalone" }),
});
```

## Defining an Action

Create `src/actions/index.ts` (exported name must be `server`):

```ts
// src/actions/index.ts
import { defineAction, ActionError } from "astro:actions";
import { z } from "astro:schema";

export const server = {
  likePost: defineAction({
    accept: "json",
    input: z.object({
      postId: z.string().uuid(),
    }),
    handler: async ({ postId }, context) => {
      const user = context.locals.user;
      if (!user) {
        throw new ActionError({ code: "UNAUTHORIZED", message: "Login required" });
      }
      const likes = await incrementLikes(postId, user.id);
      return { likes };
    },
  }),

  createComment: defineAction({
    accept: "form",
    input: z.object({
      postId: z.string().uuid(),
      body: z.string().min(1).max(1000),
    }),
    handler: async ({ postId, body }, { locals }) => {
      const user = locals.user;
      if (!user) throw new ActionError({ code: "UNAUTHORIZED" });
      return await db.comment.create({ data: { postId, body, userId: user.id } });
    },
  }),
};
```

### `defineAction()` Fields

| Field | Purpose |
|-------|---------|
| `accept` | `"json"` (default) or `"form"` — controls input parsing |
| `input` | Zod schema for validating input (optional, highly recommended) |
| `handler(input, context)` | The actual server logic. `context` = `APIContext` (cookies, locals, url, request) |

### Grouping Actions

Use nested objects for logical grouping:

```ts
export const server = {
  user: {
    update: defineAction({ /* ... */ }),
    delete: defineAction({ /* ... */ }),
  },
  post: {
    create: defineAction({ /* ... */ }),
    like: defineAction({ /* ... */ }),
  },
};
```

Client calls: `actions.user.update(...)`, `actions.post.like(...)`.

## Calling from the Client

Import `actions` in any client script or framework component:

```tsx
// LikeButton.tsx
import { actions } from "astro:actions";
import { useState } from "react";

export default function LikeButton({ postId }: { postId: string }) {
  const [likes, setLikes] = useState(0);
  const [error, setError] = useState<string | null>(null);

  async function handleClick() {
    const { data, error } = await actions.likePost({ postId });
    if (error) {
      setError(error.message);
      return;
    }
    setLikes(data.likes);
  }

  return (
    <div>
      <button onClick={handleClick}>Like ({likes})</button>
      {error && <p role="alert">{error}</p>}
    </div>
  );
}
```

Key API shape: every action call returns `{ data, error }` — **never throws** on the client. `error` is `ActionError | InputValidationError | undefined`.

### `.orThrow()` for Throwing Behavior

If you prefer try/catch:

```ts
try {
  const likes = await actions.likePost.orThrow({ postId });
} catch (err) {
  console.error(err);
}
```

## Calling from Server Code

Inside `.astro` components, endpoints, or other actions:

```astro
---
import { actions } from "astro:actions";

const result = await Astro.callAction(actions.likePost, { postId: "abc" });
if (result.error) return Astro.rewrite("/error");
---
```

`Astro.callAction` passes the current request context through so `locals`, cookies, etc. flow naturally.

## Form Handling

Actions integrate natively with HTML forms. Set `accept: "form"` and post the form directly to the action endpoint:

```astro
---
// src/pages/new-post.astro
import { actions } from "astro:actions";
---
<form method="POST" action={actions.createComment}>
  <input type="hidden" name="postId" value="abc-123" />
  <textarea name="body" required minlength="1" maxlength="1000"></textarea>
  <button type="submit">Comment</button>
</form>
```

After submission, Astro:
1. Parses the form body.
2. Runs the Zod input schema.
3. Calls the handler.
4. On success, returns a 303 redirect to the same URL.
5. On error, redirects back with the error attached to a URL-safe cookie.

### Reading the Result on the Next Render

```astro
---
import { actions } from "astro:actions";

const result = Astro.getActionResult(actions.createComment);
---
{result?.error && <p role="alert">{result.error.message}</p>}
{result?.data && <p>Comment posted!</p>}
```

`getActionResult` returns `{ data, error } | undefined`. It only resolves immediately after a form submission to this page.

### Enhancing Forms with Progressive JS

```tsx
// CommentForm.tsx
import { actions, isInputError } from "astro:actions";

export default function CommentForm({ postId }: { postId: string }) {
  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const { data, error } = await actions.createComment(formData);

    if (isInputError(error)) {
      // Validation error — error.fields has per-field messages
      Object.entries(error.fields).forEach(([field, msg]) => console.error(field, msg));
    } else if (error) {
      alert(error.message);
    } else {
      e.currentTarget.reset();
    }
  }

  return (
    <form onSubmit={onSubmit}>
      <input type="hidden" name="postId" value={postId} />
      <textarea name="body" required />
      <button type="submit">Comment</button>
    </form>
  );
}
```

The form still works **without JavaScript** — the `method="POST" action={actions.createComment}` degrades gracefully.

## Error Handling

Throw `ActionError` from the handler for structured errors:

```ts
import { ActionError } from "astro:actions";

handler: async ({ postId }, { locals }) => {
  if (!locals.user) {
    throw new ActionError({ code: "UNAUTHORIZED", message: "Login required" });
  }
  const post = await db.post.findUnique({ where: { id: postId } });
  if (!post) {
    throw new ActionError({ code: "NOT_FOUND", message: "Post missing" });
  }
  // ...
}
```

### Available Error Codes (maps to HTTP status)

| Code | HTTP |
|------|------|
| `BAD_REQUEST` | 400 |
| `UNAUTHORIZED` | 401 |
| `FORBIDDEN` | 403 |
| `NOT_FOUND` | 404 |
| `TIMEOUT` | 408 |
| `CONFLICT` | 409 |
| `UNPROCESSABLE_CONTENT` | 422 |
| `TOO_MANY_REQUESTS` | 429 |
| `INTERNAL_SERVER_ERROR` | 500 |

### Client-Side Discrimination

```ts
import { isInputError, ActionError } from "astro:actions";

const { data, error } = await actions.doThing(input);
if (isInputError(error)) {
  // Zod validation failed — error.fields is Record<string, string[]>
} else if (error?.code === "UNAUTHORIZED") {
  window.location.href = "/login";
} else if (error) {
  toast.error(error.message);
} else {
  console.log(data);
}
```

## Auth and Middleware Integration

Middleware populates `Astro.locals`; actions read it via the `context` parameter:

```ts
// src/middleware.ts
export const onRequest = defineMiddleware(async (context, next) => {
  const sessionCookie = context.cookies.get("session")?.value;
  context.locals.user = sessionCookie ? await verifySession(sessionCookie) : null;
  return next();
});
```

```ts
// src/actions/index.ts
handler: async (input, context) => {
  if (!context.locals.user) {
    throw new ActionError({ code: "UNAUTHORIZED" });
  }
  // context.locals.user is typed — see 08-middleware.md for the type setup
}
```

## Common Pitfalls

- **Actions in a prerendered page** — the form submit POST has nowhere to go. Either remove `prerender = true` from that page, or switch to a dedicated endpoint.
- **Forgetting `astro:schema`** — some guides still use `import { z } from "zod"`. Astro wraps Zod in its own package to ensure version parity; import from `astro:schema`.
- **Returning non-serializable data** (functions, classes) — action results are JSON-serialized.
- **Large file uploads through `accept: "form"`** — Astro buffers the whole body. For big uploads, use an endpoint with streaming instead.
- **Forgetting that actions run per-call, not per-page** — each call is its own request with its own middleware run; check performance implications.
- **Relying on stateful closures in the handler** — each request gets a fresh execution in most adapters (especially serverless). Use a real store.
