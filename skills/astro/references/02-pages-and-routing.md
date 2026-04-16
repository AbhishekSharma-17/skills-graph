# Pages & Routing

> Source: https://docs.astro.build/en/guides/routing/

Astro uses **file-based routing**: every file in `src/pages/` that produces HTML becomes a URL. There is no route config file.

## File Types That Become Routes

| File | URL (example) | Notes |
|------|---------------|-------|
| `src/pages/index.astro` | `/` | |
| `src/pages/about.astro` | `/about` | |
| `src/pages/blog/index.astro` | `/blog` | |
| `src/pages/blog/[slug].astro` | `/blog/:slug` | Dynamic segment |
| `src/pages/posts/[...path].astro` | `/posts/*` | Rest parameter |
| `src/pages/index.md` | `/` | Markdown page |
| `src/pages/index.mdx` | `/` | MDX page |
| `src/pages/rss.xml.ts` | `/rss.xml` | Endpoint, non-HTML |
| `src/pages/api/user.ts` | `/api/user` | Endpoint |

Files prefixed with `_` are **ignored** (`_draft.astro`, `_components/`) — a handy way to co-locate helpers without exposing them as routes.

## Static Routes

```astro
---
// src/pages/about.astro
const teamSize = 12;
---
<html>
  <body>
    <h1>About us</h1>
    <p>We are {teamSize} people.</p>
  </body>
</html>
```

This renders at build time to `dist/about/index.html`.

## Dynamic Routes — Static (SSG) Mode

Dynamic routes require `getStaticPaths()` when `output` is `"static"` (the default) OR the page is `export const prerender = true`.

```astro
---
// src/pages/blog/[slug].astro
import { getCollection } from "astro:content";

export async function getStaticPaths() {
  const posts = await getCollection("blog");
  return posts.map((post) => ({
    params: { slug: post.slug },
    props: { post },
  }));
}

const { post } = Astro.props;
const { Content } = await post.render();
---
<article>
  <h1>{post.data.title}</h1>
  <Content />
</article>
```

**Key rules:**

- `params` values must be strings, numbers, or `undefined`. Everything else goes in `props`.
- `params` keys **must match** the filename brackets exactly: `[slug]` → `params.slug`.
- Return an empty array for routes with no paths (build won't fail).
- `getStaticPaths()` runs once per build — it is **not** per-request.

### Multiple Dynamic Segments

`src/pages/[lang]/blog/[slug].astro`:

```ts
export async function getStaticPaths() {
  const posts = await getCollection("blog");
  const langs = ["en", "fr", "de"];
  return langs.flatMap((lang) =>
    posts.map((post) => ({
      params: { lang, slug: post.slug },
      props: { post, lang },
    }))
  );
}
```

### Rest Parameters (`[...path]`)

Catch-all for arbitrary depth:

```ts
// src/pages/docs/[...path].astro
export async function getStaticPaths() {
  return [
    { params: { path: "getting-started" } },              // /docs/getting-started
    { params: { path: "guides/auth" } },                  // /docs/guides/auth
    { params: { path: undefined } },                      // /docs
  ];
}
```

`params.path` is either the matched string or `undefined` for the bare `/docs`.

## Dynamic Routes — On-Demand (SSR) Mode

When `output: "server"` and the page is **not** marked `prerender`, Astro generates the HTML per request. You **omit** `getStaticPaths` entirely:

```astro
---
// src/pages/users/[id].astro  (SSR)
import { getUser } from "~/server/users";

const { id } = Astro.params;
const user = await getUser(id);

if (!user) return Astro.redirect("/404");
---
<h1>{user.name}</h1>
```

`Astro.params` is typed by Astro's route type generation.

## Route Priority

When multiple routes could match the same URL, Astro picks in this order:

1. Static routes (`/about.astro`) beat dynamic (`[slug].astro`).
2. Dynamic routes beat rest routes (`[...path].astro`).
3. Within the same type, more specific paths win (`/blog/post` beats `/blog/[slug]`).

## Accessing Route Data

Inside a `.astro` component:

```astro
---
const { slug } = Astro.params;           // dynamic segments
const { post } = Astro.props;             // passed from getStaticPaths or framework
const url = Astro.url;                    // URL object for current request
const referer = Astro.request.headers.get("referer");
const clientIp = Astro.clientAddress;     // SSR only
---
```

## Redirects

### Static Redirects (config)

```js
// astro.config.mjs
export default defineConfig({
  redirects: {
    "/old-blog": "/blog",
    "/legacy/[slug]": "/blog/[slug]",
    "/gone": { status: 410, destination: "/404" },
  },
});
```

Static redirects are emitted as HTML meta-refresh in static output, and use adapter-native redirects (e.g. `_redirects` on Cloudflare) when available.

### Programmatic Redirects (SSR)

```astro
---
if (!Astro.cookies.get("session")) {
  return Astro.redirect("/login", 302);
}
---
```

`Astro.redirect(path, status?)` returns a `Response`. Status defaults to 302.

### `Astro.rewrite` (internal rerouting)

Unlike `redirect`, `rewrite` renders a different page **under the same URL** — no client round-trip.

```astro
---
const user = await getUser(Astro.params.id);
if (!user) return Astro.rewrite("/404");
---
```

## Pagination

Astro provides a built-in `paginate()` helper inside `getStaticPaths`:

```astro
---
// src/pages/blog/[page].astro
import { getCollection } from "astro:content";

export async function getStaticPaths({ paginate }) {
  const posts = await getCollection("blog");
  return paginate(posts, { pageSize: 10 });
}

const { page } = Astro.props;
// page.data, page.start, page.end, page.total, page.url.prev, page.url.next
---
<h1>Blog page {page.currentPage} of {page.lastPage}</h1>
<ul>
  {page.data.map((p) => <li><a href={`/blog/${p.slug}`}>{p.data.title}</a></li>)}
</ul>
{page.url.prev && <a href={page.url.prev}>Previous</a>}
{page.url.next && <a href={page.url.next}>Next</a>}
```

## 404 and 500 Pages

Create `src/pages/404.astro` and `src/pages/500.astro`:

```astro
---
// src/pages/404.astro
---
<html>
  <body>
    <h1>404 — Not Found</h1>
    <a href="/">Home</a>
  </body>
</html>
```

In SSR mode, the `500.astro` page is rendered when middleware or a page throws an unhandled error.

## Per-Route Render Mode (Hybrid)

Opt any page in or out of prerendering:

```astro
---
// src/pages/dashboard.astro — force SSR even in a mostly-static project
export const prerender = false;
---
```

```astro
---
// src/pages/about.astro — force static even in an SSR project
export const prerender = true;
---
```

See `06-rendering-modes.md` for the full matrix.

## Common Pitfalls

- **Forgetting `getStaticPaths` in SSG mode** → build error: `Dynamic route missing required getStaticPaths()`.
- **Returning non-string params** (dates, numbers via `.toString()` missing) → silent mismatch at render time.
- **Using `Astro.redirect` with `output: "static"`** → only works in prerender-exempt pages (i.e., SSR-enabled routes).
- **Placing helpers in `src/pages/`** (e.g., `src/pages/_lib/utils.ts`) that Astro tries to render → prefix with `_` or move to `src/lib/`.
- **Case-sensitive slugs** on macOS/Linux deployments that were tested on Windows — Astro preserves case, but some filesystems don't.
