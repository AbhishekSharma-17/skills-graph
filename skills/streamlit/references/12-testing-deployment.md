# Streamlit — Testing & Deployment

> Source: [docs.streamlit.io/develop/api-reference/testing](https://docs.streamlit.io/develop/api-reference/testing) | Version: 1.59.x

## Table of Contents

- [AppTest Framework](#apptest-framework)
- [Testing Widgets](#testing-widgets)
- [Testing Patterns](#testing-patterns)
- [Deployment Overview](#deployment-overview)
- [Streamlit Community Cloud](#streamlit-community-cloud)
- [Docker Deployment](#docker-deployment)
- [ASGI Mounting](#asgi-mounting)
- [Production Configuration](#production-configuration)
- [Common Pitfalls](#common-pitfalls)

## AppTest Framework

`st.testing.v1.AppTest` simulates a running Streamlit app for automated testing. No browser required.

### Basic Usage

```python
# test_app.py
from streamlit.testing.v1 import AppTest

def test_title_displayed():
    at = AppTest.from_file("app.py")
    at.run()
    assert not at.exception
    assert at.title[0].value == "My App"
```

### Creating Test Instances

```python
# From a file
at = AppTest.from_file("app.py")

# From a function
def my_app():
    import streamlit as st
    st.title("Test App")
    st.text_input("Name", key="name")

at = AppTest.from_function(my_app)

# From a string
at = AppTest.from_string("""
import streamlit as st
st.title("Hello")
""")
```

### Running and Inspecting

```python
at = AppTest.from_file("app.py")
at.run()

# Check for exceptions
assert not at.exception

# Access elements by type
assert at.title[0].value == "Dashboard"
assert at.markdown[0].value == "Welcome!"
assert len(at.dataframe) == 1

# Access widgets
assert at.text_input[0].value == ""
assert at.slider[0].value == 50
assert at.selectbox[0].value == "Option A"
```

### Setting Secrets in Tests

```python
at = AppTest.from_file("app.py")
at.secrets["OPENAI_API_KEY"] = "test-key"
at.secrets["database"] = {"host": "localhost", "port": 5432}
at.run()
```

### Setting Session State

```python
at = AppTest.from_file("app.py")
at.session_state["authenticated"] = True
at.session_state["user"] = {"name": "Test User"}
at.run()
```

## Testing Widgets

### Interacting with Widgets

```python
at = AppTest.from_file("app.py")
at.run()

# Text input
at.text_input[0].input("Alice").run()
assert at.markdown[0].value == "Hello, Alice!"

# Slider
at.slider[0].set_value(75).run()
assert at.metric[0].value == "75"

# Button
at.button[0].click().run()
assert at.success[0].value == "Clicked!"

# Selectbox
at.selectbox[0].select("Option B").run()

# Checkbox
at.checkbox[0].check().run()
at.checkbox[0].uncheck().run()

# Number input
at.number_input[0].increment().run()
at.number_input[0].set_value(42).run()

# Multiselect
at.multiselect[0].select("A").select("B").run()

# Radio
at.radio[0].set_value("Option C").run()

# Toggle
at.toggle[0].set_value(True).run()

# Date input
from datetime import date
at.date_input[0].set_value(date(2024, 6, 15)).run()
```

### Available Element Accessors

| Accessor | Widget/Element |
|----------|---------------|
| `at.title` | `st.title` |
| `at.header` | `st.header` |
| `at.subheader` | `st.subheader` |
| `at.markdown` | `st.markdown` |
| `at.caption` | `st.caption` |
| `at.text` | `st.text` |
| `at.code` | `st.code` |
| `at.success` | `st.success` |
| `at.info` | `st.info` |
| `at.warning` | `st.warning` |
| `at.error` | `st.error` |
| `at.exception` | `st.exception` |
| `at.dataframe` | `st.dataframe` |
| `at.table` | `st.table` |
| `at.json` | `st.json` |
| `at.metric` | `st.metric` |
| `at.button` | `st.button` |
| `at.text_input` | `st.text_input` |
| `at.text_area` | `st.text_area` |
| `at.number_input` | `st.number_input` |
| `at.slider` | `st.slider` |
| `at.selectbox` | `st.selectbox` |
| `at.multiselect` | `st.multiselect` |
| `at.checkbox` | `st.checkbox` |
| `at.radio` | `st.radio` |
| `at.toggle` | `st.toggle` |
| `at.date_input` | `st.date_input` |
| `at.time_input` | `st.time_input` |
| `at.color_picker` | `st.color_picker` |
| `at.chat_input` | `st.chat_input` |

### Accessing by Key

```python
# Instead of positional indexing
at.text_input(key="username").input("Alice").run()
at.slider(key="temperature").set_value(0.5).run()
```

## Testing Patterns

### pytest Integration

```python
# test_dashboard.py
import pytest
from streamlit.testing.v1 import AppTest

@pytest.fixture
def app():
    at = AppTest.from_file("pages/dashboard.py")
    at.session_state["authenticated"] = True
    at.run()
    return at

def test_initial_load(app):
    assert not app.exception
    assert app.title[0].value == "Dashboard"

def test_filter_updates_chart(app):
    app.selectbox[0].select("Monthly").run()
    assert not app.exception
    assert len(app.dataframe) == 1

def test_error_on_invalid_input(app):
    app.number_input[0].set_value(-1).run()
    assert app.error[0].value == "Value must be positive"
```

### Testing Multipage Apps

```python
def test_page_navigation():
    at = AppTest.from_file("app.py")
    at.run()

    # Simulate page switch
    at = AppTest.from_file("pages/settings.py")
    at.session_state["user"] = {"role": "admin"}
    at.run()
    assert at.title[0].value == "Settings"
```

### Mocking External APIs

```python
from unittest.mock import patch

def test_with_mock_api():
    with patch("utils.api.fetch_data") as mock_fetch:
        mock_fetch.return_value = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
        at = AppTest.from_file("app.py")
        at.run()
        assert len(at.dataframe) == 1
```

## Deployment Overview

| Platform | Best For | Cost |
|----------|----------|------|
| Community Cloud | Public apps, demos | Free |
| Snowflake | Enterprise, data apps | Snowflake pricing |
| Docker | Self-hosted, any cloud | Infrastructure cost |
| Cloud VMs | Full control | VM pricing |
| PaaS (Railway, Render) | Quick deploy | Platform pricing |

## Streamlit Community Cloud

### Deploy from GitHub

1. Push code to a GitHub repo
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Select repo, branch, and entrypoint file
4. Click "Deploy"

### Requirements

```
# requirements.txt
streamlit>=1.59.0
pandas>=2.0.0
plotly>=5.0.0
openai>=1.0.0
```

### Secrets on Community Cloud

Add secrets via the app dashboard UI — they're stored encrypted and injected at runtime.

### Resource Limits

- 1 GB RAM per app
- Apps sleep after inactivity
- Public GitHub repos only (free tier)

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### docker-compose.yml

```yaml
services:
  streamlit:
    build: .
    ports:
      - "8501:8501"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

### Build and Run

```bash
docker build -t my-streamlit-app .
docker run -p 8501:8501 -e OPENAI_API_KEY="sk-..." my-streamlit-app
```

## ASGI Mounting

Mount Streamlit inside a FastAPI or Starlette server (experimental, v1.55+):

```python
# server.py
from fastapi import FastAPI
from streamlit.web.stlite import st_app

api = FastAPI()

@api.get("/api/health")
def health():
    return {"status": "ok"}

@api.get("/api/data")
def get_data():
    return {"data": [1, 2, 3]}

# Mount Streamlit at /dashboard
app = st_app("dashboard_app.py", path="/dashboard")
api.mount("/dashboard", app)

# Run with: uvicorn server:api --reload
```

This allows serving a REST API and a Streamlit dashboard from the same process.

## Production Configuration

### Server Settings

```toml
# .streamlit/config.toml
[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = true
maxUploadSize = 200
maxMessageSize = 200

[browser]
gatherUsageStats = false
serverAddress = "0.0.0.0"

[client]
toolbarMode = "viewer"       # Hide dev tools in production
showSidebarNavigation = true
```

### Health Check

Streamlit exposes `/_stcore/health` — returns 200 when healthy:

```bash
curl http://localhost:8501/_stcore/health
# Returns: ok
```

### Reverse Proxy (nginx)

```nginx
server {
    listen 80;
    server_name myapp.example.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /_stcore/stream {
        proxy_pass http://localhost:8501/_stcore/stream;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

WebSocket support (`Upgrade` / `Connection` headers) is required for Streamlit's communication protocol.

## Common Pitfalls

### 1. Missing requirements.txt

Community Cloud and Docker need explicit dependencies. Use:

```bash
pip freeze > requirements.txt
# Or better, maintain manually to avoid bloat
```

### 2. Hardcoded Localhost

```python
# Bad — fails in deployment
conn = st.connection("db", url="postgresql://localhost:5432/app")

# Good — use secrets
conn = st.connection("db", type="sql")  # Reads from secrets.toml
```

### 3. Large File Uploads in Production

Default upload limit is 200 MB. Adjust in config:

```toml
[server]
maxUploadSize = 500
```

### 4. WebSocket Timeouts

Behind reverse proxies, WebSocket connections may timeout. Set appropriate timeouts:

```nginx
proxy_read_timeout 86400;
proxy_send_timeout 86400;
```

### 5. No Persistent Storage

Streamlit apps are stateless — file writes are lost on restart. Use external storage (S3, database, mounted volumes).

## Related Topics

- `11-connections-config.md` — Database connections and secrets
- `08-multipage-apps.md` — Page structure for deployment
- `06-caching-performance.md` — Performance optimization
