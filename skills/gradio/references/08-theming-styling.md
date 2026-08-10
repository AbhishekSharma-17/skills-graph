# Gradio — Theming & Styling

> Source: [gradio.app/guides/custom-CSS-and-JS](https://gradio.app/guides/custom-CSS-and-JS)

## Table of Contents

- [Overview](#overview)
- [Built-in Themes](#built-in-themes)
- [Custom Themes](#custom-themes)
- [Custom CSS](#custom-css)
- [Custom JavaScript](#custom-javascript)
- [Head Injection](#head-injection)
- [Component Styling](#component-styling)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## Overview

Gradio provides three layers of visual customization:

1. **Themes** — High-level color, font, and spacing presets
2. **Custom CSS** — Fine-grained style overrides
3. **Custom JS** — Client-side interactivity and analytics

## Built-in Themes

```python
import gradio as gr

# Apply a built-in theme
demo = gr.Blocks(theme=gr.themes.Soft())
demo = gr.Blocks(theme=gr.themes.Glass())
demo = gr.Blocks(theme=gr.themes.Monochrome())
demo = gr.Blocks(theme=gr.themes.Default())
demo = gr.Blocks(theme=gr.themes.Base())
demo = gr.Blocks(theme=gr.themes.Citrus())
demo = gr.Blocks(theme=gr.themes.Ocean())
```

### Hub Themes

Use community themes from Hugging Face Hub:

```python
demo = gr.Blocks(theme="gradio/seafoam")
demo = gr.Blocks(theme="gradio/dracula_revamped")
```

## Custom Themes

Build a theme by extending `gr.themes.Base`:

```python
custom_theme = gr.themes.Base(
    primary_hue="indigo",
    secondary_hue="blue",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"],
    font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "monospace"],
).set(
    body_background_fill="*neutral_50",
    block_background_fill="white",
    block_border_width="1px",
    block_border_color="*neutral_200",
    block_label_text_color="*primary_600",
    button_primary_background_fill="*primary_500",
    button_primary_text_color="white",
    input_background_fill="*neutral_50",
)
```

### Available Color Hues

`red`, `orange`, `yellow`, `green`, `teal`, `cyan`, `blue`, `indigo`, `purple`, `pink`, `slate`, `gray`, `zinc`, `neutral`, `stone`

### Available Size Presets

`text_sm`, `text_md`, `text_lg`, `text_xl`, `spacing_sm`, `spacing_md`, `spacing_lg`, `radius_sm`, `radius_md`, `radius_lg`

### Pushing to Hub

```python
custom_theme.push_to_hub(
    repo_name="my-custom-theme",
    version="0.1.0",
    hf_token="hf_...",
)
```

## Custom CSS

### Method 1: Inline CSS String

```python
with gr.Blocks(css="""
    .gradio-container {
        max-width: 800px !important;
        margin: auto;
    }
    .prose h1 {
        color: #2563eb;
    }
""") as demo:
    gr.Markdown("# Styled App")
```

### Method 2: CSS File

```python
with gr.Blocks(css_paths="style.css") as demo:
    pass

# Multiple files
with gr.Blocks(css_paths=["base.css", "custom.css"]) as demo:
    pass
```

### Method 3: Element-Level Targeting

```python
with gr.Blocks(css="""
    #custom-input textarea {
        font-size: 18px;
        border: 2px solid #3b82f6;
    }
    .highlighted {
        background-color: #fef3c7 !important;
    }
""") as demo:
    inp = gr.Textbox(elem_id="custom-input", label="Input")
    out = gr.Textbox(elem_classes=["highlighted"], label="Output")
```

### Referencing Local Files in CSS

```python
# Use /gradio_api/file= prefix for local assets
css = """
.gradio-container {
    background: url('/gradio_api/file=assets/bg.jpg');
}
"""

demo = gr.Blocks(css=css)
demo.launch(allowed_paths=["./assets"])
```

## Custom JavaScript

### On Page Load

```python
# Executes once when the page loads
with gr.Blocks(js="""
    () => {
        console.log('App loaded!');
        document.title = 'My Gradio App';
    }
""") as demo:
    pass
```

### On Event Listener

```python
btn.click(
    fn=process,
    inputs=inp,
    outputs=out,
    js="(x) => { console.log('Processing:', x); return x; }",
)
```

### JS-Only Event (No Python)

```python
btn.click(
    fn=None,
    js="""
    () => {
        const el = document.querySelector('#output textarea');
        navigator.clipboard.writeText(el.value);
        alert('Copied!');
    }
    """,
)
```

### JS for Dark Mode Toggle

```python
dark_btn = gr.Button("Toggle Dark Mode")
dark_btn.click(
    fn=None,
    js="""
    () => {
        document.body.classList.toggle('dark');
        document.querySelectorAll('.gradio-container').forEach(el => {
            el.style.backgroundColor = document.body.classList.contains('dark')
                ? '#1a1a2e' : '#ffffff';
        });
    }
    """,
)
```

## Head Injection

Add analytics, meta tags, or external resources to `<head>`:

```python
analytics = """
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXX');
</script>
"""

with gr.Blocks(head=analytics) as demo:
    pass

# Or from file
with gr.Blocks(head_paths="analytics.html") as demo:
    pass
```

### Open Graph / Twitter Cards

```python
og_tags = """
<meta property="og:title" content="My ML Demo">
<meta property="og:description" content="Try my model">
<meta property="og:image" content="https://example.com/preview.png">
<meta name="twitter:card" content="summary_large_image">
"""

with gr.Blocks(head=og_tags) as demo:
    pass
```

## Component Styling

### elem_id and elem_classes

```python
# Target with CSS via #id
inp = gr.Textbox(elem_id="main-input")

# Target with CSS via .class
out = gr.Textbox(elem_classes=["output-box", "highlighted"])

# CSS to match
css = """
#main-input { border: 2px solid blue; }
.output-box { font-family: monospace; }
.highlighted { background: yellow; }
"""
```

### Component-Level show_label

```python
gr.Textbox(label="Name", show_label=False)   # Hide label
gr.Image(label="Photo", container=False)     # Remove container
```

### Button Variants

```python
gr.Button("Submit", variant="primary")       # Blue
gr.Button("Cancel", variant="secondary")     # Gray
gr.Button("Stop", variant="stop")           # Red
gr.Button("HF", variant="huggingface")      # HF brand
```

## Common Patterns

### Responsive Layout

```python
css = """
@media (max-width: 768px) {
    .gradio-container .row {
        flex-direction: column !important;
    }
}
"""

with gr.Blocks(css=css) as demo:
    with gr.Row():
        sidebar = gr.Column(scale=1)
        main = gr.Column(scale=3)
```

### Branded App

```python
custom_theme = gr.themes.Soft(
    primary_hue="blue",
    font=[gr.themes.GoogleFont("Poppins"), "sans-serif"],
)

css = """
.gradio-container {
    max-width: 1200px !important;
    margin: 0 auto;
}
footer { display: none !important; }
"""

with gr.Blocks(theme=custom_theme, css=css, title="My Brand") as demo:
    gr.Markdown("# My Brand App")
    demo.launch(favicon_path="brand-icon.png")
```

### Internationalization

```python
from gradio.i18n import I18n

translations = I18n(
    submit="Enviar",
    clear="Limpiar",
    flag="Marcar",
)

demo = gr.Interface(fn=process, inputs="text", outputs="text", i18n=translations)
```

## Common Pitfalls

1. **CSS specificity**: Gradio's built-in styles are specific — you'll often need `!important` to override them
2. **Unstable selectors**: Gradio's internal HTML structure can change between versions — prefer `elem_id` and `elem_classes` over querying built-in class names
3. **External resources in CSS**: Local file paths need the `/gradio_api/file=` prefix and the directory must be in `allowed_paths`
4. **JS execution timing**: `js` parameter runs on page load, not on component mount — DOM elements may not exist yet
5. **Theme + CSS conflicts**: Custom CSS may conflict with theme variables — test with both light and dark variants
6. **Google Fonts**: `gr.themes.GoogleFont()` loads fonts from Google CDN — ensure users have internet access, or use system fonts
