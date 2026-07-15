# htmx — Core Attributes

> Source: [htmx.org/reference](https://htmx.org/reference/) | Version: 2.0.x

## Table of Contents

- [AJAX Request Attributes](#ajax-request-attributes)
- [Targeting Attributes](#targeting-attributes)
- [Swapping Attributes](#swapping-attributes)
- [Value & Parameter Attributes](#value--parameter-attributes)
- [UI Feedback Attributes](#ui-feedback-attributes)
- [Behavioral Attributes](#behavioral-attributes)
- [Advanced Attributes](#advanced-attributes)
- [Complete Attribute Reference](#complete-attribute-reference)
- [Data Attributes Prefix](#data-attributes-prefix)

## AJAX Request Attributes

These five attributes issue HTTP requests when triggered:

### hx-get

Issues a `GET` request to the specified URL.

```html
<button hx-get="/api/users">Load Users</button>

<!-- With path parameters -->
<button hx-get="/api/users/42">Get User 42</button>

<!-- Relative and absolute paths -->
<button hx-get="/api/data">Absolute</button>
<button hx-get="data">Relative to current URL</button>
```

### hx-post

Issues a `POST` request. Includes form values in the request body.

```html
<form hx-post="/api/contacts">
    <input name="name" type="text">
    <input name="email" type="email">
    <button type="submit">Create</button>
</form>
```

### hx-put

Issues a `PUT` request for full resource replacement.

```html
<form hx-put="/api/contacts/42">
    <input name="name" value="Updated Name">
    <button type="submit">Update</button>
</form>
```

### hx-patch

Issues a `PATCH` request for partial updates.

```html
<input name="email" hx-patch="/api/contacts/42"
       hx-trigger="change"
       hx-target="closest tr">
```

### hx-delete

Issues a `DELETE` request. Parameters are sent as URL query parameters (not body).

```html
<button hx-delete="/api/contacts/42"
        hx-confirm="Are you sure?"
        hx-target="closest tr"
        hx-swap="outerHTML">
    Delete
</button>
```

## Targeting Attributes

### hx-target

Specifies which element receives the response. Accepts CSS selectors and extended syntax.

```html
<!-- CSS selector -->
<button hx-get="/data" hx-target="#results">Load</button>

<!-- this — target the triggering element itself -->
<button hx-get="/data" hx-target="this">Load</button>

<!-- closest — nearest ancestor matching selector -->
<button hx-get="/data" hx-target="closest div">Load</button>

<!-- find — first descendant matching selector -->
<div hx-target="find .output">
    <button hx-get="/data">Load</button>
    <span class="output"></span>
</div>

<!-- next / previous — sibling matching selector -->
<button hx-get="/data" hx-target="next .results">Load</button>
<div class="results"></div>

<!-- Default: when omitted, targets the element itself -->
<div hx-get="/data">This div gets replaced</div>
```

### hx-select

Picks a subset of the response HTML via CSS selector before swapping.

```html
<!-- Only swap in the #content element from the full page response -->
<a hx-get="/page" hx-select="#content" hx-target="#main">
    Load Page
</a>
```

## Swapping Attributes

### hx-swap

Controls how content replaces the target. Default: `innerHTML`.

```html
<!-- Replace inner content (default) -->
<div hx-get="/data" hx-swap="innerHTML">...</div>

<!-- Replace entire element including itself -->
<div hx-get="/data" hx-swap="outerHTML">...</div>

<!-- Insert before first child -->
<ul hx-get="/item" hx-swap="afterbegin">...</ul>

<!-- Append after last child -->
<ul hx-get="/item" hx-swap="beforeend">...</ul>

<!-- Insert before the target -->
<div hx-get="/sibling" hx-swap="beforebegin">...</div>

<!-- Insert after the target -->
<div hx-get="/sibling" hx-swap="afterend">...</div>

<!-- Delete target regardless of response -->
<button hx-delete="/item/1" hx-swap="delete" hx-target="closest tr">
    Remove
</button>

<!-- No swap — only process response headers and OOB -->
<button hx-post="/action" hx-swap="none">Fire and Forget</button>
```

### Swap Modifiers

Append modifiers to the swap value:

```html
<!-- Delay before swapping -->
<div hx-get="/data" hx-swap="innerHTML swap:500ms">...</div>

<!-- Delay before settling (applying new attributes) -->
<div hx-get="/data" hx-swap="innerHTML settle:500ms">...</div>

<!-- Use View Transitions API -->
<div hx-get="/data" hx-swap="innerHTML transition:true">...</div>

<!-- Scroll target to top after swap -->
<div hx-get="/data" hx-swap="innerHTML scroll:top">...</div>

<!-- Show element at top of viewport -->
<div hx-get="/data" hx-swap="innerHTML show:top">...</div>

<!-- Combine modifiers -->
<div hx-get="/data" hx-swap="innerHTML swap:200ms settle:100ms scroll:top">
</div>

<!-- Focus scroll control -->
<div hx-get="/form" hx-swap="innerHTML focus-scroll:true">...</div>

<!-- Ignore title tags in response -->
<div hx-get="/page" hx-swap="innerHTML ignoreTitle:true">...</div>
```

## Value & Parameter Attributes

### hx-vals

Adds extra values to the request as a JSON object.

```html
<!-- Static JSON -->
<button hx-post="/action" hx-vals='{"key": "value", "count": 42}'>
    Submit
</button>

<!-- Dynamic JavaScript (js: prefix) -->
<button hx-post="/action" hx-vals='js:{time: new Date().toISOString()}'>
    Submit with timestamp
</button>
```

### hx-headers

Adds custom HTTP headers to the request.

```html
<!-- Static headers -->
<div hx-get="/api" hx-headers='{"X-Custom": "value"}'>...</div>

<!-- CSRF token pattern -->
<body hx-headers='{"X-CSRFToken": "{{csrf_token}}"}'>
    <!-- All htmx requests in this body include the CSRF token -->
</body>
```

### hx-include

Includes additional element values in the request via CSS selector.

```html
<input id="search" name="q" type="text">
<button hx-get="/search" hx-include="#search">Search</button>

<!-- Include all inputs in a form -->
<button hx-post="/submit" hx-include="closest form">Submit</button>

<!-- Inherit and extend -->
<div hx-include="#filter">
    <button hx-get="/data" hx-include="inherit #sort">
        <!-- includes both #filter and #sort -->
    </button>
</div>
```

### hx-params

Filters which parameters are included in the request.

```html
<!-- Include all (default) -->
<form hx-post="/submit" hx-params="*">...</form>

<!-- Include none -->
<button hx-get="/refresh" hx-params="none">Refresh</button>

<!-- Include only specific params -->
<form hx-post="/search" hx-params="q, category">...</form>

<!-- Exclude specific params -->
<form hx-post="/submit" hx-params="not password_confirm">...</form>
```

### hx-encoding

Sets the encoding type for the request. Required for file uploads.

```html
<form hx-post="/upload" hx-encoding="multipart/form-data">
    <input type="file" name="document">
    <button type="submit">Upload</button>
</form>
```

## UI Feedback Attributes

### hx-indicator

Shows a loading indicator during requests.

```html
<button hx-get="/slow" hx-indicator="#spinner">
    Load Data
</button>
<span id="spinner" class="htmx-indicator">Loading...</span>
```

Default CSS makes `.htmx-indicator` elements hidden. When a request is in flight, the `htmx-request` class is added to the triggering element, making indicators visible:

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

### hx-disabled-elt

Disables elements during a request to prevent double-submission.

```html
<form hx-post="/submit" hx-disabled-elt="find button">
    <input name="data">
    <button type="submit">Submit</button>
</form>

<!-- Disable self -->
<button hx-post="/action" hx-disabled-elt="this">Click Me</button>

<!-- Disable multiple -->
<form hx-post="/submit" hx-disabled-elt="find button, find input">
```

### hx-confirm

Shows a browser confirmation dialog before issuing the request.

```html
<button hx-delete="/item/1" hx-confirm="Are you sure you want to delete this?">
    Delete
</button>
```

### hx-prompt

Prompts the user for input. The value is sent in the `HX-Prompt` header.

```html
<button hx-post="/rename" hx-prompt="Enter new name:">
    Rename
</button>
```

## Behavioral Attributes

### hx-boost

Converts standard links and forms into AJAX requests for SPA-like navigation.

```html
<!-- Boost all links and forms within -->
<div hx-boost="true">
    <a href="/page1">Page 1</a>           <!-- becomes AJAX GET -->
    <a href="/page2">Page 2</a>           <!-- becomes AJAX GET -->
    <form action="/submit" method="post">  <!-- becomes AJAX POST -->
        <button type="submit">Go</button>
    </form>
</div>
```

### hx-preserve

Preserves an element across swaps (e.g., video players, iframes). The element must have an `id`.

```html
<div id="video-player" hx-preserve>
    <video src="..."></video>
</div>
```

### hx-disable

Disables htmx processing on an element and all its children. Useful for user-generated content.

```html
<div hx-disable>
    <!-- No hx-* attributes processed here, even if present -->
    <div hx-get="/malicious">This is ignored</div>
</div>
```

## Advanced Attributes

### hx-sync

Coordinates requests between elements to prevent race conditions.

```html
<!-- Abort previous requests when a new one starts -->
<input hx-get="/search" hx-trigger="input" hx-sync="this:abort">

<!-- Queue requests, drop all but the last -->
<form hx-post="/save" hx-sync="this:drop">...</form>

<!-- Abort requests from the closest form -->
<input hx-post="/validate" hx-sync="closest form:abort">
```

Strategies: `drop`, `abort`, `replace`, `queue first`, `queue last`, `queue all`.

### hx-request

Configures request behavior per-element.

```html
<!-- Custom timeout -->
<div hx-get="/slow" hx-request='"timeout": 10000'>...</div>

<!-- Disable credentials -->
<div hx-get="/api" hx-request='"credentials": false'>...</div>
```

### hx-on\*

Handles events inline on elements (htmx or DOM events).

```html
<!-- htmx event -->
<button hx-get="/data" hx-on:htmx:before-request="console.log('loading...')">
    Load
</button>

<!-- DOM event -->
<div hx-on:click="alert('clicked')">Click me</div>

<!-- Modify request config -->
<button hx-post="/api"
        hx-on:htmx:config-request="event.detail.headers['X-Custom'] = 'value'">
    Send
</button>
```

### hx-validate

Forces HTML5 validation on non-form elements before issuing requests.

```html
<div hx-post="/submit" hx-validate="true">
    <input required name="email" type="email">
    <button type="submit">Send</button>
</div>
```

## Complete Attribute Reference

| Attribute | Purpose |
|-----------|---------|
| `hx-get` | Issue GET request |
| `hx-post` | Issue POST request |
| `hx-put` | Issue PUT request |
| `hx-patch` | Issue PATCH request |
| `hx-delete` | Issue DELETE request |
| `hx-target` | CSS selector for swap target |
| `hx-swap` | Swap strategy + modifiers |
| `hx-trigger` | Event(s) that trigger the request |
| `hx-select` | CSS selector to pick response subset |
| `hx-select-oob` | OOB element selection from response |
| `hx-swap-oob` | Mark response elements for OOB swap |
| `hx-vals` | Extra JSON values for request |
| `hx-vars` | Dynamic values (comma-separated expressions) |
| `hx-headers` | Custom request headers (JSON) |
| `hx-include` | Include additional element values |
| `hx-params` | Filter request parameters |
| `hx-encoding` | Request encoding (e.g., multipart/form-data) |
| `hx-indicator` | Loading indicator selector |
| `hx-disabled-elt` | Elements to disable during request |
| `hx-confirm` | Confirmation dialog text |
| `hx-prompt` | Prompt dialog text |
| `hx-boost` | Convert links/forms to AJAX |
| `hx-push-url` | Push URL to browser history |
| `hx-replace-url` | Replace URL in browser history |
| `hx-history` | Control history snapshot caching |
| `hx-history-elt` | Element to snapshot for history |
| `hx-preserve` | Preserve element across swaps |
| `hx-disable` | Disable htmx processing |
| `hx-disinherit` | Disable attribute inheritance |
| `hx-inherit` | Re-enable inheritance when globally disabled |
| `hx-sync` | Synchronize concurrent requests |
| `hx-validate` | Force HTML5 validation |
| `hx-request` | Configure request options |
| `hx-ext` | Enable htmx extensions |
| `hx-on\*` | Inline event handlers |

## Data Attributes Prefix

All `hx-*` attributes can be used with a `data-` prefix for HTML validation:

```html
<!-- These are equivalent -->
<button hx-get="/data">Load</button>
<button data-hx-get="/data">Load</button>
```
