# Gradio — Events & Interactivity

> Source: [gradio.app/guides/blocks-and-event-listeners](https://gradio.app/guides/blocks-and-event-listeners)

## Table of Contents

- [Overview](#overview)
- [Event Types](#event-types)
- [Registering Events](#registering-events)
- [Input/Output Binding](#inputoutput-binding)
- [Event Chaining](#event-chaining)
- [gr.on — Multi-Trigger Binding](#gron--multi-trigger-binding)
- [Component Updates](#component-updates)
- [Continuous Events](#continuous-events)
- [JavaScript Events](#javascript-events)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## Overview

In Gradio Blocks, events connect user actions to Python functions. When a user clicks a button, types in a textbox, or uploads a file, the corresponding event listener calls your function with the specified inputs and updates the specified outputs.

## Event Types

| Event | Components | Triggered When |
|-------|-----------|----------------|
| `.click()` | Button, Image, UploadButton | User clicks the component |
| `.change()` | Most components | Value changes (any source) |
| `.input()` | Textbox, Number, Slider | User directly modifies value |
| `.submit()` | Textbox | User presses Enter |
| `.select()` | Gallery, Chatbot, Dataframe | User selects an item |
| `.upload()` | File, Image, Audio, Video | File upload completes |
| `.clear()` | Most components | User clears the value |
| `.play()` | Audio, Video | Playback starts |
| `.pause()` | Audio, Video | Playback pauses |
| `.stop()` | Audio, Video | Playback/recording stops |
| `.focus()` | Textbox, Number | Component gains focus |
| `.blur()` | Textbox, Number | Component loses focus |
| `.release()` | Slider | User releases the slider |
| `.like()` | Chatbot | User likes/dislikes a message |
| `.load()` | Blocks | App loads in browser |
| `.unload()` | Blocks | Tab closes/refreshes |

### `.change()` vs `.input()`

- `.change()` fires when value changes from any source (user input OR programmatic update)
- `.input()` fires only when the user directly modifies the value
- Use `.input()` to avoid infinite loops when a function both reads and writes the same component

## Registering Events

### Method Syntax

```python
with gr.Blocks() as demo:
    inp = gr.Textbox(label="Name")
    out = gr.Textbox(label="Greeting")
    btn = gr.Button("Greet")

    btn.click(fn=greet, inputs=inp, outputs=out)
```

### Decorator Syntax

```python
with gr.Blocks() as demo:
    inp = gr.Textbox(label="Name")
    out = gr.Textbox(label="Greeting")
    btn = gr.Button("Greet")

    @btn.click(inputs=inp, outputs=out)
    def greet(name):
        return f"Hello {name}!"
```

### No Inputs/Outputs

```python
btn.click(fn=lambda: print("Clicked!"))  # No outputs
btn.click(fn=get_time, outputs=clock)     # No inputs
```

## Input/Output Binding

### List Binding (Positional)

```python
def add(a, b):
    return a + b

btn.click(fn=add, inputs=[num1, num2], outputs=result)
```

### Set Binding (Dictionary)

```python
def subtract(data):
    return data[num1] - data[num2]

btn.click(fn=subtract, inputs={num1, num2}, outputs=result)
```

### Multiple Outputs

```python
def analyze(text):
    return len(text), text.upper(), text.split()

btn.click(
    fn=analyze,
    inputs=text,
    outputs=[char_count, uppercase, words],
)
```

### Dict Return (Selective Update)

```python
def process(text):
    if text:
        return {output: text.upper(), status: "Done"}
    return {status: "Empty input"}

btn.click(fn=process, inputs=text, outputs=[output, status])
```

## Event Chaining

### Sequential Execution

```python
btn.click(fn=step1, inputs=a, outputs=b)\
   .then(fn=step2, inputs=b, outputs=c)\
   .then(fn=step3, inputs=c, outputs=d)
```

### Conditional Chaining

```python
btn.click(fn=validate, inputs=form, outputs=status)\
   .success(fn=save, inputs=form, outputs=result)\
   .failure(fn=show_error, outputs=error_msg)
```

- `.then()` — always runs after previous event completes
- `.success()` — runs only if previous event did NOT raise an error
- `.failure()` — runs only if previous event DID raise an error

### Loading States

```python
def slow_process(text):
    time.sleep(5)
    return text.upper()

btn.click(
    fn=slow_process,
    inputs=inp,
    outputs=out,
    show_progress="full",  # "full" | "minimal" | "hidden"
)
```

## gr.on — Multi-Trigger Binding

Bind multiple triggers to one function:

```python
# Method syntax
gr.on(
    triggers=[name.submit, greet_btn.click],
    fn=greet,
    inputs=name,
    outputs=output,
)

# Decorator syntax
@gr.on(triggers=[name.submit, greet_btn.click], inputs=name, outputs=output)
def greet(name):
    return f"Hello {name}!"
```

### Auto-Binding (No Triggers)

```python
@gr.on(inputs=[a, b], outputs=result)
def add(x, y):
    return x + y
# Automatically binds to .change() of a and b
```

## Component Updates

Return a new component instance to update properties:

```python
def toggle_visibility(show):
    return gr.Textbox(visible=show)

checkbox.change(fn=toggle_visibility, inputs=checkbox, outputs=textbox)
```

### gr.update() Shorthand

```python
def toggle(show):
    return gr.update(visible=show, value="Shown!" if show else "")
```

### Skip Updates

```python
def maybe_update(flag):
    if flag:
        return "New value"
    return gr.skip()  # Keep current value
```

## Continuous Events

### Timer Component

```python
timer = gr.Timer(value=5)  # Every 5 seconds

timer.tick(fn=get_data, outputs=dashboard)
```

### Shorthand Component Binding

```python
# Updates every time inputs change AND on app load
live_output = gr.Number(lambda a, b: a * b, inputs=[num1, num2])
```

### Queue Behavior

| Mode | Behavior |
|------|----------|
| `"once"` (default) | No new submissions while one is pending |
| `"multiple"` | Unlimited concurrent submissions |
| `"always_last"` | Queue latest, discard intermediate (default for `.change()`) |

```python
inp.change(
    fn=process,
    inputs=inp,
    outputs=out,
    trigger_mode="always_last",
)
```

## JavaScript Events

```python
# JS alongside Python
btn.click(
    fn=process,
    inputs=inp,
    outputs=out,
    js="(x) => { console.log('Input:', x); return x; }",
)

# JS only (no Python)
btn.click(
    fn=None,
    js="() => { alert('Hello!'); }",
)
```

## Common Patterns

### Form Validation

```python
def validate_email(email):
    if "@" not in email:
        raise gr.Error("Invalid email address")
    return gr.update(interactive=True)  # Enable submit

email.change(fn=validate_email, inputs=email, outputs=submit_btn)
```

### Progress Bar

```python
def long_task(data, progress=gr.Progress()):
    results = []
    for i, item in enumerate(data):
        progress(i / len(data), desc=f"Processing {i+1}/{len(data)}")
        results.append(process(item))
    return results
```

### Debounced Input

```python
# .key_up() with time_limit for debouncing
textbox.key_up(
    fn=search,
    inputs=textbox,
    outputs=results,
    trigger_mode="always_last",
)
```

### Loading Indicator

```python
with gr.Blocks() as demo:
    btn = gr.Button("Process")
    status = gr.Textbox(label="Status")
    result = gr.Textbox(label="Result")

    btn.click(fn=lambda: "Processing...", outputs=status)\
       .then(fn=heavy_compute, inputs=data, outputs=result)\
       .then(fn=lambda: "Done!", outputs=status)
```

## Common Pitfalls

1. **Infinite loops**: Using `.change()` on a component that is both input and output causes infinite re-triggering — use `.input()` instead, or use `gr.State` as intermediary
2. **Event ordering**: `.then()` chains are sequential, not parallel — use separate event listeners for independent operations
3. **Missing queue**: Generator functions require `demo.queue()` to work (enabled by default in recent versions)
4. **JS execution order**: JavaScript runs before Python in event listeners with both `fn` and `js`
5. **Trigger mode confusion**: `.change()` defaults to `"always_last"` while `.click()` defaults to `"once"` — this means rapid clicking is ignored, but rapid typing isn't
