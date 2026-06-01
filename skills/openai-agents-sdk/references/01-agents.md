# Agents — Configuration & Lifecycle

> Source: [openai.github.io/openai-agents-python/agents](https://openai.github.io/openai-agents-python/agents/)

## Table of Contents

- [Agent Class Parameters](#agent-class-parameters)
- [Basic Agent](#basic-agent)
- [Dynamic Instructions](#dynamic-instructions)
- [Structured Output](#structured-output)
- [Prompt Templates](#prompt-templates)
- [Model Settings](#model-settings)
- [Tool Use Behavior](#tool-use-behavior)
- [Lifecycle Hooks](#lifecycle-hooks)
- [Cloning Agents](#cloning-agents)

## Agent Class Parameters

| Parameter | Required | Purpose |
|-----------|----------|---------|
| `name` | Yes | Human-readable identifier |
| `instructions` | No | System prompt — static string or dynamic function |
| `prompt` | No | OpenAI Responses API prompt template reference |
| `handoff_description` | No | Description shown when this agent is a handoff target |
| `handoffs` | No | List of agents this agent can delegate to |
| `model` | No | Model name string or Model instance |
| `model_settings` | No | `ModelSettings` — temperature, top_p, tool_choice, etc. |
| `tools` | No | List of tools available to this agent |
| `mcp_servers` | No | MCP server instances for external tools |
| `input_guardrails` | No | Validations on user input |
| `output_guardrails` | No | Validations on agent output |
| `output_type` | No | Pydantic model or dataclass for structured output |
| `hooks` | No | `AgentHooks` instance for lifecycle callbacks |
| `tool_use_behavior` | No | Controls how tool results are handled |
| `reset_tool_choice` | No | Auto-reset tool_choice after tool calls (default: `True`) |

## Basic Agent

```python
from agents import Agent, ModelSettings, function_tool

@function_tool
def get_weather(city: str) -> str:
    """Returns weather info for the specified city."""
    return f"The weather in {city} is sunny"

agent = Agent(
    name="Haiku Agent",
    instructions="Always respond in haiku form",
    model="gpt-5-nano",
    tools=[get_weather],
)
```

## Dynamic Instructions

Instructions can be a static string or a function that receives the run context and agent:

```python
from dataclasses import dataclass
from agents import Agent, RunContextWrapper

@dataclass
class UserContext:
    name: str
    role: str

def dynamic_instructions(
    context: RunContextWrapper[UserContext], agent: Agent[UserContext]
) -> str:
    return (
        f"The user's name is {context.context.name}. "
        f"They are a {context.context.role}. Help them with their questions."
    )

agent = Agent[UserContext](
    name="Triage Agent",
    instructions=dynamic_instructions,
)
```

Both synchronous and asynchronous functions are supported.

## Structured Output

By default agents produce plain text. Use `output_type` with a Pydantic model or dataclass to get structured JSON output:

```python
from pydantic import BaseModel
from agents import Agent, Runner

class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]

agent = Agent(
    name="Calendar Extractor",
    instructions="Extract calendar events from text",
    output_type=CalendarEvent,
)

async def main():
    result = await Runner.run(
        agent,
        "Meeting with Alice and Bob on March 15th to discuss Q2 plans"
    )
    event: CalendarEvent = result.final_output
    print(event.name)          # "Q2 Plans Discussion"
    print(event.participants)  # ["Alice", "Bob"]
```

The `output_type` enables the model's structured outputs feature, ensuring JSON conformance to the schema.

## Prompt Templates

Reference stored OpenAI prompt templates with variables:

```python
agent = Agent(
    name="Prompted Assistant",
    prompt={
        "id": "pmpt_abc123",
        "version": "1",
        "variables": {"style": "haiku"},
    },
)
```

Dynamic prompt generation at runtime:

```python
from agents import Agent, GenerateDynamicPromptData, Runner

async def build_prompt(data: GenerateDynamicPromptData):
    ctx = data.context.context
    return {
        "id": ctx.prompt_id,
        "version": "1",
        "variables": {"style": ctx.style},
    }

agent = Agent(name="Dynamic Prompt Agent", prompt=build_prompt)
```

## Model Settings

Fine-tune LLM behavior with `ModelSettings`:

```python
from agents import Agent, ModelSettings
from openai.types.shared import Reasoning

agent = Agent(
    name="Research Agent",
    model="gpt-5.5",
    model_settings=ModelSettings(
        temperature=0.7,
        top_p=0.9,
        tool_choice="auto",
        parallel_tool_calls=False,
        truncation="auto",
        reasoning=Reasoning(effort="high"),
        verbosity="low",
    ),
)
```

### Forcing Tool Use

Control whether and how the LLM uses tools:

```python
from agents import Agent, ModelSettings

agent = Agent(
    name="Weather Agent",
    tools=[get_weather],
    model_settings=ModelSettings(tool_choice="required"),  # Must use a tool
)

agent2 = Agent(
    name="Specific Tool Agent",
    tools=[get_weather, get_news],
    model_settings=ModelSettings(tool_choice="get_weather"),  # Must use this specific tool
)
```

Valid `tool_choice` values: `"auto"`, `"required"`, `"none"`, or a specific tool name.

The framework automatically resets `tool_choice` to `"auto"` after tool calls to prevent infinite loops (controlled by `reset_tool_choice`).

## Tool Use Behavior

Controls what happens after tools execute:

### Default: `"run_llm_again"`
Tools execute, results are fed back to the LLM for a final response.

### `"stop_on_first_tool"`
First tool's output becomes the final response directly:

```python
agent = Agent(
    name="Lookup Agent",
    tools=[get_weather],
    tool_use_behavior="stop_on_first_tool",
)
```

### `StopAtTools` — Stop at specific tools only

```python
from agents.agent import StopAtTools

agent = Agent(
    name="Mixed Agent",
    tools=[get_weather, sum_numbers],
    tool_use_behavior=StopAtTools(stop_at_tool_names=["get_weather"]),
)
```

### Custom handler function

```python
from agents.agent import ToolsToFinalOutputResult
from agents import RunContextWrapper, FunctionToolResult

def custom_handler(
    context: RunContextWrapper, tool_results: list[FunctionToolResult]
) -> ToolsToFinalOutputResult:
    for result in tool_results:
        if result.output and "sunny" in result.output:
            return ToolsToFinalOutputResult(
                is_final_output=True,
                final_output=f"Weather report: {result.output}",
            )
    return ToolsToFinalOutputResult(is_final_output=False, final_output=None)

agent = Agent(
    name="Custom Agent",
    tools=[get_weather],
    tool_use_behavior=custom_handler,
)
```

## Lifecycle Hooks

### RunHooks — Observe entire Runner.run() invocation

```python
from agents import RunHooks, Runner, Agent

class LoggingHooks(RunHooks):
    async def on_agent_start(self, context, agent):
        print(f"Starting: {agent.name}")

    async def on_llm_end(self, context, agent, response):
        print(f"{agent.name} produced {len(response.output)} items")

    async def on_tool_start(self, context, agent, tool):
        print(f"Calling tool: {tool.name}")

    async def on_tool_end(self, context, agent, tool, result):
        print(f"Tool {tool.name} returned: {result}")

    async def on_handoff(self, context, from_agent, to_agent):
        print(f"Handoff: {from_agent.name} → {to_agent.name}")

    async def on_agent_end(self, context, agent, output):
        print(f"Finished: {agent.name}, usage: {context.usage}")

result = await Runner.run(agent, "Hello", hooks=LoggingHooks())
```

### AgentHooks — Attach to specific agent instances

```python
from agents import AgentHooks, Agent

class MyAgentHooks(AgentHooks):
    async def on_start(self, context, agent):
        print(f"Agent {agent.name} starting")

    async def on_end(self, context, agent, output):
        print(f"Agent {agent.name} done")

agent = Agent(
    name="Tracked Agent",
    instructions="Be helpful.",
    hooks=MyAgentHooks(),
)
```

### Hook Event Types

| Hook | Scope | Fires When |
|------|-------|------------|
| `on_agent_start` / `on_agent_end` | Run/Agent | Agent begins/finishes |
| `on_llm_start` / `on_llm_end` | Run | Before/after model call |
| `on_tool_start` / `on_tool_end` | Run | Before/after tool execution |
| `on_handoff` | Run | Control transfers between agents |

## Cloning Agents

Create agent variants by cloning with overrides:

```python
base_agent = Agent(
    name="Base Agent",
    instructions="Be helpful",
    model="gpt-5.5",
    tools=[get_weather],
)

pirate_agent = base_agent.clone(
    name="Pirate Agent",
    instructions="Talk like a pirate",
)

concise_agent = base_agent.clone(
    name="Concise Agent",
    model_settings=ModelSettings(temperature=0.1),
)
```

All unspecified parameters inherit from the source agent.

## Common Pitfalls

- **Forgetting `output_type` validation**: Structured output requires Pydantic models — plain dicts won't work
- **Infinite tool loops**: If `reset_tool_choice=False` and `tool_choice="required"`, the agent may loop endlessly calling tools
- **Generic context mismatch**: Every agent, tool, and hook in a run must use the same context type `Agent[T]`
- **Instructions vs prompt**: Don't set both `instructions` and `prompt` — they're mutually exclusive system prompt mechanisms

## Related Topics

- **Tools:** `02-tools.md` — Function tools and tool configuration
- **Handoffs:** `04-handoffs.md` — Agent delegation
- **Context:** `07-context.md` — RunContextWrapper and dependency injection
