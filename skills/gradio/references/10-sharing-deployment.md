# Gradio — Sharing & Deployment

> Source: [gradio.app/guides/sharing-your-app](https://gradio.app/guides/sharing-your-app)

## Table of Contents

- [Overview](#overview)
- [Share Links](#share-links)
- [Hugging Face Spaces](#hugging-face-spaces)
- [Authentication](#authentication)
- [Embedding](#embedding)
- [FastAPI Integration](#fastapi-integration)
- [Docker Deployment](#docker-deployment)
- [Reverse Proxy](#reverse-proxy)
- [Progressive Web App](#progressive-web-app)
- [MCP Server](#mcp-server)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## Overview

Gradio offers multiple deployment strategies, from one-click sharing to production Docker deployments.

| Strategy | Persistence | Custom Domain | Auth | Best For |
|----------|-------------|---------------|------|----------|
| Share link | 72 hours | No | No | Quick demos |
| HF Spaces | Permanent | Yes (paid) | OAuth | Public models |
| Docker | Permanent | Yes | Custom | Production |
| FastAPI mount | Permanent | Yes | Full | Existing apps |

## Share Links

Create a public URL instantly:

```python
demo.launch(share=True)
# Prints: Running on public URL: https://07ff8706ab.gradio.live
```

- Link expires after 72 hours (was 7 days previously)
- Traffic is proxied through Gradio servers (no data stored)
- Works behind firewalls and NAT
- Requires internet connection
- Not for production use

### Custom Share Server

```python
demo.launch(
    share=True,
    share_server_address="my-frp-server.com:7000",
    share_server_protocol="https",
)
```

## Hugging Face Spaces

### CLI Deployment

```bash
# From your app directory
gradio deploy
```

Prompts for Space name, hardware, and secrets.

### Manual Deployment

1. Create a Space at `huggingface.co/new-space` with SDK = Gradio
2. Add a `README.md` with Space metadata:

```yaml
---
title: My Model Demo
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 6.22.0
app_file: app.py
pinned: false
---
```

3. Push your code:

```bash
git add . && git commit -m "Initial commit"
git push
```

### HF Spaces Features

| Feature | Configuration |
|---------|--------------|
| GPU | `hardware: t4-small` / `a10g-small` etc. |
| Secrets | Space Settings → Secrets |
| Custom domain | Space Settings → Custom domain (PRO) |
| Private | `private: true` in README |
| Persistent storage | Space Settings → Persistent storage |
| Sleep timeout | `sleep_time: 300` (seconds) |

### Duplicating Spaces

```python
demo = gr.Interface(
    fn=predict,
    inputs="image",
    outputs="label",
    allow_duplication=True,  # Show "Duplicate this Space" button
)
```

## Authentication

### Password Authentication

```python
# Single user
demo.launch(auth=("admin", "password123"))

# Multiple users
demo.launch(auth=[("user1", "pass1"), ("user2", "pass2")])

# Custom validation function
def auth_fn(username, password):
    return username == "admin" and check_password(password)

demo.launch(auth=auth_fn, auth_message="Please log in")
```

### Hugging Face OAuth

In `README.md` Space metadata:

```yaml
---
hf_oauth: true
hf_oauth_scopes:
  - read-repos
  - manage-repos
---
```

In your app:

```python
with gr.Blocks() as demo:
    gr.LoginButton()  # "Sign in with Hugging Face" button

    def greet(profile: gr.OAuthProfile | None):
        if profile is None:
            return "Please log in"
        return f"Hello, {profile.name}!"

    gr.Markdown().attach_load_event(greet, None)
```

### External OAuth (FastAPI)

```python
from fastapi import FastAPI, Depends
import gradio as gr

app = FastAPI()

def get_current_user(request):
    # Your OAuth verification logic
    token = request.headers.get("Authorization")
    return verify_token(token)

demo = gr.Blocks()
# ... build demo

app = gr.mount_gradio_app(
    app, demo, path="/demo",
    auth_dependency=get_current_user,
)
```

### Accessing User Info

```python
def process(text, request: gr.Request):
    username = request.username
    ip = request.client.host
    headers = request.headers
    query_params = request.query_params
    session_hash = request.session_hash
    return f"Hello {username} from {ip}"
```

## Embedding

### Web Component (Recommended)

```html
<script type="module" src="https://gradio.s3-us-west-2.amazonaws.com/6.22.0/gradio.js"></script>
<gradio-app src="https://your-space.hf.space"></gradio-app>
```

| Attribute | Description |
|-----------|-------------|
| `src` | URL of the Gradio app |
| `space` | HF Space name (alternative to `src`) |
| `eager` | Load immediately without lazy loading |
| `theme_mode` | `"light"`, `"dark"`, or `"system"` |
| `initial_height` | Height before app loads (e.g., `"400px"`) |

### IFrame

```html
<iframe
    src="https://your-space.hf.space"
    width="100%"
    height="600"
    frameborder="0"
></iframe>
```

## FastAPI Integration

Mount Gradio inside an existing FastAPI application:

```python
from fastapi import FastAPI
import gradio as gr

app = FastAPI()

@app.get("/api/health")
def health():
    return {"status": "ok"}

def predict(text):
    return text.upper()

demo = gr.Interface(fn=predict, inputs="textbox", outputs="textbox")
app = gr.mount_gradio_app(app, demo, path="/demo")

# Run with: uvicorn app:app --host 0.0.0.0 --port 8000
# Gradio at: http://localhost:8000/demo
# API at: http://localhost:8000/api/health
```

### Multiple Gradio Apps

```python
demo1 = gr.Interface(fn=fn1, inputs="text", outputs="text")
demo2 = gr.Interface(fn=fn2, inputs="image", outputs="label")

app = gr.mount_gradio_app(app, demo1, path="/text")
app = gr.mount_gradio_app(app, demo2, path="/image")
```

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860
ENV GRADIO_SERVER_NAME="0.0.0.0"

CMD ["python", "app.py"]
```

### docker-compose.yml

```yaml
services:
  gradio-app:
    build: .
    ports:
      - "7860:7860"
    environment:
      - GRADIO_SERVER_NAME=0.0.0.0
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

## Reverse Proxy

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name demo.example.com;

    location / {
        proxy_pass http://localhost:7860;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_buffering off;           # Important for streaming
        proxy_read_timeout 300s;       # Long requests
    }
}
```

Set `root_path` to match the proxy mount point:

```python
demo.launch(root_path="/demo")
```

## Progressive Web App

```python
demo.launch(
    pwa=True,
    favicon_path="icon.png",  # Required for PWA
)
```

Adds a service worker and manifest for installable app experience on mobile and desktop.

## MCP Server

Expose Gradio functions as tools for LLM integration:

```python
demo.launch(mcp_server=True)
# MCP endpoint available at /gradio_api/mcp/sse
```

This allows AI assistants (like Claude) to call your Gradio functions as tools via the Model Context Protocol.

## Common Patterns

### Production Checklist

```python
demo.launch(
    server_name="0.0.0.0",
    server_port=7860,
    auth=("admin", os.environ["APP_PASSWORD"]),
    max_file_size="50mb",
    allowed_paths=["./data"],
    blocked_paths=["./secrets"],
    show_error=False,        # Don't expose errors to users
    analytics_enabled=False, # Disable telemetry
    strict_cors=True,        # Restrict CORS
    quiet=True,              # Suppress logs in stdout
    favicon_path="icon.png",
    footer_links=[],         # Remove default footer
)
```

### Deep Links (Shareable State)

```python
with gr.Blocks() as demo:
    gr.DeepLinkButton()
    prompt = gr.Textbox(label="Prompt")
    output = gr.Textbox(label="Output")
    btn = gr.Button("Generate")
    btn.click(fn=generate, inputs=prompt, outputs=output)

# Users can share URLs like: https://app.com?prompt=hello
```

## Common Pitfalls

1. **Share links are public**: Anyone with the link can access your app — don't share links for apps with sensitive data
2. **Port conflicts**: Multiple Gradio apps auto-increment ports from 7860 — specify explicit ports in production
3. **WebSocket behind proxy**: Nginx must be configured for WebSocket upgrade headers or streaming/queue won't work
4. **HF Spaces timeout**: Free Spaces sleep after inactivity — use persistent storage for data that must survive restarts
5. **root_path mismatch**: If behind a reverse proxy at `/demo`, you must set `root_path="/demo"` or WebSocket connections will fail
6. **CORS in embedding**: Set `strict_cors=False` when embedding in other sites, or the iframe/web component will be blocked
