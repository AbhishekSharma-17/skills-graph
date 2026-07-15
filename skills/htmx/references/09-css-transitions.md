# htmx — CSS Transitions & Animation

> Source: [htmx.org/docs/#css_transitions](https://htmx.org/docs/#css_transitions) | Version: 2.0.x

## Table of Contents

- [How CSS Transitions Work in htmx](#how-css-transitions-work-in-htmx)
- [htmx CSS Classes](#htmx-css-classes)
- [Transition Lifecycle](#transition-lifecycle)
- [Fade In / Fade Out](#fade-in--fade-out)
- [Slide Transitions](#slide-transitions)
- [Swap & Settle Delays](#swap--settle-delays)
- [View Transitions API](#view-transitions-api)
- [Class Tools Extension](#class-tools-extension)
- [ID Stability for Transitions](#id-stability-for-transitions)
- [Common Animation Patterns](#common-animation-patterns)

## How CSS Transitions Work in htmx

htmx uses CSS transitions by leveraging the settle step between swapping content and applying final attribute values. The key mechanism:

1. Old content is removed and new content is inserted
2. htmx copies old attribute values onto new elements (matched by `id`)
3. New content gets the `htmx-settling` class
4. After the settle delay (default 20ms), htmx applies the new attribute values
5. The browser detects the attribute change and applies CSS transitions
6. The `htmx-settling` class is removed after settling

This means **matching `id` attributes** between old and new content is essential for transitions.

## htmx CSS Classes

htmx applies these CSS classes automatically during the request lifecycle:

| Class | Applied | Removed | Purpose |
|-------|---------|---------|---------|
| `htmx-request` | When request starts | When response received | Loading indicators, button disable styling |
| `htmx-swapping` | Before content swap | After swap completes | Exit animations |
| `htmx-settling` | After swap, before settle | After settle delay | Enter animations |
| `htmx-added` | On new elements after swap | After settle delay | First-time entrance effects |
| `htmx-indicator` | Always present | Never removed | Elements shown/hidden based on `htmx-request` |

### Default Indicator CSS

htmx injects this CSS automatically (disable with `htmx.config.includeIndicatorStyles = false`):

```css
.htmx-indicator {
    opacity: 0;
    transition: opacity 200ms ease-in;
}
.htmx-request .htmx-indicator,
.htmx-request.htmx-indicator {
    opacity: 1;
}
```

### Customizing CSS Class Names

```javascript
htmx.config.indicatorClass = 'htmx-indicator';    // default
htmx.config.requestClass = 'htmx-request';        // default
htmx.config.addedClass = 'htmx-added';            // default
htmx.config.settlingClass = 'htmx-settling';      // default
htmx.config.swappingClass = 'htmx-swapping';      // default
```

## Transition Lifecycle

```
Event fires → Request sent
  │
  ├── htmx-request class ADDED to trigger element
  │
  ▼
Response received
  │
  ├── htmx-request class REMOVED
  ├── htmx-swapping class ADDED to target
  │
  ▼
[swap delay] (hx-swap="... swap:300ms")
  │
  ├── Content swapped into DOM
  ├── htmx-swapping class REMOVED
  ├── htmx-added class ADDED to new elements
  ├── htmx-settling class ADDED to target
  ├── Old attribute values applied to matching elements (by id)
  │
  ▼
[settle delay] (default 20ms, or hx-swap="... settle:500ms")
  │
  ├── New attribute values applied → CSS TRANSITION TRIGGERS
  ├── htmx-settling class REMOVED
  ├── htmx-added class REMOVED
  │
  ▼
Done
```

## Fade In / Fade Out

### Fade In New Content

```css
.fade-in {
    opacity: 0;
}
.fade-in.htmx-settling {
    opacity: 1;
    transition: opacity 0.5s ease-in;
}
```

```html
<div id="content" class="fade-in"
     hx-get="/page"
     hx-swap="innerHTML settle:500ms">
    Content fades in
</div>
```

### Fade Out Before Swap

Use the `swapping` class with a swap delay:

```css
#content.htmx-swapping {
    opacity: 0;
    transition: opacity 0.3s ease-out;
}
```

```html
<div id="content"
     hx-get="/page"
     hx-swap="innerHTML swap:300ms settle:300ms">
    Content fades out, then new content fades in
</div>
```

### Full Fade Out → Fade In

```css
.fade-transition {
    transition: opacity 0.3s ease;
}
.fade-transition.htmx-swapping {
    opacity: 0;
}
.fade-transition.htmx-settling {
    opacity: 1;
}
```

```html
<div id="content" class="fade-transition"
     hx-get="/next"
     hx-swap="innerHTML swap:300ms">
</div>
```

## Slide Transitions

### Slide Down (New Content)

```css
.slide-down {
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.5s ease-out;
}
.slide-down.htmx-settling {
    max-height: 500px;
}
```

### Slide In From Right

```css
.slide-in {
    transform: translateX(100%);
    transition: transform 0.4s ease-out;
}
.slide-in.htmx-settling {
    transform: translateX(0);
}
```

### Element-Level Transitions (Using IDs)

When swapping a specific element with `outerHTML`, give both old and new the same `id`:

```html
<!-- Current DOM -->
<div id="card-42" class="card" style="opacity: 1;">
    <h3>Old Title</h3>
</div>
```

```html
<!-- Server response -->
<div id="card-42" class="card" style="opacity: 1;">
    <h3>New Title</h3>
</div>
```

```css
.card {
    transition: all 0.3s ease;
}
```

htmx copies the old element's inline styles onto the new element during swap, then applies the new styles during settle, triggering the CSS transition.

## Swap & Settle Delays

### Swap Delay

Time between receiving the response and performing the swap. Use for exit animations:

```html
<!-- 500ms for exit animation before swapping -->
<div hx-get="/page" hx-swap="innerHTML swap:500ms">...</div>
```

### Settle Delay

Time after swap before applying final attribute values. Increase for smoother entrance transitions:

```html
<!-- 300ms settle delay for entrance animation -->
<div hx-get="/page" hx-swap="innerHTML settle:300ms">...</div>
```

### Combined Pattern

```html
<!-- 300ms exit → swap → 500ms entrance -->
<div hx-get="/page" hx-swap="outerHTML swap:300ms settle:500ms">...</div>
```

## View Transitions API

The View Transitions API provides browser-native animated transitions between DOM states.

### Per-Request

```html
<div hx-get="/page" hx-swap="innerHTML transition:true">
    Smooth cross-fade
</div>
```

### Global

```html
<meta name="htmx-config" content='{"globalViewTransitions": true}'>
```

Or via JavaScript:

```javascript
htmx.config.globalViewTransitions = true;
```

### Customizing View Transitions

```css
/* Default cross-fade */
::view-transition-old(root) {
    animation: 300ms ease-out fade-out;
}
::view-transition-new(root) {
    animation: 300ms ease-in fade-in;
}

@keyframes fade-out {
    from { opacity: 1; }
    to { opacity: 0; }
}
@keyframes fade-in {
    from { opacity: 0; }
    to { opacity: 1; }
}
```

### Named View Transitions

Use `view-transition-name` for per-element transitions:

```css
#hero-image {
    view-transition-name: hero;
}
::view-transition-old(hero) {
    animation: 400ms ease-out slide-out;
}
::view-transition-new(hero) {
    animation: 400ms ease-in slide-in;
}
```

### Canceling View Transitions

```javascript
document.addEventListener('htmx:beforeTransition', function(event) {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        event.preventDefault();
    }
});
```

## Class Tools Extension

The `class-tools` extension provides timed class toggling:

```html
<body hx-ext="class-tools">
    <!-- Add class after 1s, remove after 3s -->
    <div classes="add highlight:1s, remove highlight:3s">
        Temporarily highlighted
    </div>

    <!-- Toggle class every 2s -->
    <div classes="toggle pulse:2s">
        Pulsing element
    </div>
</body>
```

## ID Stability for Transitions

CSS transitions between old and new content require stable `id` attributes:

```html
<!-- Server returns elements with SAME IDs as current DOM -->

<!-- Current DOM -->
<div id="user-card" style="background: blue; transition: background 0.5s;">
    <h3>Alice</h3>
</div>

<!-- Response (same id, different style) -->
<div id="user-card" style="background: green;">
    <h3>Alice (Updated)</h3>
</div>
<!-- htmx copies old style, then applies new → transition fires -->
```

Without matching `id`s, there's no way to link old and new elements, so no transition occurs.

## Common Animation Patterns

### Loading Spinner

```css
.htmx-indicator {
    display: none;
}
.htmx-request .htmx-indicator {
    display: inline-block;
}
.htmx-request .htmx-hide-on-request {
    display: none;
}
```

```html
<button hx-get="/data" hx-indicator="#spinner">
    <span class="htmx-hide-on-request">Load Data</span>
    <span id="spinner" class="htmx-indicator">
        <svg class="spinner">...</svg>
    </span>
</button>
```

### Skeleton Loading

```html
<div hx-get="/content" hx-trigger="load" hx-swap="outerHTML">
    <div class="skeleton-line"></div>
    <div class="skeleton-line short"></div>
    <div class="skeleton-block"></div>
</div>
```

### Staggered List Items

```css
.list-item {
    opacity: 0;
    transform: translateY(10px);
    transition: all 0.3s ease;
}
.list-item.htmx-settling {
    opacity: 1;
    transform: translateY(0);
}
/* Stagger with nth-child */
.list-item:nth-child(2) { transition-delay: 0.1s; }
.list-item:nth-child(3) { transition-delay: 0.2s; }
.list-item:nth-child(4) { transition-delay: 0.3s; }
```

### Delete with Fade Out

```css
tr.htmx-swapping {
    opacity: 0;
    transition: opacity 0.5s ease-out;
}
```

```html
<tr>
    <td>Item</td>
    <td>
        <button hx-delete="/item/1"
                hx-target="closest tr"
                hx-swap="outerHTML swap:500ms">
            Delete
        </button>
    </td>
</tr>
```

### Progress Bar Animation

```html
<div hx-get="/job/status"
     hx-trigger="load delay:500ms"
     hx-swap="outerHTML"
     hx-target="this">
    <div class="progress-bar">
        <div class="progress-fill" id="fill"
             style="width: 0%; transition: width 0.5s ease;">
        </div>
    </div>
</div>
```

Server updates the width style, and the transition animates it:

```html
<div hx-get="/job/status"
     hx-trigger="load delay:500ms"
     hx-swap="outerHTML">
    <div class="progress-bar">
        <div class="progress-fill" id="fill" style="width: 65%;">
        </div>
    </div>
</div>
```
