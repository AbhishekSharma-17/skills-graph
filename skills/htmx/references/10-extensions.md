# htmx — Extensions

> Source: [htmx.org/extensions/](https://htmx.org/extensions/) | Version: 2.0.x

## Table of Contents

- [Extension System Overview](#extension-system-overview)
- [Installing Extensions](#installing-extensions)
- [Core Extensions](#core-extensions)
- [SSE (Server-Sent Events)](#sse-server-sent-events)
- [WebSocket](#websocket)
- [Idiomorph (Morphing)](#idiomorph-morphing)
- [Preload](#preload)
- [Response Targets](#response-targets)
- [Head Support](#head-support)
- [Community Extensions](#community-extensions)
- [Creating Custom Extensions](#creating-custom-extensions)

## Extension System Overview

Extensions augment htmx's core functionality. They are separate scripts loaded after the main htmx library and activated with `hx-ext`.

```html
<!-- 1. Load htmx -->
<script src="https://unpkg.com/htmx.org@2.0.10"></script>
<!-- 2. Load extension -->
<script src="https://unpkg.com/htmx-ext-sse@2.2.2"></script>
<!-- 3. Activate extension on an element and its children -->
<body hx-ext="sse">
    ...
</body>
```

### Activating Multiple Extensions

```html
<body hx-ext="sse, preload, response-targets">
```

### Disabling an Extension

```html
<body hx-ext="preload">
    <div hx-ext="ignore:preload">
        <!-- preload disabled here and for all children -->
    </div>
</body>
```

## Installing Extensions

### CDN (unpkg)

```html
<script src="https://unpkg.com/htmx-ext-sse@2.2.2"></script>
<script src="https://unpkg.com/htmx-ext-ws@2.0.2"></script>
<script src="https://unpkg.com/htmx-ext-preload@2.1.0"></script>
<script src="https://unpkg.com/htmx-ext-response-targets@2.0.2"></script>
<script src="https://unpkg.com/htmx-ext-head-support@2.0.3"></script>
<script src="https://unpkg.com/idiomorph@0.3.0/dist/idiomorph-ext.min.js"></script>
```

### npm

```bash
npm install htmx-ext-sse
npm install htmx-ext-ws
npm install htmx-ext-preload
npm install htmx-ext-response-targets
npm install htmx-ext-head-support
npm install idiomorph
```

### Bundler Import

```javascript
import 'htmx.org';
import 'htmx-ext-sse';
import 'htmx-ext-ws';
```

## Core Extensions

These are maintained by the htmx team:

| Extension | Package | Purpose |
|-----------|---------|---------|
| `sse` | `htmx-ext-sse` | Server-Sent Events integration |
| `ws` | `htmx-ext-ws` | WebSocket integration |
| `idiomorph` | `idiomorph` | Morph-based DOM diffing swap |
| `preload` | `htmx-ext-preload` | Preload content on hover/focus |
| `response-targets` | `htmx-ext-response-targets` | Status-code-specific targets |
| `head-support` | `htmx-ext-head-support` | Merge `<head>` tag from responses |
| `htmx-1-compat` | `htmx-ext-htmx-1-compat` | Backwards compatibility with v1 |

## SSE (Server-Sent Events)

Real-time server-to-client push via SSE.

### Basic SSE

```html
<body hx-ext="sse">
    <!-- Connect to SSE endpoint -->
    <div sse-connect="/events">

        <!-- Swap content when "message" event arrives -->
        <div sse-swap="message">
            Waiting for updates...
        </div>

        <!-- Listen for named events -->
        <div sse-swap="notification">
            No notifications yet
        </div>

        <!-- Trigger htmx request on SSE event -->
        <div hx-get="/data"
             hx-trigger="sse:dataUpdated"
             hx-target="#data-display">
        </div>
    </div>
</body>
```

### SSE with Swap Strategies

```html
<div sse-connect="/events">
    <!-- Default: innerHTML -->
    <ul sse-swap="newItem" hx-swap="beforeend">
        <!-- New items appended -->
    </ul>

    <!-- Replace the whole element -->
    <div sse-swap="statusUpdate" hx-swap="outerHTML">
        Current status
    </div>
</div>
```

### Server-Side SSE (Python / FastAPI)

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import asyncio

app = FastAPI()

async def event_generator():
    while True:
        data = await get_latest_data()
        yield f"event: message\ndata: <div>{data}</div>\n\n"
        await asyncio.sleep(1)

@app.get("/events")
async def events():
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

### Named SSE Events

```python
async def event_generator():
    yield f"event: notification\ndata: <span>New alert!</span>\n\n"
    yield f"event: statusUpdate\ndata: <div>Online</div>\n\n"
```

### SSE Close

```html
<!-- Close connection when parent is removed from DOM -->
<div sse-connect="/events" sse-close="closeEvent">
    <div sse-swap="message">...</div>
</div>
```

## WebSocket

Bidirectional real-time communication.

### Basic WebSocket

```html
<body hx-ext="ws">
    <div ws-connect="/ws/chat">
        <!-- Incoming messages swapped here -->
        <div id="messages"></div>

        <!-- Form sends data through WebSocket -->
        <form ws-send>
            <input name="message" type="text">
            <button type="submit">Send</button>
        </form>
    </div>
</body>
```

### WebSocket Server (Python / FastAPI)

```python
from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_json()
        # Return HTML fragment
        response_html = f"""
        <div id="messages" hx-swap-oob="beforeend">
            <p><strong>{data.get('user', 'Anonymous')}:</strong> {data['message']}</p>
        </div>
        """
        await websocket.send_text(response_html)
```

### WebSocket Events

```html
<div ws-connect="/ws/feed"
     hx-on:htmx:wsOpen="console.log('Connected')"
     hx-on:htmx:wsClose="console.log('Disconnected')">
    <div id="feed" hx-swap="beforeend">...</div>
</div>
```

### Reconnection

htmx automatically reconnects WebSockets using a full-jitter exponential backoff strategy:

```javascript
// Configure reconnect strategy
htmx.config.wsReconnectDelay = "full-jitter";  // default
// Or set a fixed delay (ms)
htmx.config.wsReconnectDelay = 3000;
```

## Idiomorph (Morphing)

Idiomorph patches the DOM by diffing old and new content, preserving form state, focus, scroll position, and animations.

### Usage

```html
<body hx-ext="idiomorph">
    <!-- Morph the inner content -->
    <div hx-get="/data" hx-swap="morph:innerHTML">
        <ul>
            <li id="item-1">First</li>
            <li id="item-2">Second</li>
        </ul>
    </div>

    <!-- Morph the outer element -->
    <div hx-get="/data" hx-swap="morph:outerHTML">...</div>

    <!-- Morph shorthand (default is outerHTML) -->
    <div hx-get="/data" hx-swap="morph">...</div>
</body>
```

### When to Use Morphing

- Lists that reorder frequently
- Forms that update without losing user input
- Complex UIs where preserving DOM state matters
- Animations that should continue across updates

### Morphing vs. Standard Swap

| Aspect | Standard Swap | Morph |
|--------|--------------|-------|
| DOM replacement | Wholesale | Diff-based |
| Form state | Lost | Preserved |
| Focus | Lost | Preserved |
| Scroll position | Reset | Preserved |
| Performance | Faster for simple | Better for complex |

## Preload

Preloads content into the browser cache on hover or mousedown, making navigation feel instant.

```html
<body hx-ext="preload">
    <!-- Preload on hover (default) -->
    <a href="/page" hx-boost="true" preload>
        Page (preloaded on hover)
    </a>

    <!-- Preload on mousedown -->
    <a href="/page" hx-boost="true" preload="mousedown">
        Page (preloaded on mousedown)
    </a>

    <!-- Preload all links within -->
    <nav preload>
        <a href="/home" hx-boost="true">Home</a>
        <a href="/about" hx-boost="true">About</a>
    </nav>
</body>
```

## Response Targets

Route responses to different targets based on HTTP status codes.

```html
<body hx-ext="response-targets">
    <form hx-post="/contacts"
          hx-target="#result"
          hx-target-422="#form-errors"
          hx-target-5*="#server-error"
          hx-target-404="#not-found">
        <input name="email" required>
        <button type="submit">Create</button>
    </form>

    <div id="result"></div>
    <div id="form-errors"></div>
    <div id="server-error"></div>
    <div id="not-found"></div>
</body>
```

### Wildcard Patterns

```html
hx-target-4*="#client-errors"     <!-- All 4xx -->
hx-target-5*="#server-errors"     <!-- All 5xx -->
hx-target-422="#validation"       <!-- Specific code -->
hx-target-*="#catch-all"          <!-- Any non-2xx -->
```

## Head Support

Merges `<head>` content from AJAX responses, ensuring styles and scripts update.

```html
<body hx-ext="head-support" hx-boost="true">
    <a href="/page-with-different-styles">Navigate</a>
    <!-- <head> content from the response is merged -->
</body>
```

### Head Merge Behavior

- Existing `<link>` and `<style>` tags are preserved
- New `<link>` and `<style>` tags from the response are added
- `<title>` is updated
- Elements with `head-support="re-eval"` are re-evaluated each time

## Community Extensions

Notable community extensions:

| Extension | Purpose |
|-----------|---------|
| `loading-states` | Manage complex loading states (disable, class toggle) |
| `json-enc` | Send request body as JSON |
| `multi-swap` | Swap multiple elements per response |
| `class-tools` | Timed CSS class manipulation |
| `path-params` | URL path parameter interpolation |
| `remove-me` | Auto-remove elements after timeout |
| `debug` | Console logging for debugging |
| `alpine-morph` | Morph swap preserving Alpine.js state |
| `optimistic` | Optimistic UI updates before server confirms |

## Creating Custom Extensions

```javascript
htmx.defineExtension('my-extension', {
    onEvent: function(name, event) {
        if (name === 'htmx:configRequest') {
            event.detail.headers['X-My-Header'] = 'custom-value';
        }
    },

    transformResponse: function(text, xhr, elt) {
        // Modify response before swap
        return text.toUpperCase();
    },

    isInlineSwap: function(swapStyle) {
        return swapStyle === 'my-swap';
    },

    handleSwap: function(swapStyle, target, fragment, settleInfo) {
        if (swapStyle === 'my-swap') {
            // Custom swap logic
            target.innerHTML = fragment.innerHTML;
            return [target];
        }
    },

    encodeParameters: function(xhr, parameters, elt) {
        // Custom parameter encoding
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.send(JSON.stringify(parameters));
        return null;
    }
});
```

### Extension Hooks

| Hook | Purpose |
|------|---------|
| `init` | One-time initialization |
| `onEvent` | Handle htmx events |
| `transformResponse` | Modify response text |
| `isInlineSwap` | Declare custom swap styles |
| `handleSwap` | Implement custom swapping |
| `encodeParameters` | Custom request encoding |
| `getSelectors` | Add custom CSS selectors |
