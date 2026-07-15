# htmx — Out-of-Band Swaps

> Source: [htmx.org/docs/#oob_swaps](https://htmx.org/docs/#oob_swaps) | Version: 2.0.x

## Table of Contents

- [What Are OOB Swaps](#what-are-oob-swaps)
- [hx-swap-oob (Response-Side)](#hx-swap-oob-response-side)
- [hx-select-oob (Request-Side)](#hx-select-oob-request-side)
- [OOB Swap Strategies](#oob-swap-strategies)
- [Template Tags for OOB](#template-tags-for-oob)
- [Server-Side Patterns](#server-side-patterns)
- [Updating Other Content](#updating-other-content)
- [Common Pitfalls](#common-pitfalls)
- [Common Patterns](#common-patterns)

## What Are OOB Swaps

Out-of-Band (OOB) swaps allow a single server response to update multiple parts of the page. The main response swaps into `hx-target` as normal, while additional elements marked with `hx-swap-oob` swap into their matching `id` locations anywhere in the DOM.

```
Server Response:
┌─────────────────────────────────┐
│ <div>Main content</div>         │ → swaps into hx-target
│                                 │
│ <div id="count"                 │
│      hx-swap-oob="true">       │
│   42 items                      │ → swaps into #count wherever it is
│ </div>                          │
│                                 │
│ <div id="toast"                 │
│      hx-swap-oob="afterbegin"> │
│   <p>Success!</p>               │ → prepends into #toast
│ </div>                          │
└─────────────────────────────────┘
```

## hx-swap-oob (Response-Side)

Added to elements in the server response. Each OOB element must have an `id` matching an existing element in the DOM.

### Basic Usage

```html
<!-- Server response -->

<!-- Main content (goes into hx-target normally) -->
<div>Updated contact details</div>

<!-- OOB: replace #contact-count with this element -->
<span id="contact-count" hx-swap-oob="true">
    42 contacts
</span>
```

### With Swap Strategy

```html
<!-- Replace innerHTML (default when hx-swap-oob="true") -->
<span id="count" hx-swap-oob="true">42</span>

<!-- Replace with outerHTML -->
<span id="count" hx-swap-oob="outerHTML">
    <span id="count">42</span>
</span>

<!-- Append content -->
<ul id="log" hx-swap-oob="beforeend">
    <li>New log entry</li>
</ul>

<!-- Prepend content -->
<ul id="notifications" hx-swap-oob="afterbegin">
    <li>New notification</li>
</ul>

<!-- Delete the target element -->
<div id="temp-message" hx-swap-oob="delete"></div>
```

## hx-select-oob (Request-Side)

Defined on the requesting element, tells htmx which elements to pick from the response for OOB swapping. Does not require `hx-swap-oob` on the response elements.

```html
<!-- Pick #notification and #sidebar from the response -->
<button hx-get="/data"
        hx-target="#main"
        hx-select-oob="#notification, #sidebar">
    Load
</button>
```

### With Custom Swap Strategy

```html
<!-- Swap #notification with outerHTML, #count with innerHTML -->
<button hx-get="/data"
        hx-target="#main"
        hx-select-oob="#notification:outerHTML, #count:innerHTML">
    Load
</button>
```

## OOB Swap Strategies

All standard swap strategies work with OOB:

| Strategy | hx-swap-oob Value | Behavior |
|----------|-------------------|----------|
| innerHTML | `true` or `innerHTML` | Replace inner content (default) |
| outerHTML | `outerHTML` | Replace entire element |
| afterbegin | `afterbegin` | Prepend as first child |
| beforeend | `beforeend` | Append as last child |
| beforebegin | `beforebegin` | Insert before element |
| afterend | `afterend` | Insert after element |
| delete | `delete` | Remove the element |
| none | `none` | Process but don't swap |

## Template Tags for OOB

Some HTML elements (like `<tr>`, `<td>`, `<option>`) cannot be direct children of `<div>`. Use `<template>` to wrap them for OOB swaps:

```html
<!-- Server response -->

<!-- Main content -->
<div>Updated</div>

<!-- OOB update for a table row -->
<template>
    <tr id="row-42" hx-swap-oob="outerHTML">
        <td>Updated Name</td>
        <td>updated@email.com</td>
    </tr>
</template>

<!-- OOB update for select options -->
<template>
    <select id="category-select" hx-swap-oob="innerHTML">
        <option value="1">Category A</option>
        <option value="2">Category B</option>
    </select>
</template>
```

## Server-Side Patterns

### Python / FastAPI

```python
from fastapi import Request
from fastapi.responses import HTMLResponse

@app.post("/contacts")
async def create_contact(request: Request, name: str, email: str):
    contact = await save_contact(name, email)
    count = await get_contact_count()

    return HTMLResponse(f"""
        <tr id="contact-{contact.id}">
            <td>{contact.name}</td>
            <td>{contact.email}</td>
        </tr>

        <span id="contact-count" hx-swap-oob="true">
            {count} contacts
        </span>
    """)
```

### Django Template

```html
<!-- contacts/create_response.html -->

<!-- Main content: new row -->
<tr id="contact-{{ contact.id }}">
    <td>{{ contact.name }}</td>
    <td>{{ contact.email }}</td>
</tr>

<!-- OOB: update counter -->
<span id="contact-count" hx-swap-oob="true">
    {{ total_contacts }} contacts
</span>

<!-- OOB: clear form -->
<form id="contact-form" hx-swap-oob="outerHTML">
    {% include "contacts/_form.html" %}
</form>
```

### Express / Node.js

```javascript
app.post('/contacts', async (req, res) => {
    const contact = await createContact(req.body);
    const count = await getContactCount();

    res.send(`
        <tr id="contact-${contact.id}">
            <td>${contact.name}</td>
            <td>${contact.email}</td>
        </tr>

        <span id="contact-count" hx-swap-oob="true">
            ${count} contacts
        </span>
    `);
});
```

## Updating Other Content

Three approaches to update content beyond the main target:

### 1. OOB Swaps (Recommended)

Server includes extra elements with `hx-swap-oob` in the response. Best when you know at render time what needs updating.

### 2. Server-Triggered Events

Server sends `HX-Trigger` header; other elements listen and refresh themselves.

```python
# Server
response.headers["HX-Trigger"] = "contactsUpdated"
```

```html
<!-- Another element listens and refreshes -->
<span hx-get="/contacts/count"
      hx-trigger="contactsUpdated from:body"
      hx-swap="innerHTML">
    0 contacts
</span>
```

### 3. hx-on:htmx:afterRequest Path

Use `htmx.ajax()` in an event handler to issue secondary requests:

```html
<button hx-post="/contacts"
        hx-target="#contact-list"
        hx-on:htmx:after-request="htmx.ajax('GET', '/contacts/count', '#counter')">
    Add Contact
</button>
```

## Common Pitfalls

1. **Missing `id` on OOB elements** — OOB swaps require an `id` to find the target in the DOM. No `id` = swap silently skipped.

2. **OOB element not in DOM** — if the target `id` doesn't exist on the page, the OOB swap is ignored (no error).

3. **Nested OOB** — by default nested OOB swaps are processed. Set `htmx.config.allowNestedOobSwaps = false` to disable.

4. **Table elements** — `<tr>`, `<td>`, `<th>` cannot be children of `<div>`. Wrap in `<template>` tags.

5. **OOB + hx-select** — when using `hx-select`, OOB elements are still processed from the full response, not just the selected portion.

## Common Patterns

### CRUD with Count Update

```html
<!-- Page structure -->
<h2>Contacts (<span id="count">0</span>)</h2>
<table>
    <tbody id="contact-rows" hx-target="this" hx-swap="beforeend">
    </tbody>
</table>
<form hx-post="/contacts" hx-target="#contact-rows" hx-swap="beforeend">
    <input name="name" placeholder="Name">
    <input name="email" placeholder="Email">
    <button type="submit">Add</button>
</form>
```

### Flash Messages

```html
<div id="flash-messages"></div>

<!-- Server response includes OOB flash -->
<div id="flash-messages" hx-swap-oob="afterbegin">
    <div class="alert alert-success" hx-get="/empty"
         hx-trigger="load delay:3s" hx-swap="outerHTML">
        Contact saved successfully!
    </div>
</div>
```

### Real-Time Dashboard Widget Update

```html
<div id="stats-widget" hx-get="/stats" hx-trigger="every 30s">
    <!-- Main stats content refreshes here -->
</div>

<!-- Server response includes OOB updates for other widgets -->
<div id="chart-widget" hx-swap-oob="innerHTML">
    <!-- Updated chart HTML -->
</div>
<div id="alerts-widget" hx-swap-oob="beforeend">
    <div class="alert">New alert at 14:30</div>
</div>
```
