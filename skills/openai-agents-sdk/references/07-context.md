# Context — Dependency Injection & State Management

> Source: [openai.github.io/openai-agents-python/context](https://openai.github.io/openai-agents-python/context/)

## Overview

The SDK distinguishes between two types of context:

1. **Local context** (`RunContextWrapper`) — data available to your code during tool execution, hooks, and guardrails. Not sent to the LLM.
2. **Agent/LLM context** — information visible to language models through conversation history, instructions, and tool results.

## RunContextWrapper

The primary mechanism for passing application state through the agent run:

```python
from dataclasses import dataclass
from agents import Agent, Runner, RunContextWrapper, function_tool

@dataclass
class AppContext:
    user_id: str
    user_name: str
    is_premium: bool
    db_connection: DatabasePool

    async def fetch_orders(self, limit: int = 10) -> list:
        return await self.db_connection.query(
            "SELECT * FROM orders WHERE user_id = $1 LIMIT $2",
            self.user_id, limit,
        )

@function_tool
async def get_recent_orders(ctx: RunContextWrapper[AppContext], limit: int = 5) -> str:
    """Fetch recent orders for the current user."""
    orders = await ctx.context.fetch_orders(limit)
    return json.dumps(orders)

agent = Agent[AppContext](
    name="Support Agent",
    instructions="Help users with their account.",
    tools=[get_recent_orders],
)

# Pass context when running
ctx = AppContext(
    user_id="u_123",
    user_name="Alice",
    is_premium=True,
    db_connection=db_pool,
)
result = await Runner.run(agent, "Show my recent orders", context=ctx)
```

### Critical Rule

Every agent, tool function, hook, and guardrail in a single run must use the same context type. You can't mix `Agent[UserContext]` with tools expecting `RunContextWrapper[AppContext]`.

## RunContextWrapper Properties

| Property | Type | Description |
|----------|------|-------------|
| `wrapper.context` | Your custom type | Mutable app-defined state and dependencies |
| `wrapper.usage` | `Usage` | Aggregated token usage across the run |
| `wrapper.tool_input` | `Any` | Structured input when executing within `Agent.as_tool()` |
| `wrapper.approve_tool()` | Method | Programmatically approve a tool call |
| `wrapper.reject_tool()` | Method | Programmatically reject a tool call |

## ToolContext

`ToolContext` extends `RunContextWrapper` with tool-specific metadata:

```python
from agents import function_tool, ToolContext

@function_tool
def get_weather(ctx: ToolContext[AppContext], city: str) -> str:
    """Get weather for a city."""
    print(f"Tool: {ctx.tool_name}")
    print(f"Call ID: {ctx.tool_call_id}")
    print(f"Args: {ctx.tool_arguments}")
    print(f"Namespace: {ctx.tool_namespace}")
    print(f"Qualified: {ctx.qualified_tool_name}")
    return f"Sunny in {city}"
```

### ToolContext Properties

| Property | Description |
|----------|-------------|
| `tool_name` | Name of the invoked tool |
| `tool_call_id` | Unique identifier for this call |
| `tool_arguments` | Raw argument string from the model |
| `tool_namespace` | Responses namespace (if applicable) |
| `qualified_tool_name` | Namespace-qualified tool name |

## Context Use Cases

### User Data & Dependencies

```python
@dataclass
class UserContext:
    name: str
    uid: str
    is_pro: bool
    logger: structlog.BoundLogger
    redis: Redis
    http_client: httpx.AsyncClient
```

### Dynamic Instructions from Context

```python
def build_instructions(ctx: RunContextWrapper[UserContext], agent: Agent) -> str:
    tier = "premium" if ctx.context.is_pro else "basic"
    return f"The user {ctx.context.name} is on the {tier} plan. Help accordingly."

agent = Agent[UserContext](
    name="Support",
    instructions=build_instructions,
)
```

### Cross-Tool State Sharing

```python
@dataclass
class WorkflowState:
    results: dict = field(default_factory=dict)

@function_tool
async def step_one(ctx: RunContextWrapper[WorkflowState]) -> str:
    """Execute step one."""
    result = await process_step_one()
    ctx.context.results["step_one"] = result
    return f"Step one complete: {result}"

@function_tool
async def step_two(ctx: RunContextWrapper[WorkflowState]) -> str:
    """Execute step two using step one results."""
    prior = ctx.context.results.get("step_one", "none")
    result = await process_step_two(prior)
    ctx.context.results["step_two"] = result
    return f"Step two complete: {result}"
```

## Agent/LLM Context Strategies

Since `RunContextWrapper` is not sent to the LLM, use these approaches to make data visible to the model:

### 1. Static Instructions
```python
agent = Agent(instructions="You are a billing specialist for Acme Corp.")
```

### 2. Dynamic Instructions
```python
def instructions(ctx: RunContextWrapper[UserCtx], agent: Agent) -> str:
    return f"The user is {ctx.context.name}, account #{ctx.context.id}."
```

### 3. User Input
```python
result = await Runner.run(agent, f"User {name} asks: {question}")
```

### 4. Function Tools (On-Demand)
```python
@function_tool
async def lookup_account(ctx: RunContextWrapper[Ctx], account_id: str) -> str:
    """Look up account details."""
    return json.dumps(await ctx.context.db.get_account(account_id))
```

### 5. Retrieval & Web Search
```python
agent = Agent(tools=[WebSearchTool(), FileSearchTool(vector_store_ids=[...])])
```

## Context with Agents as Tools

When using `Agent.as_tool()`, the nested agent shares the same context:

```python
orchestrator = Agent[AppContext](
    name="Orchestrator",
    tools=[
        sub_agent.as_tool(tool_name="analyze", tool_description="Run analysis"),
    ],
)

# sub_agent's tools can access the same AppContext
result = await Runner.run(orchestrator, "Analyze my data", context=app_ctx)
```

## Usage Tracking via Context

```python
class UsageHooks(RunHooks):
    async def on_agent_end(self, context: RunContextWrapper, agent, output):
        usage = context.usage
        print(f"Total requests: {usage.requests}")
        print(f"Input tokens: {usage.input_tokens}")
        print(f"Output tokens: {usage.output_tokens}")
```

## Common Pitfalls

- **Context is NOT sent to the LLM**: Don't put information in context expecting the model to see it — use instructions or tools instead
- **Type consistency**: All agents and tools in a run must share the same context type `[T]`
- **Mutable state races**: If tools run in parallel (`parallel_tool_calls=True`), be careful with shared mutable state in context
- **Missing context parameter**: If a tool expects `RunContextWrapper` but it's not the first parameter, the SDK won't inject it

## Related Topics

- **Agents:** `01-agents.md` — Agent generic type and dynamic instructions
- **Tools:** `02-tools.md` — Accessing context in function tools
- **Running Agents:** `03-running-agents.md` — Passing context to Runner.run()
