# Claude Agent SDK — Middleware & Proxy

> Source: [platform.claude.com/docs/en/agent-sdk](https://platform.claude.com/docs/en/agent-sdk/overview) — Python v0.1.51, TypeScript v0.2.86

## Contents

- [What is Middleware?](#what-is-middleware)
- [The 3 Middleware Layers](#the-3-middleware-layers)
- [Which Layer to Use?](#which-layer-to-use)
- [Layer 1: Transport Wrappers](#layer-1-transport-wrappers)
- [Layer 2: Hooks](#layer-2-hooks)
- [Layer 3: can_use_tool](#layer-3-can_use_tool)
- [Use Case: Audit Logging](#use-case-audit-logging)
- [Use Case: Content Filtering & Security](#use-case-content-filtering--security)
- [Use Case: Cost Tracking](#use-case-cost-tracking)
- [Use Case: Metrics & Monitoring](#use-case-metrics--monitoring)
- [Use Case: Input Transformation](#use-case-input-transformation)
- [Use Case: Rate Limiting](#use-case-rate-limiting)
- [Use Case: Caching](#use-case-caching)
- [Use Case: Authentication & Multi-Tenancy](#use-case-authentication--multi-tenancy)
- [Use Case: Token Counting](#use-case-token-counting)
- [Composing Multiple Middlewares](#composing-multiple-middlewares)
- [Hooks Return Value Cheat Sheet](#hooks-return-value-cheat-sheet)
- [All 10 Hook Events](#all-10-hook-events)
- [can_use_tool Deep Dive](#can_use_tool-deep-dive)
- [Quick Reference](#quick-reference)

---

## What is Middleware?

Middleware is **code that sits between your application and Claude**, intercepting messages as they flow back and forth.

```
Your App → [Middleware] → Claude Code CLI → Claude API
Your App ← [Middleware] ← Claude Code CLI ← Claude API
```

Unlike web frameworks where middleware is a single concept, Claude Agent SDK provides **three interception layers** at different levels of abstraction:

```
Your Application
        |
   ┌────┴──────────────────────────────────┐
   │  Layer 3: can_use_tool                │  ← Permission decisions
   │  (called when tool needs permission)  │
   ├───────────────────────────────────────┤
   │  Layer 2: Hooks                       │  ← Lifecycle events
   │  (PreToolUse, PostToolUse, etc.)      │     10 events, pattern matching
   ├───────────────────────────────────────┤
   │  Layer 1: Transport Wrapper           │  ← Raw JSON wire
   │  (wraps the stdin/stdout pipe)        │     full message interception
   └────┬──────────────────────────────────┘
        |
   Claude Code CLI → Claude API
```

---

## The 3 Middleware Layers

| Layer | What You See | API Stability | Power | When to Use |
|-------|-------------|--------------|-------|-------------|
| **Transport** | Every raw JSON message | Unstable (internal) | Highest | Caching, rate limiting, auth proxy, token counting |
| **Hooks** | Structured lifecycle events | Stable (first-class) | High | Audit logging, security filtering, input modification, metrics |
| **can_use_tool** | Tool permission requests | Stable (first-class) | Focused | Dynamic allow/deny, path restrictions, interrupt-on-violation |

---

## Which Layer to Use?

### Decision Table

| I want to... | Layer | Method |
|---|---|---|
| Log every tool call | Hooks | `PreToolUse` + `PostToolUse` |
| Block dangerous bash commands | Hooks | `PreToolUse` matcher `"Bash"` + deny |
| Modify a tool's input before execution | Hooks | `PreToolUse` + `updatedInput` |
| Filter user prompts for injection | Hooks | `UserPromptSubmit` + block |
| Track tool call durations | Hooks | `PreToolUse` + `PostToolUse` with timing |
| Dynamic permission decisions based on context | `can_use_tool` | `PermissionResultAllow/Deny` |
| Block writes to specific file paths | `can_use_tool` | Path check in callback |
| Stop agent on security violation | `can_use_tool` | `PermissionResultDeny(interrupt=True)` |
| Cache repeated queries | Transport | Wrap `write()` + `read_messages()` |
| Rate limit outbound messages | Transport | Sleep in `write()` |
| Add auth tokens to a proxy | Transport | Inject in `write()` |
| Count raw tokens from wire | Transport | Parse usage fields in `read_messages()` |
| Load balance across CLI instances | Transport | Round-robin `write()` + `read_messages()` |
| Track cumulative cost across sessions | `ResultMessage` | Parse `msg.total_cost_usd` |

### Rule of Thumb

```
Start with Hooks → covers 80% of use cases (stable API, clean pattern matching)
  ↓ Not flexible enough?
Use can_use_tool → for dynamic permission logic with context
  ↓ Need full message access?
Use Transport wrapper → for caching, rate limiting, auth proxy
```

---

## Layer 1: Transport Wrappers

### The Decorator Pattern

Wrap an existing transport — intercept all messages flowing through it.

```python
from claude_agent_sdk import Transport


class MyMiddleware(Transport):
    """Wraps an inner transport to add behavior."""

    def __init__(self, inner: Transport) -> None:
        self._inner = inner

    async def connect(self) -> None:
        await self._inner.connect()

    async def write(self, data: str) -> None:
        # ← intercept OUTBOUND messages here
        await self._inner.write(data)

    async def read_messages(self):
        async for msg in self._inner.read_messages():
            # ← intercept INBOUND messages here
            yield msg

    async def close(self) -> None:
        await self._inner.close()

    def is_ready(self) -> bool:
        return self._inner.is_ready()

    async def end_input(self) -> None:
        await self._inner.end_input()
```

### How to Use It

```python
from claude_agent_sdk._internal.transport.subprocess_cli import SubprocessCLITransport

options = ClaudeAgentOptions(model="sonnet", env={"ANTHROPIC_API_KEY": API_KEY}, ...)

# 1. Create the real transport
inner = SubprocessCLITransport(prompt="...", options=options)

# 2. Wrap it
transport = MyMiddleware(inner)

# 3. Pass to query() or ClaudeSDKClient
async for msg in query(prompt="...", options=options, transport=transport):
    ...
```

**When NOT to use transport wrappers:** If you only care about tool calls or permissions — hooks and `can_use_tool` are easier, more stable, and the right tool.

---

## Layer 2: Hooks

Hooks are the **first-class middleware system** — fire at 10 lifecycle points, receive structured typed data, built-in pattern matching.

### Basic Structure

```python
from claude_agent_sdk import ClaudeAgentOptions, HookMatcher

async def my_hook(
    input_data: dict,          # structured event data
    tool_use_id: str | None,   # tool call ID (if applicable)
    context: dict,             # hook context
) -> dict:
    return {}                  # empty = allow, no modification

options = ClaudeAgentOptions(
    hooks={
        "PreToolUse": [
            HookMatcher(matcher="Bash",  hooks=[my_hook]),   # only Bash
            HookMatcher(matcher=None,    hooks=[log_all]),   # all tools
        ],
        "PostToolUse": [
            HookMatcher(hooks=[post_hook]),
        ],
    }
)
```

### HookMatcher Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `matcher` | `str \| None` | `None` | Regex for tool names. `None` = all. `"Bash\|Write"` = Bash or Write. |
| `hooks` | `list[HookCallback]` | `[]` | Async callbacks to invoke |
| `timeout` | `float \| None` | `None` (60s) | Per-hook timeout in seconds |

### What PreToolUse Receives (input_data)

```python
{
    "hook_event_name": "PreToolUse",
    "session_id": "abc-123",
    "transcript_path": "/path/to/transcript",
    "cwd": "/path/to/project",
    "tool_name": "Bash",
    "tool_input": {"command": "ls -la"},
    "tool_use_id": "tu_001",
    "agent_id": "...",        # present if inside a sub-agent
    "agent_type": "...",
}
```

### What PostToolUse Receives (input_data)

```python
{
    "hook_event_name": "PostToolUse",
    "tool_name": "Bash",
    "tool_input": {"command": "ls -la"},
    "tool_response": "file1.py\nfile2.py\n...",
    "tool_use_id": "tu_001",
    ...
}
```

---

## Layer 3: can_use_tool

A **single async callback** the SDK invokes when a tool needs permission — not already in `allowed_tools` or `disallowed_tools`.

```python
from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny

async def handler(
    tool_name: str,
    tool_input: dict,
    context,         # ToolPermissionContext — includes suggestions
) -> PermissionResultAllow | PermissionResultDeny:
    ...

options = ClaudeAgentOptions(can_use_tool=handler)
```

**When it's called:**
```
disallowed_tools check → BLOCKED (handler NOT called)
allowed_tools check    → APPROVED (handler NOT called)
can_use_tool set?      → CALL IT (your callback decides)
permission_mode        → FALLBACK
```

**Critical constraint:** `can_use_tool` requires streaming mode — it works with `ClaudeSDKClient` but raises `ValueError` with `query()` using a string prompt.

---

## Use Case: Audit Logging

Log every tool call to a JSONL file for compliance audit.

```python
import json, time
from pathlib import Path
from claude_agent_sdk import ClaudeAgentOptions, HookMatcher


class AuditLogger:
    def __init__(self, log_path: str = "./audit.jsonl") -> None:
        self._log = Path(log_path)

    def _write(self, entry: dict) -> None:
        with self._log.open("a") as f:
            f.write(json.dumps(entry) + "\n")

    async def on_tool_start(self, input_data, tool_use_id, context):
        self._write({
            "event": "tool_start", "timestamp": time.time(),
            "tool": input_data.get("tool_name"),
            "input": input_data.get("tool_input"),
            "session_id": input_data.get("session_id"),
            "cwd": input_data.get("cwd"),
        })
        return {}

    async def on_tool_done(self, input_data, tool_use_id, context):
        self._write({
            "event": "tool_done", "timestamp": time.time(),
            "tool": input_data.get("tool_name"),
            "response_preview": str(input_data.get("tool_response", ""))[:500],
        })
        return {}

    async def on_tool_error(self, input_data, tool_use_id, context):
        self._write({
            "event": "tool_error", "timestamp": time.time(),
            "tool": input_data.get("tool_name"),
            "error": input_data.get("error"),
        })
        return {}

    async def on_prompt(self, input_data, tool_use_id, context):
        self._write({
            "event": "user_prompt", "timestamp": time.time(),
            "prompt": input_data.get("prompt"),
            "session_id": input_data.get("session_id"),
        })
        return {}


audit = AuditLogger(log_path="./logs/audit.jsonl")

options = ClaudeAgentOptions(
    model="sonnet",
    env={"ANTHROPIC_API_KEY": API_KEY},
    allowed_tools=["Read", "Glob", "Grep", "Bash"],
    permission_mode="bypassPermissions",
    hooks={
        "PreToolUse":         [HookMatcher(hooks=[audit.on_tool_start])],
        "PostToolUse":        [HookMatcher(hooks=[audit.on_tool_done])],
        "PostToolUseFailure": [HookMatcher(hooks=[audit.on_tool_error])],
        "UserPromptSubmit":   [HookMatcher(hooks=[audit.on_prompt])],
    },
)
```

---

## Use Case: Content Filtering & Security

Block dangerous commands and prompt injection.

```python
import re
from claude_agent_sdk import ClaudeAgentOptions, HookMatcher

BLOCKED_BASH = [
    r"rm\s+-rf\s+/", r"rm\s+-rf\s+~", r"DROP\s+TABLE",
    r"chmod\s+777", r"curl.*\|\s*(sh|bash)", r"eval\s*\(",
    r"mkfs\.", r"dd\s+if=", r">\s*/dev/sd",
]

INJECTION_MARKERS = [
    "ignore previous instructions", "ignore all previous",
    "system prompt:", "you are now", "disregard your instructions",
]


async def bash_security_filter(input_data, tool_use_id, context):
    command = input_data.get("tool_input", {}).get("command", "")
    for pattern in BLOCKED_BASH:
        if re.search(pattern, command, re.IGNORECASE):
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"BLOCKED: matches pattern '{pattern}'",
                }
            }
    return {}


async def write_path_filter(input_data, tool_use_id, context):
    tool_input = input_data.get("tool_input", {})
    path = tool_input.get("file_path", "") or tool_input.get("path", "")
    for blocked in ["/etc", "/usr", "/System", ".env", ".ssh", "credentials"]:
        if blocked in path:
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"BLOCKED: write to sensitive path '{blocked}'",
                }
            }
    return {}


async def prompt_injection_filter(input_data, tool_use_id, context):
    prompt = input_data.get("prompt", "").lower()
    for marker in INJECTION_MARKERS:
        if marker in prompt:
            return {"decision": "block", "reason": f"BLOCKED: injection marker '{marker}'"}
    return {}


options = ClaudeAgentOptions(
    model="sonnet",
    env={"ANTHROPIC_API_KEY": API_KEY},
    allowed_tools=["Read", "Write", "Edit", "Bash", "Glob"],
    permission_mode="bypassPermissions",
    hooks={
        "PreToolUse": [
            HookMatcher(matcher="Bash",       hooks=[bash_security_filter]),
            HookMatcher(matcher="Write|Edit", hooks=[write_path_filter]),
        ],
        "UserPromptSubmit": [HookMatcher(hooks=[prompt_injection_filter])],
    },
)
```

---

## Use Case: Cost Tracking

Track cumulative cost across multiple queries, stop on budget exceeded.

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, ResultMessage, AssistantMessage, TextBlock


class CostTracker:
    def __init__(self, budget_usd: float = 10.0) -> None:
        self.budget_usd = budget_usd
        self.total_cost_usd: float = 0.0
        self.query_count: int = 0
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0

    def track(self, result: ResultMessage) -> None:
        self.query_count += 1
        if result.total_cost_usd:
            self.total_cost_usd += result.total_cost_usd
        if result.usage:
            self.total_input_tokens += result.usage.get("input_tokens", 0)
            self.total_output_tokens += result.usage.get("output_tokens", 0)

    @property
    def over_budget(self) -> bool:
        return self.total_cost_usd >= self.budget_usd

    def report(self) -> str:
        return (
            f"Queries: {self.query_count} | "
            f"Cost: ${self.total_cost_usd:.4f} / ${self.budget_usd:.2f} | "
            f"Tokens: {self.total_input_tokens:,}in / {self.total_output_tokens:,}out"
        )


async def main():
    tracker = CostTracker(budget_usd=1.00)
    options = ClaudeAgentOptions(
        model="sonnet", env={"ANTHROPIC_API_KEY": API_KEY},
        allowed_tools=["Read", "Glob"], permission_mode="bypassPermissions", max_turns=5,
    )

    async with ClaudeSDKClient(options=options) as client:
        for prompt in ["List Python files", "Summarize main app file", "List dependencies"]:
            if tracker.over_budget:
                print("BUDGET EXCEEDED — stopping")
                break

            await client.query(prompt)
            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            print(block.text[:200])
                elif isinstance(msg, ResultMessage):
                    tracker.track(msg)
                    print(f"  [{tracker.report()}]")
```

---

## Use Case: Metrics & Monitoring

Collect tool duration and error metrics for dashboards.

```python
import time
from collections import defaultdict
from claude_agent_sdk import ClaudeAgentOptions, HookMatcher


class MetricsCollector:
    def __init__(self) -> None:
        self.tool_counts: dict[str, int] = defaultdict(int)
        self.tool_durations: dict[str, list[float]] = defaultdict(list)
        self.tool_errors: dict[str, int] = defaultdict(int)
        self._start_times: dict[str, float] = {}

    async def on_pre_tool(self, input_data, tool_use_id, context):
        tool = input_data.get("tool_name", "unknown")
        self.tool_counts[tool] += 1
        if tool_use_id:
            self._start_times[tool_use_id] = time.monotonic()
        return {}

    async def on_post_tool(self, input_data, tool_use_id, context):
        tool = input_data.get("tool_name", "unknown")
        if tool_use_id and tool_use_id in self._start_times:
            duration = time.monotonic() - self._start_times.pop(tool_use_id)
            self.tool_durations[tool].append(duration)
        return {}

    async def on_tool_error(self, input_data, tool_use_id, context):
        self.tool_errors[input_data.get("tool_name", "unknown")] += 1
        self._start_times.pop(tool_use_id, None)
        return {}

    def report(self) -> dict:
        return {
            "total_calls": sum(self.tool_counts.values()),
            "calls_by_tool": dict(self.tool_counts),
            "errors_by_tool": dict(self.tool_errors),
            "avg_duration_ms": {
                t: round(sum(d) / len(d) * 1000, 1)
                for t, d in self.tool_durations.items() if d
            },
        }


metrics = MetricsCollector()

options = ClaudeAgentOptions(
    model="sonnet", env={"ANTHROPIC_API_KEY": API_KEY},
    allowed_tools=["Read", "Glob", "Grep", "Bash"],
    permission_mode="bypassPermissions",
    hooks={
        "PreToolUse":         [HookMatcher(hooks=[metrics.on_pre_tool])],
        "PostToolUse":        [HookMatcher(hooks=[metrics.on_post_tool])],
        "PostToolUseFailure": [HookMatcher(hooks=[metrics.on_tool_error])],
    },
)
# After session: print(json.dumps(metrics.report(), indent=2))
```

---

## Use Case: Input Transformation

Modify tool inputs before execution — dry-run enforcement, path scoping, context injection.

```python
from claude_agent_sdk import ClaudeAgentOptions, HookMatcher


async def enforce_dry_run(input_data, tool_use_id, context):
    """Add --dry-run to destructive bash commands."""
    command = input_data.get("tool_input", {}).get("command", "")
    for cmd in ["rm ", "mv ", "cp ", "chmod ", "chown "]:
        if command.startswith(cmd) and "--dry-run" not in command:
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "updatedInput": {"command": f"{command} --dry-run"},
                    "additionalContext": "Dry-run enforced by middleware.",
                }
            }
    return {}


async def add_error_warning(input_data, tool_use_id, context):
    """Warn Claude when a tool response contains errors."""
    response = str(input_data.get("tool_response", ""))
    if "error" in response.lower() or "traceback" in response.lower():
        return {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": (
                    "WARNING: The previous command produced errors. "
                    "Check output carefully before proceeding."
                ),
            }
        }
    return {}


options = ClaudeAgentOptions(
    model="sonnet", env={"ANTHROPIC_API_KEY": API_KEY},
    allowed_tools=["Read", "Bash", "Write"],
    permission_mode="bypassPermissions",
    hooks={
        "PreToolUse":  [HookMatcher(matcher="Bash", hooks=[enforce_dry_run])],
        "PostToolUse": [HookMatcher(matcher="Bash", hooks=[add_error_warning])],
    },
)
```

---

## Use Case: Rate Limiting

Enforce minimum interval between outbound messages (transport wrapper).

```python
import time, anyio
from claude_agent_sdk import Transport


class RateLimitingTransport(Transport):
    def __init__(self, inner: Transport, min_interval_sec: float = 0.5) -> None:
        self._inner = inner
        self._min_interval = min_interval_sec
        self._last_write: float = 0.0

    async def connect(self)         -> None: await self._inner.connect()
    async def close(self)           -> None: await self._inner.close()
    def is_ready(self)              -> bool: return self._inner.is_ready()
    async def end_input(self)       -> None: await self._inner.end_input()

    async def write(self, data: str) -> None:
        elapsed = time.monotonic() - self._last_write
        if elapsed < self._min_interval:
            await anyio.sleep(self._min_interval - elapsed)
        self._last_write = time.monotonic()
        await self._inner.write(data)

    async def read_messages(self):
        async for msg in self._inner.read_messages():
            yield msg
```

---

## Use Case: Caching

Cache responses keyed by prompt hash to avoid repeat API calls.

```python
import hashlib, json
from claude_agent_sdk import Transport


class CachingTransport(Transport):
    def __init__(self, inner: Transport) -> None:
        self._inner = inner
        self._cache: dict[str, list[dict]] = {}
        self._current_key: str | None = None
        self._cached_hit: list[dict] | None = None

    async def connect(self)        -> None: await self._inner.connect()
    async def close(self)          -> None: await self._inner.close()
    def is_ready(self)             -> bool: return self._inner.is_ready()
    async def end_input(self)      -> None: await self._inner.end_input()

    async def write(self, data: str) -> None:
        key = hashlib.sha256(data.encode()).hexdigest()
        if key in self._cache:
            self._cached_hit = self._cache[key]
            return  # skip real write — serve from cache
        self._current_key = key
        self._cached_hit = None
        await self._inner.write(data)

    async def read_messages(self):
        if self._cached_hit is not None:
            for msg in self._cached_hit:
                yield msg
            return
        collected = []
        async for msg in self._inner.read_messages():
            collected.append(msg)
            yield msg
        if self._current_key:
            self._cache[self._current_key] = collected
```

---

## Use Case: Authentication & Multi-Tenancy

Inject auth metadata into outbound messages for a multi-tenant proxy.

```python
import json
from claude_agent_sdk import Transport


class AuthenticatedTransport(Transport):
    def __init__(self, inner: Transport, user_id: str, org_id: str, auth_token: str) -> None:
        self._inner = inner
        self._meta = {"user_id": user_id, "org_id": org_id, "token": auth_token}

    async def connect(self)        -> None: await self._inner.connect()
    async def close(self)          -> None: await self._inner.close()
    def is_ready(self)             -> bool: return self._inner.is_ready()
    async def end_input(self)      -> None: await self._inner.end_input()

    async def write(self, data: str) -> None:
        try:
            parsed = json.loads(data.strip())
            parsed["_auth"] = self._meta
            data = json.dumps(parsed) + "\n"
        except json.JSONDecodeError:
            pass
        await self._inner.write(data)

    async def read_messages(self):
        async for msg in self._inner.read_messages():
            msg.pop("_auth", None)  # strip auth from inbound
            yield msg
```

---

## Use Case: Token Counting

Track exact token counts from the wire.

```python
from claude_agent_sdk import Transport


class TokenCountingTransport(Transport):
    def __init__(self, inner: Transport) -> None:
        self._inner = inner
        self.input_tokens: int = 0
        self.output_tokens: int = 0
        self.message_count: int = 0

    async def connect(self)        -> None: await self._inner.connect()
    async def close(self)          -> None: await self._inner.close()
    def is_ready(self)             -> bool: return self._inner.is_ready()
    async def end_input(self)      -> None: await self._inner.end_input()
    async def write(self, data)    -> None: await self._inner.write(data)

    async def read_messages(self):
        async for msg in self._inner.read_messages():
            if msg.get("type") == "assistant":
                usage = msg.get("message", {}).get("usage", {})
                self.input_tokens  += usage.get("input_tokens", 0)
                self.output_tokens += usage.get("output_tokens", 0)
                self.message_count += 1
            elif msg.get("type") == "result":
                usage = msg.get("usage", {})
                self.input_tokens  += usage.get("input_tokens", 0)
                self.output_tokens += usage.get("output_tokens", 0)
            yield msg

    def report(self) -> str:
        return (
            f"Messages: {self.message_count} | "
            f"Input: {self.input_tokens:,} | "
            f"Output: {self.output_tokens:,} | "
            f"Total: {self.input_tokens + self.output_tokens:,}"
        )
```

---

## Composing Multiple Middlewares

### Transport Stacking (Decorator Pattern)

Nest transport wrappers — order matters:

```python
from claude_agent_sdk._internal.transport.subprocess_cli import SubprocessCLITransport

inner         = SubprocessCLITransport(prompt="...", options=options)
token_counter = TokenCountingTransport(inner)
rate_limiter  = RateLimitingTransport(token_counter, min_interval_sec=0.5)
transport     = LoggingTransport(rate_limiter)

# Message flow:
# write():  Logging → Rate Limiting → Token Counting → Real
# read():   Real → Token Counting → Rate Limiting → Logging
```

### Hook Stacking (Built-in)

Multiple matchers, multiple callbacks per event:

```python
options = ClaudeAgentOptions(
    hooks={
        "PreToolUse": [
            HookMatcher(matcher="Bash",       hooks=[bash_security_filter, enforce_dry_run]),
            HookMatcher(matcher="Write|Edit", hooks=[write_path_filter]),
            HookMatcher(hooks=[audit.on_tool_start, metrics.on_pre_tool]),  # all tools
        ],
        "PostToolUse": [
            HookMatcher(hooks=[audit.on_tool_done, metrics.on_post_tool]),
        ],
        "PostToolUseFailure": [
            HookMatcher(hooks=[audit.on_tool_error, metrics.on_tool_error]),
        ],
        "UserPromptSubmit": [
            HookMatcher(hooks=[prompt_injection_filter]),
        ],
    }
)
```

### Full Production Stack

```python
# Transport layer (wire-level)
inner     = SubprocessCLITransport(prompt="...", options=base_options)
transport = LoggingTransport(TokenCountingTransport(inner))

# Hook layer (lifecycle-level)
audit   = AuditLogger(log_path="./logs/audit.jsonl")
metrics = MetricsCollector()

options = ClaudeAgentOptions(
    model="sonnet",
    env={"ANTHROPIC_API_KEY": API_KEY},
    allowed_tools=["Read", "Glob", "Grep"],
    disallowed_tools=["Bash"],
    permission_mode="bypassPermissions",
    max_turns=10,
    max_budget_usd=1.00,
    hooks={
        "PreToolUse": [
            HookMatcher(matcher="Write|Edit", hooks=[write_path_filter]),
            HookMatcher(hooks=[audit.on_tool_start, metrics.on_pre_tool]),
        ],
        "PostToolUse":        [HookMatcher(hooks=[audit.on_tool_done,  metrics.on_post_tool])],
        "PostToolUseFailure": [HookMatcher(hooks=[audit.on_tool_error, metrics.on_tool_error])],
        "UserPromptSubmit":   [HookMatcher(hooks=[prompt_injection_filter])],
    },
)
```

---

## Hooks Return Value Cheat Sheet

```python
# ── Allow (do nothing) ──
return {}

# ── Block tool call (PreToolUse only) ──
return {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "why it was blocked",
    }
}

# ── Modify tool input (PreToolUse only) ──
return {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "updatedInput": {"command": "ls -la --safe"},  # replacement input dict
    }
}

# ── Add context for Claude (any hook, PostToolUse most useful) ──
return {
    "hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": "WARNING: output contains errors — review carefully.",
    }
}

# ── Block user prompt (UserPromptSubmit only) ──
return {"decision": "block", "reason": "injection attempt detected"}

# ── Stop the session ──
return {"continue_": False, "stopReason": "budget exceeded"}

# ── Run asynchronously (don't block Claude) ──
return {"async_": True, "asyncTimeout": 5000}  # ms
```

---

## All 10 Hook Events

| # | Event | When | Can Block? | Can Modify Input? | Can Add Context? |
|---|-------|------|-----------|------------------|-----------------|
| 1 | `PreToolUse` | Before tool execution | Yes | Yes (`updatedInput`) | Yes |
| 2 | `PostToolUse` | After tool success | No | No | Yes (`additionalContext`) |
| 3 | `PostToolUseFailure` | After tool failure | No | No | Yes |
| 4 | `UserPromptSubmit` | User sends a prompt | Yes (`decision: "block"`) | No | Yes |
| 5 | `Stop` | Agent stopping | No | No | No |
| 6 | `SubagentStart` | Sub-agent spawned | No | No | Yes |
| 7 | `SubagentStop` | Sub-agent finished | No | No | No |
| 8 | `PreCompact` | Before context compaction | No | No | No |
| 9 | `Notification` | Notification event | No | No | Yes |
| 10 | `PermissionRequest` | Tool needs permission | Yes | No | No |

**Most useful for middleware:** `PreToolUse` (security, dry-run, input validation), `PostToolUse` (metrics, warning injection), `PostToolUseFailure` (error tracking), `UserPromptSubmit` (injection filtering).

---

## can_use_tool Deep Dive

### Unique Powers (Hooks Cannot Do These)

**1. Dynamic permission rules — update session rules after a decision:**
```python
from claude_agent_sdk import PermissionResultAllow, PermissionUpdate, PermissionRuleValue

async def handler(tool_name, tool_input, context):
    return PermissionResultAllow(
        updated_permissions=[
            PermissionUpdate(
                type="addRules",
                behavior="allow",
                rules=[PermissionRuleValue(tool_name="Bash")],
                destination="session",
            )
        ]
    )
```

**2. Interrupt the entire agent loop:**
```python
async def handler(tool_name, tool_input, context):
    if is_critical_violation(tool_input):
        return PermissionResultDeny(
            message="Critical security violation",
            interrupt=True,   # STOPS THE ENTIRE AGENT
        )
    return PermissionResultAllow()
```

**3. Modify tool input on allow:**
```python
async def handler(tool_name, tool_input, context):
    if tool_name == "Bash":
        cmd = tool_input.get("command", "")
        return PermissionResultAllow(
            updated_input={"command": f"{cmd} 2>&1"}  # always capture stderr
        )
    return PermissionResultAllow()
```

**4. Access CLI permission suggestions:**
```python
async def handler(tool_name, tool_input, context):
    for suggestion in (context.suggestions or []):
        print(f"CLI suggests: {suggestion}")
    return PermissionResultAllow()
```

---

## Quick Reference

### Middleware Decision Matrix

| Need | Layer | Key |
|------|-------|-----|
| Block dangerous bash | Hooks `PreToolUse` | `permissionDecision: "deny"` |
| Log all tool calls | Hooks Pre + Post | Write to JSONL |
| Filter user prompts | Hooks `UserPromptSubmit` | `decision: "block"` |
| Modify tool inputs | Hooks `PreToolUse` | `updatedInput: {...}` |
| Inject warning after error | Hooks `PostToolUse` | `additionalContext: "..."` |
| Track tool durations | Hooks Pre + Post | `time.monotonic()` diff |
| Dynamic allow/deny by context | `can_use_tool` | `PermissionResultAllow/Deny` |
| Interrupt on violation | `can_use_tool` | `PermissionResultDeny(interrupt=True)` |
| Update session rules | `can_use_tool` | `updated_permissions` |
| Cache responses | Transport `write()` + `read_messages()` | Hash key |
| Rate limit | Transport `write()` | `anyio.sleep()` |
| Auth token injection | Transport `write()` | Inject `_auth` field |
| Token counting | Transport `read_messages()` | Parse `usage` fields |
| Load balancing | Transport `write()` + `read_messages()` | Round-robin backends |

### Transport Wrapper Template

```python
from claude_agent_sdk import Transport

class MyMiddleware(Transport):
    def __init__(self, inner: Transport):
        self._inner = inner

    async def connect(self):           await self._inner.connect()
    async def write(self, data: str):  await self._inner.write(data)    # intercept outbound
    async def read_messages(self):                                       # intercept inbound
        async for msg in self._inner.read_messages():
            yield msg
    async def close(self):             await self._inner.close()
    def is_ready(self):                return self._inner.is_ready()
    async def end_input(self):         await self._inner.end_input()
```

---

## Related Topics

- [Transport](19-transport.md) — Custom transport implementations, wire protocol, WebSocket, SSH, Mock
- [Hooks](05-hooks.md) — Hook system in depth: matchers, output fields, async hooks
- [Permissions](06-permissions.md) — can_use_tool, permission modes, evaluation order
- [ClaudeAgentOptions](18-claude-agent-options.md) — `hooks` and `can_use_tool` parameter docs
- [Secure Deployment](15-secure-deployment.md) — Security patterns, sandbox, credential management
