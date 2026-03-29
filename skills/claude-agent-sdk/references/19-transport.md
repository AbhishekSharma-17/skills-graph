# Claude Agent SDK — Transport

> Source: [platform.claude.com/docs/en/agent-sdk](https://platform.claude.com/docs/en/agent-sdk/overview) — Python v0.1.51, TypeScript v0.2.86

## Contents

- [What is Transport?](#what-is-transport)
- [The Default: SubprocessCLITransport](#the-default-subprocessclitransport)
- [The Transport Abstract Class](#the-transport-abstract-class)
- [The Wire Protocol (JSON-Lines)](#the-wire-protocol-json-lines)
- [When to Use a Custom Transport](#when-to-use-a-custom-transport)
- [Building a Custom Transport](#building-a-custom-transport)
- [Use Case 1: Testing / Mock Transport](#use-case-1-testing--mock-transport)
- [Use Case 2: WebSocket (Remote Execution)](#use-case-2-websocket-remote-execution)
- [Use Case 3: SSH Tunnel](#use-case-3-ssh-tunnel)
- [Use Case 4: HTTP (Container Hosting)](#use-case-4-http-container-hosting)
- [Use Case 5: Message Queue (Enterprise)](#use-case-5-message-queue-enterprise)
- [Plugging In a Custom Transport](#plugging-in-a-custom-transport)
- [Important Warnings](#important-warnings)
- [Decision Tree](#decision-tree)

---

## What is Transport?

Transport is the **communication pipe** between your Python code and the Claude Code CLI subprocess. It handles:

- **Sending** your prompts and control messages to Claude
- **Receiving** Claude's responses, tool calls, and result messages
- **Managing** the connection lifecycle (connect, ready, close)

By default the SDK uses `SubprocessCLITransport` — spawns `claude` CLI as a local child process and communicates via stdin/stdout. **You never need to touch it for normal usage.**

```
Default flow:

Your Python App                     Local Machine
┌─────────────────┐               ┌──────────────────┐
│                  │   stdin       │                  │
│  query() or     │──(JSON)──────→│  claude CLI       │────→ Claude API
│  ClaudeSDKClient│               │  (subprocess)     │
│                  │   stdout      │                  │
│                  │←─(JSON)──────│                  │←──── Claude API
└─────────────────┘               └──────────────────┘
        ↑                                  ↑
        └── Your code                      └── SubprocessCLITransport (auto)

Custom transport flow (e.g. WebSocket):

Your Python App                     Remote Server
┌─────────────────┐               ┌──────────────────┐
│                  │  WebSocket    │  Relay Server    │
│  query() or     │──(JSON)──────→│       ↓          │────→ Claude API
│  ClaudeSDKClient│               │  claude CLI       │
│                  │  WebSocket    │  (subprocess)    │←──── Claude API
│                  │←─(JSON)──────│                  │
└─────────────────┘               └──────────────────┘
```

**Key insight:** Transport only **moves JSON messages**. It does not understand them. The SDK's internal `Query` layer above handles protocol logic (initialization, permissions, hooks, MCP routing). Your transport just relays.

---

## The Default: SubprocessCLITransport

Auto-created. You never instantiate it directly.

| Property | Value |
|----------|-------|
| Communication | stdin/stdout pipes (JSON-lines format) |
| Buffer size | 1MB default (configurable via `max_buffer_size`) |
| Min CLI version required | 2.0.0 |
| Thread safety | Writes protected by `anyio.Lock` |
| Shutdown | Graceful: 5s wait → SIGTERM → SIGKILL |
| CLI search paths | `~/.npm-global/bin/claude`, `/usr/local/bin/claude`, `~/.local/bin/claude`, `~/.claude/local/claude` |

---

## The Transport Abstract Class

Subclass this to build a custom transport:

```python
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any


class Transport(ABC):
    """
    WARNING: This internal API is exposed for custom transport implementations
    (e.g., remote Claude Code connections). The Claude Code team may change or
    remove this abstract class in any future release.
    """

    @abstractmethod
    async def connect(self) -> None:
        """Start the connection (subprocess, WebSocket, SSH, etc.)."""

    @abstractmethod
    async def write(self, data: str) -> None:
        """Send raw JSON-line string to Claude."""

    @abstractmethod
    def read_messages(self) -> AsyncIterator[dict[str, Any]]:
        """Yield parsed JSON message dicts from Claude. Runs until connection closes."""

    @abstractmethod
    async def close(self) -> None:
        """Close connection and release resources."""

    @abstractmethod
    def is_ready(self) -> bool:
        """Return True if connection is live and ready."""

    @abstractmethod
    async def end_input(self) -> None:
        """Signal end of input (close stdin / send end-of-stream)."""
```

### The 6 Methods

| # | Method | Called | What it does |
|---|--------|--------|-------------|
| 1 | `connect()` | Once at startup | Open the connection |
| 2 | `write(data: str)` | Every outbound message | Send JSON string to Claude |
| 3 | `read_messages()` | Continuously | Yield parsed JSON dicts from Claude |
| 4 | `close()` | Once at shutdown | Clean up everything |
| 5 | `is_ready()` | Periodically | Return True if connection is live |
| 6 | `end_input()` | When input stream ends | Signal "no more messages" |

---

## The Wire Protocol (JSON-Lines)

Your transport relays these without needing to understand them. One message per line (`\n` terminated).

### Outbound — Your Code → Claude

**User message (every prompt):**
```json
{"type": "user", "message": {"role": "user", "content": "Fix the bug in app.py"}, "parent_tool_use_id": null, "session_id": "default"}
```

**Init control request (sent once on connect):**
```json
{"type": "control_request", "request_id": "init-001", "request": {"subtype": "initialize", "hooks": null, "agents": null}}
```

**Permission response (when Claude asks to use a tool):**
```json
{"type": "control_response", "response": {"subtype": "success", "request_id": "perm-001", "response": {"behavior": "allow"}}}
```

### Inbound — Claude → Your Code

**Assistant text message:**
```json
{"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "I'll read the file now."}]}, "session_id": "abc-123"}
```

**Assistant tool call:**
```json
{"type": "assistant", "message": {"role": "assistant", "content": [{"type": "tool_use", "id": "tu_001", "name": "Read", "input": {"file_path": "/app.py"}}]}}
```

**Result message (final):**
```json
{"type": "result", "subtype": "result", "duration_ms": 5432, "is_error": false, "num_turns": 3, "session_id": "abc-123", "total_cost_usd": 0.0234}
```

**Permission request (Claude asking to use a tool):**
```json
{"type": "control_request", "request_id": "perm-001", "request": {"subtype": "can_use_tool", "tool_name": "Bash", "input": {"command": "ls -la"}}}
```

### Init Handshake (Critical for Custom Transports)

The SDK sends an init control request immediately after `connect()`. Your `read_messages()` **must yield a success response first** before your real messages:

```python
async def read_messages(self):
    # The SDK expects this init response first — always yield it
    yield {
        "type": "control_response",
        "response": {"subtype": "success", "request_id": "", "response": None},
    }
    # Then yield your real messages
    for msg in self._messages:
        yield msg
```

---

## When to Use a Custom Transport

The default covers 99% of use cases. Only build custom transports for:

| Use Case | Problem | Solution |
|----------|---------|----------|
| **Testing** | Don't want real API calls in tests | MockTransport with canned responses |
| **Remote execution** | CLI can't run locally (Lambda, ARM, no Node.js) | WebSocket transport to remote server |
| **Web UI** | Browser needs to talk to Claude backend | WebSocket relay from backend to frontend |
| **Container/Cloud** | CLI runs in a Docker container | HTTP transport to container endpoint |
| **SSH tunnel** | Claude Code on a remote dev box | SSHTransport piping stdin/stdout |
| **Enterprise** | Must go through message queue | Kafka/Redis Streams transport |

**Decision tree:**
```
Is claude CLI installed locally?
  YES → Use default transport. DONE.
  NO  → Are you writing tests?
    YES → Build MockTransport
    NO  → Does CLI run on a remote server?
      YES → Build WebSocket or SSH transport
      NO  → You probably don't need custom transport
```

---

## Building a Custom Transport

### Step 1 — Subclass Transport

```python
from claude_agent_sdk import Transport

class MyTransport(Transport):
    async def connect(self) -> None: ...
    async def write(self, data: str) -> None: ...
    async def read_messages(self): ...
    async def close(self) -> None: ...
    def is_ready(self) -> bool: ...
    async def end_input(self) -> None: ...
```

### Step 2 — Handle init handshake in `read_messages()`

```python
async def read_messages(self):
    yield {"type": "control_response", "response": {"subtype": "success", "request_id": "", "response": None}}
    # real messages follow
```

### Step 3 — Relay JSON faithfully

- `write(data)` — send `data` string as-is over your channel
- `read_messages()` — receive lines, parse JSON (`json.loads(line)`), yield dicts

### Step 4 — Plug it in

```python
transport = MyTransport(...)

# With query()
async for msg in query(prompt="Hello", options=options, transport=transport):
    ...

# With ClaudeSDKClient
client = ClaudeSDKClient(options=options, transport=transport)
async with client:
    await client.query("Hello")
    async for msg in client.receive_response():
        ...
```

---

## Use Case 1: Testing / Mock Transport

The **most practical use case** — no API costs, deterministic, fast, no CLI needed.

```python
import json
from collections.abc import AsyncIterator
from typing import Any

from claude_agent_sdk import Transport


class MockTransport(Transport):
    """Returns pre-configured responses — no API calls, no CLI needed."""

    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self._responses = responses
        self._ready = False
        self._writes: list[str] = []

    async def connect(self) -> None:
        self._ready = True

    async def write(self, data: str) -> None:
        self._writes.append(data)   # log what was sent

    async def read_messages(self) -> AsyncIterator[dict[str, Any]]:
        # Init handshake first
        yield {"type": "control_response", "response": {"subtype": "success", "request_id": "", "response": None}}
        for response in self._responses:
            yield response

    async def close(self) -> None:
        self._ready = False

    def is_ready(self) -> bool:
        return self._ready

    async def end_input(self) -> None:
        pass

    @property
    def writes(self) -> list[str]:
        return self._writes

    @property
    def parsed_writes(self) -> list[dict[str, Any]]:
        return [json.loads(w) for w in self._writes if w.strip()]


# ── Response builder helpers ──

def make_text_response(text: str, session_id: str = "test") -> dict:
    return {
        "type": "assistant",
        "message": {
            "role": "assistant",
            "model": "claude-sonnet-4-6",
            "content": [{"type": "text", "text": text}],
        },
        "session_id": session_id,
    }


def make_tool_call(tool_name: str, tool_input: dict, session_id: str = "test") -> dict:
    return {
        "type": "assistant",
        "message": {
            "role": "assistant",
            "model": "claude-sonnet-4-6",
            "content": [{"type": "tool_use", "id": f"tu_{tool_name}_001", "name": tool_name, "input": tool_input}],
        },
        "session_id": session_id,
    }


def make_result(cost: float = 0.001, turns: int = 1, session_id: str = "test", is_error: bool = False) -> dict:
    return {
        "type": "result",
        "subtype": "result",
        "duration_ms": 1000,
        "duration_api_ms": 800,
        "is_error": is_error,
        "num_turns": turns,
        "session_id": session_id,
        "total_cost_usd": cost,
    }
```

### Using in pytest

```python
import pytest
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ResultMessage, TextBlock


@pytest.mark.asyncio
async def test_simple_text_response():
    transport = MockTransport(responses=[
        make_text_response("The capital of France is Paris."),
        make_result(cost=0.002, turns=1),
    ])

    options = ClaudeAgentOptions(permission_mode="bypassPermissions")
    messages = []

    async for msg in query(prompt="Capital of France?", options=options, transport=transport):
        messages.append(msg)

    assert isinstance(messages[0], AssistantMessage)
    assert "Paris" in messages[0].content[0].text
    assert isinstance(messages[1], ResultMessage)
    assert messages[1].total_cost_usd == 0.002


@pytest.mark.asyncio
async def test_tool_call_response():
    transport = MockTransport(responses=[
        make_tool_call("Read", {"file_path": "/app.py"}),
        make_text_response("The file contains a Flask application."),
        make_result(cost=0.005, turns=2),
    ])

    options = ClaudeAgentOptions(permission_mode="bypassPermissions")
    texts = []

    async for msg in query(prompt="Read app.py", options=options, transport=transport):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    texts.append(block.text)

    assert any("Flask" in t for t in texts)


@pytest.mark.asyncio
async def test_writes_logged():
    transport = MockTransport(responses=[make_text_response("Hi!"), make_result()])
    options = ClaudeAgentOptions(permission_mode="bypassPermissions")

    async for _ in query(prompt="Hello", options=options, transport=transport):
        pass

    assert len(transport.writes) > 0
    # Verify the prompt was included in outbound writes
    all_written = " ".join(transport.writes)
    assert "Hello" in all_written
```

---

## Use Case 2: WebSocket (Remote Execution)

Connect to a Claude Code CLI running on a remote server via WebSocket relay.

```python
"""
Requirements: pip install websockets
"""
import json
from collections.abc import AsyncIterator
from typing import Any

import websockets

from claude_agent_sdk import Transport


class WebSocketTransport(Transport):
    """Connect to Claude Code CLI via a WebSocket relay server."""

    def __init__(self, url: str, auth_token: str | None = None) -> None:
        self._url = url
        self._auth_token = auth_token
        self._ws = None
        self._ready = False

    async def connect(self) -> None:
        headers = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        self._ws = await websockets.connect(
            self._url,
            additional_headers=headers,
            max_size=10 * 1024 * 1024,
            ping_interval=30,
            ping_timeout=10,
        )
        self._ready = True

    async def write(self, data: str) -> None:
        if not self._ws:
            raise ConnectionError("Not connected")
        await self._ws.send(data)

    async def read_messages(self) -> AsyncIterator[dict[str, Any]]:
        if not self._ws:
            raise ConnectionError("Not connected")
        try:
            async for raw in self._ws:
                for line in raw.strip().split("\n"):
                    line = line.strip()
                    if line:
                        try:
                            yield json.loads(line)
                        except json.JSONDecodeError:
                            pass
        except websockets.ConnectionClosed:
            self._ready = False

    async def close(self) -> None:
        self._ready = False
        if self._ws:
            await self._ws.close()
            self._ws = None

    def is_ready(self) -> bool:
        return self._ready and self._ws is not None

    async def end_input(self) -> None:
        if self._ws:
            await self._ws.send(json.dumps({"type": "end_input"}) + "\n")


# ── Usage ──
async def main():
    from claude_agent_sdk import query, ClaudeAgentOptions

    transport = WebSocketTransport(
        url="wss://my-claude-server.com/ws",
        auth_token="my-secret-token",
    )
    options = ClaudeAgentOptions(
        model="sonnet",
        # No env needed — credentials are on the remote server
        permission_mode="bypassPermissions",
        max_turns=5,
    )
    async for msg in query(prompt="List files in the project", options=options, transport=transport):
        ...
```

**Related community projects:**
- [claude-agent-server](https://github.com/dzhng/claude-agent-server) — WebSocket server wrapping Claude Code CLI
- [claude-code-server](https://github.com/Kurogoma4D/claude-code-server) — Remote Claude Code over WebSocket

---

## Use Case 3: SSH Tunnel

Run Claude Code CLI on a remote dev machine, controlled from your local script.

```python
import asyncio
import json
from claude_agent_sdk import Transport


class SSHTransport(Transport):
    """Run claude CLI on a remote machine over SSH."""

    def __init__(self, host: str, user: str, key_path: str, remote_cwd: str = "~") -> None:
        self._host = host
        self._user = user
        self._key_path = key_path
        self._remote_cwd = remote_cwd
        self._process = None
        self._ready = False

    async def connect(self) -> None:
        self._process = await asyncio.create_subprocess_exec(
            "ssh",
            "-i", self._key_path,
            "-o", "StrictHostKeyChecking=no",
            f"{self._user}@{self._host}",
            f"cd {self._remote_cwd} && claude --output-format stream-json --verbose -p -",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._ready = True

    async def write(self, data: str) -> None:
        if self._process and self._process.stdin:
            self._process.stdin.write(data.encode())
            await self._process.stdin.drain()

    async def read_messages(self):
        if not self._process or not self._process.stdout:
            return
        buffer = ""
        while True:
            chunk = await self._process.stdout.read(4096)
            if not chunk:
                break
            buffer += chunk.decode()
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if line:
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        pass  # skip SSH banners etc.

    async def close(self) -> None:
        self._ready = False
        if self._process:
            self._process.terminate()
            await self._process.wait()

    def is_ready(self) -> bool:
        return self._ready

    async def end_input(self) -> None:
        if self._process and self._process.stdin:
            self._process.stdin.close()


# Usage
transport = SSHTransport(
    host="dev-server.example.com",
    user="abhishek",
    key_path="~/.ssh/id_rsa",
    remote_cwd="/home/abhishek/projects/my-app",
)
```

---

## Use Case 4: HTTP (Container Hosting)

Claude Code CLI runs inside a Docker container; your app talks to it via HTTP/SSE.

```python
import json
import httpx
from claude_agent_sdk import Transport


class HttpTransport(Transport):
    """HTTP transport for container-hosted Claude Code."""

    def __init__(self, base_url: str, auth_token: str | None = None) -> None:
        self._base_url = base_url
        self._auth_token = auth_token
        self._client: httpx.AsyncClient | None = None
        self._session_id: str | None = None
        self._ready = False

    async def connect(self) -> None:
        headers = {"Authorization": f"Bearer {self._auth_token}"} if self._auth_token else {}
        self._client = httpx.AsyncClient(base_url=self._base_url, headers=headers, timeout=300.0)
        resp = await self._client.post("/sessions")
        resp.raise_for_status()
        self._session_id = resp.json()["session_id"]
        self._ready = True

    async def write(self, data: str) -> None:
        await self._client.post(
            f"/sessions/{self._session_id}/messages",
            content=data,
            headers={"Content-Type": "application/json"},
        )

    async def read_messages(self):
        async with self._client.stream("GET", f"/sessions/{self._session_id}/stream") as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data:
                        yield json.loads(data)

    async def close(self) -> None:
        self._ready = False
        if self._client:
            if self._session_id:
                await self._client.delete(f"/sessions/{self._session_id}")
            await self._client.aclose()

    def is_ready(self) -> bool:
        return self._ready

    async def end_input(self) -> None:
        await self._client.post(f"/sessions/{self._session_id}/end")
```

---

## Use Case 5: Message Queue (Enterprise)

All communication through Redis Streams for audit, compliance, retry, and load sharing.

```python
import json
from claude_agent_sdk import Transport


class RedisStreamTransport(Transport):
    """Route messages through Redis Streams for enterprise deployments."""

    def __init__(self, redis_client, session_id: str) -> None:
        self._redis = redis_client
        self._inbound = f"claude:{session_id}:in"    # SDK writes here
        self._outbound = f"claude:{session_id}:out"   # Worker writes here
        self._ready = False

    async def connect(self) -> None:
        self._ready = True

    async def write(self, data: str) -> None:
        await self._redis.xadd(self._inbound, {"data": data})

    async def read_messages(self):
        last_id = "0"
        while True:
            entries = await self._redis.xread({self._outbound: last_id}, block=5000)
            for stream, messages in entries:
                for msg_id, fields in messages:
                    last_id = msg_id
                    yield json.loads(fields["data"])

    async def close(self) -> None:
        self._ready = False

    def is_ready(self) -> bool:
        return self._ready

    async def end_input(self) -> None:
        await self._redis.xadd(self._inbound, {"data": '{"type": "end_input"}'})
```

**When this makes sense:**
- Compliance requires all AI interactions logged to a queue
- Multiple workers process Claude requests from a shared queue
- Retry logic — failed requests can be replayed from the queue
- Rate limiting at the broker level

---

## Plugging In a Custom Transport

Both `query()` and `ClaudeSDKClient` accept a `transport` parameter:

```python
# query() — pass as keyword argument
async for msg in query(
    prompt="Hello",
    options=options,
    transport=MyTransport(...),
):
    ...

# ClaudeSDKClient — pass to constructor
client = ClaudeSDKClient(
    options=options,
    transport=MyTransport(...),
)
async with client:
    await client.query("Hello")
    async for msg in client.receive_response():
        ...
```

When `transport=None` (default), the SDK auto-creates `SubprocessCLITransport`.

---

## Important Warnings

### The Transport API is Unstable

From the source code docstring:

> **WARNING:** This internal API is exposed for custom transport implementations. The Claude Code team may change or remove this abstract class in any future release. Custom implementations must be updated to match interface changes.

**Practical implications:**
- Custom transports may break on SDK version upgrades
- Pin your SDK version if using custom transports: `claude-agent-sdk==0.1.51`
- Check the changelog before upgrading

### No Official Remote Transport Exists

As of March 2026, Anthropic ships only:
- `SubprocessCLITransport` — the one built-in transport
- `Transport` ABC — the extension point

Community projects (claude-agent-server, claude-code-server) exist but are not maintained by Anthropic.

### Claude Code CLI Must Be on the Other End

Any transport — local or remote — ultimately connects to a `claude` CLI process. Transport changes HOW you connect, not WHAT you connect to.

```
Always: Your Code → Transport → Claude Code CLI → Claude API
                     ↑
                     This is what you're replacing
```

---

## Decision Tree

| Scenario | Transport to Use | Complexity |
|----------|-----------------|-----------|
| Normal usage — scripts, production | Default (omit `transport`) | None |
| Unit tests without API calls | `MockTransport` | Low |
| CLI runs on remote server | WebSocket or SSH | Medium |
| Web UI backend relay | WebSocket | Medium |
| CLI in Docker container | HTTP | Medium |
| Enterprise message queue | Redis/Kafka transport | High |

---

## Related Topics

- [Middleware & Proxy](20-middleware.md) — Transport wrappers as middleware, hooks, can_use_tool
- [ClaudeSDKClient](17-client.md) — `transport` constructor parameter
- [query() and Messages](16-query-and-messages.md) — `transport` parameter in query()
- [Deployment](10-deployment.md) — Containerized deployment patterns
- [Secure Deployment](15-secure-deployment.md) — Security considerations for remote transports
