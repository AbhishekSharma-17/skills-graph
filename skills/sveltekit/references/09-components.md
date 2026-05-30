# SvelteKit — Components & Template Syntax

> Source: [svelte.dev/docs/svelte](https://svelte.dev/docs/svelte)

## Table of Contents

- [Component Basics](#component-basics)
- [Props with $props](#props-with-props)
- [Snippets](#snippets)
- [Children](#children)
- [Template Syntax](#template-syntax)
- [Bindings](#bindings)
- [Actions](#actions)
- [Component Lifecycle](#component-lifecycle)
- [Context API](#context-api)
- [Special Elements](#special-elements)

## Component Basics

Svelte components are `.svelte` files with three optional sections:

```svelte
<!-- Button.svelte -->
<script lang="ts">
  // Logic (runs per-instance)
  let { label, onclick } = $props();
  let count = $state(0);
</script>

<!-- Markup (template) -->
<button {onclick}>
  {label}: {count}
</button>

<!-- Styles (scoped by default) -->
<style>
  button {
    padding: 0.5rem 1rem;
    border-radius: 4px;
  }
</style>
```

### Using Components

```svelte
<script>
  import Button from '$lib/components/Button.svelte';
</script>

<Button label="Click me" onclick={() => console.log('clicked')} />
```

## Props with $props

Declare and destructure props:

```svelte
<script lang="ts">
  interface Props {
    title: string;
    description?: string;
    variant?: 'primary' | 'secondary';
    disabled?: boolean;
    onclick?: (e: MouseEvent) => void;
    children?: import('svelte').Snippet;
  }

  let {
    title,
    description = '',
    variant = 'primary',
    disabled = false,
    onclick,
    children
  }: Props = $props();
</script>
```

### Rest Props

Spread remaining props onto an element:

```svelte
<script>
  let { class: className, children, ...rest } = $props();
</script>

<div class={className} {...rest}>
  {@render children?.()}
</div>
```

## Snippets

Snippets define reusable markup blocks within a component. They replace Svelte 4 slots:

### Declaring Snippets

```svelte
{#snippet greeting(name)}
  <h2>Hello, {name}!</h2>
{/snippet}

{@render greeting('Alice')}
{@render greeting('Bob')}
```

### Snippets as Props

```svelte
<!-- Card.svelte -->
<script>
  import type { Snippet } from 'svelte';

  interface Props {
    header: Snippet;
    footer?: Snippet;
    children: Snippet;
  }

  let { header, footer, children }: Props = $props();
</script>

<div class="card">
  <div class="card-header">{@render header()}</div>
  <div class="card-body">{@render children()}</div>
  {#if footer}
    <div class="card-footer">{@render footer()}</div>
  {/if}
</div>
```

```svelte
<!-- Usage -->
<Card>
  {#snippet header()}
    <h2>Card Title</h2>
  {/snippet}

  <p>Card body content goes here.</p>

  {#snippet footer()}
    <button>Action</button>
  {/snippet}
</Card>
```

### Typed Snippets with Parameters

```svelte
<!-- DataTable.svelte -->
<script lang="ts" generics="T">
  import type { Snippet } from 'svelte';

  interface Props {
    items: T[];
    row: Snippet<[T, number]>;
    empty?: Snippet;
  }

  let { items, row, empty }: Props = $props();
</script>

{#if items.length === 0}
  {@render empty?.()}
{:else}
  {#each items as item, i}
    {@render row(item, i)}
  {/each}
{/if}
```

```svelte
<DataTable items={users}>
  {#snippet row(user, index)}
    <tr>
      <td>{index + 1}</td>
      <td>{user.name}</td>
      <td>{user.email}</td>
    </tr>
  {/snippet}

  {#snippet empty()}
    <p>No users found.</p>
  {/snippet}
</DataTable>
```

## Children

Content between component tags becomes the `children` snippet:

```svelte
<!-- Layout.svelte -->
<script>
  let { children } = $props();
</script>

<main>
  {@render children()}
</main>

<!-- Usage -->
<Layout>
  <h1>Page Title</h1>
  <p>Page content</p>
</Layout>
```

## Template Syntax

### Conditionals

```svelte
{#if condition}
  <p>Truthy</p>
{:else if otherCondition}
  <p>Other</p>
{:else}
  <p>Falsy</p>
{/if}
```

### Each Blocks

```svelte
{#each items as item, index (item.id)}
  <li>{index}: {item.name}</li>
{:else}
  <li>No items</li>
{/each}
```

The `(item.id)` key expression enables efficient DOM updates when the list changes.

### Await Blocks

```svelte
{#await promise}
  <p>Loading...</p>
{:then data}
  <p>Result: {data}</p>
{:catch error}
  <p>Error: {error.message}</p>
{/await}

<!-- Short form when you don't need the loading state -->
{#await promise then data}
  <p>{data}</p>
{/await}
```

### HTML Rendering

```svelte
<!-- Render raw HTML (careful: XSS risk with user input) -->
{@html markdownToHtml(content)}
```

### Const Declarations

```svelte
{#each items as item}
  {@const total = item.price * item.quantity}
  <p>{item.name}: ${total.toFixed(2)}</p>
{/each}
```

### Debug

```svelte
<!-- Pause debugger when values change -->
{@debug user, items}
```

## Bindings

Two-way binding between a variable and a DOM element:

### Input Bindings

```svelte
<script>
  let name = $state('');
  let agreed = $state(false);
  let color = $state('#ff0000');
  let selected = $state('a');
  let volume = $state(50);
</script>

<input bind:value={name} />
<input type="checkbox" bind:checked={agreed} />
<input type="color" bind:value={color} />
<input type="range" bind:value={volume} min="0" max="100" />

<select bind:value={selected}>
  <option value="a">A</option>
  <option value="b">B</option>
</select>

<textarea bind:value={name}></textarea>
```

### Element Bindings

```svelte
<script>
  let div: HTMLDivElement;
  let width = $state(0);
  let height = $state(0);
</script>

<div bind:this={div} bind:clientWidth={width} bind:clientHeight={height}>
  {width} x {height}
</div>
```

### Component Bindings

Use `$bindable()` in child components (see Runes reference).

## Actions

Reusable element-level behavior via the `use:` directive:

```ts
// src/lib/actions/clickOutside.ts
export function clickOutside(node: HTMLElement, callback: () => void) {
  function handleClick(event: MouseEvent) {
    if (!node.contains(event.target as Node)) {
      callback();
    }
  }

  document.addEventListener('click', handleClick, true);

  return {
    destroy() {
      document.removeEventListener('click', handleClick, true);
    }
  };
}
```

```svelte
<script>
  import { clickOutside } from '$lib/actions/clickOutside';
  let showDropdown = $state(false);
</script>

<div use:clickOutside={() => showDropdown = false}>
  {#if showDropdown}
    <ul class="dropdown">...</ul>
  {/if}
</div>
```

### Action Lifecycle

```ts
export function myAction(node: HTMLElement, param: string) {
  // Setup — called when element is mounted
  console.log('mounted with', param);

  return {
    update(newParam: string) {
      // Called when the parameter changes
      console.log('updated to', newParam);
    },
    destroy() {
      // Cleanup — called when element is removed
      console.log('destroyed');
    }
  };
}
```

## Component Lifecycle

```svelte
<script>
  import { onMount, onDestroy, tick, untrack } from 'svelte';

  onMount(() => {
    // Runs after component mounts in the browser
    const interval = setInterval(update, 1000);

    return () => {
      // Cleanup on unmount
      clearInterval(interval);
    };
  });

  onDestroy(() => {
    // Runs when component is destroyed (server + client)
  });

  // tick() — wait for pending DOM updates
  async function handleInput() {
    value = 'new';
    await tick(); // DOM is now updated
    input.selectionStart = 0;
  }

  // untrack() — read reactive values without creating dependencies
  $effect(() => {
    const tracked = count; // This creates a dependency
    const untracked = untrack(() => otherValue); // This does not
  });
</script>
```

## Context API

Share data between parent and child components without prop drilling:

```svelte
<!-- Parent.svelte -->
<script>
  import { setContext } from 'svelte';

  const theme = $state({ color: 'blue', mode: 'dark' });
  setContext('theme', theme);
</script>

<!-- DeepChild.svelte -->
<script>
  import { getContext } from 'svelte';

  const theme = getContext('theme');
</script>

<div style:color={theme.color}>{theme.mode}</div>
```

Context is available during component initialization only. For reactive context, pass reactive state:

```svelte
<script>
  import { setContext } from 'svelte';

  let count = $state(0);
  setContext('counter', {
    get count() { return count; },
    increment() { count++; }
  });
</script>
```

## Special Elements

```svelte
<!-- Render on the <head> -->
<svelte:head>
  <title>My Page</title>
  <meta name="description" content="..." />
</svelte:head>

<!-- Bind to window events -->
<svelte:window bind:innerWidth={w} onkeydown={handleKey} />

<!-- Bind to document -->
<svelte:document onvisibilitychange={handleVisibility} />

<!-- Bind to body -->
<svelte:body onmouseenter={handleHover} />

<!-- Dynamic component -->
<svelte:component this={currentComponent} {data} />

<!-- Self-referencing (recursive) -->
<svelte:self count={count - 1} />

<!-- Target a specific element for mounting -->
<svelte:element this={tag} />
```

## Common Pitfalls

1. **Using slots instead of snippets** — Slots are deprecated in Svelte 5. Use `{#snippet}` and `{@render}`.
2. **Forgetting `(key)` in each blocks** — Without a key, DOM elements are reused by index, causing bugs with stateful children
3. **`{@html}` with user input** — Raw HTML rendering is an XSS risk. Always sanitize user-provided HTML.
4. **Context outside initialization** — `setContext` and `getContext` must be called during component initialization, not in event handlers or effects

## Related

- Runes & Reactivity → `02-runes-reactivity.md`
- Styling → `10-styling.md`
- Form Actions → `04-form-actions.md`
