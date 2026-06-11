# Multimodal Inputs

> Source: [docs.vllm.ai](https://docs.vllm.ai/) — v0.22.1

## Table of Contents
- [Overview](#overview)
- [Supported Modalities](#supported-modalities)
- [Offline Inference — Images](#offline-inference--images)
- [Offline Inference — Audio](#offline-inference--audio)
- [Offline Inference — Video](#offline-inference--video)
- [Online Serving — Images](#online-serving--images)
- [Online Serving — Audio](#online-serving--audio)
- [Online Serving — Video](#online-serving--video)
- [Embedding Inputs](#embedding-inputs)
- [Media Caching](#media-caching)
- [Security Configuration](#security-configuration)
- [Common Pitfalls](#common-pitfalls)

## Overview

vLLM supports multimodal models that process text alongside images, audio, video, or pre-computed embeddings. The API follows OpenAI's multimodal Chat Completions format for online serving, and provides a `multi_modal_data` dictionary for offline inference.

## Supported Modalities

| Modality | Offline API | Online API | Example Models |
|----------|:-----------:|:----------:|----------------|
| Images | Yes | Yes | LLaVA, Qwen2-VL, Phi-3-Vision, InternVL |
| Audio | Yes | Yes | Whisper, Qwen2-Audio, Granite Speech |
| Video | Yes | Yes | Qwen2.5-VL, LLaVA-NeXT-Video |
| Embeddings | Yes | Yes | Any multimodal model |

### Popular Multimodal Models

| Model | Modalities | Notes |
|-------|-----------|-------|
| Qwen2.5-VL | Image, Video | Strong vision-language |
| Qwen2-Audio | Audio | Audio understanding |
| LLaVA 1.5/1.6 | Image | Classic vision-language |
| Phi-3-Vision | Image | Microsoft, compact |
| InternVL2 | Image | Open-source, strong |
| Llama 3.2 Vision | Image | Meta's multimodal |
| Whisper | Audio | Speech-to-text |
| Granite Speech | Audio | IBM, with LoRA |

## Offline Inference — Images

### Single Image

```python
from vllm import LLM, SamplingParams
from PIL import Image

llm = LLM(model="llava-hf/llava-1.5-7b-hf")
params = SamplingParams(temperature=0, max_tokens=256)

image = Image.open("photo.jpg")

outputs = llm.generate({
    "prompt": "USER: <image>\nWhat is in this image?\nASSISTANT:",
    "multi_modal_data": {"image": image},
}, params)

print(outputs[0].outputs[0].text)
```

### Multiple Images

```python
image1 = Image.open("cat.jpg")
image2 = Image.open("dog.jpg")

outputs = llm.generate({
    "prompt": "USER: <image><image>\nCompare these two images.\nASSISTANT:",
    "multi_modal_data": {"image": [image1, image2]},
}, params)
```

### RGBA Background Color

Customize transparency handling for PNG images with alpha channels:

```python
llm = LLM(
    model="llava-hf/llava-1.5-7b-hf",
    media_io_kwargs={"image": {"rgba_background_color": [0, 0, 0]}},  # Black bg
)
```

## Offline Inference — Audio

Pass audio as a tuple of `(numpy_array, sample_rate)`:

```python
import numpy as np
import soundfile as sf

audio_data, sample_rate = sf.read("audio.wav")

llm = LLM(model="Qwen/Qwen2-Audio-7B-Instruct")
params = SamplingParams(temperature=0, max_tokens=256)

outputs = llm.generate({
    "prompt": "<audio>\nWhat is being said?\n",
    "multi_modal_data": {"audio": (audio_data, sample_rate)},
}, params)
```

### Long Audio Splitting

For audio files exceeding model limits, use the split utility:

```python
from vllm.multimodal.audio import split_audio

chunks = split_audio(
    audio_data=audio_data,
    sample_rate=sample_rate,
    max_clip_duration_s=30.0,
    overlap_duration_s=1.0,
)
```

Stereo audio is automatically converted to mono for Whisper and Qwen audio models.

## Offline Inference — Video

Pass videos as lists of NumPy arrays or torch tensors:

```python
import numpy as np

# frames: list of NumPy arrays (H, W, C)
frames = [np.array(frame) for frame in video_frames]

outputs = llm.generate({
    "prompt": "<video>\nDescribe this video.\n",
    "multi_modal_data": {"video": frames},
}, params)
```

## Online Serving — Images

### URL-based Images

```python
from openai import OpenAI

client = OpenAI(api_key="EMPTY", base_url="http://localhost:8000/v1")

response = client.chat.completions.create(
    model="llava-hf/llava-1.5-7b-hf",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "What's in this image?"},
            {
                "type": "image_url",
                "image_url": {"url": "https://example.com/photo.jpg"},
            },
        ],
    }],
    max_tokens=256,
)
```

### Base64 Images

```python
import base64

with open("photo.jpg", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

response = client.chat.completions.create(
    model="model-name",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Describe this image."},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
            },
        ],
    }],
)
```

### Local File Images

Requires `--allowed-local-media-path` server flag:

```bash
vllm serve model --allowed-local-media-path /data/images
```

```python
response = client.chat.completions.create(
    model="model-name",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "What's this?"},
            {"type": "image_url", "image_url": {"url": "file:///data/images/photo.jpg"}},
        ],
    }],
)
```

## Online Serving — Audio

### Base64 Audio

```python
import base64

with open("audio.wav", "rb") as f:
    b64_audio = base64.b64encode(f.read()).decode()

response = client.chat.completions.create(
    model="Qwen/Qwen2-Audio-7B-Instruct",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Transcribe this audio."},
            {
                "type": "input_audio",
                "input_audio": {"data": b64_audio, "format": "wav"},
            },
        ],
    }],
)
```

### URL-based Audio

```python
response = client.chat.completions.create(
    model="model-name",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "What is being said?"},
            {"type": "audio_url", "audio_url": {"url": "https://example.com/audio.wav"}},
        ],
    }],
)
```

## Online Serving — Video

```python
response = client.chat.completions.create(
    model="Qwen/Qwen2.5-VL-7B-Instruct",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Describe this video."},
            {"type": "video_url", "video_url": {"url": "https://example.com/video.mp4"}},
        ],
    }],
)
```

### Frame Recovery for Corrupted Videos

```bash
vllm serve model --media-io-kwargs '{"video": {"frame_recovery": true}}'
```

### Client-Side Frame Metadata

Preserve temporal information when sending pre-extracted frames:

```python
response = client.chat.completions.create(
    model="model-name",
    messages=[...],
    extra_body={
        "media_io_kwargs": {
            "video": {
                "fps": 30.0,
                "frames_indices": [0, 10, 20, 30],
                "total_num_frames": 900,
                "duration": 30.0,
            }
        }
    },
)
```

## Embedding Inputs

Pass pre-computed embeddings directly to skip the vision/audio encoder:

### Offline

```python
llm = LLM(model="llava-hf/llava-1.5-7b-hf", enable_mm_embeds=True)

outputs = llm.generate({
    "prompt": "USER: <image>\nDescribe this.\nASSISTANT:",
    "multi_modal_data": {"image": image_embedding_tensor},
})
```

### Online

```python
from vllm.utils.serial_utils import tensor2base64

response = client.chat.completions.create(
    model="model-name",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "What is this?"},
            {"type": "image_embeds", "image_embeds": tensor2base64(embedding)},
        ],
    }],
)
```

Only enable `enable_mm_embeds` for trusted users — malicious embeddings can crash the model.

## Media Caching

Attach stable UUIDs to media for cross-request caching:

```python
# Offline
outputs = llm.generate({
    "prompt": prompt,
    "multi_modal_data": {"image": [img_a, img_b]},
    "multi_modal_uuids": {"image": ["sku-1234-a", None]},
})

# Online — attach uuid to image_url
{
    "type": "image_url",
    "image_url": {"url": "https://..."},
    "uuid": "product-photo-123"
}
```

## Security Configuration

| Setting | Purpose |
|---------|---------|
| `--allowed-media-domains` | Whitelist domains for URL-based media (prevents SSRF) |
| `--allowed-local-media-path` | Allow local file:// paths from specific directories |
| `VLLM_MEDIA_URL_ALLOW_REDIRECTS=0` | Disable URL redirect following |
| `VLLM_IMAGE_FETCH_TIMEOUT=5` | Image fetch timeout (seconds) |
| `VLLM_VIDEO_FETCH_TIMEOUT=30` | Video fetch timeout (seconds) |
| `VLLM_AUDIO_FETCH_TIMEOUT=10` | Audio fetch timeout (seconds) |

## Common Pitfalls

1. **Chat template required** — multimodal models via the Chat API require a chat template; provide `--chat-template` if missing
2. **Placeholder tokens** — each model expects specific placeholder tokens (`<image>`, `<audio>`, etc.) in the prompt; check model documentation
3. **Image count mismatch** — the number of `<image>` placeholders must match the number of images in `multi_modal_data`
4. **SSRF risk** — without `--allowed-media-domains`, the server fetches any URL; restrict in production
5. **Memory with large media** — video and high-res images consume significant GPU memory; adjust `--max-model-len` and `--gpu-memory-utilization`
6. **enable_mm_embeds security** — only enable for trusted clients; arbitrary embeddings can cause undefined behavior
