# Gradio — Overview & Installation

> Source: [gradio.app](https://gradio.app/) · Version tracked: 6.22.x · License: Apache-2.0

## What Is Gradio?

Gradio is an open-source Python library (built by Hugging Face) that lets you build interactive web-based demos and applications for machine learning models, APIs, or arbitrary Python functions. With a few lines of code you get a shareable UI — no JavaScript or frontend knowledge required.

## When to Use Gradio

| Use Case | Fit |
|----------|-----|
| Quick ML model demo | Ideal — minimal code to UI |
| LLM chatbot prototype | Ideal — `ChatInterface` purpose-built |
| Internal data tool | Good — auth, state, layouts |
| Hugging Face Spaces deployment | Ideal — native integration |
| Production SaaS frontend | Not ideal — use React/Next.js |
| Static content site | Not ideal — use Astro/Hugo |

## Gradio vs Streamlit vs Dash

| Feature | Gradio | Streamlit | Dash |
|---------|--------|-----------|------|
| Primary focus | ML demos, model serving | Data apps, dashboards | Enterprise dashboards |
| Learning curve | Very low | Low | Medium |
| Execution model | Event-driven | Script reruns top-to-bottom | Callback-based |
| Sharing | One-click share links | Community Cloud | Self-hosted |
| HF integration | Native | Third-party | Third-party |
| Chatbot support | Built-in `ChatInterface` | `st.chat_input` | Manual |
| Custom components | Svelte-based system | React-based system | React-based system |
| API auto-generation | Yes (REST + clients) | No | No |

## Architecture

```
User Browser
     │
     ▼
┌──────────────┐     ┌──────────────────┐
│  Gradio      │────▶│  FastAPI Server   │
│  Frontend    │◀────│  (ASGI / Uvicorn) │
│  (Svelte)    │     │                   │
└──────────────┘     │  ┌──────────────┐ │
                     │  │ Your Python  │ │
                     │  │ Function(s)  │ │
                     │  └──────────────┘ │
                     │  ┌──────────────┐ │
                     │  │ Queue System │ │
                     │  └──────────────┘ │
                     └──────────────────┘
```

- **Frontend**: Pre-built Svelte components rendered in the browser
- **Backend**: FastAPI application serving the UI and handling API calls
- **Queue**: Built-in request queueing with concurrency control
- **API**: Auto-generated REST endpoints for every function

## Installation

```bash
# Basic install
pip install gradio

# With uv
uv pip install gradio

# Verify installation
python -c "import gradio as gr; print(gr.__version__)"
```

### Requirements

- Python 3.10+
- Works on macOS, Linux, Windows
- No Node.js required (frontend is pre-built)

## Quick Start

### Minimal Example

```python
import gradio as gr

def greet(name):
    return f"Hello, {name}!"

demo = gr.Interface(fn=greet, inputs="textbox", outputs="textbox")
demo.launch()
```

This starts a local server at `http://localhost:7860` with a text input, submit button, and text output.

### Three Core APIs

```python
# 1. Interface — simple function wrapper
demo = gr.Interface(fn=predict, inputs="image", outputs="label")

# 2. Blocks — flexible layout builder
with gr.Blocks() as demo:
    inp = gr.Textbox()
    out = gr.Textbox()
    btn = gr.Button("Run")
    btn.click(fn=process, inputs=inp, outputs=out)

# 3. ChatInterface — chatbot wrapper
demo = gr.ChatInterface(fn=chat_response)
```

### Running Your App

```python
# Default: localhost:7860
demo.launch()

# Network accessible
demo.launch(server_name="0.0.0.0", server_port=8080)

# With public share link (72-hour expiry)
demo.launch(share=True)

# In Jupyter notebook
demo.launch(inline=True)

# Auto-open browser
demo.launch(inbrowser=True)
```

## Project Structure

```
my-gradio-app/
├── app.py           # Main application
├── requirements.txt # Dependencies (include gradio)
├── README.md        # HF Spaces metadata (if deploying)
├── flagged/         # Auto-created for flagged data
└── assets/          # Static files (optional)
```

## Key Concepts

### String Shortcuts

Common components can be referenced by string instead of class:

```python
# These are equivalent:
gr.Interface(fn=fn, inputs="textbox", outputs="textbox")
gr.Interface(fn=fn, inputs=gr.Textbox(), outputs=gr.Textbox())

# Common shortcuts: "text", "textbox", "image", "audio",
# "video", "file", "dataframe", "number", "slider",
# "checkbox", "dropdown", "label", "json", "html"
```

### Import Convention

```python
import gradio as gr  # Always use this convention
```

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `GRADIO_SERVER_NAME` | Default server host |
| `GRADIO_SERVER_PORT` | Default server port |
| `GRADIO_ANALYTICS_ENABLED` | Enable/disable telemetry |
| `GRADIO_TEMP_DIR` | Temporary file directory |
| `GRADIO_SHARE` | Default share setting |

## Common Pitfalls

1. **Port already in use**: Gradio auto-increments from 7860; kill stale processes or specify a port
2. **Function signature mismatch**: Number of `inputs` must match function parameters
3. **Return value count**: Number of return values must match `outputs` list length
4. **Forgetting `demo.launch()`**: The app won't start without calling `.launch()`
5. **Large file uploads**: Set `max_file_size` in `launch()` to prevent memory issues
