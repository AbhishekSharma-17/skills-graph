# Gradio — Components

> Source: [gradio.app/docs](https://gradio.app/docs)

## Table of Contents

- [Overview](#overview)
- [Text Components](#text-components)
- [Numeric Components](#numeric-components)
- [Media Components](#media-components)
- [Selection Components](#selection-components)
- [Data Components](#data-components)
- [Display Components](#display-components)
- [Interactive Components](#interactive-components)
- [Special Components](#special-components)
- [Common Parameters](#common-parameters)
- [Component as Input vs Output](#component-as-input-vs-output)

## Overview

Gradio components are the building blocks of any UI. Each component can serve as input, output, or both. Components auto-detect their role from context (in `inputs` vs `outputs` list).

## Text Components

### Textbox

```python
gr.Textbox(
    label="Input",
    placeholder="Type here...",
    lines=3,              # Display height
    max_lines=10,         # Max visible lines
    type="text",          # "text" | "password" | "email"
    value="default",      # Default value
    interactive=True,     # Editable
    show_copy_button=True,
)
```

**Events**: `.change()`, `.submit()`, `.input()`, `.focus()`, `.blur()`
**Value type**: `str`

### Code

```python
gr.Code(
    language="python",     # Syntax highlighting
    lines=10,
    label="Code Editor",
)
```

### MultimodalTextbox

```python
gr.MultimodalTextbox(
    file_types=["image", ".pdf", ".csv"],
    placeholder="Type or upload...",
)
```

**Value type**: `dict` with `"text"` and `"files"` keys

## Numeric Components

### Number

```python
gr.Number(label="Age", value=25, minimum=0, maximum=150, step=1)
```

### Slider

```python
gr.Slider(
    minimum=0,
    maximum=100,
    value=50,
    step=1,
    label="Quality",
    info="Higher = better quality, slower",
)
```

**Events**: `.change()`, `.input()`, `.release()`

### DateTime

```python
gr.DateTime(label="Select Date", type="datetime")
```

## Media Components

### Image

```python
# As input
gr.Image(
    type="pil",            # "pil" | "numpy" | "filepath"
    sources=["upload", "webcam", "clipboard"],
    label="Upload Image",
)

# As output
gr.Image(label="Result", format="png")
```

**Value type**: PIL.Image, numpy.ndarray, or filepath string

### Audio

```python
gr.Audio(
    sources=["upload", "microphone"],
    type="filepath",       # "filepath" | "numpy"
    label="Audio Input",
    streaming=False,       # Enable for real-time
)
```

### Video

```python
gr.Video(
    sources=["upload", "webcam"],
    label="Video",
    format="mp4",
    autoplay=False,
)
```

### Gallery

```python
gr.Gallery(
    columns=3,
    rows=2,
    object_fit="contain",
    label="Image Gallery",
    allow_preview=True,
    show_download_button=True,
)
```

**Value type**: List of `(image, caption)` tuples or image paths

### Model3D

```python
gr.Model3D(label="3D Model")  # Accepts .obj, .gltf, .glb
```

### ImageEditor

```python
gr.ImageEditor(
    type="pil",
    brush=gr.Brush(colors=["#ff0000", "#00ff00"]),
    eraser=gr.Eraser(default_size=10),
)
```

## Selection Components

### Dropdown

```python
gr.Dropdown(
    choices=["Option A", "Option B", "Option C"],
    value="Option A",
    label="Select",
    multiselect=False,     # True for multi-select
    allow_custom_value=True,
    filterable=True,
)
```

### Radio

```python
gr.Radio(
    choices=["Small", "Medium", "Large"],
    value="Medium",
    label="Size",
)
```

### Checkbox

```python
gr.Checkbox(label="I agree", value=False)
```

### CheckboxGroup

```python
gr.CheckboxGroup(
    choices=["Red", "Green", "Blue"],
    value=["Red"],
    label="Select colors",
)
```

### ColorPicker

```python
gr.ColorPicker(label="Choose color", value="#ff0000")
```

## Data Components

### Dataframe

```python
gr.Dataframe(
    headers=["Name", "Age", "Score"],
    datatype=["str", "number", "number"],
    row_count=(5, "dynamic"),
    col_count=(3, "fixed"),
    interactive=True,
    label="Data Table",
)
```

**Value type**: pandas DataFrame or list of lists

### JSON

```python
gr.JSON(label="API Response")
```

### File

```python
gr.File(
    file_count="multiple",   # "single" | "multiple" | "directory"
    file_types=[".csv", ".json", ".txt"],
    label="Upload Files",
)
```

### FileExplorer

```python
gr.FileExplorer(
    root_dir="./data",
    glob="**/*.csv",
    label="Browse Files",
)
```

## Display Components

### Markdown

```python
gr.Markdown("## Hello **World**")
gr.Markdown(value=lambda: f"Updated at {datetime.now()}")
```

### HTML

```python
gr.HTML("<div style='color:red'>Custom HTML</div>")
```

### Label

```python
gr.Label(num_top_classes=5, label="Classification")
```

**Value type**: `dict[str, float]` — class names to confidence scores

### HighlightedText

```python
gr.HighlightedText(
    label="NER",
    combine_adjacent=True,
    color_map={"PER": "red", "ORG": "blue"},
)
```

**Value type**: List of `(text, label)` tuples

### Plot

```python
gr.Plot(label="Chart")  # Accepts matplotlib, plotly, altair, bokeh figures
```

### LinePlot / ScatterPlot

```python
gr.LinePlot(
    x="date",
    y="price",
    color="symbol",
    title="Stock Prices",
)
```

## Interactive Components

### Button

```python
gr.Button(
    value="Submit",
    variant="primary",     # "primary" | "secondary" | "stop" | "huggingface"
    icon="https://...",    # Icon URL
    size="lg",             # "sm" | "lg"
)
```

### UploadButton

```python
gr.UploadButton(
    label="Upload CSV",
    file_types=[".csv"],
    file_count="single",
)
```

### ClearButton

```python
gr.ClearButton(components=[textbox, image, output])
```

### DownloadButton

```python
gr.DownloadButton(label="Download Result", value="result.csv")
```

### LoginButton (HF OAuth)

```python
gr.LoginButton()  # Sign in with Hugging Face
```

## Special Components

### State

```python
state = gr.State(value=[])  # Session-scoped invisible state
```

### BrowserState

```python
state = gr.BrowserState(default_value="", storage_key="my_key")
```

### Timer

```python
timer = gr.Timer(value=5)  # Fires every 5 seconds
timer.tick(fn=update_dashboard, outputs=chart)
```

### Dataset

```python
gr.Dataset(
    components=[gr.Textbox(), gr.Image()],
    samples=[["Hello", "img1.png"], ["World", "img2.png"]],
)
```

## Common Parameters

Most components share these parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `label` | `str` | Display label |
| `info` | `str` | Help text below component |
| `value` | `any` | Default value |
| `visible` | `bool` | Show/hide component |
| `interactive` | `bool` | Editable vs read-only |
| `elem_id` | `str` | HTML element ID (for CSS) |
| `elem_classes` | `list[str]` | CSS classes |
| `render` | `bool` | Whether to render immediately |
| `scale` | `int` | Relative width in Row |
| `min_width` | `int` | Minimum pixel width |
| `show_label` | `bool` | Display the label |
| `container` | `bool` | Wrap in container div |
| `every` | `Timer \| float` | Auto-refresh interval |

## Component as Input vs Output

Same component can serve both roles. Behavior differs:

```python
# As input: user uploads image → PIL Image passed to fn
# As output: fn returns PIL Image → displayed to user
img = gr.Image(type="pil")

demo = gr.Interface(fn=process, inputs=img, outputs=img)
```

When used as output, `interactive` defaults to `False`. Override with `interactive=True` if you want the output to be editable.

## Common Pitfalls

1. **Image `type` mismatch**: Default is `"filepath"` — set `type="pil"` or `type="numpy"` if your function expects those
2. **Audio sample rate**: NumPy audio returns `(sample_rate, data)` tuple, not just data
3. **Dataframe mutations**: Return a new DataFrame from your function; in-place mutations may not trigger UI updates
4. **Gallery format**: Returns list of paths or `(path, caption)` tuples — single image returns won't render
5. **File paths**: `gr.File` returns temp file paths that may be cleaned up — copy files if you need persistence
