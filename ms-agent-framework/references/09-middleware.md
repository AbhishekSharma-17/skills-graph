# Middleware — Agent, Function, Chat Middleware

## Three Middleware Types

| Type | Intercepts | Use For |
|---|---|---|
| **Agent Middleware** | `agent.run()` execution | Logging, auth, rate limiting, caching |
| **Function Middleware** | Tool/function calls | Approval, auditing, retries |
| **Chat Middleware** | AI model requests | Token tracking, content filtering |

## Execution Flow

```
User Input
  → Agent Middleware (outermost)
    → Run-level Middleware
      → Agent Logic
        → Function Middleware (on tool calls)
        → Chat Middleware (on LLM calls)
      ← Agent Logic returns
    ← Run-level Middleware post-processing
  ← Agent Middleware post-processing
→ Response to User
```

## Three Implementation Patterns

### 1. Function-Based (Simplest)

#### Agent Middleware
```python
from agent_framework import AgentRunContext
from collections.abc import Awaitable, Callable

async def logging_agent_middleware(
    context: AgentRunContext,
    next: Callable[[AgentRunContext], Awaitable[None]],
) -> None:
    print("[Agent] Starting execution")
    await next(context)  # Continue to agent
    print("[Agent] Execution completed")
```

#### Function Middleware
```python
from agent_framework import FunctionInvocationContext

async def logging_function_middleware(
    context: FunctionInvocationContext,
    next: Callable[[FunctionInvocationContext], Awaitable[None]],
) -> None:
    print(f"[Function] Calling {context.function.name}")
    await next(context)  # Continue to function
    print(f"[Function] {context.function.name} completed")
```

#### Chat Middleware
```python
from agent_framework import ChatContext

async def logging_chat_middleware(
    context: ChatContext,
    next: Callable[[ChatContext], Awaitable[None]],
) -> None:
    print(f"[Chat] Sending {len(context.messages)} messages to AI")
    await next(context)  # Continue to AI
    print("[Chat] AI response received")
```

### 2. Decorator-Based

```python
from agent_framework import agent_middleware, function_middleware, chat_middleware

@agent_middleware
async def simple_agent_mw(context, next):
    print("Before agent execution")
    await next(context)
    print("After agent execution")

@function_middleware
async def simple_function_mw(context, next):
    print(f"Calling: {context.function.name}")
    await next(context)
    print("Function done")

@chat_middleware
async def simple_chat_mw(context, next):
    print(f"Messages: {len(context.messages)}")
    await next(context)
    print("Chat done")
```

### 3. Class-Based

```python
from agent_framework import AgentMiddleware, AgentRunContext

class LoggingAgentMiddleware(AgentMiddleware):
    async def process(
        self,
        context: AgentRunContext,
        next: Callable[[AgentRunContext], Awaitable[None]],
    ) -> None:
        print("[Agent] Starting")
        await next(context)
        print("[Agent] Done")
```

```python
from agent_framework import FunctionMiddleware, FunctionInvocationContext

class LoggingFunctionMiddleware(FunctionMiddleware):
    async def process(
        self,
        context: FunctionInvocationContext,
        next: Callable[[FunctionInvocationContext], Awaitable[None]],
    ) -> None:
        print(f"[Function] {context.function.name}")
        await next(context)
```

```python
from agent_framework import ChatMiddleware, ChatContext

class LoggingChatMiddleware(ChatMiddleware):
    async def process(
        self,
        context: ChatContext,
        next: Callable[[ChatContext], Awaitable[None]],
    ) -> None:
        print(f"[Chat] {len(context.messages)} messages")
        await next(context)
```

## Context Type Properties

### AgentRunContext
```python
context.messages      # list[Message] — conversation messages
context.metadata      # dict — shared data between middleware
context.terminate     # bool — set True to skip agent execution
context.result        # AgentResponse or async generator
context.is_streaming  # bool — whether streaming mode is active
```

### FunctionInvocationContext
```python
context.function      # The function being invoked
context.function.name # str — function name
context.arguments     # dict — validated function arguments
context.metadata      # dict — shared data between middleware
context.result        # Function call result
context.terminate     # bool — set True to skip function execution
```

### ChatContext
```python
context.messages      # list[Message] — messages being sent to AI
context.chat_client   # The chat client instance
context.metadata      # dict — shared data between middleware
context.result        # ChatResponse from AI service
```

## Registration

### Agent-Level (All Runs)

```python
agent = client.as_agent(
    name="GuardedAgent",
    tools=[get_weather],
    middleware=[
        SecurityAgentMiddleware(),    # Applies to ALL runs
        TimingFunctionMiddleware(),
    ],
)
```

### Run-Level (Single Run)

```python
# Agent-level middleware + run-level middleware both apply
result = await agent.run(
    "What's the weather?",
    middleware=[logging_chat_middleware],  # This run only
)

# Next run — only agent-level middleware applies
result = await agent.run("Tell me a joke")
```

**Execution order:** Agent-level middleware runs first (outermost), then run-level middleware (innermost).

## Advanced Patterns

### Termination — Block Execution

```python
async def content_filter_middleware(
    context: AgentRunContext,
    next: Callable[[AgentRunContext], Awaitable[None]],
) -> None:
    last_msg = context.messages[-1] if context.messages else None
    if last_msg and "blocked_word" in (last_msg.text or "").lower():
        print("Request blocked by content filter")
        context.terminate = True  # Agent execution completely skipped
        return

    await next(context)
```

### Result Override — Replace Response

```python
from agent_framework import AgentResponse, AgentResponseUpdate, TextContent, Message, Role
from typing import AsyncIterable

async def override_middleware(
    context: AgentRunContext,
    next: Callable[[AgentRunContext], Awaitable[None]],
) -> None:
    await next(context)  # Let agent run

    if context.result is not None:
        if context.is_streaming:
            # Override streaming response
            async def custom_stream() -> AsyncIterable[AgentResponseUpdate]:
                yield AgentResponseUpdate(contents=[TextContent(text="Custom response")])
            context.result = custom_stream()
        else:
            # Override non-streaming response
            context.result = AgentResponse(
                messages=[Message(role=Role.ASSISTANT, text="Custom response")]
            )
```

### Function Approval (Human-in-the-Loop)

```python
async def approval_middleware(
    context: FunctionInvocationContext,
    next: Callable[[FunctionInvocationContext], Awaitable[None]],
) -> None:
    sensitive = ["delete_record", "send_email", "make_payment"]
    if context.function.name in sensitive:
        print(f"Tool: {context.function.name}, Args: {context.arguments}")
        if input("Approve? (y/n): ").lower() != "y":
            context.terminate = True
            return
    await next(context)
```

### Retry Middleware

```python
async def retry_chat_middleware(
    context: ChatContext,
    next: Callable[[ChatContext], Awaitable[None]],
) -> None:
    for attempt in range(3):
        try:
            await next(context)
            return
        except Exception as e:
            if attempt < 2:
                print(f"Retry {attempt + 1}/3: {e}")
                await asyncio.sleep(2 ** attempt)
            else:
                raise
```

### Token Tracking Middleware

```python
async def token_tracking_middleware(
    context: ChatContext,
    next: Callable[[ChatContext], Awaitable[None]],
) -> None:
    await next(context)

    if context.result and hasattr(context.result, 'usage'):
        usage = context.result.usage
        print(f"Tokens: {usage.prompt_tokens} in, {usage.completion_tokens} out")
        context.metadata["total_tokens"] = (
            context.metadata.get("total_tokens", 0) + usage.total_tokens
        )
```

## Important Notes

1. Always call `await next(context)` unless you're intentionally terminating
2. Middleware chains execute in registration order
3. Agent-level runs before run-level
4. Function middleware only works with tools that go through `FunctionInvokingChatClient`
5. Provide both streaming and non-streaming handling for result overrides
