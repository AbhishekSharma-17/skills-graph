# Streamlit — Layout & Containers

> Source: [docs.streamlit.io/develop/api-reference/layouts](https://docs.streamlit.io/develop/api-reference/layouts) | Version: 1.59.x

## Table of Contents

- [st.columns](#stcolumns)
- [st.container](#stcontainer)
- [st.sidebar](#stsidebar)
- [st.tabs](#sttabs)
- [st.expander](#stexpander)
- [st.popover](#stpopover)
- [st.dialog](#stdialog)
- [st.empty](#stempty)
- [st.bottom](#stbottom)
- [st.space](#stspace)
- [Layout Patterns](#layout-patterns)

## st.columns

Create side-by-side containers:

```python
col1, col2, col3 = st.columns(3)

with col1:
    st.header("Column 1")
    st.write("Content here")

with col2:
    st.header("Column 2")
    st.metric("Users", "1,234")

with col3:
    st.header("Column 3")
    st.line_chart([1, 2, 3, 4])
```

### Custom Column Widths

```python
left, right = st.columns([2, 1])    # 2:1 ratio
left, middle, right = st.columns([1, 3, 1])

# With gap control
col1, col2 = st.columns(2, gap="large")   # "small", "medium", "large"
```

### Vertical Alignment

```python
col1, col2 = st.columns(2, vertical_alignment="center")
# "top" (default), "center", "bottom"
```

### Alternative Syntax

```python
col1, col2 = st.columns(2)
col1.write("Left content")
col2.write("Right content")
```

## st.container

Generic multi-element container — useful for grouping or out-of-order rendering:

```python
with st.container():
    st.write("Inside the container")
    st.line_chart([1, 2, 3])
```

### Fixed-Height Container with Scrolling

```python
with st.container(height=300):
    for i in range(50):
        st.write(f"Row {i}")
```

### Bordered Container

```python
with st.container(border=True):
    st.write("This has a visible border")
```

### Out-of-Order Rendering

```python
placeholder = st.container()

st.write("This appears second")

# Write to the container after other elements
with placeholder:
    st.write("This appears first")
```

## st.sidebar

Collapsible sidebar panel:

```python
with st.sidebar:
    st.title("Settings")
    theme = st.selectbox("Theme", ["Light", "Dark"])
    font_size = st.slider("Font size", 10, 24, 14)
    st.divider()
    st.write("Version 1.0")
```

Alternative syntax:

```python
st.sidebar.title("Settings")
theme = st.sidebar.selectbox("Theme", ["Light", "Dark"])
```

### Sidebar with Logo

```python
st.logo("logo.png", link="https://myapp.com")
```

`st.logo` places an image in the sidebar header (collapsed: icon, expanded: full logo).

## st.tabs

Tabbed interface:

```python
tab1, tab2, tab3 = st.tabs(["📈 Chart", "🗃 Data", "⚙️ Settings"])

with tab1:
    st.line_chart(data)

with tab2:
    st.dataframe(df)

with tab3:
    st.slider("Parameter", 0, 100)
```

### Dynamic Tab Content

```python
tabs = st.tabs([f"Tab {i}" for i in range(5)])
for i, tab in enumerate(tabs):
    with tab:
        st.write(f"Content for tab {i}")
```

### on_change Callback (v1.55+)

```python
def tab_changed():
    st.write(f"Switched to tab index: {st.session_state.my_tabs}")

st.tabs(["A", "B", "C"], key="my_tabs", on_change=tab_changed)
```

## st.expander

Collapsible section:

```python
with st.expander("See details"):
    st.write("Hidden content revealed on click")
    st.code("print('hello')")
```

### Initially Expanded

```python
with st.expander("Advanced options", expanded=True):
    st.slider("Learning rate", 0.001, 1.0, 0.01)
```

### With Icon

```python
with st.expander("🔧 Configuration", icon=":material/settings:"):
    st.write("Settings here")
```

## st.popover

Floating container triggered by a button:

```python
with st.popover("Open settings"):
    st.markdown("**Filter options:**")
    red = st.checkbox("Red")
    blue = st.checkbox("Blue")
    green = st.checkbox("Green")

if red:
    st.write("Showing red items")
```

### Popover Width

```python
with st.popover("Wide menu", use_container_width=True):
    st.write("Full-width popover content")
```

## st.dialog

Modal dialog that reruns independently:

```python
@st.dialog("Edit item")
def edit_dialog(item_name):
    new_name = st.text_input("Name", value=item_name)
    if st.button("Save"):
        st.session_state.item_name = new_name
        st.rerun()

if st.button("Edit"):
    edit_dialog("My Item")
```

### Key Points About Dialogs

- Defined using the `@st.dialog` decorator on a function
- The function is called to open the dialog
- Widgets inside the dialog rerun only the dialog, not the full app
- Call `st.rerun()` to close the dialog and refresh the app
- Cannot nest dialogs

### Dialog with Form

```python
@st.dialog("Add User")
def add_user_dialog():
    with st.form("user_form"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        role = st.selectbox("Role", ["Admin", "User", "Viewer"])
        if st.form_submit_button("Create"):
            st.session_state.users.append({"name": name, "email": email, "role": role})
            st.rerun()
```

## st.empty

Single-element container that can be overwritten:

```python
placeholder = st.empty()
placeholder.text("Loading...")

import time
time.sleep(2)

placeholder.text("Done!")       # Replaces previous content
placeholder.empty()             # Clears the container
```

### Progress Animation

```python
import time

placeholder = st.empty()
for i in range(100):
    placeholder.metric("Progress", f"{i+1}%")
    time.sleep(0.01)
placeholder.success("Complete!")
```

## st.bottom

Pin content to the bottom of the app (above `st.chat_input`):

```python
with st.bottom():
    cols = st.columns(3)
    cols[0].button("Action 1")
    cols[1].button("Action 2")
    cols[2].button("Action 3")
```

## st.space

Add vertical or horizontal spacing:

```python
st.space()           # Default vertical space
st.space("lg")       # "sm", "md", "lg", "xl"
```

## Layout Patterns

### Dashboard Layout

```python
st.set_page_config(layout="wide")

# Header row
col1, col2, col3, col4 = st.columns(4)
col1.metric("Revenue", "$12.4M", "8%")
col2.metric("Users", "1,234", "12%")
col3.metric("Orders", "567", "-3%")
col4.metric("Satisfaction", "4.5/5", "0.2")

# Main content
left, right = st.columns([2, 1])
with left:
    st.subheader("Revenue Trend")
    st.line_chart(revenue_data)
with right:
    st.subheader("Top Products")
    st.dataframe(products_df)
```

### Sidebar + Main + Detail

```python
with st.sidebar:
    selected = st.radio("Section", ["Overview", "Details", "Settings"])

if selected == "Overview":
    st.title("Overview")
    st.write("Dashboard content")
elif selected == "Details":
    st.title("Details")
    col1, col2 = st.columns(2)
    with col1:
        st.write("Left detail")
    with col2:
        st.write("Right detail")
```

### Accordion FAQ

```python
faqs = [
    ("How do I install?", "Run `pip install streamlit`"),
    ("How do I deploy?", "Use Streamlit Community Cloud"),
    ("Is it free?", "Yes, the framework is open source"),
]

for question, answer in faqs:
    with st.expander(question):
        st.write(answer)
```

## Related Topics

- `02-input-widgets.md` — Widgets to place in containers
- `08-multipage-apps.md` — App-level layout with pages
- `07-forms-fragments.md` — Forms and independent reruns
