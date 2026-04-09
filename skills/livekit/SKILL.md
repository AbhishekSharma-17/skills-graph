---
name: livekit
description: "Build realtime voice, video, and AI agent applications with LiveKit. MANDATORY TRIGGERS: livekit, live kit, voice agent, voice AI, realtime audio, realtime video, WebRTC agent, speech-to-speech, voice pipeline, voice assistant framework. Also trigger when user wants to build voice AI agents, realtime communication apps, telephony integrations, video conferencing, or multimodal AI agents with audio/video. When in doubt about whether to use this skill for realtime media or voice AI tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["livekit", "webrtc", "voice-ai", "realtime", "agents", "stt", "tts", "llm", "telephony", "sip"]
---

# LiveKit — Skill Router

> Build and deploy realtime voice, video, and AI agent applications with WebRTC, STT-LLM-TTS pipelines, telephony, and multi-agent workflows.

**Source:** [livekit.io](https://livekit.io) v1.5.2 | **SDK:** `livekit-agents` (Python) | **License:** Apache 2.0

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Setup** | `references/00-overview.md` | Getting started, installation, what LiveKit is, quickstart, CLI |
| **Core Concepts** | `references/01-core-concepts.md` | Rooms, participants, tracks, access tokens, WebRTC transport |
| **Agent Sessions** | `references/02-agent-sessions.md` | AgentSession, lifecycle, events, RoomIO, voice pipeline config |
| **Voice Pipeline** | `references/03-voice-pipeline.md` | STT-LLM-TTS pipeline, turn detection, interruptions, VAD |
| **Models & Plugins** | `references/04-models-plugins.md` | STT/LLM/TTS providers, plugin system, LiveKit Inference, OpenAI compat |
| **Tools & Function Calling** | `references/05-tools-function-calling.md` | function_tool, provider tools, MCP integration, frontend RPC |
| **Multi-Agent Workflows** | `references/06-multi-agent-workflows.md` | Agent handoffs, tasks, task groups, workflow patterns |
| **Frontend SDKs** | `references/07-frontend-sdks.md` | React components, JavaScript SDK, Swift, Android, Flutter |
| **Telephony & SIP** | `references/08-telephony-sip.md` | SIP trunking, phone numbers, inbound/outbound calls, DTMF |
| **Room Service API** | `references/09-room-service-api.md` | Server-side API, Twirp, room/participant/track management |
| **Deployment & Observability** | `references/10-deployment-observability.md` | Cloud deploy, self-hosted, Docker, scaling, metrics, logging |
| **Recipes & Patterns** | `references/11-recipes-patterns.md` | Push-to-talk, content filtering, RAG, translation, IVR |

## Installation

```bash
# Python (recommended)
pip install "livekit-agents[openai,silero,deepgram,cartesia,turn-detector]~=1.4"

# Node.js
pnpm add livekit-agents @livekit/agents-plugin-openai

# CLI
brew install livekit-cli
```

## Quick Reference

- **Docs:** https://docs.livekit.io
- **GitHub:** https://github.com/livekit/agents
- **PyPI:** https://pypi.org/project/livekit-agents/
- **Cloud:** https://cloud.livekit.io
