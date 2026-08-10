# Gradio — State Management

> Source: [gradio.app/guides/state-in-blocks](https://gradio.app/guides/state-in-blocks)

## Table of Contents

- [Overview](#overview)
- [Three State Approaches](#three-state-approaches)
- [Global State](#global-state)
- [Session State — gr.State](#session-state--grstate)
- [Browser State — gr.BrowserState](#browser-state--grbrowserstate)
- [State Change Detection](#state-change-detection)
- [Complex Objects in State](#complex-objects-in-state)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## Overview

Gradio supports three scopes of state: global (shared across all users), session (per-user, per-tab), and browser (persists across page refreshes via localStorage).

## Three State Approaches

| Approach | Scope | Survives Refresh | Shared | Use Case |
|----------|-------|-------------------|--------|----------|
| Global variables | All users | Yes (in-memory) | Yes | Counters, model cache |
| `gr.State` | Per session | No | No | Shopping cart, form wizard |
| `gr.BrowserState` | Per browser | Yes (localStorage) | No | User prefs, theme choice |

## Global State

Variables declared outside functions are shared across all users:

```python
import gradio as gr

total_requests = 0

def process(text):
    global total_requests
    total_requests += 1
    return f"Request #{total_requests}: {text.upper()}"

with gr.Blocks() as demo:
    inp = gr.Textbox(label="Input")
    out = gr.Textbox(label="Output")
    btn = gr.Button("Process")
    btn.click(fn=process, inputs=inp, outputs=out)

demo.launch()
```

**Warning**: Global state has no concurrency protection. Use `threading.Lock` for thread safety:

```python
import threading

lock = threading.Lock()
shared_data = {}

def safe_update(key, value):
    with lock:
        shared_data[key] = value
```

## Session State — gr.State

`gr.State` maintains data across multiple submissions within a single page session. Data is isolated per user and cleared on refresh.

### Basic Usage

```python
import gradio as gr

def add_item(item, cart):
    cart.append(item)
    return cart, cart

with gr.Blocks() as demo:
    cart = gr.State(value=[])           # Hidden state
    item = gr.Textbox(label="Item")
    display = gr.JSON(label="Cart")
    btn = gr.Button("Add to Cart")

    # State must be in BOTH inputs and outputs
    btn.click(fn=add_item, inputs=[item, cart], outputs=[cart, display])
```

### Key Rules

1. Create with `gr.State(value=default_value)`
2. Default value must be deepcopy-able (lists, dicts, primitives)
3. Include State in both `inputs` and `outputs` of event listeners
4. Add the state variable as a function parameter AND return value

### Counter Example

```python
def increment(count):
    count += 1
    return count, f"Count: {count}"

with gr.Blocks() as demo:
    counter = gr.State(value=0)
    display = gr.Textbox(label="Counter")
    btn = gr.Button("Increment")
    btn.click(fn=increment, inputs=counter, outputs=[counter, display])
```

### Multi-Step Form Wizard

```python
def next_step(current_step, form_data, field_value):
    form_data[f"step_{current_step}"] = field_value
    return current_step + 1, form_data, get_field_label(current_step + 1)

with gr.Blocks() as demo:
    step = gr.State(value=0)
    data = gr.State(value={})
    field = gr.Textbox(label="Step 1: Name")
    btn = gr.Button("Next")
    btn.click(
        fn=next_step,
        inputs=[step, data, field],
        outputs=[step, data, field],
    )
```

## Browser State — gr.BrowserState

Persists data in the browser's localStorage — survives page refreshes and app restarts.

```python
import gradio as gr

def save_preference(theme, stored):
    stored = theme
    return stored, f"Saved: {theme}"

with gr.Blocks() as demo:
    saved_theme = gr.BrowserState(
        default_value="light",
        storage_key="user_theme",
    )
    theme = gr.Dropdown(["light", "dark", "auto"], label="Theme")
    status = gr.Textbox(label="Status")

    theme.change(
        fn=save_preference,
        inputs=[theme, saved_theme],
        outputs=[saved_theme, status],
    )

    # Restore on load
    demo.load(
        fn=lambda s: s,
        inputs=saved_theme,
        outputs=theme,
    )
```

## State Change Detection

`gr.State` supports a `.change()` listener:

```python
cart = gr.State(value=[])
cart_display = gr.JSON()

cart.change(fn=lambda c: c, inputs=cart, outputs=cart_display)
```

### Detection Rules

| Value Type | Change Detected When |
|-----------|---------------------|
| Primitives | Value differs from previous |
| Lists, sets, dicts | Any element added, removed, or modified |
| Objects | Hash value changes (implement `__hash__`) |

## Complex Objects in State

### Custom Classes

```python
class GameState:
    def __init__(self):
        self.score = 0
        self.level = 1
        self.inventory = []

    def __hash__(self):
        return hash((self.score, self.level, tuple(self.inventory)))

state = gr.State(value=GameState())
```

### Non-Deepcopyable Objects

For objects that can't be deepcopied (e.g., database connections, locks):

```python
sessions = {}

def get_db(request: gr.Request):
    session_id = request.session_hash
    if session_id not in sessions:
        sessions[session_id] = create_db_connection()
    return sessions[session_id]

def cleanup(request: gr.Request):
    session_id = request.session_hash
    if session_id in sessions:
        sessions[session_id].close()
        del sessions[session_id]

with gr.Blocks() as demo:
    demo.unload(fn=cleanup)
```

## Common Patterns

### Undo/Redo History

```python
def update_with_history(new_value, history, current_idx):
    history = history[:current_idx + 1]
    history.append(new_value)
    return new_value, history, len(history) - 1

def undo(history, current_idx):
    if current_idx > 0:
        current_idx -= 1
    return history[current_idx], history, current_idx

with gr.Blocks() as demo:
    history = gr.State(value=[""])
    idx = gr.State(value=0)
    editor = gr.Textbox(label="Editor")
    undo_btn = gr.Button("Undo")

    editor.change(
        fn=update_with_history,
        inputs=[editor, history, idx],
        outputs=[editor, history, idx],
    )
    undo_btn.click(fn=undo, inputs=[history, idx], outputs=[editor, history, idx])
```

### Conversation Memory

```python
def chat(message, conversation):
    conversation.append({"role": "user", "content": message})
    response = llm_call(conversation)
    conversation.append({"role": "assistant", "content": response})
    return "", conversation, conversation

with gr.Blocks() as demo:
    history = gr.State(value=[])
    chatbot = gr.Chatbot(type="messages")
    msg = gr.Textbox(label="Message")

    msg.submit(fn=chat, inputs=[msg, history], outputs=[msg, history, chatbot])
```

### Session Cleanup

```python
with gr.Blocks(delete_cache=(3600, 3600)) as demo:
    # Cleanup: check every 3600s, delete caches older than 3600s
    state = gr.State(value=init_resources())

    demo.unload(fn=cleanup_resources)
```

## Common Pitfalls

1. **Forgetting State in outputs**: If State is only in inputs, updates are lost — it must be returned and listed in outputs
2. **Mutable default values**: `gr.State(value=[])` creates one list shared initially — each session gets a deep copy, but nested mutable objects can still cause issues
3. **State not surviving refresh**: `gr.State` is session-scoped — use `gr.BrowserState` for persistence across refreshes
4. **Thread safety with global state**: Multiple concurrent users can race on global variables — use locks
5. **Session hash dependency**: `request.session_hash` changes if the user refreshes — don't use it as a permanent identifier
6. **Cleanup**: Sessions persist for 60 minutes after tab closure by default — implement `unload()` handlers for resource cleanup
