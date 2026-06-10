# Agents

> Source: [pydantic.dev/docs/ai/core-concepts/agent](https://pydantic.dev/docs/ai/core-concepts/agent/)

## Table of Contents

- [Creating Agents](#creating-agents)
- [System Prompts and Instructions](#system-prompts-and-instructions)
- [Running Agents](#running-agents)
- [Model Settings](#model-settings)
- [Conversations and Message History](#conversations-and-message-history)
- [Agent Type Safety](#agent-type-safety)
- [Usage Limits](#usage-limits)
- [Agent Specs](#agent-specs)
- [Debugging](#debugging)
- [Common Pitfalls](#common-pitfalls)

## Creating Agents

An `Agent` encapsulates instructions, tools, structured output, dependencies, and model configuration. Agents are created once and reused — they hold no per-run state.

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-5.2')
```

### Agent Constructor Parameters

| Parameter | Type | Purpose |
|-----------|------|---------|
| `model` | `str \| Model` | Default model (can override per run) |
| `instructions` | `str \| callable` | System-level guidance (excluded from history) |
| `system_prompt` | `str \| callable` | System prompt (preserved in message history) |
| `deps_type` | `type` | Dependency type for RunContext |
| `output_type` | `type \| list` | Structured output schema |
| `tools` | `list[Tool]` | Function tools |
| `capabilities` | `list[Capability]` | Reusable behavior bundles |
| `model_settings` | `ModelSettings \| callable` | Temperature, max_tokens, etc. |
| `end_strategy` | `str` | How to handle parallel tool calls (`early`, `graceful`, `exhaustive`) |
| `max_concurrency` | `int` | Max concurrent tool executions |
| `retries` | `int` | Default retry count for output validation |
| `name` | `str` | Agent name (for observability/logging) |

## System Prompts and Instructions

### Static Instructions

```python
agent = Agent(
    'openai:gpt-5.2',
    instructions="You are a helpful customer support agent. Always be polite."
)
```

### Dynamic Instructions (Callable)

```python
from pydantic_ai import RunContext
from datetime import date

agent = Agent('openai:gpt-5.2', deps_type=str)

@agent.instructions
def dynamic_instructions(ctx: RunContext[str]) -> str:
    return f"The date is {date.today()}. Customer name: {ctx.deps}"
```

### System Prompts vs Instructions

- **`instructions`** — excluded from prior agent context in message history. Use for per-run guidance.
- **`system_prompt`** — preserved as system messages across multiple runs via `message_history`. Use for persistent context.

```python
agent = Agent(
    'openai:gpt-5.2',
    system_prompt="You are a math tutor.",
    instructions="Always show your work step by step."
)
```

### Multiple System Prompts

```python
agent = Agent('openai:gpt-5.2')

@agent.system_prompt
def prompt_one() -> str:
    return "You are a helpful assistant."

@agent.system_prompt
def prompt_two() -> str:
    return f"Today's date: {date.today()}"
```

All system prompt functions are called and concatenated at run time.

## Running Agents

### Five Execution Methods

**1. `run()` — Async execution (preferred in async code)**

```python
result = await agent.run('What is 2 + 2?')
print(result.output)  # "4"
```

**2. `run_sync()` — Synchronous wrapper**

```python
result = agent.run_sync('What is 2 + 2?')
print(result.output)
```

**3. `run_stream()` — Stream text or structured output**

```python
async with agent.run_stream('Tell me a story') as response:
    async for text in response.stream_text():
        print(text, end='', flush=True)
```

**4. `run_stream_events()` — Stream all events (tool calls, model responses)**

```python
async with agent.run_stream_events('Tell me a story') as stream:
    async for event in stream:
        print(event)
```

**5. `iter()` — Node-by-node iteration for custom control flow**

```python
async with agent.iter('Tell me a story') as agent_run:
    async for node in agent_run:
        if Agent.is_model_request_node(node):
            # Custom per-node handling
            pass
```

### Run Result

All run methods return an `AgentRunResult` with:

```python
result = agent.run_sync('Hello')
result.output          # The typed output
result.all_messages()  # Full message history
result.new_messages()  # Messages from this run only
result.usage()         # Token usage stats
```

## Model Settings

Control generation parameters per-agent or per-run.

```python
from pydantic_ai import Agent, ModelSettings

agent = Agent(
    'openai:gpt-5.2',
    model_settings=ModelSettings(temperature=0.0, max_tokens=500)
)

# Override per run
result = agent.run_sync(
    'Explain quantum computing',
    model_settings=ModelSettings(temperature=0.7, max_tokens=2000)
)
```

### Dynamic Model Settings

```python
agent = Agent(
    'openai:gpt-5.2',
    model_settings=lambda ctx: ModelSettings(
        temperature=0.0 if ctx.run_step <= 1 else 0.7
    )
)
```

### Setting Precedence (highest wins)

1. Run-time override (`agent.run(..., model_settings=...)`)
2. Agent-level default (`Agent(..., model_settings=...)`)
3. Model-level default

## Conversations and Message History

### Multi-Turn Conversations

```python
result1 = agent.run_sync('Who was Einstein?')
result2 = agent.run_sync(
    'What was his most famous equation?',
    message_history=result1.new_messages()
)
print(result2.output)  # References Einstein from previous turn
```

### Continuing With Full History

```python
result2 = agent.run_sync(
    'Tell me more',
    message_history=result1.all_messages()
)
```

## Agent Type Safety

Agents are generic in `[DepsType, OutputType]`:

```python
from dataclasses import dataclass
from pydantic import BaseModel

@dataclass
class UserDeps:
    user_id: int

class Report(BaseModel):
    title: str
    summary: str

agent: Agent[UserDeps, Report] = Agent(
    'openai:gpt-5.2',
    deps_type=UserDeps,
    output_type=Report,
)
```

Static type checkers (mypy, pyright) verify that:
- `deps=` matches `UserDeps`
- `result.output` is typed as `Report`
- Tools using `RunContext[UserDeps]` are type-safe

## Usage Limits

Prevent runaway costs or infinite loops:

```python
from pydantic_ai import UsageLimits

result = agent.run_sync(
    'Research this topic thoroughly',
    usage_limits=UsageLimits(
        request_limit=10,              # Max model requests
        response_tokens_limit=5000,    # Max output tokens total
    )
)
```

## Agent Specs

Define agents declaratively in YAML:

```yaml
# agent.yaml
model: anthropic:claude-opus-4-6
instructions: You are a helpful assistant.
capabilities:
  - WebSearch
```

```python
agent = Agent.from_file('agent.yaml')
result = agent.run_sync('What happened today?')
```

## Debugging

### Capture Run Messages

```python
from pydantic_ai import capture_run_messages
from pydantic_ai.exceptions import UnexpectedModelBehavior

with capture_run_messages() as messages:
    try:
        result = agent.run_sync('Do something complex')
    except UnexpectedModelBehavior:
        print(messages)  # Inspect the full message exchange
```

### Logfire Integration

```python
import logfire
logfire.configure()
logfire.instrument_pydantic_ai()

result = agent.run_sync('Hello')
# Full traces visible in Logfire dashboard
```

## Common Pitfalls

- **Instructions vs system_prompt** — use `instructions` for per-run context that shouldn't persist; use `system_prompt` for reusable context that should appear in `message_history`
- **Model override** — pass `model=` to `run()` to override the default model for a specific call
- **Concurrency** — `max_concurrency` limits parallel tool calls, not parallel runs; use `asyncio.gather()` for parallel runs
- **run_sync in async context** — calling `run_sync()` inside an existing event loop raises; use `await agent.run()` instead

## Related

- `02-dependencies.md` — Dependency injection with RunContext
- `03-output.md` — Structured output types
- `04-tools.md` — Function tools
- `07-streaming.md` — Streaming patterns
