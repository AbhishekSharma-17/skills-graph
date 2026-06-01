# Running Agents — Runner, RunConfig & Execution

> Source: [openai.github.io/openai-agents-python/running_agents](https://openai.github.io/openai-agents-python/running_agents/)

## Table of Contents

- [Runner Methods](#runner-methods)
- [RunConfig](#runconfig)
- [Input Management](#input-management)
- [Conversation History](#conversation-history)
- [Error Handling](#error-handling)
- [Usage Tracking](#usage-tracking)
- [Durable Execution](#durable-execution)

## Runner Methods

The `Runner` class provides three execution modes:

| Method | Type | Returns | Use When |
|--------|------|---------|----------|
| `Runner.run()` | Async | `RunResult` | Standard async execution |
| `Runner.run_sync()` | Sync | `RunResult` | Scripts, notebooks, sync code |
| `Runner.run_streamed()` | Async | `RunResultStreaming` | Real-time UI, streaming output |

### Basic Execution

```python
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="Be helpful.")

# Async
result = await Runner.run(agent, "Hello!")
print(result.final_output)

# Sync
result = Runner.run_sync(agent, "Hello!")
print(result.final_output)

# Streamed
result = Runner.run_streamed(agent, "Hello!")
async for event in result.stream_events():
    # Process events
    pass
print(result.final_output)
```

### Input Types

`Runner.run()` accepts input as:

```python
# String — converted to a user message
result = await Runner.run(agent, "What is 2+2?")

# List of items — Responses API format
result = await Runner.run(agent, [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi! How can I help?"},
    {"role": "user", "content": "What's the weather?"},
])

# RunState — resume an interrupted run
state = previous_result.to_state()
result = await Runner.run(agent, state)
```

## RunConfig

Customize per-run behavior across model, guardrails, tracing, and tools:

```python
from agents import RunConfig, ModelSettings

config = RunConfig(
    # Model overrides
    model="gpt-5.5",
    model_settings=ModelSettings(temperature=0.3),

    # Guardrails
    input_guardrails=[my_input_guardrail],
    output_guardrails=[my_output_guardrail],

    # Handoffs
    nest_handoff_history=True,
    handoff_input_filter=my_filter,

    # Tracing
    tracing_disabled=False,
    workflow_name="customer-support",
    trace_id="trace_abc123",
    group_id="session_456",
    trace_include_sensitive_data=False,

    # Tools
    tool_execution_config=ToolExecutionConfig(max_concurrent=5),

    # Session
    session_settings=SessionSettings(limit=50),
)

result = await Runner.run(agent, "Hello", run_config=config)
```

### Key RunConfig Fields

| Field | Purpose |
|-------|---------|
| `model` | Override agent's model for this run |
| `model_provider` | Custom model provider instance |
| `model_settings` | Override temperature, top_p, etc. |
| `input_guardrails` | Additional input guardrails (appended to agent's) |
| `output_guardrails` | Additional output guardrails |
| `nest_handoff_history` | Collapse prior transcript on handoffs |
| `tracing_disabled` | Disable tracing for this run |
| `workflow_name` | Name shown in tracing dashboard |
| `trace_include_sensitive_data` | Include LLM I/O in traces (default: `True`) |
| `call_model_input_filter` | Hook to edit model input before LLM call |
| `tool_error_formatter` | Custom error messages for rejected tool calls |
| `session_settings` | Control history retrieval limits |

### Call Model Input Filter

Edit the prepared input immediately before the LLM call:

```python
from agents import RunConfig, CallModelData, ModelInputData

def trim_history(data: CallModelData) -> ModelInputData:
    trimmed = data.model_data.input[-5:]  # Keep last 5 items
    return ModelInputData(
        input=trimmed,
        instructions=data.model_data.instructions,
    )

result = await Runner.run(
    agent, prompt,
    run_config=RunConfig(call_model_input_filter=trim_history),
)
```

## Input Management

### Manual History (Simple)

Use `result.to_input_list()` to chain conversations:

```python
# Turn 1
result = await Runner.run(agent, "What's the capital of France?")
print(result.final_output)  # "Paris"

# Turn 2 — include prior history
new_input = result.to_input_list() + [
    {"role": "user", "content": "What about Germany?"}
]
result = await Runner.run(agent, new_input)
print(result.final_output)  # "Berlin"
```

### Session-Based Persistence (Recommended)

Sessions handle history automatically:

```python
from agents import SQLiteSession

session = SQLiteSession("user_123", "conversations.db")

# Turn 1 — history saved automatically
result = await Runner.run(agent, "Hello!", session=session)

# Turn 2 — prior context loaded automatically
result = await Runner.run(agent, "What did I just say?", session=session)
```

### Server-Managed State

Use OpenAI's Conversations API:

```python
# Using conversation_id
conversation = await client.conversations.create()
result = await Runner.run(
    agent, "Hello",
    conversation_id=conversation.id,
)

# Using response chaining
previous_id = None
result = await Runner.run(agent, "Hello", previous_response_id=previous_id)
previous_id = result.last_response_id

result = await Runner.run(agent, "Follow up", previous_response_id=previous_id)
```

Session persistence cannot be combined with server-managed conversation settings in the same run.

## Conversation History

### Max Turns

Limit agent loop iterations to prevent runaway execution:

```python
# Default: raises MaxTurnsExceeded
result = await Runner.run(agent, "Complex task", max_turns=10)

# Disable limit entirely
result = await Runner.run(agent, "Open-ended task", max_turns=None)
```

## Error Handling

### Error Handlers Dictionary

Convert exceptions into controlled outputs instead of raising:

```python
from agents import Runner, RunErrorHandlerInput, RunErrorHandlerResult

def handle_max_turns(data: RunErrorHandlerInput) -> RunErrorHandlerResult:
    return RunErrorHandlerResult(
        final_output="I've reached my processing limit. Please simplify your request.",
        include_in_history=False,
    )

def handle_refusal(data: RunErrorHandlerInput) -> RunErrorHandlerResult:
    return RunErrorHandlerResult(
        final_output="I'm unable to help with that request.",
        include_in_history=True,
    )

result = Runner.run_sync(
    agent, "Complex request",
    max_turns=5,
    error_handlers={
        "max_turns": handle_max_turns,
        "model_refusal": handle_refusal,
    },
)
```

### Exception Types

| Exception | Cause |
|-----------|-------|
| `AgentsException` | Base class for all SDK exceptions |
| `MaxTurnsExceeded` | Agent loop exceeded `max_turns` |
| `ModelBehaviorError` | Invalid model output (malformed JSON, unexpected tool failure) |
| `ToolTimeoutError` | Tool execution exceeded timeout |
| `UserError` | Incorrect SDK usage |
| `InputGuardrailTripwireTriggered` | Input guardrail tripped |
| `OutputGuardrailTripwireTriggered` | Output guardrail tripped |

### Exception Handling Pattern

```python
from agents.exceptions import (
    InputGuardrailTripwireTriggered,
    MaxTurnsExceeded,
)

try:
    result = await Runner.run(agent, user_input, max_turns=10)
    print(result.final_output)
except InputGuardrailTripwireTriggered as e:
    print(f"Input rejected: {e.guardrail_result.output.output_info}")
except MaxTurnsExceeded:
    print("Agent exceeded turn limit")
```

## Usage Tracking

The SDK automatically tracks token usage:

```python
result = await Runner.run(agent, "Explain quantum computing")

print(f"Input tokens:  {result.raw_responses[-1].usage.input_tokens}")
print(f"Output tokens: {result.raw_responses[-1].usage.output_tokens}")

# Aggregated usage from context
# Available in hooks via context.usage
```

## Durable Execution

For long-running workflows with failure recovery, the SDK integrates with:

| Platform | Description |
|----------|-------------|
| **Dapr** | CNCF workflow orchestrator |
| **Temporal** | Long-running workflows with human-in-the-loop |
| **Restate** | Lightweight durable agents with approval/handoffs |
| **DBOS** | Progress preservation via SQLite/Postgres |

## Common Pitfalls

- **Mixing session with conversation_id**: Can't use both in the same run
- **Ignoring max_turns**: Without a limit, complex agent chains can run indefinitely
- **Forgetting async**: `Runner.run()` is async — use `Runner.run_sync()` for sync contexts
- **Not consuming the stream**: `run_streamed()` isn't complete until the async iterator finishes — post-processing occurs after visible tokens

## Related Topics

- **Streaming:** `06-streaming.md` — Real-time event streaming
- **Sessions:** `11-sessions.md` — Conversation persistence
- **Context:** `07-context.md` — RunContextWrapper
