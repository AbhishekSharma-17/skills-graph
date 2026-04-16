# Endpoints & API Routes

> Source: https://docs.astro.build/en/guides/endpoints/

Endpoints are `.ts` / `.js` files in `src/pages/` that export HTTP method handlers. They're the lowest-level tool in Astro — use them for JSON APIs, webhooks, file downloads, RSS feeds, sitemaps, anything non-HTML. (For form submissions and type-safe RPC between your own client and server, prefer **Actions** — see `07-actions.md`.)

## Table of Contents

- [File Types](#file-types)
- [Basic JSON Endpoint](#basic-json-endpoint)
- [Multiple Methods](#multiple-methods-in-one-file)
- [Static vs On-Demand Endpoints](#static-vs-on-demand-endpoints)
- [Dynamic Endpoints](#dynamic-endpoints)
- [Reading Request Body](#reading-request-body)
- [Setting Cookies](#setting-cookies-from-endpoints)
- [Webhooks](#webhooks-pattern)
- [Streaming Responses](#streaming-responses)
- [File Downloads](#file-downloads)
- [RSS Feed Example](#rss-feed-example)
- [Dynamic OG Image Generation](#dynamic-og-image-generation)
- [CORS for Public APIs](#cors-for-public-apis)
- [Endpoint vs Action](#endpoint-vs-action--when-to-use-which)
- [Common Pitfalls](#common-pitfalls)

## File Types

| Filename | URL |
|----------|-----|
| `src/pages/api/health.ts` | `/api/health` |
| `src/pages/rss.xml.ts` | `/rss.xml` |
| `src/pages/og/[slug].png.ts` | `/og/:slug.png` |
| `src/pages/robots.txt.ts` | `/robots.txt` |

The extension embedded in the filename (`.xml`, `.png`, `.txt`) is preserved in the URL. The `.ts`/`.js` extension does not.

## Basic JSON Endpoint

```ts
// src/pages/api/health.ts
import type { APIRoute } from "astro";

export const GET: APIRoute = ({ params, request }) => {
  return new Response(
    JSON.stringify({ status: "ok", ts: Date.now() }),
    { status: 200, headers: { "content-type": "application/json" } },
  );
};
```

Every method handler gets an `APIContext` and returns a `Response`.

## Multiple Methods in One File

```ts
// src/pages/api/posts.ts
import type { APIRoute } from "astro";

export const GET: APIRoute = async ({ url }) => {
  const page = Number(url.searchParams.get("page") ?? 1);
  const posts = await db.post.findMany({ skip: (page - 1) * 10, take: 10 });
  return Response.json(posts);
};

export const POST: APIRoute = async ({ request, locals }) => {
  if (!locals.user) return new Response("Unauthorized", { status: 401 });
  const body = await request.json();
  const post = await db.post.create({ data: { ...body, authorId: locals.user.id } });
  return Response.json(post, { status: 201 });
};

export const DELETE: APIRoute = async ({ url, locals }) => {
  if (locals.user?.role !== "admin") return new Response("Forbidden", { status: 403 });
  const id = url.searchParams.get("id");
  await db.post.delete({ where: { id } });
  return new Response(null, { status: 204 });
};
```

Supported methods: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `OPTIONS`, `ALL` (catch-all).

## Static vs On-Demand Endpoints

Endpoints follow the same rules as pages:

```ts
// Prerendered — runs at build time only. Good for RSS feeds and sitemaps.
export const prerender = true;

export const GET: APIRoute = async () => {
  const posts = await getCollection("blog");
  return new Response(buildRssXml(posts), { headers: { "content-type": "application/rss+xml" } });
};
```

Prerendered endpoints only support `GET`. `POST/PUT/DELETE` require on-demand rendering.

## Dynamic Endpoints

```ts
// src/pages/api/posts/[id].ts
import type { APIRoute } from "astro";

export const GET: APIRoute = async ({ params }) => {
  const post = await db.post.findUnique({ where: { id: params.id } });
  if (!post) return new Response("Not found", { status: 404 });
  return Response.json(post);
};
```

For static/prerendered dynamic endpoints, same `getStaticPaths` rules as pages:

```ts
export const prerender = true;

export async function getStaticPaths() {
  const posts = await getCollection("blog");
  return posts.map((p) => ({ params: { id: p.id } }));
}

export const GET: APIRoute = ({ params }) => { /* ... */ };
```

## Reading Request Body

```ts
// JSON body
const data = await request.json();

// Form data
const form = await request.formData();
const name = form.get("name");

// Raw text
const text = await request.text();

// Streams (for large uploads)
const reader = request.body?.getReader();
```

## Setting Cookies from Endpoints

```ts
export const POST: APIRoute = async ({ request, cookies }) => {
  const { email, password } = await request.json();
  const session = await createSession(email, password);

  cookies.set("session", session.token, {
    httpOnly: true,
    secure: true,
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 7,
  });

  return Response.json({ ok: true });
};
```

## Webhooks Pattern

Handle incoming webhook requests. Always verify signatures:

```ts
// src/pages/api/webhooks/stripe.ts
import type { APIRoute } from "astro";
import Stripe from "stripe";

const stripe = new Stripe(import.meta.env.STRIPE_SECRET_KEY);
const endpointSecret = import.meta.env.STRIPE_WEBHOOK_SECRET;

export const POST: APIRoute = async ({ request }) => {
  const sig = request.headers.get("stripe-signature");
  const body = await request.text();

  let event;
  try {
    event = stripe.webhooks.constructEvent(body, sig!, endpointSecret);
  } catch (err) {
    return new Response(`Webhook Error: ${(err as Error).message}`, { status: 400 });
  }

  switch (event.type) {
    case "checkout.session.completed":
      await fulfillOrder(event.data.object);
      break;
    case "invoice.payment_failed":
      await handleFailedPayment(event.data.object);
      break;
  }

  return new Response(null, { status: 200 });
};
```

## Streaming Responses

```ts
export const GET: APIRoute = async () => {
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      for (let i = 0; i < 10; i++) {
        controller.enqueue(encoder.encode(`data: chunk-${i}\n\n`));
        await new Promise((r) => setTimeout(r, 200));
      }
      controller.close();
    },
  });

  return new Response(stream, {
    headers: {
      "content-type": "text/event-stream",
      "cache-control": "no-cache",
      connection: "keep-alive",
    },
  });
};
```

Works for SSE, streaming LLM responses, large file exports.

## File Downloads

```ts
export const GET: APIRoute = async ({ url }) => {
  const buffer = await generatePdf(url.searchParams.get("id"));
  return new Response(buffer, {
    headers: {
      "content-type": "application/pdf",
      "content-disposition": `attachment; filename="report.pdf"`,
    },
  });
};
```

## RSS Feed Example

Using the official integration `@astrojs/rss`:

```bash
npm install @astrojs/rss
```

```ts
// src/pages/rss.xml.ts
import rss from "@astrojs/rss";
import { getCollection } from "astro:content";
import type { APIRoute } from "astro";

export const GET: APIRoute = async (context) => {
  const posts = await getCollection("blog", ({ data }) => !data.draft);
  return rss({
    title: "My Blog",
    description: "Posts about web dev",
    site: context.site!,
    items: posts.map((post) => ({
      title: post.data.title,
      pubDate: post.data.publishDate,
      description: post.data.description,
      link: `/blog/${post.id}/`,
    })),
  });
};
```

## Dynamic OG Image Generation

```ts
// src/pages/og/[slug].png.ts
import type { APIRoute } from "astro";
import { ImageResponse } from "@vercel/og";          // or @cloudflare/pages-plugin-vercel-og
import { getEntry } from "astro:content";

export const GET: APIRoute = async ({ params }) => {
  const post = await getEntry("blog", params.slug!);
  return new ImageResponse(
    {
      type: "div",
      props: {
        style: { display: "flex", fontSize: 64, background: "#0f172a", color: "white", padding: 80 },
        children: post?.data.title ?? "",
      },
    },
    { width: 1200, height: 630 },
  );
};
```

## CORS for Public APIs

```ts
export const OPTIONS: APIRoute = () =>
  new Response(null, {
    status: 204,
    headers: {
      "access-control-allow-origin": "*",
      "access-control-allow-methods": "GET, POST",
      "access-control-allow-headers": "content-type",
    },
  });

export const GET: APIRoute = () =>
  Response.json(
    { items: [] },
    { headers: { "access-control-allow-origin": "*" } },
  );
```

## Endpoint vs Action — When to Use Which

| Use Case | Pick |
|----------|------|
| Form submission from Astro's own pages | **Action** (type-safe, progressive enhancement) |
| RPC-style call from your own React/Vue island | **Action** |
| Webhook receiver (Stripe, GitHub, Linear) | **Endpoint** |
| Public JSON API for third parties | **Endpoint** |
| RSS, sitemap, robots.txt | **Endpoint** (prerendered) |
| File downloads / streaming | **Endpoint** |
| OG image generation | **Endpoint** (dynamic `.png.ts`) |

## Common Pitfalls

- **Returning plain objects** — you must return a `Response`. Use `Response.json(obj)` or `new Response(JSON.stringify(obj), { headers: { "content-type": "application/json" } })`.
- **Missing `content-type`** on JSON responses → browsers try to render the JSON, fetch clients may parse wrong.
- **Forgetting `prerender = true`** for RSS/sitemap endpoints in a `server`-output project → they run per-request instead of building once.
- **Case-insensitive method handling** — Astro matches the exact HTTP method uppercase. Lowercase method exports (`get`, `post`) no longer work since 4.x.
- **Calling Astro's request.json() twice** → the body is a stream, can only be consumed once.
- **Writing to `Astro.response`** inside endpoints — that API exists only in `.astro` components. Endpoints mutate the `Response` object directly.
