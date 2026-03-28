# Claude Agent SDK — Permissions

> Source: [platform.claude.com/docs/en/agent-sdk](https://platform.claude.com/docs/en/agent-sdk/overview) — Python v0.1.51, TypeScript v0.2.86

## Contents

- [Permission Evaluation Order](#permission-evaluation-order)
- [Permission Modes](#permission-modes)
- [canUseTool Callback](#canusetool-callback)
- [allowed_tools and disallowed_tools](#allowed_tools-and-disallowed_tools)
- [Dynamic Permission Changes](#dynamic-permission-changes)
- [Security Considerations](#security-considerations)
- [Common Configurations](#common-configurations)
- [Gotchas](#gotchas)

## Permission Evaluation Order

When Claude requests to use a tool, the SDK evaluates permissions in this order:

```
1. Hooks (PreToolUse)        →  Can allow, deny, or ask
2. disallowed_tools           →  DENY if matched (highest priority rule)
3. Permission mode check      →  Mode-specific behavior
4. allowed_tools              →  ALLOW if matched (auto-approve)
5. canUseTool callback        →  Custom decision function
6. Default                    →  Depends on mode (prompt user or deny)
```

> **Key principle:** `disallowed_tools` always wins. Even `bypassPermissions` mode cannot override it.

## Permission Modes

Set via `permission_mode` in options:

### default

Standard mode. Unmatched tools trigger `canUseTool` callback or prompt the user.

```python
options = ClaudeAgentOptions(permission_mode="default")
```

### acceptEdits

Auto-approves file modification tools: `Edit`, `Write`, `mkdir`, `rm`, `mv`, `cp`. Other tools follow default behavior.

```python
options = ClaudeAgentOptions(permission_mode="acceptEdits")
```

Best for: interactive development where you trust Claude to edit files but want control over Bash and external tools.

### bypassPermissions

Auto-approves **all** tools. Use only in trusted, sandboxed environments.

```python
options = ClaudeAgentOptions(permission_mode="bypassPermissions")
```

> **Warning:** Subagents inherit `bypassPermissions` and it cannot be overridden for them. Use `disallowed_tools` to block specific tools even in bypass mode.

### plan

No tool execution at all. Claude can only plan and describe what it would do.

```python
options = ClaudeAgentOptions(permission_mode="plan")
```

### dontAsk (TypeScript only)

Denies anything not explicitly pre-approved via `allowed_tools`. Never prompts the user.

```typescript
const q = query({
  prompt: "...",
  options: {
    permissionMode: "dontAsk",
    allowedTools: ["Read", "Glob", "Grep"],  // Only these tools work
  },
});
```

Not available in the Python SDK.

## canUseTool Callback

A function called when a tool isn't auto-approved or denied. Returns allow or deny.

### Python

```python
from claude_agent_sdk import ClaudeAgentOptions

async def my_permission_handler(
    tool_name: str,
    input_data: dict,
    context,  # ToolPermissionContext
) -> dict:
    # Allow all read operations
    if tool_name in ("Read", "Glob", "Grep"):
        return {"type": "allow"}

    # Allow Bash but modify the command
    if tool_name == "Bash":
        safe_command = input_data.get("command", "")
        if safe_command.startswith("git "):
            return {"type": "allow", "updated_input": input_data}
        return {"type": "deny", "message": "Only git commands allowed"}

    # Deny everything else
    return {"type": "deny", "message": f"Tool {tool_name} not permitted"}

options = ClaudeAgentOptions(
    can_use_tool=my_permission_handler,
)
```

### TypeScript

```typescript
const q = query({
  prompt: "...",
  options: {
    canUseTool: async (toolName, input, context) => {
      if (["Read", "Glob", "Grep"].includes(toolName)) {
        return { type: "allow" };
      }
      return { type: "deny", message: `Tool ${toolName} not permitted` };
    },
  },
});
```

### Return Types

```python
# Allow (optionally modify input)
{"type": "allow"}
{"type": "allow", "updated_input": modified_input_dict}

# Deny
{"type": "deny", "message": "Reason for denial"}
```

> **Python gotcha:** `can_use_tool` requires streaming mode and at least one `PreToolUse` hook registered (even a no-op one) to function properly.

## allowed_tools and disallowed_tools

### allowed_tools — Pre-approve

Auto-approve specific tools without requiring permission prompts:

```python
options = ClaudeAgentOptions(
    allowed_tools=[
        "Read",                      # Specific built-in tool
        "Glob",
        "Grep",
        "mcp__github__*",           # All tools from github server (wildcard)
        "mcp__db__query",           # Specific MCP tool
    ]
)
```

> `allowed_tools` does NOT restrict — it only auto-approves. Tools not listed still work but may require permission.

### disallowed_tools — Always Block

Block specific tools regardless of permission mode:

```python
options = ClaudeAgentOptions(
    permission_mode="bypassPermissions",
    disallowed_tools=[
        "Bash",                     # Block shell access
        "WebFetch",                 # Block web access
        "mcp__db__execute",         # Block DB writes
    ]
)
```

> `disallowed_tools` has the highest priority — it overrides `bypassPermissions`, `allowed_tools`, and hooks.

## Dynamic Permission Changes

Change permission mode mid-session:

### Python

```python
client = ClaudeSDKClient(options)
async with client:
    await client.connect()

    # Start in default mode
    await client.set_permission_mode("default")
    await client.query("Analyze the codebase")

    # Switch to accept edits for implementation
    await client.set_permission_mode("acceptEdits")
    await client.query("Implement the changes we discussed")
```

### TypeScript

```typescript
const q = query({ prompt: "...", options: { permissionMode: "default" } });

// Change mid-stream
await q.setPermissionMode("acceptEdits");
```

## Security Considerations

### Principle of Least Privilege

```python
# Good: Only approve what's needed
options = ClaudeAgentOptions(
    permission_mode="default",
    allowed_tools=["Read", "Glob", "Grep"],
    disallowed_tools=["Bash"],
)

# Bad: Bypass everything
options = ClaudeAgentOptions(permission_mode="bypassPermissions")
```

### Sandboxed Environments

When running in containers, VMs, or sandboxes, `bypassPermissions` is acceptable because the blast radius is contained:

```python
# OK in a disposable container
options = ClaudeAgentOptions(
    permission_mode="bypassPermissions",
    max_turns=50,
    max_budget_usd=2.00,
    cwd="/workspace",  # Sandboxed directory
)
```

### Defense in Depth

Combine multiple permission layers:

```python
options = ClaudeAgentOptions(
    permission_mode="acceptEdits",              # Layer 1: mode
    disallowed_tools=["mcp__db__drop_table"],   # Layer 2: blocklist
    hooks={                                       # Layer 3: hooks
        "PreToolUse": [{"matcher": "Bash", "hooks": [bash_guard]}],
    },
    can_use_tool=custom_permission_fn,            # Layer 4: callback
    max_turns=30,                                 # Layer 5: resource limits
    max_budget_usd=1.00,
)
```

## Common Configurations

### CI/CD Pipeline Agent

```python
options = ClaudeAgentOptions(
    permission_mode="bypassPermissions",
    max_turns=50,
    max_budget_usd=5.00,
    disallowed_tools=["WebSearch", "WebFetch"],  # No internet access
)
```

### Code Review Agent (Read-Only)

```python
options = ClaudeAgentOptions(
    permission_mode="default",
    tools=["Read", "Glob", "Grep"],
    disallowed_tools=["Write", "Edit", "Bash", "NotebookEdit"],
)
```

### Interactive Assistant with Guardrails

```python
options = ClaudeAgentOptions(
    permission_mode="acceptEdits",
    disallowed_tools=["mcp__*__delete_*"],  # Block all delete operations
    can_use_tool=interactive_permission_handler,
)
```

## Gotchas

1. **`bypassPermissions` is inherited by subagents** — and cannot be overridden. Use `disallowed_tools` on the subagent definition instead.
2. **`allowed_tools` does NOT constrain `bypassPermissions`** — bypass mode approves everything; use `disallowed_tools` to block.
3. **`dontAsk` is TypeScript-only** — Python SDK does not support this mode.
4. **`can_use_tool` requires a PreToolUse hook in Python** — register at least a no-op hook: `{"matcher": None, "hooks": [lambda *a: {}]}`.
5. **Wildcard patterns** — `mcp__server__*` works in `allowed_tools` and `disallowed_tools`, but `*` alone does not match built-in tools.
6. **Setting sources** — permission settings from `settings.json` are only loaded when `setting_sources` includes the relevant source.

## Related Topics

- [Hooks](05-hooks.md) — Custom permission logic via hooks
- [Configuration](01-configuration.md) — Full options reference
- [Built-in Tools](02-built-in-tools.md) — Tool names for permission rules
