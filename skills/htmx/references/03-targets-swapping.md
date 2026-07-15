# htmx — Targets & Swapping

> Source: [htmx.org/docs/#swapping](https://htmx.org/docs/#swapping) | Version: 2.0.x

## Table of Contents

- [Targeting Overview](#targeting-overview)
- [Extended CSS Selectors](#extended-css-selectors)
- [Swap Strategies](#swap-strategies)
- [Swap Modifiers](#swap-modifiers)
- [Morphing Swaps](#morphing-swaps)
- [View Transitions API](#view-transitions-api)
- [Preserving Elements](#preserving-elements)
- [Response Selection](#response-selection)
- [Request Lifecycle & CSS Classes](#request-lifecycle--css-classes)
- [Common Patterns](#common-patterns)

## Targeting Overview

By default, htmx swaps content into the element that made the request. The `hx-target` attribute changes the destination:

```html
<!-- Default: swap into self -->
<div hx-get="/data">Replaced content goes here</div>

<!-- Target another element by ID -->
<button hx-get="/data" hx-target="#output">Load</button>
<div id="output">Content appears here</div>

<!-- Target inherited from parent -->
<div hx-target="#output">
    <button hx-get="/page1">Page 1</button>
    <button hx-get="/page2">Page 2</button>
</div>
<div id="output"></div>
```

## Extended CSS Selectors

htmx extends standard CSS selectors with relative positioning keywords:

### this

Targets the element itself (explicit version of the default).

```html
<div hx-get="/data" hx-target="this">Replaces own content</div>
```

### closest \<selector\>

Finds the nearest ancestor (including self) matching the selector.

```html
<tr>
    <td>Item</td>
    <td>
        <button hx-delete="/item/1" hx-target="closest tr" hx-swap="outerHTML">
            Delete Row
        </button>
    </td>
</tr>
```

### find \<selector\>

Finds the first descendant matching the selector.

```html
<div hx-target="find .output">
    <button hx-get="/data">Load</button>
    <div class="output">Content appears here</div>
</div>
```

### next \<selector\>

Scans forward in document order for the next element matching the selector.

```html
<button hx-get="/data" hx-target="next .results">Load</button>
<div class="results">Content appears here</div>
```

### previous \<selector\>

Scans backward in document order for the previous matching element.

```html
<div class="status">Status appears here</div>
<button hx-get="/status" hx-target="previous .status">Check</button>
```

### Combining Extended Selectors

```html
<!-- Find within closest ancestor -->
<button hx-get="/data" hx-target="closest .card">Load</button>

<!-- Target by ID (standard CSS) -->
<button hx-get="/data" hx-target="#specific-element">Load</button>
```

## Swap Strategies

### innerHTML (default)

Replaces the inner content of the target element.

```html
<div id="target"><p>Old content</p></div>
<!-- After swap: <div id="target"><p>New content</p></div> -->
```

### outerHTML

Replaces the entire target element including itself.

```html
<div id="target"><p>Old</p></div>
<!-- After swap: the whole div is replaced with the response -->
```

### afterbegin

Inserts response as the first child of the target.

```html
<!-- Before: <ul><li>Existing</li></ul> -->
<!-- After:  <ul><li>New</li><li>Existing</li></ul> -->
<ul id="list">
    <li>Existing</li>
</ul>
<button hx-get="/new-item" hx-target="#list" hx-swap="afterbegin">
    Prepend Item
</button>
```

### beforeend

Appends response as the last child of the target.

```html
<!-- Before: <ul><li>Existing</li></ul> -->
<!-- After:  <ul><li>Existing</li><li>New</li></ul> -->
<button hx-get="/new-item" hx-target="#list" hx-swap="beforeend">
    Append Item
</button>
```

### beforebegin

Inserts response before the target element (as a sibling).

```html
<!-- Response inserted before the target div -->
<button hx-get="/alert" hx-target="#content" hx-swap="beforebegin">
    Show Alert Above
</button>
<div id="content">Main content</div>
```

### afterend

Inserts response after the target element (as a sibling).

```html
<div id="content">Main content</div>
<button hx-get="/footer" hx-target="#content" hx-swap="afterend">
    Add Below
</button>
```

### delete

Removes the target from the DOM regardless of response content.

```html
<tr id="row-42">
    <td>Item 42</td>
    <td>
        <button hx-delete="/items/42"
                hx-target="closest tr"
                hx-swap="delete"
                hx-confirm="Delete this item?">
            Remove
        </button>
    </td>
</tr>
```

### none

Skips swapping entirely. Response headers and OOB swaps still process.

```html
<!-- Fire-and-forget: just send the request -->
<button hx-post="/analytics" hx-swap="none">Track</button>
```

## Swap Modifiers

Append to the swap strategy separated by spaces:

### swap:\<time\>

Delay between receiving the response and performing the swap.

```html
<div hx-get="/data" hx-swap="innerHTML swap:300ms">
    <!-- Waits 300ms after response before swapping -->
</div>
```

### settle:\<time\>

Delay after swap before applying final attribute values (CSS transitions leverage this). Default: 20ms.

```html
<div hx-get="/data" hx-swap="innerHTML settle:500ms">
    <!-- 500ms settle period for CSS transitions -->
</div>
```

### transition:true

Uses the View Transitions API (where supported).

```html
<div hx-get="/page" hx-swap="innerHTML transition:true">
    <!-- Smooth cross-fade transition -->
</div>
```

### scroll:top | scroll:bottom

Scrolls the target element after swap.

```html
<div hx-get="/messages" hx-swap="beforeend scroll:bottom">
    <!-- Appends content and scrolls to bottom -->
</div>
```

### show:top | show:bottom

Scrolls the viewport to show the target or a specific element.

```html
<!-- Scroll page so target is at the top -->
<div hx-get="/content" hx-swap="innerHTML show:top">...</div>

<!-- Scroll to show a specific element -->
<div hx-get="/content" hx-swap="innerHTML show:#header:top">...</div>

<!-- Show nothing (no scroll) -->
<div hx-get="/content" hx-swap="innerHTML show:none">...</div>
```

### focus-scroll:true | focus-scroll:false

Controls whether the browser scrolls to the focused element after swap.

```html
<!-- Prevent focus-scroll after swap -->
<form hx-post="/validate" hx-swap="outerHTML focus-scroll:false">
    <input name="email" autofocus>
</form>
```

### ignoreTitle:true

Ignores `<title>` tags in the response (doesn't update page title).

```html
<div hx-get="/fragment" hx-swap="innerHTML ignoreTitle:true">...</div>
```

### Combined Modifiers

```html
<div hx-get="/data"
     hx-swap="innerHTML swap:200ms settle:100ms scroll:top transition:true">
</div>
```

## Morphing Swaps

Morphing intelligently patches the DOM instead of replacing it wholesale, preserving input focus, scroll position, and animation state.

### Idiomorph (Official)

```html
<!-- Enable the idiomorph extension -->
<body hx-ext="idiomorph">
    <div hx-get="/data" hx-swap="morph">
        <!-- DOM is morphed, not replaced -->
    </div>

    <!-- Morph the inner HTML only -->
    <div hx-get="/data" hx-swap="morph:innerHTML">...</div>

    <!-- Morph the outer element -->
    <div hx-get="/data" hx-swap="morph:outerHTML">...</div>
</body>
```

Install the extension:

```html
<script src="https://unpkg.com/idiomorph@0.3.0/dist/idiomorph-ext.min.js"></script>
```

## View Transitions API

Enables smooth animated transitions between content states.

### Per-Swap

```html
<div hx-get="/new-page" hx-swap="innerHTML transition:true">
    Smooth transition
</div>
```

### Global

```html
<meta name="htmx-config" content='{"globalViewTransitions": true}'>
```

### CSS Customization

```css
::view-transition-old(root) {
    animation: fade-out 0.3s ease-out;
}
::view-transition-new(root) {
    animation: fade-in 0.3s ease-in;
}

@keyframes fade-out { to { opacity: 0; } }
@keyframes fade-in { from { opacity: 0; } }
```

### Canceling Transitions

```javascript
document.addEventListener('htmx:beforeTransition', function(event) {
    if (shouldSkipTransition()) {
        event.preventDefault();
    }
});
```

## Preserving Elements

`hx-preserve` prevents an element from being replaced during swaps. The element must have a stable `id`.

```html
<!-- Video player stays intact during page navigation -->
<div id="player" hx-preserve>
    <video src="..."></video>
</div>

<!-- Keep a chat widget alive across page swaps -->
<div id="chat-widget" hx-preserve>
    <iframe src="/chat"></iframe>
</div>
```

## Response Selection

### hx-select

Extract a piece of the response before swapping.

```html
<!-- Server returns a full page, but only #content is swapped -->
<a hx-get="/about" hx-select="#content" hx-target="#main">
    About
</a>
```

### hx-select-oob

Select specific elements from the response for out-of-band swaps.

```html
<!-- Main swap into #content, plus update #notification separately -->
<button hx-get="/data"
        hx-target="#content"
        hx-select-oob="#notification">
    Load
</button>
```

## Request Lifecycle & CSS Classes

htmx automatically applies and removes CSS classes during the request lifecycle:

| Class | Applied | Removed | Use For |
|-------|---------|---------|---------|
| `htmx-request` | Request starts | Response received | Loading indicators |
| `htmx-swapping` | Before swap | After swap | Exit animations |
| `htmx-settling` | After swap | After settle delay | Enter animations |
| `htmx-added` | On new elements after swap | After settle delay | Entrance effects |

### CSS Transition Pattern

```css
.fade-in {
    opacity: 0;
    transition: opacity 0.5s ease-in;
}
.fade-in.htmx-settling {
    opacity: 1;
}
```

## Common Patterns

### Tab Navigation

```html
<div hx-target="#tab-content" hx-swap="innerHTML">
    <button hx-get="/tabs/1" class="active">Tab 1</button>
    <button hx-get="/tabs/2">Tab 2</button>
    <button hx-get="/tabs/3">Tab 3</button>
</div>
<div id="tab-content">Tab 1 content</div>
```

### Editable Table Row

```html
<!-- View mode -->
<tr id="row-1">
    <td>Alice</td>
    <td>alice@example.com</td>
    <td>
        <button hx-get="/contacts/1/edit" hx-target="closest tr" hx-swap="outerHTML">
            Edit
        </button>
    </td>
</tr>

<!-- Server returns edit mode (swap replaces entire row) -->
<tr id="row-1">
    <td><input name="name" value="Alice"></td>
    <td><input name="email" value="alice@example.com"></td>
    <td>
        <button hx-put="/contacts/1" hx-target="closest tr" hx-swap="outerHTML"
                hx-include="closest tr">
            Save
        </button>
        <button hx-get="/contacts/1" hx-target="closest tr" hx-swap="outerHTML">
            Cancel
        </button>
    </td>
</tr>
```

### Cascading Selects

```html
<select name="country" hx-get="/states" hx-target="#state-select">
    <option value="us">United States</option>
    <option value="ca">Canada</option>
</select>

<select id="state-select" name="state">
    <option>Select country first</option>
</select>
```
