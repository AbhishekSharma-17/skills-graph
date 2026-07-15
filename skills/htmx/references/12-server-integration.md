# htmx — Server Integration

> Source: [htmx.org/server-examples/](https://htmx.org/server-examples/) | Version: 2.0.x

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Django Integration](#django-integration)
- [FastAPI Integration](#fastapi-integration)
- [Flask Integration](#flask-integration)
- [Express.js Integration](#expressjs-integration)
- [Go Integration](#go-integration)
- [Template Fragment Pattern](#template-fragment-pattern)
- [Testing htmx Endpoints](#testing-htmx-endpoints)
- [Common Server Patterns](#common-server-patterns)
- [Production Considerations](#production-considerations)

## Architecture Overview

htmx applications follow the **Hypermedia-Driven Application (HDA)** architecture:

```
Browser (htmx)              Server
┌──────────────┐            ┌──────────────┐
│ HTML + htmx  │  ←─HTML──  │ Templates    │
│ attributes   │            │ + Business   │
│              │  ──HTTP──→ │   Logic      │
│ Thin client  │            │ Thick server │
└──────────────┘            └──────────────┘
```

### Key Server Responsibilities

1. Detect htmx requests via `HX-Request` header
2. Return HTML fragments (not JSON) for htmx requests
3. Return full pages for direct/bookmark navigation
4. Include CSRF protection for state-changing requests
5. Use response headers (`HX-Trigger`, `HX-Redirect`, etc.) to control client behavior

## Django Integration

### django-htmx Package

```bash
pip install django-htmx
```

```python
# settings.py
MIDDLEWARE = [
    ...
    "django_htmx.middleware.HtmxMiddleware",
]
```

```python
# views.py
from django.shortcuts import render

def contact_list(request):
    contacts = Contact.objects.all()
    if request.htmx:
        return render(request, "contacts/_list.html", {"contacts": contacts})
    return render(request, "contacts/page.html", {"contacts": contacts})

def create_contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save()
            if request.htmx:
                return render(request, "contacts/_row.html", {"contact": contact})
            return redirect("contact_list")
        if request.htmx:
            return render(request, "contacts/_form.html", {"form": form}, status=422)
    form = ContactForm()
    return render(request, "contacts/_form.html", {"form": form})
```

### Django Template Fragments

Use `django-render-block` for rendering individual template blocks:

```bash
pip install django-render-block
```

```python
from render_block import render_block_to_string

def contact_list(request):
    contacts = Contact.objects.all()
    context = {"contacts": contacts}
    if request.htmx:
        return HttpResponse(
            render_block_to_string("contacts/page.html", "contact_list", context, request)
        )
    return render(request, "contacts/page.html", context)
```

```html
<!-- contacts/page.html -->
{% extends "base.html" %}
{% block content %}
    <h1>Contacts</h1>
    {% block contact_list %}
    <table>
        {% for contact in contacts %}
        <tr id="contact-{{ contact.id }}">
            <td>{{ contact.name }}</td>
            <td>{{ contact.email }}</td>
        </tr>
        {% endfor %}
    </table>
    {% endblock %}
{% endblock %}
```

### Django CSRF

```html
<!-- Option 1: hx-headers on body -->
<body hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>

<!-- Option 2: via JavaScript -->
<script>
document.addEventListener('htmx:configRequest', (e) => {
    e.detail.headers['X-CSRFToken'] = '{{ csrf_token }}';
});
</script>
```

### Django HX-Trigger Response

```python
from django.http import HttpResponse
import json

def delete_contact(request, pk):
    Contact.objects.filter(pk=pk).delete()
    response = HttpResponse(status=200)
    response["HX-Trigger"] = json.dumps({
        "contactDeleted": {"id": pk},
        "showToast": {"message": "Contact deleted", "type": "success"}
    })
    return response
```

## FastAPI Integration

### Basic Setup with Jinja2

```python
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def is_htmx(request: Request) -> bool:
    return request.headers.get("HX-Request") == "true"
```

### CRUD Example

```python
@app.get("/contacts", response_class=HTMLResponse)
async def list_contacts(request: Request):
    contacts = await get_all_contacts()
    template = "contacts/_list.html" if is_htmx(request) else "contacts/page.html"
    return templates.TemplateResponse(template, {
        "request": request,
        "contacts": contacts
    })

@app.post("/contacts", response_class=HTMLResponse)
async def create_contact(request: Request):
    form = await request.form()
    errors = validate_contact(form)

    if errors:
        response = templates.TemplateResponse("contacts/_form.html", {
            "request": request,
            "errors": errors,
            "values": dict(form)
        }, status_code=422)
        return response

    contact = await save_contact(form)
    count = await get_contact_count()

    response = templates.TemplateResponse("contacts/_row.html", {
        "request": request,
        "contact": contact,
        "count": count
    })
    response.headers["HX-Trigger"] = json.dumps({
        "showToast": {"message": f"Contact '{contact.name}' created"}
    })
    return response

@app.delete("/contacts/{contact_id}", response_class=HTMLResponse)
async def delete_contact(request: Request, contact_id: int):
    await remove_contact(contact_id)
    response = HTMLResponse("", status_code=200)
    response.headers["HX-Trigger"] = "contactsUpdated"
    return response
```

### fasthx Package

```bash
pip install fasthx
```

```python
from fasthx import Jinja

jinja = Jinja(templates)

@app.get("/items")
@jinja.hx("items/_list.html", no_data=True)
@jinja.page("items/page.html")
async def list_items(request: Request):
    return {"items": await get_items()}
```

### Active Search with FastAPI

```python
@app.get("/search", response_class=HTMLResponse)
async def search(request: Request, q: str = ""):
    results = await search_contacts(q)
    return templates.TemplateResponse("contacts/_search_results.html", {
        "request": request,
        "results": results,
        "query": q
    })
```

```html
<!-- templates/contacts/_search.html -->
<input type="search" name="q"
       hx-get="/search"
       hx-trigger="input changed delay:300ms"
       hx-target="#results"
       hx-indicator="#spinner"
       placeholder="Search contacts...">
<span id="spinner" class="htmx-indicator">Searching...</span>
<div id="results"></div>
```

## Flask Integration

### flask-htmx Package

```bash
pip install flask-htmx
```

```python
from flask import Flask, render_template, request
from flask_htmx import Htmx

app = Flask(__name__)
htmx = Htmx(app)

@app.route("/contacts")
def contacts():
    contacts = get_all_contacts()
    if htmx:
        return render_template("contacts/_list.html", contacts=contacts)
    return render_template("contacts/page.html", contacts=contacts)

@app.route("/contacts", methods=["POST"])
def create_contact():
    contact = save_contact(request.form)
    if htmx:
        response = make_response(
            render_template("contacts/_row.html", contact=contact)
        )
        response.headers["HX-Trigger"] = "contactsUpdated"
        return response
    return redirect(url_for("contacts"))
```

### Manual Detection

```python
@app.route("/contacts")
def contacts():
    if request.headers.get("HX-Request"):
        return render_template("contacts/_list.html", contacts=contacts)
    return render_template("contacts/page.html", contacts=contacts)
```

## Express.js Integration

```javascript
const express = require('express');
const app = express();

app.set('view engine', 'ejs');

function isHtmx(req) {
    return req.headers['hx-request'] === 'true';
}

app.get('/contacts', async (req, res) => {
    const contacts = await getContacts();
    if (isHtmx(req)) {
        return res.render('contacts/_list', { contacts });
    }
    res.render('contacts/page', { contacts });
});

app.post('/contacts', async (req, res) => {
    const contact = await createContact(req.body);
    if (isHtmx(req)) {
        res.set('HX-Trigger', JSON.stringify({
            showToast: { message: 'Contact created!' }
        }));
        return res.render('contacts/_row', { contact });
    }
    res.redirect('/contacts');
});

app.delete('/contacts/:id', async (req, res) => {
    await deleteContact(req.params.id);
    res.set('HX-Trigger', 'contactsUpdated');
    res.send('');
});
```

## Go Integration

```go
package main

import (
    "html/template"
    "net/http"
)

func isHtmx(r *http.Request) bool {
    return r.Header.Get("HX-Request") == "true"
}

func contactsHandler(w http.ResponseWriter, r *http.Request) {
    contacts := getContacts()
    if isHtmx(r) {
        tmpl := template.Must(template.ParseFiles("templates/contacts/_list.html"))
        tmpl.Execute(w, contacts)
        return
    }
    tmpl := template.Must(template.ParseFiles(
        "templates/base.html", "templates/contacts/page.html",
    ))
    tmpl.Execute(w, contacts)
}
```

## Template Fragment Pattern

The core pattern for htmx server integration: **same template, two rendering modes**.

### Approach 1: Separate Templates

```
templates/
  contacts/
    page.html          ← Full page (extends base, includes _list)
    _list.html         ← Fragment (just the list)
    _row.html          ← Single row fragment
    _form.html         ← Form fragment
```

### Approach 2: Block Rendering

```html
<!-- page.html -->
{% extends "base.html" %}
{% block content %}
    {% block contact_list %}
        <!-- Render this block alone for htmx requests -->
        <table>{% for c in contacts %}<tr>...</tr>{% endfor %}</table>
    {% endblock %}
{% endblock %}
```

### Approach 3: Conditional Layout

```html
<!-- Jinja2 -->
{% if not request.headers.get('HX-Request') %}
<!DOCTYPE html>
<html>
<head>...</head>
<body>
{% endif %}

    <div id="content">
        <!-- Actual content -->
    </div>

{% if not request.headers.get('HX-Request') %}
</body>
</html>
{% endif %}
```

## Testing htmx Endpoints

```python
# pytest + httpx: send HX-Request header, assert fragment (no <!DOCTYPE)
async def test_htmx_fragment():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/contacts", headers={"HX-Request": "true"})
        assert resp.status_code == 200
        assert "<!DOCTYPE" not in resp.text

# Django: use HTTP_HX_REQUEST kwarg
def test_htmx(self):
    resp = self.client.get("/contacts/", HTTP_HX_REQUEST="true")
    self.assertNotContains(resp, "<!DOCTYPE")
```

## Common Server Patterns

### Redirect After Form Submit

```python
@app.post("/login")
async def login(request: Request):
    if authenticated:
        response = Response(status_code=200)
        response.headers["HX-Redirect"] = "/dashboard"
        return response
    return HTMLResponse("<p class='error'>Invalid credentials</p>", status_code=401)
```

### Flash Messages via OOB

```python
def flash_oob(message, level="info"):
    return f'''<div id="flash" hx-swap-oob="afterbegin">
        <div class="alert alert-{level}"
             hx-get="/empty" hx-trigger="load delay:5s" hx-swap="outerHTML">
            {message}
        </div>
    </div>'''
```

## Production Considerations

### Caching

```python
@app.get("/data")
async def data(request: Request):
    response = HTMLResponse(render_data())
    if is_htmx(request):
        response.headers["Vary"] = "HX-Request"
        response.headers["Cache-Control"] = "private, max-age=60"
    return response
```

### Error Handling

Return fragments for htmx requests, full pages otherwise:

```python
@app.exception_handler(404)
async def not_found(request: Request, exc):
    if is_htmx(request):
        return HTMLResponse("<p>Not found</p>", status_code=404)
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
```

### Performance Tips

1. Keep HTML fragments small — return only what changed
2. Use OOB swaps sparingly — each adds DOM operations
3. Set appropriate polling intervals; prefer SSE/WebSocket for real-time
4. Enable HTTP caching with `Vary: HX-Request`
5. Rate-limit polling endpoints to prevent abuse
