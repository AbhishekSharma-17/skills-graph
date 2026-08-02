# Streamlit — Charts & Visualization

> Source: [docs.streamlit.io/develop/api-reference/charts](https://docs.streamlit.io/develop/api-reference/charts) | Version: 1.59.x

## Table of Contents

- [Built-in Charts](#built-in-charts)
- [Library Integrations](#library-integrations)
- [st.map](#stmap)
- [Chart Selection Events](#chart-selection-events)
- [Common Patterns](#common-patterns)

## Built-in Charts

Streamlit provides simple chart functions that accept DataFrames, NumPy arrays, or dicts directly. They use Vega-Lite under the hood.

### st.line_chart

```python
import streamlit as st
import pandas as pd
import numpy as np

df = pd.DataFrame(np.random.randn(20, 3), columns=["A", "B", "C"])
st.line_chart(df)
```

With explicit axis control:

```python
chart_data = pd.DataFrame({
    "date": pd.date_range("2024-01-01", periods=30),
    "revenue": np.random.randn(30).cumsum() + 100,
    "cost": np.random.randn(30).cumsum() + 80,
})

st.line_chart(
    chart_data,
    x="date",
    y=["revenue", "cost"],
    color=["#FF4B4B", "#0068C9"],
    x_label="Date",
    y_label="Amount ($)",
)
```

### st.area_chart

```python
st.area_chart(df)

st.area_chart(
    df,
    x="date",
    y="value",
    color="category",       # Color by column values
    stack=True,             # Stacked area (default: True)
)
```

### st.bar_chart

```python
st.bar_chart(df)

st.bar_chart(
    df,
    x="category",
    y="value",
    color="group",
    horizontal=True,        # Horizontal bars
    stack=False,            # Grouped bars
)
```

### st.scatter_chart

```python
st.scatter_chart(
    df,
    x="height",
    y="weight",
    color="species",
    size="age",             # Bubble chart (column for point sizes)
)
```

### Common Parameters for Built-in Charts

All built-in charts share these parameters:

```python
st.line_chart(
    data,
    x=None,                 # Column for x-axis (default: index)
    y=None,                 # Column(s) for y-axis
    x_label=None,           # Custom x-axis label
    y_label=None,           # Custom y-axis label
    color=None,             # Color column or hex color(s)
    width=0,                # Chart width (0 = auto)
    height=0,               # Chart height (0 = auto)
    use_container_width=True,
)
```

## Library Integrations

### st.plotly_chart — Plotly

```python
import plotly.express as px

fig = px.scatter(
    df, x="x", y="y", color="category",
    title="Scatter Plot",
    template="plotly_white",
)

st.plotly_chart(fig, use_container_width=True, theme="streamlit")
```

Parameters:

```python
st.plotly_chart(
    fig,
    use_container_width=True,
    theme="streamlit",       # "streamlit" (styled) or None (raw Plotly)
    on_select="rerun",       # Enable selection events
    selection_mode=["points", "box", "lasso"],
    key="my_plotly_chart",
)
```

### st.altair_chart — Altair / Vega-Lite

```python
import altair as alt

chart = alt.Chart(df).mark_circle().encode(
    x="x:Q",
    y="y:Q",
    color="category:N",
    tooltip=["x", "y", "category"],
).interactive()

st.altair_chart(chart, use_container_width=True, theme="streamlit")
```

### st.pyplot — Matplotlib

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.plot([1, 2, 3, 4], [10, 20, 25, 30])
ax.set_xlabel("X")
ax.set_ylabel("Y")

st.pyplot(fig)
```

Always pass the `fig` object explicitly — `st.pyplot()` without arguments uses the global Matplotlib state and shows a deprecation warning.

### st.vega_lite_chart — Raw Vega-Lite Spec

```python
st.vega_lite_chart(
    df,
    {
        "mark": {"type": "circle", "tooltip": True},
        "encoding": {
            "x": {"field": "x", "type": "quantitative"},
            "y": {"field": "y", "type": "quantitative"},
            "color": {"field": "category", "type": "nominal"},
        },
    },
    use_container_width=True,
)
```

### st.pydeck_chart — Deck.gl 3D Maps

```python
import pydeck as pdk

layer = pdk.Layer(
    "HexagonLayer",
    data=df,
    get_position=["lng", "lat"],
    radius=200,
    elevation_scale=4,
    elevation_range=[0, 1000],
    pickable=True,
    extruded=True,
)

view_state = pdk.ViewState(latitude=37.76, longitude=-122.4, zoom=11, pitch=50)

st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state))
```

### st.graphviz_chart — Graphviz DOT

```python
st.graphviz_chart("""
    digraph {
        A -> B
        B -> C
        B -> D
        C -> E
    }
""")
```

### st.mermaid_chart — Mermaid Diagrams (v1.55+)

```python
st.mermaid_chart("""
    graph TD
        A[Start] --> B{Decision}
        B -->|Yes| C[Action 1]
        B -->|No| D[Action 2]
""")
```

## st.map

Display a map with point markers:

```python
df = pd.DataFrame({
    "lat": [37.76, 37.77, 37.78],
    "lon": [-122.4, -122.41, -122.42],
})

st.map(df)
```

With customization:

```python
st.map(
    df,
    latitude="lat",
    longitude="lon",
    size="magnitude",          # Column for point sizes
    color="category",          # Column for point colors
    zoom=11,
    use_container_width=True,
)
```

## Chart Selection Events

Built-in charts and Plotly/Altair support selection events for interactivity:

```python
event = st.scatter_chart(
    df,
    x="x",
    y="y",
    on_select="rerun",
    selection_mode=["points", "box"],
    key="scatter",
)

# Access selected data
selected_points = event.selection.points
if selected_points:
    indices = [p["index"] for p in selected_points]
    st.write(f"Selected {len(indices)} points")
    st.dataframe(df.iloc[indices])
```

### Plotly Selection

```python
event = st.plotly_chart(
    fig,
    on_select="rerun",
    selection_mode=["points", "box", "lasso"],
    key="plotly_select",
)

selected = event.selection.points
```

## Common Patterns

### Dashboard with Multiple Charts

```python
col1, col2 = st.columns(2)
with col1:
    st.subheader("Revenue Trend")
    st.line_chart(revenue_df, x="month", y="amount")
with col2:
    st.subheader("Distribution")
    st.bar_chart(dist_df, x="category", y="count")
```

### Chart with Filters

```python
years = st.multiselect("Years", df["year"].unique(), default=df["year"].unique())
filtered = df[df["year"].isin(years)]
st.line_chart(filtered, x="month", y="sales", color="year")
```

### Dynamic Chart Type

```python
chart_type = st.selectbox("Chart type", ["Line", "Bar", "Area", "Scatter"])
chart_func = {
    "Line": st.line_chart,
    "Bar": st.bar_chart,
    "Area": st.area_chart,
    "Scatter": st.scatter_chart,
}[chart_type]
chart_func(df, x="x", y="y")
```

## Related Topics

- `01-text-data-display.md` — Data display with tables
- `04-layout-containers.md` — Multi-column chart layouts
- `07-forms-fragments.md` — Fragments for independent chart updates
