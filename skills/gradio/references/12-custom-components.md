# Gradio — Custom Components

> Source: [gradio.app/guides/custom-components-in-five-minutes](https://gradio.app/guides/custom-components-in-five-minutes)

## Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
- [Component Structure](#component-structure)
- [Python Backend](#python-backend)
- [Svelte Frontend](#svelte-frontend)
- [Events](#events)
- [Data Types](#data-types)
- [CLI Commands](#cli-commands)
- [Publishing](#publishing)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## Overview

Custom Components let you create reusable UI elements beyond Gradio's built-in components. They consist of a Python backend (for data processing) and a Svelte frontend (for rendering). Components are published as Python packages on PyPI.

### When to Build Custom Components

| Scenario | Approach |
|----------|----------|
| Need a component Gradio doesn't have | Custom Component |
| Want to modify existing component behavior | Template from existing |
| Need a specialized visualization | Custom Component |
| Simple styling change | Use `elem_id`/CSS instead |
| One-off HTML | Use `gr.HTML()` instead |

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend build)
- `pip install gradio`

### Create a Component

```bash
# Scaffold from scratch
gradio cc create MyCounter

# Scaffold from an existing component template
gradio cc create MyTextbox --template SimpleTextbox

# Scaffold with specific directory
gradio cc create MyComponent --directory ./my-component
```

### Available Templates

Any built-in Gradio component can be used as a template:

```bash
gradio cc create MyImage --template Image
gradio cc create MySlider --template Slider
gradio cc create MyChat --template Chatbot
gradio cc create MyCode --template Code
```

## Component Structure

```
my_counter/
├── demo/
│   └── app.py                 # Demo application
├── frontend/
│   ├── Index.svelte           # Main Svelte component
│   ├── package.json           # Node dependencies
│   └── ...
├── backend/
│   └── my_counter/
│       ├── __init__.py
│       └── my_counter.py      # Python component class
├── pyproject.toml             # Package configuration
└── README.md
```

## Python Backend

The backend defines data processing, serialization, and event support:

```python
from gradio.components.base import Component
from gradio.events import Events

class MyCounter(Component):
    # Events this component supports
    EVENTS = [Events.change, Events.input]

    def __init__(
        self,
        value: int = 0,
        label: str | None = None,
        minimum: int = 0,
        maximum: int = 100,
        step: int = 1,
        **kwargs,
    ):
        self.minimum = minimum
        self.maximum = maximum
        self.step = step
        super().__init__(value=value, label=label, **kwargs)

    def preprocess(self, payload: int) -> int:
        """Convert frontend value to Python value (for fn input)."""
        return int(payload)

    def postprocess(self, value: int) -> int:
        """Convert Python value to frontend value (for fn output)."""
        return int(value)

    def example_payload(self) -> int:
        """Example value for API docs."""
        return 5

    def example_value(self) -> int:
        """Example value for demo."""
        return 42

    def api_info(self) -> dict:
        """JSON Schema for API documentation."""
        return {"type": "integer", "minimum": self.minimum, "maximum": self.maximum}
```

### Key Methods

| Method | Purpose |
|--------|---------|
| `preprocess(payload)` | Frontend → Python (called before your fn) |
| `postprocess(value)` | Python → Frontend (called after your fn) |
| `example_payload()` | Example value for auto-generated API docs |
| `example_value()` | Example value shown in the demo |
| `api_info()` | JSON Schema describing the component's data type |

## Svelte Frontend

The frontend renders the component in the browser:

```svelte
<script lang="ts">
    import type { Gradio } from "@gradio/utils";
    import { Block, BlockLabel } from "@gradio/atoms";
    import { StatusTracker } from "@gradio/statustracker";

    export let gradio: Gradio;
    export let label = "Counter";
    export let value = 0;
    export let minimum = 0;
    export let maximum = 100;
    export let step = 1;
    export let loading_status: object;
    export let elem_id = "";
    export let elem_classes: string[] = [];

    function increment() {
        if (value + step <= maximum) {
            value += step;
            gradio.dispatch("change");
            gradio.dispatch("input");
        }
    }

    function decrement() {
        if (value - step >= minimum) {
            value -= step;
            gradio.dispatch("change");
            gradio.dispatch("input");
        }
    }
</script>

<Block {elem_id} {elem_classes}>
    <StatusTracker {...loading_status} />
    <BlockLabel {label} />
    <div class="counter">
        <button on:click={decrement}>−</button>
        <span class="value">{value}</span>
        <button on:click={increment}>+</button>
    </div>
</Block>

<style>
    .counter {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px;
    }
    .value {
        font-size: 24px;
        font-weight: bold;
        min-width: 60px;
        text-align: center;
    }
    button {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        border: 1px solid var(--border-color-primary);
        background: var(--background-fill-primary);
        cursor: pointer;
        font-size: 20px;
    }
</style>
```

### Key Frontend Concepts

- `gradio.dispatch("event_name")` — triggers a Gradio event
- `value` is two-way bound — changes in the frontend update the backend
- Use Gradio's CSS variables (`var(--border-color-primary)`) for theme compatibility
- Import shared atoms from `@gradio/atoms` for consistent styling

## Events

### Built-in Events

```python
from gradio.events import Events

class MyComponent(Component):
    EVENTS = [
        Events.change,       # Value changed
        Events.input,        # User input
        Events.submit,       # Enter pressed
        Events.focus,        # Gained focus
        Events.blur,         # Lost focus
        Events.select,       # Item selected
        Events.upload,       # File uploaded
        Events.clear,        # Value cleared
    ]
```

### Custom Events

```python
from gradio.events import EventListener

class MyComponent(Component):
    EVENTS = [
        Events.change,
        EventListener(
            "double_click",
            doc="Triggered when the component is double-clicked.",
        ),
    ]
```

```svelte
<!-- In frontend -->
<div on:dblclick={() => gradio.dispatch("double_click")}>
    ...
</div>
```

## Data Types

### Simple Types

```python
def preprocess(self, payload: str) -> str:
    return payload

def postprocess(self, value: str) -> str:
    return value
```

### File Types

For components that handle files:

```python
from gradio.data_classes import FileData

class MyFileViewer(Component):
    data_model = FileData

    def preprocess(self, payload: FileData) -> str:
        return payload.path  # Return file path

    def postprocess(self, value: str) -> FileData:
        return FileData(path=value)
```

### Complex Types

```python
from pydantic import BaseModel

class CounterData(BaseModel):
    value: int
    label: str

class MyComponent(Component):
    data_model = CounterData

    def preprocess(self, payload: CounterData) -> dict:
        return {"value": payload.value, "label": payload.label}

    def postprocess(self, value: dict) -> CounterData:
        return CounterData(**value)
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `gradio cc create <Name>` | Scaffold new component |
| `gradio cc dev` | Start dev server with hot reload |
| `gradio cc build` | Build for distribution |
| `gradio cc publish` | Publish to PyPI |
| `gradio cc install` | Install component locally |
| `gradio cc docs` | Generate documentation |
| `gradio cc show` | Show component info |

### Development Workflow

```bash
# 1. Create component
gradio cc create MyCounter

# 2. Develop with hot reload
cd my_counter
gradio cc dev

# 3. Build
gradio cc build

# 4. Install locally for testing
pip install dist/my_counter-0.1.0-py3-none-any.whl

# 5. Publish to PyPI
gradio cc publish
```

## Publishing

### Build & Publish

```bash
# Build the package
gradio cc build

# Publish to PyPI
gradio cc publish

# Publish with demo to HF Spaces
gradio cc publish --upload-pypi --upload-demo
```

### pyproject.toml Configuration

```toml
[project]
name = "gradio_my_counter"
version = "0.1.0"
description = "A counter component for Gradio"
license = "MIT"
requires-python = ">=3.10"
dependencies = ["gradio>=6.0"]

[project.optional-dependencies]
dev = ["gradio[dev]"]
```

### Documentation

```bash
# Auto-generate docs
gradio cc docs

# Creates a README.md with:
# - Installation instructions
# - API reference
# - Screenshots
# - Example usage
```

## Common Patterns

### Extending Existing Components

```python
from gradio.components import Textbox

class SmartTextbox(Textbox):
    def postprocess(self, value):
        # Add custom post-processing
        if isinstance(value, dict):
            value = json.dumps(value, indent=2)
        return super().postprocess(value)
```

### Component with External Dependencies

```python
class MapComponent(Component):
    def __init__(self, center=(0, 0), zoom=10, **kwargs):
        self.center = center
        self.zoom = zoom
        super().__init__(**kwargs)
```

Frontend uses Leaflet.js (bundled via npm):

```json
// frontend/package.json
{
    "dependencies": {
        "leaflet": "^1.9.0"
    }
}
```

### Using in Blocks

```python
# After installing: pip install gradio_my_counter
from gradio_my_counter import MyCounter

with gr.Blocks() as demo:
    counter = MyCounter(value=0, minimum=0, maximum=100)
    display = gr.Number(label="Current Value")

    counter.change(fn=lambda v: v, inputs=counter, outputs=display)
```

## Common Pitfalls

1. **Node.js version**: Requires Node.js 18+ — check with `node --version`
2. **Package naming**: PyPI packages must be prefixed with `gradio_` (e.g., `gradio_my_counter`)
3. **CSS variables**: Use Gradio's CSS variables (`var(--...)`) for theme compatibility — hardcoded colors break in dark mode
4. **Event dispatching**: You must call `gradio.dispatch("change")` in the Svelte frontend for the `.change()` listener to work in Python
5. **Two-way binding**: The `value` prop in Svelte is automatically synced — don't manually send value updates via separate API calls
6. **Build artifacts**: Run `gradio cc build` before publishing — the frontend must be compiled
7. **Template mismatch**: When using `--template`, the template component's data model and events carry over — modify them to match your needs
