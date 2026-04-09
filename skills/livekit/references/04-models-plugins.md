# Models & Plugins

> Source: [docs.livekit.io/agents/models](https://docs.livekit.io/agents/models/) — Provider integrations and plugin system

## Table of Contents

- [Two Integration Approaches](#two-integration-approaches)
- [LiveKit Inference](#livekit-inference)
- [Plugin System](#plugin-system)
- [STT Providers](#stt-providers)
- [LLM Providers](#llm-providers)
- [TTS Providers](#tts-providers)
- [Realtime Models](#realtime-models)
- [Virtual Avatars](#virtual-avatars)
- [OpenAI API Compatibility](#openai-api-compatibility)
- [Plugin Installation](#plugin-installation)
- [Custom Plugins](#custom-plugins)

---

## Two Integration Approaches

### 1. LiveKit Inference (Managed)
Direct model access through LiveKit Cloud — no API keys needed for supported providers.

### 2. Plugin Ecosystem (Self-managed)
Open-source plugins for each provider. Bring your own API keys.

## LiveKit Inference

Simplest approach — uses inference strings:

```python
from livekit.agents import AgentSession, inference

session = AgentSession(
    stt=inference.STT(model="deepgram/nova-3", language="en"),
    llm=inference.LLM(model="openai/gpt-4.1-mini"),
    tts=inference.TTS(model="cartesia/sonic-3:voice-id"),
)
```

**Shorthand strings:**

```python
session = AgentSession(
    stt="deepgram/nova-3:en",
    llm="openai/gpt-4.1-mini",
    tts="cartesia/sonic-3:voice-id",
)
```

**Available through LiveKit Inference:**
- STT: Deepgram, AssemblyAI
- LLM: OpenAI, Google, Anthropic
- TTS: Cartesia, ElevenLabs

## Plugin System

Each plugin wraps a single provider's API:

```python
from livekit.plugins import openai, cartesia, deepgram, assemblyai

session = AgentSession(
    stt=deepgram.STT(model="nova-3", language="en"),
    llm=openai.responses.LLM(model="gpt-4.1-mini"),
    tts=cartesia.TTS(model="sonic-3", voice="voice-id"),
)
```

Plugins require provider API keys set as environment variables.

## STT Providers

### Deepgram (recommended default)

```python
from livekit.plugins import deepgram

stt = deepgram.STT(
    model="nova-3",
    language="en",
)
# Env: DEEPGRAM_API_KEY
```

Features: Streaming, 30+ languages, speaker diarization, custom vocabulary.

### AssemblyAI

```python
from livekit.plugins import assemblyai

stt = assemblyai.STT(language="en")
# Env: ASSEMBLYAI_API_KEY
```

Features: High accuracy, real-time streaming, content moderation.

## LLM Providers

### OpenAI (recommended default)

```python
from livekit.plugins import openai

# Responses API (newer)
llm = openai.responses.LLM(model="gpt-4.1-mini")

# Chat Completions API
llm = openai.LLM(model="gpt-4.1-mini")
# Env: OPENAI_API_KEY
```

### Google Gemini

```python
from livekit.plugins import google

llm = google.LLM(model="gemini-2.0-flash")
# Env: GOOGLE_API_KEY
```

### Anthropic Claude

```python
from livekit.plugins import anthropic

llm = anthropic.LLM(model="claude-sonnet-4-20250514")
# Env: ANTHROPIC_API_KEY
```

### Groq (ultra-low latency)

```python
from livekit.plugins import openai

llm = openai.LLM(
    model="llama-3.3-70b-versatile",
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ["GROQ_API_KEY"],
)
```

### Cerebras (fast inference)

```python
from livekit.plugins import openai

llm = openai.LLM(
    model="llama-3.3-70b",
    base_url="https://api.cerebras.ai/v1",
    api_key=os.environ["CEREBRAS_API_KEY"],
)
```

## TTS Providers

### Cartesia (recommended default)

```python
from livekit.plugins import cartesia

tts = cartesia.TTS(
    model="sonic-3",
    voice="voice-id-here",  # From Cartesia voice library
)
# Env: CARTESIA_API_KEY
```

Features: Ultra-low latency, streaming, multilingual, voice cloning.

### ElevenLabs

```python
from livekit.plugins import elevenlabs

tts = elevenlabs.TTS(
    model="eleven_turbo_v2",
    voice_id="voice-id-here",
)
# Env: ELEVENLABS_API_KEY
```

Features: Highest quality, 29 languages, voice cloning, emotion control.

### OpenAI TTS

```python
from livekit.plugins import openai

tts = openai.TTS(model="tts-1", voice="alloy")
# Env: OPENAI_API_KEY
```

## Realtime Models

Direct speech-to-speech (skip STT/TTS pipeline):

### OpenAI Realtime API

```python
from livekit.plugins import openai

model = openai.realtime.RealtimeModel(
    model="gpt-4o-realtime-preview",
    voice="alloy",
)
# Env: OPENAI_API_KEY
```

### Gemini Live

```python
from livekit.plugins import google

model = google.live.RealtimeModel(
    model="gemini-2.0-flash",
)
# Env: GOOGLE_API_KEY
```

Realtime models handle the full speech-in/speech-out pipeline in a single API call. Lower latency but less control over individual components.

## Virtual Avatars

Visual representation for voice agents:

```python
# Hedra
from livekit.plugins import hedra
avatar = hedra.Avatar(...)

# Tavus
from livekit.plugins import tavus
avatar = tavus.Avatar(...)
```

## OpenAI API Compatibility

Many providers implement OpenAI's API format. Use the OpenAI plugin with custom endpoints:

```python
from livekit.plugins import openai

# Any OpenAI-compatible provider
llm = openai.LLM(
    model="provider-model-name",
    base_url="https://provider.com/v1",
    api_key="provider-api-key",
)
```

This works with: Groq, Cerebras, Together AI, Anyscale, vLLM, Ollama, and others.

**Ollama (local models):**

```python
llm = openai.LLM(
    model="llama3.2",
    base_url="http://localhost:11434/v1",
    api_key="ollama",  # Ollama doesn't require a real key
)
```

## Plugin Installation

### Python

```bash
# Individual plugins
uv add "livekit-agents[openai]~=1.4"
uv add "livekit-agents[deepgram]~=1.4"
uv add "livekit-agents[cartesia]~=1.4"

# Multiple plugins at once
uv add "livekit-agents[openai,silero,deepgram,cartesia,turn-detector]~=1.4"

# All plugins
uv add "livekit-agents[all]~=1.4"
```

### Node.js

```bash
pnpm add @livekit/agents-plugin-openai@1.x
pnpm add @livekit/agents-plugin-deepgram@1.x
pnpm add @livekit/agents-plugin-cartesia@1.x
```

## Custom Plugins

The plugin framework is extensible. Create plugins for unsupported providers:

```python
from livekit.agents import stt, llm, tts

class MyCustomSTT(stt.STT):
    async def recognize(self, audio_buffer) -> stt.SpeechEvent:
        # Call your custom STT API
        text = await my_api.transcribe(audio_buffer)
        return stt.SpeechEvent(text=text, is_final=True)
```

Contribute plugins to the community via the `livekit-plugins-*` namespace on PyPI.
