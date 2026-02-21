# Custom Agents — BaseAgent, SupportsAgentRun, Extending the Framework

## Two Approaches

| Approach | When to Use |
|---|---|
| **`BaseAgent`** | Extend framework's base class — get session management, middleware for free |
| **`SupportsAgentRun`** | Implement protocol from scratch — full control |

## BaseAgent — Recommended

Extend `BaseAgent` and implement `_run_implementation` and `_run_streaming_implementation`:

```python
import asyncio
from collections.abc import AsyncIterable, Sequence
from typing import Any
from agent_framework import (
    AgentResponse,
    AgentResponseUpdate,
    AgentSession,
    BaseAgent,
    Content,
    Message,
    ResponseStream,
    normalize_messages,
)

class EchoAgent(BaseAgent):
    """Custom agent that echoes user messages with a prefix."""

    @property
    def id(self) -> str:
        return "echo-agent"

    async def _run_implementation(
        self,
        messages: Sequence[Message],
        session: AgentSession | None = None,
        **kwargs: Any,
    ) -> AgentResponse:
        """Non-streaming implementation."""
        if messages:
            last = normalize_messages(messages)[-1]
            return AgentResponse(
                messages=[Message(role="assistant", text=f"Echo: {last.text}")]
            )
        return AgentResponse(messages=[])

    async def _run_streaming_implementation(
        self,
        messages: Sequence[Message],
        session: AgentSession | None = None,
        **kwargs: Any,
    ) -> AsyncIterable[AgentResponseUpdate]:
        """Streaming implementation."""
        if messages:
            last = normalize_messages(messages)[-1]
            echo_text = f"Echo: {last.text}"
            for char in echo_text:
                yield AgentResponseUpdate(contents=[Content(text=char)])
                await asyncio.sleep(0.05)
```

### Using BaseAgent

```python
echo = EchoAgent()

# Non-streaming
response = await echo.run("Hello!", session=echo.create_session())
print(response.text)  # "Echo: Hello!"

# Streaming
stream = echo.run("Stream this", stream=True, session=echo.create_session())
async for update in stream:
    print(update.text or "", end="", flush=True)

final = await stream.get_final_response()
print(f"\nFull: {final.text}")
```

## SupportsAgentRun — Full Protocol

For complete control, implement the `SupportsAgentRun` protocol:

```python
from typing import Any, Literal, overload
from collections.abc import Sequence
from agent_framework import (
    AgentResponse,
    AgentResponseUpdate,
    AgentSession,
    Message,
    ResponseStream,
    SupportsAgentRun,
)

class MyCustomAgent(SupportsAgentRun):
    @property
    def id(self) -> str:
        return "my-custom-agent"

    @overload
    async def run(
        self,
        messages: Sequence[Message],
        session: AgentSession | None = None,
        *,
        stream: Literal[True],
        **kwargs: Any,
    ) -> ResponseStream: ...

    @overload
    async def run(
        self,
        messages: Sequence[Message],
        session: AgentSession | None = None,
        *,
        stream: Literal[False] = False,
        **kwargs: Any,
    ) -> AgentResponse: ...

    async def run(self, messages, session=None, *, stream=False, **kwargs):
        if stream:
            return self._run_stream(messages, session, **kwargs)
        return await self._run_sync(messages, session, **kwargs)

    async def _run_sync(self, messages, session, **kwargs) -> AgentResponse:
        # Your custom logic
        return AgentResponse(
            messages=[Message(role="assistant", text="Custom response")]
        )

    async def _run_stream(self, messages, session, **kwargs) -> ResponseStream:
        # Your custom streaming logic
        async def generate():
            yield AgentResponseUpdate(contents=[Content(text="Custom ")])
            yield AgentResponseUpdate(contents=[Content(text="stream")])
        return ResponseStream(generate())
```

## Custom Agent Wrapping External APIs

```python
class ExternalAPIAgent(BaseAgent):
    """Agent that delegates to an external AI service."""

    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key

    @property
    def id(self) -> str:
        return "external-api-agent"

    async def _run_implementation(self, messages, session=None, **kwargs):
        import aiohttp
        async with aiohttp.ClientSession() as http:
            resp = await http.post(
                self.api_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"messages": [{"role": m.role, "content": m.text} for m in messages]},
            )
            data = await resp.json()
            return AgentResponse(
                messages=[Message(role="assistant", text=data["response"])]
            )

    async def _run_streaming_implementation(self, messages, session=None, **kwargs):
        # Implement SSE parsing for streaming
        ...
```

## Using Custom Agents in Workflows

Custom agents work seamlessly with workflows:

```python
from agent_framework.workflows import Executor, handler, WorkflowContext

class CustomAgentExecutor(Executor):
    def __init__(self, custom_agent):
        super().__init__(id=custom_agent.id)
        self.agent = custom_agent

    @handler
    async def process(self, text: str, ctx: WorkflowContext[str]) -> None:
        result = await self.agent.run(text)
        await ctx.send_message(result.text)
```

## Hosting Custom Agents

Custom agents can be hosted via Azure Functions:

```python
from agent_framework.azure import AgentFunctionApp

custom_agent = MyCustomAgent()
app = AgentFunctionApp(agents=[custom_agent])
```

## Key Points

1. `BaseAgent` gives you session management and middleware support for free
2. `SupportsAgentRun` gives full control but requires implementing everything
3. Both approaches work with workflows, middleware, and hosting
4. Implement BOTH streaming and non-streaming for full compatibility
5. Use `normalize_messages()` to handle different message input formats
