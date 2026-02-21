# Agno Multimodal System

Agno agents can process and generate images, audio, video, and files. All media is passed via the `agno.media` classes.

## Media Classes

```python
from agno.media import Image, Audio, Video, File
```

### Image Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | `Optional[str]` | `None` | URL of the image |
| `filepath` | `Optional[str]` | `None` | Local file path to the image |
| `content` | `Optional[bytes]` | `None` | Raw image bytes |
| `format` | `str` | `"png"` | Image format (png, jpg, webp, etc.) |

### Audio Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | `Optional[str]` | `None` | URL of the audio file |
| `filepath` | `Optional[str]` | `None` | Local file path to the audio |
| `content` | `Optional[bytes]` | `None` | Raw audio bytes |
| `format` | `str` | `"wav"` | Audio format (wav, mp3, flac, etc.) |

### Video Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | `Optional[str]` | `None` | URL of the video file |
| `filepath` | `Optional[str]` | `None` | Local file path to the video |
| `content` | `Optional[bytes]` | `None` | Raw video bytes |
| `format` | `str` | `"mp4"` | Video format (mp4, webm, etc.) |

### File Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | `Optional[str]` | `None` | URL of the file |
| `filepath` | `Optional[str]` | `None` | Local file path |
| `content` | `Optional[bytes]` | `None` | Raw file bytes |
| `filename` | `Optional[str]` | `None` | Filename hint for the model |

### Passing Media to Agents

| Class | Pass as |
|-------|---------|
| `Image` | `images=[Image(...)]` |
| `Audio` | `audio=[Audio(...)]` |
| `Video` | `videos=[Video(...)]` |
| `File` | `files=[File(...)]` |

## Quick Start — Image Input

```python
from agno.agent import Agent
from agno.media import Image
from agno.models.openai import OpenAIResponses

agent = Agent(model=OpenAIResponses(id="gpt-5.2"), markdown=True)

agent.print_response(
    "Tell me about this image",
    images=[Image(url="https://upload.wikimedia.org/wikipedia/commons/0/0c/GoldenGateBridge-001.jpg")],
    stream=True,
)
```

## Quick Start — Audio I/O

```python
from agno.agent import Agent
from agno.media import Audio
from agno.models.openai import OpenAIChat
from agno.utils.audio import write_audio_to_file

agent = Agent(
    model=OpenAIChat(
        id="gpt-4o-audio-preview",
        modalities=["text", "audio"],
        audio={"voice": "alloy", "format": "wav"},
    ),
)

response = agent.run(
    "What's in this recording?",
    audio=[Audio(filepath="./question.wav")],
)

if response.response_audio:
    write_audio_to_file(response.response_audio.content, "response.wav")
```

## Quick Start — Video Input (Gemini only)

```python
from agno.agent import Agent
from agno.media import Video
from agno.models.google import Gemini

agent = Agent(model=Gemini(id="gemini-2.0-flash-exp"))
agent.run("Describe what happens in this video", videos=[Video(filepath="./clip.mp4")])
```

## Quick Start — File Input

```python
from agno.agent import Agent
from agno.media import File
from agno.models.anthropic import Claude

agent = Agent(model=Claude(id="claude-sonnet-4-5"))
agent.run("Summarize this document", files=[File(filepath="./report.pdf")])
```

## Response Object

```python
from agno.agent import RunOutput

response: RunOutput = agent.run("prompt", images=[...])

response.content          # Text response
response.images           # List[Image] — generated images
response.response_audio   # Audio — generated audio
```

## Model Compatibility

| Capability | OpenAI | Gemini | Claude |
|------------|--------|--------|--------|
| Image input | GPT-4o, GPT-5.2 | All Gemini models | Claude 3+ |
| Image generation | Via DalleTools | `gemini-2.0-flash-exp-image-generation` | — |
| Audio input | `gpt-4o-audio-preview` | Gemini 3 Flash | — |
| Audio output | `gpt-4o-audio-preview` | — | — |
| Video input | — | Gemini 2.0+ | — |
| File/PDF input | GPT-4o+ | Gemini models | Claude 3+ |

## Sub-References

Read only what the task requires:

| Reference | File | Read When |
|-----------|------|-----------|
| **Images** | `references/multimodal/images.md` | Image input, image generation (DALL-E, Gemini), image analysis, image-to-text |
| **Audio** | `references/multimodal/audio.md` | Audio input/output, transcription, speech generation, voice config, audio utilities |
| **Examples** | `references/multimodal/examples.md` | Complete examples: cross-modal pipelines (image→audio, image→text), video, files, tools+multimodal, teams |
