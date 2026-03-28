# Claude Agent SDK — Sessions

> Source: [platform.claude.com/docs/en/agent-sdk](https://platform.claude.com/docs/en/agent-sdk/overview) — Python v0.1.51, TypeScript v0.2.86

## Contents

- [Session Approaches](#session-approaches)
- [One-Shot Queries](#one-shot-queries)
- [Multi-Turn with ClaudeSDKClient (Python)](#multi-turn-with-claudesdkclient-python)
- [Multi-Turn with continue (TypeScript)](#multi-turn-with-continue-typescript)
- [Resuming Sessions](#resuming-sessions)
- [Forking Sessions](#forking-sessions)
- [Session Storage](#session-storage)
- [Session Management Functions](#session-management-functions)
- [Interrupt and Rewind](#interrupt-and-rewind)
- [In-Memory Sessions (TypeScript)](#in-memory-sessions-typescript)
- [Common Patterns](#common-patterns)
- [Gotchas](#gotchas)

## Session Approaches

| Approach | Use Case | Persistence |
|----------|----------|------------|
| **One-shot** | Single task, no follow-up | New session each call |
| **Multi-turn (same process)** | Interactive conversation | Single session, same process |
| **Resume** | Continue previous work | Load from disk by session ID |
| **Fork** | Branch from a point | New session branching from existing |

## One-Shot Queries

The simplest approach — a single `query()` call that creates a new session:

### Python

```python
from claude_agent_sdk import query, ClaudeAgentOptions

async def run_task():
    options = ClaudeAgentOptions(max_turns=20)
    session_id = None

    async for msg in query(prompt="Fix the bug in auth.py", options=options):
        if msg.type == "result":
            session_id = msg.session_id
            print(f"Done. Session: {session_id}")

    return session_id
```

### TypeScript

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

const q = query({ prompt: "Fix the bug in auth.py", options: { maxTurns: 20 } });

for await (const msg of q) {
  if (msg.type === "result") {
    console.log(`Done. Session: ${msg.session_id}`);
  }
}
```

## Multi-Turn with ClaudeSDKClient (Python)

`ClaudeSDKClient` maintains a persistent connection for multiple exchanges:

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

async def interactive_session():
    options = ClaudeAgentOptions(
        permission_mode="acceptEdits",
        max_turns=10,
    )

    client = ClaudeSDKClient(options=options)

    async with client:
        # First turn
        await client.connect(prompt="Analyze the project structure")
        async for msg in client.receive_messages():
            if msg.type == "assistant":
                for block in msg.content:
                    if hasattr(block, "text"):
                        print(block.text)

        # Second turn (same session)
        await client.query("Now add unit tests for the auth module")
        async for msg in client.receive_response():
            if msg.type == "assistant":
                for block in msg.content:
                    if hasattr(block, "text"):
                        print(block.text)

        # Third turn
        await client.query("Run the tests and fix any failures")
        async for msg in client.receive_response():
            ...
```

### ClaudeSDKClient Methods

| Method | Description |
|--------|-------------|
| `connect(prompt?)` | Initialize session, optionally with first prompt |
| `query(prompt, session_id?)` | Send a follow-up prompt |
| `receive_messages()` | Async iterator for all messages |
| `receive_response()` | Async iterator for current response only |
| `interrupt()` | Stop current execution |
| `set_permission_mode(mode)` | Change permissions mid-session |
| `set_model(model)` | Change model mid-session |
| `rewind_files(user_message_id)` | Revert file changes to a point |
| `get_mcp_status()` | Check MCP server status |
| `reconnect_mcp_server(name)` | Reconnect a failed MCP server |
| `toggle_mcp_server(name, enabled)` | Enable/disable MCP server |
| `stop_task(task_id)` | Stop a background task |
| `get_server_info()` | Get server capabilities |
| `disconnect()` | Close the session |

## Multi-Turn with continue (TypeScript)

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

// First query
let sessionId: string | undefined;
const q1 = query({ prompt: "Analyze the project", options: { maxTurns: 10 } });

for await (const msg of q1) {
  if (msg.type === "result") {
    sessionId = msg.session_id;
  }
}

// Continue the same session
const q2 = query({
  prompt: "Now add tests",
  options: { resume: sessionId },
});

for await (const msg of q2) {
  // ...
}
```

Or use `continue: true` to resume the most recent session in the working directory:

```typescript
const q2 = query({
  prompt: "Now add tests",
  options: { continue: true, cwd: "/path/to/project" },
});
```

## Resuming Sessions

Resume a previous session by its ID:

### Python

```python
# Capture session_id from a previous run
session_id = "abc123-..."

# Resume later
options = ClaudeAgentOptions(resume=session_id)
async for msg in query(prompt="Continue where we left off", options=options):
    ...
```

### TypeScript

```typescript
const q = query({
  prompt: "Continue where we left off",
  options: { resume: "abc123-..." },
});
```

> **Important:** The `cwd` must match the original session's working directory. Sessions are stored relative to the working directory.

## Forking Sessions

Create a branch from an existing session — the fork gets the full conversation history but diverges from that point:

### Python

```python
options = ClaudeAgentOptions(
    resume="original-session-id",
    fork_session=True,
)
async for msg in query(prompt="Try a different approach...", options=options):
    if msg.type == "result":
        forked_session_id = msg.session_id  # New session ID
```

### TypeScript

```typescript
const q = query({
  prompt: "Try a different approach...",
  options: { resume: "original-session-id", forkSession: true },
});
```

## Session Storage

Sessions are stored as JSONL files on disk:

```
~/.claude/projects/<encoded-cwd>/<session-id>.jsonl
```

- `<encoded-cwd>` is a deterministic encoding of the working directory path
- Each line in the JSONL file is a message in the conversation
- Sessions are local to the machine — not synced across devices

## Session Management Functions

### Python

```python
from claude_agent_sdk import list_sessions, get_session_messages, get_session_info, rename_session, tag_session

# List recent sessions
sessions = await list_sessions(
    directory="/path/to/project",
    limit=10,
    include_worktrees=False,
)
for s in sessions:
    print(f"{s.session_id}: {s.title} ({s.created_at})")

# Get messages from a session
messages = await get_session_messages(
    session_id="abc123",
    directory="/path/to/project",
    limit=50,
    offset=0,
)

# Get session info
info = await get_session_info(session_id="abc123", directory="/path/to/project")

# Rename a session
await rename_session(session_id="abc123", title="Auth refactor", directory="/path/to/project")

# Tag a session
await tag_session(session_id="abc123", tag="v2-migration", directory="/path/to/project")
```

### SDKSessionInfo Fields

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | `str` | Unique session identifier |
| `title` | `str \| None` | Human-readable title |
| `created_at` | `str` | ISO timestamp |
| `updated_at` | `str` | Last activity timestamp |
| `tags` | `list[str]` | User-assigned tags |

## Interrupt and Rewind

### Interrupt

Stop the agent mid-execution:

```python
# Python
await client.interrupt()

# TypeScript
await q.interrupt();
```

### Rewind Files

Revert file changes made after a specific message:

```python
# Python — revert to state after a specific user message
await client.rewind_files(user_message_id="msg-abc123")

# TypeScript
await q.rewindFiles("msg-abc123");
```

This undoes file modifications (Write, Edit) but doesn't undo Bash commands or external API calls.

## In-Memory Sessions (TypeScript)

TypeScript supports sessions that don't persist to disk:

```typescript
const q = query({
  prompt: "...",
  options: {
    persistSession: false,  // No disk storage
  },
});
```

Useful for ephemeral tasks, testing, or when running in environments without persistent storage.

Not available in the Python SDK.

## Common Patterns

### Task Pipeline (Sequential Sessions)

```python
async def pipeline():
    # Step 1: Analysis
    analysis_session = None
    async for msg in query(prompt="Analyze auth.py for security issues", options=opts):
        if msg.type == "result":
            analysis_session = msg.session_id

    # Step 2: Fix (resume from analysis)
    async for msg in query(
        prompt="Fix the issues you found",
        options=ClaudeAgentOptions(resume=analysis_session),
    ):
        ...
```

### A/B Testing with Forks

```python
async def ab_test(session_id: str):
    # Approach A
    async for msg in query(
        prompt="Refactor using strategy pattern",
        options=ClaudeAgentOptions(resume=session_id, fork_session=True),
    ):
        ...

    # Approach B (from same starting point)
    async for msg in query(
        prompt="Refactor using composition",
        options=ClaudeAgentOptions(resume=session_id, fork_session=True),
    ):
        ...
```

### Session Archival

```python
sessions = await list_sessions(directory="/project")
for s in sessions:
    if s.updated_at < cutoff_date:
        await tag_session(s.session_id, "archived", directory="/project")
```

## Gotchas

1. **`cwd` must match** — when resuming, the working directory must be the same as the original session
2. **Sessions are local** — stored on disk, not synced across machines
3. **`persistSession: false` is TypeScript-only** — Python always persists
4. **`continue_conversation` vs `resume`** — `continue_conversation=True` resumes the *most recent* session in the cwd; `resume="id"` resumes a *specific* session
5. **Forking creates a new ID** — the forked session gets its own `session_id`
6. **Compaction affects history** — older messages may be summarized when context limits approach; persistent instructions should be in system prompt or CLAUDE.md

## Related Topics

- [Configuration](01-configuration.md) — Session-related options
- [Subagents](08-subagents.md) — Subagent sessions
- [Deployment](10-deployment.md) — Session patterns in production
