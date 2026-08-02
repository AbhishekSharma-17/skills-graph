# Streamlit — Input Widgets

> Source: [docs.streamlit.io/develop/api-reference/widgets](https://docs.streamlit.io/develop/api-reference/widgets) | Version: 1.59.x

## Table of Contents

- [Widget Fundamentals](#widget-fundamentals)
- [Buttons](#buttons)
- [Selection Widgets](#selection-widgets)
- [Text Input](#text-input)
- [Numeric Input](#numeric-input)
- [Date and Time](#date-and-time)
- [File and Media Input](#file-and-media-input)
- [Specialized Widgets](#specialized-widgets)
- [Widget Patterns](#widget-patterns)
- [Common Pitfalls](#common-pitfalls)

## Widget Fundamentals

Every widget **returns its current value** and triggers a script rerun when the value changes:

```python
name = st.text_input("Name")    # Returns str
age = st.slider("Age", 0, 100)  # Returns int
agree = st.checkbox("Agree")    # Returns bool
```

### Widget Keys

Assign `key` to link a widget to `st.session_state`:

```python
st.text_input("Name", key="user_name")
# Accessible as st.session_state.user_name
```

### Callbacks

Execute a function when a widget value changes:

```python
def on_name_change():
    st.session_state.greeting = f"Hello, {st.session_state.user_name}!"

st.text_input("Name", key="user_name", on_change=on_name_change)
```

### Disabled and Label Visibility

```python
st.text_input("Name", disabled=True)
st.text_input("Name", label_visibility="hidden")    # "visible", "hidden", "collapsed"
```

## Buttons

### st.button

Returns `True` only during the rerun triggered by the click:

```python
if st.button("Click me"):
    st.write("Button was clicked!")
# On the NEXT rerun, this is False again
```

Parameters:

```python
st.button(
    "Submit",
    type="primary",       # "primary" (filled) or "secondary" (outline)
    icon=":material/send:",
    use_container_width=True,
    on_click=my_callback,
    args=(arg1,),
    kwargs={"key": "val"},
    disabled=False,
)
```

### st.download_button

Serve a file for download:

```python
st.download_button(
    label="Download CSV",
    data=df.to_csv(index=False),
    file_name="export.csv",
    mime="text/csv",
)

# Binary file
with open("report.pdf", "rb") as f:
    st.download_button("Download PDF", f, "report.pdf", "application/pdf")
```

### st.link_button

Navigate to an external URL:

```python
st.link_button("Go to Streamlit", "https://streamlit.io")
```

### st.menu_button

Dropdown menu from a button (v1.55+):

```python
with st.menu_button("Options"):
    if st.button("Edit"):
        st.write("Editing...")
    if st.button("Delete"):
        st.write("Deleting...")
```

## Selection Widgets

### st.selectbox — Single Selection Dropdown

```python
option = st.selectbox("Choose a color", ["Red", "Green", "Blue"])
st.write(f"You selected: {option}")

# With index and placeholder
option = st.selectbox(
    "Status",
    ["Active", "Inactive", "Pending"],
    index=None,                    # No default selection
    placeholder="Select a status",
)
```

### st.multiselect — Multiple Selection

```python
colors = st.multiselect(
    "Favorite colors",
    ["Red", "Green", "Blue", "Yellow"],
    default=["Red", "Blue"],
    max_selections=3,
)
```

### st.radio — Radio Buttons

```python
genre = st.radio(
    "Favorite genre",
    ["Comedy", "Drama", "Documentary"],
    index=0,
    horizontal=True,      # Lay out horizontally
    captions=["😂", "🎭", "📹"],
)
```

### st.checkbox — Boolean Toggle

```python
show_data = st.checkbox("Show raw data", value=False)
if show_data:
    st.dataframe(df)
```

### st.toggle — On/Off Switch

```python
dark_mode = st.toggle("Dark mode", value=False)
```

### st.pills — Pill Buttons (v1.55+)

```python
selected = st.pills(
    "Tags",
    ["Sports", "AI", "Politics", "Science"],
    selection_mode="multi",   # "single" or "multi"
    default=["AI"],
)
```

### st.segmented_control — Button Group (v1.55+)

```python
view = st.segmented_control(
    "View",
    ["Table", "Chart", "Map"],
    default="Table",
    selection_mode="single",
)
```

### st.select_slider — Slider with Discrete Options

```python
size = st.select_slider("Size", options=["XS", "S", "M", "L", "XL"], value="M")

# Range slider
start, end = st.select_slider(
    "Range",
    options=["Mon", "Tue", "Wed", "Thu", "Fri"],
    value=("Tue", "Thu"),
)
```

### st.color_picker

```python
color = st.color_picker("Pick a color", "#FF0000")
```

## Text Input

### st.text_input — Single Line

```python
name = st.text_input("Name", value="", max_chars=50, placeholder="Enter name")

# Password input
password = st.text_input("Password", type="password")
```

### st.text_area — Multi-Line

```python
text = st.text_area(
    "Description",
    value="",
    height=200,
    max_chars=1000,
    placeholder="Enter description...",
)
```

### st.chat_input — Chat-Style Input

Pinned to the bottom of the app:

```python
prompt = st.chat_input("Say something")
if prompt:
    st.write(f"You said: {prompt}")
```

## Numeric Input

### st.number_input

```python
age = st.number_input("Age", min_value=0, max_value=120, value=25, step=1)
price = st.number_input("Price", min_value=0.0, value=9.99, step=0.01, format="%.2f")
```

### st.slider — Numeric Slider

```python
# Single value
val = st.slider("Value", min_value=0, max_value=100, value=50, step=5)

# Range slider (pass tuple as value)
low, high = st.slider("Range", 0.0, 100.0, (25.0, 75.0))

# Float slider
temp = st.slider("Temperature", -10.0, 40.0, 20.0, 0.5)
```

## Date and Time

### st.date_input

```python
from datetime import date, timedelta

d = st.date_input("Date", value=date.today())

# Date range
start, end = st.date_input(
    "Date range",
    value=(date.today() - timedelta(days=30), date.today()),
    min_value=date(2020, 1, 1),
    max_value=date.today(),
)
```

### st.time_input

```python
from datetime import time

t = st.time_input("Alarm time", value=time(8, 0), step=timedelta(minutes=15))
```

### st.datetime_input (v1.55+)

```python
from datetime import datetime

dt = st.datetime_input("Schedule event", value=datetime.now())
```

## File and Media Input

### st.file_uploader

```python
uploaded = st.file_uploader("Upload CSV", type=["csv", "xlsx"])
if uploaded is not None:
    df = pd.read_csv(uploaded)
    st.dataframe(df)

# Multiple files
files = st.file_uploader("Upload images", type=["png", "jpg"], accept_multiple_files=True)
for f in files:
    st.image(f)
```

### st.camera_input

```python
photo = st.camera_input("Take a photo")
if photo is not None:
    st.image(photo)
```

### st.audio_input

```python
audio = st.audio_input("Record audio")
if audio is not None:
    st.audio(audio)
```

## Specialized Widgets

### st.feedback — Star Ratings (v1.55+)

```python
sentiment = st.feedback("stars")    # Returns 0-4 (None if unrated)
# Also: "thumbs", "faces"
```

### st.pagination (v1.55+)

```python
page = st.pagination(total_pages=10)
st.write(f"Page {page}")
```

### st.page_link — Navigation Link

```python
st.page_link("pages/dashboard.py", label="Go to Dashboard", icon="📊")
st.page_link("https://streamlit.io", label="Streamlit Docs", icon="🌐")
```

## Widget Patterns

### Dynamic Widget Options

```python
category = st.selectbox("Category", ["Fruits", "Vegetables"])
if category == "Fruits":
    item = st.selectbox("Item", ["Apple", "Banana", "Cherry"])
else:
    item = st.selectbox("Item", ["Carrot", "Broccoli", "Spinach"])
```

### Sidebar Widgets

```python
with st.sidebar:
    st.title("Settings")
    theme = st.selectbox("Theme", ["Light", "Dark"])
    font_size = st.slider("Font size", 10, 24, 14)
```

### Reset Button Pattern

```python
if "counter" not in st.session_state:
    st.session_state.counter = 0

col1, col2 = st.columns(2)
with col1:
    if st.button("Increment"):
        st.session_state.counter += 1
with col2:
    if st.button("Reset"):
        st.session_state.counter = 0

st.write(f"Count: {st.session_state.counter}")
```

## Common Pitfalls

### Button Value is Ephemeral

`st.button` returns `True` only during the rerun it triggered. Use session state for persistent actions:

```python
# Wrong — data disappears on next interaction
if st.button("Load"):
    data = load_data()  # Lost after any other widget interaction

# Correct
if st.button("Load"):
    st.session_state.data = load_data()
if "data" in st.session_state:
    st.dataframe(st.session_state.data)
```

### Widget Default Values

Cannot set `st.button` or `st.file_uploader` values via session state — raises `StreamlitAPIException`.

### Key Uniqueness

Every widget needs a unique `key` if you create multiple instances of the same widget type:

```python
for i, col in enumerate(columns):
    st.text_input(f"Value for {col}", key=f"input_{i}")
```

## Related Topics

- `05-session-state.md` — State management and callbacks
- `07-forms-fragments.md` — Grouping widgets in forms
- `04-layout-containers.md` — Widget placement
