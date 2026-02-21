# Audio — Input, Output & Transcription

## Audio Input (Transcription / Analysis)

### OpenAI (gpt-4o-audio-preview)

```python
from agno.agent import Agent
from agno.media import Audio
from agno.models.openai import OpenAIChat

agent = Agent(
    model=OpenAIChat(
        id="gpt-4o-audio-preview",
        modalities=["text"],              # Text-only output (transcription)
    ),
)

# From file
agent.run("What is being said in this audio?", audio=[Audio(filepath="./recording.wav")])

# From bytes
with open("recording.wav", "rb") as f:
    audio_bytes = f.read()
agent.run("Transcribe this audio", audio=[Audio(content=audio_bytes, format="wav")])
```

### Gemini (transcription with speaker ID)

```python
import requests
from agno.agent import Agent
from agno.media import Audio
from agno.models.google import Gemini

agent = Agent(model=Gemini(id="gemini-3-flash-preview"), markdown=True)

url = "https://agno-public.s3.us-east-1.amazonaws.com/demo_data/QA-01.mp3"
response = requests.get(url)

agent.print_response(
    "Give a transcript of this audio conversation. Use speaker A, speaker B to identify speakers.",
    audio=[Audio(content=response.content)],
    stream=True,
)
```

## Audio Output (Speech Generation)

Generate spoken responses using OpenAI's audio modality:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.utils.audio import write_audio_to_file

agent = Agent(
    model=OpenAIChat(
        id="gpt-4o-audio-preview",
        modalities=["text", "audio"],     # Enable audio output
        audio={"voice": "alloy", "format": "wav"},
    ),
)

response = agent.run("Tell me a short story")

if response.response_audio:
    write_audio_to_file(response.response_audio.content, "story.wav")
```

### Voice Options

Available voices for `audio={"voice": "..."}`:
- `alloy` — neutral, balanced
- `echo` — warm, conversational
- `fable` — expressive, narrative
- `onyx` — deep, authoritative
- `nova` — friendly, upbeat
- `sage` — calm, thoughtful
- `shimmer` — clear, bright

### Audio Format Options

`audio={"format": "..."}`
- `wav` — uncompressed, high quality
- `mp3` — compressed
- `flac` — lossless compressed
- `opus` — efficient compressed
- `pcm16` — raw PCM

## Combined Audio I/O

Agent that listens AND speaks:

```python
from agno.agent import Agent
from agno.media import Audio
from agno.models.openai import OpenAIChat
from agno.utils.audio import write_audio_to_file

agent = Agent(
    model=OpenAIChat(
        id="gpt-4o-audio-preview",
        modalities=["text", "audio"],
        audio={"voice": "sage", "format": "wav"},
    ),
    markdown=True,
)

response = agent.run(
    "Respond to this message",
    audio=[Audio(filepath="./question.wav")],
)

if response.response_audio:
    write_audio_to_file(response.response_audio.content, "response.wav")
print(response.content)  # Also get text transcript
```

## Audio Class Reference

```python
from agno.media import Audio

Audio(
    url: str = None,           # Audio URL
    filepath: str = None,      # Local file path
    content: bytes = None,     # Raw audio bytes
    format: str = None,        # Format hint: "wav", "mp3", etc.
)
```

## Audio Utilities

```python
from agno.utils.audio import write_audio_to_file

write_audio_to_file(
    audio=response.response_audio.content,   # bytes
    filename="output.wav",                    # output path
)
```

## Model Configuration Reference

```python
# Transcription only (text output)
OpenAIChat(id="gpt-4o-audio-preview", modalities=["text"])

# Speech generation (text + audio output)
OpenAIChat(
    id="gpt-4o-audio-preview",
    modalities=["text", "audio"],
    audio={"voice": "alloy", "format": "wav"},
)

# Gemini audio input
Gemini(id="gemini-3-flash-preview")
```

## Supported Models

| Capability | Model |
|------------|-------|
| Audio input (transcription) | `gpt-4o-audio-preview`, Gemini 3 Flash |
| Audio output (speech) | `gpt-4o-audio-preview` |
| Audio I/O (both) | `gpt-4o-audio-preview` |
