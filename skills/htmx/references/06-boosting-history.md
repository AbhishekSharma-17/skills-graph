# htmx — Boosting & History

> Source: [htmx.org/docs/#boosting](https://htmx.org/docs/#boosting) | Version: 2.0.x

## Table of Contents

- [hx-boost Overview](#hx-boost-overview)
- [Boosting Links](#boosting-links)
- [Boosting Forms](#boosting-forms)
- [History Support](#history-support)
- [hx-push-url](#hx-push-url)
- [hx-replace-url](#hx-replace-url)
- [History Caching](#history-caching)
- [History Restoration](#history-restoration)
- [History Configuration](#history-configuration)
- [Progressive Enhancement](#progressive-enhancement)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## hx-boost Overview

`hx-boost="true"` converts standard `<a>` and `<form>` elements into AJAX requests, giving your site SPA-like navigation without changing any markup. The page URL updates, browser history works, and content swaps smoothly.

```html
<!-- Enable boosting for all links and forms within -->
<body hx-boost="true">
    <nav>
        <a href="/home">Home</a>           <!-- AJAX GET, pushes URL -->
        <a href="/about">About</a>         <!-- AJAX GET, pushes URL -->
        <a href="/contact">Contact</a>     <!-- AJAX GET, pushes URL -->
    </nav>
    <main id="content">
        <!-- Content swapped here -->
    </main>
</body>
```

### How It Works

1. htmx intercepts the link click or form submit
2. Issues an AJAX request (GET for links, method from form)
3. Swaps the response into the `<body>` (innerHTML by default)
4. Pushes the URL to browser history
5. Back/forward buttons work via cached snapshots

### Disabling Boost on Specific Elements

```html
<body hx-boost="true">
    <a href="/page">Boosted</a>
    <a href="/page" hx-boost="false">Not boosted (full page load)</a>
    <a href="https://external.com">External links are NOT boosted</a>
    <a href="/file.pdf" hx-boost="false">Download link</a>
</body>
```

## Boosting Links

Boosted links send GET requests and swap the response into `<body>`.

```html
<div hx-boost="true">
    <!-- All these become AJAX navigations -->
    <a href="/users">Users</a>
    <a href="/settings">Settings</a>

    <!-- Customize target and swap -->
    <a href="/users" hx-target="#main" hx-swap="innerHTML">Users</a>

    <!-- Anchor links are not boosted -->
    <a href="#section">Jump to section</a>
</div>
```

### Boost with hx-select

To swap only a portion of the response:

```html
<body hx-boost="true" hx-select="#content" hx-target="#content">
    <nav>
        <a href="/page1">Page 1</a>
        <a href="/page2">Page 2</a>
    </nav>
    <div id="content">
        <!-- Only this part gets swapped -->
    </div>
</body>
```

## Boosting Forms

Boosted forms use their `method` and `action` attributes:

```html
<div hx-boost="true">
    <form action="/search" method="get">
        <input name="q" type="search">
        <button type="submit">Search</button>
    </form>

    <form action="/contacts" method="post">
        <input name="name">
        <input name="email">
        <button type="submit">Create</button>
    </form>
</div>
```

### Scroll Behavior

By default, boosted requests scroll to the top of the page. Disable:

```html
<a href="/page" hx-boost="true" hx-swap="innerHTML show:none">
    No scroll on navigation
</a>
```

Or globally:

```javascript
htmx.config.scrollIntoViewOnBoost = false;
```

## History Support

htmx integrates with the browser's History API to provide back/forward navigation for AJAX-loaded content.

### How History Works

1. Before issuing a request, htmx snapshots the current DOM
2. The snapshot is cached in `localStorage`
3. The URL is pushed to the browser history stack
4. On back/forward, htmx restores from cache or re-fetches

### Enabling History

History is enabled automatically with `hx-boost`. For non-boosted requests, use `hx-push-url`:

```html
<button hx-get="/page2" hx-push-url="true" hx-target="#content">
    Go to Page 2
</button>
```

## hx-push-url

Pushes a URL to the browser history stack.

```html
<!-- Push the request URL -->
<a hx-get="/users" hx-push-url="true">Users</a>

<!-- Push a custom URL (different from request URL) -->
<button hx-get="/api/users" hx-push-url="/users">
    Load Users
</button>

<!-- Disable URL push (override inherited value) -->
<a hx-get="/fragment" hx-push-url="false">Load Fragment</a>
```

Server can override via response header:

```python
response.headers["HX-Push-Url"] = "/custom-url"
# or prevent push
response.headers["HX-Push-Url"] = "false"
```

## hx-replace-url

Replaces the current URL without creating a new history entry.

```html
<!-- Replace URL (no new history entry) -->
<button hx-get="/users?page=2"
        hx-replace-url="true"
        hx-target="#user-list">
    Next Page
</button>

<!-- Replace with custom URL -->
<button hx-get="/api/search"
        hx-replace-url="/search?q=test"
        hx-target="#results">
    Search
</button>
```

Useful for pagination, filters, sorting — updates the URL for shareability without polluting the back button.

## History Caching

htmx caches DOM snapshots in `localStorage` for instant back/forward restoration.

### Cache Size

```javascript
// Default: 10 snapshots
htmx.config.historyCacheSize = 10;

// Disable history cache entirely
htmx.config.historyCacheSize = 0;
```

### Excluding Sensitive Pages

Use `hx-history="false"` to prevent caching pages with sensitive data:

```html
<div hx-history="false">
    <!-- This page's content is NOT cached in localStorage -->
    <h2>Account Settings</h2>
    <p>SSN: ***-**-1234</p>
</div>
```

### History Snapshot Element

By default, htmx snapshots the entire `<body>`. Specify a different element:

```html
<!-- Only snapshot #content for history -->
<div id="content" hx-history-elt>
    <h1>Page Content</h1>
</div>
```

## History Restoration

### Default: Restore from Cache

When the user navigates back/forward, htmx restores the cached snapshot instantly.

### Cache Miss Behavior

If the snapshot is not in cache:

```javascript
// Default: make AJAX request to restore
// (sends HX-History-Restore-Request: true header)
htmx.config.refreshOnHistoryMiss = false;  // default

// Alternative: do a full page reload on cache miss
htmx.config.refreshOnHistoryMiss = true;
```

### History Restore as htmx Request

```javascript
// Default: true — restoration requests include HX-Request header
htmx.config.historyRestoreAsHxRequest = true;

// Set to false if your server might return different content
// for htmx vs. regular requests and you want full-page HTML on restore
htmx.config.historyRestoreAsHxRequest = false;
```

### Server-Side Handling

```python
@app.get("/page")
async def page(request: Request):
    is_htmx = request.headers.get("HX-Request")
    is_history_restore = request.headers.get("HX-History-Restore-Request")

    if is_history_restore:
        return full_page_response()   # Return full page for restoration
    if is_htmx:
        return fragment_response()    # Return fragment for normal requests
    return full_page_response()       # Regular page load
```

## History Configuration

```javascript
// Enable/disable history entirely
htmx.config.historyEnabled = true;

// Number of snapshots to keep
htmx.config.historyCacheSize = 10;

// Full reload on cache miss
htmx.config.refreshOnHistoryMiss = false;

// Send HX-Request on restoration
htmx.config.historyRestoreAsHxRequest = true;
```

Via meta tag:

```html
<meta name="htmx-config" content='{
    "historyCacheSize": 20,
    "refreshOnHistoryMiss": true
}'>
```

## Progressive Enhancement

htmx supports progressive enhancement — pages work without JavaScript, and htmx enhances them when loaded.

### Links

```html
<!-- Works as a regular link without JS; becomes AJAX with htmx -->
<a href="/users" hx-boost="true">Users</a>
```

### Forms

```html
<!-- Works as a regular form without JS; becomes AJAX with htmx -->
<form action="/submit" method="post" hx-boost="true">
    <input name="data">
    <button type="submit">Submit</button>
</form>
```

### Server Strategy

Return full pages for non-htmx requests, fragments for htmx:

```python
@app.get("/page")
async def page(request: Request):
    content = render_content()
    if request.headers.get("HX-Request"):
        return HTMLResponse(content)  # Just the fragment
    return full_page_with(content)    # Wrapped in layout
```

## Common Patterns

### SPA-Like Navigation

```html
<body hx-boost="true" hx-target="#content" hx-select="#content" hx-swap="innerHTML">
    <nav>
        <a href="/">Home</a>
        <a href="/about">About</a>
        <a href="/contact">Contact</a>
    </nav>
    <div id="content">
        <!-- All navigation swaps here -->
    </div>
</body>
```

### Bookmarkable Filter State

```html
<form hx-get="/products"
      hx-target="#product-grid"
      hx-replace-url="true"
      hx-trigger="change">
    <select name="category">
        <option value="all">All</option>
        <option value="electronics">Electronics</option>
    </select>
    <select name="sort">
        <option value="newest">Newest</option>
        <option value="price">Price</option>
    </select>
</form>
<div id="product-grid">...</div>
```

### Wizard / Multi-Step Form

```html
<div id="wizard">
    <form hx-post="/wizard/step1"
          hx-target="#wizard"
          hx-swap="outerHTML"
          hx-push-url="/wizard/step2">
        <h2>Step 1: Personal Info</h2>
        <input name="name" required>
        <button type="submit">Next</button>
    </form>
</div>
```

## Common Pitfalls

1. **Full pages required** — URLs pushed to history must return complete HTML when navigated directly (bookmarks, refresh). Your server must handle both htmx and direct requests.

2. **External links** — `hx-boost` only boosts same-origin links. Cross-origin links are left as-is.

3. **Download links** — Don't boost links to downloadable files. Use `hx-boost="false"` on them.

4. **CSS/JS consistency** — Since only the body is swapped, ensure CSS and JS loaded in `<head>` cover all pages. Use the `head-support` extension if pages need different head content.

5. **Form method** — Boosted forms use their HTML `method` attribute. Missing `method` defaults to GET.
