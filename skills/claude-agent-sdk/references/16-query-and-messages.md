# Claude Agent SDK — query() Function & Message Types

> Source: [platform.claude.com/docs/en/agent-sdk](https://platform.claude.com/docs/en/agent-sdk/overview) — Python v0.1.51, TypeScript v0.2.86

## Contents

- [What is query()?](#what-is-query)
- [Function Signature](#function-signature)
- [query() Parameters](#query-parameters)
- [query() vs ClaudeSDKClient — When to Use Which](#query-vs-claudesdkclient--when-to-use-which)
- [Message Types — What Comes Back](#message-types--what-comes-back)
  - [AssistantMessage](#assistantmessage)
  - [Content Blocks](#content-blocks)
  - [ResultMessage](#resultmessage)
  - [Other Message Types](#other-message-types)
- [Minimum Viable Options (3 levels)](#minimum-viable-options)
- [Permission Priority Diagram](#permission-priority-diagram)
- [Common Patterns](#common-patterns)
- [Related Topics](#related-topics)

---

## What is query()?

`query()` is a **one-shot async function** — you send a prompt, Claude processes it (optionally calling tools), and you iterate over messages as they arrive. That's it. No connection management, no follow-ups.

```
You send a prompt → Claude works (may call tools) → You receive messages → Done.
```

**Key characteristics:**
- **Stateless** — each call is independent, no memory between calls
- **Unidirectional** — send everything upfront, then receive
- **No follow-ups** — cannot send additional messages after the query starts
- **No interrupts** — cannot stop Claude mid-execution
- **Simple** — no connection or session handling

**Think of it as:** `query()` = sending an email. `ClaudeSDKClient` = having a phone call.

---

## Function Signature

```python
async def query(
    *,
    prompt: str | AsyncIterable[dict[str, Any]],
    options: ClaudeAgentOptions | None = None,
    transport: Transport | None = None,
) -> AsyncIterator[Message]
```

- `*` means all parameters are **keyword-only** — you must use `prompt=`, `options=`
- Returns an **async iterator** — iterate with `async for`
- If `options` is omitted, defaults to `ClaudeAgentOptions()` (all defaults)

**TypeScript:**

```typescript
function query(params: {
  prompt: string | AsyncIterable<...>;
  options?: Options;
}): AsyncIterable<Message>
```

---

## query() Parameters

### `prompt` (required)

What you want Claude to do.

**Simple string (99% of the time):**

```python
async for msg in query(prompt="Explain Python decorators"):
    ...
```

**AsyncIterable (streaming input — advanced):**

```python
async def prompts():
    yield {"type": "user", "message": {"role": "user", "content": "Hello"}}
    yield {"type": "user", "message": {"role": "user", "content": "How are you?"}}

async for msg in query(prompt=prompts()):
    ...
```

You will almost always use a simple string. AsyncIterable is for advanced streaming pipelines.

### `options` (optional)

A `ClaudeAgentOptions` instance controlling model, tools, permissions, cost limits, etc. See [Configuration](01-configuration.md) for all 38 parameters.

```python
options = ClaudeAgentOptions(
    model="sonnet",
    env={"ANTHROPIC_API_KEY": "sk-..."},
    allowed_tools=["Read", "Bash"],
    permission_mode="bypassPermissions",
    max_turns=5,
)
async for msg in query(prompt="...", options=options):
    ...
```

### `transport` (optional)

Custom transport implementation. Only needed for building a custom communication layer. Ignore for normal usage.

---

## query() vs ClaudeSDKClient — When to Use Which

| Feature | `query()` | `ClaudeSDKClient` |
|---------|-----------|-------------------|
| **Style** | One-shot function | Stateful class (async context manager) |
| **State** | Stateless — each call independent | Stateful — remembers full conversation |
| **Follow-ups** | Cannot send follow-up messages | Send as many as you want |
| **Interrupt** | Cannot interrupt | `client.interrupt()` stops Claude |
| **AskUserQuestion** | Does NOT work (no way to reply) | Works — human-in-the-loop |
| **Change model mid-chat** | No | `client.set_model("opus")` |
| **Change permissions** | No | `client.set_permission_mode("plan")` |
| **MCP server management** | Static only | Dynamic — reconnect, toggle, check status |
| **File rewind** | No | `client.rewind_files(checkpoint_id)` |
| **Connection** | Auto-managed | You manage with `async with` or `connect()`/`disconnect()` |
| **Best for** | Scripts, CI/CD, batch jobs | Chat apps, interactive agents, complex workflows |

**Use `query()` when:** inputs are known upfront, no back-and-forth needed, automated scripts.

**Use `ClaudeSDKClient` when:** multi-turn conversation, AskUserQuestion, interrupt/cancel, chat apps, dynamic MCP management. See [ClaudeSDKClient](17-client.md).

---

## Message Types — What Comes Back

`query()` yields different message types as Claude works. Iterate with `async for`:

```python
async for msg in query(prompt="...", options=options):
    if isinstance(msg, AssistantMessage):
        ...
    elif isinstance(msg, ResultMessage):
        ...
```

### AssistantMessage

Claude's response — contains text and/or tool calls.

```python
@dataclass
class AssistantMessage:
    content: list[ContentBlock]      # text, tool calls, thinking blocks
    model: str                       # model used (e.g., "claude-sonnet-4-6")
    parent_tool_use_id: str | None   # for sub-agent responses
    error: str | None                # error type if message failed
    usage: dict | None               # token counts for this message
    message_id: str | None           # unique message ID
    stop_reason: str | None          # why this message ended
    session_id: str | None           # session ID
```

**TypeScript:**

```typescript
interface AssistantMessage {
  type: "assistant";
  content: ContentBlock[];
  model: string;
  usage?: { inputTokens: number; outputTokens: number };
}
```

---

### Content Blocks

`AssistantMessage.content` is a list of content blocks — one of three types:

#### TextBlock

```python
@dataclass
class TextBlock:
    type: Literal["text"] = "text"
    text: str                        # Claude's words
```

```python
for block in msg.content:
    if isinstance(block, TextBlock):
        print(block.text)
```

#### ToolUseBlock

```python
@dataclass
class ToolUseBlock:
    type: Literal["tool_use"] = "tool_use"
    id: str                          # unique tool call ID
    name: str                        # tool name: "Read", "Bash", "mcp__server__tool"
    input: dict[str, Any]            # tool arguments
```

```python
for block in msg.content:
    if isinstance(block, ToolUseBlock):
        print(f"Tool: {block.name}")
        print(f"Args: {block.input}")
        # e.g. name="Read", input={"file_path": "/src/app.py"}
```

**Special case — AskUserQuestion tool:**

```python
if isinstance(block, ToolUseBlock) and block.name == "AskUserQuestion":
    question = block.input.get("question", "")
    options_list = block.input.get("options", [])
    # Only works with ClaudeSDKClient — you must call client.query(answer)
```

#### ThinkingBlock

```python
@dataclass
class ThinkingBlock:
    type: Literal["thinking"] = "thinking"
    thinking: str                    # Claude's internal reasoning
    signature: str                   # thinking block signature
```

Only present when `thinking` is enabled in `ClaudeAgentOptions`. Treat as read-only — Claude's scratchpad.

---

### ResultMessage

Final summary — **always the last message** from `query()`.

```python
@dataclass
class ResultMessage:
    subtype: str                       # see subtypes below
    duration_ms: int                   # total wall time in milliseconds
    duration_api_ms: int               # time spent on API calls
    is_error: bool                     # did the query fail?
    num_turns: int                     # how many tool-use cycles
    session_id: str                    # save this for resume
    stop_reason: str | None            # "end_turn", "max_turns", "max_budget", etc.
    total_cost_usd: float | None       # total cost in USD
    usage: dict | None                 # aggregate token counts
    result: str | None                 # final text result
    structured_output: Any             # if output_format was set
    model_usage: dict | None           # per-model token breakdown
    permission_denials: list | None    # tools that were denied
    errors: list[str] | None           # error messages
```

**`subtype` values:**

| Subtype | Meaning |
|---------|---------|
| `"success"` | Agent completed normally |
| `"error_max_turns"` | Hit the `max_turns` limit |
| `"error_max_budget_usd"` | Hit the `max_budget_usd` limit |
| `"error_during_execution"` | Tool execution error |
| `"error_max_structured_output_retries"` | Structured output validation failed repeatedly |

**Standard ResultMessage handling:**

```python
async for msg in query(prompt="...", options=options):
    if isinstance(msg, ResultMessage):
        print(f"Cost:    ${msg.total_cost_usd:.4f}")
        print(f"Turns:   {msg.num_turns}")
        print(f"Time:    {msg.duration_ms}ms")
        print(f"Session: {msg.session_id}")
        if msg.is_error:
            print(f"ERRORS: {msg.errors}")
        if msg.structured_output:
            data = msg.structured_output   # parsed JSON matching your output_format schema
```

---

### Other Message Types

| Type | When you see it | Should you handle it? |
|------|----------------|----------------------|
| `UserMessage` | Your messages echoed back (streaming mode) | Rarely — only when `replay-user-messages` is set |
| `SystemMessage` | Internal SDK events (task started, init) | Usually ignore |
| `TaskStartedMessage` | Sub-agent task started (subclass of SystemMessage) | If using `Agent` tool |
| `TaskProgressMessage` | Sub-agent progress update | If using `Agent` tool |
| `TaskNotificationMessage` | Sub-agent done/failed/stopped | If using `Agent` tool |
| `StreamEvent` | Partial tokens (raw Anthropic API events) | Only when `include_partial_messages=True` |
| `RateLimitEvent` | Rate limit warning or rejection | In production — add backoff handling |

**Minimal message handling (covers 99% of cases):**

```python
async for msg in query(prompt="...", options=options):
    if isinstance(msg, AssistantMessage):
        for block in msg.content:
            if isinstance(block, TextBlock):
                print(block.text)
            elif isinstance(block, ToolUseBlock):
                print(f"[Tool] {block.name}({block.input})")
    elif isinstance(msg, ResultMessage):
        print(f"[Done] ${msg.total_cost_usd:.4f} | {msg.num_turns} turns")
```

---

## Minimum Viable Options

```python
# Level 1 — Absolute minimum (just answer a question, no tools)
ClaudeAgentOptions(
    model="sonnet",
    env={"ANTHROPIC_API_KEY": API_KEY},
)

# Level 2 — With tools (typical setup)
ClaudeAgentOptions(
    model="sonnet",
    env={"ANTHROPIC_API_KEY": API_KEY},
    allowed_tools=["Read", "Glob", "Grep"],
    permission_mode="bypassPermissions",
    max_turns=5,
)

# Level 3 — Production with safety limits
ClaudeAgentOptions(
    model="sonnet",
    env={"ANTHROPIC_API_KEY": API_KEY},
    allowed_tools=["Read", "Glob", "Grep"],
    disallowed_tools=["Bash"],
    permission_mode="default",
    max_turns=10,
    max_budget_usd=1.00,
    cwd="/path/to/project",
)
```

---

## Permission Priority Diagram

When Claude wants to use a tool, evaluation happens in this order:

```
disallowed_tools   →  ALWAYS BLOCKED  (highest priority — overrides everything)
       ↓
allowed_tools      →  AUTO-APPROVED   (no permission prompt)
       ↓
can_use_tool       →  CUSTOM CALLBACK  (your function decides)
       ↓
permission_mode    →  FALLBACK         (lowest priority)
```

**Example:**

```python
options = ClaudeAgentOptions(
    allowed_tools=["Read", "Glob"],        # auto-approved
    disallowed_tools=["Bash"],             # BLOCKED even if bypassPermissions
    permission_mode="bypassPermissions",   # everything else auto-approved
)
# Read → allowed (in allowed_tools)
# Glob → allowed (in allowed_tools)
# Write → allowed (bypassPermissions)
# Edit → allowed (bypassPermissions)
# Bash → BLOCKED (disallowed_tools overrides bypassPermissions)
```

---

## Common Patterns

### Pattern 1: Simple Question (No Tools)

```python
options = ClaudeAgentOptions(
    model="sonnet",
    env={"ANTHROPIC_API_KEY": API_KEY},
    max_turns=1,
    permission_mode="bypassPermissions",
)

async for msg in query(prompt="What is Python's GIL?", options=options):
    if isinstance(msg, AssistantMessage):
        for block in msg.content:
            if isinstance(block, TextBlock):
                print(block.text)
```

### Pattern 2: File Analysis (Read-Only)

```python
options = ClaudeAgentOptions(
    model="sonnet",
    env={"ANTHROPIC_API_KEY": API_KEY},
    allowed_tools=["Read", "Glob", "Grep"],
    disallowed_tools=["Write", "Edit", "Bash"],  # hard block writes
    permission_mode="bypassPermissions",
    max_turns=10,
    max_budget_usd=0.10,
    cwd="/path/to/project",
)

async for msg in query(
    prompt="Find all TODO comments in the codebase and summarize them.",
    options=options,
):
    if isinstance(msg, AssistantMessage):
        for block in msg.content:
            if isinstance(block, TextBlock):
                print(block.text)
    elif isinstance(msg, ResultMessage):
        print(f"Cost: ${msg.total_cost_usd:.4f}")
```

### Pattern 3: Code Generation with Budget

```python
options = ClaudeAgentOptions(
    model="opus",
    env={"ANTHROPIC_API_KEY": API_KEY},
    allowed_tools=["Read", "Write", "Bash"],
    permission_mode="bypassPermissions",
    max_turns=20,
    max_budget_usd=2.00,
    system_prompt="You are a senior Python developer. Follow PEP 8. Use type hints.",
    cwd="/path/to/project",
)

async for msg in query(
    prompt="Create a FastAPI CRUD API for user management.",
    options=options,
):
    ...
```

### Pattern 4: Structured Output

```python
options = ClaudeAgentOptions(
    model="sonnet",
    env={"ANTHROPIC_API_KEY": API_KEY},
    max_turns=1,
    permission_mode="bypassPermissions",
    output_format={
        "type": "json_schema",
        "schema": {
            "type": "object",
            "properties": {
                "language": {"type": "string"},
                "frameworks": {"type": "array", "items": {"type": "string"}},
                "complexity": {"type": "string", "enum": ["low", "medium", "high"]},
            },
            "required": ["language", "frameworks", "complexity"],
        },
    },
)

async for msg in query(
    prompt="Analyze this code: def app(): return FastAPI()",
    options=options,
):
    if isinstance(msg, ResultMessage):
        data = msg.structured_output
        # {"language": "Python", "frameworks": ["FastAPI"], "complexity": "low"}
```

### Pattern 5: Resume a Previous Session

```python
# First query — save the session_id
session_id = None
async for msg in query(prompt="Read all files in src/", options=options):
    if isinstance(msg, ResultMessage):
        session_id = msg.session_id

# Later — resume with context
resume_options = ClaudeAgentOptions(
    model="sonnet",
    env={"ANTHROPIC_API_KEY": API_KEY},
    allowed_tools=["Read", "Write", "Edit"],
    permission_mode="bypassPermissions",
    resume=session_id,   # Claude remembers what it read before
    max_turns=10,
)

async for msg in query(
    prompt="Now refactor the utils.py file you read earlier.",
    options=resume_options,
):
    ...
```

### Pattern 6: With Custom Tools

```python
from claude_agent_sdk import tool, create_sdk_mcp_server
import json

@tool(name="get_user", description="Get user by ID", input_schema={"user_id": int})
async def get_user(args):
    user = {"id": args["user_id"], "name": "Abhishek", "role": "Lead"}
    return {"content": [{"type": "text", "text": json.dumps(user)}]}

server = create_sdk_mcp_server(name="api", tools=[get_user])

options = ClaudeAgentOptions(
    model="sonnet",
    env={"ANTHROPIC_API_KEY": API_KEY},
    mcp_servers={"api": server},
    allowed_tools=["mcp__api__get_user"],
    permission_mode="bypassPermissions",
    max_turns=5,
)

async for msg in query(prompt="Get user #42 and describe them.", options=options):
    if isinstance(msg, AssistantMessage):
        for block in msg.content:
            if isinstance(block, TextBlock):
                print(block.text)
```

### Pattern 7: Streaming Partial Messages (Chat UI)

```python
options = ClaudeAgentOptions(
    model="sonnet",
    env={"ANTHROPIC_API_KEY": API_KEY},
    include_partial_messages=True,   # yields StreamEvent with partial tokens
    max_turns=1,
    permission_mode="bypassPermissions",
)

from claude_agent_sdk import StreamEvent

async for msg in query(prompt="Write a haiku about Python.", options=options):
    if isinstance(msg, StreamEvent):
        # Raw Anthropic API stream event — extract partial text delta here
        event = msg.event
    elif isinstance(msg, AssistantMessage):
        for block in msg.content:
            if isinstance(block, TextBlock):
                print(block.text)  # full text once complete
    elif isinstance(msg, ResultMessage):
        print(f"Done: ${msg.total_cost_usd:.4f}")
```

**When NOT to use `include_partial_messages`:** Scripts, batch jobs, CI/CD — you just want the final result.

---

## Related Topics

- [Configuration](01-configuration.md) — All 38 ClaudeAgentOptions parameters
- [ClaudeSDKClient](17-client.md) — Multi-turn stateful client with 14 methods
- [Sessions](07-sessions.md) — Resume, fork, session storage, session management functions
- [Streaming](11-streaming.md) — StreamEvent, partial messages, streaming UIs
- [Structured Outputs](09-structured-outputs.md) — output_format, Pydantic, Zod, validation
- [Built-in Tools](02-built-in-tools.md) — Tool reference, allowed_tools configuration
- [Custom Tools](03-custom-tools.md) — @tool decorator, MCP servers
