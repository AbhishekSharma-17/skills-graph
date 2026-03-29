# Claude Agent SDK — ClaudeAgentOptions Deep Reference

> Used by both `query()` and `ClaudeSDKClient`. All 38 parameters documented with when-to-use, when-not-to-use, and examples.

## Contents

- [The 3 You Always Need](#the-3-you-always-need)
- [Group 1 — Core](#group-1--core)
- [Group 2 — Tool Control](#group-2--tool-control)
- [Group 3 — Cost & Safety Limits](#group-3--cost--safety-limits)
- [Group 4 — System Prompt](#group-4--system-prompt)
- [Group 5 — MCP Servers](#group-5--mcp-servers)
- [Group 6 — Session & Conversation](#group-6--session--conversation)
- [Group 7 — Thinking & Effort](#group-7--thinking--effort)
- [Group 8 — Structured Output](#group-8--structured-output)
- [Group 9 — Permissions & Hooks](#group-9--permissions--hooks)
- [Group 10 — Paths & Working Directory](#group-10--paths--working-directory)
- [Group 11 — Streaming & Debugging](#group-11--streaming--debugging)
- [Group 12 — Sandbox](#group-12--sandbox)
- [Group 13 — Sub-agents](#group-13--sub-agents)
- [Group 14 — Settings & Plugins](#group-14--settings--plugins)
- [Group 15 — Token Budget & Checkpointing](#group-15--token-budget--checkpointing)
- [TypeScript Name Mapping](#typescript-name-mapping)
- [TypeScript-Only Parameters](#typescript-only-parameters)
- [Decision Matrix — What to Set for Each Use Case](#decision-matrix--what-to-set-for-each-use-case)
- [All Parameters — Quick Reference Table](#all-parameters--quick-reference-table)
- [Deprecated Parameters](#deprecated-parameters)

---

## The 3 You Always Need

Every agent needs at minimum:

```python
options = ClaudeAgentOptions(
    model="sonnet",                            # which model to use
    env={"ANTHROPIC_API_KEY": "sk-ant-..."},   # how to authenticate
    permission_mode="bypassPermissions",       # what Claude is allowed to do
)
```

Everything else is optional — but you'll almost always also want:
- `allowed_tools` — which tools Claude can use
- `max_turns` — prevent runaway loops
- `max_budget_usd` — prevent cost spikes in production

---

## Group 1 — Core

### `model`

**Type:** `str | None` | **Default:** `None` (SDK picks its default)

Which Claude model to use.

```python
# Short aliases — always resolve to the latest version of that family
model="haiku"    # fastest, cheapest — good for simple tasks and scanning
model="sonnet"   # balanced quality + speed (recommended default)
model="opus"     # most capable, most expensive — complex reasoning/refactoring

# Full model IDs — use for Bedrock/Vertex or when you need a pinned version
model="claude-sonnet-4-6"
model="anthropic.claude-sonnet-4-6"          # AWS Bedrock
model="claude-sonnet-4-6@20250514"           # Google Vertex AI
```

**When to use:**
- Always set this explicitly. Relying on the SDK default is fragile across versions.
- Use `"haiku"` for exploration, file scanning, simple Q&A (10x cheaper than opus)
- Use `"sonnet"` for the majority of coding tasks
- Use `"opus"` for architecture design, complex multi-file refactoring, hard reasoning

**When NOT to use full IDs:** In general code — use aliases so you automatically get upgrades. Reserve full IDs for Bedrock/Vertex or reproducibility requirements.

---

### `env`

**Type:** `dict[str, str]` | **Default:** `{}`

Environment variables passed to the Claude Code CLI subprocess. **This is how you select providers and pass credentials.** There is no `provider=` parameter — everything goes through `env`.

```python
# Anthropic direct API (most common)
env={"ANTHROPIC_API_KEY": "sk-ant-..."}

# AWS Bedrock
env={
    "CLAUDE_CODE_USE_BEDROCK": "1",
    "AWS_ACCESS_KEY_ID": "AKIA...",
    "AWS_SECRET_ACCESS_KEY": "wJal...",
    "AWS_REGION": "us-east-1",
}

# Google Vertex AI
env={
    "CLAUDE_CODE_USE_VERTEX": "1",
    "CLOUD_ML_REGION": "us-east5",
    "ANTHROPIC_VERTEX_PROJECT_ID": "my-gcp-project",
}

# Azure AI Foundry (via proxy)
env={
    "CLAUDE_CODE_USE_FOUNDRY": "1",
    "ANTHROPIC_BASE_URL": "https://my-azure-endpoint.com",
    "ANTHROPIC_API_KEY": "my-azure-key",
}

# Pass runtime secrets to Bash commands
env={
    "ANTHROPIC_API_KEY": API_KEY,
    "DATABASE_URL": "postgres://...",
    "GITHUB_TOKEN": "ghp_...",
}
```

**When to use:** Always. Without `env`, the SDK either falls back to the shell environment or fails to authenticate.

**Security:** Never hardcode secrets — load from `os.environ` or a secrets manager:
```python
import os
env={"ANTHROPIC_API_KEY": os.environ["ANTHROPIC_API_KEY"]}
```

---

### `permission_mode`

**Type:** `Literal["default", "acceptEdits", "plan", "bypassPermissions", "dontAsk"] | None`
**Default:** `None` → falls back to `"default"`

Controls what Claude is allowed to do without asking permission.

| Mode | File Reads | File Edits | Bash | Use Case |
|------|-----------|-----------|------|----------|
| `"default"` | Auto | Prompt | Prompt | Interactive dev — ask before writing or running |
| `"acceptEdits"` | Auto | Auto | Prompt | Auto-accept file edits, ask before bash |
| `"plan"` | Auto | **BLOCKED** | **BLOCKED** | Read-only planning — see what Claude would do |
| `"bypassPermissions"` | Auto | Auto | Auto | Scripts, CI/CD, trusted automation |
| `"dontAsk"` | Auto | Auto | Auto | Same as bypass — never prompt |

```python
# For scripts and CI/CD (you trust the environment)
permission_mode="bypassPermissions"

# For chat apps where users are watching (ask before Bash)
permission_mode="acceptEdits"

# For "show me what you'd change before you change it"
permission_mode="plan"

# For production apps handling untrusted input
permission_mode="default"   # + custom can_use_tool callback
```

**When NOT to use `"bypassPermissions"`:** When untrusted user input controls the prompt — an adversarial user could instruct Claude to run destructive bash commands.

**Tip:** In `ClaudeSDKClient`, you can switch modes mid-conversation with `client.set_permission_mode()`.

---

### `fallback_model`

**Type:** `str | None` | **Default:** `None`

Model to use if the primary `model` fails (rate limit, model unavailable, etc.).

```python
options = ClaudeAgentOptions(
    model="opus",
    fallback_model="sonnet",   # fall back to sonnet if opus is rate-limited
)
```

**When to use:** Production systems where continuity matters more than always using the best model. Especially useful during Anthropic model outages or rate limit periods.

**When NOT to use:** If the task specifically requires the capability level of the primary model (e.g., if opus is required for accuracy, a sonnet fallback might produce wrong answers).

---

## Group 2 — Tool Control

### `allowed_tools`

**Type:** `list[str]` | **Default:** `[]`

Tools Claude can use **without triggering a permission prompt**. These are auto-approved. Does not restrict — just pre-approves.

```python
# Built-in tools (exact names)
allowed_tools=["Read", "Glob", "Grep", "Write", "Edit", "Bash"]

# Custom MCP tool — specific
allowed_tools=["mcp__validators__validate_email"]

# Custom MCP tools — wildcard (all tools from server)
allowed_tools=["mcp__validators__*"]

# Mix
allowed_tools=["Read", "Glob", "Grep", "mcp__my_server__*"]
```

**All 17 built-in tool names:**
`Read`, `Glob`, `Grep`, `Write`, `Edit`, `Bash`, `NotebookEdit`, `WebSearch`, `WebFetch`, `TodoWrite`, `BashOutput`, `KillBash`, `Agent`, `AskUserQuestion`, `ExitPlanMode`, `ListMcpResources`, `ReadMcpResource`

**When to use:** Always set this. If `permission_mode` is `"default"` and `allowed_tools` is empty, Claude will prompt for permission on every single tool call — which breaks scripts.

**When NOT to use broad wildcards in production:** `allowed_tools=["*"]` or `["mcp__*"]` bypasses your intentional tool restrictions. Be explicit.

---

### `disallowed_tools`

**Type:** `list[str]` | **Default:** `[]`

Tools Claude is **never allowed to use**. Overrides everything — even `allowed_tools` and `bypassPermissions`.

```python
# Block bash in user-facing apps
disallowed_tools=["Bash"]

# Block all write operations (read-only agent)
disallowed_tools=["Write", "Edit", "Bash", "NotebookEdit"]

# Block a specific dangerous custom tool
disallowed_tools=["mcp__admin__delete_all_users"]
```

**Priority:** `disallowed_tools` > `allowed_tools` > `permission_mode`. If a tool is in both `allowed_tools` and `disallowed_tools`, it is **blocked**.

**When to use:**
- User-facing applications where Claude has Bash but you want to prevent specific commands
- Hard safety guardrails regardless of what the prompt says
- Whitelisting approach: block everything except what you explicitly allow via `allowed_tools`

---

### `tools`

**Type:** `list[str] | ToolsPreset | None` | **Default:** `None` (all tools visible)

Controls which built-in tools **exist** (are visible to Claude at all). Different from `allowed_tools`:
- `tools` = what tools Claude can see and attempt to use
- `allowed_tools` = which of those are auto-approved (permission)

```python
# Claude can only see and use these 3 tools — others don't exist
options = ClaudeAgentOptions(tools=["Read", "Glob", "Grep"])

# Remove ALL built-in tools (only custom MCP tools remain)
options = ClaudeAgentOptions(tools=[])

# Use the full Claude Code tool preset
options = ClaudeAgentOptions(tools={"type": "preset", "preset": "claude_code"})
```

**When to use:** When you want to completely hide tools from Claude — not just deny permission but make them invisible. This prevents Claude from even attempting to use them.

**When NOT to use:** For simple permission control — use `allowed_tools` / `disallowed_tools` instead. Use `tools` only when you want to fundamentally change what tool set Claude operates with.

---

## Group 3 — Cost & Safety Limits

### `max_turns`

**Type:** `int | None` | **Default:** `None` (unlimited)

Maximum number of tool-use cycles. Each "turn" = one loop of: Claude thinks → calls tool → gets result → thinks again.

```python
max_turns=1    # answer only, no tool loops (pure Q&A)
max_turns=5    # up to 5 tool calls (simple file tasks)
max_turns=10   # typical coding tasks
max_turns=20   # multi-file edits, test + fix cycles
max_turns=50   # complex autonomous agents
```

**When to use:** Always set this in production. An unconstrained agent can loop indefinitely on certain prompts, burning tokens and money.

**What happens when exceeded:** Claude stops mid-task. `ResultMessage.stop_reason` will be `"error_max_turns"` and `ResultMessage.is_error` will be `True`. The agent returns whatever it completed so far.

**Sizing guidance:** Count how many tool calls the task realistically needs, then add 50% buffer.

---

### `max_budget_usd`

**Type:** `float | None` | **Default:** `None` (unlimited)

Maximum spend in USD. If the running cost exceeds this, Claude stops.

```python
max_budget_usd=0.01    # 1 cent — for testing, no-op checks
max_budget_usd=0.10    # 10 cents — small file analysis
max_budget_usd=1.00    # $1 — typical coding task
max_budget_usd=5.00    # $5 — complex multi-file work
max_budget_usd=20.00   # $20 — large autonomous project
```

**When to use:** Always in production. Prevents accidental runaway costs from infinite loops, large file reads, or unexpectedly long Bash outputs.

**When NOT to use:** During development when you want Claude to always complete the task regardless of cost — but still set `max_turns` to prevent loops.

**What happens when exceeded:** `ResultMessage.stop_reason` = `"error_max_budget_usd"`. Returns work completed so far.

**Note:** This is cost-based (USD). For token-based limits, see `task_budget`.

---

## Group 4 — System Prompt

### `system_prompt`

**Type:** `str | SystemPromptPreset | SystemPromptFile | None` | **Default:** `None`

Custom instructions shaping Claude's behavior. Three forms:

```python
# Form 1: String — REPLACES the default prompt entirely
system_prompt="You are a senior Python developer. Use type hints. Never use print()."

# Form 2: Preset — use Claude Code's full built-in prompt (with tool instructions)
system_prompt={"type": "preset", "preset": "claude_code"}

# Form 3: Preset + append — Claude Code prompt PLUS your additions (BEST PRACTICE)
system_prompt={
    "type": "preset",
    "preset": "claude_code",
    "append": "Always write tests. Never use deprecated APIs. Prefer async/await.",
}

# Form 4: Load from file
system_prompt={"type": "file", "path": "/path/to/system_prompt.txt"}
```

**Critical gotcha:** The SDK default is a **minimal** system prompt — NOT Claude Code's full prompt with tool instructions. If Claude isn't using tools correctly, add `{"type": "preset", "preset": "claude_code"}`.

**When to use:**
- When you want Claude to adopt a persona or role (security auditor, Python expert, etc.)
- When you have permanent rules for a project
- Preset with `append` is the best approach — you keep built-in capabilities and add rules

**When NOT to use:** For simple one-off questions — the overhead is unnecessary.

---

## Group 5 — MCP Servers

### `mcp_servers`

**Type:** `dict[str, McpServerConfig] | str | Path | None` | **Default:** `None`

Connect custom tool servers. Four transport types:

```python
# Type 1: SDK server — in-process, no subprocess overhead (RECOMMENDED for custom tools)
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool(name="greet", description="Greet someone", input_schema={"name": str})
async def greet(args): return {"content": [{"type": "text", "text": f"Hi {args['name']}!"}]}

server = create_sdk_mcp_server(name="utils", tools=[greet])
mcp_servers={"utils": server}

# Type 2: Stdio — external process (for existing MCP servers)
mcp_servers={
    "my_db": {
        "type": "stdio",
        "command": "python",
        "args": ["-m", "my_db_mcp_server"],
        "env": {"DB_URL": "postgres://..."},
    }
}

# Type 3: SSE — remote server (Server-Sent Events)
mcp_servers={
    "remote": {
        "type": "sse",
        "url": "https://my-server.com/mcp/sse",
        "headers": {"Authorization": "Bearer token"},
    }
}

# Type 4: HTTP — remote server (HTTP)
mcp_servers={
    "remote": {
        "type": "http",
        "url": "https://my-server.com/mcp",
        "headers": {"Authorization": "Bearer token"},
    }
}
```

**After connecting, add tool names to `allowed_tools`:**
```python
allowed_tools=["mcp__utils__greet"]       # specific
allowed_tools=["mcp__utils__*"]            # all from server
```

**When to use:** When Claude needs to call your custom business logic (query your DB, call your APIs, run domain-specific calculations).

---

## Group 6 — Session & Conversation

### `resume`

**Type:** `str | None` | **Default:** `None`

Resume a previous session by ID. Claude remembers everything from that session.

```python
# Step 1: save the session_id
session_id = None
async for msg in query(prompt="Read and understand app.py", options=opts):
    if isinstance(msg, ResultMessage):
        session_id = msg.session_id

# Step 2: later, resume — Claude remembers what it read
resume_opts = ClaudeAgentOptions(
    model="sonnet",
    env={"ANTHROPIC_API_KEY": API_KEY},
    resume=session_id,
    max_turns=10,
)
async for msg in query(prompt="Now fix the bug in app.py", options=resume_opts):
    ...
```

**When to use:** Multi-step pipelines where step 2 needs the context from step 1. "Analyze now, fix later" workflows.

**Gotcha:** The `cwd` must match the original session's working directory. Sessions are stored keyed to the path.

---

### `continue_conversation`

**Type:** `bool` | **Default:** `False`

Resumes the **most recent session** in the current `cwd`. Simpler than `resume` but less precise.

```python
continue_conversation=True   # resume latest session in cwd
```

**When to use:** Quick interactive use when you don't track session IDs. One-liner to pick up where you left off.

**`continue_conversation` vs `resume`:**
- `continue_conversation=True` → most recent session in cwd (imprecise)
- `resume="session-id"` → specific session by ID (precise)

---

### `fork_session`

**Type:** `bool` | **Default:** `False`

When resuming, creates a **new session** that starts from the same context as the resumed session. Both sessions diverge from that point.

```python
# A/B test two refactoring approaches from the same starting context
async for msg in query(
    prompt="Refactor using strategy pattern",
    options=ClaudeAgentOptions(resume=base_session_id, fork_session=True),
):
    ...
    # → new_session_id_A

async for msg in query(
    prompt="Refactor using composition instead",
    options=ClaudeAgentOptions(resume=base_session_id, fork_session=True),
):
    ...
    # → new_session_id_B
```

**When to use:** Exploring multiple approaches from the same starting point. A/B testing prompts. Parallel experimentation.

---

## Group 7 — Thinking & Effort

### `thinking`

**Type:** `ThinkingConfig | None` | **Default:** `None`

Controls Claude's extended thinking — chain-of-thought reasoning before responding.

```python
# Adaptive — Claude decides when deep thinking helps
thinking={"type": "adaptive"}

# Always enabled — think up to N tokens
thinking={"type": "enabled", "budget_tokens": 10000}

# Disabled — no extended thinking
thinking={"type": "disabled"}
```

**When to use:**
- Complex reasoning: math, logic puzzles, architecture decisions
- Ambiguous or multi-constraint problems
- When accuracy matters more than speed

**When NOT to use:** Simple factual questions, file reads, straightforward code edits — wastes tokens with no quality benefit.

**Cost impact:** Thinking tokens count toward usage. `budget_tokens=10000` can double the cost of a response.

---

### `effort`

**Type:** `Literal["low", "medium", "high", "max"] | None` | **Default:** `None`

Controls how much effort Claude puts into a response. Distinct from `thinking` — this governs overall response depth.

| Level | Use When |
|-------|----------|
| `"low"` | Simple lookups, quick summaries, file listing |
| `"medium"` | Default behavior — balanced quality/speed |
| `"high"` | Code review, bug analysis, system design |
| `"max"` | Hardest problems, highest-stakes decisions |

```python
effort="low"    # fast, cheaper
effort="high"   # deeper, more thorough
```

**When to use:** Set `"high"` or `"max"` for tasks where quality matters. Set `"low"` for bulk/scan tasks where speed and cost matter more.

---

## Group 8 — Structured Output

### `output_format`

**Type:** `dict | None` | **Default:** `None`

Force Claude to respond with a specific JSON schema. Result is in `ResultMessage.structured_output`.

```python
# Simple schema
output_format={
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "score": {"type": "integer", "minimum": 1, "maximum": 10},
            "tags": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["summary", "score"],
    }
}

# Accessing the result
async for msg in query(prompt="...", options=options):
    if isinstance(msg, ResultMessage):
        data = msg.structured_output
        # {"summary": "...", "score": 8, "tags": ["python", "api"]}
        print(data["score"])
```

**When to use:** When you need machine-readable output — feeding Claude's response into another system, parsing responses programmatically, classifying inputs.

**When NOT to use:** Conversational responses, code generation (use Write/Edit tools instead), anything where free text is the right format.

**Gotcha:** If Claude fails to produce valid JSON matching the schema after retries, you get `"error_max_structured_output_retries"`. Make your schema as simple as possible.

---

## Group 9 — Permissions & Hooks

### `can_use_tool`

**Type:** `CanUseTool | None` | **Default:** `None`

Async callback for fine-grained, dynamic permission decisions. Called for any tool not already in `allowed_tools`.

```python
from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny

async def permission_handler(
    tool_name: str,
    tool_input: dict[str, Any],
    context: ToolPermissionContext,
) -> PermissionResult:
    # Allow all reads unconditionally
    if tool_name in ("Read", "Glob", "Grep"):
        return PermissionResultAllow()

    # Block rm -rf and similar
    if tool_name == "Bash":
        cmd = tool_input.get("command", "")
        if any(danger in cmd for danger in ["rm -rf", "sudo", "DROP TABLE"]):
            return PermissionResultDeny(message=f"Blocked: {cmd}")
        return PermissionResultAllow()

    # Allow writes only to /output/ directory
    if tool_name == "Write":
        path = tool_input.get("file_path", "")
        if not path.startswith("/output/"):
            return PermissionResultDeny(message="Writes only allowed in /output/")
        return PermissionResultAllow()

    return PermissionResultAllow()

options = ClaudeAgentOptions(can_use_tool=permission_handler)
```

**When to use:** When `allowed_tools` / `disallowed_tools` isn't granular enough. Dynamic rules that depend on the actual tool input (e.g., block specific bash commands, restrict writes to certain paths).

**When NOT to use:** Simple blanket allow/deny — use `allowed_tools` / `disallowed_tools` instead. They're faster and clearer.

---

### `hooks`

**Type:** `dict[HookEvent, list[HookMatcher]] | None` | **Default:** `None`

Intercept Claude's behavior at lifecycle points. More powerful than `can_use_tool` — can also modify outputs.

```python
from claude_agent_sdk import HookMatcher

async def audit_log(input_data, tool_use_id, context):
    """Log all tool calls for compliance."""
    tool = input_data.get("tool_name", "unknown")
    args = input_data.get("tool_input", {})
    print(f"[AUDIT] {tool}: {args}")
    return {}  # empty dict = allow, no modification

async def block_prod_writes(input_data, tool_use_id, context):
    """Block writes to production paths."""
    if input_data.get("tool_name") in ("Write", "Edit"):
        path = input_data.get("tool_input", {}).get("file_path", "")
        if "/prod/" in path or "/production/" in path:
            return {"decision": "deny", "reason": "Writes to /prod/ are blocked"}
    return {}

options = ClaudeAgentOptions(
    hooks={
        "PreToolUse": [
            HookMatcher(matcher="*",    hooks=[audit_log]),
            HookMatcher(matcher="Write", hooks=[block_prod_writes]),
            HookMatcher(matcher="Edit",  hooks=[block_prod_writes]),
        ]
    }
)
```

**Hook events:**

| Event | When it fires | Can modify? |
|-------|--------------|-------------|
| `"PreToolUse"` | Before any tool call | Yes — can deny or modify input |
| `"PostToolUse"` | After tool returns result | Yes — can modify output |
| `"PostToolUseFailure"` | After a tool call fails | Yes |
| `"UserPromptSubmit"` | When prompt is submitted | Yes |
| `"Stop"` | When Claude is about to stop | Yes |
| `"SubagentStop"` | When a sub-agent stops | Yes |
| `"PreCompact"` | Before context compaction | No |
| `"Notification"` | On notification events | No |
| `"SubagentStart"` | When a sub-agent starts | No |
| `"PermissionRequest"` | When permission is requested | Yes |

**When to use:** Audit logging, compliance enforcement, dynamic input sanitization, modifying tool outputs.

**When NOT to use:** Simple allow/deny — `allowed_tools` / `disallowed_tools` are clearer and faster.

---

### `permission_prompt_tool_name`

**Type:** `str | None` | **Default:** `None`

Name of a custom tool that handles permission prompts in your UI. Advanced — lets you build a custom "approve this action?" UI.

**When to use:** Building a custom IDE or chat UI where you want to display a custom approval dialog instead of the default CLI prompt.

**When NOT to use:** Almost never in normal usage — ignore unless you're building a Claude Code-like product.

---

## Group 10 — Paths & Working Directory

### `cwd`

**Type:** `str | Path | None` | **Default:** `None` (current working directory of your script)

Working directory for Claude's file operations. All relative paths in Read, Write, Glob, Grep, Bash are resolved against this.

```python
cwd="/Users/abhishek/projects/my-api"
cwd=Path(__file__).parent  # relative to your script's location
```

**When to use:** When your script runs from a different directory than the project you want Claude to work on. Always set this explicitly in production to avoid accidentally operating on the wrong directory.

**Gotcha:** Session storage is keyed to `cwd`. When resuming sessions, `cwd` must match the original.

---

### `add_dirs`

**Type:** `list[str | Path]` | **Default:** `[]`

Additional directories Claude can read/write beyond `cwd`.

```python
add_dirs=[
    "/shared/configs",
    "/data/reference-datasets",
    Path.home() / "templates",
]
```

**When to use:** When Claude needs to reference files outside the main project directory (shared libraries, data files, config templates).

---

### `cli_path`

**Type:** `str | Path | None` | **Default:** `None` (auto-detected from PATH)

Path to the Claude Code CLI binary.

```python
cli_path="/usr/local/bin/claude"
cli_path="/opt/homebrew/bin/claude"
```

**When to use:** Almost never. Only if `claude` isn't in your PATH or you need a specific version.

---

### `settings`

**Type:** `str | None` | **Default:** `None`

Path to a Claude Code settings JSON file.

```python
settings="/path/to/project/.claude/settings.json"
```

**When to use:** When you have project-specific Claude Code settings you want to apply programmatically.

---

## Group 11 — Streaming & Debugging

### `include_partial_messages`

**Type:** `bool` | **Default:** `False`

When `True`, yields `StreamEvent` messages with partial tokens as they arrive. Enables a "typing" effect.

```python
from claude_agent_sdk import StreamEvent

options = ClaudeAgentOptions(include_partial_messages=True)

async for msg in query(prompt="...", options=options):
    if isinstance(msg, StreamEvent):
        # Raw Anthropic API stream event — extract partial text delta
        event = msg.event
    elif isinstance(msg, AssistantMessage):
        ...  # full text once complete
```

**When to use:** Building a chat UI where you want to show tokens as they stream in (like ChatGPT).

**When NOT to use:** Scripts, batch jobs, CI/CD — you just want the final result, not partial tokens.

---

### `stderr`

**Type:** `Callable[[str], None] | None` | **Default:** `None`

Callback receiving stderr output from the Claude Code CLI process line by line.

```python
import logging
logger = logging.getLogger(__name__)

# Print to console
stderr=lambda line: print(f"[CLI] {line}", flush=True)

# Log via structlog / standard logging
stderr=lambda line: logger.debug("cli_stderr", line=line)

# Capture to a list
debug_lines = []
stderr=lambda line: debug_lines.append(line)
```

**When to use:** When things aren't working as expected — tool calls failing, unexpected behavior, debugging permission issues.

---

### `extra_args`

**Type:** `dict[str, str | None]` | **Default:** `{}`

Pass arbitrary CLI flags to the Claude Code subprocess.

```python
# Disable tool search (load all MCP tool defs into context upfront)
extra_args={"--no-tool-search": None}

# Get UserMessage UUIDs back (needed for rewind_files)
extra_args={"replay-user-messages": None}

# Pass multiple flags
extra_args={"--verbose": None, "--timeout": "60"}
```

**When to use:** Accessing a CLI feature not yet exposed through `ClaudeAgentOptions`. Check the Claude Code CLI docs for available flags.

---

### `max_buffer_size`

**Type:** `int | None` | **Default:** `None`

Maximum bytes when buffering CLI stdout. Only needed if dealing with very large responses.

**When to use:** Almost never. Only if you get buffer overflow errors with huge outputs.

---

## Group 12 — Sandbox

### `sandbox`

**Type:** `SandboxSettings | None` | **Default:** `None`

Isolate Bash commands in a security sandbox. Restricts filesystem and network access for shell commands.

```python
from claude_agent_sdk import SandboxSettings

options = ClaudeAgentOptions(
    sandbox=SandboxSettings(
        enabled=True,
        autoAllowBashIfSandboxed=True,       # auto-approve sandboxed bash
        excludedCommands=["git", "docker"],   # these bypass sandbox
        allowUnsandboxedCommands=False,       # force everything through sandbox
        network={
            "allowUnixSockets": ["/var/run/docker.sock"],
            "allowLocalBinding": True,
        },
    )
)
```

**SandboxSettings fields:**

| Field | Type | Default | What it does |
|-------|------|---------|-------------|
| `enabled` | `bool` | `False` | Enable sandbox (macOS/Linux only) |
| `autoAllowBashIfSandboxed` | `bool` | `True` | Auto-approve bash when sandboxed |
| `excludedCommands` | `list[str]` | `[]` | Commands that bypass sandbox |
| `allowUnsandboxedCommands` | `bool` | `True` | Allow `dangerouslyDisableSandbox` |
| `network` | `SandboxNetworkConfig` | — | Network access rules |
| `enableWeakerNestedSandbox` | `bool` | `False` | Weaker sandbox for Docker (Linux) |

**When to use:** Production deployments where untrusted prompts can reach Claude with Bash access. Multi-tenant systems.

**When NOT to use:** Development and testing — adds complexity and can break legitimate tool use.

---

## Group 13 — Sub-agents

### `agents`

**Type:** `dict[str, AgentDefinition] | None` | **Default:** `None`

Define custom sub-agents that Claude can spawn via the `Agent` tool.

```python
from claude_agent_sdk import AgentDefinition

options = ClaudeAgentOptions(
    allowed_tools=["Agent", "Read", "Glob"],
    agents={
        "security-scanner": AgentDefinition(
            description="Scans for security vulnerabilities",
            prompt="You are a security expert. Look for: hardcoded secrets, injection risks, auth flaws, insecure deps.",
            tools=["Read", "Grep"],
            model="sonnet",
            maxTurns=5,
        ),
        "test-generator": AgentDefinition(
            description="Generates pytest test suites",
            prompt="You are a test engineer. Write comprehensive async pytest tests with fixtures.",
            tools=["Read", "Write", "Bash"],
            model="sonnet",
            maxTurns=10,
        ),
        "doc-writer": AgentDefinition(
            description="Writes docstrings and README sections",
            prompt="Write clear, concise Google-style docstrings.",
            tools=["Read", "Edit"],
            model="haiku",     # cheaper model for simpler task
            maxTurns=5,
        ),
    }
)
```

**AgentDefinition fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | `str` | Yes | What the agent does — shown to Claude when deciding which to use |
| `prompt` | `str` | Yes | System prompt for the sub-agent |
| `tools` | `list[str] \| None` | No | Built-in tools available to sub-agent |
| `disallowedTools` | `list[str] \| None` | No | Tools blocked for sub-agent |
| `model` | `str \| None` | No | Model override (can be cheaper than parent) |
| `skills` | `list[str] \| None` | No | Skills available to sub-agent |
| `maxTurns` | `int \| None` | No | Max turns for sub-agent |
| `mcpServers` | `list \| None` | No | MCP servers available to sub-agent |
| `initialPrompt` | `str \| None` | No | Override initial prompt for sub-agent |

**When to use:** When a task has multiple independent subtasks that benefit from different tools, prompts, or models. Sub-agents run in parallel, each in fresh context.

**When NOT to use:** Sequential tasks where each step needs the result of the previous one — use multi-turn conversation instead.

---

## Group 14 — Settings & Plugins

### `setting_sources`

**Type:** `list[SettingSource] | None` | **Default:** `[]` (empty — no settings loaded)

Which `.claude/settings.json` files to load from disk.

```python
# Default: load nothing (cleanest for programmatic use)
setting_sources=[]

# Load user settings only
setting_sources=["user"]        # ~/.claude/settings.json

# Load everything (includes CLAUDE.md, skills, file-based hooks)
setting_sources=["user", "project", "local"]
```

**Critical gotcha:** The default is `[]` — no settings files are loaded. If you expect CLAUDE.md files, skills, or file-based hooks to work, you must explicitly set this. This catches many "why aren't my Claude Code settings working?" issues.

---

### `user`

**Type:** `str | None` | **Default:** `None`

User identifier for audit/tracking purposes.

```python
user="user_12345"
user="abhishek@genaiprotos.com"
```

**When to use:** Multi-user systems where you need to track which user made which query for billing, auditing, or rate limiting.

---

### `betas`

**Type:** `list[SdkBeta]` | **Default:** `[]`

Opt into Anthropic beta features.

```python
betas=["context-1m-2025-08-07"]   # 1M token context window
```

**When to use:** When you need a specific beta feature. Check current available betas in Anthropic docs — they change frequently.

---

### `plugins`

**Type:** `list[SdkPluginConfig]` | **Default:** `[]`

Load custom Claude Code plugins.

```python
plugins=[{"type": "local", "path": "/path/to/my-plugin"}]
```

**When to use:** When you have a local Claude Code plugin to load programmatically.

---

## Group 15 — Token Budget & Checkpointing

### `task_budget`

**Type:** `TaskBudget | None` | **Default:** `None`

API-side token budget. When set, the model is aware of its remaining tokens and self-regulates.

```python
task_budget={"total": 50000}    # 50K token budget — model paces itself
task_budget={"total": 100000}   # 100K token budget
```

**`task_budget` vs `max_budget_usd`:**
- `max_budget_usd` = hard cost ceiling (USD) — stops Claude when cost exceeded
- `task_budget` = token guidance — Claude knows its budget and tries to finish within it

**When to use:** When you want Claude to complete its task within a token envelope rather than stopping abruptly. Produces better-quality truncated outputs than hitting `max_budget_usd`.

---

### `enable_file_checkpointing`

**Type:** `bool` | **Default:** `False`

Track file changes during the session so they can be rewound.

```python
enable_file_checkpointing=True
```

**Required partner:** `extra_args={"replay-user-messages": None}` to get `UserMessage.uuid` values needed for `rewind_files()`.

```python
options = ClaudeAgentOptions(
    enable_file_checkpointing=True,
    extra_args={"replay-user-messages": None},
    # ... other options
)

async with ClaudeSDKClient(options=options) as client:
    await client.query("Refactor app.py")
    async for msg in client.receive_response():
        if isinstance(msg, UserMessage) and msg.uuid:
            checkpoint = msg.uuid

    # Don't like the changes?
    await client.rewind_files(checkpoint)
```

**When to use:** Any time you want undo capability within a conversation.

**Only works with `ClaudeSDKClient.rewind_files()`** — has no effect with `query()`.

---

## TypeScript Name Mapping

Python uses `snake_case`. TypeScript uses `camelCase`. Key mappings:

| Python | TypeScript |
|--------|-----------|
| `permission_mode` | `permissionMode` |
| `allowed_tools` | `allowedTools` |
| `disallowed_tools` | `disallowedTools` |
| `max_turns` | `maxTurns` |
| `max_budget_usd` | `maxBudgetUsd` |
| `system_prompt` | `systemPrompt` |
| `mcp_servers` | `mcpServers` |
| `output_format` | `outputFormat` |
| `include_partial_messages` | `includePartialMessages` |
| `fallback_model` | `fallbackModel` |
| `continue_conversation` | `continueConversation` or `continue` |
| `fork_session` | `forkSession` |
| `can_use_tool` | `canUseTool` |
| `enable_file_checkpointing` | `enableFileCheckpointing` |
| `setting_sources` | `settingsSources` |
| `task_budget` | `taskBudget` |

---

## TypeScript-Only Parameters

These exist in TypeScript but have no Python equivalent:

| Field | Type | Description |
|-------|------|-------------|
| `persistSession` | `boolean` | `false` = in-memory only, no disk storage |
| `spawnClaudeCodeProcess` | `Function` | Custom process spawning (for VMs, containers, remote execution) |
| `abortController` | `AbortController` | Cancel the query externally from outside the loop |
| `debug` | `boolean` | Enable debug logging |
| `debugFile` | `string` | Write debug output to a file |
| `sessionId` | `string` | Explicit session ID (instead of auto-generated) |
| `strictMcpConfig` | `boolean` | Fail hard on invalid MCP config (default: warn and continue) |
| `resumeSessionAt` | `string` | Resume at a specific message ID within a session |

---

## Decision Matrix — What to Set for Each Use Case

### CI/CD Script

```python
ClaudeAgentOptions(
    model="sonnet",
    env={"ANTHROPIC_API_KEY": os.environ["ANTHROPIC_API_KEY"]},
    permission_mode="bypassPermissions",
    allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
    max_turns=30,
    max_budget_usd=2.00,
    cwd="/workspace",
    setting_sources=[],
)
```

### Read-Only Analysis / Audit

```python
ClaudeAgentOptions(
    model="sonnet",
    env={"ANTHROPIC_API_KEY": API_KEY},
    allowed_tools=["Read", "Glob", "Grep", "WebSearch"],
    disallowed_tools=["Write", "Edit", "Bash"],
    max_turns=20,
    max_budget_usd=0.50,
    cwd="/project",
)
```

### Interactive Chat App

```python
ClaudeAgentOptions(
    model="sonnet",
    env={"ANTHROPIC_API_KEY": API_KEY},
    permission_mode="acceptEdits",
    allowed_tools=["Read", "Glob", "Grep", "Write", "Edit", "AskUserQuestion"],
    include_partial_messages=True,       # streaming tokens for UI
    max_turns=10,
    setting_sources=["user", "project"], # load CLAUDE.md, skills
)
```

### Production (Untrusted Input)

```python
ClaudeAgentOptions(
    model="sonnet",
    env={"ANTHROPIC_API_KEY": API_KEY},
    permission_mode="default",
    allowed_tools=["Read", "Glob"],
    disallowed_tools=["Bash", "Write", "Edit"],
    can_use_tool=my_permission_handler,  # fine-grained dynamic control
    max_turns=10,
    max_budget_usd=0.25,
    sandbox=SandboxSettings(enabled=True),
)
```

### Code Generation with Undo

```python
ClaudeAgentOptions(
    model="sonnet",
    env={"ANTHROPIC_API_KEY": API_KEY},
    permission_mode="bypassPermissions",
    allowed_tools=["Read", "Write", "Edit", "Bash"],
    max_turns=20,
    enable_file_checkpointing=True,
    extra_args={"replay-user-messages": None},
)
```

### Structured Data Extraction

```python
ClaudeAgentOptions(
    model="sonnet",
    env={"ANTHROPIC_API_KEY": API_KEY},
    permission_mode="bypassPermissions",
    max_turns=1,
    output_format={
        "type": "json_schema",
        "schema": {
            "type": "object",
            "properties": {
                "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
                "score": {"type": "number"},
                "topics": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["sentiment", "score"],
        },
    },
)
```

### Multi-Specialist Sub-agents

```python
ClaudeAgentOptions(
    model="sonnet",
    env={"ANTHROPIC_API_KEY": API_KEY},
    permission_mode="bypassPermissions",
    allowed_tools=["Agent", "Read", "Glob"],
    max_turns=20,
    agents={
        "security-scanner": AgentDefinition(
            description="Scans for security vulnerabilities",
            tools=["Read", "Grep"],
            model="haiku",      # cheaper for scanning
            maxTurns=5,
        ),
        "code-reviewer": AgentDefinition(
            description="Reviews code quality and best practices",
            tools=["Read", "Grep"],
            model="sonnet",
            maxTurns=5,
        ),
    }
)
```

---

## All Parameters — Quick Reference Table

| # | Parameter | Type | Default | Group |
|---|-----------|------|---------|-------|
| 1 | `model` | `str \| None` | `None` | Core |
| 2 | `env` | `dict[str, str]` | `{}` | Core |
| 3 | `permission_mode` | `PermissionMode \| None` | `None` | Core |
| 4 | `fallback_model` | `str \| None` | `None` | Core |
| 5 | `allowed_tools` | `list[str]` | `[]` | Tools |
| 6 | `disallowed_tools` | `list[str]` | `[]` | Tools |
| 7 | `tools` | `list[str] \| ToolsPreset \| None` | `None` | Tools |
| 8 | `max_turns` | `int \| None` | `None` | Limits |
| 9 | `max_budget_usd` | `float \| None` | `None` | Limits |
| 10 | `system_prompt` | `str \| Preset \| File \| None` | `None` | Prompt |
| 11 | `mcp_servers` | `dict \| str \| Path \| None` | `None` | MCP |
| 12 | `resume` | `str \| None` | `None` | Session |
| 13 | `continue_conversation` | `bool` | `False` | Session |
| 14 | `fork_session` | `bool` | `False` | Session |
| 15 | `thinking` | `ThinkingConfig \| None` | `None` | Thinking |
| 16 | `effort` | `"low"\|"medium"\|"high"\|"max"\|None` | `None` | Thinking |
| 17 | `output_format` | `dict \| None` | `None` | Output |
| 18 | `can_use_tool` | `CanUseTool \| None` | `None` | Permissions |
| 19 | `permission_prompt_tool_name` | `str \| None` | `None` | Permissions |
| 20 | `hooks` | `dict[HookEvent, list[HookMatcher]] \| None` | `None` | Hooks |
| 21 | `cwd` | `str \| Path \| None` | `None` | Paths |
| 22 | `add_dirs` | `list[str \| Path]` | `[]` | Paths |
| 23 | `cli_path` | `str \| Path \| None` | `None` | Paths |
| 24 | `settings` | `str \| None` | `None` | Paths |
| 25 | `include_partial_messages` | `bool` | `False` | Streaming |
| 26 | `stderr` | `Callable \| None` | `None` | Debug |
| 27 | `extra_args` | `dict[str, str \| None]` | `{}` | Advanced |
| 28 | `max_buffer_size` | `int \| None` | `None` | Advanced |
| 29 | `sandbox` | `SandboxSettings \| None` | `None` | Sandbox |
| 30 | `agents` | `dict[str, AgentDefinition] \| None` | `None` | Agents |
| 31 | `setting_sources` | `list[SettingSource] \| None` | `[]` | Settings |
| 32 | `user` | `str \| None` | `None` | Settings |
| 33 | `betas` | `list[SdkBeta]` | `[]` | Settings |
| 34 | `plugins` | `list[SdkPluginConfig]` | `[]` | Plugins |
| 35 | `task_budget` | `TaskBudget \| None` | `None` | Limits |
| 36 | `enable_file_checkpointing` | `bool` | `False` | Session |
| 37 | `debug_stderr` | `Any` | `sys.stderr` | **DEPRECATED** |
| 38 | `max_thinking_tokens` | `int \| None` | `None` | **DEPRECATED** |

---

## Deprecated Parameters

| Parameter | Replace With | Migration |
|-----------|-------------|-----------|
| `debug_stderr` | `stderr` | `stderr=lambda line: print(line)` |
| `max_thinking_tokens` | `thinking` | `thinking={"type": "enabled", "budget_tokens": N}` |

---

## Related Topics

- [query() and Messages](16-query-and-messages.md) — How to use these options with `query()`
- [ClaudeSDKClient](17-client.md) — How to use these options with `ClaudeSDKClient`
- [Permissions](06-permissions.md) — Permission modes and evaluation order in depth
- [Hooks](05-hooks.md) — Hook system in depth: matchers, outputs, async hooks
- [Sessions](07-sessions.md) — resume, fork, session storage, session management
- [Subagents](08-subagents.md) — AgentDefinition spawning and patterns in depth
- [MCP Integration](04-mcp-integration.md) — MCP server types and configuration
- [Structured Outputs](09-structured-outputs.md) — output_format with Pydantic/Zod validation
- [Secure Deployment](15-secure-deployment.md) — sandbox, credential management, isolation
