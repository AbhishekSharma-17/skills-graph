# Astro Components

> Source: https://docs.astro.build/en/basics/astro-components/

`.astro` is Astro's native component format. It is HTML-first: the output has **zero JavaScript** by default. Framework components (React/Vue/Svelte/Solid) are invoked from `.astro` components and hydrated explicitly — see `05-islands-and-client-directives.md`.

## Anatomy

```astro
---
// Component Script (frontmatter) — runs on the server only
// Has access to Node APIs, env vars, the filesystem, databases, etc.

import Layout from "../layouts/Default.astro";
import Card from "../components/Card.astro";

const { title = "Untitled" } = Astro.props;
const items = await fetchItems();
---
<!-- Component Template — JSX-like HTML -->
<Layout title={title}>
  <h1>{title}</h1>
  <ul>
    {items.map((item) => <Card title={item.title} />)}
  </ul>
</Layout>

<style>
  /* Scoped CSS — Astro adds a hash attribute to every selector */
  h1 { color: hotpink; }
</style>
```

Three sections, separated by `---` fences:

1. **Component Script** — TypeScript/JavaScript run at build time (SSG) or per-request (SSR). Never ships to the browser.
2. **Template** — HTML + JSX-style expressions.
3. **`<style>` / `<script>`** — scoped CSS and optional client-side JS.

## Props

Props are passed as HTML attributes and received via `Astro.props`:

```astro
---
// src/components/Card.astro
interface Props {
  title: string;
  href?: string;
  variant?: "primary" | "secondary";
}
const { title, href, variant = "primary" } = Astro.props;
---
<a href={href} class:list={["card", variant]}>{title}</a>
```

**Why declare `Props` interface?** It gives you autocomplete and type-checking everywhere this component is used — Astro's editor tooling reads it.

## Expressions

Anywhere inside the template:

```astro
---
const name = "Astro";
const items = ["a", "b", "c"];
const loggedIn = false;
---
<h1>Hello, {name}</h1>                                 <!-- Simple interpolation -->
<p>{1 + 2}</p>                                         <!-- Any JS expression -->
<ul>{items.map((i) => <li>{i}</li>)}</ul>              <!-- Map over arrays -->
{loggedIn ? <a href="/logout">Log out</a> : <a href="/login">Log in</a>}
{loggedIn && <p>Welcome back</p>}

<!-- Fragments -->
<>
  <p>One</p>
  <p>Two</p>
</>
```

### `set:html` and `set:text`

- `<div set:html={rawHtml} />` — inject raw HTML (skip escaping). **Only use for trusted content.**
- `<h1 set:text={title} />` — force text-only insertion even for strings that look like HTML.

### Dynamic Tags

```astro
---
const Tag = Astro.props.as ?? "div";
---
<Tag class="wrapper"><slot /></Tag>
```

The variable must start with a capital letter; Astro treats lowercase identifiers as HTML tags.

## Slots

Astro components accept children via `<slot />`:

```astro
---
// src/components/Card.astro
---
<article class="card">
  <slot name="header" />
  <div class="body"><slot /></div>
  <slot name="footer" />
</article>
```

```astro
---
import Card from "../components/Card.astro";
---
<Card>
  <h2 slot="header">Title</h2>
  <p>Main content goes in the default slot.</p>
  <small slot="footer">Footer line</small>
</Card>
```

### Slot Fallback Content

```astro
<slot>
  <p>Default content if nothing is passed in.</p>
</slot>
```

### `<slot is:inline />`

Avoid Astro wrapping slot contents in any additional element. Useful when the parent is counting direct children (grid layouts).

## Scoped CSS

Styles in `<style>` blocks are **scoped to the component** by default — Astro adds a `data-astro-cid-xxxx` attribute to elements and rewrites selectors:

```astro
<style>
  h1 { color: red; }               /* Applies only inside this component */
</style>
```

### Global Styles

```astro
<style is:global>
  body { margin: 0; }
</style>
```

Or import a global stylesheet:

```astro
---
import "../styles/global.css";
---
```

### CSS Variables from Frontmatter

Pass dynamic values into CSS via `define:vars`:

```astro
---
const color = "hotpink";
---
<style define:vars={{ color }}>
  h1 { color: var(--color); }
</style>
```

### `class:list` Directive

Conditionally apply classes — accepts strings, objects, or arrays:

```astro
<div class:list={[
  "base",
  { active: isActive, disabled: !isActive },
  ["a", "b"],
]} />
```

## Client-Side Scripts

```astro
<script>
  // Bundled + processed by Vite. Runs on every page where this component appears.
  import { track } from "../lib/analytics";
  document.querySelector("button")?.addEventListener("click", () => track("click"));
</script>
```

### Script Directives

| Directive | Behavior |
|-----------|----------|
| *(default)* | Processed, bundled, deduplicated across pages |
| `is:inline` | Inline the literal script tag (no bundling) |
| `is:raw` | Same as inline but no processing |
| `define:vars={...}` | Expose frontmatter values to the script |

```astro
---
const apiUrl = "/api/user";
---
<script define:vars={{ apiUrl }}>
  fetch(apiUrl).then((r) => r.json()).then(console.log);
</script>
```

## Astro API Reference (`Astro.*`)

Inside any `.astro` component script:

| Property | Description |
|----------|-------------|
| `Astro.props` | Props passed from parent |
| `Astro.params` | Dynamic route params |
| `Astro.request` | Standard `Request` object |
| `Astro.response` | Mutable response (headers, status) — for setting cookies / headers on SSR |
| `Astro.cookies` | `get/set/delete/has` with signing support |
| `Astro.url` | `URL` object for the current page |
| `Astro.site` | Value of `site` from `astro.config.mjs` |
| `Astro.generator` | Astro version string (for meta generator tag) |
| `Astro.redirect(path, status?)` | Returns a redirect `Response` |
| `Astro.rewrite(path)` | Internally rewrite to another route |
| `Astro.clientAddress` | Client IP (SSR only) |
| `Astro.locals` | Typed per-request context — written by middleware |
| `Astro.slots.render(name)` | Imperative slot rendering inside frontmatter |
| `Astro.self` | Reference to this component (for recursion) |

## Async Components

Top-level `await` is supported — frontmatter is async:

```astro
---
const data = await fetch("https://api.example.com/items").then((r) => r.json());
---
<ul>
  {data.map((item) => <li>{item.name}</li>)}
</ul>
```

## Recursion

```astro
---
// src/components/Tree.astro
const { node } = Astro.props;
---
<li>
  {node.label}
  {node.children?.length > 0 && (
    <ul>
      {node.children.map((child) => <Astro.self node={child} />)}
    </ul>
  )}
</li>
```

## Scoped `<style>` and Child Components

By default, scoped styles **do not cross component boundaries**. To target child components, use `:global()`:

```astro
<style>
  .wrapper :global(.child-class) { color: red; }
</style>
```

Or use CSS Modules / a global stylesheet.

## Common Pitfalls

- **Forgetting the `---` fences** on a pure-HTML component is fine; but any frontmatter script requires them.
- **Using `return` inside the template** — you can only `return` from the frontmatter (e.g., `Astro.redirect`).
- **Passing non-serializable props to framework components** (functions, class instances) — they must serialize to JSON at the island boundary.
- **Using browser-only APIs in the frontmatter** (`document`, `window`) — frontmatter runs on the server. Move to `<script>` or a framework component with `client:load`.
- **Mutating `Astro.props`** — they're frozen; treat as read-only.
- **Ordering of `<style>` blocks** — later styles in the same component override earlier ones, but scoped styles from different components should not collide unless you use `:global`.
