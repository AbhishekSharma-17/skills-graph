# Gradio — Clients & API

> Source: [gradio.app/docs/python-client](https://gradio.app/docs/python-client) · [gradio.app/docs/js-client](https://gradio.app/docs/js-client)

## Table of Contents

- [Overview](#overview)
- [Auto-Generated API](#auto-generated-api)
- [Python Client](#python-client)
- [JavaScript Client](#javascript-client)
- [API Configuration](#api-configuration)
- [File Handling](#file-handling)
- [Streaming with Clients](#streaming-with-clients)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## Overview

Every Gradio app automatically gets a REST API. Gradio provides official Python and JavaScript clients for programmatic access, plus community clients for Rust, Go, and Ruby.

## Auto-Generated API

### View API Page

Every Gradio app has an API documentation page at `/gradio_api/docs` (or click "Use via API" at the bottom of the UI).

The page shows:
- All available endpoints
- Input/output types
- Code snippets for Python and JavaScript clients
- Example payloads

### API Endpoint Structure

```
POST /gradio_api/call/{endpoint_name}
  → Returns: {"event_id": "..."}

GET /gradio_api/call/{endpoint_name}/{event_id}
  → Returns: Server-Sent Events stream with results
```

## Python Client

### Installation

```bash
pip install gradio-client
```

### Basic Usage

```python
from gradio_client import Client

# Connect to a running Gradio app
client = Client("http://localhost:7860")

# Or connect to a Hugging Face Space
client = Client("abidlabs/whisper")

# Call an endpoint (blocking)
result = client.predict("Hello, how are you?", api_name="/chat")
print(result)
```

### Discovering Endpoints

```python
client = Client("http://localhost:7860")
client.view_api()
# Prints all available endpoints with parameters and types
```

### predict() — Blocking Call

```python
# Single input
result = client.predict("Hello!", api_name="/predict")

# Multiple inputs
result = client.predict(
    "input text",           # param 0
    0.7,                    # param 1 (temperature)
    api_name="/generate",
)
```

### submit() — Non-Blocking Call

```python
job = client.submit("Hello!", api_name="/predict")

# Check status
print(job.status())

# Get result (blocks until done)
result = job.result()

# Cancel
job.cancel()
```

### Streaming Results

```python
job = client.submit("Tell me a story", api_name="/chat")

# Iterate over streaming results
for result in job:
    print(result, end="", flush=True)
```

### File Uploads

```python
from gradio_client import handle_file

# Upload a local file
result = client.predict(
    handle_file("path/to/image.jpg"),
    api_name="/classify",
)

# Upload from URL
result = client.predict(
    handle_file("https://example.com/image.jpg"),
    api_name="/classify",
)
```

### Authentication

```python
# Username/password auth
client = Client("http://localhost:7860", auth=("user", "password"))

# HF token auth
client = Client("private/space", hf_token="hf_...")
```

### Async Client

```python
import asyncio
from gradio_client import Client

async def main():
    client = Client("http://localhost:7860")
    job = client.submit("Hello!", api_name="/predict")
    result = await asyncio.to_thread(job.result)
    print(result)

asyncio.run(main())
```

## JavaScript Client

### Installation

```bash
npm install @gradio/client
```

### Browser Usage

```javascript
import { Client } from "@gradio/client";

const app = await Client.connect("http://localhost:7860");

// List endpoints
const api = await app.view_api();
console.log(api);

// Blocking prediction
const result = await app.predict("/predict", {
  text: "Hello!",
  temperature: 0.7,
});
console.log(result.data);
```

### Node.js Usage

```javascript
import { Client } from "@gradio/client";

const app = await Client.connect("abidlabs/whisper");
const result = await app.predict("/predict", {
  audio: await fetch("audio.wav").then(r => r.blob()),
});
console.log(result.data);
```

### Streaming

```javascript
const app = await Client.connect("http://localhost:7860");
const submission = app.submit("/chat", { message: "Hello" });

submission.on("data", (data) => {
  console.log("Received:", data.data);
});

submission.on("status", (status) => {
  console.log("Status:", status.stage);
});
```

### File Uploads (JS)

```javascript
import { Client, handle_file } from "@gradio/client";

const app = await Client.connect("http://localhost:7860");
const result = await app.predict("/classify", {
  image: handle_file("https://example.com/image.jpg"),
});
```

### Authentication (JS)

```javascript
// Password auth
const app = await Client.connect("http://localhost:7860", {
  auth: ["username", "password"],
});

// HF token
const app = await Client.connect("private/space", {
  hf_token: "hf_...",
});
```

## API Configuration

### Endpoint Naming

```python
btn.click(
    fn=predict,
    inputs=inp,
    outputs=out,
    api_name="/predict",  # Custom endpoint name
)
```

### Visibility Control

```python
# Public: shown in API docs, accessible
btn.click(fn=fn, api_name="/predict", api_visibility="public")

# Private: not in docs, but accessible if you know the name
btn.click(fn=fn, api_name="/internal", api_visibility="private")

# Undocumented: hidden from API page
btn.click(fn=fn, api_name="/hidden", api_visibility="undocumented")

# No API endpoint at all
btn.click(fn=fn, api_name=False)
```

### API Description

```python
btn.click(
    fn=predict,
    inputs=inp,
    outputs=out,
    api_name="/predict",
    api_description="Classify an image and return top-5 labels",
)
```

## File Handling

### Python Client File Downloads

```python
result = client.predict(
    handle_file("input.jpg"),
    api_name="/process",
)
# result is a filepath to the downloaded output file
print(result)  # '/tmp/gradio/xxxx/output.png'
```

### Upload Directory

```python
# Client uploads go to a temp directory by default
# Configure on the server:
demo.launch(allowed_paths=["./uploads"])
```

## Streaming with Clients

### Python Streaming

```python
# Generator endpoint streaming
job = client.submit("Write a poem", api_name="/generate")

for partial_result in job:
    print(partial_result)
```

### JavaScript SSE Streaming

```javascript
const submission = app.submit("/generate", { prompt: "Write a poem" });

submission.on("data", ({ data }) => {
  document.getElementById("output").innerText = data[0];
});

submission.on("status", ({ stage, position, queue_size }) => {
  if (stage === "pending") {
    console.log(`Position ${position} of ${queue_size}`);
  }
});

submission.on("error", (error) => {
  console.error("Error:", error);
});
```

### Status Events

| Stage | Description |
|-------|-------------|
| `"pending"` | Waiting in queue |
| `"generating"` | Function is running |
| `"complete"` | Finished successfully |
| `"error"` | Function raised an error |

## Common Patterns

### Pipeline: Chain Multiple Endpoints

```python
client = Client("http://localhost:7860")

# Step 1: Transcribe audio
text = client.predict(handle_file("audio.mp3"), api_name="/transcribe")

# Step 2: Summarize text
summary = client.predict(text, api_name="/summarize")

# Step 3: Translate
translated = client.predict(summary, "es", api_name="/translate")
```

### Batch Processing

```python
import concurrent.futures

client = Client("http://localhost:7860")
images = ["img1.jpg", "img2.jpg", "img3.jpg"]

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    futures = [
        executor.submit(client.predict, handle_file(img), api_name="/classify")
        for img in images
    ]
    results = [f.result() for f in futures]
```

### Health Check via API

```python
from gradio_client import Client

try:
    client = Client("http://localhost:7860")
    client.view_api()
    print("App is healthy")
except Exception as e:
    print(f"App is down: {e}")
```

## Common Pitfalls

1. **Wrong `api_name`**: Endpoint names include the leading `/` — use `/predict` not `predict`
2. **File handling**: Use `handle_file()` for file inputs — don't pass raw file paths as strings
3. **Positional arguments**: `predict()` uses positional args matching the endpoint parameter order — check `view_api()` for the correct order
4. **Streaming vs blocking**: `predict()` blocks until complete; use `submit()` for streaming or non-blocking access
5. **Version mismatch**: Client and server versions should be compatible — update `gradio-client` when you update `gradio`
6. **CORS in browser**: JavaScript client in the browser needs CORS headers — set `strict_cors=False` on the server if accessing from a different origin
