# Running Agents — Streaming, Non-Streaming, Options, Response Types

## Non-Streaming (Default)

Returns complete `AgentResponse` after full generation:

```python
response = await agent.run("What is the weather in Amsterdam?")
print(response.text)  # Aggregated text from all TextContent items
print(len(response.messages))  # Number of ChatMessage items
```

### Accessing Response Data
```python
response = await agent.run("Analyze this data")

# Full text
print(response.text)

# Individual messages
for message in response.messages:
    print(f"Role: {message.role}, Text: {message.text}")

# Structured output (if response_format was set)
if response.value:
    print(response.value)  # Pydantic model instance
```

## Streaming

Returns `ResponseStream` — an async iterator of `AgentResponseUpdate` objects:

```python
async for update in agent.run("Tell me a story", stream=True):
    if update.text:
        print(update.text, end="", flush=True)
```

### Three Consumption Patterns

**Pattern 1 — Iterate only (most common):**
```python
response_stream = agent.run("Tell me a story", stream=True)
async for update in response_stream:
    if update.text:
        print(update.text, end="", flush=True)
```

**Pattern 2 — Skip iteration, get final response directly:**
```python
response_stream = agent.run("Tell me a story", stream=True)
final = await response_stream.get_final_response()
print(final.text)
```

**Pattern 3 — Iterate AND get aggregated final response:**
```python
response_stream = agent.run("Tell me a story", stream=True)

# Stream to user in real-time
async for update in response_stream:
    if update.text:
        print(update.text, end="", flush=True)

# Then get the complete aggregated response
final = await response_stream.get_final_response()
print(f"\n\nFull response: {final.text}")
print(f"Messages: {len(final.messages)}")
```

## ResponseStream API

```python
response_stream = agent.run("query", stream=True)

# Async iteration — yields AgentResponseUpdate objects
async for update in response_stream:
    update.text       # str | None — text portion of this update
    update.contents   # list[Content] — content items in this update

# Finalization — returns full AgentResponse
final = await response_stream.get_final_response()
final.text       # str — complete aggregated text
final.messages   # list[Message] — all messages
final.value      # T | None — parsed structured output (if response_format set)
```

## AgentResponseUpdate Fields

Each streaming update contains:

| Field | Type | Description |
|---|---|---|
| `text` | `str \| None` | Text portion of this chunk |
| `contents` | `list[Content]` | Content items (text, data, function calls, etc.) |

## Run Options

Override model behavior per-run:

```python
from agent_framework.openai import OpenAIChatOptions

# Set default options at agent creation
agent = client.as_agent(
    instructions="You are a helpful assistant",
    default_options={
        "temperature": 0.7,
        "max_tokens": 500,
    },
)

# Override per-run
options: OpenAIChatOptions = {
    "temperature": 0.3,
    "max_tokens": 150,
    "model_id": "gpt-4o",
    "presence_penalty": 0.5,
    "frequency_penalty": 0.3,
}

result = await agent.run(
    "Summarize this briefly",
    options=options,
)

# Streaming with options
async for update in agent.run(
    "Tell me a detailed forecast",
    stream=True,
    options={"temperature": 0.7, "top_p": 0.9},
):
    if update.text:
        print(update.text, end="", flush=True)
```

### Available Options

| Option | Type | Description |
|---|---|---|
| `temperature` | `float` | Controls randomness (0.0 = deterministic, 2.0 = max random) |
| `max_tokens` | `int` | Maximum tokens to generate |
| `model_id` | `str` | Override model for this run |
| `top_p` | `float` | Nucleus sampling parameter |
| `presence_penalty` | `float` | Penalize tokens already present |
| `frequency_penalty` | `float` | Penalize frequently used tokens |
| `response_format` | `Type[BaseModel]` | Force structured output (see `03-structured-output.md`) |

## Adding Extra Tools Per-Run

```python
# Agent has default tools
agent = client.as_agent(tools=[get_weather])

# Add extra tools for a specific run
result = await agent.run(
    "Book me a flight and check weather",
    tools=[book_flight],  # Added to default tools for this run only
)
```

## Running with Session

```python
session = agent.create_session()

# Each run in same session shares conversation history
r1 = await agent.run("My name is Alice", session=session)
r2 = await agent.run("What's my name?", session=session)

# Streaming with session
async for chunk in agent.run("Tell me more", stream=True, session=session):
    if chunk.text:
        print(chunk.text, end="", flush=True)
```

## Running with Middleware

```python
# Run-level middleware (applies to this run only)
result = await agent.run(
    "What's the weather?",
    middleware=[logging_middleware, timing_middleware],
)
```

See `09-middleware.md` for middleware details.

## Error Handling

```python
try:
    result = await agent.run("query")
except Exception as e:
    print(f"Agent error: {e}")
    # Common: InvalidAuthenticationTokenError, RateLimitError,
    # ResourceNotFoundError, ToolNotFoundError
```

## When to Use Streaming vs Non-Streaming

| Scenario | Use |
|---|---|
| User-facing chat UI | **Streaming** — better perceived latency |
| Backend pipeline / batch | **Non-streaming** — simpler code |
| Need token-by-token display | **Streaming** |
| Need complete response for processing | **Non-streaming** or stream + `get_final_response()` |
| Structured output parsing | Either — both support `response_format` |
