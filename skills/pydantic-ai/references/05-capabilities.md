# Capabilities

> Source: [pydantic.dev/docs/ai/core-concepts/capabilities](https://pydantic.dev/docs/ai/core-concepts/capabilities/)

## Table of Contents

- [Overview](#overview)
- [Built-in Capabilities](#built-in-capabilities)
- [Capability Convenience Class](#capability-convenience-class)
- [On-Demand Capabilities](#on-demand-capabilities)
- [Custom Capabilities](#custom-capabilities)
- [Providing Tools](#providing-tools)
- [Providing Instructions](#providing-instructions)
- [Providing Model Settings](#providing-model-settings)
- [Lifecycle Hooks in Capabilities](#lifecycle-hooks-in-capabilities)
- [Composition Patterns](#composition-patterns)
- [Common Pitfalls](#common-pitfalls)

## Overview

Capabilities are reusable, composable units of agent behavior. They bundle tools, hooks, instructions, and model settings into a single component that can be shared across agents. Capabilities are the primary extension point for Pydantic AI.

Instead of scattering tools, hooks, and instructions across separate constructor parameters, package them into a capability:

```python
from pydantic_ai import Agent
from pydantic_ai.capabilities import Capability

refunds = Capability(
    id='refunds',
    description='Use for refund eligibility, status, or processing.',
    instructions='Always confirm the order ID before issuing a refund.',
)

@refunds.tool_plain
def refund_status(order_id: str) -> str:
    """Look up the refund status for an order."""
    return f'Order {order_id}: refund issued.'

agent = Agent('openai:gpt-5.2', capabilities=[refunds])
```

## Built-in Capabilities

| Capability | Purpose |
|-----------|---------|
| `Thinking` | Enables model reasoning at configurable effort levels |
| `WebSearch` | Web search with native or local fallback |
| `WebFetch` | URL fetching with native or local fallback |
| `ImageGeneration` | Image generation with fallback model |
| `MCP` | MCP server integration |
| `ToolSearch` | Discovery of deferred/on-demand tools |
| `Hooks` | Decorator-based hook registration |
| `PrepareTools` | Filter/modify tool definitions per step |
| `PrefixTools` | Namespace tool names with a prefix |

### Thinking Example

```python
from pydantic_ai import Agent
from pydantic_ai.capabilities import Thinking

agent = Agent(
    'anthropic:claude-sonnet-4-6',
    capabilities=[Thinking(effort='high')]
)
```

## Capability Convenience Class

For simple capabilities without subclassing:

```python
from pydantic_ai import RunContext
from pydantic_ai.capabilities import Capability

orders = Capability(
    id='orders',
    description='Use for order tracking or delivery status.',
    instructions='Quote the order ID when discussing an order.',
)

@orders.tool
def order_status(ctx: RunContext[None], order_id: str) -> str:
    """Look up shipping or delivery status."""
    return f'Order {order_id}: shipped'

@orders.tool_plain
def return_policy() -> str:
    """Get the return policy."""
    return '30-day returns on all items.'
```

## On-Demand Capabilities

On-demand capabilities defer loading until the model explicitly requests them via `load_capability`. This reduces token overhead in multi-workflow agents.

```python
refunds = Capability(
    id='refunds',
    description='Use for refund operations.',
    instructions='Confirm order ID before refunding.',
    defer_loading=True,  # Key: deferred until model needs it
)

@refunds.tool_plain
def refund_status(order_id: str) -> str:
    return f'Order {order_id}: refunded.'

agent = Agent(
    'openai-responses:gpt-5.4',
    instructions='You are a customer support assistant.',
    capabilities=[refunds],
)
```

What gets deferred:
- Instructions → returned as tool result on load
- Function tools → exposed on next request after loading
- Model settings → merged after loading
- Lifecycle hooks → fire only after capability loads
- Native tools → exposed after loading

## Custom Capabilities

Subclass `AbstractCapability` for full control:

```python
from dataclasses import dataclass
from pydantic_ai.capabilities import AbstractCapability
from pydantic_ai.toolsets import FunctionToolset

@dataclass
class MathTools(AbstractCapability):
    """Provides basic math operations."""

    def get_toolset(self):
        ts = FunctionToolset()

        @ts.tool_plain
        def add(a: float, b: float) -> float:
            """Add two numbers."""
            return a + b

        @ts.tool_plain
        def multiply(a: float, b: float) -> float:
            """Multiply two numbers."""
            return a * b

        return ts
```

### Available Override Methods

| Method | Returns | Purpose |
|--------|---------|---------|
| `get_toolset()` | `AgentToolset` | Function tools |
| `get_native_tools()` | `list` | Native/provider tools |
| `get_wrapper_toolset()` | `AgentToolset` | Wraps the assembled toolset |
| `get_instructions()` | `str \| callable` | Static or dynamic instructions |
| `get_model_settings()` | `ModelSettings \| callable` | Static or per-step settings |

## Providing Tools

```python
@dataclass
class DatabaseCapability(AbstractCapability):
    connection_string: str

    def get_toolset(self):
        ts = FunctionToolset()

        @ts.tool_plain
        def query_db(sql: str) -> str:
            """Execute a read-only SQL query."""
            return execute(self.connection_string, sql)

        return ts
```

## Providing Instructions

Static or dynamic instructions:

```python
from datetime import datetime
from pydantic_ai import RunContext

@dataclass
class TimeAware(AbstractCapability):

    def get_instructions(self):
        def _get_time(ctx: RunContext) -> str:
            return f'Current time: {datetime.now().isoformat()}'
        return _get_time
```

## Providing Model Settings

Static or dynamic settings:

```python
from pydantic_ai import ModelSettings, RunContext

@dataclass
class ThinkingOnRetry(AbstractCapability):
    def get_model_settings(self):
        def resolve(ctx: RunContext) -> ModelSettings:
            if ctx.run_step > 1:
                return ModelSettings(thinking='high')
            return ModelSettings()
        return resolve
```

## Lifecycle Hooks in Capabilities

Capabilities can implement hooks directly as methods:

```python
from pydantic_ai import ModelRetry

@dataclass
class RunbookRequired(AbstractCapability):

    async def before_tool_execute(self, ctx, *, call, tool_def, args):
        required = self.requirements.get(tool_def.name)
        if required and required not in ctx.loaded_capability_ids:
            raise ModelRetry(
                f'Load capability {required!r} before calling {tool_def.name}.'
            )
        return args
```

## Composition Patterns

### Multi-Workflow Agent

```python
orders = Capability(id='orders', description='Order tracking.', defer_loading=True)
refunds = Capability(id='refunds', description='Refund processing.', defer_loading=True)
account = Capability(id='account', description='Account management.', defer_loading=True)

agent = Agent(
    'openai:gpt-5.2',
    instructions='You are a customer support agent.',
    capabilities=[orders, refunds, account],
)
```

The model sees a catalog of available capabilities and loads only what it needs — dramatically reducing prompt token usage.

### Combining Capabilities

```python
agent = Agent(
    'anthropic:claude-sonnet-4-6',
    capabilities=[
        Thinking(effort='high'),
        MathTools(),
        DatabaseCapability(connection_string='postgresql://...'),
        Hooks(before_model_request=log_request),
    ],
)
```

## Common Pitfalls

- **Missing `id` for on-demand** — `defer_loading=True` requires a stable `id` for the model to reference
- **Tools in deferred capabilities** — tools aren't available until the model calls `load_capability`; ensure instructions guide the model to load first
- **Duplicate tool names** — tools from different capabilities with the same name conflict; use `PrefixTools` for namespacing
- **Hook ordering** — hooks from capabilities fire in the order capabilities are listed in `capabilities=[]`

## Related

- `04-tools.md` — Function tool definitions
- `06-hooks.md` — Lifecycle hooks in detail
- `01-agents.md` — Agent configuration
