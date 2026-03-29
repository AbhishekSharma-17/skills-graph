# Claude Agent SDK — ClaudeSDKClient

> Source: [platform.claude.com/docs/en/agent-sdk](https://platform.claude.com/docs/en/agent-sdk/overview) — Python v0.1.51, TypeScript v0.2.86

## Contents

- [What is ClaudeSDKClient?](#what-is-claudesdkclient)
- [How It Works Under the Hood](#how-it-works-under-the-hood)
- [Constructor](#constructor)
- [Lifecycle — connect, use, disconnect](#lifecycle--connect-use-disconnect)
- [All 14 Methods](#all-14-methods)
  - [connect()](#connect)
  - [query()](#query)
  - [receive_messages()](#receive_messages)
  - [receive_response()](#receive_response)
  - [interrupt()](#interrupt)
  - [set_permission_mode()](#set_permission_mode)
  - [set_model()](#set_model)
  - [rewind_files()](#rewind_files)
  - [get_mcp_status()](#get_mcp_status)
  - [reconnect_mcp_server()](#reconnect_mcp_server)
  - [toggle_mcp_server()](#toggle_mcp_server)
  - [stop_task()](#stop_task)
  - [get_server_info()](#get_server_info)
  - [disconnect()](#disconnect)
- [ClaudeSDKClient-Only Features](#claudesdkclient-only-features)
- [Message Types Specific to Client](#message-types-specific-to-client)
- [Common Patterns](#common-patterns)
- [Quick Reference Tables](#quick-reference-tables)

---

## What is ClaudeSDKClient?

`ClaudeSDKClient` is a **stateful, bidirectional client** for multi-turn conversations with Claude. Unlike `query()` (fire-and-forget), the client keeps a persistent connection open and lets you:

- Send multiple messages back and forth (full conversation state)
- React to Claude's responses with follow-ups
- Interrupt Claude mid-execution
- Change model or permission mode mid-conversation
- Use the `AskUserQuestion` tool (human-in-the-loop)
- Manage MCP servers dynamically
- Rewind file changes to a checkpoint

**Use `ClaudeSDKClient` when:**
- Multi-turn conversation needed
- Need to ask user questions (`AskUserQuestion` tool)
- Building a chat application or interactive CLI
- Need to interrupt/cancel mid-execution
- Need to switch model during a conversation (cheap analysis → quality execution)
- Need file undo capability

**Use `query()` instead when:** inputs are known upfront, one-shot tasks, CI/CD scripts. See [query() reference](16-query-and-messages.md).

---

## How It Works Under the Hood

```
Your Python script ←→ ClaudeSDKClient ←→ Claude Code CLI subprocess ←→ Claude API
                       (persistent connection, bidirectional stdin/stdout)
```

The client spawns a Claude Code CLI process and maintains a persistent pipe:
- **You → Claude:** `client.query("...")` writes to CLI's stdin
- **Claude → You:** `client.receive_response()` reads from CLI's stdout
- **Control signals:** `client.interrupt()`, `client.set_permission_mode()`, etc. send control messages

**Lifecycle flow:**

```
1. CREATE:     client = ClaudeSDKClient(options=options)
2. CONNECT:    async with client:       → starts CLI subprocess
3. SEND:       await client.query("your prompt")
4. RECEIVE:    async for msg in client.receive_response():
5. REPEAT:     → go to step 3 for follow-ups
6. DISCONNECT: → automatic with 'async with'
```

---

## Constructor

```python
client = ClaudeSDKClient(
    options: ClaudeAgentOptions | None = None,
    transport: Transport | None = None,
)
```

**`options`** — same `ClaudeAgentOptions` used by `query()`. All 38 parameters work. See [Configuration](01-configuration.md).

```python
options = ClaudeAgentOptions(
    model="sonnet",
    env={"ANTHROPIC_API_KEY": API_KEY},
    allowed_tools=["Read", "Glob", "Grep", "AskUserQuestion"],
    permission_mode="bypassPermissions",
    max_turns=10,
)
client = ClaudeSDKClient(options=options)
```

**`transport`** — custom transport. Only for advanced use cases (custom communication layers). Ignore for normal usage.

---

## Lifecycle — connect, use, disconnect

### Option A: `async with` (Recommended)

Auto-connects on enter, auto-disconnects on exit — even if errors occur.

```python
async with ClaudeSDKClient(options=options) as client:
    # client is connected here
    await client.query("Hello!")
    async for msg in client.receive_response():
        ...

    await client.query("Follow-up question")
    async for msg in client.receive_response():
        ...
# client is automatically disconnected here
```

### Option B: Manual connect/disconnect

More control, but YOU must handle cleanup.

```python
client = ClaudeSDKClient(options=options)
try:
    await client.connect()
    await client.query("Hello!")
    async for msg in client.receive_response():
        ...
finally:
    await client.disconnect()  # always in finally block
```

### Important: Same Async Context

The client must be used within the same async context where it was created. Do not pass it between different asyncio tasks or event loops.

```python
# CORRECT — same async context
async def main():
    async with ClaudeSDKClient(options=options) as client:
        await client.query("Hello")
        async for msg in client.receive_response():
            ...

# WRONG — do not pass across tasks/event loops
client = ClaudeSDKClient(options=options)
# Don't try to use this client in different asyncio tasks
```

---

## All 14 Methods

### `connect()`

```python
await client.connect(prompt: str | AsyncIterable | None = None)
```

Starts the Claude Code CLI subprocess and establishes the bidirectional connection.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prompt` | `str \| AsyncIterable \| None` | `None` | Optional initial prompt |

```python
# Auto-connect (recommended — via async with)
async with ClaudeSDKClient(options=options) as client:
    ...  # already connected

# Manual connect — no initial prompt
await client.connect()

# Manual connect — with initial prompt (equivalent to connect() + query(prompt))
await client.connect(prompt="Analyze this codebase")
```

**When to use:** Automatically called by `async with`. Only call manually if not using context manager.

---

### `query()`

```python
await client.query(prompt: str | AsyncIterable, session_id: str = "default")
```

Send a message to Claude. **Non-blocking** — sends and returns immediately. You must call `receive_response()` after.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prompt` | `str \| AsyncIterable` | required | Your message to Claude |
| `session_id` | `str` | `"default"` | Session identifier |

```python
# Send a message
await client.query("What files are in this project?")

# Follow-up (Claude remembers previous context)
await client.query("Now fix the bug in app.py")

# Another follow-up
await client.query("Run the tests to verify the fix")
```

**Critical:** `query()` does NOT return the response — call `receive_response()` after:

```python
await client.query("Hello")                    # sends message
async for msg in client.receive_response():    # receives response
    ...
```

**When NOT to use** as a standalone call without `receive_response()`: the messages will queue up and be consumed by the next `receive_response()` call, which can cause confusion.

---

### `receive_messages()`

```python
async for msg in client.receive_messages():
    ...
```

**Low-level** — yields ALL messages indefinitely. Does NOT stop at `ResultMessage`. Runs forever unless you break.

```python
# You must break manually
async for msg in client.receive_messages():
    if isinstance(msg, AssistantMessage):
        ...
    elif isinstance(msg, ResultMessage):
        break  # YOU must break, or it runs forever
```

**When to use:** Advanced cases where you need to process messages across multiple query/response cycles.

**When NOT to use:** For normal single-response workflows — use `receive_response()` instead.

---

### `receive_response()`

```python
async for msg in client.receive_response():
    ...
```

**High-level** — yields messages until a `ResultMessage` is received, then **automatically stops**. This is what you want almost always.

```python
await client.query("Explain Python decorators")

async for msg in client.receive_response():
    if isinstance(msg, AssistantMessage):
        for block in msg.content:
            if isinstance(block, TextBlock):
                print(block.text)
            elif isinstance(block, ToolUseBlock):
                print(f"[Tool] {block.name}")
    elif isinstance(msg, ResultMessage):
        print(f"Cost: ${msg.total_cost_usd:.4f}")
        # Iterator automatically stops here
```

**`receive_messages()` vs `receive_response()`:**
- `receive_response()` — stops after `ResultMessage` (one response cycle) ← use this
- `receive_messages()` — runs forever (you must break manually) ← advanced only

---

### `interrupt()`

```python
await client.interrupt()
```

Send an interrupt signal to stop Claude mid-execution. Like pressing Ctrl+C.

```python
import asyncio

async with ClaudeSDKClient(options=options) as client:
    await client.query("Refactor every file in this large project")

    start = asyncio.get_event_loop().time()
    async for msg in client.receive_response():
        elapsed = asyncio.get_event_loop().time() - start
        if elapsed > 30:
            print("Taking too long — interrupting!")
            await client.interrupt()
            continue  # keep consuming to get the final ResultMessage

        if isinstance(msg, AssistantMessage):
            ...
        elif isinstance(msg, ResultMessage):
            print(f"Done (interrupted): ${msg.total_cost_usd:.4f}")
```

**When to use:** User clicks "Stop" in a chat UI, task taking too long, got enough information.

**What happens after interrupt:**
- Claude stops working
- A `ResultMessage` is emitted with what was completed
- You CAN still send new queries on the same client

---

### `set_permission_mode()`

```python
await client.set_permission_mode(mode: PermissionMode)
```

Change permissions mid-conversation. Useful for plan-then-execute workflows.

| Parameter | Type | Options |
|-----------|------|---------|
| `mode` | `PermissionMode` | `"default"`, `"acceptEdits"`, `"plan"`, `"bypassPermissions"`, `"dontAsk"` |

```python
options = ClaudeAgentOptions(
    model="sonnet",
    env={"ANTHROPIC_API_KEY": API_KEY},
    allowed_tools=["Read", "Glob", "Grep", "Write", "Edit", "ExitPlanMode"],
    permission_mode="plan",   # start in plan mode — no writes allowed
    max_turns=10,
)

async with ClaudeSDKClient(options=options) as client:
    # Phase 1: Plan (Claude reads and proposes, cannot edit)
    await client.query("Analyze app.py and plan what changes to make")
    async for msg in client.receive_response():
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    print(f"[PLAN] {block.text}")

    # User approves → switch to execution mode
    approve = input("Approve this plan? (yes/no): ")
    if approve.lower() == "yes":
        await client.set_permission_mode("bypassPermissions")
        await client.query("Now execute the plan you just made")
        async for msg in client.receive_response():
            ...  # Claude makes actual changes
```

**When to use:** "Preview before commit" workflows, progressive trust escalation.

**Only works with `ClaudeSDKClient`** — cannot do this with `query()`.

---

### `set_model()`

```python
await client.set_model(model: str | None = None)
```

Switch to a different model mid-conversation. Conversation context is preserved.

```python
async with ClaudeSDKClient(options=options) as client:
    # Phase 1: Quick analysis with haiku (fast + cheap)
    await client.set_model("haiku")
    await client.query("List all files in the project")
    async for msg in client.receive_response():
        ...

    # Phase 2: Complex refactoring with opus (best quality)
    await client.set_model("opus")
    await client.query("Now refactor the authentication module")
    async for msg in client.receive_response():
        ...
```

**When to use:**
- Cheap model (haiku) for simple tasks, expensive model (opus) for complex ones
- Start with fast model for exploration, switch to better model for execution

**Only works with `ClaudeSDKClient`** — cannot do this with `query()`.

---

### `rewind_files()`

```python
await client.rewind_files(user_message_id: str)
```

Rewind all tracked files to their state at a specific point in the conversation. Like "git undo" for file changes.

**Requires in options:**
- `enable_file_checkpointing=True`
- `extra_args={"replay-user-messages": None}` to get `UserMessage` UUIDs

```python
from claude_agent_sdk import UserMessage

options = ClaudeAgentOptions(
    model="sonnet",
    env={"ANTHROPIC_API_KEY": API_KEY},
    allowed_tools=["Read", "Write", "Edit"],
    permission_mode="bypassPermissions",
    max_turns=10,
    enable_file_checkpointing=True,
    extra_args={"replay-user-messages": None},
)

checkpoint = None

async with ClaudeSDKClient(options=options) as client:
    await client.query("Refactor app.py to use async/await everywhere")
    async for msg in client.receive_response():
        if isinstance(msg, UserMessage) and msg.uuid:
            checkpoint = msg.uuid   # save checkpoint before changes

    # Review the changes — decide you don't like them
    undo = input("Revert changes? (yes/no): ")
    if undo.lower() == "yes" and checkpoint:
        await client.rewind_files(checkpoint)
        print("Files rewound!")
```

**When to use:** When Claude makes changes you want to undo.

**What rewind does NOT undo:** Bash commands, external API calls, database operations.

**Only works with `ClaudeSDKClient`** — cannot do this with `query()`.

---

### `get_mcp_status()`

```python
status = await client.get_mcp_status()
```

Get the connection status of all MCP servers.

**Returns:** `McpStatusResponse` — dict with `mcpServers` list.

| Server Field | Type | Description |
|---|---|---|
| `name` | `str` | Server name |
| `status` | `str` | `"connected"`, `"pending"`, `"failed"`, `"needs-auth"`, `"disabled"` |
| `serverInfo` | `dict` | Name/version (when connected) |
| `error` | `str` | Error message (when failed) |
| `tools` | `list` | Available tools (when connected) |

```python
async with ClaudeSDKClient(options=options) as client:
    status = await client.get_mcp_status()

    for server in status["mcpServers"]:
        print(f"{server['name']}: {server['status']}")
        if server["status"] == "connected":
            tools = server.get("tools", [])
            print(f"  Tools: {[t['name'] for t in tools]}")
        elif server["status"] == "failed":
            print(f"  Error: {server.get('error')}")
```

**When to use:** Debugging MCP connections, health checks, before relying on custom tools.

---

### `reconnect_mcp_server()`

```python
await client.reconnect_mcp_server(server_name: str)
```

Retry connecting to a failed or disconnected MCP server.

```python
status = await client.get_mcp_status()
for server in status["mcpServers"]:
    if server["status"] == "failed":
        print(f"Reconnecting {server['name']}...")
        await client.reconnect_mcp_server(server["name"])
```

**When to use:** An MCP server fails during a conversation and you want to retry without restarting.

---

### `toggle_mcp_server()`

```python
await client.toggle_mcp_server(server_name: str, enabled: bool)
```

Enable or disable an MCP server mid-conversation.

```python
# Disable temporarily — Claude can't use db tools in this phase
await client.toggle_mcp_server("my-db-server", enabled=False)
await client.query("Do analysis without database access")
async for msg in client.receive_response():
    ...

# Re-enable
await client.toggle_mcp_server("my-db-server", enabled=True)
await client.query("Now query the database")
async for msg in client.receive_response():
    ...
```

**When to use:** Temporarily restricting tool access during specific phases without restarting.

---

### `stop_task()`

```python
await client.stop_task(task_id: str)
```

Stop a running sub-agent task (spawned by the `Agent` tool).

```python
from claude_agent_sdk import TaskStartedMessage, TaskNotificationMessage
import asyncio

async with ClaudeSDKClient(options=options) as client:
    await client.query("Run code review on all 50 files")

    async for msg in client.receive_response():
        if isinstance(msg, TaskStartedMessage):
            task_id = msg.task_id
            print(f"Task started: {task_id}")
            # Stop if taking too long
            await asyncio.sleep(30)
            await client.stop_task(task_id)

        elif isinstance(msg, TaskNotificationMessage):
            if msg.status == "stopped":
                print(f"Task {msg.task_id} was stopped")
```

**When to use:** Cancelling sub-agent tasks that are running too long or are no longer needed.

---

### `get_server_info()`

```python
info = await client.get_server_info()
```

Get server initialization info including available commands and output styles.

**Returns:** `dict | None`

```python
async with ClaudeSDKClient(options=options) as client:
    info = await client.get_server_info()
    if info:
        print(f"Commands: {len(info.get('commands', []))}")
        print(f"Output style: {info.get('output_style', 'default')}")
```

**When to use:** Rarely. Only for introspecting what the Claude Code CLI supports.

---

### `disconnect()`

```python
await client.disconnect()
```

Close the connection and clean up the CLI subprocess.

```python
# Automatic (recommended) — use async with
async with ClaudeSDKClient(options=options) as client:
    ...
# disconnect() called automatically

# Manual — always in a finally block
client = ClaudeSDKClient(options=options)
await client.connect()
try:
    ...
finally:
    await client.disconnect()
```

**When to use:** Only with manual connect. `async with` handles this for you.

---

## ClaudeSDKClient-Only Features

These capabilities are NOT available in `query()`:

| Feature | Method | Use Case |
|---------|--------|----------|
| Multi-turn chat | `query()` multiple times | Chat apps, interactive workflows |
| Human-in-the-loop | Handle `AskUserQuestion` tool | User provides input mid-execution |
| Interrupt | `interrupt()` | Stop long-running tasks |
| Change model mid-session | `set_model()` | Cheap analysis → quality execution |
| Change permissions mid-session | `set_permission_mode()` | Plan → review → execute |
| File undo | `rewind_files()` | Revert unwanted changes |
| MCP management | `get_mcp_status()`, `reconnect_mcp_server()`, `toggle_mcp_server()` | Dynamic server control |
| Stop sub-agents | `stop_task()` | Cancel sub-agent tasks |

---

## Message Types Specific to Client

Beyond the standard types (see [query() and Messages](16-query-and-messages.md)), the client surfaces these:

| Type | When you see it |
|------|----------------|
| `UserMessage` | Your messages echoed back (when `replay-user-messages` extra_arg set) — needed for `rewind_files()` |
| `TaskStartedMessage` | Sub-agent task launched by `Agent` tool |
| `TaskProgressMessage` | Sub-agent progress update |
| `TaskNotificationMessage` | Sub-agent done/failed/stopped |
| `RateLimitEvent` | Rate limit warning/rejection — add backoff |

**Standard client message handling:**

```python
async for msg in client.receive_response():
    if isinstance(msg, AssistantMessage):
        for block in msg.content:
            if isinstance(block, TextBlock):
                print(f"Claude: {block.text}")
            elif isinstance(block, ToolUseBlock):
                if block.name == "AskUserQuestion":
                    question = block.input.get("question", "")
                    options_list = block.input.get("options", [])
                    print(f"Claude asks: {question}")
                    if options_list:
                        for i, opt in enumerate(options_list, 1):
                            print(f"  {i}. {opt}")
                    answer = input("> ")
                    await client.query(answer)   # send reply back
                else:
                    print(f"  [used {block.name}]")
    elif isinstance(msg, ResultMessage):
        print(f"Done: ${msg.total_cost_usd:.4f} | {msg.num_turns} turns")
```

---

## Common Patterns

### Pattern 1: Simple Multi-Turn Conversation

```python
import asyncio
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AssistantMessage, ResultMessage, TextBlock

options = ClaudeAgentOptions(
    model="sonnet",
    env={"ANTHROPIC_API_KEY": API_KEY},
    allowed_tools=["Read", "Glob"],
    permission_mode="bypassPermissions",
    max_turns=5,
)

async def main():
    async with ClaudeSDKClient(options=options) as client:
        # Turn 1
        await client.query("List all Python files in this project")
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(block.text)

        # Turn 2 — Claude remembers Turn 1
        await client.query("Which of those files has the most lines?")
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(block.text)

asyncio.run(main())
```

### Pattern 2: Human-in-the-Loop (AskUserQuestion)

```python
options = ClaudeAgentOptions(
    model="sonnet",
    env={"ANTHROPIC_API_KEY": API_KEY},
    allowed_tools=["Read", "Glob", "AskUserQuestion"],
    permission_mode="bypassPermissions",
    max_turns=10,
)

async def main():
    async with ClaudeSDKClient(options=options) as client:
        await client.query("List files in sample_data/ and ask which one to analyze.")

        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, ToolUseBlock) and block.name == "AskUserQuestion":
                        question = block.input.get("question", "")
                        print(f"\nClaude asks: {question}")
                        answer = input("> Your answer: ")
                        await client.query(answer)
                    elif isinstance(block, TextBlock):
                        print(block.text)

        # Second receive_response() gets the answer-based response
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(block.text)

asyncio.run(main())
```

### Pattern 3: Plan Then Execute

```python
options = ClaudeAgentOptions(
    model="sonnet",
    env={"ANTHROPIC_API_KEY": API_KEY},
    allowed_tools=["Read", "Glob", "Grep", "Write", "Edit", "ExitPlanMode"],
    permission_mode="plan",          # start read-only
    max_turns=10,
)

async def main():
    async with ClaudeSDKClient(options=options) as client:
        await client.query("Analyze app.py and plan fixes for all bugs")
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"[PLAN] {block.text}")

        approve = input("\nApprove this plan? (yes/no): ")
        if approve.lower() == "yes":
            await client.set_permission_mode("bypassPermissions")
            await client.query("Execute the plan you just made")
            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            print(f"[EXEC] {block.text}")

asyncio.run(main())
```

### Pattern 4: Model Switching (Cheap Analysis → Quality Execution)

```python
options = ClaudeAgentOptions(
    model="haiku",                    # start cheap
    env={"ANTHROPIC_API_KEY": API_KEY},
    allowed_tools=["Read", "Glob", "Grep", "Write", "Edit"],
    permission_mode="bypassPermissions",
    max_turns=15,
)

async def main():
    async with ClaudeSDKClient(options=options) as client:
        # Phase 1: Quick scan with haiku (fast + cheap)
        await client.query("Scan the codebase for TODO comments and security issues")
        async for msg in client.receive_response():
            ...

        # Phase 2: Switch to opus for complex refactoring
        await client.set_model("opus")
        await client.query("Now fix the critical security issues you found")
        async for msg in client.receive_response():
            ...

asyncio.run(main())
```

### Pattern 5: Interrupt Long-Running Task

```python
import asyncio

options = ClaudeAgentOptions(
    model="sonnet",
    env={"ANTHROPIC_API_KEY": API_KEY},
    allowed_tools=["Read", "Glob", "Grep", "Bash"],
    permission_mode="bypassPermissions",
    max_turns=50,
)

async def main():
    async with ClaudeSDKClient(options=options) as client:
        await client.query("Run comprehensive analysis on every file in the project")

        start = asyncio.get_event_loop().time()
        async for msg in client.receive_response():
            elapsed = asyncio.get_event_loop().time() - start
            if elapsed > 30:
                print("Taking too long — interrupting!")
                await client.interrupt()
                continue

            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(block.text[:200])
            elif isinstance(msg, ResultMessage):
                print(f"Done: ${msg.total_cost_usd:.4f}")

asyncio.run(main())
```

### Pattern 6: File Checkpointing (Undo Changes)

```python
from claude_agent_sdk import UserMessage

options = ClaudeAgentOptions(
    model="sonnet",
    env={"ANTHROPIC_API_KEY": API_KEY},
    allowed_tools=["Read", "Write", "Edit"],
    permission_mode="bypassPermissions",
    max_turns=10,
    enable_file_checkpointing=True,
    extra_args={"replay-user-messages": None},
)

async def main():
    checkpoint = None
    async with ClaudeSDKClient(options=options) as client:
        await client.query("Refactor app.py to use async/await everywhere")
        async for msg in client.receive_response():
            if isinstance(msg, UserMessage) and msg.uuid:
                checkpoint = msg.uuid   # save checkpoint
            elif isinstance(msg, ResultMessage):
                ...

        undo = input("Revert changes? (yes/no): ")
        if undo.lower() == "yes" and checkpoint:
            await client.rewind_files(checkpoint)
            print("Files rewound!")

asyncio.run(main())
```

### Pattern 7: MCP Server Health Check + Auto-Reconnect

```python
options = ClaudeAgentOptions(
    model="sonnet",
    env={"ANTHROPIC_API_KEY": API_KEY},
    mcp_servers={"db": db_server, "api": api_server},
    allowed_tools=["mcp__db__*", "mcp__api__*"],
    permission_mode="bypassPermissions",
    max_turns=10,
)

async def main():
    async with ClaudeSDKClient(options=options) as client:
        # Check health before using tools
        status = await client.get_mcp_status()
        for server in status["mcpServers"]:
            name, state = server["name"], server["status"]
            print(f"{name}: {state}")
            if state == "failed":
                print(f"  Reconnecting {name}...")
                await client.reconnect_mcp_server(name)

        # Now use the tools
        await client.query("Query the database for recent orders")
        async for msg in client.receive_response():
            ...

asyncio.run(main())
```

### Pattern 8: Interactive Chat Loop

```python
options = ClaudeAgentOptions(
    model="sonnet",
    env={"ANTHROPIC_API_KEY": API_KEY},
    allowed_tools=["Read", "Glob", "Grep", "Write", "Edit", "Bash"],
    permission_mode="bypassPermissions",
    max_turns=10,
)

async def main():
    async with ClaudeSDKClient(options=options) as client:
        print("Chat with Claude (type 'exit' to quit)\n")

        while True:
            user_input = input("You: ").strip()
            if user_input.lower() == "exit":
                break
            if not user_input:
                continue

            await client.query(user_input)
            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            print(f"Claude: {block.text}")
                        elif isinstance(block, ToolUseBlock):
                            print(f"  [used {block.name}]")
                elif isinstance(msg, ResultMessage):
                    print(f"  (${msg.total_cost_usd:.4f})\n")

asyncio.run(main())
```

---

## Quick Reference Tables

### All 14 Methods

| # | Method | Returns | Description |
|---|--------|---------|-------------|
| 1 | `connect(prompt?)` | `None` | Start CLI process, establish connection |
| 2 | `query(prompt, session_id?)` | `None` | Send message (non-blocking — call receive_response() after) |
| 3 | `receive_messages()` | `AsyncIterator[Message]` | Yield ALL messages (never stops — you must break) |
| 4 | `receive_response()` | `AsyncIterator[Message]` | Yield messages until ResultMessage (auto-stops) |
| 5 | `interrupt()` | `None` | Stop Claude mid-execution |
| 6 | `set_permission_mode(mode)` | `None` | Change permissions mid-conversation |
| 7 | `set_model(model)` | `None` | Switch model mid-conversation |
| 8 | `rewind_files(msg_id)` | `None` | Undo file changes to a checkpoint |
| 9 | `get_mcp_status()` | `McpStatusResponse` | Check MCP server connection states |
| 10 | `reconnect_mcp_server(name)` | `None` | Retry failed MCP connection |
| 11 | `toggle_mcp_server(name, bool)` | `None` | Enable/disable MCP server |
| 12 | `stop_task(task_id)` | `None` | Cancel a running sub-agent task |
| 13 | `get_server_info()` | `dict \| None` | Get CLI server capabilities |
| 14 | `disconnect()` | `None` | Close connection and cleanup |

### Typical Usage Flow

```
1.  Create options         → ClaudeAgentOptions(model=..., env=..., ...)
2.  Create client          → ClaudeSDKClient(options=options)
3.  Connect                → async with client: (or await client.connect())
4.  Send first message     → await client.query("...")
5.  Receive response       → async for msg in client.receive_response(): ...
6.  Handle AskUserQuestion → if block.name == "AskUserQuestion": ... await client.query(answer)
7.  Receive again          → async for msg in client.receive_response(): ...
8.  Send follow-up         → await client.query("follow-up...")
9.  Receive response       → async for msg in client.receive_response(): ...
10. Disconnect             → automatic with async with
```

### Minimum Viable Client

```python
import asyncio
from claude_agent_sdk import (
    ClaudeSDKClient, ClaudeAgentOptions,
    AssistantMessage, ResultMessage, TextBlock,
)

options = ClaudeAgentOptions(
    model="sonnet",
    env={"ANTHROPIC_API_KEY": "sk-..."},
    permission_mode="bypassPermissions",
    max_turns=5,
)

async def main():
    async with ClaudeSDKClient(options=options) as client:
        await client.query("Hello, Claude!")
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(block.text)
            elif isinstance(msg, ResultMessage):
                print(f"Cost: ${msg.total_cost_usd:.4f}")

asyncio.run(main())
```

---

## Related Topics

- [query() and Messages](16-query-and-messages.md) — query() function, AssistantMessage/ResultMessage fields, patterns
- [Configuration](01-configuration.md) — All 38 ClaudeAgentOptions parameters
- [Sessions](07-sessions.md) — Resume, fork, session storage, session management functions
- [User Input](12-user-input.md) — AskUserQuestion in depth, approval flows, canUseTool
- [Permissions](06-permissions.md) — Permission modes, evaluation order, security
- [Hooks](05-hooks.md) — Intercept tool execution at key lifecycle points
- [Subagents](08-subagents.md) — AgentDefinition, spawning, stop_task
