# LiveKit Overview & Setup

> Source: [docs.livekit.io](https://docs.livekit.io) — LiveKit Agents v1.5.2

## Table of Contents

- [What is LiveKit](#what-is-livekit)
- [Architecture](#architecture)
- [Key Components](#key-components)
- [Installation](#installation)
- [CLI Setup](#cli-setup)
- [Quickstart: Voice AI Agent](#quickstart-voice-ai-agent)
- [Project Structure](#project-structure)
- [Running Modes](#running-modes)
- [LiveKit Cloud vs Self-Hosted](#livekit-cloud-vs-self-hosted)
- [Common Pitfalls](#common-pitfalls)

---

## What is LiveKit

LiveKit is an open-source WebRTC platform for building realtime audio, video, and data applications. It provides:

- **WebRTC SFU (Selective Forwarding Unit)** — Scalable media server written in Go
- **Agents Framework** — Python/Node.js SDK for building AI-powered voice, video, and text agents
- **Client SDKs** — JavaScript, Swift, Android, Flutter, React Native
- **Server SDKs** — Go, Python, Node.js, Ruby, Rust, Kotlin
- **Telephony** — SIP trunking for phone integration
- **LiveKit Cloud** — Managed deployment with inference, observability, and hosting

The Agents framework is the primary focus for AI developers — it lets you build voice assistants, multimodal agents, and conversational AI that join LiveKit rooms as full participants.

## Architecture

```
┌─────────────┐     WebRTC      ┌──────────────┐     HTTP/WS     ┌─────────────┐
│   Frontend   │ ◄────────────► │  LiveKit SFU  │ ◄────────────► │   Backend    │
│ (React, Web) │                │   (Go server) │                │  (Your API)  │
└─────────────┘                └──────────────┘                └─────────────┘
                                       ▲
                                       │ WebRTC
                                       ▼
                               ┌──────────────┐
                               │  Agent Server │
                               │  (Python/JS)  │
                               │               │
                               │ STT → LLM → TTS│
                               └──────────────┘
```

**Two-tier agent system:**

1. **Agent Server** — Long-running process that registers with LiveKit and awaits dispatch
2. **Job** — Subprocess spawned per-room to handle a specific session

WebRTC connects frontends to agents. Agents communicate with your backend via HTTP/WebSockets.

## Key Components

| Component | Purpose |
|-----------|---------|
| `livekit-agents` | Core framework for building agents |
| `livekit-plugins-*` | Provider integrations (OpenAI, Deepgram, Cartesia, etc.) |
| `livekit-client` | JavaScript client SDK |
| `@livekit/components-react` | React UI components |
| `livekit-server-sdk` | Server-side room management |
| `lk` (CLI) | Project scaffolding, deployment, management |

## Installation

### Python Agent (recommended)

```bash
# Using uv (recommended)
uv add "livekit-agents[openai,silero,deepgram,cartesia,turn-detector]~=1.4"

# Using pip
pip install "livekit-agents[openai,silero,deepgram,cartesia,turn-detector]~=1.4"
```

### Node.js Agent

```bash
pnpm add livekit-agents @livekit/agents-plugin-openai
```

### Client SDKs

```bash
# JavaScript/React
npm install livekit-client @livekit/components-react

# Flutter
flutter pub add livekit_client

# Swift — via Swift Package Manager
# github.com/livekit/client-sdk-swift

# Android — via Maven/JitPack
```

### Server SDKs

```bash
# Python
pip install livekit-api

# Node.js
npm install livekit-server-sdk

# Go
go get github.com/livekit/server-sdk-go
```

## CLI Setup

```bash
# Install
brew install livekit-cli          # macOS
curl -sSL https://get.livekit.io/cli | bash  # Linux

# Authenticate with LiveKit Cloud
lk cloud auth

# Initialize a new agent project
lk agent init my-agent --template agent-starter-python

# Install dependencies
cd my-agent && uv sync

# Download model files (VAD, turn detector)
uv run src/agent.py download-files

# Run in dev mode
uv run src/agent.py dev
```

## Quickstart: Voice AI Agent

```python
from livekit.agents import AgentSession, Agent, RtcSession, inference
from livekit.plugins import silero, noise_cancellation

# Define the session handler
@RtcSession.on("session")
async def on_session(session: RtcSession):
    agent_session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3", language="en"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(model="cartesia/sonic-3:voice-id-here"),
        vad=silero.VAD.load(),
    )

    await agent_session.start(
        room=session.room,
        agent=Agent(instructions="You are a helpful voice assistant."),
    )

if __name__ == "__main__":
    RtcSession.run()
```

**Default pipeline:** Deepgram Nova-3 (STT) → GPT-4.1 mini (LLM) → Cartesia Sonic-3 (TTS)

## Project Structure

```
my-agent/
├── src/
│   └── agent.py        # Main agent entry point
├── .env.local           # LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET
├── pyproject.toml       # Dependencies
└── livekit-plugins-*/   # Auto-installed provider plugins
```

## Running Modes

| Mode | Command | Purpose |
|------|---------|---------|
| `console` | `uv run src/agent.py console` | Local terminal testing (Python only) |
| `dev` | `uv run src/agent.py dev` | Development with hot reload |
| `start` | `uv run src/agent.py start` | Production deployment |

## LiveKit Cloud vs Self-Hosted

| Feature | Cloud | Self-Hosted |
|---------|-------|-------------|
| Media server | Managed | Deploy `livekit-server` |
| Agent hosting | Built-in | Your infrastructure |
| Inference (STT/LLM/TTS) | Included | Bring your own API keys |
| Telephony (SIP) | Included | Deploy `livekit-sip` |
| Observability | Built-in dashboard | External tools |
| Scaling | Automatic | Manual / K8s |

## Common Pitfalls

1. **Missing model files** — Run `download-files` before first launch (VAD and turn detector models)
2. **Python version** — Requires Python 3.10+ (3.14 max)
3. **ENV not set** — Ensure `.env.local` has `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`
4. **Port conflicts** — Default dev server on `localhost:7880`
5. **Plugin extras** — Install specific extras: `livekit-agents[openai,deepgram]` not just `livekit-agents`
6. **Network** — WebRTC requires UDP access; falls back to TURN over TCP/TLS on restricted networks
