# SvelteKit — Runes & Reactivity (Svelte 5)

> Source: [svelte.dev/docs/svelte](https://svelte.dev/docs/svelte) | Svelte v5.55.x

## Table of Contents

- [$state](#state)
- [$derived](#derived)
- [$effect](#effect)
- [$props](#props)
- [$bindable](#bindable)
- [$inspect](#inspect)
- [Reactive Proxies](#reactive-proxies)
- [Reactive Files (.svelte.ts)](#reactive-files-sveltets)
- [Stores vs Runes](#stores-vs-runes)
- [Common Patterns](#common-patterns)

## Overview

Svelte 5 replaced the implicit `$:` reactive declarations with explicit reactive primitives called **runes**. Runes are compiler instructions prefixed with `$` that declare how values are reactive, derived, or effectful. They provide fine-grained reactivity — when a `$state` value changes, only the specific `$derived` values and `$effect`s that depend on it update.

## $state

Declares reactive state. When the value changes, anything that reads it (UI, derived values, effects) updates automatically.

```svelte
<script>
  let count = $state(0);
  let name = $state('world');
  let items = $state<string[]>([]);
</script>

<button onclick={() => count++}>
  Clicked {count} times
</button>
```

### Deep Reactivity

Objects and arrays become deeply reactive proxies. Mutations at any depth trigger updates:

```svelte
<script>
  let user = $state({
    name: 'Alice',
    address: { city: 'Portland' }
  });

  let todos = $state([
    { text: 'Learn Svelte', done: false }
  ]);
</script>

<!-- These all trigger updates: -->
<button onclick={() => user.name = 'Bob'}>Rename</button>
<button onclick={() => user.address.city = 'Seattle'}>Move</button>
<button onclick={() => todos.push({ text: 'New', done: false })}>Add</button>
<button onclick={() => todos[0].done = true}>Complete</button>
```

### $state.raw

For large objects or data you don't mutate, use `$state.raw` to avoid proxy overhead. Reassignment (not mutation) triggers updates:

```svelte
<script>
  let data = $state.raw(hugeDataset);

  function refresh() {
    // This triggers an update (reassignment):
    data = await fetchData();

    // This does NOT trigger an update (mutation):
    // data.items.push(newItem);  // Won't work with raw
  }
</script>
```

### $state.snapshot

Get a plain (non-reactive) snapshot of a state proxy, useful for logging, serialization, or passing to external libraries:

```svelte
<script>
  let form = $state({ name: '', email: '' });

  function submit() {
    const plain = $state.snapshot(form);
    console.log(plain); // Regular object, not a Proxy
    fetch('/api', { body: JSON.stringify(plain) });
  }
</script>
```

## $derived

Computes values from reactive state. Automatically recalculates when dependencies change. Memoized — only recomputes when inputs actually differ.

```svelte
<script>
  let width = $state(10);
  let height = $state(20);

  let area = $derived(width * height);
  let isLarge = $derived(area > 100);
</script>

<p>Area: {area}, Large: {isLarge}</p>
```

### $derived.by

For complex derivations requiring multi-line logic:

```svelte
<script>
  let items = $state([3, 1, 4, 1, 5, 9]);

  let stats = $derived.by(() => {
    const sorted = [...items].sort((a, b) => a - b);
    const sum = items.reduce((a, b) => a + b, 0);
    return {
      min: sorted[0],
      max: sorted[sorted.length - 1],
      avg: sum / items.length,
      count: items.length
    };
  });
</script>

<p>Min: {stats.min}, Max: {stats.max}, Avg: {stats.avg.toFixed(1)}</p>
```

### Key Rule

`$derived` is for **pure computations** — no side effects. If you need side effects, use `$effect`.

## $effect

Runs side effects when dependencies change. Tracks dependencies automatically like `$derived`.

```svelte
<script>
  let count = $state(0);

  $effect(() => {
    document.title = `Count: ${count}`;
  });

  $effect(() => {
    console.log('Count changed to', count);
    // Cleanup function (optional):
    return () => {
      console.log('Cleaning up previous effect');
    };
  });
</script>
```

### When Effects Run

- Effects run after the DOM updates (post-paint)
- They re-run when any reactive value read inside them changes
- They run in components only (not during SSR)

### $effect.pre

Runs before the DOM updates. Useful for measuring DOM state before a change:

```svelte
<script>
  let messages = $state<string[]>([]);
  let div: HTMLDivElement;

  $effect.pre(() => {
    // Check scroll position before messages update the DOM
    messages; // read to track
    if (div) {
      const isAtBottom = div.scrollHeight - div.scrollTop === div.clientHeight;
      if (isAtBottom) {
        // After DOM update, scroll will auto-adjust
        tick().then(() => div.scrollTo(0, div.scrollHeight));
      }
    }
  });
</script>
```

### Anti-Patterns

```svelte
<script>
  let count = $state(0);

  // BAD: Don't use $effect to sync state — use $derived instead
  // let doubled = $state(0);
  // $effect(() => { doubled = count * 2; });

  // GOOD:
  let doubled = $derived(count * 2);

  // BAD: Don't use $effect for data fetching in SvelteKit — use load functions
  // $effect(() => { fetch(`/api/data/${id}`).then(...) });

  // GOOD: Use +page.server.ts load function instead
</script>
```

## $props

Declares component props. Replaces Svelte 4's `export let`:

```svelte
<!-- Button.svelte -->
<script>
  let {
    variant = 'primary',
    size = 'md',
    disabled = false,
    onclick,
    children
  } = $props();
</script>

<button class="{variant} {size}" {disabled} {onclick}>
  {@render children()}
</button>
```

### TypeScript Props

```svelte
<script lang="ts">
  interface Props {
    title: string;
    count?: number;
    onchange?: (value: string) => void;
  }

  let { title, count = 0, onchange }: Props = $props();
</script>
```

### Rest Props

```svelte
<script>
  let { class: className, children, ...rest } = $props();
</script>

<div class={className} {...rest}>
  {@render children()}
</div>
```

## $bindable

Marks a prop as two-way bindable by parent components:

```svelte
<!-- TextInput.svelte -->
<script>
  let { value = $bindable('') } = $props();
</script>

<input bind:value />

<!-- Parent.svelte -->
<script>
  import TextInput from './TextInput.svelte';
  let name = $state('');
</script>

<TextInput bind:value={name} />
<p>Name is: {name}</p>
```

## $inspect

Development-only debugging rune. Logs reactive values when they change (stripped in production):

```svelte
<script>
  let count = $state(0);
  let doubled = $derived(count * 2);

  $inspect(count, doubled);
  // Logs: "init", 0, 0
  // After count changes: "update", 1, 2

  $inspect(count).with(console.trace); // Custom handler
</script>
```

## Reactive Proxies

`$state` wraps objects and arrays in Proxy wrappers for deep reactivity:

```svelte
<script>
  let list = $state([1, 2, 3]);

  // All these trigger UI updates:
  list.push(4);          // Array methods work
  list[0] = 10;          // Index assignment works
  list.splice(1, 1);     // Splice works
  list.length = 0;       // Truncation works
</script>
```

### Proxy Caveats

```svelte
<script>
  let obj = $state({ a: 1 });

  // Identity comparison changes with proxies:
  console.log(obj === obj); // true (same proxy)

  // But spreading creates a non-reactive copy:
  let copy = { ...obj };   // Plain object, not reactive

  // Use $state.snapshot for serialization:
  JSON.stringify($state.snapshot(obj));

  // Class instances need $state on fields:
  class Counter {
    count = $state(0);
    doubled = $derived(this.count * 2);
    increment() { this.count++; }
  }
</script>
```

## Reactive Files (.svelte.ts)

Runes work in `.svelte.ts` and `.svelte.js` files, enabling shared reactive state:

```ts
// src/lib/counter.svelte.ts
export function createCounter(initial = 0) {
  let count = $state(initial);
  let doubled = $derived(count * 2);

  return {
    get count() { return count; },
    get doubled() { return doubled; },
    increment() { count++; },
    reset() { count = initial; }
  };
}
```

```svelte
<!-- Any component -->
<script>
  import { createCounter } from '$lib/counter.svelte';
  const counter = createCounter(5);
</script>

<button onclick={counter.increment}>
  {counter.count} (doubled: {counter.doubled})
</button>
```

### Shared Global State

```ts
// src/lib/auth.svelte.ts
let user = $state<User | null>(null);

export const auth = {
  get user() { return user; },
  get isLoggedIn() { return user !== null; },
  login(u: User) { user = u; },
  logout() { user = null; }
};
```

## Stores vs Runes

Svelte 5 runes replace the need for stores in most cases:

| Feature | Stores (Svelte 4) | Runes (Svelte 5) |
|---------|-------------------|-------------------|
| Syntax | `$store` prefix | `$state()`, `$derived()` |
| Location | Anywhere | `.svelte` and `.svelte.ts` files |
| Reactivity | Subscribe/unsubscribe | Automatic tracking |
| SSR safety | Manual cleanup | Handled by compiler |

Stores still work in Svelte 5 but are considered legacy for new code.

## Common Patterns

### Form State

```svelte
<script>
  let form = $state({ email: '', password: '' });
  let isValid = $derived(form.email.includes('@') && form.password.length >= 8);
</script>

<input bind:value={form.email} />
<input type="password" bind:value={form.password} />
<button disabled={!isValid}>Submit</button>
```

### Debounced Search

```svelte
<script>
  let query = $state('');
  let results = $state<string[]>([]);

  $effect(() => {
    const q = query;
    if (!q) { results = []; return; }
    const timer = setTimeout(async () => {
      results = await search(q);
    }, 300);
    return () => clearTimeout(timer);
  });
</script>
```

## Common Pitfalls

1. **Using `$effect` for derived state** — If you're setting state inside an effect, you almost certainly want `$derived` instead
2. **Forgetting `.svelte.ts` extension** — Runes only work in `.svelte`, `.svelte.ts`, and `.svelte.js` files
3. **Mutating `$state.raw`** — Raw state only reacts to reassignment, not mutation
4. **Circular dependencies** — `$derived` values that depend on each other will cause infinite loops

## Related

- Components → `09-components.md`
- Loading Data → `03-loading-data.md`
- Styling → `10-styling.md`
