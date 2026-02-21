# Agno Multimodal Input / Output

## Contents
- [Media Classes](#media-classes)
- [Image Input](#image-input)
- [Audio Input](#audio-input)
- [Audio Output](#audio-output)
- [Video Input (Gemini only)](#video-input-gemini-only)
- [File Input](#file-input)
- [Image Generation](#image-generation)
- [Multimodal Compatibility](#multimodal-compatibility)

---

## Multimodal Input

### Media classes

All imported from `agno.media`:

| Class | Key Parameters | Notes |
|-------|---------------|-------|
| `Image` | `url`, `filepath`, `content` (bytes) | Supported by OpenAI, Anthropic, Gemini, and more |
| `Audio` | `url`, `filepath`, `content` (bytes), `format` | Supported by OpenAI, Gemini |
| `Video` | `url`, `filepath`, `content` (bytes) | Gemini only |
| `File` | `url`, `filepath`, `content` (bytes) | PDF, text files, etc. |

Each accepts one of: `url` (remote), `filepath` (local), or `content` (raw bytes).

### Image input

```python
from agno.media import Image

agent = Agent(model=OpenAIResponses(id="gpt-4o"))

# From URL
agent.run(
    "What's in this image?",
    images=[Image(url="https://example.com/photo.jpg")],
)

# From file
agent.run(
    "Describe this image",
    images=[Image(filepath="./photo.jpg")],
)

# Multiple images
agent.run(
    "Compare these two images",
    images=[
        Image(url="https://example.com/photo1.jpg"),
        Image(url="https://example.com/photo2.jpg"),
    ],
)
```

### Image input → structured output

```python
from agno.media import Image

class ImageAnalysis(BaseModel):
    main_subject: str
    colors: list[str]
    composition: str
    mood: str

agent = Agent(
    model=OpenAIResponses(id="gpt-4o"),
    output_schema=ImageAnalysis,
)

response = agent.run(
    "Analyze this image",
    images=[Image(filepath="./photo.jpg")],
)
analysis: ImageAnalysis = response.content
```

### Audio input

```python
from agno.media import Audio

agent = Agent(
    model=OpenAIResponses(id="gpt-4o-audio-preview", modalities=["text"]),
)

# From file
agent.run(
    "What is being said in this audio?",
    audio=[Audio(filepath="./recording.wav")],
)

# From bytes
with open("recording.wav", "rb") as f:
    audio_bytes = f.read()

agent.run(
    "Transcribe this audio",
    audio=[Audio(content=audio_bytes, format="wav")],
)
```

### Audio output

```python
from agno.utils.audio import write_audio_to_file

agent = Agent(
    model=OpenAIResponses(
        id="gpt-4o-audio-preview",
        modalities=["text", "audio"],
        audio={"voice": "alloy", "format": "wav"},
    ),
)

response = agent.run("Tell me a short story")

if response.response_audio:
    write_audio_to_file(response.response_audio.content, "story.wav")
```

### Combined audio I/O

```python
from agno.media import Audio
from agno.utils.audio import write_audio_to_file

agent = Agent(
    model=OpenAIResponses(
        id="gpt-4o-audio-preview",
        modalities=["text", "audio"],
        audio={"voice": "alloy", "format": "wav"},
    ),
)

response = agent.run(
    "Respond to this message",
    audio=[Audio(filepath="./question.wav")],
)

if response.response_audio:
    write_audio_to_file(response.response_audio.content, "response.wav")
```

### Video input (Gemini only)

```python
from agno.media import Video
from agno.models.google import Gemini

agent = Agent(model=Gemini(id="gemini-2.0-flash-exp"))

agent.run(
    "Describe what happens in this video",
    videos=[Video(filepath="./clip.mp4")],
)
```

### File input

```python
from agno.media import File
from agno.models.anthropic import Claude

agent = Agent(model=Claude(id="claude-sonnet-4-5"))

# PDF from URL
agent.run(
    "Summarize this document",
    files=[File(url="https://example.com/report.pdf")],
)

# Local file
agent.run(
    "What are the key points?",
    files=[File(filepath="./report.pdf")],
)
```

### Image generation

```python
from agno.tools.dalle import DalleTools

agent = Agent(
    model=OpenAIResponses(id="gpt-4o"),
    tools=[DalleTools()],
)

agent.run("Generate an image of a sunset over mountains")
images = agent.get_images()
for img in images:
    print(img.url)
```

---

## Multimodal Compatibility

| Feature | OpenAI | Anthropic | Gemini | Others |
|---------|--------|-----------|--------|--------|
| Image input | Yes | Yes | Yes | Varies |
| Audio input | Yes | — | Yes | Few |
| Audio output | Yes | — | — | Few |
| Video input | — | — | Yes | Limited |
| File upload | Yes | Yes | Yes | Few |
| Structured output | Yes (native) | Yes (native) | Yes (native) | JSON mode fallback |

