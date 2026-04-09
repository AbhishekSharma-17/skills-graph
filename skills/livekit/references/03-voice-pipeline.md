# Voice Pipeline

> Source: [docs.livekit.io](https://docs.livekit.io) — STT-LLM-TTS pipeline, turn detection, interruptions

## Table of Contents

- [Pipeline Architecture](#pipeline-architecture)
- [STT (Speech-to-Text)](#stt-speech-to-text)
- [LLM (Language Model)](#llm-language-model)
- [TTS (Text-to-Speech)](#tts-text-to-speech)
- [VAD (Voice Activity Detection)](#vad-voice-activity-detection)
- [Turn Detection](#turn-detection)
- [Interruption Handling](#interruption-handling)
- [Pipeline vs Realtime Models](#pipeline-vs-realtime-models)
- [Performance Optimization](#performance-optimization)
- [Common Pitfalls](#common-pitfalls)

---

## Pipeline Architecture

LiveKit's voice pipeline chains three models in sequence:

```
User Audio → VAD → STT → LLM → TTS → Agent Audio
                    ↓         ↓
              Transcript   Response Text
```

**Flow:**
1. **VAD** detects speech activity in the audio stream
2. **STT** converts speech segments to text
3. **Turn detector** determines when the user has finished speaking
4. **LLM** processes text and generates a response
5. **TTS** converts the response back to audio
6. Audio is streamed back to the user via WebRTC

This is the **cascaded pipeline** — the default for most production deployments. It provides transparency, debuggability, and the flexibility to swap any component.

## STT (Speech-to-Text)

Converts user audio into text transcripts.

```python
from livekit.agents import inference

# Using LiveKit Inference
stt = inference.STT(model="deepgram/nova-3", language="en")

# Using plugins directly
from livekit.plugins import deepgram
stt = deepgram.STT(model="nova-3", language="en")

# AssemblyAI
from livekit.plugins import assemblyai
stt = assemblyai.STT(language="en")
```

**Key STT providers:**
- **Deepgram Nova-3** — Fast, accurate, multilingual (recommended default)
- **AssemblyAI** — High accuracy, speaker diarization
- **Google Cloud Speech** — Wide language support
- **Azure Speech** — Enterprise-grade

**STT considerations:**
- Streaming STT provides partial transcripts for faster turn detection
- Language must be specified for optimal accuracy
- Some models support automatic language detection

## LLM (Language Model)

Processes transcribed text and generates responses.

```python
# Using LiveKit Inference
llm = inference.LLM(model="openai/gpt-4.1-mini")

# Using plugins
from livekit.plugins import openai
llm = openai.responses.LLM(model="gpt-4.1-mini")

# Anthropic
from livekit.plugins import anthropic
llm = anthropic.LLM(model="claude-sonnet-4-20250514")

# Google
from livekit.plugins import google
llm = google.LLM(model="gemini-2.0-flash")
```

**Key LLM providers:**
- **OpenAI** — GPT-4.1, GPT-4.1 mini (recommended default)
- **Anthropic** — Claude Sonnet, Haiku
- **Google** — Gemini 2.0 Flash, Pro
- **Azure OpenAI** — Enterprise GPT models
- **Groq** — Ultra-low latency inference
- **Cerebras** — Fast inference
- **xAI** — Grok models

**OpenAI API compatibility:** Many providers expose OpenAI-compatible endpoints. Override `base_url` and `api_key`:

```python
from livekit.plugins import openai

llm = openai.LLM(
    model="my-model",
    base_url="https://my-provider.com/v1",
    api_key="my-key",
)
```

## TTS (Text-to-Speech)

Converts LLM text responses into audio.

```python
# Using LiveKit Inference
tts = inference.TTS(model="cartesia/sonic-3:voice-id-here")

# Using plugins
from livekit.plugins import cartesia
tts = cartesia.TTS(model="sonic-3", voice="voice-id-here")

# ElevenLabs
from livekit.plugins import elevenlabs
tts = elevenlabs.TTS(model="eleven_turbo_v2", voice_id="voice-id")
```

**Key TTS providers:**
- **Cartesia Sonic-3** — Low latency, natural (recommended default)
- **ElevenLabs** — High quality, voice cloning
- **OpenAI TTS** — Simple, good quality
- **Google Cloud TTS** — Wide language support

**Voice selection:** Each provider has a voice catalog. Voices are referenced by ID or name.

## VAD (Voice Activity Detection)

Detects when the user starts and stops speaking.

```python
from livekit.plugins import silero

vad = silero.VAD.load()  # Silero VAD v5 — the standard choice
```

**Silero VAD** is the de facto standard:
- Runs locally (no API calls)
- Low latency (~30ms)
- Requires model download: `uv run agent.py download-files`

**VAD parameters:**
- `threshold` — Speech detection sensitivity (0.0–1.0)
- `min_speech_duration` — Minimum speech segment length
- `min_silence_duration` — Silence needed to end a speech segment

## Turn Detection

Determines when the user has finished their turn (done speaking).

```python
from livekit.agents.voice import TurnHandlingOptions
from livekit.agents.voice.turn_detector import MultilingualModel

session = AgentSession(
    turn_handling=TurnHandlingOptions(
        turn_detection=MultilingualModel()  # Semantic turn detection
    ),
)
```

**Turn detection modes:**

### 1. Semantic Turn Detection (recommended)
Uses a transformer model to understand when the user's thought is complete — not just when they pause.

```python
TurnHandlingOptions(
    turn_detection=MultilingualModel()  # Downloads model automatically
)
```

Benefits:
- Reduces false interruptions
- Handles mid-sentence pauses naturally
- Works across languages

### 2. VAD-only Turn Detection
Simpler — treats any silence gap as end-of-turn.

```python
TurnHandlingOptions(
    turn_detection=None  # Use VAD silence detection only
)
```

### 3. Manual Turn Detection
Disable automatic detection; control turns programmatically.

## Interruption Handling

When VAD detects speech while the agent is talking:

1. **Interruption event fires**
2. Active TTS playback is cancelled
3. New STT pass begins on the user's speech
4. Agent transitions back to `listening`

**Uninterruptible mode** for important messages:

```python
# Agent speaks without being interruptible
await session.say("Important: Your order has been confirmed.", allow_interruptions=False)
```

## Pipeline vs Realtime Models

| Aspect | Cascaded Pipeline (STT→LLM→TTS) | Realtime Model |
|--------|----------------------------------|----------------|
| Latency | Higher (3 hops) | Lower (direct speech-to-speech) |
| Control | Full (swap any component) | Limited (single model) |
| Debugging | Easy (inspect each stage) | Harder (black box) |
| Cost | Pay per component | Single model cost |
| Flexibility | Any STT + any LLM + any TTS | OpenAI Realtime or Gemini Live |
| Production default | Yes | Emerging |

**Realtime model usage:**

```python
from livekit.plugins import openai

# OpenAI Realtime API (speech-to-speech)
model = openai.realtime.RealtimeModel(model="gpt-4o-realtime-preview")

# Gemini Live
from livekit.plugins import google
model = google.live.RealtimeModel(model="gemini-2.0-flash")
```

## Performance Optimization

1. **Preemptive generation** — Start LLM/TTS before turn detection confirms end-of-turn:
   ```python
   AgentSession(preemptive_generation=True)  # Default: True
   ```

2. **Streaming** — All pipeline stages stream by default (no waiting for full outputs)

3. **Text transforms** — Filter markdown/emoji before TTS to avoid speaking markup:
   ```python
   AgentSession(tts_text_transforms=["filter_markdown", "filter_emoji"])
   ```

4. **Noise cancellation** — Reduce false VAD triggers:
   ```python
   from livekit.agents import noise_cancellation
   room_io.AudioInputOptions(noise_cancellation=noise_cancellation.BVC())
   ```

## Common Pitfalls

1. **No VAD model downloaded** — Run `download-files` before starting
2. **High latency** — Check STT/LLM/TTS individually; Groq or Cerebras for faster LLM
3. **Agent interrupts itself** — Ensure noise cancellation is enabled; echo from speakers triggers VAD
4. **Markdown in speech** — Use `filter_markdown` transform to strip `**bold**`, `#headers`, etc.
5. **Wrong language** — STT language must match user's spoken language for accuracy
6. **Turn detection too aggressive** — Switch from VAD-only to `MultilingualModel()` for semantic detection
