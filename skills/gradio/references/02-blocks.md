# Gradio — Blocks API

> Source: [gradio.app/docs/gradio/blocks](https://gradio.app/docs/gradio/blocks)

## Table of Contents

- [Overview](#overview)
- [Basic Pattern](#basic-pattern)
- [Layout Components](#layout-components)
- [Constructor Parameters](#constructor-parameters)
- [Event Registration](#event-registration)
- [Conditional Visibility](#conditional-visibility)
- [Dynamic UIs](#dynamic-uis)
- [Multiple Pages](#multiple-pages)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## Overview

`gr.Blocks` is Gradio's low-level API for building custom web applications with full control over layout, event handling, and data flow between components. Use Blocks when Interface is too limiting.

### Interface vs Blocks

| Aspect | Interface | Blocks |
|--------|-----------|--------|
| Layout | Fixed (inputs → outputs) | Fully customizable |
| Event triggers | Single submit | Multiple events per component |
| Data flow | Linear (inputs → fn → outputs) | Arbitrary (cascading, circular) |
| Multiple functions | No | Yes |
| Component updates | No | Yes (return new instances) |

## Basic Pattern

```python
import gradio as gr

def update(name):
    return f"Welcome, {name}!"

with gr.Blocks() as demo:
    gr.Markdown("# My App")
    with gr.Row():
        inp = gr.Textbox(placeholder="Your name", label="Name")
        out = gr.Textbox(label="Greeting")
    btn = gr.Button("Run")
    btn.click(fn=update, inputs=inp, outputs=out)

demo.launch()
```

## Layout Components

### Row — Horizontal Layout

```python
with gr.Row():
    left = gr.Textbox(label="Left")
    right = gr.Textbox(label="Right")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `equal_height` | `bool` | `True` | Match heights of children |
| `variant` | `'default' \| 'panel' \| 'compact'` | `'default'` | Visual style |

### Column — Vertical Layout

```python
with gr.Column(scale=2):
    title = gr.Textbox(label="Title")
    body = gr.Textbox(label="Body", lines=5)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `scale` | `int` | `1` | Relative width in a Row |
| `min_width` | `int` | `320` | Minimum pixel width |

### Row + Column Nesting

```python
with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column(scale=1):
            image_input = gr.Image(label="Upload")
        with gr.Column(scale=2):
            label_output = gr.Label(label="Prediction")
            json_output = gr.JSON(label="Details")
```

### Tab — Tabbed Sections

```python
with gr.Blocks() as demo:
    with gr.Tab("Generate"):
        prompt = gr.Textbox(label="Prompt")
        output = gr.Image(label="Result")
        btn = gr.Button("Generate")
    with gr.Tab("Settings"):
        model = gr.Dropdown(["v1", "v2"], label="Model")
        steps = gr.Slider(1, 100, value=50, label="Steps")
```

### Accordion — Collapsible Section

```python
with gr.Accordion("Advanced Settings", open=False):
    temperature = gr.Slider(0, 2, value=0.7, label="Temperature")
    top_p = gr.Slider(0, 1, value=0.9, label="Top P")
```

### Group — Visual Grouping

```python
with gr.Group():
    username = gr.Textbox(label="Username")
    password = gr.Textbox(label="Password", type="password")
```

### Sidebar — Collapsible Side Panel

```python
with gr.Blocks() as demo:
    with gr.Sidebar():
        model = gr.Dropdown(["GPT-4", "Claude"], label="Model")
        temp = gr.Slider(0, 2, value=0.7)
    chatbot = gr.Chatbot()
```

## Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `title` | `str` | `"Gradio"` | Browser tab title |
| `theme` | `Theme \| str \| None` | `None` | UI theme |
| `css` | `str \| None` | `None` | Inline CSS |
| `js` | `str \| bool \| None` | `None` | Inline JavaScript |
| `head` | `str \| None` | `None` | Custom `<head>` HTML |
| `fill_height` | `bool` | `False` | Expand vertically |
| `fill_width` | `bool` | `False` | Expand horizontally |
| `delete_cache` | `tuple[int,int] \| None` | `None` | Auto-cleanup: `(check_every, older_than)` in seconds |
| `analytics_enabled` | `bool \| None` | `None` | Telemetry toggle |

## Event Registration

### Direct Method

```python
btn.click(fn=process, inputs=[inp1, inp2], outputs=out)
inp.change(fn=validate, inputs=inp, outputs=status)
inp.submit(fn=process, inputs=inp, outputs=out)
```

### Event Chaining

```python
btn.click(fn=step1, inputs=a, outputs=b)\
   .then(fn=step2, inputs=b, outputs=c)\
   .then(fn=step3, inputs=c, outputs=d)
```

- `.then()` — runs regardless of success/failure
- `.success()` — runs only if previous succeeded
- `.failure()` — runs only if previous raised an error

### gr.on() — Multiple Triggers

```python
@gr.on(triggers=[name.submit, greet_btn.click], inputs=name, outputs=output)
def greet(name):
    return f"Hello {name}!"
```

### Load/Unload Events

```python
with gr.Blocks() as demo:
    # ...
    demo.load(fn=on_load, outputs=status)    # App opens
    demo.unload(fn=on_close)                 # Tab closes
```

## Conditional Visibility

```python
def toggle_advanced(show):
    return gr.update(visible=show)

checkbox = gr.Checkbox(label="Show advanced")
advanced = gr.Column(visible=False)
checkbox.change(fn=toggle_advanced, inputs=checkbox, outputs=advanced)
```

### Returning Component Updates

```python
def update_textbox(choice):
    if choice == "short":
        return gr.Textbox(lines=1, placeholder="Brief answer")
    else:
        return gr.Textbox(lines=10, placeholder="Detailed response")

radio = gr.Radio(["short", "long"], label="Mode")
output = gr.Textbox()
radio.change(fn=update_textbox, inputs=radio, outputs=output)
```

### Special Return Values

```python
def maybe_update(flag):
    if flag:
        return "Updated value"
    return gr.skip()  # Keep current value unchanged
```

## Dynamic UIs

### Render Decorator

```python
with gr.Blocks() as demo:
    count = gr.Number(value=3, label="Number of fields")

    @gr.render(inputs=count)
    def render_fields(n):
        boxes = [gr.Textbox(label=f"Field {i+1}") for i in range(int(n))]
        btn = gr.Button("Submit")
        btn.click(fn=lambda *args: list(args), inputs=boxes, outputs=gr.JSON())
```

## Multiple Pages

```python
with gr.Blocks() as demo:
    with gr.Tab("Text"):
        text_in = gr.Textbox()
        text_out = gr.Textbox()
        gr.Button("Analyze").click(fn=analyze_text, inputs=text_in, outputs=text_out)

    with gr.Tab("Image"):
        img_in = gr.Image()
        img_out = gr.Label()
        gr.Button("Classify").click(fn=classify_img, inputs=img_in, outputs=img_out)

    with gr.Tab("Audio"):
        audio_in = gr.Audio()
        audio_out = gr.Textbox()
        gr.Button("Transcribe").click(fn=transcribe, inputs=audio_in, outputs=audio_out)
```

## Common Patterns

### Dashboard Layout

```python
with gr.Blocks() as demo:
    gr.Markdown("# Analytics Dashboard")

    with gr.Row():
        metric1 = gr.Number(label="Total Users", value=1250)
        metric2 = gr.Number(label="Active Today", value=89)
        metric3 = gr.Number(label="Revenue", value=5420)

    with gr.Row():
        with gr.Column(scale=2):
            chart = gr.Plot(label="Trends")
        with gr.Column(scale=1):
            table = gr.Dataframe(label="Top Users")

    refresh = gr.Button("Refresh")
    refresh.click(fn=fetch_data, outputs=[metric1, metric2, metric3, chart, table])
```

### Sidebar + Main Content

```python
with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column(scale=1, min_width=200):
            gr.Markdown("### Settings")
            model = gr.Dropdown(["v1", "v2"], label="Model")
            temp = gr.Slider(0, 2, value=0.7, label="Temp")

        with gr.Column(scale=3):
            gr.Markdown("### Output")
            output = gr.Textbox(lines=10, label="Response")
            btn = gr.Button("Generate")

    btn.click(fn=generate, inputs=[model, temp], outputs=output)
```

## Common Pitfalls

1. **Component outside `with gr.Blocks()`**: All components must be created inside the context manager
2. **Event listener on wrong component**: `.click()` is for Buttons; use `.change()` or `.submit()` for Textbox
3. **Circular dependencies**: A component that is both input and output of the same event can cause infinite loops — use `gr.State` as intermediary
4. **Forgetting `outputs`**: If your function returns a value but no output is specified, the return is silently discarded
5. **Scale confusion**: `scale` only works inside a `Row` parent; it's ignored in standalone Columns
