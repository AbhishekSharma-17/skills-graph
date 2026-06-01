# OpenAI Agents SDK — Overview & Setup

> Source: [openai.github.io/openai-agents-python](https://openai.github.io/openai-agents-python/) | Package: `openai-agents` v0.17.x

## What It Is

The OpenAI Agents SDK is a lightweight Python framework for building multi-agent workflows. It provides a small set of composable primitives — **Agents**, **Tools**, **Handoffs**, and **Guardrails** — that map directly to production patterns for LLM-powered applications.

The SDK uses the OpenAI Responses API by default but adds a higher-level runtime around model calls, handling the agent loop, tool execution, handoffs between agents, and guardrail checks automatically.

## When to Use It

- Building conversational agents with tool-calling capabilities
- Multi-agent orchestration where specialists handle different domains
- Applications requiring input/output validation (guardrails)
- Systems needing conversation persistence across turns (sessions)
- Production LLM apps with observability requirements (tracing)
- Workflows mixing multiple model providers or model tiers

## Core Primitives

| Primitive | Purpose |
|-----------|---------|
| **Agent** | LLM configured with instructions, tools, and behavior |
| **Tool** | Function the agent can call (Python functions, hosted, MCP) |
| **Handoff** | Delegation mechanism between agents |
| **Guardrail** | Input/output validation running in parallel with agent |
| **Runner** | Execution engine that drives the agent loop |
| **Session** | Conversation history persistence across runs |
| **Tracing** | Built-in observability for debugging and monitoring |

## Installation

```bash
# Create project
mkdir my_agent_project && cd my_agent_project
python -m venv .venv
source .venv/bin/activate  # macOS/Linux

# Install
pip install openai-agents

# Optional extras
pip install 'openai-agents[voice]'      # Voice/realtime agents
pip install 'openai-agents[litellm]'    # LiteLLM provider support
pip install 'openai-agents[any-llm]'    # Any-LLM adapter
pip install 'openai-agents[redis]'      # Redis session backend

# Set API key
export OPENAI_API_KEY=sk-...
```

## Quickstart — Hello World

```python
import asyncio
from agents import Agent, Runner

agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant. Answer concisely.",
)

async def main():
    result = await Runner.run(agent, "What is the capital of France?")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

## Quickstart — Agent with Tools

```python
from agents import Agent, Runner, function_tool

@function_tool
def get_weather(city: str) -> str:
    """Returns weather info for the specified city."""
    return f"The weather in {city} is sunny, 22°C"

agent = Agent(
    name="Weather Agent",
    instructions="Help users check the weather.",
    tools=[get_weather],
)

async def main():
    result = await Runner.run(agent, "What's the weather in Tokyo?")
    print(result.final_output)
```

## Quickstart — Multi-Agent with Handoffs

```python
from agents import Agent, Runner

history_tutor = Agent(
    name="History Tutor",
    handoff_description="Specialist for historical questions",
    instructions="Answer history questions clearly and concisely.",
)

math_tutor = Agent(
    name="Math Tutor",
    handoff_description="Specialist for math questions",
    instructions="Explain math step by step with worked examples.",
)

triage_agent = Agent(
    name="Triage Agent",
    instructions="Route each question to the right specialist.",
    handoffs=[history_tutor, math_tutor],
)

async def main():
    result = await Runner.run(triage_agent, "What year did WW2 end?")
    print(result.final_output)
```

## Architecture Overview

```
User Input
    │
    ▼
┌─────────────────────────────────────────┐
│  Runner.run()                           │
│  ┌────────────────────────────────────┐ │
│  │ Input Guardrails (parallel check)  │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │ Agent Loop                         │ │
│  │  1. Call LLM with instructions     │ │
│  │  2. Process response:              │ │
│  │     - Final output → return        │ │
│  │     - Tool call → execute, loop    │ │
│  │     - Handoff → switch agent, loop │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │ Output Guardrails (validate)       │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │ Session Persistence (save history) │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │ Tracing (export spans)             │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
    │
    ▼
RunResult (final_output, items, usage)
```

## Agent Loop Behavior

1. The Runner calls the LLM for the current agent
2. It processes the response:
   - **Final output** generated → return the `RunResult`
   - **Handoff** triggered → switch to the new agent, continue loop
   - **Tool calls** made → execute tools, feed results back, continue loop
3. If `max_turns` is exceeded, raises `MaxTurnsExceeded` (disable with `max_turns=None`)

## Key Dependencies

| Package | Purpose |
|---------|---------|
| `openai` | OpenAI API client (Responses API + Chat Completions) |
| `pydantic` | Schema generation, structured outputs, validation |
| `griffe` | Docstring parsing for tool descriptions |
| `mcp` | Model Context Protocol client |

## Project Structure — Recommended

```
my_agent_project/
├── agents/
│   ├── __init__.py
│   ├── triage.py          # Triage/router agent
│   ├── specialists/
│   │   ├── billing.py     # Billing specialist
│   │   └── support.py     # Support specialist
│   └── tools/
│       ├── database.py    # DB query tools
│       └── search.py      # Search tools
├── guardrails/
│   ├── input.py           # Input validation
│   └── output.py          # Output validation
├── sessions/
│   └── config.py          # Session backend setup
├── main.py                # Entry point
└── pyproject.toml
```

## Common Patterns

| Pattern | Use Case | Key Feature |
|---------|----------|-------------|
| Single agent + tools | Simple assistants | `Agent(tools=[...])` |
| Triage + specialists | Customer support | `Agent(handoffs=[...])` |
| Manager + sub-agents | Orchestration | `agent.as_tool(...)` |
| Guardrailed pipeline | Safety-critical apps | `input_guardrails=[...]` |
| Streaming UI | Chat interfaces | `Runner.run_streamed()` |
| Persistent chat | Multi-turn conversations | `session=SQLiteSession(...)` |

## Related Topics

- **Agents:** `01-agents.md` — Agent configuration and lifecycle
- **Tools:** `02-tools.md` — Function tools and hosted tools
- **Running Agents:** `03-running-agents.md` — Runner execution patterns
- **Handoffs:** `04-handoffs.md` — Agent delegation patterns
