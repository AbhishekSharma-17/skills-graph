# htmx — Forms & Validation

> Source: [htmx.org/docs/#validation](https://htmx.org/docs/#validation) | Version: 2.0.x

## Table of Contents

- [Form Handling Basics](#form-handling-basics)
- [Form Submission](#form-submission)
- [Input Values & Parameters](#input-values--parameters)
- [File Uploads](#file-uploads)
- [HTML5 Validation](#html5-validation)
- [Inline Field Validation](#inline-field-validation)
- [Server-Side Validation](#server-side-validation)
- [CSRF Protection](#csrf-protection)
- [Disabling During Submit](#disabling-during-submit)
- [Form Reset After Submit](#form-reset-after-submit)
- [Confirmation Dialogs](#confirmation-dialogs)
- [Common Form Patterns](#common-form-patterns)

## Form Handling Basics

htmx can submit forms via AJAX. A form with `hx-post` (or `hx-put`, `hx-patch`) will include all its input values in the request body.

```html
<form hx-post="/contacts" hx-target="#contact-list" hx-swap="beforeend">
    <input name="name" type="text" placeholder="Name" required>
    <input name="email" type="email" placeholder="Email" required>
    <button type="submit">Add Contact</button>
</form>
<ul id="contact-list"></ul>
```

### Default Behavior

- `<form>` elements trigger on `submit` by default
- All inputs within the form are included
- POST/PUT/PATCH requests use URL-encoded body (`application/x-www-form-urlencoded`)
- GET requests append parameters as query strings

## Form Submission

### Standard AJAX Form

```html
<form hx-post="/api/contacts"
      hx-target="#result"
      hx-swap="innerHTML">
    <label>Name: <input name="name" required></label>
    <label>Email: <input name="email" type="email" required></label>
    <button type="submit">Create</button>
</form>
<div id="result"></div>
```

### Submit Button Outside Form

```html
<form id="my-form" hx-post="/submit">
    <input name="data">
</form>
<button type="submit" form="my-form">Submit</button>
```

### Non-Form Elements as Forms

Any element can submit values using `hx-include`:

```html
<div>
    <input id="search-input" name="q" type="text">
    <button hx-get="/search"
            hx-include="#search-input"
            hx-target="#results">
        Search
    </button>
</div>
```

### Multiple Submit Buttons

```html
<form hx-post="/process">
    <input name="data">
    <button name="action" value="save">Save Draft</button>
    <button name="action" value="publish">Publish</button>
</form>
```

## Input Values & Parameters

### Which Values Are Included

For `<form>` elements: all `<input>`, `<select>`, and `<textarea>` within the form.

For non-form elements: the element's own value (if it has `name`), plus any elements specified by `hx-include`.

### hx-vals: Extra Static Values

```html
<form hx-post="/submit" hx-vals='{"source": "web", "version": 2}'>
    <input name="email">
    <button type="submit">Submit</button>
</form>
```

### hx-vals: Dynamic JavaScript Values

```html
<form hx-post="/submit"
      hx-vals='js:{
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          timestamp: Date.now()
      }'>
    <input name="email">
    <button type="submit">Submit</button>
</form>
```

### hx-params: Filter Parameters

```html
<!-- Only send specific fields -->
<form hx-post="/search" hx-params="q, category">
    <input name="q">
    <select name="category">...</select>
    <input name="debug" type="hidden">  <!-- excluded -->
</form>

<!-- Exclude specific fields -->
<form hx-post="/submit" hx-params="not password_confirm, debug">
    <input name="password" type="password">
    <input name="password_confirm" type="password">  <!-- excluded -->
</form>
```

## File Uploads

Set `hx-encoding="multipart/form-data"` for file uploads:

```html
<form hx-post="/upload"
      hx-encoding="multipart/form-data"
      hx-target="#upload-result">
    <input type="file" name="document">
    <input type="text" name="description" placeholder="Description">
    <button type="submit">Upload</button>
    <progress id="upload-progress" value="0" max="100"></progress>
</form>
<div id="upload-result"></div>
```

### Upload Progress Bar

```html
<form id="upload-form"
      hx-post="/upload"
      hx-encoding="multipart/form-data"
      hx-target="#result">
    <input type="file" name="file">
    <button type="submit">Upload</button>
    <progress id="progress" value="0" max="100"></progress>
</form>

<script>
htmx.on('#upload-form', 'htmx:xhr:progress', function(event) {
    var progress = event.detail.loaded / event.detail.total * 100;
    htmx.find('#progress').setAttribute('value', progress);
});
</script>
```

### Multiple File Upload

```html
<form hx-post="/upload-multiple"
      hx-encoding="multipart/form-data">
    <input type="file" name="files" multiple>
    <button type="submit">Upload All</button>
</form>
```

### Preserving File Inputs After Errors

When a form submission fails validation, the server response replaces the form. File inputs lose their selection. Use `hx-swap-oob` to only update the error area:

```python
# Server-side: on validation error, only return error message
@app.post("/upload")
async def upload(request: Request):
    if not valid:
        return HTMLResponse(
            '<div id="errors" hx-swap-oob="true">'
            '<p class="error">File too large</p></div>',
            status_code=422
        )
```

## HTML5 Validation

htmx integrates with HTML5 form validation by default. If validation fails, the request is not sent.

```html
<form hx-post="/submit">
    <input name="email" type="email" required>  <!-- Must be valid email -->
    <input name="age" type="number" min="18" max="120">  <!-- Range check -->
    <input name="code" pattern="[A-Z]{3}-\d{4}">  <!-- Pattern match -->
    <button type="submit">Submit</button>
</form>
```

### Non-Form Validation

For elements outside a `<form>`, use `hx-validate="true"`:

```html
<div hx-post="/submit" hx-validate="true">
    <input name="email" type="email" required>
    <button type="submit">Submit</button>
</div>
```

### Custom Validation

Use the `htmx:validation:validate` event:

```javascript
document.addEventListener('htmx:validation:validate', function(event) {
    var elt = event.detail.elt;
    if (elt.name === 'username' && elt.value.length < 3) {
        elt.setCustomValidity('Username must be at least 3 characters');
        event.preventDefault();  // Prevent the request
    }
});
```

## Inline Field Validation

Validate individual fields on blur or input change:

```html
<form hx-post="/contacts" hx-target="#result">
    <div>
        <label>Email</label>
        <input name="email" type="email"
               hx-post="/validate/email"
               hx-trigger="blur changed"
               hx-target="next .error"
               hx-swap="innerHTML">
        <span class="error"></span>
    </div>
    <div>
        <label>Username</label>
        <input name="username"
               hx-post="/validate/username"
               hx-trigger="input changed delay:500ms"
               hx-target="next .error"
               hx-swap="innerHTML"
               hx-indicator="next .checking">
        <span class="checking htmx-indicator">Checking...</span>
        <span class="error"></span>
    </div>
    <button type="submit">Create</button>
</form>
```

Server-side validation endpoint:

```python
@app.post("/validate/email")
async def validate_email(email: str):
    if await email_exists(email):
        return HTMLResponse('<span class="error">Email already taken</span>')
    return HTMLResponse('<span class="valid">Available</span>')

@app.post("/validate/username")
async def validate_username(username: str):
    if len(username) < 3:
        return HTMLResponse("Username must be at least 3 characters")
    if await username_taken(username):
        return HTMLResponse("Username already taken")
    return HTMLResponse("")
```

## Server-Side Validation

When the full form fails validation, return the form with error messages:

```python
@app.post("/contacts")
async def create_contact(request: Request):
    form = await request.form()
    errors = validate(form)

    if errors:
        response = templates.TemplateResponse("contacts/_form.html", {
            "request": request,
            "errors": errors,
            "values": dict(form)
        })
        response.status_code = 422
        return response

    contact = await save_contact(form)
    return templates.TemplateResponse("contacts/_row.html",
        {"request": request, "contact": contact})
```

Handle 422 status to swap anyway:

```javascript
document.addEventListener('htmx:beforeSwap', function(event) {
    if (event.detail.xhr.status === 422) {
        event.detail.shouldSwap = true;
        event.detail.isError = false;
    }
});
```

Or configure globally:

```html
<meta name="htmx-config" content='{
    "responseHandling": [
        {"code": "204", "swap": false},
        {"code": "[23]..", "swap": true},
        {"code": "422", "swap": true, "error": false},
        {"code": "[45]..", "swap": false, "error": true}
    ]
}'>
```

## CSRF Protection

### Django

```html
<body hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>
```

### JavaScript Cookie Reader

```html
<body hx-on:htmx:config-request="
    event.detail.headers['X-CSRFToken'] = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
">
```

### Meta Tag Pattern

```html
<meta name="csrf-token" content="{{ csrf_token }}">
<script>
document.addEventListener('htmx:configRequest', function(event) {
    event.detail.headers['X-CSRFToken'] =
        document.querySelector('meta[name="csrf-token"]').content;
});
</script>
```

## Disabling During Submit

Prevent double submission with `hx-disabled-elt`:

```html
<form hx-post="/submit" hx-disabled-elt="find button, find input[type=submit]">
    <input name="data">
    <button type="submit">Submit</button>  <!-- Disabled during request -->
</form>

<!-- Disable the button itself -->
<button hx-post="/action" hx-disabled-elt="this">
    Process
</button>
```

## Form Reset After Submit

### Server Returns Empty Form

The simplest approach — server responds with a blank form:

```html
<form id="add-form" hx-post="/items" hx-target="#items" hx-swap="beforeend">
    <input name="title">
    <button type="submit">Add</button>
</form>

<!-- Server includes OOB reset of the form -->
<!-- Response:
<li>New Item</li>
<form id="add-form" hx-swap-oob="outerHTML">
    (blank form HTML here)
</form>
-->
```

### Using htmx:afterRequest Event

```html
<form hx-post="/items" hx-target="#list" hx-swap="beforeend"
      hx-on:htmx:after-request="if(event.detail.successful) this.reset()">
    <input name="title">
    <button type="submit">Add</button>
</form>
```

## Confirmation Dialogs

### Browser Confirm

```html
<button hx-delete="/item/42"
        hx-confirm="Are you sure you want to delete this item?">
    Delete
</button>
```

### Custom Confirm Dialog

```html
<button hx-delete="/item/42"
        hx-confirm="Delete this item?"
        hx-on:htmx:confirm="
            event.preventDefault();
            showCustomDialog(event.detail.question, function() {
                event.detail.issueRequest(true);
            });
        ">
    Delete
</button>
```

### Prompt for Input

```html
<button hx-post="/rename"
        hx-prompt="Enter new name:"
        hx-vals='{"id": 42}'>
    Rename
</button>
<!-- User input sent as HX-Prompt header -->
```

## Common Form Patterns

### Search with Debounce

```html
<input type="search" name="q"
       hx-get="/search"
       hx-trigger="input changed delay:300ms, search"
       hx-target="#results"
       hx-indicator="#spinner"
       placeholder="Type to search...">
<span id="spinner" class="htmx-indicator">Searching...</span>
<div id="results"></div>
```

### Auto-Save Form

```html
<form hx-post="/autosave"
      hx-trigger="input changed delay:2000ms"
      hx-swap="none"
      hx-indicator="#save-status">
    <textarea name="content">...</textarea>
    <span id="save-status" class="htmx-indicator">Saving...</span>
</form>
```

### Dependent Dropdowns

```html
<select name="country"
        hx-get="/api/states"
        hx-target="#state-select"
        hx-trigger="change"
        hx-indicator="#state-loading">
    <option value="">Select Country</option>
    <option value="us">United States</option>
    <option value="ca">Canada</option>
</select>

<span id="state-loading" class="htmx-indicator">Loading...</span>
<select id="state-select" name="state">
    <option>Select country first</option>
</select>
```
