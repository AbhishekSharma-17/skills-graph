# htmx — Events & JavaScript API

> Source: [htmx.org/reference/#events](https://htmx.org/reference/#events) | Version: 2.0.x

## Table of Contents

- [Event System Overview](#event-system-overview)
- [Request Lifecycle Events](#request-lifecycle-events)
- [Swap & Settle Events](#swap--settle-events)
- [Validation Events](#validation-events)
- [History Events](#history-events)
- [Error Events](#error-events)
- [Extension Events](#extension-events)
- [hx-on Attribute](#hx-on-attribute)
- [JavaScript API](#javascript-api)
- [Integration with Other Libraries](#integration-with-other-libraries)
- [Debugging with Events](#debugging-with-events)

## Event System Overview

htmx fires events at every stage of request processing. Events use kebab-case naming (e.g., `htmx:before-request`) and are standard DOM events — listen with `addEventListener` or `htmx.on()`.

```javascript
// Listen for events
document.addEventListener('htmx:afterSwap', function(event) {
    console.log('Swapped into:', event.detail.target);
});

// Using htmx.on() shorthand
htmx.on('htmx:afterSwap', function(event) {
    console.log('Swapped into:', event.detail.target);
});

// Listen on a specific element
htmx.on('#my-form', 'htmx:afterRequest', function(event) {
    console.log('Request complete');
});
```

## Request Lifecycle Events

Events fire in this order during a request:

### htmx:configRequest

Fired before the request. Modify headers, parameters, or URL.

```javascript
document.addEventListener('htmx:configRequest', function(event) {
    // Add a custom header
    event.detail.headers['X-Custom'] = 'value';

    // Modify parameters
    event.detail.parameters['extra'] = 'data';

    // Change the request URL
    event.detail.path = '/different-url';
});
```

`event.detail` properties: `headers`, `parameters`, `path`, `verb`, `elt`, `target`, `triggeringEvent`.

### htmx:beforeRequest

Fired just before the AJAX request. Cancel by calling `event.preventDefault()`.

```javascript
document.addEventListener('htmx:beforeRequest', function(event) {
    if (!isAuthenticated()) {
        event.preventDefault();
        window.location = '/login';
    }
});
```

### htmx:beforeSend

Fired after the request is configured but before it's sent. Last chance to inspect or modify.

### htmx:afterRequest

Fired after the request completes (success or failure).

```javascript
htmx.on('htmx:afterRequest', function(event) {
    if (event.detail.successful) {
        console.log('Success:', event.detail.xhr.status);
    } else {
        console.log('Failed:', event.detail.xhr.status);
    }
});
```

`event.detail` properties: `elt`, `xhr`, `target`, `requestConfig`, `successful`, `failed`.

### htmx:xhr:loadstart / htmx:xhr:progress / htmx:xhr:loadend

XHR progress events (useful for file uploads).

```javascript
htmx.on('#upload-form', 'htmx:xhr:progress', function(event) {
    var percent = (event.detail.loaded / event.detail.total) * 100;
    document.getElementById('progress').style.width = percent + '%';
});
```

## Swap & Settle Events

### htmx:beforeSwap

Fired before content is swapped. Modify swap behavior or cancel.

```javascript
document.addEventListener('htmx:beforeSwap', function(event) {
    // Handle error responses
    if (event.detail.xhr.status === 422) {
        event.detail.shouldSwap = true;
        event.detail.isError = false;
    }
    if (event.detail.xhr.status === 404) {
        event.detail.shouldSwap = true;
        event.detail.target = document.getElementById('not-found');
    }
});
```

`event.detail` properties: `shouldSwap`, `isError`, `target`, `swapOverride`, `serverResponse`.

### htmx:afterSwap

Fired after content is swapped into the DOM.

```javascript
htmx.on('htmx:afterSwap', function(event) {
    // Initialize any new components
    initTooltips(event.detail.target);
});
```

### htmx:beforeSettle

Fired before the settle phase (before new attribute values are applied).

### htmx:afterSettle

Fired after settle completes. Good for running code on the final state.

```javascript
htmx.on('htmx:afterSettle', function(event) {
    // Content is fully settled — safe to read final DOM state
    highlightCode(event.detail.target);
});
```

### htmx:oobBeforeSwap / htmx:oobAfterSwap

Fired before/after each out-of-band swap.

### htmx:load

Fired when new content is loaded into the DOM (similar to `DOMContentLoaded` for new elements).

```javascript
htmx.onLoad(function(content) {
    // Initialize third-party libraries on new content
    $(content).find('.date-picker').datepicker();
    hljs.highlightAll();
});
```

## Validation Events

### htmx:validation:validate

Custom validation before the request.

```javascript
document.addEventListener('htmx:validation:validate', function(event) {
    var elt = event.detail.elt;
    if (elt.name === 'password' && elt.value.length < 8) {
        elt.setCustomValidity('Password must be 8+ characters');
        event.preventDefault();
    } else {
        elt.setCustomValidity('');
    }
});
```

### htmx:validation:failed

Fired when an element fails validation.

### htmx:validation:halted

Fired when a request is halted due to validation failure.

## History Events

### htmx:beforeHistorySave

Fired before the DOM is saved to history cache. Modify the DOM before snapshotting.

```javascript
document.addEventListener('htmx:beforeHistorySave', function() {
    // Remove ephemeral UI before caching
    document.querySelectorAll('.toast').forEach(el => el.remove());
});
```

### htmx:historyRestore

Fired when content is restored from history cache.

### htmx:pushedIntoHistory / htmx:replacedInHistory

Fired after URL push/replace in browser history.

## Error Events

### htmx:responseError

Fired on HTTP error responses (4xx, 5xx).

```javascript
htmx.on('htmx:responseError', function(event) {
    console.error('HTTP Error:', event.detail.xhr.status);
    showErrorToast('Request failed: ' + event.detail.xhr.statusText);
});
```

### htmx:sendError

Fired on network errors (connection refused, timeout).

```javascript
htmx.on('htmx:sendError', function(event) {
    showErrorToast('Network error — please check your connection');
});
```

### htmx:timeout

Fired when a request exceeds the configured timeout.

### htmx:sseError / htmx:wsError

Fired on SSE/WebSocket connection errors.

## Extension Events

### htmx:beforeTransition

Fired before a View Transition. Cancel to skip the transition.

### htmx:confirm

Fired for `hx-confirm`. Supports async confirmation patterns.

```javascript
document.addEventListener('htmx:confirm', function(event) {
    event.preventDefault();
    showModal(event.detail.question).then(function(confirmed) {
        if (confirmed) {
            event.detail.issueRequest(true);
        }
    });
});
```

### htmx:validateUrl

Fired before a request to validate the URL. Cancel to block the request.

```javascript
document.addEventListener('htmx:validateUrl', function(event) {
    if (!event.detail.sameHost) {
        event.preventDefault();  // Block cross-origin requests
    }
});
```

## hx-on Attribute

Handle events inline on elements without separate `<script>` tags:

```html
<!-- htmx events -->
<button hx-get="/data"
        hx-on:htmx:before-request="showSpinner()"
        hx-on:htmx:after-request="hideSpinner()">
    Load
</button>

<!-- DOM events -->
<input hx-on:focus="this.select()"
       hx-on:blur="validateField(this)">

<!-- Modify request configuration -->
<form hx-post="/api"
      hx-on:htmx:config-request="
          event.detail.headers['Authorization'] = 'Bearer ' + getToken();
      ">
    <button type="submit">Submit</button>
</form>

<!-- Conditional behavior -->
<div hx-on:htmx:after-swap="
    if (event.detail.xhr.status === 201) {
        showToast('Created!');
    }
">
```

## JavaScript API

### htmx.ajax()

Issue AJAX requests programmatically:

```javascript
// Simple GET
htmx.ajax('GET', '/api/data', '#target');

// With options
htmx.ajax('POST', '/api/data', {
    target: '#result',
    swap: 'innerHTML',
    values: { key: 'value' },
    headers: { 'X-Custom': 'header' }
});

// Returns a Promise
htmx.ajax('GET', '/data', '#target').then(function() {
    console.log('Request complete');
});
```

### htmx.on() / htmx.off()

Register/remove event listeners:

```javascript
var handler = htmx.on('htmx:afterSwap', function(e) {
    console.log('Swapped');
});

// Remove later
htmx.off('htmx:afterSwap', handler);

// Listen on specific element
htmx.on('#my-div', 'htmx:load', function(e) { ... });
```

### htmx.onLoad()

Register a function to run on new content:

```javascript
htmx.onLoad(function(content) {
    // content is the new element loaded into the DOM
    initComponents(content);
});
```

### htmx.trigger()

Trigger events on elements:

```javascript
htmx.trigger('#my-element', 'myCustomEvent');
htmx.trigger('#my-element', 'myEvent', { detail: { key: 'value' } });
htmx.trigger(document.body, 'refreshAll');
```

### htmx.find() / htmx.findAll()

Find elements:

```javascript
var el = htmx.find('#my-id');
var els = htmx.findAll('.my-class');
var child = htmx.find('#parent', '.child');
```

### htmx.process()

Process htmx attributes on dynamically added content:

```javascript
var newContent = document.createElement('div');
newContent.innerHTML = '<button hx-get="/data">Load</button>';
document.body.appendChild(newContent);
htmx.process(newContent);  // Activate hx-* attributes
```

### htmx.swap()

Swap content programmatically:

```javascript
htmx.swap('#target', '<p>New content</p>', {
    swapStyle: 'innerHTML',
    settle: true
});
```

### htmx.addClass() / htmx.removeClass() / htmx.toggleClass()

```javascript
htmx.addClass('#el', 'active');
htmx.removeClass('#el', 'active', 500);  // delay in ms
htmx.toggleClass('#el', 'visible');
```

### htmx.closest() / htmx.remove()

```javascript
var form = htmx.closest(button, 'form');
htmx.remove(element);
htmx.remove(element, 500);  // remove after 500ms
```

### htmx.values()

Get the values of an element and its inputs:

```javascript
var vals = htmx.values(document.getElementById('my-form'));
// { name: "John", email: "john@example.com" }
```

## Integration with Other Libraries

### Alpine.js

```html
<div x-data="{ count: 0 }"
     hx-get="/items"
     hx-trigger="load"
     hx-on:htmx:after-settle="count = $el.querySelectorAll('li').length">
    <p>Items: <span x-text="count"></span></p>
    <ul id="items"></ul>
</div>
```

### jQuery

```javascript
htmx.onLoad(function(content) {
    $(content).find('.datepicker').datepicker();
    $(content).find('[data-toggle="tooltip"]').tooltip();
});
```

### Hyperscript

```html
<button hx-get="/data" _="on htmx:afterSwap add .highlight to #result">
    Load
</button>
```

## Debugging with Events

### Log All Events

```javascript
htmx.logAll();
// Logs every htmx event to the console
```

### Custom Logger

```javascript
htmx.logger = function(elt, event, data) {
    if (event === 'htmx:afterRequest') {
        console.log('Request to:', data.path, 'Status:', data.xhr?.status);
    }
};
```

### Monitor Specific Element

```javascript
['htmx:configRequest', 'htmx:beforeRequest', 'htmx:afterRequest',
 'htmx:beforeSwap', 'htmx:afterSwap'].forEach(function(event) {
    htmx.on('#my-element', event, function(e) {
        console.log(event, e.detail);
    });
});
```
