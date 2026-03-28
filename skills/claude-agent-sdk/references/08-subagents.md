# Claude Agent SDK — Subagents

> Source: [platform.claude.com/docs/en/agent-sdk](https://platform.claude.com/docs/en/agent-sdk/overview) — Python v0.1.51, TypeScript v0.2.86

## Contents

- [What Are Subagents](#what-are-subagents)
- [AgentDefinition](#agentdefinition)
- [Defining Subagents](#defining-subagents)
- [How Subagents Execute](#how-subagents-execute)
- [Model Selection](#model-selection)
- [Tool Scoping](#tool-scoping)
- [MCP Servers in Subagents](#mcp-servers-in-subagents)
- [Communication Patterns](#communication-patterns)
- [Subagent Lifecycle Hooks](#subagent-lifecycle-hooks)
- [Limitations](#limitations)
- [Common Patterns](#common-patterns)
- [Gotchas](#gotchas)

## What Are Subagents

Subagents are specialized agents spawned by the main agent via the `Agent` tool. Each subagent runs in its own fresh context window, receives a focused task, and returns a single result message to the parent.

Use subagents to:
- Parallelize independent tasks (research + implementation)
- Isolate context (prevent one task from polluting another's context)
- Use different models for different tasks (haiku for simple, opus for complex)
- Scope tool access (read-only research agent vs full-access implementation agent)

## AgentDefinition

### Python

```python
from claude_agent_sdk import ClaudeAgentOptions

options = ClaudeAgentOptions(
    agents={
        "researcher": {
            "description": "Explores codebases and gathers information",
            "prompt": "You are a code researcher. Find and summarize relevant code patterns.",
            "tools": ["Read", "Glob", "Grep", "WebSearch"],
            "model": "haiku",
            "max_turns": 15,
        },
        "implementer": {
            "description": "Writes and modifies code",
            "prompt": "You are a senior engineer. Write clean, tested code.",
            "tools": ["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
            "model": "sonnet",
            "max_turns": 30,
        },
    },
    allowed_tools=["Agent"],  # Allow the parent to spawn subagents
)
```

### TypeScript

```typescript
const q = query({
  prompt: "...",
  options: {
    agents: {
      researcher: {
        description: "Explores codebases and gathers information",
        prompt: "You are a code researcher. Find and summarize relevant code patterns.",
        tools: ["Read", "Glob", "Grep", "WebSearch"],
        model: "haiku",
        maxTurns: 15,
      },
      implementer: {
        description: "Writes and modifies code",
        prompt: "You are a senior engineer. Write clean, tested code.",
        tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
        model: "sonnet",
        maxTurns: 30,
      },
    },
    allowedTools: ["Agent"],
  },
});
```

### AgentDefinition Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | `str` | Yes | When to use this agent (shown to parent) |
| `prompt` | `str` | Yes | System prompt for the subagent |
| `tools` | `list[str]` | No | Allowed tools (omit = inherit all from parent) |
| `disallowed_tools` | `list[str]` | No | Blocked tools |
| `model` | `str` | No | `"sonnet"`, `"opus"`, `"haiku"`, or `"inherit"` |
| `max_turns` | `int` | No | Max tool-use cycles |
| `mcp_servers` | `list` | No | MCP servers available to this agent |
| `skills` | `list[str]` | No | Skills available to this agent |

## Defining Subagents

### Minimal Definition

```python
agents={
    "helper": {
        "description": "General-purpose assistant",
        "prompt": "Help with the assigned task.",
    },
}
```

### Full Definition

```python
agents={
    "security_auditor": {
        "description": "Reviews code for security vulnerabilities",
        "prompt": """You are a security expert. Review code for:
- SQL injection
- XSS vulnerabilities
- Authentication bypasses
- Insecure dependencies
Report findings with severity levels.""",
        "tools": ["Read", "Glob", "Grep"],
        "disallowed_tools": ["Write", "Edit", "Bash"],
        "model": "opus",
        "max_turns": 20,
    },
}
```

## How Subagents Execute

1. Parent agent calls the `Agent` tool with a prompt and optional `subagent_type`
2. SDK creates a new context window for the subagent
3. Subagent executes autonomously using its allowed tools
4. Only the **final message** returns to the parent agent
5. Subagent's full transcript is stored independently

```
Parent Agent
    │
    ├── Agent(subagent_type="researcher", prompt="Find all API endpoints")
    │       │
    │       └── Subagent runs: Read, Glob, Grep...
    │           └── Returns: "Found 15 endpoints in src/routes/..."
    │
    ├── Agent(subagent_type="implementer", prompt="Add auth middleware to all endpoints")
    │       │
    │       └── Subagent runs: Read, Edit, Write, Bash...
    │           └── Returns: "Added auth middleware to 15 endpoints, tests passing"
    │
    └── Parent synthesizes results
```

## Model Selection

Assign different models to different agent roles:

```python
agents={
    "quick_lookup": {
        "description": "Fast lookups and simple searches",
        "prompt": "Find information quickly.",
        "model": "haiku",        # Fast, cheap
    },
    "code_writer": {
        "description": "Writes production code",
        "prompt": "Write high-quality code.",
        "model": "sonnet",       # Balanced
    },
    "architect": {
        "description": "Designs system architecture",
        "prompt": "Design robust architectures.",
        "model": "opus",         # Most capable
    },
    "flexible": {
        "description": "Inherits parent's model",
        "prompt": "General tasks.",
        "model": "inherit",      # Same as parent
    },
}
```

## Tool Scoping

### Restrict Subagent Tools

```python
agents={
    "reader": {
        "description": "Read-only research",
        "prompt": "Research the codebase.",
        "tools": ["Read", "Glob", "Grep"],  # Only these tools
    },
}
```

### Inherit Parent Tools

Omit `tools` to inherit all parent tools:

```python
agents={
    "full_access": {
        "description": "Full access agent",
        "prompt": "Handle any task.",
        # No tools field = inherits everything from parent
    },
}
```

### Block Specific Tools

```python
agents={
    "safe_agent": {
        "description": "Agent without shell access",
        "prompt": "Work without shell commands.",
        "disallowed_tools": ["Bash"],  # Everything except Bash
    },
}
```

## MCP Servers in Subagents

Subagents can have their own MCP server access:

```python
agents={
    "db_agent": {
        "description": "Database operations",
        "prompt": "Query and analyze database.",
        "mcp_servers": [
            {"name": "postgres", "tools": ["query"]},  # Only query tool
        ],
    },
}
```

## Communication Patterns

### Parent Dispatches Tasks

The parent agent decides when and how to use subagents:

```python
# The parent sees the agent definitions and can call:
# Agent(subagent_type="researcher", prompt="Find all TODO comments")
# Agent(subagent_type="implementer", prompt="Fix the top 3 TODOs")
```

### Parallel Subagents

The parent can launch multiple subagents concurrently:

```python
# Parent can call Agent tool multiple times in one response
# Each subagent runs independently
# Results return as they complete
```

### Chaining Subagents

Results from one subagent inform the next:

```python
# 1. Parent sends: Agent(type="researcher", prompt="Analyze the auth system")
# 2. Researcher returns findings
# 3. Parent sends: Agent(type="implementer", prompt="Based on the analysis, refactor...")
```

### Background Subagents

Launch subagents asynchronously:

```python
# Agent(subagent_type="researcher", prompt="...", run_in_background=True)
# Parent continues working
# Notified when background agent completes
```

## Subagent Lifecycle Hooks

Monitor subagent start/stop via hooks:

```python
async def on_subagent_start(input_data, tool_use_id, context):
    print(f"Subagent starting: {input_data.get('subagent_type', 'default')}")
    return {}

async def on_subagent_stop(input_data, tool_use_id, context):
    print(f"Subagent completed: {tool_use_id}")
    return {}

options = ClaudeAgentOptions(
    hooks={
        "SubagentStart": [{"matcher": None, "hooks": [on_subagent_start]}],
        "SubagentStop": [{"matcher": None, "hooks": [on_subagent_stop]}],
    },
    agents={...},
)
```

## Limitations

| Limitation | Details |
|-----------|---------|
| **No nesting** | Subagents cannot spawn their own subagents |
| **Single result** | Only the final message returns to parent |
| **Fresh context** | Each subagent starts with an empty context window |
| **Permission inheritance** | `bypassPermissions` is inherited and cannot be overridden |
| **No shared state** | Subagents don't share memory or conversation history |
| **Windows limit** | Long prompts may fail on Windows (8191 char command line limit) |

## Common Patterns

### Research + Implement

```python
agents={
    "explorer": {
        "description": "Codebase exploration and research",
        "prompt": "You explore codebases. Report findings concisely.",
        "tools": ["Read", "Glob", "Grep", "WebSearch"],
        "model": "haiku",
        "max_turns": 15,
    },
    "developer": {
        "description": "Code implementation and testing",
        "prompt": "You write clean, tested code following project conventions.",
        "tools": ["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
        "model": "sonnet",
        "max_turns": 30,
    },
}
```

### Multi-Perspective Review

```python
agents={
    "security_reviewer": {
        "description": "Security-focused code review",
        "prompt": "Review for OWASP Top 10 vulnerabilities.",
        "tools": ["Read", "Glob", "Grep"],
        "model": "opus",
    },
    "performance_reviewer": {
        "description": "Performance-focused code review",
        "prompt": "Review for performance bottlenecks and optimization opportunities.",
        "tools": ["Read", "Glob", "Grep"],
        "model": "sonnet",
    },
}
```

### Specialized Tool Agents

```python
agents={
    "db_analyst": {
        "description": "Database analysis and queries",
        "prompt": "Analyze database schema and query patterns.",
        "mcp_servers": [{"name": "postgres"}],
        "tools": ["Read", "Grep"],
    },
    "api_tester": {
        "description": "API endpoint testing",
        "prompt": "Test API endpoints and report results.",
        "tools": ["Bash", "Read", "WebFetch"],
    },
}
```

## Three Ways to Create Subagents

| Method | Configuration | Persistence |
|--------|--------------|-------------|
| **Programmatic** | `agents` param in options | Session only |
| **Filesystem** | `.claude/agents/*.md` files | Persistent (via git) |
| **Built-in** | General-purpose agent (always available) | Always |

### Filesystem Agent Definitions

Create `.claude/agents/my-agent.md` with YAML frontmatter:

```markdown
---
description: Explores codebases and gathers information
tools: [Read, Glob, Grep]
model: haiku
---

You are a code researcher. Find and summarize relevant code patterns.
Report findings concisely with file paths and line numbers.
```

Filesystem agents require `setting_sources` to include `"project"`:

```python
options = ClaudeAgentOptions(
    setting_sources=["project"],
    allowed_tools=["Agent"],
)
```

### Resuming Subagents

Capture the `session_id` and `agentId` from the subagent's tool result to resume it later:

```python
async for msg in query(prompt="...", options=options):
    if msg.type == "assistant":
        for block in msg.content:
            if block.type == "tool_result" and hasattr(block, "agent_id"):
                # Save for later resumption
                saved_agent_id = block.agent_id
                saved_session_id = block.session_id
```

## Gotchas

1. **Include `Agent` in `allowedTools`** — the parent needs permission to spawn subagents
2. **No nesting** — subagents cannot call the `Agent` tool themselves
3. **Fresh context per subagent** — they don't see the parent's conversation history; include all needed context in the prompt
4. **`bypassPermissions` inheritance** — if the parent uses bypass mode, all subagents do too; use `disallowed_tools` in agent definitions to restrict
5. **Cost accumulates** — subagent token usage counts toward the parent's budget
6. **Tool renamed** — the `Agent` tool was formerly called `Task` (renamed in Claude Code v2.1.63)
7. **Subagent inherits parent's system prompt** — does NOT get the parent's conversation; gets its own prompt + Agent tool prompt
8. **Filesystem agents need setting_sources** — set `setting_sources=["project"]` to load `.claude/agents/` files

## Related Topics

- [Configuration](01-configuration.md) — Agent definitions in options
- [Permissions](06-permissions.md) — Permission inheritance
- [Hooks](05-hooks.md) — SubagentStart/SubagentStop hooks
