# Streamlit — Connections & Configuration

> Source: [docs.streamlit.io/develop/concepts/connections](https://docs.streamlit.io/develop/concepts/connections) | Version: 1.59.x

## Table of Contents

- [st.connection](#stconnection)
- [Built-in Connections](#built-in-connections)
- [Custom Connections](#custom-connections)
- [Secrets Management](#secrets-management)
- [Configuration](#configuration)
- [Authentication](#authentication)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## st.connection

Unified API for connecting to databases and APIs. Connections are cached via `st.cache_resource` internally.

```python
import streamlit as st

conn = st.connection("my_database", type="sql")
df = conn.query("SELECT * FROM users LIMIT 10")
st.dataframe(df)
```

### Parameters

```python
conn = st.connection(
    name="my_db",              # Used for secrets lookup
    type="sql",                # Connection type
    max_entries=None,          # Max cached connections
    ttl=None,                  # Cache expiration (seconds or timedelta)
    **kwargs,                  # Passed to the connection's _connect() method
)
```

### Type Resolution

- `"sql"` → `st.connections.SQLConnection`
- `"snowflake"` → `st.connections.SnowflakeConnection`
- Module path string → `"mypackage.MyConnection"`
- Class reference → `MyConnection`

## Built-in Connections

### SQLConnection

For any SQLAlchemy-supported database (PostgreSQL, MySQL, SQLite, etc.):

```python
conn = st.connection("my_db", type="sql")

# Simple query
df = conn.query("SELECT * FROM products WHERE price > :price", params={"price": 10})
st.dataframe(df)

# With TTL for auto-refresh
df = conn.query("SELECT * FROM orders", ttl="10m")
```

**secrets.toml:**

```toml
[connections.my_db]
type = "sql"
dialect = "postgresql"
host = "localhost"
port = 5432
database = "myapp"
username = "user"
password = "pass"

# Or use a URL
# url = "postgresql://user:pass@localhost:5432/myapp"
```

### SQLite Quick Start

```toml
# .streamlit/secrets.toml
[connections.my_db]
url = "sqlite:///data.db"
```

```python
conn = st.connection("my_db", type="sql")
df = conn.query("SELECT * FROM users")
```

### SnowflakeConnection

```python
conn = st.connection("snowflake")
df = conn.query("SELECT * FROM my_table")

# Access Snowpark session
session = conn.session()
```

**secrets.toml:**

```toml
[connections.snowflake]
account = "myaccount"
user = "myuser"
password = "mypassword"
warehouse = "COMPUTE_WH"
database = "MY_DB"
schema = "PUBLIC"
```

### Session and Raw Connection

```python
conn = st.connection("my_db", type="sql")

# Raw SQLAlchemy session
with conn.session as session:
    session.execute(text("INSERT INTO logs (msg) VALUES (:msg)"), {"msg": "hello"})
    session.commit()
```

## Custom Connections

Build your own connection class by extending `BaseConnection`:

```python
from streamlit.connections import BaseConnection
import pandas as pd

class MyAPIConnection(BaseConnection[dict]):
    def _connect(self, **kwargs) -> dict:
        api_key = self._secrets.get("api_key", kwargs.get("api_key"))
        base_url = self._secrets.get("base_url", "https://api.example.com")
        return {"api_key": api_key, "base_url": base_url}

    def query(self, endpoint: str, ttl: int = 3600) -> pd.DataFrame:
        @st.cache_data(ttl=ttl)
        def _query(endpoint):
            import requests
            config = self._instance
            resp = requests.get(
                f"{config['base_url']}/{endpoint}",
                headers={"Authorization": f"Bearer {config['api_key']}"},
            )
            return pd.DataFrame(resp.json())
        return _query(endpoint)
```

Usage:

```python
conn = st.connection("my_api", type=MyAPIConnection)
df = conn.query("users")
st.dataframe(df)
```

**secrets.toml:**

```toml
[connections.my_api]
api_key = "sk-..."
base_url = "https://api.example.com/v1"
```

## Secrets Management

### secrets.toml

Store sensitive values in `.streamlit/secrets.toml`:

```toml
# Simple key-value
OPENAI_API_KEY = "sk-..."
APP_PASSWORD = "mysecret"

# Nested sections
[database]
host = "localhost"
port = 5432
name = "myapp"
user = "admin"
password = "secret"

# Connection-specific (auto-resolved by st.connection)
[connections.my_db]
url = "postgresql://user:pass@host/db"
```

### Accessing Secrets

```python
# Top-level
api_key = st.secrets["OPENAI_API_KEY"]

# Nested
db_host = st.secrets["database"]["host"]
db_host = st.secrets.database.host   # Attribute syntax also works

# Check existence
if "OPENAI_API_KEY" in st.secrets:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
```

### Security Rules

1. **Never commit** `secrets.toml` to git — add to `.gitignore`
2. Use **environment variables** in production
3. Streamlit Community Cloud has its own secrets UI
4. Secrets are read-only — cannot modify at runtime

### Environment Variables

Streamlit also reads from environment variables:

```bash
export OPENAI_API_KEY="sk-..."
```

```python
import os
api_key = os.environ.get("OPENAI_API_KEY", st.secrets.get("OPENAI_API_KEY"))
```

## Configuration

### config.toml

Located at `.streamlit/config.toml`:

```toml
[server]
port = 8501
headless = true              # No browser auto-open
runOnSave = true             # Auto-reload on file save
maxUploadSize = 200          # Max upload size in MB
enableXsrfProtection = true
enableStaticServing = true   # Serve static files from /static

[browser]
gatherUsageStats = false
serverAddress = "localhost"

[theme]
base = "light"
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[client]
toolbarMode = "minimal"
showSidebarNavigation = true
disableDataExport = false    # v1.55+ hide CSV export

[runner]
magicEnabled = true
enforceSerializableSessionState = false
```

### st.set_page_config

Must be the first Streamlit call:

```python
st.set_page_config(
    page_title="My App",
    page_icon="📊",                     # Emoji or image path
    layout="wide",                       # "centered" or "wide"
    initial_sidebar_state="expanded",    # "auto", "expanded", "collapsed"
    menu_items={
        "Get Help": "https://docs.example.com",
        "Report a bug": "https://github.com/example/issues",
        "About": "My awesome app v1.0",
    },
)
```

### Runtime Options

```python
# Get a config value
theme_color = st.get_option("theme.primaryColor")

# Set (very limited — most options are config.toml only)
st.set_option("deprecation.showPyplotGlobalUse", False)
```

## Authentication

### Built-in OIDC (v1.55+)

```python
st.login("my_oidc_provider")

# After login
user = st.user
st.write(f"Welcome, {user.name}!")
st.write(f"Email: {user.email}")

st.logout("Sign out")
```

Configure in `secrets.toml`:

```toml
[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
cookie_secret = "random-secret-string"

[auth.my_oidc_provider]
client_id = "..."
client_secret = "..."
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

### Manual Auth Pattern

```python
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    pw = st.text_input("Password", type="password")
    if st.button("Login") and pw == st.secrets["APP_PASSWORD"]:
        st.session_state.authenticated = True
        st.rerun()
    st.stop()

# Protected content below
st.title("Admin Dashboard")
```

## Common Patterns

### Database Dashboard

```python
conn = st.connection("analytics_db", type="sql")

@st.cache_data(ttl="5m")
def load_metrics():
    return conn.query("""
        SELECT date, revenue, orders, users
        FROM daily_metrics
        WHERE date >= CURRENT_DATE - INTERVAL '30 days'
        ORDER BY date
    """)

df = load_metrics()
st.line_chart(df, x="date", y=["revenue", "orders"])
```

### Multi-Connection App

```python
# Connect to multiple data sources
pg_conn = st.connection("postgres", type="sql")
sf_conn = st.connection("snowflake")

pg_data = pg_conn.query("SELECT * FROM users")
sf_data = sf_conn.query("SELECT * FROM events")
```

### Static File Serving

Enable in config:

```toml
[server]
enableStaticServing = true
```

Place files in a `static/` directory:

```
my-app/
├── app.py
└── static/
    ├── style.css
    └── logo.png
```

Access via `http://localhost:8501/app/static/logo.png`.

## Common Pitfalls

### 1. Committing secrets.toml

Always add to `.gitignore`:

```gitignore
.streamlit/secrets.toml
```

### 2. Connection String Format

Different databases use different SQLAlchemy dialects:

```toml
# PostgreSQL
url = "postgresql://user:pass@host:5432/db"

# MySQL
url = "mysql+pymysql://user:pass@host:3306/db"

# SQLite
url = "sqlite:///path/to/db.sqlite"
```

### 3. Query Without TTL

```python
# Cached forever — stale data
df = conn.query("SELECT * FROM orders")

# Better — refresh every 5 minutes
df = conn.query("SELECT * FROM orders", ttl="5m")
```

## Related Topics

- `06-caching-performance.md` — Caching connections with cache_resource
- `08-multipage-apps.md` — Auth gating for pages
- `12-testing-deployment.md` — Deployment configuration
