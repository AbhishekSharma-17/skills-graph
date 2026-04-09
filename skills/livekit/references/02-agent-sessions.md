# Agent Sessions

> Source: [docs.livekit.io/agents/logic/sessions](https://docs.livekit.io/agents/logic/sessions/) — AgentSession orchestration

## Table of Contents

- [What is AgentSession](#what-is-agentsession)
- [Creating a Session](#creating-a-session)
- [Configuration Options](#configuration-options)
- [Lifecycle Phases](#lifecycle-phases)
- [Event System](#event-system)
- [RoomIO & Participant Management](#roomio--participant-management)
- [Starting a Session](#starting-a-session)
- [Room Options](#room-options)
- [Agent State Machine](#agent-state-machine)
- [The rtc_session Decorator](#the-rtc_session-decorator)
- [Common Patterns](#common-patterns)

---

## What is AgentSession

`AgentSession` is the main orchestrator for voice AI applications. It handles:

- Collecting user input (audio, video, text)
- Managing the voice pipeline (STT → LLM → TTS)
- Invoking the LLM and processing responses
- Sending output back to the user
- Emitting events for observability and control

## Creating a Session

```python
from livekit.agents import AgentSession, Agent, inference
from livekit.plugins import silero
from livekit.agents.voice import TurnHandlingOptions
from livekit.agents.voice.turn_detector import MultilingualModel

session = AgentSession(
    stt=inference.STT(model="deepgram/nova-3", language="en"),
    llm=inference.LLM(model="openai/gpt-4.1-mini"),
    tts=inference.TTS(model="cartesia/sonic-3:voice-id"),
    vad=silero.VAD.load(),
    turn_handling=TurnHandlingOptions(
        turn_detection=MultilingualModel()
    ),
)
```

You can also use shorthand inference strings:

```python
session = AgentSession(
    stt="deepgram/nova-3:en",
    llm="openai/gpt-4.1-mini",
    tts="cartesia/sonic-3:voice-id",
    vad=silero.VAD.load(),
)
```

## Configuration Options

### AI Models

| Parameter | Type | Description |
|-----------|------|-------------|
| `stt` | `STT \| str` | Speech-to-text model or inference string |
| `llm` | `LLM \| str` | Language model or inference string |
| `tts` | `TTS \| str` | Text-to-speech model or inference string |
| `vad` | `VAD` | Voice Activity Detection (typically Silero) |

### Turn Detection & Interruptions

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `turn_handling` | `TurnHandlingOptions` | — | Controls turn detection and interruption behavior |
| `preemptive_generation` | `bool` | `True` | Start LLM/TTS before turn-end detection |

### Tools & Capabilities

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tools` | `list[FunctionTool]` | `[]` | Tools available to the LLM |
| `mcp_servers` | `list[MCPServer]` | `[]` | MCP servers for external tools |
| `max_tool_steps` | `int` | `3` | Max consecutive tool invocations |

### User Interaction

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `user_away_timeout` | `float` | `15.0` | Seconds of silence before "away" state |
| `min_consecutive_speech_delay` | `float` | `0.0` | Min delay between utterances |
| `ivr_detection` | `IVRDetection` | — | Detect IVR systems on phone calls |

### Text Processing

| Parameter | Type | Description |
|-----------|------|-------------|
| `tts_text_transforms` | `list` | Filters like `filter_markdown`, `filter_emoji` |
| `use_tts_aligned_transcript` | `bool` | Use TTS-aligned transcripts |

### Video

| Parameter | Type | Description |
|-----------|------|-------------|
| `video_sampler` | `VideoSampler` | Frame sampling strategy (default: ~1fps speaking, ~0.3fps silent) |

### Other

| Parameter | Type | Description |
|-----------|------|-------------|
| `userdata` | `Any` | Arbitrary per-session state |

## Lifecycle Phases

```
Initializing → Starting → Running → Closing
```

### 1. Initializing
- Setup phase, no audio/video processing
- Agent state: `initializing`

### 2. Starting
- `start()` called
- I/O connections initialized
- Agent transitions to `listening`

### 3. Running (Active Processing)
- Agent cycles through states: `listening` → `thinking` → `speaking`
- Processes user input, invokes LLM, generates speech

### 4. Closing
- Graceful shutdown
- Drains in-progress speech
- Commits final transcript
- Closes I/O connections

## Event System

```python
@session.on("agent_state_changed")
def on_agent_state(state: str):
    print(f"Agent is now: {state}")  # listening, thinking, speaking

@session.on("user_state_changed")
def on_user_state(state: str):
    print(f"User is now: {state}")

@session.on("user_input_transcribed")
def on_user_input(transcript: str):
    print(f"User said: {transcript}")

@session.on("conversation_item_added")
def on_item(item):
    print(f"New conversation item: {item}")

@session.on("close")
def on_close():
    print("Session closed")
```

| Event | Payload | When |
|-------|---------|------|
| `agent_state_changed` | State string | `listening` → `thinking` → `speaking` |
| `user_state_changed` | State string | User activity changes |
| `user_input_transcribed` | Transcript text | User speech converted to text |
| `conversation_item_added` | Conversation item | Message added to history |
| `close` | — | Session ends (graceful or error) |

## RoomIO & Participant Management

### Linked Participant

Each session links to one participant (the user it interacts with). By default, this is the first participant who joins.

```python
from livekit.agents import room_io

# Specify participant explicitly
options = room_io.RoomOptions(
    participant_identity="user-123"
)

# Or set dynamically
room_io_instance = room_io.RoomIO(session)
room_io_instance.set_participant(participant)
```

### Auto-close Behavior

```python
room_io.RoomOptions(
    close_on_disconnect=True,   # Close when linked participant leaves
    delete_room_on_close=False, # Don't delete room when session ends
)
```

## Starting a Session

```python
from livekit.agents import room_io, noise_cancellation

await session.start(
    room=ctx.room,
    agent=Agent(
        instructions="You are a helpful customer support agent.",
    ),
    room_options=room_io.RoomOptions(
        audio_input=room_io.AudioInputOptions(
            noise_cancellation=noise_cancellation.BVC()
        ),
        video_input=True,
        text_input=True,
        text_output=True,
        participant_kinds=["STANDARD", "SIP"],
    ),
)
```

## Room Options

### Input Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `text_input` | `bool` | `True` | Accept text messages |
| `audio_input` | `AudioInputOptions` | enabled | Accept audio |
| `video_input` | `bool` | `False` | Accept video frames |

### Output Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `text_output` | `bool` | `True` | Send text responses |
| `audio_output` | `bool` | `True` | Send audio responses |
| `transcription_options` | `TranscriptionOptions` | — | Customize transcripts |

## Agent State Machine

```
         user speaks          LLM responds         TTS completes
LISTENING ────────► THINKING ────────────► SPEAKING ────────────► LISTENING
    ▲                                          │
    │              user interrupts             │
    └──────────────────────────────────────────┘
```

## The rtc_session Decorator

The decorator registers a session handler:

```python
from livekit.agents import RtcSession

@RtcSession.on("session")
async def on_session(session: RtcSession):
    # session.room — the LiveKit room
    # session.participant — the linked participant
    agent_session = AgentSession(...)
    await agent_session.start(room=session.room, agent=Agent(...))

if __name__ == "__main__":
    RtcSession.run()
```

**Decorator options:**
- `agent_name` — Name for agent dispatch routing
- `type` — `"per_room"` or `"per_publisher"`
- `on_session_end` — Callback when session completes
- `on_request` — Handler for new dispatch requests

## Common Patterns

### Generate a one-off reply

```python
# Force the agent to speak without user input
await session.generate_reply(instructions="Greet the user warmly")
```

### Say something directly

```python
# Bypass LLM, speak text directly
await session.say("Please hold while I look that up.")
```

### Access conversation history

```python
history = session.conversation
for item in history:
    print(item.role, item.content)
```

### Update agent mid-session

```python
# Switch to a different agent personality
new_agent = Agent(instructions="You are now a technical support specialist.")
await session.update_agent(new_agent)
```
