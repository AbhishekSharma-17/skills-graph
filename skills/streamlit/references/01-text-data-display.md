# Streamlit — Text & Data Display

> Source: [docs.streamlit.io/develop/api-reference](https://docs.streamlit.io/develop/api-reference) | Version: 1.59.x

## Table of Contents

- [Text Elements](#text-elements)
- [st.write and Magic](#stwrite-and-magic)
- [Data Display](#data-display)
- [st.dataframe](#stdataframe)
- [st.data_editor](#stdata_editor)
- [Column Configuration](#column-configuration)
- [st.metric](#stmetric)
- [st.json](#stjson)
- [st.table](#sttable)
- [Common Patterns](#common-patterns)

## Text Elements

### Headings and Text

```python
import streamlit as st

st.title("Page Title")           # Largest heading
st.header("Section Header")      # h2-level
st.subheader("Subsection")       # h3-level
st.caption("Small muted text")   # Caption/footnote style
st.text("Fixed-width text")      # Monospace, no Markdown
```

### Markdown

```python
st.markdown("**Bold**, *italic*, `code`")
st.markdown("[Link](https://streamlit.io)")
st.markdown("- Bullet 1\n- Bullet 2")

# Unsafe HTML (opt-in)
st.markdown("<span style='color:red'>Red text</span>", unsafe_allow_html=True)
```

CSS color support in Markdown (v1.55+):

```python
st.markdown(":red[This text is red]")
st.markdown(":blue-background[Blue background]")
st.markdown(":rainbow[Rainbow text]")
```

Supported colors: `blue`, `green`, `orange`, `red`, `violet`, `gray`, `rainbow`. Add `-background` for background highlighting.

### Code Blocks

```python
st.code("""
import pandas as pd
df = pd.read_csv("data.csv")
""", language="python")

# With line numbers
st.code("print('hello')", language="python", line_numbers=True)
```

### st.echo — Show and Run Code

```python
with st.echo():
    # This code block is displayed AND executed
    x = 42
    st.write(f"x = {x}")
```

### Other Text Elements

```python
st.latex(r"\int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2}")
st.divider()  # Horizontal rule
st.html("<h1>Raw HTML</h1>")
st.badge("New", color="green")    # v1.55+
```

### st.help

```python
st.help(pd.DataFrame)  # Renders docstring for any Python object
```

## st.write and Magic

### st.write — Universal Renderer

`st.write()` accepts almost any Python object and renders it appropriately:

```python
st.write("# Markdown heading")                  # Markdown
st.write(42)                                      # Number
st.write(pd.DataFrame({"a": [1, 2], "b": [3, 4]}))  # DataFrame
st.write(fig)                                     # Matplotlib/Plotly
st.write({"key": "value"})                        # JSON
st.write(my_function)                             # Help text

# Multiple arguments
st.write("The answer is", 42, "and the data:", df)
```

### st.write_stream — Typewriter Effect

```python
import time

def stream_text():
    for word in "Hello Streamlit World".split():
        yield word + " "
        time.sleep(0.1)

st.write_stream(stream_text)
```

Works with generator functions and OpenAI-style streaming responses.

### Magic Commands

Any standalone expression is auto-displayed:

```python
"# This is a title"    # Rendered as markdown
df                      # Rendered as interactive table
42                      # Rendered as text
```

Disable via `config.toml`:

```toml
[runner]
magicEnabled = false
```

## Data Display

## st.dataframe

Interactive, scrollable, sortable table:

```python
import pandas as pd

df = pd.DataFrame({
    "name": ["Alice", "Bob", "Carol"],
    "score": [95, 87, 92],
    "passed": [True, True, True],
})

st.dataframe(df)
```

### Parameters

```python
st.dataframe(
    df,
    width=700,                    # Fixed width in pixels
    height=400,                   # Fixed height in pixels
    use_container_width=True,     # Fill parent container
    hide_index=True,              # Hide the index column
    column_order=["name", "score"],  # Column display order
    column_config={               # Per-column config (see below)
        "score": st.column_config.ProgressColumn(
            min_value=0, max_value=100
        )
    },
    on_select="rerun",            # Enable row selection
    selection_mode="multi-row",   # "single-row", "multi-row", "single-column", "multi-column"
)
```

### Row Selection

```python
event = st.dataframe(df, on_select="rerun", selection_mode="multi-row")
selected_rows = event.selection.rows  # List of selected row indices
filtered_df = df.iloc[selected_rows]
```

### Supported Data Types

- `pandas.DataFrame` / `pandas.Series`
- `numpy.ndarray`
- `list` / `dict`
- `pyarrow.Table`
- `snowpark.DataFrame`
- Anything with a `.to_pandas()` method

## st.data_editor

Editable data table — users can modify cell values:

```python
edited_df = st.data_editor(df)

# The returned DataFrame contains user edits
st.write("Edited data:", edited_df)
```

### Editable with Add/Delete Rows

```python
edited_df = st.data_editor(
    df,
    num_rows="dynamic",          # Allow adding/deleting rows
    disabled=["name"],           # Lock specific columns
    key="my_editor",             # Track changes in session state
)
```

### Tracking Changes

```python
edited_df = st.data_editor(df, key="editor")

# Access change details
changes = st.session_state["editor"]
# {"edited_rows": {0: {"score": 99}}, "added_rows": [...], "deleted_rows": [...]}
```

## Column Configuration

Customize how columns render in `st.dataframe` and `st.data_editor`:

```python
st.dataframe(df, column_config={
    "name": st.column_config.TextColumn("Full Name", width="medium"),
    "score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100),
    "url": st.column_config.LinkColumn("Website"),
    "avatar": st.column_config.ImageColumn("Avatar", width="small"),
    "rating": st.column_config.NumberColumn("Rating", format="%.1f ⭐"),
    "date": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
    "select": st.column_config.CheckboxColumn("Select", default=False),
    "chart": st.column_config.BarChartColumn("Trend", y_min=0, y_max=100),
    "line": st.column_config.LineChartColumn("History"),
    "area": st.column_config.AreaChartColumn("Usage"),
})
```

### Available Column Types

| Type | Use Case |
|------|----------|
| `TextColumn` | Plain text |
| `NumberColumn` | Numbers with formatting |
| `CheckboxColumn` | Boolean toggles |
| `SelectboxColumn` | Dropdown selection |
| `DateColumn` | Date values |
| `TimeColumn` | Time values |
| `DatetimeColumn` | Date + time |
| `LinkColumn` | Clickable URLs |
| `ImageColumn` | Image thumbnails |
| `ProgressColumn` | Progress bars |
| `BarChartColumn` | Inline bar chart |
| `LineChartColumn` | Inline sparkline |
| `AreaChartColumn` | Inline area chart |
| `ListColumn` | List of values |

## st.metric

Display KPI-style metrics with delta indicators:

```python
st.metric(
    label="Revenue",
    value="$12.4M",
    delta="8.2%",
    delta_color="normal",   # "normal", "inverse", "off"
)
```

### Three-Column KPI Layout

```python
col1, col2, col3 = st.columns(3)
col1.metric("Temperature", "72°F", "3°F")
col2.metric("Humidity", "45%", "-2%")
col3.metric("Pressure", "30.1 inHg", "0.02")
```

### Delta Description (v1.55+)

```python
st.metric(
    label="Users",
    value="1,234",
    delta="12%",
    delta_description="vs last month",
)
```

## st.json

Pretty-print JSON/dict with syntax highlighting:

```python
st.json({"name": "Alice", "scores": [95, 87, 92], "active": True})

# Collapsed by default
st.json(data, expanded=False)

# Expand to specific depth
st.json(data, expanded=2)
```

## st.table

Static (non-interactive) table — good for small, fixed data:

```python
st.table(df)
```

Unlike `st.dataframe`, `st.table` renders the entire table without scrolling, sorting, or column resizing.

## Common Patterns

### Conditional Data Display

```python
if st.checkbox("Show raw data"):
    st.dataframe(df)
```

### Filtered Dataframe

```python
column = st.selectbox("Filter by column", df.columns)
value = st.text_input(f"Filter {column}")
if value:
    filtered = df[df[column].astype(str).str.contains(value, case=False)]
    st.dataframe(filtered)
else:
    st.dataframe(df)
```

### Download Data

```python
csv = df.to_csv(index=False)
st.download_button("Download CSV", csv, "data.csv", "text/csv")
```

## Related Topics

- `02-input-widgets.md` — Input elements
- `03-charts-visualization.md` — Chart elements
- `04-layout-containers.md` — Arranging elements
