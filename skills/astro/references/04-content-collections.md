# Content Collections

> Source: https://docs.astro.build/en/guides/content-collections/

Content Collections are Astro's first-class system for organizing and querying local content (Markdown, MDX, JSON, YAML) or remote content (CMS, APIs) with **type-safe schemas**. In Astro 5+, collections are built on the **Content Layer**, which replaced the legacy `src/content/` folder-only API and added pluggable loaders.

## Table of Contents

- [Defining a Collection](#defining-a-collection)
- [Built-in Loaders](#built-in-loaders)
- [Querying Content](#querying-content)
- [Rendering Content](#rendering-content)
- [Custom Loaders](#custom-loaders)
- [Live Content Collections (v5.10+)](#live-content-collections-v510)
- [Common Pitfalls](#common-pitfalls)

## Defining a Collection

Create `src/content/config.ts` (or `src/content.config.ts` — both work):

```ts
// src/content.config.ts
import { defineCollection, z } from "astro:content";
import { glob, file } from "astro/loaders";

const blog = defineCollection({
  // Loader picks up the files and hands Astro the raw data
  loader: glob({ pattern: "**/*.{md,mdx}", base: "./src/content/blog" }),
  // Schema validates every entry at build time
  schema: z.object({
    title: z.string(),
    description: z.string().max(160),
    publishDate: z.coerce.date(),
    author: z.string().default("Anonymous"),
    tags: z.array(z.string()).default([]),
    draft: z.boolean().default(false),
    heroImage: z.string().optional(),
  }),
});

const authors = defineCollection({
  loader: file("./src/content/authors.json"),
  schema: z.object({
    id: z.string(),
    name: z.string(),
    twitter: z.string().optional(),
    bio: z.string(),
  }),
});

export const collections = { blog, authors };
```

`z` is a re-exported Zod. All Zod validators work — discriminated unions, refinements, transforms, etc. See `zod` skill for schema patterns.

### Using `image()` for Optimized Images

```ts
import { defineCollection, z } from "astro:content";

const blog = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/blog" }),
  schema: ({ image }) => z.object({
    title: z.string(),
    heroImage: image(),           // Resolves to optimized, hashed image
    heroAlt: z.string(),
  }),
});
```

In a Markdown file:

```md
---
title: "My post"
heroImage: "./hero.jpg"
heroAlt: "A sunset"
---
```

Then render:

```astro
---
import { Image } from "astro:assets";
const { heroImage, heroAlt } = post.data;
---
<Image src={heroImage} alt={heroAlt} />
```

## Built-in Loaders

Astro ships two loaders in `astro/loaders`:

### `glob()` — multi-file collections

```ts
import { glob } from "astro/loaders";

loader: glob({
  pattern: "**/*.{md,mdx}",         // Glob pattern
  base: "./src/content/blog",        // Root to scan
  generateId: ({ entry }) => entry,  // Optional custom ID
});
```

The ID defaults to the file path relative to `base`, minus the extension. `posts/hello-world.md` → id `posts/hello-world`.

### `file()` — single-file collection

```ts
import { file } from "astro/loaders";

loader: file("./src/content/authors.json");                // JSON array of objects
loader: file("./src/content/authors.yaml");                // YAML array
loader: file("./src/content/data.json", {
  parser: (text) => JSON.parse(text).items,                // Custom parser
});
```

Each top-level item must have an `id` field (or provide `parser` that injects one).

## Querying Content

Use the `astro:content` module inside any `.astro` / `.ts` file:

```astro
---
import { getCollection, getEntry, getEntries, render } from "astro:content";

// All entries, optionally filtered
const posts = await getCollection("blog");
const published = await getCollection("blog", ({ data }) => !data.draft);

// Single entry by ID
const post = await getEntry("blog", "hello-world");

// Entry by reference (see References below)
const author = await getEntry(post.data.author);
---
```

`posts` is an array of entries shaped like:

```ts
type Entry = {
  id: string;            // Unique per collection
  slug: string;          // URL-friendly (glob loader)
  body: string;          // Raw Markdown/MDX
  collection: "blog";
  data: {
    title: string;
    description: string;
    // ...everything from the schema
  };
  render(): Promise<{ Content, headings, remarkPluginFrontmatter }>;
};
```

### Sorting and Filtering

```ts
const posts = (await getCollection("blog"))
  .filter((p) => !p.data.draft)
  .sort((a, b) => b.data.publishDate.valueOf() - a.data.publishDate.valueOf());
```

### Cross-Collection References

Reference one collection from another:

```ts
const blog = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/blog" }),
  schema: z.object({
    title: z.string(),
    author: reference("authors"),                 // ← reference helper
    related: z.array(reference("blog")).optional(),
  }),
});
```

Then hydrate the reference at render time:

```astro
---
import { getEntry, getEntries } from "astro:content";

const post = await getEntry("blog", "hello-world");
const author = await getEntry(post.data.author);
const related = await getEntries(post.data.related ?? []);
---
<h1>{post.data.title}</h1>
<p>By {author.data.name}</p>
```

## Rendering Content

### Markdown / MDX → HTML

```astro
---
import { getEntry, render } from "astro:content";

const post = await getEntry("blog", Astro.params.slug);
if (!post) return Astro.rewrite("/404");

const { Content, headings } = await render(post);
---
<article>
  <h1>{post.data.title}</h1>
  <nav aria-label="Table of contents">
    <ul>
      {headings.filter((h) => h.depth === 2).map((h) => (
        <li><a href={`#${h.slug}`}>{h.text}</a></li>
      ))}
    </ul>
  </nav>
  <Content />
</article>
```

- `Content` is a component — renders the Markdown/MDX body with all plugins applied.
- `headings` is an array of `{ depth, slug, text }` auto-generated by `remark-rehype`.

### JSON / YAML Collections

Non-Markdown collections don't have a `render()` step — use `data` directly:

```astro
---
import { getCollection } from "astro:content";
const authors = await getCollection("authors");
---
<ul>
  {authors.map((author) => (
    <li>
      <strong>{author.data.name}</strong>
      {author.data.twitter && <a href={`https://x.com/${author.data.twitter}`}>@{author.data.twitter}</a>}
    </li>
  ))}
</ul>
```

## Generating Pages from Collections

Standard pattern in `src/pages/blog/[...slug].astro`:

```astro
---
import { getCollection, render } from "astro:content";
import Layout from "~/layouts/BlogPost.astro";

export async function getStaticPaths() {
  const posts = await getCollection("blog", ({ data }) => !data.draft);
  return posts.map((post) => ({
    params: { slug: post.id },
    props: { post },
  }));
}

const { post } = Astro.props;
const { Content } = await render(post);
---
<Layout frontmatter={post.data}>
  <Content />
</Layout>
```

## Custom Loaders

A loader is any object implementing the `Loader` interface. Use this for CMS, databases, REST APIs:

```ts
// src/loaders/notion.ts
import type { Loader } from "astro/loaders";

export function notionLoader(databaseId: string): Loader {
  return {
    name: "notion-loader",
    load: async ({ store, meta, logger }) => {
      const lastRun = meta.get("lastRun");
      const pages = await fetchNotionPages(databaseId, { since: lastRun });

      for (const page of pages) {
        store.set({
          id: page.id,
          data: {
            title: page.properties.title,
            publishDate: page.properties.publishDate,
            body: page.body,
          },
        });
      }
      meta.set("lastRun", new Date().toISOString());
    },
  };
}
```

Use it in `content.config.ts`:

```ts
import { notionLoader } from "../loaders/notion";

const posts = defineCollection({
  loader: notionLoader("abc123"),
  schema: z.object({ title: z.string(), publishDate: z.coerce.date(), body: z.string() }),
});
```

`store` is a key-value store persisted across builds. `meta` is a small metadata store for incremental loading.

## Live Content Collections (v5.10+)

Live collections fetch **at request time** instead of at build. Ideal for dashboards and CMSs where rebuilds are impractical:

```ts
// src/live.config.ts
import { defineLiveCollection } from "astro:content";
import { liveNotionLoader } from "../loaders/notion-live";

export const collections = {
  announcements: defineLiveCollection({
    loader: liveNotionLoader("abc123"),
    schema: z.object({ title: z.string(), body: z.string() }),
  }),
};
```

Query at request time:

```astro
---
import { getLiveCollection } from "astro:content";
export const prerender = false;                // Required for live data
const announcements = await getLiveCollection("announcements");
---
```

Live collections became stable in Astro 6.

## Common Pitfalls

- **Editing `src/content.config.ts` without restarting** — legacy HMR sometimes misses the type regeneration. Run `astro sync` to force it.
- **Using the old `src/content/` folder-only API in Astro 5+** without a loader — works via legacy fallback but emits a deprecation warning. Move to explicit `glob()` loader.
- **Forgetting `z.coerce.date()` for Markdown dates** — YAML frontmatter dates arrive as strings, and `z.date()` will reject them.
- **Mutating `entry.data`** at runtime — treat as read-only. To derive values, do so in the template.
- **Referencing collections that don't exist yet** in `reference("slug")` — Astro can't verify cross-collection refs until both collections are defined.
- **Setting `draft: true` to hide posts in production** — Astro does NOT filter drafts automatically. You must filter inside `getCollection`.
