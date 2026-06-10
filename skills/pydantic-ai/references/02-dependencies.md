# Dependencies

> Source: [pydantic.dev/docs/ai/core-concepts/dependencies](https://pydantic.dev/docs/ai/core-concepts/dependencies/)

## Table of Contents

- [Overview](#overview)
- [Defining Dependencies](#defining-dependencies)
- [RunContext](#runcontext)
- [Using Dependencies in Prompts](#using-dependencies-in-prompts)
- [Using Dependencies in Tools](#using-dependencies-in-tools)
- [Using Dependencies in Validators](#using-dependencies-in-validators)
- [Sync vs Async](#sync-vs-async)
- [Overriding for Tests](#overriding-for-tests)
- [Template Strings](#template-strings)
- [Common Pitfalls](#common-pitfalls)

## Overview

Pydantic AI uses dependency injection to provide data and services to system prompts, tools, and output validators. Dependencies are passed at run time via `deps=` and accessed through `RunContext[T]` — a typed container that gives tools and prompts access to external resources without coupling them to global state.

The pattern mirrors FastAPI's `Depends()` — define a type, declare it on the agent, and the framework threads it through automatically.

## Defining Dependencies

Any Python type can serve as a dependency. Dataclasses are idiomatic for grouping multiple resources:

```python
from dataclasses import dataclass
import httpx

@dataclass
class AppDeps:
    api_key: str
    http_client: httpx.AsyncClient
    db_pool: object  # Your DB connection pool

agent = Agent('openai:gpt-5.2', deps_type=AppDeps)
```

### Simple Dependencies

For single-value deps, use a plain type:

```python
agent = Agent('openai:gpt-5.2', deps_type=str)

result = agent.run_sync('Hello', deps='user-123')
```

### Running With Dependencies

```python
async def main():
    async with httpx.AsyncClient() as client:
        deps = AppDeps(
            api_key='sk-...',
            http_client=client,
            db_pool=my_pool,
        )
        result = await agent.run('Fetch user data', deps=deps)
```

## RunContext

`RunContext[T]` is the typed accessor for dependencies. It's always the first parameter in system prompt functions, tools, and output validators.

```python
from pydantic_ai import RunContext

@agent.tool
async def get_user(ctx: RunContext[AppDeps], user_id: int) -> str:
    """Fetch a user from the API."""
    resp = await ctx.deps.http_client.get(
        f'/users/{user_id}',
        headers={'Authorization': f'Bearer {ctx.deps.api_key}'},
    )
    return resp.text
```

### RunContext Attributes

| Attribute | Type | Purpose |
|-----------|------|---------|
| `ctx.deps` | `T` | The injected dependency instance |
| `ctx.agent` | `Agent` | Reference to the running agent |
| `ctx.run_step` | `int` | Current step number in the agent loop |
| `ctx.retry` | `int` | Current retry count (for tool/output retries) |
| `ctx.partial_output` | `bool` | Whether this is a partial (streaming) validation |
| `ctx.model` | `Model` | The model being used for this run |
| `ctx.usage` | `Usage` | Current token usage |

## Using Dependencies in Prompts

### System Prompt With Dependencies

```python
@agent.system_prompt
async def personalized_prompt(ctx: RunContext[AppDeps]) -> str:
    user_data = await ctx.deps.http_client.get(
        '/me',
        headers={'Authorization': f'Bearer {ctx.deps.api_key}'},
    )
    user_data.raise_for_status()
    return f"You are assisting: {user_data.json()['name']}"
```

### Instructions With Dependencies

```python
@agent.instructions
def custom_instructions(ctx: RunContext[AppDeps]) -> str:
    return f"API environment: {'production' if 'prod' in ctx.deps.api_key else 'staging'}"
```

## Using Dependencies in Tools

```python
@agent.tool
async def search_products(ctx: RunContext[AppDeps], query: str) -> list[dict]:
    """Search the product catalog."""
    resp = await ctx.deps.http_client.get(
        '/products/search',
        params={'q': query},
        headers={'Authorization': f'Bearer {ctx.deps.api_key}'},
    )
    resp.raise_for_status()
    return resp.json()['results']

@agent.tool
async def get_order(ctx: RunContext[AppDeps], order_id: str) -> dict:
    """Look up an order by ID."""
    resp = await ctx.deps.http_client.get(f'/orders/{order_id}')
    return resp.json()
```

### Plain Tools (No Context)

If a tool doesn't need dependencies, use `@agent.tool_plain`:

```python
@agent.tool_plain
def calculate_tax(amount: float, rate: float) -> float:
    """Calculate tax on an amount."""
    return amount * rate
```

## Using Dependencies in Validators

```python
from pydantic_ai import ModelRetry

@agent.output_validator
async def validate_output(ctx: RunContext[AppDeps], output: str) -> str:
    resp = await ctx.deps.http_client.post(
        '/validate',
        json={'text': output},
        headers={'Authorization': f'Bearer {ctx.deps.api_key}'},
    )
    if resp.status_code == 400:
        raise ModelRetry(f'Invalid output: {resp.text}')
    return output
```

## Sync vs Async

System prompts, tools, and validators run in an async context. Non-async functions are executed via `run_in_executor` in a thread pool. Prefer `async` for I/O-bound operations:

```python
# Preferred for I/O
@agent.tool
async def fetch_data(ctx: RunContext[AppDeps], key: str) -> str:
    resp = await ctx.deps.http_client.get(f'/data/{key}')
    return resp.text

# Also works — runs in thread pool
@agent.tool
def compute_result(ctx: RunContext[AppDeps], x: int) -> int:
    return x * 2
```

Whether you call `run()` or `run_sync()` is independent of tool sync/async — the agent always runs in an async context internally.

## Overriding for Tests

`agent.override()` replaces model, deps, or toolsets for testing application code that internally calls agents:

```python
from pydantic_ai.models.test import TestModel

# Production code
async def handle_request(prompt: str) -> str:
    async with httpx.AsyncClient() as client:
        deps = AppDeps(api_key='real-key', http_client=client, db_pool=pool)
        result = await agent.run(prompt, deps=deps)
    return result.output

# Test code
async def test_handle_request():
    mock_deps = AppDeps(api_key='test-key', http_client=mock_client, db_pool=mock_pool)
    with agent.override(model='test', deps=mock_deps):
        output = await handle_request('Test prompt')
    assert 'expected' in output
```

### Override Scope

`agent.override()` is a context manager — the override applies only within the `with` block:

```python
with agent.override(model='test'):
    result1 = agent.run_sync('Hello')   # Uses TestModel

result2 = agent.run_sync('Hello')       # Uses original model
```

## Template Strings

In agent specs (YAML), reference dependency fields via template syntax:

```python
from pydantic_ai import Agent, TemplateStr

agent = Agent(
    'openai:gpt-5.2',
    deps_type=AppDeps,
    instructions=TemplateStr('API key starts with: {{api_key[:4]}}'),
)
```

## Common Pitfalls

- **Missing `deps=` at run time** — if `deps_type` is set, you must pass `deps=` to every `run()` / `run_sync()` call
- **Wrong RunContext type** — `RunContext[AppDeps]` must match the agent's `deps_type=AppDeps`; mypy catches mismatches
- **Mutable deps** — deps are shared across all tools in a single run; don't mutate shared state without synchronization
- **Lifetime management** — the caller manages dependency lifetimes (e.g., closing httpx.AsyncClient); the agent doesn't own them

## Related

- `01-agents.md` — Agent creation and run methods
- `04-tools.md` — Tool definitions that use dependencies
- `11-testing-evals.md` — Testing patterns with overrides
