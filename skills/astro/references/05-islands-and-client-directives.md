# Islands Architecture & Client Directives

> Source: https://docs.astro.build/en/concepts/islands/ and https://docs.astro.build/en/reference/directives-reference/#client-directives

## The Idea

Traditional JS frameworks hydrate the **entire page**: every element becomes a React/Vue component with associated JS even if it's just static text. Astro inverts this: pages are **static HTML by default**, and small **islands** of interactivity are opted in per component.

Benefits:

- Less JS shipped → faster TTI, better LCP/INP.
- Islands are **isolated**: each one has its own JS bundle that loads independently.
- **Progressive enhancement** — the page works before any JS executes.

## Using Framework Components

Install the integration:

```bash
npx astro add react            # or vue, svelte, solid, preact, lit, alpinejs
```

Import and use:

```astro
---
// src/pages/index.astro
import Counter from "../components/Counter.jsx";
import Nav from "../components/Nav.astro";
---
<Nav />
<Counter />                      <!-- Server-rendered HTML only, no JS -->
<Counter client:load />          <!-- Becomes an island -->
```

**Key insight:** `<Counter />` WITHOUT a client directive is still rendered — but only on the server. The user sees the HTML; no JS is shipped for it.

## Client Directives

Add one of these attributes to any framework component to ship JS and hydrate it:

### `client:load`

Hydrate immediately on page load. Use for **above-the-fold interactive components** that need to be responsive instantly.

```astro
<Counter client:load />
```

- Bundle: downloaded and executed ASAP, blocks interactive readiness.
- **Cost:** adds bytes to the critical path.

### `client:idle`

Hydrate when the browser's main thread is idle (`requestIdleCallback`, or `setTimeout` fallback). Use for **medium-priority** interactive components.

```astro
<Dropdown client:idle />
<Dropdown client:idle={{ timeout: 2000 }} />     <!-- Force hydrate after 2s -->
```

- Bundle: downloaded async, executed when idle.
- **Cost:** delays interactivity slightly, but never blocks first paint.

### `client:visible`

Hydrate when the component scrolls into view (`IntersectionObserver`). Use for **below-the-fold** components (comments, related-posts carousels, etc.).

```astro
<CommentSection client:visible />
<CommentSection client:visible={{ rootMargin: "200px" }} />   <!-- Preload 200px before visible -->
```

- **Cost:** zero until the user scrolls there.

### `client:media`

Hydrate only when a CSS media query matches. Use for **responsive-only components** (mobile nav, desktop sidebar).

```astro
<MobileNav client:media="(max-width: 768px)" />
<DesktopSidebar client:media="(min-width: 1024px)" />
```

- Bundle: not downloaded on the other viewport at all.

### `client:only`

**Skip server rendering entirely.** The component is rendered only on the client. Use when:

- The component depends on browser-only APIs (`window`, `document`, `localStorage`).
- The component is part of a third-party library that fails to SSR.

```astro
<ChartJsWidget client:only="react" />           <!-- Specify the framework! -->
<SvelteWidget client:only="svelte" />
```

⚠️ `client:only` requires the framework name because Astro can't infer it from the component alone. A fallback is rendered during SSR (a `<div>` placeholder by default).

### Fallback Content

Show placeholder HTML until the island hydrates:

```astro
<Counter client:only="react">
  <p slot="fallback">Loading counter…</p>
</Counter>
```

## Choosing a Directive — A Quick Decision Table

| Component | Recommendation |
|-----------|----------------|
| Above-the-fold nav/header with JS behavior | `client:load` |
| Interactive widget below the fold | `client:visible` |
| Heavy carousel, comments, chat | `client:visible` or `client:idle` |
| Mobile-only hamburger menu | `client:media="(max-width: 768px)"` |
| Depends on `window`/`localStorage` at init | `client:only="framework"` |
| Purely presentational (no state, no events) | **No directive** — let Astro render it server-only |

## Passing Props

Props are serialized to JSON at the island boundary. This means:

- **OK:** strings, numbers, booleans, plain objects, arrays, `Date` (via `toJSON`).
- **Not OK:** functions, class instances (with methods), `Map`, `Set`, DOM elements.

```astro
---
import Counter from "../components/Counter.jsx";
const initialCount = 5;
---
<Counter client:load initialCount={initialCount} />
```

If you need complex logic, move it into the framework component itself or fetch it inside the component.

## Framework Components Can Nest — But With a Rule

You can use framework components inside Astro components freely. Framework components **can** accept Astro components **only** as children/slots, not as props:

```astro
<!-- ✅ OK — Astro as children -->
<ReactLayout client:load>
  <AstroHero />
</ReactLayout>

<!-- ❌ Not OK — Astro component as prop -->
<ReactCard client:load header={<AstroHeader />} />
```

## Sharing State Between Islands

By design, each island is isolated — independent React trees don't share state. Options:

1. **Nanostores** — tiny framework-agnostic stores. Official pattern; see `@nanostores/react`, `@nanostores/vue`, etc.

```ts
// src/stores/cart.ts
import { atom } from "nanostores";
export const cartCount = atom(0);
```

```tsx
// Counter.tsx
import { useStore } from "@nanostores/react";
import { cartCount } from "../stores/cart";
export default function Counter() {
  const count = useStore(cartCount);
  return <button onClick={() => cartCount.set(count + 1)}>{count}</button>;
}
```

All islands that import `cartCount` share state.

2. **Custom events on `window`** — simple pub/sub.
3. **URL / cookies** — persist across full page loads.

## Server Islands (Astro 5+)

Server Islands defer **slow server-rendered** components, streaming them in after the static shell. Add `server:defer` to an `.astro` component:

```astro
---
// src/components/Recommendations.astro
const items = await slowRecommendationService();
---
<ul>{items.map((i) => <li>{i.title}</li>)}</ul>
```

```astro
---
import Recommendations from "../components/Recommendations.astro";
import Static from "../components/Static.astro";
---
<Static />
<Recommendations server:defer>
  <div slot="fallback">Loading recommendations…</div>
</Recommendations>
```

On request:
1. Astro streams the shell + static content immediately.
2. The deferred component renders as a placeholder.
3. A separate request fetches the rendered HTML in the background.
4. Astro swaps the placeholder for the real content.

Server islands require `output: "server"` or `output: "hybrid"` and an adapter.

## Common Pitfalls

- **Using `client:load` for everything** — defeats Astro's purpose. Audit with `astro check` and aim to demote to `client:visible` or remove directives entirely.
- **Forgetting `client:only="framework"`** for truly client-only components → runtime error about missing framework name.
- **Expecting context/providers to cross island boundaries** — a React context set in one island is not visible in another. Use nanostores or props.
- **Passing functions as props** → silent JSON stringification drops them. Move the function definition into the island.
- **Mixing `client:visible` with zero content** — IntersectionObserver needs a visible element to observe. Ensure the island has layout.
- **Using browser APIs in framework components during SSR** → errors like `ReferenceError: window is not defined`. Wrap with `useEffect` (React) / `onMount` (Svelte), or switch to `client:only`.
