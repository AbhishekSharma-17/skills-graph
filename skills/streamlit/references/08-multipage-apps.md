# Streamlit — Multipage Apps

> Source: [docs.streamlit.io/develop/concepts/multipage-apps](https://docs.streamlit.io/develop/concepts/multipage-apps) | Version: 1.59.x

## Table of Contents

- [Two Approaches](#two-approaches)
- [st.navigation and st.Page (Preferred)](#stnavigation-and-stpage-preferred)
- [Pages Directory (Legacy)](#pages-directory-legacy)
- [Page Configuration](#page-configuration)
- [Dynamic Pages](#dynamic-pages)
- [Authentication Gating](#authentication-gating)
- [Navigation Patterns](#navigation-patterns)
- [Common Pitfalls](#common-pitfalls)

## Two Approaches

Streamlit offers two methods for multipage apps:

1. **`st.navigation` + `st.Page`** (preferred) — flexible, explicit routing
2. **`pages/` directory** (legacy) — convention-based, automatic sidebar

## st.navigation and st.Page (Preferred)

### Basic Setup

**app.py** (entrypoint):

```python
import streamlit as st

pg = st.navigation([
    st.Page("pages/dashboard.py", title="Dashboard", icon="📊"),
    st.Page("pages/analysis.py", title="Analysis", icon="🔍"),
    st.Page("pages/settings.py", title="Settings", icon="⚙️"),
])

pg.run()
```

**pages/dashboard.py**:

```python
import streamlit as st

st.title("Dashboard")
st.write("Welcome to the dashboard!")
```

### st.Page Parameters

```python
st.Page(
    page="pages/dashboard.py",   # File path or callable
    title="Dashboard",            # Navigation label
    icon="📊",                    # Sidebar icon (emoji or Material)
    url_path="dashboard",         # Custom URL path
    default=True,                 # Homepage (first page if not set)
)
```

### Pages from Functions

```python
def dashboard():
    st.title("Dashboard")
    st.line_chart([1, 2, 3])

def settings():
    st.title("Settings")
    st.slider("Volume", 0, 100)

pg = st.navigation([
    st.Page(dashboard, title="Dashboard", icon="📊"),
    st.Page(settings, title="Settings", icon="⚙️"),
])
pg.run()
```

### Grouped Navigation with Sections

```python
pg = st.navigation({
    "Reports": [
        st.Page("pages/dashboard.py", title="Dashboard"),
        st.Page("pages/analytics.py", title="Analytics"),
        st.Page("pages/alerts.py", title="Alerts"),
    ],
    "Admin": [
        st.Page("pages/users.py", title="Users"),
        st.Page("pages/settings.py", title="Settings"),
    ],
})
pg.run()
```

Sections render as labeled groups in the sidebar.

### Navigation Position

```python
# Sidebar (default)
pg = st.navigation(pages, position="sidebar")

# Top navigation bar
pg = st.navigation(pages, position="top")

# Hidden (build custom navigation)
pg = st.navigation(pages, position="hidden")
```

## Pages Directory (Legacy)

Place `.py` files in a `pages/` subdirectory alongside your entrypoint:

```
my-app/
├── app.py
└── pages/
    ├── 1_📊_Dashboard.py
    ├── 2_🔍_Analysis.py
    └── 3_⚙️_Settings.py
```

Streamlit auto-generates sidebar navigation from filenames. File naming conventions:
- Numeric prefix for ordering (`1_`, `2_`, `3_`)
- Emoji prefix for icons
- Underscores become spaces in labels
- `.py` extension stripped

### Limitations vs st.navigation

- Cannot group pages into sections
- Cannot dynamically show/hide pages
- Cannot use custom navigation (top bar, hidden)
- File naming controls ordering and labels

## Page Configuration

### Per-Page Browser Tab

```python
# In each page file
st.set_page_config(
    page_title="Dashboard — MyApp",   # Browser tab title
    page_icon="📊",                    # Favicon
    layout="wide",                     # "centered" or "wide"
)
```

`st.set_page_config` must be the first Streamlit call in the file.

### Shared Code Across Pages

Common code goes in the entrypoint (before `pg.run()`):

```python
# app.py
import streamlit as st

st.set_page_config(page_title="MyApp", layout="wide")
st.logo("logo.png")

# Shared sidebar
with st.sidebar:
    st.write(f"User: {st.session_state.get('user', 'Guest')}")

pg = st.navigation([...])
pg.run()
```

### Utility Modules

```python
# utils/data.py (not a page — no st.* calls at module level)
import pandas as pd

def load_data():
    return pd.read_csv("data.csv")
```

```python
# pages/dashboard.py
from utils.data import load_data

st.title("Dashboard")
df = load_data()
st.dataframe(df)
```

## Dynamic Pages

### Conditional Page Lists

```python
pages = [
    st.Page("pages/home.py", title="Home", default=True),
    st.Page("pages/dashboard.py", title="Dashboard"),
]

if st.session_state.get("is_admin"):
    pages.append(st.Page("pages/admin.py", title="Admin Panel"))

pg = st.navigation(pages)
pg.run()
```

### Role-Based Navigation

```python
ROLE_PAGES = {
    "viewer": [
        st.Page("pages/dashboard.py", title="Dashboard"),
    ],
    "editor": [
        st.Page("pages/dashboard.py", title="Dashboard"),
        st.Page("pages/editor.py", title="Editor"),
    ],
    "admin": [
        st.Page("pages/dashboard.py", title="Dashboard"),
        st.Page("pages/editor.py", title="Editor"),
        st.Page("pages/admin.py", title="Admin"),
        st.Page("pages/users.py", title="Users"),
    ],
}

role = st.session_state.get("role", "viewer")
pg = st.navigation(ROLE_PAGES[role])
pg.run()
```

## Authentication Gating

### Login Page Pattern

```python
# app.py
import streamlit as st

def login_page():
    st.title("Login")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if password == st.secrets["password"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Invalid password")

def logout_page():
    st.title("Logout")
    if st.button("Confirm Logout"):
        st.session_state.authenticated = False
        st.rerun()

if st.session_state.get("authenticated"):
    pg = st.navigation({
        "Main": [
            st.Page("pages/dashboard.py", title="Dashboard", default=True),
            st.Page("pages/analysis.py", title="Analysis"),
        ],
        "Account": [
            st.Page(logout_page, title="Logout"),
        ],
    })
else:
    pg = st.navigation([st.Page(login_page, title="Login")])

pg.run()
```

### Built-in Authentication (v1.55+)

```python
st.login("oidc_provider")      # OIDC-based login
st.logout("Logout", key="logout")
user_info = st.user             # Access authenticated user info
```

### URL Protection

Pages excluded from `st.navigation` are inaccessible even via direct URL. Attempting to access an unmapped URL shows "Page not found" and redirects to the default page.

## Navigation Patterns

### Programmatic Navigation

```python
st.switch_page("pages/dashboard.py")  # Navigate to a page
```

### Custom Navigation UI

```python
pg = st.navigation(pages, position="hidden")

# Build custom nav
col1, col2, col3 = st.columns(3)
with col1:
    st.page_link("pages/dashboard.py", label="Dashboard", icon="📊")
with col2:
    st.page_link("pages/analysis.py", label="Analysis", icon="🔍")
with col3:
    st.page_link("pages/settings.py", label="Settings", icon="⚙️")

pg.run()
```

### Shared State Across Pages

Session state persists across pages automatically:

```python
# pages/page1.py
st.session_state.shared_data = load_data()
st.switch_page("pages/page2.py")

# pages/page2.py
data = st.session_state.shared_data  # Available from page1
```

## Common Pitfalls

### 1. Forgetting pg.run()

```python
pg = st.navigation([...])
# ❌ Missing pg.run() — no page content renders
pg.run()  # ✅ Required to render the selected page
```

### 2. set_page_config Not First

```python
# ❌ Will raise an error
st.title("Hello")
st.set_page_config(page_title="MyApp")

# ✅ Must be first
st.set_page_config(page_title="MyApp")
st.title("Hello")
```

### 3. Mixing Both Approaches

Don't use both `st.navigation` and the `pages/` directory convention simultaneously — pick one.

### 4. Relative Imports in Pages

Page files are run as scripts, not modules. Use `sys.path` manipulation or a proper package structure for shared imports.

## Related Topics

- `05-session-state.md` — State across pages
- `04-layout-containers.md` — Layout within pages
- `11-connections-config.md` — Page configuration
