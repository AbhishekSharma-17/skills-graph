# htmx — Triggers

> Source: [htmx.org/docs/#triggers](https://htmx.org/docs/#triggers) | Version: 2.0.x

## Table of Contents

- [Default Triggers](#default-triggers)
- [hx-trigger Syntax](#hx-trigger-syntax)
- [Trigger Modifiers](#trigger-modifiers)
- [Trigger Filters](#trigger-filters)
- [Special Events](#special-events)
- [Polling](#polling)
- [Load Polling](#load-polling)
- [Multiple Triggers](#multiple-triggers)
- [Custom Events](#custom-events)
- [Intersection Observer](#intersection-observer)
- [From Modifier](#from-modifier)
- [Consume Modifier](#consume-modifier)
- [Common Patterns](#common-patterns)

## Default Triggers

When `hx-trigger` is omitted, htmx uses sensible defaults based on element type:

| Element | Default Trigger |
|---------|----------------|
| `<input>` | `change` |
| `<textarea>` | `change` |
| `<select>` | `change` |
| `<form>` | `submit` |
| Everything else | `click` |

## hx-trigger Syntax

```
hx-trigger="event [filter] [modifier1] [modifier2] ..."
```

### Basic Usage

```html
<!-- Trigger on click (default for buttons) -->
<button hx-get="/data" hx-trigger="click">Load</button>

<!-- Trigger on input (typing) -->
<input hx-get="/search" hx-trigger="input">

<!-- Trigger on custom event -->
<div hx-get="/data" hx-trigger="myEvent">...</div>

<!-- Trigger on submit -->
<form hx-post="/submit" hx-trigger="submit">...</form>
```

## Trigger Modifiers

### once

Fire only once.

```html
<button hx-get="/data" hx-trigger="click once">
    Load (only first click)
</button>
```

### changed

Only fire if the element's value has actually changed.

```html
<input hx-get="/search" hx-trigger="input changed">
```

### delay:\<time\>

Wait before firing. Resets on each new event (debounce).

```html
<!-- Debounce: wait 500ms after last keystroke -->
<input hx-get="/search"
       hx-trigger="input changed delay:500ms"
       hx-target="#results"
       name="q">
```

### throttle:\<time\>

Fire at most once per time interval.

```html
<!-- Throttle: max once every 2 seconds -->
<input hx-get="/search"
       hx-trigger="input throttle:2s"
       hx-target="#results">
```

### queue:\<strategy\>

Control event queuing when a request is in-flight.

```html
<!-- Queue the first event only -->
<button hx-get="/data" hx-trigger="click queue:first">Load</button>

<!-- Queue the last event only (default) -->
<button hx-get="/data" hx-trigger="click queue:last">Load</button>

<!-- Queue all events -->
<button hx-get="/data" hx-trigger="click queue:all">Load</button>

<!-- Queue none (drop all) -->
<button hx-get="/data" hx-trigger="click queue:none">Load</button>
```

## Trigger Filters

Conditional expressions in square brackets. Access event properties directly.

```html
<!-- Only on Ctrl+click -->
<button hx-get="/admin" hx-trigger="click[ctrlKey]">Admin Action</button>

<!-- Only on Enter key -->
<input hx-get="/search" hx-trigger="keyup[key=='Enter']">

<!-- Only when checkbox is checked -->
<input type="checkbox" hx-get="/toggle"
       hx-trigger="click[this.checked]">

<!-- Combine with JavaScript expression -->
<button hx-get="/data" hx-trigger="click[isAuthorized()]">
    Protected Action
</button>

<!-- Multiple conditions -->
<input hx-post="/save"
       hx-trigger="keyup[key=='Enter' && !shiftKey]">
```

## Special Events

### load

Fires when the element is loaded into the DOM.

```html
<!-- Load content immediately when this element appears -->
<div hx-get="/initial-data" hx-trigger="load">
    Loading...
</div>

<!-- Lazy load with delay -->
<div hx-get="/data" hx-trigger="load delay:1s">
    Loading in 1 second...
</div>
```

### revealed

Fires when the element scrolls into the viewport.

```html
<!-- Load when visible (infinite scroll, lazy images) -->
<div hx-get="/more-content" hx-trigger="revealed" hx-swap="afterend">
    <img class="placeholder">
</div>
```

### intersect

Uses the Intersection Observer API with configurable thresholds.

```html
<!-- Fire when 50% visible -->
<div hx-get="/analytics"
     hx-trigger="intersect threshold:0.5"
     hx-swap="none">
</div>

<!-- Fire once when any part is visible -->
<img hx-get="/lazy-image"
     hx-trigger="intersect once"
     hx-swap="outerHTML">
```

## Polling

Use `every` to set up polling intervals.

```html
<!-- Poll every 2 seconds -->
<div hx-get="/status" hx-trigger="every 2s">
    Checking status...
</div>

<!-- Poll with a filter (conditional polling) -->
<div hx-get="/status"
     hx-trigger="every 5s [isActive()]"
     hx-target="this">
    Status: active
</div>
```

**Stop polling:** Server responds with HTTP status code `286`.

```python
# Server-side: stop polling when task is complete
@app.get("/status")
async def status():
    if task_complete:
        return HTMLResponse("<div>Done!</div>", status_code=286)
    return HTMLResponse("<div>Working...</div>")
```

## Load Polling

A pattern where the response includes the trigger, creating a self-polling element.

```html
<!-- Initial element -->
<div hx-get="/job/status"
     hx-trigger="load delay:1s"
     hx-swap="outerHTML">
    Starting...
</div>
```

Server returns the same structure with updated content:

```html
<!-- Server response while in progress -->
<div hx-get="/job/status"
     hx-trigger="load delay:1s"
     hx-swap="outerHTML">
    Processing: 45% complete
</div>

<!-- Server response when done (no trigger = stops polling) -->
<div>Complete!</div>
```

## Multiple Triggers

Separate multiple triggers with commas.

```html
<!-- Fire on click OR keyup Enter -->
<input hx-get="/search"
       hx-trigger="click from:next button, keyup[key=='Enter']">

<!-- Fire on load (once) and then on every click -->
<div hx-get="/data"
     hx-trigger="load once, click">
</div>

<!-- Different modifiers per trigger -->
<input hx-get="/suggest"
       hx-trigger="input changed delay:300ms, focus once">
```

## Custom Events

Trigger on custom JavaScript events dispatched via `htmx.trigger()` or `dispatchEvent()`.

```html
<div hx-get="/data" hx-trigger="dataRefresh">...</div>

<script>
// Trigger from JavaScript
htmx.trigger('#my-element', 'dataRefresh');

// Or with vanilla JS
document.getElementById('my-element')
    .dispatchEvent(new CustomEvent('dataRefresh'));
</script>
```

### Triggering from Server Responses

The server can trigger client-side events via the `HX-Trigger` response header:

```python
# Server response triggers a client event
response = HTMLResponse("<div>Updated</div>")
response.headers["HX-Trigger"] = "showMessage"
return response

# Trigger with data
response.headers["HX-Trigger"] = json.dumps({
    "showMessage": {"level": "success", "text": "Saved!"}
})
```

```html
<!-- Listen for server-triggered event -->
<div hx-trigger="showMessage from:body"
     hx-get="/notifications"
     hx-swap="innerHTML">
</div>
```

## Intersection Observer

The `intersect` trigger uses `IntersectionObserver` for viewport-based triggers.

```html
<!-- Default: fire when element enters viewport -->
<div hx-get="/data" hx-trigger="intersect">...</div>

<!-- With threshold -->
<div hx-get="/data" hx-trigger="intersect threshold:0.5">...</div>

<!-- Root margin (expand/shrink observation area) -->
<div hx-get="/data" hx-trigger="intersect root:.container threshold:0.1">
</div>
```

## From Modifier

Listen for events on a different element.

```html
<!-- Trigger when a different element is clicked -->
<div hx-get="/data" hx-trigger="click from:#other-button">
    This loads when #other-button is clicked
</div>

<!-- Listen for events from the document -->
<div hx-get="/data" hx-trigger="custom-event from:document">...</div>

<!-- Listen for events from the window -->
<div hx-get="/data" hx-trigger="resize from:window throttle:500ms">...</div>

<!-- Listen from closest ancestor -->
<div hx-get="/data" hx-trigger="submit from:closest form">...</div>
```

## Consume Modifier

Prevents event propagation when the trigger fires.

```html
<!-- Consume the click so parent handlers don't see it -->
<button hx-post="/action" hx-trigger="click consume">
    Action
</button>
```

## Common Patterns

### Active Search (Debounced Input)

```html
<input type="search" name="q"
       hx-get="/search"
       hx-trigger="input changed delay:300ms, search"
       hx-target="#search-results"
       hx-indicator="#search-spinner"
       placeholder="Search...">
<span id="search-spinner" class="htmx-indicator">Searching...</span>
<div id="search-results"></div>
```

### Infinite Scroll

```html
<table>
    <tbody id="rows">
        <!-- initial rows -->
    </tbody>
</table>
<div hx-get="/rows?page=2"
     hx-trigger="revealed"
     hx-target="#rows"
     hx-swap="beforeend"
     hx-select="tr">
    <span class="htmx-indicator">Loading more...</span>
</div>
```

### Click to Load More

```html
<table>
    <tbody id="contacts">
        <!-- rows here -->
    </tbody>
</table>
<button hx-get="/contacts?page=2"
        hx-target="#contacts"
        hx-swap="beforeend"
        hx-select="tr">
    Load More
</button>
```

### Form Auto-Save

```html
<form hx-post="/autosave"
      hx-trigger="input changed delay:2s"
      hx-swap="none"
      hx-indicator="#save-indicator">
    <textarea name="content">...</textarea>
    <span id="save-indicator" class="htmx-indicator">Saving...</span>
</form>
```

### Keyboard Shortcuts

```html
<div hx-get="/refresh"
     hx-trigger="keyup[key=='r'] from:body"
     hx-target="#content">
    Press 'r' to refresh
</div>
```
