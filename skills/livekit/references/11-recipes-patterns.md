# Recipes & Patterns

> Source: [docs.livekit.io/reference/recipes](https://docs.livekit.io/reference/recipes/) — Common patterns and examples

## Table of Contents

- [Voice Patterns](#voice-patterns)
- [LLM Patterns](#llm-patterns)
- [Telephony Patterns](#telephony-patterns)
- [Advanced Patterns](#advanced-patterns)
- [Integration Patterns](#integration-patterns)

---

## Voice Patterns

### Push-to-Talk

Disable continuous listening; only process audio when user presses a button:

```python
from livekit.agents import AgentSession, room_io

session = AgentSession(
    stt="deepgram/nova-3:en",
    llm="openai/gpt-4.1-mini",
    tts="cartesia/sonic-3:voice-id",
    # No VAD — audio controlled externally
)

await session.start(
    room=ctx.room,
    agent=Agent(instructions="..."),
    room_options=room_io.RoomOptions(
        audio_input=room_io.AudioInputOptions(
            # Audio toggling controlled by frontend RPC
        ),
    ),
)
```

Frontend toggles audio via `setMicrophoneEnabled(true/false)`.

### Uninterruptible Agent

Prevent users from interrupting the agent during critical messages:

```python
# The agent cannot be interrupted while saying this
await session.say(
    "Your order number is A-B-C-1-2-3. Please write this down.",
    allow_interruptions=False,
)
```

### Multi-language Support

```python
# Detect language and configure STT/TTS accordingly
agent = Agent(
    instructions="""You are a multilingual assistant.
    Detect the user's language and respond in the same language.
    Supported: English, Spanish, French, German, Japanese.""",
)

session = AgentSession(
    stt=inference.STT(model="deepgram/nova-3"),  # Auto-detect language
    llm=inference.LLM(model="openai/gpt-4.1-mini"),
    tts=inference.TTS(model="cartesia/sonic-3:multilingual-voice-id"),
)
```

### Echo Agent (Testing)

Simple agent that repeats what the user says — useful for testing:

```python
@session.on("user_input_transcribed")
async def echo(transcript: str):
    await session.say(f"You said: {transcript}")
```

### Audio Metrics

```python
# Track STT, VAD, and TTS metrics
@session.on("metrics")
def on_metrics(metrics):
    print(f"STT latency: {metrics.stt_latency:.2f}s")
    print(f"LLM TTFT: {metrics.llm_ttft:.2f}s")
    print(f"TTS latency: {metrics.tts_latency:.2f}s")
    print(f"Total response: {metrics.total_latency:.2f}s")
```

## LLM Patterns

### Chain-of-Thought Reasoning

```python
agent = Agent(
    instructions="""You are a technical support agent.
    When diagnosing issues:
    1. Think through the problem step by step
    2. Consider multiple possible causes
    3. Ask clarifying questions before suggesting solutions
    4. Explain your reasoning to the user""",
)
```

### Context Variables

Pass dynamic context to the agent at runtime:

```python
# Inject user-specific context
agent = Agent(
    instructions=f"""You are a support agent for {company_name}.
    The caller is {customer_name} (ID: {customer_id}).
    Their account tier is {account_tier}.
    Recent issues: {recent_tickets}""",
)
```

### Content Filtering

LLM-powered moderation:

```python
@function_tool()
async def check_content(context: RunContext, message: str) -> str:
    """Check if content is appropriate before proceeding."""
    result = await moderation_api.check(message)
    if result.flagged:
        return "I'm sorry, I can't help with that request."
    return "Content is appropriate, proceeding."
```

Simple keyword filtering:

```python
BLOCKED_TOPICS = ["competitor pricing", "internal policies"]

@session.on("user_input_transcribed")
async def filter_input(transcript: str):
    for topic in BLOCKED_TOPICS:
        if topic.lower() in transcript.lower():
            await session.say("I'm not able to discuss that topic.")
            return
```

### Structured Output

```python
from pydantic import BaseModel

class OrderSummary(BaseModel):
    items: list[str]
    total: float
    delivery_date: str

# Use as a Task output type
order_task = Task(
    instructions="Collect the user's order details.",
    output_type=OrderSummary,
)

result: OrderSummary = await session.run_task(order_task)
```

### Metrics Tracking

```python
# Track LLM token usage and latency
@session.on("llm_response_complete")
def track_llm(response):
    print(f"Tokens: {response.usage.total_tokens}")
    print(f"Time to first token: {response.ttft:.2f}s")
```

## Telephony Patterns

### IVR Navigation

Navigate through automated phone menus:

```python
@function_tool()
async def press_key(context: RunContext, digit: str) -> str:
    """Press a key on the phone keypad (DTMF)."""
    await context.session.room.local_participant.publish_dtmf(digit)
    return f"Pressed {digit}"
```

### Survey Execution

```python
from pydantic import BaseModel

class SurveyResponse(BaseModel):
    satisfaction: int  # 1-5
    would_recommend: bool
    feedback: str

survey_task = Task(
    instructions="""Conduct a brief satisfaction survey:
    1. Ask how satisfied they are on a scale of 1-5
    2. Ask if they would recommend us to a friend
    3. Ask for any additional feedback
    Be conversational and thank them after each answer.""",
    output_type=SurveyResponse,
)
```

### Warm Transfer

```python
@function_tool()
async def warm_transfer(context: RunContext, agent_name: str, summary: str) -> str:
    """Transfer the caller to a human agent with context."""
    # 1. Brief the human agent
    await notify_human_agent(agent_name, summary)

    # 2. Put caller on hold
    await context.session.say("I'm connecting you with a specialist. One moment please.")

    # 3. Wait for human to join
    # (Human agent joins the same LiveKit room)

    return f"Connected with {agent_name}"
```

### Outbound Call Campaign

```python
async def make_outbound_call(phone_number: str, room_name: str):
    lk_api = api.LiveKitAPI()

    # Create room
    await lk_api.room.create_room(
        api.CreateRoomRequest(name=room_name, empty_timeout=60)
    )

    # Make the call
    await lk_api.sip.create_sip_participant(
        api.CreateSIPParticipantRequest(
            sip_trunk_id=outbound_trunk_id,
            sip_call_to=phone_number,
            room_name=room_name,
            participant_identity="callee",
        )
    )
```

## Advanced Patterns

### RAG (Retrieval-Augmented Generation)

```python
@function_tool()
async def search_knowledge_base(context: RunContext, query: str) -> str:
    """Search the knowledge base for relevant information."""
    results = await vector_db.search(query, top_k=5)
    context_text = "\n".join([r.text for r in results])
    return f"Found relevant information:\n{context_text}"

agent = Agent(
    instructions="""You are a support agent.
    Always search the knowledge base before answering questions.
    Cite your sources when providing information.""",
    tools=[search_knowledge_base],
)
```

### Vision / Video Processing

```python
session = AgentSession(
    stt="deepgram/nova-3:en",
    llm="openai/gpt-4.1-mini",
    tts="cartesia/sonic-3:voice-id",
    vad=silero.VAD.load(),
    video_sampler=VoiceActivityVideoSampler(
        speaking_fps=1.0,   # 1 frame per second while speaking
        silent_fps=0.3,     # 0.3 fps while silent
    ),
)

await session.start(
    room=ctx.room,
    agent=Agent(
        instructions="You can see the user's camera. Describe what you see when asked.",
    ),
    room_options=room_io.RoomOptions(video_input=True),
)
```

### LangChain Integration

```python
from langchain.agents import AgentExecutor
from livekit.agents import function_tool, RunContext

# Wrap a LangChain agent as a LiveKit tool
@function_tool()
async def langchain_agent(context: RunContext, query: str) -> str:
    """Process complex queries using the research agent."""
    result = await langchain_executor.ainvoke({"input": query})
    return result["output"]
```

## Integration Patterns

### RPC + State Management

```python
# Agent maintains state, frontend queries it via RPC
@function_tool()
async def update_ui(context: RunContext, component: str, data: str) -> str:
    """Update a UI component on the user's screen."""
    await context.session.room.local_participant.perform_rpc(
        destination_identity=context.session.linked_participant.identity,
        method="updateUI",
        payload=json.dumps({"component": component, "data": data}),
    )
    return f"Updated {component}"
```

### Webhook Notifications

```python
# Notify external systems on session events
@session.on("close")
async def on_session_close():
    await httpx.post(
        "https://your-api.com/webhooks/session-ended",
        json={
            "room": session.room.name,
            "duration": session.duration,
            "transcript": session.transcript,
        },
    )
```

### Avatar Integration

```python
from livekit.plugins import hedra

session = AgentSession(
    stt="deepgram/nova-3:en",
    llm="openai/gpt-4.1-mini",
    tts="cartesia/sonic-3:voice-id",
    avatar=hedra.Avatar(avatar_id="your-avatar-id"),
)
# Avatar video is published as a track in the room
```
