# Ollama — Vision & Multimodal Models

> Source: [ollama.com/blog/vision-models](https://ollama.com/blog/vision-models) | Version: 0.22.x

## Table of Contents

- [Overview](#overview)
- [Available Vision Models](#available-vision-models)
- [CLI Usage](#cli-usage)
- [API Usage](#api-usage)
- [Python Library Usage](#python-library-usage)
- [OpenAI SDK Usage](#openai-sdk-usage)
- [Image Input Formats](#image-input-formats)
- [Use Cases](#use-cases)
- [Performance Considerations](#performance-considerations)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

Ollama supports multimodal models that can process both text and images. Vision models accept base64-encoded images alongside text prompts and can describe scenes, read text in images, interpret charts, answer visual questions, and extract structured data from images.

All image processing happens locally — no data is sent to external servers.

## Available Vision Models

| Model | Sizes | VRAM | Strengths |
|-------|-------|------|-----------|
| **Gemma 4** | 4B, 12B, 27B | 6–20 GB | Best quality/size ratio in 2026, natively multimodal |
| **Llama 4 Scout** | 17B (active) | ~12 GB | Meta's latest, strong general vision |
| **Qwen2.5-VL** | 3B, 7B, 72B | 4–48 GB | Excellent for documents, charts, tables |
| **LLaVA 1.6** | 7B, 13B, 34B | 5–22 GB | Established, reliable general vision |
| **Gemma 3** | 4B, 12B, 27B | 6–20 GB | Good vision, wide availability |
| **moondream** | 1.8B | ~2 GB | Tiny, edge-device vision |

**Recommendations:**
- **Laptop/edge:** Gemma 4 E4B or moondream (fits in 6–8 GB)
- **General purpose:** Gemma 4 12B or LLaVA 1.6 13B
- **Documents/charts:** Qwen2.5-VL 7B
- **Highest quality:** LLaVA 1.6 34B or Qwen2.5-VL 72B

## CLI Usage

```bash
# Describe an image interactively
ollama run llava
>>> Describe this image: /path/to/image.jpg

# One-shot with file redirect
ollama run gemma4 "What's in this image?" < photo.jpg

# Pipe image content
cat screenshot.png | ollama run llava "Extract the text from this screenshot"
```

## API Usage

Images are sent as base64-encoded strings in the `images` array:

```bash
# Encode image to base64
IMAGE_BASE64=$(base64 -i photo.jpg)

# Using /api/chat
curl http://localhost:11434/api/chat -d '{
  "model": "llava",
  "messages": [{
    "role": "user",
    "content": "Describe this image",
    "images": ["'$IMAGE_BASE64'"]
  }],
  "stream": false
}'

# Using /api/generate
curl http://localhost:11434/api/generate -d '{
  "model": "llava",
  "prompt": "What objects are in this image?",
  "images": ["'$IMAGE_BASE64'"],
  "stream": false
}'
```

## Python Library Usage

```python
from ollama import chat
import base64
from pathlib import Path

image_bytes = Path("photo.jpg").read_bytes()
image_b64 = base64.b64encode(image_bytes).decode("utf-8")

response = chat(
    model="llava",
    messages=[{
        "role": "user",
        "content": "Describe this image in detail. Note any text visible.",
        "images": [image_b64],
    }],
)
print(response.message.content)
```

### Multiple Images

```python
from ollama import chat
import base64
from pathlib import Path

def encode_image(path: str) -> str:
    return base64.b64encode(Path(path).read_bytes()).decode("utf-8")

response = chat(
    model="llava",
    messages=[{
        "role": "user",
        "content": "Compare these two images. What are the differences?",
        "images": [encode_image("before.png"), encode_image("after.png")],
    }],
)
print(response.message.content)
```

### Async Vision

```python
import asyncio
import base64
from pathlib import Path
from ollama import AsyncClient

async def analyze_image(image_path: str, prompt: str) -> str:
    client = AsyncClient()
    image_b64 = base64.b64encode(Path(image_path).read_bytes()).decode()
    response = await client.chat(
        model="gemma4",
        messages=[{
            "role": "user",
            "content": prompt,
            "images": [image_b64],
        }],
    )
    return response.message.content

result = asyncio.run(analyze_image("chart.png", "Extract the data from this chart"))
print(result)
```

## OpenAI SDK Usage

Using the OpenAI compatibility layer with vision:

```python
from openai import OpenAI
import base64
from pathlib import Path

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

image_b64 = base64.b64encode(Path("photo.jpg").read_bytes()).decode()

response = client.chat.completions.create(
    model="llava",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Describe this image"},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
            },
        ],
    }],
)
print(response.choices[0].message.content)
```

## Image Input Formats

| Format | Support | Notes |
|--------|---------|-------|
| JPEG | Yes | Most common, smaller file size |
| PNG | Yes | Lossless, good for screenshots |
| GIF | Yes | First frame only |
| WebP | Yes | Modern format, good compression |
| BMP | Yes | Uncompressed |

**Size limits:**
- Images are resized internally by the model. Most vision models work best with images under 4 megapixels.
- Larger images are automatically downscaled but increase processing time.
- For best results, resize images to 1024x1024 or smaller before sending.

## Use Cases

### OCR / Text Extraction

```python
response = chat(
    model="qwen2.5-vl:7b",
    messages=[{
        "role": "user",
        "content": "Extract all text from this image. Format as plain text.",
        "images": [image_b64],
    }],
)
```

### Chart/Graph Analysis

```python
response = chat(
    model="qwen2.5-vl:7b",
    messages=[{
        "role": "user",
        "content": "Analyze this chart. What are the key trends and data points?",
        "images": [image_b64],
    }],
    format={"type": "object", "properties": {
        "chart_type": {"type": "string"},
        "title": {"type": "string"},
        "data_points": {"type": "array", "items": {"type": "object"}},
        "trends": {"type": "array", "items": {"type": "string"}},
    }},
)
```

### UI Screenshot Analysis

```python
response = chat(
    model="gemma4",
    messages=[{
        "role": "user",
        "content": "Describe the UI layout. List all buttons, menus, and interactive elements.",
        "images": [image_b64],
    }],
)
```

## Performance Considerations

- **First image is slowest** — the vision encoder loads on first use
- **Image size matters** — larger images take more time to process. Resize to the minimum needed resolution
- **VRAM usage** — vision models use more VRAM than text-only models of the same parameter count
- **Batch processing** — process one image per request; concurrent requests via `OLLAMA_NUM_PARALLEL`

## Common Pitfalls

1. **Wrong model** — text-only models ignore the `images` field silently. Verify the model is a vision model with `ollama show <model>`
2. **Image not base64** — the API requires base64-encoded strings, not file paths. Encode before sending
3. **Image too large** — very high-resolution images slow down inference significantly. Pre-resize to 1024px on the longest side
4. **Multiple images unsupported** — some older vision models only support a single image per message. Check model docs
5. **Hallucinated text** — vision models may "read" text that isn't actually in the image. Cross-validate OCR results
