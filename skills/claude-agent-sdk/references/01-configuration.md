# Claude Agent SDK — Configuration

> Source: [platform.claude.com/docs/en/agent-sdk](https://platform.claude.com/docs/en/agent-sdk/overview) — Python v0.1.51, TypeScript v0.2.86

## Contents

- [ClaudeAgentOptions (Python)](#claudeagentoptions-python)
- [Options (TypeScript)](#options-typescript)
- [Model Selection](#model-selection)
- [Thinking Configuration](#thinking-configuration)
- [Effort Levels](#effort-levels)
- [System Prompts](#system-prompts)
- [Environment Variables](#environment-variables)
- [Setting Sources](#setting-sources)
- [Beta Features](#beta-features)
- [Common Configurations](#common-configurations)

## ClaudeAgentOptions (Python)

All fields are optional. Pass to `query()` or `ClaudeSDKClient()`.

```python
from claude_agent_sdk import ClaudeAgentOptions

options = ClaudeAgentOptions(
    # --- Core ---
    model="claude-sonnet-4-5-20250514",
    fallback_model="claude-haiku-4-5-20251001",
    system_prompt="You are a Python expert.",
    permission_mode="acceptEdits",

    # --- Limits ---
    max_turns=30,
    max_budget_usd=1.00,

    # --- Tools ---
    tools=["Read", "Grep", "Glob"],           # Restrict built-in tools
    allowed_tools=["mcp__myserver__*"],         # Pre-approve tools
    disallowed_tools=["Bash"],                  # Always deny tools

    # --- MCP ---
    mcp_servers={"myserver": {...}},

    # --- Sessions ---
    continue_conversation=False,
    resume="session-id-here",
    fork_session=False,

    # --- Agents ---
    agents={"researcher": AgentDefinition(...)},

    # --- Output ---
    output_format={"type": "json_schema", "schema": {...}},
    include_partial_messages=True,

    # --- Thinking ---
    thinking={"type": "enabled", "budget_tokens": 10000},
    effort="high",

    # --- Environment ---
    cwd="/path/to/project",
    env={"MY_VAR": "value"},
    setting_sources=["user", "project", "local"],

    # --- Advanced ---
    betas=["context-1m-2025-08-07"],
    cli_path="/custom/path/to/claude",
    max_buffer_size=None,
    stderr=lambda line: print(f"[stderr] {line}"),
    can_use_tool=my_permission_callback,
    hooks={...},
    user="user-id",
    sandbox=SandboxSettings(...),
    plugins=[...],
    enable_file_checkpointing=True,
    add_dirs=["/extra/dir1", "/extra/dir2"],
    extra_args={"--flag": "value"},
    settings="/path/to/settings.json",
    permission_prompt_tool_name="custom_permission_tool",
)
```

### Complete Field Reference (Python)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `model` | `str \| None` | `None` (uses default) | Model ID or alias |
| `fallback_model` | `str \| None` | `None` | Fallback if primary unavailable |
| `system_prompt` | `str \| SystemPromptPreset \| None` | `None` | Custom system prompt |
| `permission_mode` | `PermissionMode \| None` | `"default"` | Permission enforcement mode |
| `max_turns` | `int \| None` | `None` (unlimited) | Max tool-use cycles |
| `max_budget_usd` | `float \| None` | `None` (unlimited) | Spending cap |
| `tools` | `list[str] \| ToolsPreset \| None` | `None` (all) | Built-in tools to include |
| `allowed_tools` | `list[str]` | `[]` | Pre-approved tool patterns |
| `disallowed_tools` | `list[str]` | `[]` | Always-denied tool patterns |
| `mcp_servers` | `dict \| str \| Path \| None` | `None` | MCP server configurations |
| `continue_conversation` | `bool` | `False` | Resume last session in cwd |
| `resume` | `str \| None` | `None` | Specific session ID to resume |
| `fork_session` | `bool` | `False` | Branch from resumed session |
| `output_format` | `dict \| None` | `None` | Structured output JSON Schema |
| `include_partial_messages` | `bool` | `False` | Stream partial text chunks |
| `thinking` | `ThinkingConfig \| None` | `None` | Extended thinking settings |
| `effort` | `Literal["low","medium","high","max"] \| None` | `None` | Response effort level |
| `cwd` | `str \| Path \| None` | Current dir | Working directory |
| `env` | `dict[str, str]` | `{}` | Extra environment variables |
| `setting_sources` | `list[SettingSource] \| None` | `[]` | Which settings files to load |
| `agents` | `dict[str, AgentDefinition] \| None` | `None` | Named subagent definitions |
| `hooks` | `dict[HookEvent, list[HookMatcher]] \| None` | `None` | Lifecycle hooks |
| `can_use_tool` | `CanUseTool \| None` | `None` | Permission callback |
| `betas` | `list[SdkBeta]` | `[]` | Beta feature flags |
| `cli_path` | `str \| Path \| None` | Auto-detected | Path to Claude CLI binary |
| `user` | `str \| None` | `None` | User identifier |
| `sandbox` | `SandboxSettings \| None` | `None` | Sandbox configuration |
| `plugins` | `list[SdkPluginConfig]` | `[]` | Plugin configurations |
| `enable_file_checkpointing` | `bool` | `False` | Track file changes for revert |
| `add_dirs` | `list[str \| Path]` | `[]` | Additional accessible directories |
| `max_buffer_size` | `int \| None` | `None` | Max output buffer size |
| `stderr` | `Callable \| None` | `None` | stderr handler |
| `extra_args` | `dict[str, str \| None]` | `{}` | Extra CLI arguments |
| `settings` | `str \| None` | `None` | Path to settings file |

## Options (TypeScript)

TypeScript uses a plain object. Key differences from Python are noted.

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

const conversation = query({
  prompt: "...",
  options: {
    model: "claude-sonnet-4-5-20250514",
    permissionMode: "acceptEdits",
    maxTurns: 30,
    maxBudgetUsd: 1.0,
    tools: ["Read", "Grep"],
    allowedTools: ["mcp__myserver__*"],
    disallowedTools: ["Bash"],
    mcpServers: { myserver: { command: "npx", args: [...] } },
    outputFormat: { type: "json_schema", schema: {...} },
    thinking: { type: "enabled", budget_tokens: 10000 },
    effort: "high",
    cwd: "/path/to/project",
    env: { MY_VAR: "value" },

    // TypeScript-only options:
    persistSession: false,       // In-memory only, no disk
    spawnClaudeCodeProcess: fn,  // Custom process spawning (VMs, containers)
    abortController: ctrl,       // AbortController for cancellation
    debug: true,                 // Debug logging
    debugFile: "debug.log",      // Debug log file
    sessionId: "custom-id",      // Explicit session ID
    strictMcpConfig: true,       // Fail on invalid MCP config
    promptSuggestions: true,     // Enable prompt suggestions
  },
});
```

### TypeScript-Only Fields

| Field | Type | Description |
|-------|------|-------------|
| `persistSession` | `boolean` | `false` = in-memory only |
| `spawnClaudeCodeProcess` | `Function` | Custom process spawning for remote execution |
| `abortController` | `AbortController` | Cancel the query externally |
| `debug` | `boolean` | Enable debug logging |
| `debugFile` | `string` | Write debug output to file |
| `sessionId` | `string` | Explicit session ID |
| `strictMcpConfig` | `boolean` | Fail hard on bad MCP config |
| `resumeSessionAt` | `string` | Resume at specific message ID |

## Model Selection

```python
# Use model ID
options = ClaudeAgentOptions(model="claude-sonnet-4-5-20250514")

# Use alias (convenience)
options = ClaudeAgentOptions(model="sonnet")  # Latest Sonnet
options = ClaudeAgentOptions(model="opus")    # Latest Opus
options = ClaudeAgentOptions(model="haiku")   # Latest Haiku

# With fallback
options = ClaudeAgentOptions(
    model="claude-opus-4-6",
    fallback_model="claude-sonnet-4-5-20250514",
)
```

> Available models depend on your API key and provider. Use `get_server_info()` (Python) or `supportedModels()` (TypeScript) to check.

## Thinking Configuration

Control Claude's extended thinking (chain-of-thought reasoning):

```python
# Adaptive — Claude decides when to think deeply
options = ClaudeAgentOptions(thinking={"type": "adaptive"})

# Enabled with budget — always think, up to N tokens
options = ClaudeAgentOptions(thinking={"type": "enabled", "budget_tokens": 10000})

# Disabled — no extended thinking
options = ClaudeAgentOptions(thinking={"type": "disabled"})
```

## Effort Levels

Control how much effort Claude puts into responses:

| Level | Behavior |
|-------|----------|
| `"low"` | Quick, minimal analysis |
| `"medium"` | Balanced (default behavior) |
| `"high"` | Thorough analysis and consideration |
| `"max"` | Maximum effort, most comprehensive |

```python
options = ClaudeAgentOptions(effort="high")
```

## System Prompts

```python
# Custom string
options = ClaudeAgentOptions(system_prompt="You are a security auditor. Only review code for vulnerabilities.")

# System prompt preset
options = ClaudeAgentOptions(system_prompt="default")  # Standard Claude Code prompt
```

> **Important:** The system prompt replaces (does not append to) the default prompt. If you want the default behavior plus additions, use CLAUDE.md files instead via `setting_sources`.

## Environment Variables

```python
# Pass to the agent's execution environment
options = ClaudeAgentOptions(
    env={
        "DATABASE_URL": "postgres://localhost:5432/mydb",
        "API_KEY": "sk-...",
        "NODE_ENV": "development",
    }
)
```

These are available to Bash commands and any processes the agent spawns.

## Setting Sources

Control which settings files the SDK loads from disk:

```python
# Load no settings files (default) — cleanest for programmatic use
options = ClaudeAgentOptions(setting_sources=[])

# Load user-level settings (~/.claude/settings.json)
options = ClaudeAgentOptions(setting_sources=["user"])

# Load project-level too (.claude/settings.json, CLAUDE.md, skills, hooks)
options = ClaudeAgentOptions(setting_sources=["user", "project", "local"])
```

> **Gotcha:** The default is `[]` (empty) — no filesystem settings are loaded. If you want CLAUDE.md files, skills, or file-based hooks to work, you must explicitly set `setting_sources`.

## Beta Features

```python
# Enable 1M context window
options = ClaudeAgentOptions(betas=["context-1m-2025-08-07"])
```

## Common Configurations

### Trusted Automation (CI/CD)

```python
options = ClaudeAgentOptions(
    permission_mode="bypassPermissions",
    max_turns=50,
    max_budget_usd=2.00,
    model="sonnet",
    cwd="/workspace",
    setting_sources=[],
)
```

### Interactive Development Assistant

```python
options = ClaudeAgentOptions(
    permission_mode="acceptEdits",
    include_partial_messages=True,
    setting_sources=["user", "project"],
    enable_file_checkpointing=True,
)
```

### Read-Only Research Agent

```python
options = ClaudeAgentOptions(
    tools=["Read", "Glob", "Grep", "WebSearch", "WebFetch"],
    disallowed_tools=["Write", "Edit", "Bash"],
    max_turns=20,
    max_budget_usd=0.50,
)
```

## Related Topics

- [Permissions](06-permissions.md) — Permission modes and evaluation order
- [Hooks](05-hooks.md) — Lifecycle hooks for intercepting tool execution
- [Sessions](07-sessions.md) — Multi-turn conversations and session management
