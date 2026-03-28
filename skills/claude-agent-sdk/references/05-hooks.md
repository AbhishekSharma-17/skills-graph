# Claude Agent SDK — Hooks

> Source: [platform.claude.com/docs/en/agent-sdk](https://platform.claude.com/docs/en/agent-sdk/overview) — Python v0.1.51, TypeScript v0.2.86

## Contents

- [What Are Hooks](#what-are-hooks)
- [Hook Events](#hook-events)
- [Hook Matchers](#hook-matchers)
- [Callback Signatures](#callback-signatures)
- [Hook Output Fields](#hook-output-fields)
- [Permission Decisions](#permission-decisions)
- [Async Hooks](#async-hooks)
- [Python Examples](#python-examples)
- [TypeScript Examples](#typescript-examples)
- [Python vs TypeScript Differences](#python-vs-typescript-differences)
- [Common Patterns](#common-patterns)
- [Gotchas](#gotchas)

## What Are Hooks

Hooks let you intercept and modify agent behavior at key lifecycle points. They run custom code before/after tool execution, on permission requests, when subagents start/stop, and more.

Use hooks to:
- Log or audit tool usage
- Modify tool inputs before execution
- Inject system messages into the conversation
- Make permission decisions programmatically
- Block dangerous operations
- Add context after tool results

## Hook Events

| Event | Trigger | Python | TypeScript |
|-------|---------|--------|-----------|
| `PreToolUse` | Before a tool executes | Yes | Yes |
| `PostToolUse` | After a tool returns a result | Yes | Yes |
| `PostToolUseFailure` | After a tool execution error | Yes | Yes |
| `UserPromptSubmit` | When a prompt is submitted | Yes | Yes |
| `Stop` | When the agent is about to stop | Yes | Yes |
| `SubagentStart` | When a subagent initializes | Yes | Yes |
| `SubagentStop` | When a subagent completes | Yes | Yes |
| `PreCompact` | Before context compaction | Yes | Yes |
| `Notification` | On status/notification messages | Yes | Yes |
| `PermissionRequest` | When a permission prompt triggers | Yes | Yes |
| `SessionStart` | When a session initializes | No | Yes |
| `SessionEnd` | When a session ends | No | Yes |
| `Setup` | During setup/maintenance | No | Yes |
| `TeammateIdle` | When a teammate becomes idle | No | Yes |
| `TaskCompleted` | When a background task completes | No | Yes |
| `ConfigChange` | When configuration changes | No | Yes |
| `WorktreeCreate` | When a git worktree is created | No | Yes |
| `WorktreeRemove` | When a git worktree is removed | No | Yes |

## Hook Matchers

A `HookMatcher` defines which tools/events trigger the hook:

### Python

```python
from claude_agent_sdk import ClaudeAgentOptions

options = ClaudeAgentOptions(
    hooks={
        "PreToolUse": [
            {
                "matcher": "Bash",              # Exact tool name match
                "hooks": [my_bash_hook],
                "timeout": 30,                   # Seconds (default: 60)
            },
            {
                "matcher": "mcp__github__.*",    # Regex pattern
                "hooks": [my_github_hook],
            },
            {
                "matcher": None,                 # Match ALL tools
                "hooks": [my_logging_hook],
            },
        ],
    }
)
```

### TypeScript

```typescript
const q = query({
  prompt: "...",
  options: {
    hooks: {
      PreToolUse: [
        { matcher: "Bash", hooks: [myBashHook], timeout: 30 },
        { matcher: /mcp__github__.*/, hooks: [myGithubHook] },
        { matcher: undefined, hooks: [myLoggingHook] },
      ],
    },
  },
});
```

| Field | Type | Description |
|-------|------|-------------|
| `matcher` | `str \| None` (Python), `string \| RegExp \| undefined` (TS) | Tool name pattern (regex) or `None`/`undefined` for all |
| `hooks` | `list[Callable]` | Array of callback functions |
| `timeout` | `int` | Seconds before timeout (default: 60) |

## Callback Signatures

### Python

```python
async def my_hook(
    input_data: dict,           # Tool input or event data
    tool_use_id: str | None,    # Tool use ID (None for non-tool events)
    context: Any,               # Hook context
) -> dict:
    return {}  # Empty dict = allow, no modifications
```

### TypeScript

```typescript
const myHook: HookCallback = async (
  input: Record<string, any>,   // Tool input or event data
  toolUseID: string | undefined, // Tool use ID
  { signal }: { signal: AbortSignal },
) => {
  return {};
};
```

## Hook Output Fields

The returned dict can contain:

### Top-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `systemMessage` | `str` | Inject a message into the conversation |
| `continue` (TS) / `continue_` (Python) | `bool` | Keep the agent running after Stop event |
| `suppressOutput` | `bool` | Suppress the hook's output from display |
| `stopReason` | `str` | Custom stop reason |
| `decision` | `"block"` | Block the tool entirely (alternative to hookSpecificOutput deny) |
| `reason` | `str` | Reason for blocking (used with `decision: "block"`) |

### hookSpecificOutput (PreToolUse)

Nested under `hookSpecificOutput` for `PreToolUse` events:

| Field | Type | Description |
|-------|------|-------------|
| `hookEventName` | `str` | The event name (e.g., `"PreToolUse"`) |
| `permissionDecision` | `"allow" \| "deny" \| "ask"` | Permission verdict |
| `permissionDecisionReason` | `str` | Reason shown to user/logs |
| `updatedInput` | `dict` | Modified tool input (requires `permissionDecision: "allow"`) |
| `additionalContext` | `str` | Extra context for Claude |

### hookSpecificOutput (PostToolUse)

For `PostToolUse` events, additional fields are available:

| Field | Type | Description |
|-------|------|-------------|
| `additionalContext` | `str` | Extra context injected after tool result |
| `updatedMCPToolOutput` | `dict` | Modify the MCP tool's output before Claude sees it |

## Permission Decisions

Hooks can make permission decisions for tools:

```python
async def security_hook(input_data, tool_use_id, context):
    command = input_data.get("command", "")

    # Block dangerous commands
    if "rm -rf" in command or "sudo" in command:
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": "Blocked dangerous command",
            }
        }

    # Allow safe commands
    if command.startswith("git ") or command.startswith("ls "):
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
            }
        }

    # Defer to default handling
    return {}
```

### Priority

When multiple hooks match the same tool:

```
deny > ask > allow
```

If any hook returns `deny`, the tool is blocked. If none deny but one says `ask`, the user is prompted. Only if all return `allow` (or empty) is the tool auto-approved.

## Async Hooks

Run hooks without blocking the agent:

```python
async def background_logger(input_data, tool_use_id, context):
    # Log asynchronously — agent proceeds immediately
    return {
        "async_": True,
        "asyncTimeout": 30000,  # ms
    }
```

```typescript
const backgroundLogger: HookCallback = async (input, toolUseID, { signal }) => {
  return { async: true, asyncTimeout: 30000 };
};
```

## Python Examples

### Audit Logger

```python
async def audit_hook(input_data, tool_use_id, context):
    """Log all tool invocations."""
    import json, datetime
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "tool_use_id": tool_use_id,
        "input": input_data,
    }
    with open("audit.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    return {}

options = ClaudeAgentOptions(
    hooks={
        "PreToolUse": [{"matcher": None, "hooks": [audit_hook]}],
    }
)
```

### Input Sanitizer

```python
async def sanitize_bash(input_data, tool_use_id, context):
    """Prevent command injection via environment variables."""
    command = input_data.get("command", "")
    if "$(" in command or "`" in command:
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": "Command substitution not allowed",
            }
        }
    return {}

options = ClaudeAgentOptions(
    hooks={
        "PreToolUse": [{"matcher": "Bash", "hooks": [sanitize_bash]}],
    }
)
```

### Post-Tool Context Injection

```python
async def add_context_after_read(input_data, tool_use_id, context):
    """Add instructions after file reads."""
    return {
        "systemMessage": "Remember: this project uses ESM modules, not CommonJS.",
    }

options = ClaudeAgentOptions(
    hooks={
        "PostToolUse": [{"matcher": "Read", "hooks": [add_context_after_read]}],
    }
)
```

## TypeScript Examples

### Permission Gate

```typescript
const permissionGate: HookCallback = async (input, toolUseID) => {
  const toolName = input.tool_name;

  // Auto-approve read operations
  if (["Read", "Glob", "Grep"].includes(toolName)) {
    return {
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "allow",
      },
    };
  }

  // Ask for write operations
  return {
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "ask",
      permissionDecisionReason: "Write operation requires approval",
    },
  };
};
```

### Modify Tool Input

```typescript
const addTimeout: HookCallback = async (input) => {
  // Add timeout to all Bash commands
  return {
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "allow",
      updatedInput: { ...input, timeout: 30000 },
    },
  };
};
```

> **Important:** `updatedInput` must be inside `hookSpecificOutput`, not at the top level, and requires `permissionDecision: "allow"`.

## Python vs TypeScript Differences

| Feature | Python | TypeScript |
|---------|--------|-----------|
| `continue` field | `continue_` (underscore, reserved word) | `continue` |
| `async` field | `async_` (underscore, reserved word) | `async` |
| SessionStart/End | Not available | Available |
| WorktreeCreate/Remove | Not available | Available |
| Regex matchers | String patterns | `RegExp` objects or strings |
| Hook context | Generic `context` | `{ signal: AbortSignal }` |

## Common Patterns

### Cost Tracking Hook

```python
total_cost = 0.0

async def track_cost(input_data, tool_use_id, context):
    global total_cost
    # input_data contains usage info in PostToolUse
    return {}

async def budget_guard(input_data, tool_use_id, context):
    if total_cost > 5.0:
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"Budget exceeded: ${total_cost:.2f}",
            }
        }
    return {}
```

### Subagent Monitoring

```python
options = ClaudeAgentOptions(
    hooks={
        "SubagentStart": [{"matcher": None, "hooks": [log_subagent_start]}],
        "SubagentStop": [{"matcher": None, "hooks": [log_subagent_stop]}],
    }
)
```

## Gotchas

1. **`updatedInput` requires `permissionDecision: "allow"`** — without it, input modifications are silently ignored
2. **`updatedInput` goes inside `hookSpecificOutput`** — not at the top level of the return dict
3. **Python uses `continue_` and `async_`** — both are reserved words in Python, so the SDK adds an underscore suffix
4. **Hook timeout default is 60 seconds** — set a shorter timeout for hooks that call external APIs
5. **`can_use_tool` in Python requires a dummy `PreToolUse` hook** — the callback only fires in streaming mode with at least one PreToolUse hook registered
6. **Multiple hooks on same tool** — all hooks run; permission decisions follow deny > ask > allow priority

## Related Topics

- [Permissions](06-permissions.md) — Permission modes and evaluation order
- [Custom Tools](03-custom-tools.md) — Creating tools that hooks can intercept
- [Configuration](01-configuration.md) — Hooks in ClaudeAgentOptions
