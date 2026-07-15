# htmx — Request & Response

> Source: [htmx.org/reference/#headers](https://htmx.org/reference/#headers) | Version: 2.0.x

## Table of Contents

- [Request Headers](#request-headers)
- [Response Headers](#response-headers)
- [Parameter Handling](#parameter-handling)
- [Request Synchronization](#request-synchronization)
- [Response Status Codes](#response-status-codes)
- [Response Handling Configuration](#response-handling-configuration)
- [HTTP Caching](#http-caching)
- [File Uploads](#file-uploads)
- [CSRF Protection](#csrf-protection)
- [Common Server Patterns](#common-server-patterns)

## Request Headers

htmx automatically includes these headers with every AJAX request:

| Header | Value | Description |
|--------|-------|-------------|
| `HX-Request` | `true` | Always present — distinguishes htmx from regular requests |
| `HX-Current-URL` | Current page URL | The URL of the page making the request |
| `HX-Target` | Element ID | The `id` of the target element (if it has one) |
| `HX-Trigger` | Element ID | The `id` of the triggered element (if it has one) |
| `HX-Trigger-Name` | Element name | The `name` of the triggered element (if it has one) |
| `HX-Boosted` | `true` | Present only for boosted requests (`hx-boost`) |
| `HX-Prompt` | User input | Present only when `hx-prompt` was used |
| `HX-History-Restore-Request` | `true` | Present on history restoration requests |

### Detecting htmx Requests on the Server

```python
# FastAPI
@app.get("/page")
async def page(request: Request):
    if request.headers.get("HX-Request"):
        return HTMLResponse("<div>Partial fragment</div>")
    return full_page_template()

# Django
def page_view(request):
    if request.headers.get("HX-Request"):
        return render(request, "fragment.html")
    return render(request, "full_page.html")
```

```javascript
// Express
app.get('/page', (req, res) => {
    if (req.headers['hx-request']) {
        return res.send('<div>Fragment</div>');
    }
    res.render('full_page');
});
```

## Response Headers

The server can control client behavior via response headers:

### HX-Trigger

Triggers client-side events after the response is processed.

```python
# Simple event
response.headers["HX-Trigger"] = "showNotification"

# Multiple events
response.headers["HX-Trigger"] = "event1, event2"

# Events with data (JSON)
import json
response.headers["HX-Trigger"] = json.dumps({
    "showToast": {"message": "Contact saved!", "level": "success"}
})
```

```html
<!-- Listen for server-triggered event -->
<div hx-on:showToast="showToast(event.detail)">...</div>
```

### HX-Trigger-After-Settle / HX-Trigger-After-Swap

Same as `HX-Trigger` but fires after the settle or swap phase.

### HX-Redirect

Client-side full-page redirect.

```python
response.headers["HX-Redirect"] = "/login"
```

### HX-Location

Client-side redirect via AJAX (no full page reload).

```python
# Simple
response.headers["HX-Location"] = "/new-page"

# With options (JSON)
response.headers["HX-Location"] = json.dumps({
    "path": "/new-page",
    "target": "#content",
    "swap": "innerHTML"
})
```

### HX-Push-Url / HX-Replace-Url

Updates the browser URL bar.

```python
# Push new URL to history stack
response.headers["HX-Push-Url"] = "/contacts/42"

# Replace current URL (no new history entry)
response.headers["HX-Replace-Url"] = "/contacts?page=2"

# Prevent URL update (set to false)
response.headers["HX-Push-Url"] = "false"
```

### HX-Refresh

Forces a full page refresh.

```python
response.headers["HX-Refresh"] = "true"
```

### HX-Reswap

Overrides the swap strategy for this response.

```python
response.headers["HX-Reswap"] = "outerHTML"
```

### HX-Retarget

Changes the target element for this response.

```python
response.headers["HX-Retarget"] = "#error-container"
```

### HX-Reselect

Overrides `hx-select` for this response.

```python
response.headers["HX-Reselect"] = "#specific-part"
```

## Parameter Handling

### Default Behavior

For `GET` and `DELETE`: parameters sent as URL query params.
For `POST`, `PUT`, `PATCH`: parameters sent as form-encoded body.

### hx-vals (Static JSON Values)

```html
<button hx-post="/action" hx-vals='{"key": "value", "id": 42}'>
    Submit
</button>
```

### hx-vals (Dynamic JavaScript Values)

```html
<button hx-post="/action" hx-vals='js:{
    timestamp: new Date().toISOString(),
    screenWidth: window.innerWidth
}'>
    Submit
</button>
```

### hx-include

Include values from other elements:

```html
<!-- Include a specific input -->
<input id="token" name="token" type="hidden" value="abc123">
<button hx-post="/action" hx-include="#token">Submit</button>

<!-- Include all inputs in closest form -->
<button hx-post="/action" hx-include="closest form">Submit</button>

<!-- Include multiple selectors -->
<button hx-post="/action" hx-include="#field1, #field2">Submit</button>
```

### hx-params

Filter which parameters are sent:

```html
<!-- All parameters (default) -->
<form hx-post="/submit" hx-params="*">

<!-- No parameters -->
<button hx-post="/action" hx-params="none">

<!-- Only specific parameters -->
<form hx-post="/search" hx-params="q, category">

<!-- Exclude specific parameters -->
<form hx-post="/submit" hx-params="not debug, internal_id">
```

### hx-headers

Add custom HTTP headers:

```html
<!-- JSON object of headers -->
<div hx-get="/api" hx-headers='{"Authorization": "Bearer token123"}'>
</div>

<!-- Inherited headers (set on body) -->
<body hx-headers='{"X-CSRFToken": "{{token}}"}'>
    <!-- All htmx requests include this header -->
</body>
```

## Request Synchronization

`hx-sync` coordinates concurrent requests from related elements.

### Strategies

```html
<!-- Drop: ignore new request while one is in flight -->
<form hx-post="/save" hx-sync="this:drop">

<!-- Abort: cancel in-flight request and issue new one -->
<input hx-get="/search" hx-sync="this:abort">

<!-- Replace: like abort but queues the new request -->
<input hx-get="/search" hx-sync="this:replace">

<!-- Queue first: queue first pending request only -->
<button hx-post="/action" hx-sync="this:queue first">

<!-- Queue last: keep only the most recent queued request -->
<button hx-post="/action" hx-sync="this:queue last">

<!-- Queue all: queue all requests -->
<button hx-post="/action" hx-sync="this:queue all">
```

### Sync with Other Elements

```html
<!-- Abort other requests from the same form -->
<input name="email"
       hx-post="/validate/email"
       hx-sync="closest form:abort">

<input name="username"
       hx-post="/validate/username"
       hx-sync="closest form:abort">
```

### Programmatic Abort

```javascript
// Cancel a pending request
htmx.trigger(document.getElementById('my-element'), 'htmx:abort');
```

## Response Status Codes

| Status | htmx Behavior |
|--------|---------------|
| `200-299` | Normal swap |
| `204` | No swap, no error (No Content) |
| `286` | Stops polling |
| `300-399` | Follows redirects (browser handles) |
| `400-499` | No swap, triggers error event |
| `500-599` | No swap, triggers error event |

### Customizing Status Code Handling

Override via `htmx:beforeSwap` event:

```javascript
document.addEventListener('htmx:beforeSwap', function(event) {
    if (event.detail.xhr.status === 422) {
        event.detail.shouldSwap = true;       // Force swap
        event.detail.isError = false;         // Don't treat as error
        event.detail.target = document.getElementById('form-errors');
    }
    if (event.detail.xhr.status === 404) {
        event.detail.shouldSwap = true;
        event.detail.target = document.getElementById('not-found');
    }
});
```

## Response Handling Configuration

The `responseHandling` config array defines behavior per status code pattern:

```javascript
htmx.config.responseHandling = [
    { code: "204", swap: false },
    { code: "[23]..", swap: true },
    { code: "422", swap: true, error: false },
    { code: "[45]..", swap: false, error: true },
    { code: "...", swap: false }
];
```

Properties: `code` (regex pattern), `swap` (bool), `error` (bool), `ignoreTitle`, `select`, `target`, `swapOverride`.

## HTTP Caching

htmx respects standard HTTP caching headers:

```python
# Server: use Last-Modified / ETag
from datetime import datetime

@app.get("/data")
async def data(request: Request):
    response = HTMLResponse("<div>Data</div>")
    response.headers["Last-Modified"] = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    response.headers["Vary"] = "HX-Request"  # Different response for htmx vs. regular
    return response
```

**Important:** If your server renders differently based on `HX-Request`, always set `Vary: HX-Request` to prevent caching mismatches.

### Cache Busting

```javascript
// Add a cache-buster param to GET requests
htmx.config.getCacheBusterParam = true;
// Appends ?org.htmx.cache-buster=<targetId> to GETs
```

## File Uploads

```html
<form hx-post="/upload"
      hx-encoding="multipart/form-data"
      hx-target="#result">
    <input type="file" name="document">
    <button type="submit">Upload</button>
    <progress id="progress" value="0" max="100"></progress>
</form>
```

### Upload Progress

```javascript
htmx.on('#upload-form', 'htmx:xhr:progress', function(event) {
    const percent = event.detail.loaded / event.detail.total * 100;
    document.getElementById('progress').value = percent;
});
```

## CSRF Protection

### Via hx-headers on Body

```html
<!-- Django pattern -->
<body hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>

<!-- Read from cookie -->
<body hx-headers='js:{"X-CSRFToken": getCookie("csrftoken")}'>
```

### Via hx-on Event

```html
<body hx-on:htmx:config-request="event.detail.headers['X-CSRFToken'] = getCookie('csrftoken')">
```

### Via JavaScript

```javascript
document.addEventListener('htmx:configRequest', function(event) {
    event.detail.headers['X-CSRFToken'] = getCookie('csrftoken');
});
```

## Common Server Patterns

### Conditional Fragment / Full Page

```python
@app.get("/contacts")
async def contacts(request: Request):
    contacts = await get_contacts()
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse("contacts/_list.html",
            {"request": request, "contacts": contacts})
    return templates.TemplateResponse("contacts/page.html",
        {"request": request, "contacts": contacts})
```

### Server-Triggered Toast Notifications

```python
@app.post("/contacts")
async def create_contact(request: Request):
    contact = await save_contact(data)
    response = templates.TemplateResponse("contacts/_row.html",
        {"request": request, "contact": contact})
    response.headers["HX-Trigger"] = json.dumps({
        "showToast": {"message": "Contact created!", "type": "success"}
    })
    return response
```

### Redirect After POST

```python
@app.post("/login")
async def login(request: Request):
    if authenticated:
        response = Response(status_code=200)
        response.headers["HX-Redirect"] = "/dashboard"
        return response
    return HTMLResponse("<div class='error'>Invalid credentials</div>")
```
