# Streamlit — Session State

> Source: [docs.streamlit.io/develop/concepts/architecture/session-state](https://docs.streamlit.io/develop/concepts/architecture/session-state) | Version: 1.59.x

## Table of Contents

- [What Is Session State](#what-is-session-state)
- [Basic Usage](#basic-usage)
- [Widget Keys](#widget-keys)
- [Callbacks](#callbacks)
- [Initialization Patterns](#initialization-patterns)
- [Query Params](#query-params)
- [Context Object](#context-object)
- [Common Patterns](#common-patterns)
- [Pitfalls and Limitations](#pitfalls-and-limitations)

## What Is Session State

A **session** is a single browser tab connected to the Streamlit server. Since scripts rerun top-to-bottom on every interaction, variables reset each time. `st.session_state` provides a dictionary-like namespace that **persists across reruns** within the same session.

```
Script rerun 1: st.session_state.counter = 0
Script rerun 2: st.session_state.counter = 1  (preserved!)
Script rerun 3: st.session_state.counter = 2  (preserved!)
```

Session state is:
- **Per-tab** — each browser tab has its own state
- **Per-session** — lost when the tab closes or server restarts
- **Shared across pages** — persists in multipage apps
- **Not persistent** — no automatic database storage

## Basic Usage

### Two Access Syntaxes

```python
# Attribute syntax
st.session_state.counter = 0
value = st.session_state.counter

# Dictionary syntax
st.session_state["counter"] = 0
value = st.session_state["counter"]
```

### Check, Read, Write, Delete

```python
# Check existence
if "counter" not in st.session_state:
    st.session_state.counter = 0

# Read
st.write(st.session_state.counter)

# Update
st.session_state.counter += 1

# Delete
del st.session_state.counter

# Iterate
for key in st.session_state:
    st.write(f"{key}: {st.session_state[key]}")
```

### Store Any Python Object

```python
st.session_state.df = pd.DataFrame({"a": [1, 2, 3]})
st.session_state.model = load_model()
st.session_state.messages = []
st.session_state.config = {"theme": "dark", "lang": "en"}
```

## Widget Keys

Linking a widget to session state via the `key` parameter:

```python
st.text_input("Name", key="user_name")
# st.session_state.user_name now holds the widget's current value
```

### Auto-Sync Behavior

When a widget has a `key`:
1. The widget value is stored in `st.session_state[key]` automatically
2. Setting `st.session_state[key]` before the widget renders pre-populates it
3. The value updates on every interaction

```python
# Pre-populate a widget
if "temperature" not in st.session_state:
    st.session_state.temperature = 50.0

st.slider("Temperature", -100.0, 100.0, key="temperature")
st.write(f"Current: {st.session_state.temperature}")
```

### Programmatic Widget Updates

Set a widget's value before it renders:

```python
if st.button("Reset"):
    st.session_state.user_name = ""

st.text_input("Name", key="user_name")
```

## Callbacks

Functions called **before the script reruns** when a widget value changes:

### on_click (buttons)

```python
def increment():
    st.session_state.counter += 1

st.button("Increment", on_click=increment)
```

### on_change (input widgets)

```python
def name_changed():
    st.session_state.greeting = f"Hello, {st.session_state.user_name}!"

st.text_input("Name", key="user_name", on_change=name_changed)

if "greeting" in st.session_state:
    st.write(st.session_state.greeting)
```

### Callback Arguments

```python
def update_score(player, points):
    st.session_state[f"{player}_score"] += points

st.button(
    "Add 10 points",
    on_click=update_score,
    args=("player1",),           # Positional args
    kwargs={"points": 10},       # Keyword args
)
```

### Callback Execution Order

1. User interacts with widget
2. Callback executes (with the **new** widget value already in session state)
3. Script reruns top-to-bottom

This means in a callback you can safely read `st.session_state[key]` for the updated value.

## Initialization Patterns

### Guard Pattern (Most Common)

```python
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.counter = 0
    st.session_state.data = []
    st.session_state.user = None
```

### setdefault Pattern

```python
st.session_state.setdefault("counter", 0)
st.session_state.setdefault("messages", [])
```

### Function-Based Init

```python
def init_state():
    defaults = {
        "counter": 0,
        "messages": [],
        "config": {"theme": "light"},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_state()
```

## Query Params

Bind widget values to URL query parameters for shareable URLs:

```python
# Read query params
params = st.query_params
page = params.get("page", "home")

# Set query params
st.query_params["page"] = "settings"
st.query_params["filter"] = "active"

# Clear
st.query_params.clear()
```

### Widget-Linked Query Params

Some widgets support direct URL binding via the `key` parameter combined with `st.query_params`.

## Context Object

Access request context (cookies, headers, locale):

```python
ctx = st.context

# Headers (read-only dict)
user_agent = ctx.headers.get("User-Agent")

# Cookies (read-only dict)
session_cookie = ctx.cookies.get("session_id")

# Locale
locale = ctx.locale  # e.g., "en_US"
```

## Common Patterns

### Step-by-Step Wizard

```python
if "step" not in st.session_state:
    st.session_state.step = 1

if st.session_state.step == 1:
    st.header("Step 1: Personal Info")
    name = st.text_input("Name", key="name")
    if st.button("Next") and name:
        st.session_state.step = 2
        st.rerun()

elif st.session_state.step == 2:
    st.header("Step 2: Preferences")
    st.write(f"Welcome, {st.session_state.name}")
    color = st.selectbox("Favorite color", ["Red", "Blue", "Green"], key="color")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Back"):
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.button("Submit"):
            st.session_state.step = 3
            st.rerun()

elif st.session_state.step == 3:
    st.header("Complete!")
    st.write(f"Name: {st.session_state.name}")
    st.write(f"Color: {st.session_state.color}")
```

### Toggle with State

```python
if "show_settings" not in st.session_state:
    st.session_state.show_settings = False

if st.button("Toggle Settings"):
    st.session_state.show_settings = not st.session_state.show_settings

if st.session_state.show_settings:
    st.write("Settings panel content")
```

### Shopping Cart

```python
if "cart" not in st.session_state:
    st.session_state.cart = []

products = ["Widget A", "Widget B", "Widget C"]

for product in products:
    col1, col2 = st.columns([3, 1])
    col1.write(product)
    if col2.button("Add", key=f"add_{product}"):
        st.session_state.cart.append(product)

st.sidebar.header("Cart")
for item in st.session_state.cart:
    st.sidebar.write(f"- {item}")
```

### Authentication State

```python
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if password == st.secrets["app_password"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password")
else:
    st.write("Welcome! You are logged in.")
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()
```

## Pitfalls and Limitations

### 1. Cannot Set Button/File Uploader State

```python
# Raises StreamlitAPIException
st.session_state.my_button = True    # ❌
st.session_state.my_file = file_obj  # ❌
```

### 2. Setting State After Widget Renders

```python
# Wrong — setting state after widget causes inconsistency
st.slider("Value", key="val")
st.session_state.val = 50          # ❌ Conflicting update

# Correct — set before widget or use callback
if "val" not in st.session_state:
    st.session_state.val = 50
st.slider("Value", key="val")      # ✅
```

### 3. State Lost on Tab Close / Server Restart

Session state lives in server memory. For persistence, write to a database:

```python
def save_state():
    db.save(dict(st.session_state))

def load_state():
    saved = db.load(user_id)
    if saved:
        for k, v in saved.items():
            st.session_state[k] = v
```

### 4. Mutating Collections

Mutating a list or dict in session state works but can be surprising:

```python
# This works — in-place mutation persists
st.session_state.items.append("new")

# This also works
st.session_state.items = st.session_state.items + ["new"]
```

### 5. Serialization Mode

Enable strict serialization for debugging:

```toml
# .streamlit/config.toml
[runner]
enforceSerializableSessionState = true
```

Only pickle-compatible objects are allowed. Lambdas, open files, and DB connections will raise errors.

## Related Topics

- `02-input-widgets.md` — Widget keys and callbacks
- `06-caching-performance.md` — Caching vs state
- `07-forms-fragments.md` — Forms batch state updates
- `08-multipage-apps.md` — State shared across pages
