---
name: htmx
description: "htmx — hypermedia-driven library for building dynamic web UIs with HTML attributes instead of JavaScript. MANDATORY TRIGGERS: htmx, hx-get, hx-post, hx-swap, hx-trigger, hx-target, hx-boost, hypermedia, HATEOAS, htmx.org. Also trigger when user wants to add AJAX to server-rendered HTML, build interactive UIs without a JavaScript framework, return HTML fragments from an API, use server-sent events or WebSockets from HTML, implement infinite scroll or active search with minimal JS, or integrate htmx with Django/FastAPI/Flask/Express. When in doubt about whether to use this skill for hypermedia or HTML-over-the-wire tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["htmx", "hypermedia", "ajax", "html", "hateoas", "server-rendered", "sse", "websocket", "progressive-enhancement"]
---

# htmx — Skill Router

> High-power tools for HTML — access AJAX, CSS Transitions, WebSockets, and SSE directly from HTML attributes.

**Source:** [htmx.org](https://htmx.org/) | **Version:** `2.0.x` | **GitHub:** 45K+ stars

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Getting Started** | `references/00-overview.md` | What htmx is, hypermedia philosophy, installation, first example |
| **Core Attributes** | `references/01-core-attributes.md` | hx-get, hx-post, hx-put, hx-patch, hx-delete, AJAX requests |
| **Triggers** | `references/02-triggers.md` | hx-trigger, events, modifiers (once, delay, throttle), polling |
| **Targets & Swapping** | `references/03-targets-swapping.md` | hx-target, hx-swap, swap strategies, extended selectors |
| **Request & Response** | `references/04-request-response.md` | Headers, hx-vals, hx-include, hx-params, hx-headers, sync |
| **Out-of-Band Swaps** | `references/05-out-of-band.md` | hx-swap-oob, hx-select-oob, multi-target updates |
| **Boosting & History** | `references/06-boosting-history.md` | hx-boost, hx-push-url, hx-replace-url, history cache |
| **Forms & Validation** | `references/07-forms-validation.md` | Form handling, file uploads, inline validation, CSRF |
| **Events & JavaScript API** | `references/08-events-api.md` | Lifecycle events, htmx.on/off/trigger, scripting integration |
| **CSS Transitions & Animation** | `references/09-css-transitions.md` | CSS transitions, View Transitions API, htmx CSS classes |
| **Extensions** | `references/10-extensions.md` | Extension system, SSE, WebSocket, idiomorph, preload |
| **Configuration & Security** | `references/11-configuration-security.md` | htmx.config, security hardening, CSP, XSS prevention |
| **Server Integration** | `references/12-server-integration.md` | Django, FastAPI, Flask, Express patterns, template fragments |

## Installation

```html
<!-- CDN (simplest) -->
<script src="https://unpkg.com/htmx.org@2.0.10"></script>

<!-- npm -->
npm install htmx.org

<!-- Download and self-host -->
<script src="/static/htmx.min.js"></script>
```

## Quick Reference

- [htmx Documentation](https://htmx.org/docs/)
- [Attribute Reference](https://htmx.org/reference/)
- [Examples](https://htmx.org/examples/)
- [Extensions](https://htmx.org/extensions/)
- [GitHub](https://github.com/bigskysoftware/htmx)
