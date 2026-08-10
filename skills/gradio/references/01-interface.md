# Gradio — Interface API

> Source: [gradio.app/docs/gradio/interface](https://gradio.app/docs/gradio/interface)

## Table of Contents

- [Overview](#overview)
- [Constructor Parameters](#constructor-parameters)
- [Launch Parameters](#launch-parameters)
- [Examples & Caching](#examples--caching)
- [String Shortcuts](#string-shortcuts)
- [From Pipeline](#from-pipeline)
- [Flagging](#flagging)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## Overview

`gr.Interface` is the highest-level API in Gradio. It wraps a single Python function with auto-generated input/output components, a submit button, and optional examples — ideal when you have one function to demo.

```python
import gradio as gr

def classify(image):
    # ... model inference
    return {"cat": 0.9, "dog": 0.1}

demo = gr.Interface(fn=classify, inputs="image", outputs="label")
demo.launch()
```

## Constructor Parameters

### Core (Required)

| Parameter | Type | Description |
|-----------|------|-------------|
| `fn` | `Callable` | Function to wrap; params map to inputs, returns to outputs |
| `inputs` | `str \| Component \| list \| None` | Input component(s) — string shortcut or instance |
| `outputs` | `str \| Component \| list \| None` | Output component(s) — string shortcut or instance |

### UI Customization

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `title` | `str \| None` | `None` | Heading above the interface |
| `description` | `str \| None` | `None` | Text below title (Markdown/HTML) |
| `article` | `str \| None` | `None` | Extended text below components |
| `live` | `bool` | `False` | Auto-rerun on input change (no submit button) |
| `fill_width` | `bool` | `False` | Expand to fill container width |
| `show_progress` | `'full' \| 'minimal' \| 'hidden'` | `'full'` | Progress animation style |

### Button Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `submit_btn` | `str \| Button` | `"Submit"` | Submit button label/instance |
| `stop_btn` | `str \| Button` | `"Stop"` | Stop button label/instance |
| `clear_btn` | `str \| Button \| None` | `"Clear"` | Clear button; `None` hides it |

### Additional Inputs

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `additional_inputs` | `str \| Component \| list \| None` | `None` | Components in accordion below main inputs |
| `additional_inputs_accordion` | `str \| Accordion \| None` | `None` | Accordion config for extra inputs |

### Batch Processing

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `batch` | `bool` | `False` | Process multiple inputs simultaneously |
| `max_batch_size` | `int` | `4` | Max batch size when `batch=True` |

### API & Concurrency

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_visibility` | `'public' \| 'private' \| 'undocumented'` | `'public'` | API endpoint visibility |
| `api_name` | `str \| None` | `None` | Custom endpoint name |
| `concurrency_limit` | `int \| None \| 'default'` | `'default'` | Max simultaneous executions |

### Streaming

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `time_limit` | `int \| None` | `30` | Seconds limit for streaming |
| `stream_every` | `float` | `0.5` | Latency for stream chunks (seconds) |

### Theming

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `theme` | `Theme \| str \| None` | `None` | Built-in or Hub theme |
| `css` | `str \| None` | `None` | Inline CSS |
| `css_paths` | `str \| Path \| list \| None` | `None` | External CSS files |
| `js` | `str \| bool \| None` | `None` | Inline JavaScript |
| `head` | `str \| None` | `None` | Custom HTML in `<head>` |

## Launch Parameters

```python
demo.launch(
    server_name="0.0.0.0",     # Network accessible
    server_port=7860,           # Custom port
    share=True,                 # Public share link
    auth=("user", "pass"),      # Simple auth
    inbrowser=True,             # Open browser tab
    debug=True,                 # Block thread (Colab)
    max_file_size="10mb",       # Upload limit
    quiet=True,                 # Suppress logs
    favicon_path="icon.png",    # Custom favicon
    ssr_mode=True,              # Server-side rendering
    pwa=True,                   # Progressive Web App
    mcp_server=True,            # MCP server mode
    allowed_paths=["./data"],   # Accessible directories
    blocked_paths=["./secret"], # Blocked directories
)
```

## Examples & Caching

Provide sample inputs for users to try:

```python
demo = gr.Interface(
    fn=image_classifier,
    inputs=gr.Image(type="pil"),
    outputs=gr.Label(num_top_classes=3),
    examples=[
        ["cat.jpg"],
        ["dog.jpg"],
        ["bird.jpg"],
    ],
    cache_examples=True,       # Pre-compute outputs
    cache_mode="lazy",         # "eager" or "lazy"
    examples_per_page=5,
    example_labels=["Cat", "Dog", "Bird"],
)
```

- **`cache_examples=True`**: Pre-computes and caches outputs for examples
- **`cache_mode="eager"`**: Caches all at startup
- **`cache_mode="lazy"`**: Caches on first access
- **`examples_per_page`**: Paginate examples display

## String Shortcuts

| Shortcut | Component |
|----------|-----------|
| `"text"`, `"textbox"` | `gr.Textbox()` |
| `"number"` | `gr.Number()` |
| `"image"` | `gr.Image()` |
| `"audio"` | `gr.Audio()` |
| `"video"` | `gr.Video()` |
| `"file"` | `gr.File()` |
| `"dataframe"` | `gr.Dataframe()` |
| `"slider"` | `gr.Slider()` |
| `"checkbox"` | `gr.Checkbox()` |
| `"dropdown"` | `gr.Dropdown()` |
| `"label"` | `gr.Label()` |
| `"json"` | `gr.JSON()` |
| `"html"` | `gr.HTML()` |

## From Pipeline

Auto-create an Interface from a Hugging Face pipeline:

```python
from transformers import pipeline
import gradio as gr

pipe = pipeline("text-classification")
demo = gr.Interface.from_pipeline(pipe)
demo.launch()
```

Works with `transformers.Pipeline` and `diffusers.DiffusionPipeline`.

## Flagging

Let users flag problematic inputs/outputs:

```python
demo = gr.Interface(
    fn=predict,
    inputs="text",
    outputs="text",
    flagging_mode="manual",          # "never", "auto", "manual"
    flagging_options=["Wrong", "Offensive", "Other"],
    flagging_dir=".gradio/flagged",  # Storage directory
)
```

Flagged data is saved as CSV by default. Use `flagging_callback` for custom handlers.

## Common Patterns

### Multi-Input/Output

```python
def analyze(text, language, temperature):
    result = model.predict(text, lang=language, temp=temperature)
    return result.summary, result.confidence, result.tokens

demo = gr.Interface(
    fn=analyze,
    inputs=[
        gr.Textbox(label="Input Text", lines=5),
        gr.Dropdown(["en", "es", "fr"], label="Language"),
        gr.Slider(0, 2, value=0.7, label="Temperature"),
    ],
    outputs=[
        gr.Textbox(label="Summary"),
        gr.Number(label="Confidence"),
        gr.JSON(label="Tokens"),
    ],
)
```

### Live Interface

```python
def calculate(num1, operation, num2):
    ops = {"+": lambda a, b: a + b, "-": lambda a, b: a - b}
    return ops[operation](num1, num2)

demo = gr.Interface(
    fn=calculate,
    inputs=[
        gr.Number(label="A"),
        gr.Radio(["+", "-", "*", "/"], label="Op"),
        gr.Number(label="B"),
    ],
    outputs="number",
    live=True,  # No submit button, auto-updates
)
```

### Input Validation

```python
def safe_predict(text):
    if len(text) > 1000:
        raise gr.Error("Input too long (max 1000 chars)")
    if not text.strip():
        raise gr.Error("Input cannot be empty")
    return model(text)
```

## Common Pitfalls

1. **Input/output count mismatch**: The function parameter count must equal `len(inputs)`, and return value count must equal `len(outputs)`
2. **`None` inputs**: Setting `inputs=None` creates a function with no UI inputs
3. **Live + heavy model**: `live=True` re-runs on every keystroke — add debouncing or use Blocks with explicit triggers for expensive operations
4. **Example paths**: Example file paths are relative to the working directory, not the script location
5. **Cache invalidation**: Changing the function invalidates cached examples — delete the cache directory manually
