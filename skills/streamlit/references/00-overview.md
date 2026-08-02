# Streamlit — Overview & Architecture

> Source: [docs.streamlit.io](https://docs.streamlit.io/) | Version: 1.59.x

## Table of Contents

- [What Is Streamlit](#what-is-streamlit)
- [Execution Model](#execution-model)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Hello World](#hello-world)
- [Core Concepts](#core-concepts)
- [Configuration](#configuration)
- [When to Use Streamlit](#when-to-use-streamlit)
- [Streamlit vs Alternatives](#streamlit-vs-alternatives)

## What Is Streamlit

Streamlit is an open-source Python framework that turns scripts into shareable web apps. Write a Python script, sprinkle in `st.*` calls, and you get an interactive browser-based UI — no HTML, CSS, or JavaScript required.

Key characteristics:
- **Python-only** — the entire app is a `.py` file
- **Top-to-bottom execution** — the script reruns on every interaction
- **Reactive widgets** — user input triggers a full script rerun by default
- **Zero frontend code** — Streamlit generates the UI from your Python calls
- **Built-in sharing** — deploy to Streamlit Community Cloud in one click

Streamlit is owned by Snowflake (acquired 2022) and is trusted by 90%+ of Fortune 50 companies for internal tools, prototyping, and dashboards.

## Execution Model

This is the single most important concept. Streamlit apps run **top-to-bottom on every user interaction**:

```
User interacts with widget
       ↓
Script reruns from line 1
       ↓
All st.* calls re-execute
       ↓
UI updates in the browser
```

Every time a user clicks a button, moves a slider, or types in an input, the **entire script** runs again. This means:

1. Variables reset on each rerun (use `st.session_state` to persist)
2. Expensive computations re-execute (use `@st.cache_data` to avoid)
3. UI elements redraw in order (placement = call order in script)

### Rerun Triggers

- Widget value change (slider moved, checkbox toggled)
- `st.rerun()` called programmatically
- Source file saved (in development mode with auto-reload)
- Fragment auto-rerun interval elapsed

### Partial Reruns with Fragments

Since v1.37, `@st.fragment` enables rerunning only part of the script:

```python
@st.fragment
def chart_section():
    filter_val = st.selectbox("Filter", ["A", "B", "C"])
    st.line_chart(get_data(filter_val))

chart_section()  # Only this reruns when its widgets change
```

## Installation

```bash
# Basic install
pip install streamlit

# With uv (recommended)
uv pip install streamlit

# With poetry
poetry add streamlit

# Verify installation
streamlit hello

# Run your app
streamlit run app.py

# Run on a specific port
streamlit run app.py --server.port 8501

# Run with a specific theme
streamlit run app.py --theme.base dark
```

### Requirements

- Python 3.9–3.13
- pip, uv, or conda

## Project Structure

### Minimal App

```
my-app/
├── app.py                  # Entry point
└── requirements.txt        # Dependencies
```

### Production App

```
my-app/
├── app.py                  # Entry point (router for multipage)
├── pages/
│   ├── 1_dashboard.py      # Page 1
│   ├── 2_analysis.py       # Page 2
│   └── 3_settings.py       # Page 3
├── .streamlit/
│   ├── config.toml         # App configuration
│   └── secrets.toml        # API keys, DB credentials (gitignored)
├── utils/
│   ├── data.py             # Data loading functions
│   └── charts.py           # Chart helpers
├── requirements.txt
└── README.md
```

## Hello World

```python
import streamlit as st

st.title("Hello Streamlit!")
st.write("This is my first app.")

name = st.text_input("What's your name?")
if name:
    st.write(f"Hello, {name}!")

number = st.slider("Pick a number", 0, 100, 50)
st.write(f"You picked: {number}")
```

Run it:

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`. Every time you change a widget, the script reruns and the UI updates.

## Core Concepts

### 1. Everything is `st.*`

Every UI element is a function call:

```python
st.title("Dashboard")           # Display
st.text_input("Search")         # Input → returns value
st.line_chart(data)             # Visualization
st.sidebar.selectbox(...)       # Layout
st.cache_data                   # Performance
st.session_state                # State
```

### 2. st.write — The Swiss Army Knife

`st.write()` renders almost anything:

```python
st.write("Markdown **text**")       # Markdown string
st.write(42)                        # Number
st.write(df)                        # DataFrame → interactive table
st.write(fig)                       # Matplotlib/Plotly figure
st.write({"key": "value"})          # Dict → JSON
st.write(my_function)               # Function → help text
```

### 3. Magic Commands

Variables alone on a line are auto-rendered (syntactic sugar for `st.write()`):

```python
import streamlit as st
import pandas as pd

df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
df  # Automatically displayed as an interactive table
```

### 4. Widget Return Values

Every input widget returns its current value:

```python
age = st.number_input("Age", 0, 120, 25)     # Returns int
name = st.text_input("Name")                   # Returns str
agree = st.checkbox("I agree")                  # Returns bool
color = st.selectbox("Color", ["Red", "Blue"])  # Returns selected str
```

### 5. Conditional Display

Since widgets return values, use standard Python conditionals:

```python
show_data = st.checkbox("Show raw data")
if show_data:
    st.dataframe(df)
```

## Configuration

### .streamlit/config.toml

```toml
[server]
port = 8501
headless = true
runOnSave = true

[browser]
gatherUsageStats = false

[theme]
base = "light"               # "light" or "dark"
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"          # "sans serif", "serif", "monospace"

[client]
toolbarMode = "minimal"      # "auto", "developer", "viewer", "minimal"
```

### st.set_page_config

Must be the first Streamlit call in your script:

```python
st.set_page_config(
    page_title="My Dashboard",
    page_icon="📊",
    layout="wide",                    # "centered" (default) or "wide"
    initial_sidebar_state="expanded", # "auto", "expanded", "collapsed"
)
```

## When to Use Streamlit

**Use Streamlit for:**
- Data exploration dashboards
- ML model demos and prototypes
- Internal tools and admin panels
- LLM/chatbot interfaces
- Data science reports with interactivity
- Quick proof-of-concept apps
- API exploration tools

**Don't use Streamlit for:**
- Production web applications with complex routing
- High-concurrency, stateful backends
- Mobile-first applications
- Apps requiring pixel-perfect custom UI
- Multi-user collaborative editing

## Streamlit vs Alternatives

| Feature | Streamlit | Gradio | Dash | Panel |
|---------|-----------|--------|------|-------|
| **Language** | Python | Python | Python | Python |
| **Primary use** | Data apps | ML demos | Dashboards | Data apps |
| **Frontend code** | None | None | Some HTML | None |
| **Reactivity** | Full rerun | Component | Callbacks | Reactive |
| **Charts** | Built-in + libs | Basic + libs | Plotly native | HoloViews |
| **State** | Session state | State object | Callbacks | Param |
| **Deployment** | Community Cloud | HF Spaces | Self-host | Self-host |
| **Learning curve** | Very low | Low | Medium | Medium |
| **Customization** | Limited | Limited | High | High |
| **LLM/Chat** | Built-in | Built-in | Manual | Manual |

## Related Topics

- `01-text-data-display.md` — Display elements
- `02-input-widgets.md` — Input widgets
- `05-session-state.md` — State management
- `06-caching-performance.md` — Caching for performance
