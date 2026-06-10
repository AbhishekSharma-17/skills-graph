# Hooks

> Source: [pydantic.dev/docs/ai/core-concepts/hooks](https://pydantic.dev/docs/ai/core-concepts/hooks/)

## Table of Contents

- [Overview](#overview)
- [Registration Methods](#registration-methods)
- [Hook Categories](#hook-categories)
- [Run Hooks](#run-hooks)
- [Model Request Hooks](#model-request-hooks)
- [Tool Hooks](#tool-hooks)
- [Output Hooks](#output-hooks)
- [Wrap Hooks](#wrap-hooks)
- [Tool Hook Filtering](#tool-hook-filtering)
- [Error Hooks](#error-hooks)
- [ModelRetry in Hooks](#modelretry-in-hooks)
- [Timeouts](#timeouts)
- [Hook Ordering](#hook-ordering)
- [Common Pitfalls](#common-pitfalls)

## Overview

Hooks are lifecycle interceptors that modify agent behavior at every stage of a run — model requests, tool calls, streaming events, and output validation. They use simple decorators or constructor arguments and compose with the capabilities system.

## Registration Methods

### Decorator Registration

```python
from pydantic_ai import RunContext
from pydantic_ai.capabilities import Hooks

hooks = Hooks()

@hooks.on.before_model_request
async def log_request(ctx: RunContext[None], request_context) -> object:
    print(f'Sending {len(request_context.messages)} messages')
    return request_context

agent = Agent('openai:gpt-5.2', capabilities=[hooks])
```

### Constructor Registration

```python
async def log_request(ctx, request_context):
    print(f'Request: {len(request_context.messages)} messages')
    return request_context

agent = Agent('openai:gpt-5.2', capabilities=[
    Hooks(before_model_request=log_request)
])
```

## Hook Categories

| Category | Fires When |
|----------|-----------|
| **Run hooks** | Once per agent run (before/after entire execution) |
| **Node hooks** | For each graph step (UserPrompt, ModelRequest, CallTools) |
| **Model request hooks** | Around each LLM API call |
| **Tool validation hooks** | When tool JSON arguments are parsed/validated |
| **Tool execution hooks** | When the tool function actually runs |
| **Output validation hooks** | When structured output is parsed (including partials) |
| **Output processing hooks** | When output is extracted or output function called |
| **Event stream hooks** | Around the event stream (for streaming runs) |
| **Deferred tool call hooks** | When approval-required tools are invoked |
| **Tool preparation hooks** | When tool definitions are filtered/modified |

## Run Hooks

Execute once per agent run:

```python
@hooks.on.before_run
async def on_start(ctx: RunContext[None]) -> None:
    print('Agent run starting')

@hooks.on.after_run
async def on_end(ctx: RunContext[None], *, result) -> object:
    print(f'Agent run finished: {result.output}')
    return result
```

### Wrap Run (Middleware Pattern)

```python
@hooks.on.run
async def time_run(ctx, *, handler):
    import time
    start = time.time()
    result = await handler()
    print(f'Run took {time.time() - start:.2f}s')
    return result
```

## Model Request Hooks

Fire around each LLM API call:

```python
@hooks.on.before_model_request
async def add_metadata(ctx, request_context):
    print(f'Model: {request_context.model}')
    print(f'Messages: {len(request_context.messages)}')
    return request_context

@hooks.on.after_model_request
async def log_response(ctx, *, request_context, response):
    print(f'Response parts: {len(response.parts)}')
    return response
```

### Swapping Models Dynamically

```python
@hooks.on.before_model_request
async def use_better_model_on_retry(ctx, request_context):
    if ctx.run_step > 1:
        request_context.model = 'openai:gpt-5.2'  # Upgrade on retry
    return request_context
```

## Tool Hooks

Separate hooks for validation (JSON parsing) and execution (function call):

### Tool Validation Hooks

```python
@hooks.on.before_tool_validate
async def log_raw_args(ctx, *, call, tool_def) -> None:
    print(f'Tool {tool_def.name} raw args: {call.args_as_json_str()}')

@hooks.on.after_tool_validate
async def log_validated_args(ctx, *, call, tool_def, args):
    print(f'Tool {tool_def.name} validated: {args}')
    return args
```

### Tool Execution Hooks

```python
@hooks.on.before_tool_execute
async def audit_tool(ctx, *, call, tool_def, args):
    print(f'Executing {tool_def.name}')
    return args

@hooks.on.after_tool_execute
async def log_result(ctx, *, call, tool_def, args, result):
    print(f'{tool_def.name} returned: {result}')
    return result
```

## Output Hooks

### Output Validation Hooks

Fire when structured output is parsed (including during streaming for partials):

```python
@hooks.on.before_output_validate
async def log_output_attempt(ctx, *, output_context):
    print(f'Validating output')
    return output_context

@hooks.on.after_output_validate
async def log_validated_output(ctx, *, output_context, output):
    print(f'Output validated: {output}')
    return output
```

### Output Processing Hooks

Fire when output is extracted or output functions are called:

```python
@hooks.on.before_output_process
async def pre_process(ctx, *, output_context):
    return output_context

@hooks.on.after_output_process
async def post_process(ctx, *, output_context, result):
    return result
```

## Wrap Hooks

Middleware-style hooks that control both before and after execution:

```python
@hooks.on.model_request
async def retry_on_rate_limit(ctx, *, request_context, handler):
    import asyncio
    for attempt in range(3):
        try:
            return await handler(request_context)
        except RateLimitError:
            await asyncio.sleep(2 ** attempt)
    raise

@hooks.on.tool_execute
async def time_tool(ctx, *, call, tool_def, args, handler):
    import time
    start = time.time()
    result = await handler(args)
    print(f'{tool_def.name}: {time.time() - start:.2f}s')
    return result
```

## Tool Hook Filtering

Target specific tools by name:

```python
@hooks.on.before_tool_execute(tools=['send_email', 'delete_record'])
async def audit_dangerous(ctx, *, call, tool_def, args):
    print(f'AUDIT: {tool_def.name} called with {args}')
    return args
```

## Error Hooks

Error hooks use raise-to-propagate, return-to-recover semantics:

```python
@hooks.on.model_request_error
async def handle_api_error(ctx, *, request_context, error):
    if isinstance(error, TimeoutError):
        return fallback_response  # Suppress error, return fallback
    raise error  # Propagate other errors

@hooks.on.tool_execute_error
async def handle_tool_error(ctx, *, call, tool_def, args, error):
    print(f'Tool {tool_def.name} failed: {error}')
    raise  # Re-raise (default behavior)
```

## ModelRetry in Hooks

Hooks can raise `ModelRetry` to ask the model to retry:

```python
@hooks.on.after_model_request
async def check_response(ctx, *, request_context, response):
    if 'PLACEHOLDER' in str(response.parts):
        raise ModelRetry('Response contains placeholder text.')
    return response
```

## Timeouts

Each hook supports an optional timeout:

```python
@hooks.on.before_model_request(timeout=5.0)
async def slow_hook(ctx, request_context):
    await some_slow_operation()
    return request_context
# Raises HookTimeoutError after 5 seconds
```

## Hook Ordering

- **`before_*`** hooks fire in registration/capability order
- **`after_*`** hooks fire in reverse order
- **`wrap_*`** hooks nest as middleware layers (first registered = outermost)

## Common Pitfalls

- **Hooks vs Capabilities** — use `Hooks` for quick interceptors and logging; use `AbstractCapability` when you need reusable bundles of tools + hooks + instructions
- **Partial output in output hooks** — output validation hooks fire on every partial during streaming; check `ctx.partial_output`
- **ModelRetry budget** — retries from hooks count against the tool/output `max_retries` budget
- **Async required for wrap hooks** — wrap hooks must be `async def` since they call `await handler(...)`

## Related

- `05-capabilities.md` — Capabilities that contain hooks
- `04-tools.md` — Tool definitions
- `01-agents.md` — Agent lifecycle
