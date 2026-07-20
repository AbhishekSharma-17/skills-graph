# Instructor — Multimodal Extraction

> Source: https://python.useinstructor.com/concepts/multimodal | v1.15.4

## Table of Contents

- [Overview](#overview)
- [Image Extraction](#image-extraction)
- [PDF Extraction](#pdf-extraction)
- [Audio Extraction](#audio-extraction)
- [Loading Methods](#loading-methods)
- [Provider Compatibility](#provider-compatibility)
- [Caching for Anthropic](#caching-for-anthropic)
- [Patterns and Examples](#patterns-and-examples)

## Overview

Instructor provides a unified multimodal API through `Image`, `PDF`, and `Audio` classes. These wrap media content for inclusion in messages, enabling structured data extraction from non-text sources across providers.

```python
from instructor.multimodal import Image, PDF, Audio
```

All classes share the same loading methods: `from_url()`, `from_path()`, `from_base64()`, and `autodetect()`.

## Image Extraction

Extract structured data from images using vision-capable models:

```python
import instructor
from pydantic import BaseModel
from instructor.multimodal import Image

class ProductInfo(BaseModel):
    name: str
    brand: str
    price: float | None = None
    colors: list[str]

client = instructor.from_provider("openai/gpt-4o")

product = client.create(
    response_model=ProductInfo,
    messages=[{
        "role": "user",
        "content": [
            "Extract product details from this image:",
            Image.from_url("https://example.com/product.jpg"),
        ],
    }],
)
```

### From Local File

```python
product = client.create(
    response_model=ProductInfo,
    messages=[{
        "role": "user",
        "content": [
            "Extract product details:",
            Image.from_path("./photos/product.jpg"),
        ],
    }],
)
```

### From Base64

```python
import base64

with open("image.png", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

product = client.create(
    response_model=ProductInfo,
    messages=[{
        "role": "user",
        "content": [
            "Extract product details:",
            Image.from_base64(b64, media_type="image/png"),
        ],
    }],
)
```

### Auto-Detection

```python
# Automatically detects URL vs path vs base64
product = client.create(
    response_model=ProductInfo,
    messages=[{
        "role": "user",
        "content": [
            "Extract product details:",
            Image.autodetect("https://example.com/img.jpg"),
            # Also works with local paths and base64 strings
        ],
    }],
)
```

## PDF Extraction

Extract structured data from PDF documents:

```python
from instructor.multimodal import PDF

class Invoice(BaseModel):
    vendor: str
    invoice_number: str
    date: str
    line_items: list[LineItem]
    subtotal: float
    tax: float
    total: float

class LineItem(BaseModel):
    description: str
    quantity: int
    unit_price: float
    amount: float

invoice = client.create(
    response_model=Invoice,
    messages=[{
        "role": "user",
        "content": [
            "Extract all invoice data from this document:",
            PDF.from_path("./invoices/march-2026.pdf"),
        ],
    }],
)
```

### From URL

```python
invoice = client.create(
    response_model=Invoice,
    messages=[{
        "role": "user",
        "content": [
            "Extract invoice data:",
            PDF.from_url("https://example.com/invoice.pdf"),
        ],
    }],
)
```

## Audio Extraction

Extract structured data from audio files (OpenAI and Google only):

```python
from instructor.multimodal import Audio

class TranscriptSummary(BaseModel):
    speakers: list[str]
    topics: list[str]
    action_items: list[str]
    duration_estimate: str

client = instructor.from_provider("openai/gpt-4o-audio-preview")

summary = client.create(
    response_model=TranscriptSummary,
    messages=[{
        "role": "user",
        "content": [
            "Summarize this meeting recording:",
            Audio.from_path("./recordings/meeting.wav"),
        ],
    }],
)
```

### From URL

```python
summary = client.create(
    response_model=TranscriptSummary,
    messages=[{
        "role": "user",
        "content": [
            "Summarize this audio:",
            Audio.from_url("https://example.com/recording.mp3"),
        ],
    }],
)
```

## Loading Methods

All multimodal classes support these methods:

| Method | Input | Notes |
|--------|-------|-------|
| `from_url(url)` | HTTP/HTTPS URL | Downloads and encodes |
| `from_gs_url(url)` | Google Cloud Storage URL | For GCS buckets |
| `from_path(path)` | Local file path | Reads and base64 encodes |
| `from_base64(data, media_type)` | Base64 string | Direct encoding |
| `autodetect(source)` | Any of the above | Auto-detects format |

## Provider Compatibility

| Media | OpenAI | Anthropic | Google | Mistral | Bedrock |
|-------|--------|-----------|--------|---------|---------|
| Images | Yes | Yes | Yes | Yes | Yes |
| PDFs | Yes | Yes | Yes | Limited* | Yes |
| Audio | Yes | — | Yes | — | — |

\* Mistral does not support `from_path()` or `from_base64()` for PDFs.

## Caching for Anthropic

Use cache-enabled variants to reduce costs when processing the same media repeatedly:

### Image Caching

```python
from instructor.multimodal import ImageWithCacheControl

response = client.create(
    response_model=ProductInfo,
    messages=[{
        "role": "user",
        "content": [
            "Extract product details:",
            ImageWithCacheControl.from_path("large_catalog.jpg"),
        ],
    }],
)

# Monitor cache effectiveness
raw = response._raw_response
print(f"Cache created: {raw.usage.cache_creation_input_tokens}")
print(f"Cache read: {raw.usage.cache_read_input_tokens}")
```

### PDF Caching

```python
from instructor.multimodal import PdfWithCacheControl

# PdfWithCacheControl is the default for Anthropic
response = client.create(
    response_model=Invoice,
    messages=[{
        "role": "user",
        "content": [
            "Extract invoice data:",
            PdfWithCacheControl.from_path("contract.pdf"),
        ],
    }],
)
```

### Google Files API

```python
from instructor.multimodal import PDFWithGenaiFile

# Uses Google's File API for large document handling
response = client.create(
    response_model=Report,
    messages=[{
        "role": "user",
        "content": [
            "Analyze this report:",
            PDFWithGenaiFile.from_path("large_report.pdf"),
        ],
    }],
)
```

## Patterns and Examples

### Multi-Image Comparison

```python
class Comparison(BaseModel):
    similarities: list[str]
    differences: list[str]
    recommendation: str

comparison = client.create(
    response_model=Comparison,
    messages=[{
        "role": "user",
        "content": [
            "Compare these two product images:",
            Image.from_path("product_a.jpg"),
            Image.from_path("product_b.jpg"),
        ],
    }],
)
```

### Document + Text Context

```python
class ContractReview(BaseModel):
    parties: list[str]
    key_terms: list[str]
    risks: list[str]
    compliant: bool

review = client.create(
    response_model=ContractReview,
    messages=[
        {"role": "system", "content": "Review contracts against company policy."},
        {"role": "user", "content": [
            "Review this contract for compliance issues:",
            PDF.from_path("contract.pdf"),
            "Our policy requires: 30-day termination, no auto-renewal.",
        ]},
    ],
)
```

### Batch Image Processing

```python
import asyncio

async def process_images(image_paths: list[str]) -> list[ProductInfo]:
    client = instructor.from_provider("openai/gpt-4o-mini", async_client=True)

    tasks = [
        client.create(
            response_model=ProductInfo,
            messages=[{
                "role": "user",
                "content": [
                    "Extract product info:",
                    Image.from_path(path),
                ],
            }],
        )
        for path in image_paths
    ]
    return await asyncio.gather(*tasks)
```
