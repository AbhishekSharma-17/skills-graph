# Streamlit — Forms & Fragments

> Source: [docs.streamlit.io/develop/concepts/architecture](https://docs.streamlit.io/develop/concepts/architecture) | Version: 1.59.x

## Table of Contents

- [Forms](#forms)
- [Form Patterns](#form-patterns)
- [Fragments](#fragments)
- [Fragment Parameters](#fragment-parameters)
- [Fragment Patterns](#fragment-patterns)
- [Forms vs Fragments vs Callbacks](#forms-vs-fragments-vs-callbacks)
- [Common Pitfalls](#common-pitfalls)

## Forms

Forms batch widget input into a single rerun — widgets inside a form don't trigger reruns until the form is submitted.

### Basic Form

```python
with st.form("my_form"):
    name = st.text_input("Name")
    age = st.number_input("Age", 0, 120, 25)
    color = st.selectbox("Color", ["Red", "Blue", "Green"])
    submitted = st.form_submit_button("Submit")

if submitted:
    st.write(f"Name: {name}, Age: {age}, Color: {color}")
```

### Form with Variable Syntax

```python
form = st.form("my_form")
name = form.text_input("Name")
age = form.number_input("Age", 0, 120, 25)
form.form_submit_button("Submit")
```

### Form Submission Methods

Users can submit via:
- Clicking `st.form_submit_button`
- Pressing **Enter** in `st.number_input` or `st.text_input`
- Pressing **Ctrl+Enter** (Cmd+Enter on Mac) in `st.text_area`

### Form with Callback

```python
def process_form():
    st.session_state.result = f"Hello, {st.session_state.form_name}!"

with st.form("greeting"):
    st.text_input("Name", key="form_name")
    st.form_submit_button("Greet", on_click=process_form)

if "result" in st.session_state:
    st.success(st.session_state.result)
```

In callbacks, access widget values via `st.session_state[key]`, not the widget's return value.

### Form Rules

1. Every form **must** have exactly one `st.form_submit_button`
2. `st.button` and `st.download_button` **cannot** be inside forms
3. Forms **cannot** nest inside other forms
4. Only `st.form_submit_button` accepts `on_click` inside a form
5. Widgets inside forms don't trigger reruns until submission

## Form Patterns

### Data Entry Form

```python
with st.form("entry", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        first = st.text_input("First Name")
    with col2:
        last = st.text_input("Last Name")
    email = st.text_input("Email")
    role = st.selectbox("Role", ["Admin", "User", "Viewer"])
    submitted = st.form_submit_button("Create User")

if submitted:
    if first and last and email:
        st.session_state.setdefault("users", []).append(
            {"first": first, "last": last, "email": email, "role": role}
        )
        st.success(f"User {first} {last} created!")
    else:
        st.error("All fields required")
```

### Settings Form

```python
with st.form("settings"):
    st.subheader("Model Settings")
    temperature = st.slider("Temperature", 0.0, 2.0, 1.0, 0.1)
    max_tokens = st.number_input("Max Tokens", 100, 4096, 1024)
    model = st.selectbox("Model", ["gpt-4o", "gpt-4o-mini", "claude-sonnet"])
    stream = st.checkbox("Stream response", value=True)

    if st.form_submit_button("Save Settings"):
        st.session_state.settings = {
            "temperature": temperature,
            "max_tokens": max_tokens,
            "model": model,
            "stream": stream,
        }
        st.success("Settings saved!")
```

### Form with st.rerun

Use `st.rerun()` to reflect changes above the form:

```python
st.write(f"Current count: {st.session_state.get('count', 0)}")

with st.form("counter"):
    increment = st.number_input("Add", 1, 100, 1)
    if st.form_submit_button("Add"):
        st.session_state.count = st.session_state.get("count", 0) + increment
        st.rerun()  # Re-renders the count display above
```

## Fragments

Fragments enable **partial reruns** — when a widget inside a fragment changes, only that fragment re-executes, not the entire script. Introduced in v1.37.

### Basic Fragment

```python
@st.fragment
def filter_section():
    category = st.selectbox("Category", ["All", "Active", "Archived"])
    st.write(f"Showing: {category}")
    st.dataframe(filter_data(category))

filter_section()
st.write("This does NOT rerun when the selectbox changes")
```

### How Fragments Work

- **Fragment rerun**: only the fragment function executes; rest of the app is unchanged
- **Full rerun**: fragments execute as part of the normal top-to-bottom flow
- Widgets outside fragments trigger full reruns as usual
- Widgets inside fragments trigger fragment-only reruns

## Fragment Parameters

### run_every — Auto-Refresh

```python
@st.fragment(run_every="10s")
def live_metrics():
    data = fetch_latest_data()
    st.metric("Active Users", data["users"])
    st.metric("Requests/sec", data["rps"])

live_metrics()
```

Supported formats: `"5s"`, `"1m"`, `"30s"`, `timedelta(seconds=10)`

### parallel — Concurrent Execution

```python
@st.fragment(parallel=True)
def slow_chart():
    data = expensive_query()  # Runs concurrently during full reruns
    st.line_chart(data)

@st.fragment(parallel=True)
def another_chart():
    data = another_expensive_query()
    st.bar_chart(data)

slow_chart()
another_chart()
```

During full reruns, parallel fragments run in thread pools. During fragment reruns, they execute sequentially.

### Combined Parameters

```python
@st.fragment(parallel=True, run_every="5s")
def live_dashboard():
    data = fetch_latest()
    st.metric("Revenue", f"${data['revenue']:,.0f}")
    st.line_chart(data["history"])
```

## Fragment Patterns

### Independent Filter Sections

```python
@st.fragment
def revenue_chart():
    period = st.selectbox("Period", ["Daily", "Weekly", "Monthly"], key="rev_period")
    st.line_chart(get_revenue(period))

@st.fragment
def user_chart():
    metric = st.selectbox("Metric", ["Signups", "Active", "Churn"], key="user_metric")
    st.bar_chart(get_user_metric(metric))

col1, col2 = st.columns(2)
with col1:
    revenue_chart()
with col2:
    user_chart()
```

Changing the period selectbox only reruns the revenue chart, not the user chart.

### Streaming Fragment

```python
@st.fragment(run_every="2s")
def log_viewer():
    logs = read_latest_logs(n=20)
    with st.container(height=400):
        for log in logs:
            st.text(log)

log_viewer()
```

### Fragment with External Container

```python
header = st.container()

@st.fragment
def update_header():
    if st.button("Refresh"):
        with header:
            st.write(f"Last updated: {datetime.now()}")

update_header()
```

Caveat: elements written to external containers during fragment reruns **accumulate** — use `st.empty()` to prevent stacking.

## Forms vs Fragments vs Callbacks

| Feature | Forms | Fragments | Callbacks |
|---------|-------|-----------|-----------|
| **Purpose** | Batch input | Partial rerun | Pre-rerun action |
| **Rerun scope** | Full (on submit) | Fragment only | Full |
| **When runs** | On submit | On widget change | Before rerun |
| **Widget interaction** | Deferred | Immediate | N/A |
| **Use case** | Data entry, settings | Independent sections | State updates |
| **Nesting** | No | Yes | N/A |
| **Caching compat** | Yes | No (same function) | Yes |

### Decision Guide

- **"Don't rerun until the user is done"** → Form
- **"Only rerun this section"** → Fragment
- **"Run some code before the rerun"** → Callback
- **"Speed up expensive functions"** → Caching (not forms/fragments)

## Common Pitfalls

### 1. Fragment Return Values

Streamlit ignores fragment return values during reruns. Use session state to share data:

```python
@st.fragment
def selector():
    choice = st.selectbox("Pick", ["A", "B", "C"])
    st.session_state.choice = choice    # Share via session state

selector()
st.write(f"Selected: {st.session_state.get('choice', 'None')}")
```

### 2. Caching + Fragment on Same Function

Not supported — use caching for data functions called inside fragments:

```python
@st.cache_data
def load(category):
    return pd.read_csv(f"{category}.csv")

@st.fragment
def chart():
    cat = st.selectbox("Category", ["A", "B"])
    st.line_chart(load(cat))    # Cached function inside fragment
```

### 3. Widgets in External Containers (Fragments)

Widgets inside fragments must be in the fragment's main body — they cannot render in containers created outside the fragment.

### 4. Restricted Commands in Parallel Fragments

During parallel execution, `st.dialog`, `st.switch_page`, and writing to external containers are not allowed.

### 5. Form Submit Without on_click

Without a callback, the submit button's return value is only `True` during that one rerun:

```python
# The result display disappears on the next widget interaction
with st.form("f"):
    name = st.text_input("Name")
    if st.form_submit_button("Go"):
        st.write(f"Hello, {name}")  # Gone on next rerun

# Fix: persist in session state
with st.form("f"):
    name = st.text_input("Name")
    if st.form_submit_button("Go"):
        st.session_state.greeting = f"Hello, {name}"
if "greeting" in st.session_state:
    st.write(st.session_state.greeting)
```

## Related Topics

- `02-input-widgets.md` — All input widgets
- `05-session-state.md` — State persistence
- `06-caching-performance.md` — Caching strategies
- `00-overview.md` — Execution model
