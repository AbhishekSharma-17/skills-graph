# Media & AI Toolkits

Pre-built toolkits for image generation, audio synthesis, video creation, and AI model integration.

## DALL-E

OpenAI image generation with configurable size, quality, and style.

```bash
uv pip install -U openai
export OPENAI_API_KEY=your_key
```

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.tools.dalle import DalleTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[DalleTools(
        model="dall-e-3",
        size="1024x1024",
        quality="hd",
        style="vivid",
    )],
    show_tool_calls=True,
)
agent.print_response("Generate an image of a futuristic city at sunset")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `str` | `"dall-e-3"` | DALL-E model version |
| `enable_create_image` | `bool` | `True` | Enable image generation |
| `n` | `int` | `1` | Number of images to generate |
| `size` | `str` | `"1024x1024"` | Image size: `256x256`, `512x512`, `1024x1024`, `1792x1024`, `1024x1792` |
| `quality` | `str` | `"standard"` | `"standard"` or `"hd"` |
| `style` | `str` | `"vivid"` | `"vivid"` or `"natural"` |

**Functions:** `generate_image`

---

## ElevenLabs

Text-to-speech with voice cloning and audio generation.

```bash
uv pip install -U elevenlabs
export ELEVEN_API_KEY=your_key
```

```python
from agno.tools.elevenlabs import ElevenLabsTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[ElevenLabsTools()],
)
agent.print_response("Convert this text to speech: Hello, welcome to Agno!")
```

---

## Replicate

Run open-source AI models for image/video generation.

```bash
uv pip install -U replicate
export REPLICATE_API_TOKEN=your_token
```

```python
from agno.tools.replicate import ReplicateTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[ReplicateTools(model="minimax/video-01")],
)
agent.print_response("Generate a short video of ocean waves")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | `str` | env var | Replicate API token |
| `model` | `str` | `"minimax/video-01"` | Model to use |
| `enable_generate_media` | `bool` | `True` | Enable media generation |

**Functions:** `generate_media`

---

## Fal

Fast inference for generative AI models (image, video, audio).

```bash
uv pip install -U fal-client
export FAL_KEY=your_key
```

```python
from agno.tools.fal import FalTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[FalTools()],
)
agent.print_response("Generate an image of a mountain landscape")
```

---

## Other Media & AI Toolkits

| Toolkit | Import | Install | Description |
|---------|--------|---------|-------------|
| Giphy | `from agno.tools.giphy import GiphyTools` | — | GIF search |
| Cartesia | `from agno.tools.cartesia import CartesiaTools` | `uv pip install cartesia` | Audio generation |
| ModelsLabs | `from agno.tools.modelslabs import ModelsLabsTools` | — | AI model hosting |
| Lumalabs | `from agno.tools.lumalabs import LumalabsTools` | `uv pip install lumaai` | Video generation |
| Desi Vocal | `from agno.tools.desi_vocal import DesiVocalTools` | — | Multilingual TTS |
| OpenCV | `from agno.tools.opencv import OpenCVTools` | `uv pip install opencv-python` | Computer vision |
| MLX Transcribe | `from agno.tools.mlx_transcribe import MLXTranscribeTools` | — | Audio transcription (Apple Silicon) |
| Stability AI | `from agno.tools.stability import StabilityTools` | — | Image generation |
| Nano Banana | `from agno.tools.nano_banana import NanoBananaTools` | — | Fast inference |
