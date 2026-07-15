# htmx — Overview & Getting Started

> Source: [htmx.org](https://htmx.org/) | Version: 2.0.x | License: BSD 2-Clause

## Table of Contents

- [What Is htmx](#what-is-htmx)
- [Core Philosophy](#core-philosophy)
- [Installation](#installation)
- [First Example](#first-example)
- [How htmx Works](#how-htmx-works)
- [Key Concepts](#key-concepts)
- [When to Use htmx](#when-to-use-htmx)
- [When NOT to Use htmx](#when-not-to-use-htmx)
- [Comparison with SPAs](#comparison-with-spas)
- [Browser Support](#browser-support)
- [Common Pitfalls](#common-pitfalls)

## What Is htmx

htmx is a dependency-free JavaScript library (~14KB min+gzip) that lets you access AJAX, CSS Transitions, WebSockets, and Server-Sent Events directly from HTML attributes. Instead of writing JavaScript to make API calls and manipulate the DOM, you declare behavior in HTML and let the server return HTML fragments.

```html
<!-- Click button → GET /api/users → replace #results innerHTML -->
<button hx-get="/api/users" hx-target="#results" hx-swap="innerHTML">
  Load Users
</button>
<div id="results"></div>
```

## Core Philosophy

htmx extends HTML as a hypertext by removing arbitrary constraints:

1. **Any element can issue HTTP requests** — not just `<a>` and `<form>`
2. **Any event can trigger requests** — not just clicks and submits
3. **Any HTTP method is available** — not just GET and POST
4. **Any element can be the replacement target** — not just the entire page

This is the **Hypermedia-Driven Application (HDA)** approach: the server returns HTML, not JSON. The server controls the UI state, and the client is a thin presentation layer.

**HATEOAS** (Hypermedia As The Engine Of Application State): htmx embraces this REST principle — the server sends hypermedia controls (links, forms, htmx attributes) that tell the client what it can do next.

## Installation

### CDN (Simplest)

```html
<script src="https://unpkg.com/htmx.org@2.0.10"></script>
```

### npm

```bash
npm install htmx.org
```

```javascript
// In your bundler entry point
import 'htmx.org';
// or require('htmx.org');
```

### Self-Hosted Download

Download `htmx.min.js` from the releases page and serve it as a static asset:

```html
<script src="/static/js/htmx.min.js"></script>
```

### Webpack / Bundler

```javascript
import 'htmx.org';

// Make htmx globally available if needed
window.htmx = require('htmx.org');
```

## First Example

### Server (Python / FastAPI)

```python
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://unpkg.com/htmx.org@2.0.10"></script>
    </head>
    <body>
        <h1>Contacts</h1>
        <input type="search" name="q"
               hx-get="/search"
               hx-trigger="input changed delay:300ms"
               hx-target="#results"
               placeholder="Search contacts...">
        <div id="results"></div>
    </body>
    </html>
    """

@app.get("/search", response_class=HTMLResponse)
async def search(q: str = ""):
    contacts = [c for c in ALL_CONTACTS if q.lower() in c.lower()]
    rows = "".join(f"<li>{c}</li>" for c in contacts)
    return f"<ul>{rows}</ul>"
```

### What Happens

1. User types in the search box
2. After 300ms of inactivity, htmx sends `GET /search?q=...`
3. Server returns an HTML fragment `<ul>...</ul>`
4. htmx swaps it into `#results`

No JavaScript written. No JSON parsing. No DOM manipulation.

## How htmx Works

### Request Lifecycle

1. An event fires on an element with `hx-*` attributes
2. htmx gathers values from the element and included inputs
3. An AJAX request is issued to the specified URL
4. The `htmx-request` CSS class is applied to the triggering element
5. The server returns an HTML fragment
6. htmx swaps the fragment into the target element
7. CSS settling classes are applied/removed for transitions

### Attribute Inheritance

Most `hx-*` attributes inherit down the DOM tree. Set `hx-target` on a parent, and all children with `hx-get` etc. use that target:

```html
<div hx-target="#output" hx-swap="innerHTML">
    <button hx-get="/page1">Page 1</button>  <!-- targets #output -->
    <button hx-get="/page2">Page 2</button>  <!-- targets #output -->
</div>
<div id="output"></div>
```

Disable inheritance per-attribute: `hx-disinherit="hx-target"` or globally: `htmx.config.disableInheritance = true`.

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Attributes** | `hx-get`, `hx-post`, `hx-target`, `hx-swap`, `hx-trigger` — the core API |
| **Triggers** | Events that initiate requests: clicks, input, load, revealed, intersect, polling |
| **Targets** | CSS selector identifying where the response goes |
| **Swapping** | How the response replaces content: innerHTML, outerHTML, beforeend, afterbegin, etc. |
| **OOB Swaps** | Out-of-band: update multiple DOM elements from a single response |
| **Boosting** | `hx-boost` converts regular links/forms into AJAX requests automatically |
| **History** | Push/replace URLs in browser history for deep-linkable AJAX pages |
| **Extensions** | Pluggable modules: SSE, WebSocket, idiomorph, preload, etc. |
| **Indicators** | Loading spinners shown/hidden automatically during requests |

## When to Use htmx

- Server-rendered apps (Django, Rails, FastAPI, Flask, Express, Go, PHP) that need interactivity
- CRUD applications with forms, tables, lists
- Content-heavy sites that need dynamic updates (comments, search, filters)
- Progressive enhancement of existing server-rendered pages
- Real-time features (SSE, WebSocket) without a JS framework
- Replacing jQuery AJAX patterns with a declarative approach
- Teams that prefer server-side rendering over client-side frameworks

## When NOT to Use htmx

- Highly interactive offline-first applications (use a SPA framework)
- Complex client-side state management (collaborative editors, drag-and-drop builders)
- Applications requiring extensive client-side computation
- When your API must serve both web and mobile (JSON APIs still needed for mobile)

## Comparison with SPAs

| Aspect | htmx (HDA) | SPA (React/Vue/etc.) |
|--------|-----------|---------------------|
| **Server returns** | HTML fragments | JSON data |
| **Rendering** | Server-side | Client-side |
| **Bundle size** | ~14KB (htmx) | 100-300KB+ (framework + app) |
| **State management** | Server holds state | Client holds state |
| **SEO** | Built-in (server renders) | Requires SSR/SSG |
| **Offline** | Limited | Full support |
| **API reuse** | Hypermedia (HTML) | Data API (JSON) |
| **Team skills** | Backend + HTML/CSS | Backend + Frontend JS |

## Browser Support

htmx 2.x supports all modern browsers. IE11 is NOT supported (use htmx 1.x for IE11).

Supported: Chrome, Firefox, Safari, Edge (all recent versions).

## Common Pitfalls

1. **Returning full pages instead of fragments** — htmx expects HTML fragments, not complete `<!DOCTYPE html>` pages (unless using `hx-select` to pick out a piece)

2. **Forgetting `hx-target`** — without a target, htmx swaps into the triggering element itself (innerHTML), which may not be what you want

3. **Not handling the `HX-Request` header** — your server should detect htmx requests and return fragments vs. full pages

4. **CSRF token issues** — htmx doesn't include CSRF tokens by default; configure via `hx-headers` or framework middleware

5. **Stale element references** — after a swap, old DOM references are invalid; use `htmx:afterSwap` events

6. **Over-inheriting attributes** — `hx-*` attributes inherit down the DOM; use `hx-disinherit` to prevent unintended behavior

7. **Missing `id` attributes** — OOB swaps and CSS transitions require stable `id` attributes on elements
