# SvelteKit — API Routes

> Source: [svelte.dev/docs/kit/routing#server](https://svelte.dev/docs/kit/routing#server)

## Table of Contents

- [Overview](#overview)
- [Basic Endpoints](#basic-endpoints)
- [HTTP Methods](#http-methods)
- [Request Handling](#request-handling)
- [Response Helpers](#response-helpers)
- [Streaming Responses](#streaming-responses)
- [Error Handling](#error-handling)
- [CORS](#cors)
- [Content Negotiation](#content-negotiation)

## Overview

API routes (endpoints) are defined in `+server.ts` files. They export functions named after HTTP methods (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `OPTIONS`, `HEAD`) and return a `Response` object. API routes have no associated page component — they return data directly.

## Basic Endpoints

```ts
// src/routes/api/health/+server.ts
import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async () => {
  return json({ status: 'ok', timestamp: Date.now() });
};
```

### File Placement

```
src/routes/
├── api/
│   ├── posts/
│   │   ├── +server.ts           → GET/POST /api/posts
│   │   └── [id]/
│   │       └── +server.ts       → GET/PUT/DELETE /api/posts/:id
│   └── auth/
│       ├── login/
│       │   └── +server.ts       → POST /api/auth/login
│       └── logout/
│           └── +server.ts       → POST /api/auth/logout
```

## HTTP Methods

Export a function for each HTTP method your endpoint supports:

```ts
// src/routes/api/posts/+server.ts
import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { db } from '$lib/server/db';

export const GET: RequestHandler = async ({ url }) => {
  const limit = Number(url.searchParams.get('limit') ?? '20');
  const offset = Number(url.searchParams.get('offset') ?? '0');

  const posts = await db.post.findMany({ take: limit, skip: offset });
  return json(posts);
};

export const POST: RequestHandler = async ({ request, locals }) => {
  if (!locals.user) throw error(401, 'Unauthorized');

  const body = await request.json();
  const post = await db.post.create({
    data: { ...body, authorId: locals.user.id }
  });

  return json(post, { status: 201 });
};
```

```ts
// src/routes/api/posts/[id]/+server.ts
import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async ({ params }) => {
  const post = await db.post.findUnique({ where: { id: params.id } });
  if (!post) throw error(404, 'Not found');
  return json(post);
};

export const PUT: RequestHandler = async ({ params, request, locals }) => {
  if (!locals.user) throw error(401, 'Unauthorized');

  const body = await request.json();
  const post = await db.post.update({
    where: { id: params.id },
    data: body
  });

  return json(post);
};

export const DELETE: RequestHandler = async ({ params, locals }) => {
  if (!locals.user) throw error(401, 'Unauthorized');

  await db.post.delete({ where: { id: params.id } });
  return new Response(null, { status: 204 });
};
```

## Request Handling

### JSON Body

```ts
export const POST: RequestHandler = async ({ request }) => {
  const body = await request.json();
  // body is the parsed JSON
};
```

### Form Data

```ts
export const POST: RequestHandler = async ({ request }) => {
  const data = await request.formData();
  const name = data.get('name') as string;
  const file = data.get('file') as File;
};
```

### URL Parameters

```ts
export const GET: RequestHandler = async ({ url, params }) => {
  // Route params: /api/users/[id] → params.id
  const userId = params.id;

  // Query params: /api/users?sort=name → url.searchParams
  const sort = url.searchParams.get('sort');
  const page = Number(url.searchParams.get('page') ?? '1');
};
```

### Headers

```ts
export const GET: RequestHandler = async ({ request }) => {
  const auth = request.headers.get('authorization');
  const contentType = request.headers.get('content-type');
};
```

### Cookies

```ts
export const POST: RequestHandler = async ({ cookies }) => {
  const session = cookies.get('session');

  cookies.set('token', 'abc123', {
    path: '/',
    httpOnly: true,
    secure: true,
    sameSite: 'lax',
    maxAge: 60 * 60 * 24
  });

  cookies.delete('old-cookie', { path: '/' });
};
```

## Response Helpers

```ts
import { json, text, error, redirect } from '@sveltejs/kit';

// JSON response
return json({ data: 'value' });
return json({ data: 'value' }, { status: 201 });
return json({ data: 'value' }, {
  headers: { 'X-Custom': 'header' }
});

// Text response
return text('Hello, world!');

// Custom response
return new Response(buffer, {
  headers: {
    'Content-Type': 'application/pdf',
    'Content-Disposition': 'attachment; filename="report.pdf"'
  }
});

// Error
throw error(404, 'Not found');
throw error(403, { message: 'Forbidden', code: 'AUTH_REQUIRED' });

// Redirect
throw redirect(301, '/new-location');
```

## Streaming Responses

### Server-Sent Events (SSE)

```ts
export const GET: RequestHandler = async () => {
  const stream = new ReadableStream({
    start(controller) {
      const encoder = new TextEncoder();
      let count = 0;

      const interval = setInterval(() => {
        const data = JSON.stringify({ count: count++, time: Date.now() });
        controller.enqueue(encoder.encode(`data: ${data}\n\n`));

        if (count > 100) {
          clearInterval(interval);
          controller.close();
        }
      }, 1000);
    }
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive'
    }
  });
};
```

### Streaming JSON

```ts
export const GET: RequestHandler = async () => {
  const stream = new ReadableStream({
    async start(controller) {
      const encoder = new TextEncoder();

      for await (const chunk of generateLargeDataset()) {
        controller.enqueue(encoder.encode(JSON.stringify(chunk) + '\n'));
      }

      controller.close();
    }
  });

  return new Response(stream, {
    headers: { 'Content-Type': 'application/x-ndjson' }
  });
};
```

## Error Handling

```ts
import { error, json } from '@sveltejs/kit';

export const POST: RequestHandler = async ({ request }) => {
  let body: unknown;

  try {
    body = await request.json();
  } catch {
    throw error(400, 'Invalid JSON body');
  }

  if (!isValidPayload(body)) {
    throw error(422, 'Validation failed');
  }

  try {
    const result = await processData(body);
    return json(result, { status: 201 });
  } catch (err) {
    throw error(500, 'Internal server error');
  }
};
```

## CORS

Add CORS headers for cross-origin access:

```ts
// src/routes/api/public/+server.ts
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization'
};

export const OPTIONS: RequestHandler = async () => {
  return new Response(null, { headers: corsHeaders });
};

export const GET: RequestHandler = async () => {
  return json({ data: 'public' }, { headers: corsHeaders });
};
```

## Content Negotiation

A route can have both `+page.svelte` and `+server.ts`. SvelteKit handles content negotiation:

- Browser requests (HTML) → `+page.svelte`
- `fetch` requests or Accept: application/json → `+server.ts`

```ts
// src/routes/items/+page.server.ts — serves the page with load data
export const load = async () => ({ items: await getItems() });

// src/routes/items/+server.ts — serves JSON for API consumers
export const GET: RequestHandler = async () => {
  return json(await getItems());
};
```

## Common Pitfalls

1. **Forgetting to return a Response** — Every handler must return a `Response` object
2. **Using `+server.ts` with `+page.server.ts` actions** — You can't have POST in both; use form actions for page forms
3. **Not handling OPTIONS** — CORS preflight requests need an OPTIONS handler
4. **Throwing plain errors** — Use `throw error(status, message)` from `@sveltejs/kit`, not `throw new Error()`
5. **Blocking the event loop** — CPU-heavy work blocks the server; offload to workers or background jobs

## Related

- Form Actions → `04-form-actions.md`
- Hooks → `06-hooks.md`
- Loading Data → `03-loading-data.md`
